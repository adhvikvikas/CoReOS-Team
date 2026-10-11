from fastapi import APIRouter, HTTPException
import pandas as pd
import numpy as np
from pathlib import Path
from src.coreos.data.loader import DatasetLoader
from src.coreos.data.profiler import DatasetProfiler
from src.coreos.data.preprocessing import DataPreprocessor

router = APIRouter()

@router.get("/")
def get_dataset_info():
    try:
        loader = DatasetLoader()
        df = loader.load()
        profiler = DatasetProfiler(loader)
        prof = profiler.profile(df)
        
        df_head = df.head(100).replace([np.inf, -np.inf], np.nan).astype(object).where(pd.notnull(df.head(100)), None).to_dict(orient="records")
        describe_df = df.describe().T.reset_index().rename(columns={"index": "feature"}).replace([np.inf, -np.inf], np.nan)
        describe = describe_df.astype(object).where(pd.notnull(describe_df), None).to_dict(orient="records")
        num_cols = [c for c in df.select_dtypes(include=[np.number]).columns]
        corr_df = df[num_cols].corr()
        corr_matrix = [[float(v) if pd.notnull(v) and not np.isinf(v) else 0.0 for v in row] for row in corr_df.values]
        corr_records = []
        for idx, row in corr_df.iterrows():
            rec = {"feature": str(idx)}
            for col in num_cols:
                v = row[col]
                rec[col] = float(v) if pd.notnull(v) and not np.isinf(v) else 0.0
            corr_records.append(rec)
        
        # Prepare distributions
        distributions = {}
        num_cols = [c for c in df.select_dtypes(include=[np.number]).columns]
        for col in num_cols:
            hist_normal, bin_edges = np.histogram(df[df["status"] == 0][col].dropna(), bins=40)
            hist_anomaly, _ = np.histogram(df[df["status"] == 1][col].dropna(), bins=bin_edges)
            distributions[col] = {
                "bin_edges": bin_edges.tolist(),
                "normal_counts": hist_normal.tolist(),
                "anomaly_counts": hist_anomaly.tolist()
            }
            
        return {
            "metadata": {
                "rows": prof["rows"],
                "cols": prof["cols"],
                "duplicates": prof["duplicates"],
                "anomaly_count": prof["status_distribution"].get(1, 0),
                "anomaly_percentage": round((prof["status_distribution"].get(1, 0) / prof["rows"]) * 100, 2) if prof["rows"] > 0 else 0
            },
            "columns": list(df.columns),
            "head": df_head,
            "describe": describe,
            "correlations": corr_records,
            "corr_matrix": corr_matrix,
            "corr_features": num_cols,
            "features": num_cols,
            "distributions": distributions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train")
def train_anomaly_baseline():
    try:
        loader = DatasetLoader()
        df = loader.load()
        preproc = DataPreprocessor()
        metrics = preproc.train_anomaly_baseline(df)
        
        imp_list = [{"Feature": k, "Importance": v} for k, v in metrics["feature_importance"].items()]
        imp_list = sorted(imp_list, key=lambda x: x["Importance"], reverse=True)[:8]
        
        return {
            "metrics": metrics,
            "feature_importance": imp_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
