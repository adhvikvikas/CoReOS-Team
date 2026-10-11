from fastapi import APIRouter
from backend.state import state_store

router = APIRouter()

@router.get("/")
def get_conflict_analysis():
    return state_store.get_conflict_analytics()
