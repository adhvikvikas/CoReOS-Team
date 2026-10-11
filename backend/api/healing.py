from fastapi import APIRouter
from backend.state import state_store

router = APIRouter()

@router.get("/")
def get_healing_metrics():
    return state_store.get_healing_analytics()
