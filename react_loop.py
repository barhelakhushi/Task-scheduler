""" for llm decomposition , smt gated reflection """


from __future__ import annotations
import json
import os
from openai import OpenAI
from typing import List, Tuple
from datetime import time
from models import Task, Importance
from verifier import verify_schedule_constraints


llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "your_openai_api_key"))

class ReactAgent:
    def __init__(self, llm_client= None):
        self.context_history: List[str] = []
        self.llm_client = llm_client
        
    #will replace later -> used incase of no API key
    #def mock_llm_parse(self, text: str) -> List[Task]:
    # 1. Logs the ReAct reasoning step to agent history
     #   self.context_history.append("Thought: Decomposing user input into typed Task schemas.")
    
    # 2. Returns structured Task models with typed priorities, loads, and deadlines
      #  tasks = [
       #     Task(id="t1", name="ML Assignment", cognitive_load=5, duration_min=90, imp=Importance.CRITICAL, deadline=time(12, 0)),
        #    Task(id="t2", name="Team Sync", cognitive_load=3, duration_min=30, imp=Importance.HIGH, deadline=time(13, 0)),
         #   Task(id="t3", name="Laundry", cognitive_load=1, duration_min=45,    imp=Importance.LOW, deadline=time(18, 0)),
    
    
    # 3. Logs the action result
        #self.context_history.append(f"Action: Extracted {len(tasks)} tasks.")
        #return tasks
        
    def parse_user_input(self, text: str) -> List[Task]:
        """Parses user input into dynamic Task objects."""
        
        if self.llm_client:
          response = self.llm_client.chat.completions.create(
              model="gpt-4o-mini",
              messages=[
                  {"role": "system", "content": "Extract tasks into JSON format."},
                  {"role": "user", "content": text},
              ],
          )
        self.context_history.append(
            f"Thought: Parsing user input into Task schemas: '{text}'"
        )

        tasks = []
        # Split input by commas or newlines if multiple tasks are entered
        raw_items = [item.strip() for item in re.split(r"[,;\n]", text) if item.strip()]

        for item in raw_items:
          # Generate a unique task ID
          task_id = f"t_{uuid.uuid4().hex[:6]}"

          # Extract simple deadline if mentioned (e.g. '12:00', '17:30', '5 PM')
          deadline_obj = None
          time_match = re.search(r"(\d{1,2}):(\d{2})", item)
          if time_match:
            h, m = int(time_match.group(1)), int(time_match.group(2))
            deadline_obj = time(h, m)

          # Extract duration if specified (e.g. '30m', '2 hrs', '90 min')
          dur_min = 30
          dur_match = re.search(r"(\d+)\s*(m|min|hour|hr|hrs)", item, re.IGNORECASE)
          if dur_match:
            val, unit = int(dur_match.group(1)), dur_match.group(2).lower()
            dur_min = val * 60 if "h" in unit else val

          # Default to MEDIUM importance unless keywords are present
          imp_enum = Importance.MEDIUM
          if re.search(r"\b(critical|urgent|must|due soon)\b", item, re.IGNORECASE):
            imp_enum = Importance.CRITICAL
          elif re.search(r"\b(high|important)\b", item, re.IGNORECASE):
            imp_enum = Importance.HIGH
          elif re.search(r"\b(low|someday|optional)\b", item, re.IGNORECASE):
            imp_enum = Importance.LOW

          tasks.append(
              Task(
                  id=task_id,
                  name=item,
                  cognitive_load=3,  # Default cognitive load
                  duration_min=dur_min,
                  imp=imp_enum,
                  deadline=deadline_obj,
              )
          )

        self.context_history.append(f"Action: Extracted {len(tasks)} dynamic task(s).")
        return tasks
    
    def process_n_verify(self, user_prompt: str) -> Tuple[bool, List[Task],str]:
        tasks = self.parse_user_input(user_prompt)   #mock_llm_parse(user_prompt)
        
        is_sat, err, conflict_id = verify_schedule_constraints(tasks)
        
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
                

