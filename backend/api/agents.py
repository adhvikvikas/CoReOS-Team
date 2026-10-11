from fastapi import APIRouter
from backend.state import state_store

router = APIRouter()

@router.get("/")
def get_agent_decisions():
    return state_store.get_agent_records()
