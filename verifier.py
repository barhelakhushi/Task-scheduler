#Verifier for non-overlap, deadline bounds, 'and maybe buffers between heavy tasks'

from __future__ import annotations
from typing import List, Tuple, Optional
from datetime import time
import z3
from models import Task

def _to_min(t: time) -> int:
    return t.hour * 60 + t.minute

def verify_schedule_constraints(
    tasks: List[Task],
    day_start: time = time(8, 0),
    day_end: time = time(22, 0)
) -> Tuple[bool, Optional[str], Optional[List[str]]]:
    """
    Formally checks feasibility via Z3 QF_LIA.
    Returns: (is_sat, error_message, conflict_task_ids)
    """
    solver = z3.Solver()
    start_bound = _to_min(day_start)
    end_bound = _to_min(day_end)
    start_vars = {t.id: z3.Int(f"start_{t.id}") for t in tasks}
    
    #1 day boundary and hard deadline constraints
    for t in tasks:
        s_i = start_vars[t.id]
        dur = t.duration_min
        
        solver.add(s_i >= start_bound)
        solver.add(s_i + dur <= end_bound)
        
        if t.deadline is not None:
            track_var = z3.Bool(f"deadline_{t.id}")
            solver.assert_and_track(s_i + dur <= _to_min(t.deadline), track_var)
            
        if t.fixed_start is not None:
            solver.add(s_i == _to_min(t.fixed_start))

    #2 Pairwise non-overlap and cognitive load spacing
    task_list = list(tasks)
    for i in range(len(task_list)):
        for j in range(i + 1, len(task_list)):
            t1, t2 = task_list[i], task_list[j]
            s1, s2 = start_vars[t1.id], start_vars[t2.id]
            d1, d2 = t1.duration_min, t2.duration_min
            
            #No overlap
            t1_before_t2 = (s1 + d1 <= s2)
            t2_before_t1 = (s2 + d2 <= s1)
            
            #Pacing: if both load >= 4, require >= 15 min rest gap
            #Can be perhaps switched with shuffing -> heavy , light , heavy
            if t1.cognitive_load >= 4 and t2.cognitive_load >= 4:
                t1_before_t2 = (s1 + d1 + 15 <= s2)
                t2_before_t1 = (s2 + d2 + 15 <= s1)
                
            solver.add(z3.Or(t1_before_t2, t2_before_t1))

    if solver.check() == z3.sat:
        return True, None, None
    else:
        # Extract infeasible tasks for the ReAct renegotiation loop
        #core = [str(clause).replace("track_","") for clause in s.unsat_core()]
        core = [str(clause) for clause in solver.unsat_core()]
        return False,"SMT Solver proved schedule infeasible", core
