"""
CoReOS Safety Constraints Engine
Enforces hard safety invariants: bounds on allocations, policy validity,
and non-negotiable capacity limits.
"""

from typing import Dict, Any, Tuple


VALID_CPU_POLICIES = {"ROUND_ROBIN", "FCFS", "PRIORITY", "SRTF"}
VALID_IO_POLICIES = {"FCFS", "SSTF", "SCAN"}
MIN_QUANTUM = 1.0
MAX_QUANTUM = 32.0


def validate_safety_constraints(
    decision: Dict[str, Any],
    system_state: Dict[str, Any],
    total_memory_mb: float = 16384.0
) -> Tuple[Dict[str, Any], bool, str]:
    """
    Validates and clamps candidate actions to prevent illegal states.
    Returns: (sanitized_decision, is_modified, safety_note)
    """
    sanitized = dict(decision)
    modified = False
    notes = []

    # 1. CPU Policy & Quantum Safety
    cpu_policy = sanitized.get("cpu_policy", "ROUND_ROBIN")
    if cpu_policy not in VALID_CPU_POLICIES:
        sanitized["cpu_policy"] = "ROUND_ROBIN"
        modified = True
        notes.append(f"Invalid CPU policy '{cpu_policy}' reverted to ROUND_ROBIN")

    quantum = float(sanitized.get("cpu_quantum", 4.0))
    if quantum < MIN_QUANTUM or quantum > MAX_QUANTUM:
        clamped_q = max(MIN_QUANTUM, min(MAX_QUANTUM, quantum))
        sanitized["cpu_quantum"] = clamped_q
        modified = True
        notes.append(f"Quantum {quantum} clamped to {clamped_q}")

    # 2. Memory Reclamation Bounds
    reclaim_mb = float(sanitized.get("memory_reclaim_target", 0.0))
    if reclaim_mb < 0.0:
        sanitized["memory_reclaim_target"] = 0.0
        modified = True
        notes.append("Negative memory reclaim clamped to 0.0")
    elif reclaim_mb > total_memory_mb:
        sanitized["memory_reclaim_target"] = total_memory_mb * 0.5
        modified = True
        notes.append(f"Excessive memory reclaim clamped to {total_memory_mb * 0.5} MB")

    # 3. I/O Policy Validity
    io_policy = sanitized.get("io_policy", "FCFS")
    if io_policy not in VALID_IO_POLICIES:
        sanitized["io_policy"] = "FCFS"
        modified = True
        notes.append(f"Invalid I/O policy '{io_policy}' reverted to FCFS")

    safety_note = "; ".join(notes) if notes else "All hard constraints satisfied"
    return sanitized, modified, safety_note
