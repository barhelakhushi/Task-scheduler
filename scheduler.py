""" UCS using MIN-HEAP 

State = (frozenset of remaining free-task ids, current_time_in_minutes).
Transition cost = energy/cognitive-load mismatch at the time a task
would be scheduled. Hard deadlines and end-of-day constraints , voilating brach pruned


"""
from __future__ import annotations
import heapq
from dataclasses import dataclass,field
from datetime import time
from typing import Dict, FrozenSet, List, Tuple, Callable, Optional
from models import Task

#from energy import energy_at

DAY_START = time(8, 0)   #Future: Can take inputs from user
DAY_END = time(22, 0)


def _to_minutes(t: time) -> int:
    return t.hour* 60 + t.minute


def _to_time(m: int) -> time:
    m = m % (24* 60)
    return time(m // 60, m % 60)


def _mismatch_cost(task: Task, start: time, current_energy: Optional[float]= None) -> float:   #capacity_fn: Optional[Callable[[int], float]

    """Higher when a heavy-load task lands during a low-energy slot."""
    required= task.cognitive_load / 5.0
    #initial = energy_at(start)
    ##using HMM provided capacity
    
    available= current_energy if current_energy is not None else 0.55
    #else:
     #   available = 0.55 # baseline
    mismatch= max(0.0, required - available)
    return task.cognitive_load * mismatch
    
def _admissible_heuristic(remaining_ids: FrozenSet[str], tasks_by_id: Dict[str, Task]) -> float:
    """
    Admissible Heuristic h(n): Sum of optimistic minimum mismatch costs
    for remaining high-load tasks (assuming best case capacity = 1.0).
    Satisfies h(n) <= h*(n).
    """
    # Lower bound mismatch assuming peak energy (capacity = 1.0) is 0.0,
    # but can be tightened if specific constraints apply.
    return 0.0


@dataclass(order=True)
class _Node:
    f: float
    g: float = field(compare=False, default=0.0)
    time_min: int = field(compare=False, default=0)
    remaining: FrozenSet[str] = field(compare=False, default_factory=frozenset)
    schedule: Tuple[Tuple[str, int], ...] = field(compare=False, default=())
    

def _fixed_commitments(
    current_min: int,
    task_duration: int,
    fixed_intervals: List[Tuple[int, int]] ) -> int:
    """ Pushes `current_min` forward if a task execution window overlaps with any locked fixed-start appointment."""
    
    adjusted_start = current_min
    for fix_start, fix_end in fixed_intervals:
        # Check for overlap
        if adjusted_start < fix_end and (adjusted_start + task_duration) > fix_start:
            #advance start to after the fixed commitment
            adjusted_start = fix_end
    return adjusted_start


def plan_day(tasks: List[Task], current_energy:Optional[float] = None) -> Tuple[List[Tuple[Task, time]], bool]:
    """Return (ordered [(task, start_time)], feasible).

    feasible =False ->  no ordering of the free tasks can satisfy
    every hard deadline within the day window.
    Find global min - mismatch for free tasks
    Return -> ordered, feasible
    """
    tasks_by_id = {t.id: t for t in tasks}
    fixed_tasks = [t for t in tasks if t.fixed_start is not None]
    free_ids = frozenset(t.id for t in tasks if t.fixed_start is None)
    
    fixed_intervals: List[Tuple[int, int]] = sorted([
        (_to_minutes(t.fixed_start), _to_minutes(t.fixed_start) + t.duration_min)
        for t in fixed_tasks]
        )

    start_min = _to_minutes(DAY_START)
    end_min = _to_minutes(DAY_END)

    start_node = _Node(f=0.0, g=0.0, time_min=start_min, remaining=free_ids, schedule=())
    frontier: List[_Node] = [start_node]
    best_g: Dict[Tuple[FrozenSet[str], int], float] = {(free_ids, start_min): 0.0}

    while frontier:
        node = heapq.heappop(frontier)
        key = (node.remaining, node.time_min)
        if best_g.get(key, float("inf")) < node.g:
            continue  #stale queue entry

        if not node.remaining:
            ordered = [(tasks_by_id[tid], _to_time(t)) for tid, t in node.schedule]
            return ordered, True

        for tid in node.remaining:
            task = tasks_by_id[tid]
            
            #start_t =_to_time(node.time_min)
            actual_start_min = _fixed_commitments(node.time_min, task.duration_min, fixed_intervals )
            finish_min = actual_start_min + task.duration_min

            if finish_min > end_min:
                continue  # exceeds end of day
            if task.deadline is not None and finish_min > _to_minutes(task.deadline):
                continue  # would miss a hard deadline: illegal

            # step mismatch and heuristic
            cost = _mismatch_cost(task,actual_start_min, current_energy)
            new_g = node.g + cost
            new_remaining = node.remaining - {tid}
            new_h = _admissible_heuristic(new_remaining, tasks_by_id)
            new_f = new_g + new_h
            new_key = (new_remaining, finish_min)

            if new_g < best_g.get(new_key, float("inf")):
                best_g[new_key] = new_g
                new_node = _Node(
                    f=new_f,  # h = 0
                    g=new_g,
                    time_min=finish_min,
                    remaining=new_remaining,
                    schedule=node.schedule + ((tid, actual_start_min),),
                )
                heapq.heappush(frontier, new_node)

    return [], False


def _fits_individually(task: Task) -> bool:
    #check if every task fits in teh day bound
    if task.fixed_start is not None:
        return True
    limit = _to_minutes(task.deadline) if task.deadline is not None else _to_minutes(DAY_END)
    return _to_minutes(DAY_START) + task.duration_min <= limit


def plan_day_robust(tasks: List[Task], current_energy:Optional[float] = None) -> Tuple[List[Tuple[Task, time]], List[Tuple[Task, str]]]:
    """drops task that cant fit and iterate over lowest- priority task untill feasible schedulefn
    Returns (ordered schedule, [(dropped_task, reason), ...])
    """
    dropped: List[Tuple[Task, str]] = []
    candidates: List[Task] = []

    for t in tasks:
        if t.fixed_start is None and not _fits_individually(t):
            limit_desc = f"deadline {t.deadline}" if t.deadline else "end of day"
            dropped.append((
                t,
                f"needs {t.duration_min} min but can't fit before {limit_desc} "
                f"even if started immediately -- impossible regardless of ordering",
            ))
        else:
            candidates.append(t)

    while candidates:
        ordered, feasible = plan_day(candidates, current_energy=current_energy)
        if feasible:
            return ordered, dropped
        # lowest priority first; among ties, drop the longer task
        # frees more time, more likely to resolve infeasibility in
        # fewer drops.
        worst = min(candidates,key= lambda t:(t.priority, -t.duration_min))
        candidates.remove(worst)
        dropped.append((worst, "didn't fit alongside the other remaining tasks today"))

    return [], dropped
