from fastapi import APIRouter
from pydantic import BaseModel
from backend.state import state_store

router = APIRouter()

class SimulationRequest(BaseModel):
    num_processes: int
    workload_type: str
    policy_mode: str
    seed: int
    sim_quantum: float

@router.get("/latest")
def get_latest_simulation():
    state_store.initialize_defaults()
    return {
        "config": state_store.workload_info,
        "result": state_store.latest_simulation_result,
        "is_completed": state_store.latest_simulation_result is not None
    }

@router.post("/run")
def run_simulation(req: SimulationRequest):
    return state_store.run_and_record_simulation(
        workload_type=req.workload_type,
        num_processes=req.num_processes,
        policy_mode=req.policy_mode,
        seed=req.seed,
        sim_quantum=req.sim_quantum
    )
