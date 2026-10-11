import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import (
    overview,
    dataset,
    simulation,
    agents,
    conflicts,
    healing,
    benchmarks,
    reports
)

app = FastAPI(
    title="CoReOS API",
    description="Conflict-Aware, Self-Healing Multi-Agent AI Operating System Resource Manager API",
    version="0.1.0"
)

# Configure CORS for React development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview.router, prefix="/api/overview", tags=["overview"])
app.include_router(dataset.router, prefix="/api/dataset", tags=["dataset"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["simulation"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(conflicts.router, prefix="/api/conflicts", tags=["conflicts"])
app.include_router(healing.router, prefix="/api/healing", tags=["healing"])
app.include_router(benchmarks.router, prefix="/api/benchmarks", tags=["benchmarks"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])

@app.get("/")
def root():
    return {"message": "Welcome to CoReOS API"}
