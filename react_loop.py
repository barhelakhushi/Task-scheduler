""" for llm decomposition , smt gated reflection """


from __future__ import annotations
import json
from typing import List, Tuple
from datetime import time
from models import Task, Importance
from verifier import verify_schedule_constraints



class ReactAgent:
    def __init__(self):
        self.context_history: List[str] = []
        
    #will replace later
    def mock_llm_parse(self, text: str) -> List[Task]:
    # 1. Logs the ReAct reasoning step to agent history
        self.context_history.append("Thought: Decomposing user input into typed Task schemas.")
    
    # 2. Returns structured Task models with typed priorities, loads, and deadlines
        tasks = [
            Task(id="t1", name="ML Assignment", cognitive_load=5, duration_min=90, imp=Importance.CRITICAL, deadline=time(12, 0)),
            Task(id="t2", name="Team Sync", cognitive_load=3, duration_min=30, imp=Importance.HIGH, deadline=time(13, 0)),
            Task(id="t3", name="Laundry", cognitive_load=1, duration_min=45,    imp=Importance.LOW, deadline=time(18, 0)),
    ]
    
    # 3. Logs the action result
        self.context_history.append(f"Action: Extracted {len(tasks)} tasks.")
        return tasks
    
    def process_n_vefify(self, user_prompt: str) -> Tuple[bool, List[Task],str]:
        tasks = self.mock_llm_parse(user_prompt)
        
        is_sat, err, conflicts_id = verify_schedule_constraints(tasks)
        
        if is_sat:
            self.context_history.append("Obs: Z3 verified QF_LIA constraints SAT.")
            return True, tasks, "Verified feasible."
        #react on unsat
        
        self.context_history.append(f"Obs:Z3 returned UNSAT. Conflict core {conflict_ids} ")
        self.context_history.append("Thought: Workload is mathematically infeasible. Initiating renegotiation")
        #drop lowest imp task
        reduced_tasks =[t for t in tasks if t.imp != Importance.LOW]
        
        #re-verify
        reduced_sat, _, _ = verify_schedule_constraints(reduced_tasks)
        if reduced_sat:
            self.context_history.append("Observation: Reduced workload verified SAT.")
            return False, reduced_tasks, f"UNSAT: Resolved by dropping low priority tasks ({conflict_ids})."
        
        return False, [], "UNSAT: Workload remains infeasible even after dropping low priority tasks."
        

