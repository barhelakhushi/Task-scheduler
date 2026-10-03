""" task perception 
Forward Algo belief filter updating hidden mental stamina from noisy check-in observations and supplying dynamic energy E(t)
states = {HighFocus,Baseline,Burnout}.
obs_space = {Energized,Neutral,Fatigued,Frozen}
    B =[0.30,0.60,0.10] not overly optimistic or uniform

"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from enum import IntEnum
from typing import Dict


#### task schedule models first attempt
class Importance(IntEnum):
    FUTURE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    
#class Priority(IntEnum):
    #FUTURE = 0.5
    #LOW = 1
    #MEDIUM = 2
    #HIGH = 3
    #sCRITICAL = 4
    
    
#class COG_LOAD:

@dataclass
class Task:
    id: str
    name: str
    imp: Importance
    cognitive_load: int     #1 - 5 (heavy)
    duration_min: int      #estimated time
    priority: Optional[int] = None     #could change accordingto time & importance
    deadline: Optional[time] = None
    fixed_start: Optional[time] = None   # set for immovable commitments
                                          # (class, meds, therapy) — the
                                          # scheduler must never move these

    def __post_init__(self) -> None:
        if not (1 <= self.cognitive_load <= 5):
            raise ValueError(f"cognitive_load must be 1-5, got {self.cognitive_load}")
        if self.duration_min <= 0:
            raise ValueError("duration_min must be positive")
            
    def dynamic_priority(self, current_time_min: int) -> int:
        """
        Computes urgency score based on time remaining until deadline.
        Priority = Base Importance + Urgency 
        """
        base_score = int(self.imp) * 10 #10, 20, 30, 40

        if self.deadline is None:
            return base_score
        dl_min = self.deadline.hour * 60 + self.deadline.minute
        time_left = dl_min - current_time_min
        slack = time_left - self.duration_min

        
        if slack <= 30:
            urgency_surge = 50       # imminent deadline
        elif slack <= 90:
            urgency_surge = 25
        elif slack <= 180:
            urgency_surge = 10       # due in a few hours
        else:
            urgency_surge = 0
        return base_score + urgency_surge
       



#cognitiev states model
class CognitiveState(IntEnum):
    HIGH_FOCUS = 0
    BASELINE = 1
    BURNOUT = 2 #Just high cog load
    
class Observation(IntEnum):
    Energised = 0
    Neutral = 1
    Fatigue = 2
    Frozen = 3
    
class CognitiveHMM:
    def __init__(self):
        #b = (p_high, p_base, burnout)
        self.belief = np.array([0.30, 0.60, 0.10], dtype=float)
        self.T = np.array([
            [0.70, 0.25, 0.05], #from high
            [0.15, 0.70, 0.15],  #from base
            [0.05, 0.35, 0.60]  #from burtout
            ], dtype=float)
        self.O = np.array([[0.65, 0.30, 0.04, 0.01],
        [0.15, 0.60, 0.20, 0.05],
        [0.02, 0.18, 0.50, 0.30]])
        self.weights = np.array([1.00, 0.55, 0.15], dtype=float)
    
    def forward_update(self, obs: Observation):
        """ forward algo 
        predict: B_t = t^t * b_(t-1)
        update: B_t = 
        """
        predicted = self.T.T @ self.belief
        likelihood = self.O[:, obs.value]
        unnormalized = likelihood * predicted
        norm_cost = np.sum(unnormalized)
        
        if norm_cost > 0:
            self.belief = unnormalized/ norm_cost
    def get_expected_energy (self) -> float:
        """ scalar capacitty to feed to a*"""
        return(float (np.dot(self.belief , self.weights)))
    
    def get_dominant_state(self) -> CognitiveState:
        return CognitiveState(int(np.argmax(self.belief)))
        
