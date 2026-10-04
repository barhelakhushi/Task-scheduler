import unittest
from datetime import time
from models import Task, Importance
from verifier import verify_schedule_constraints

class TestVerifier(unittest.TestCase):

    def test_feasible_schedule_sat(self):
        tasks = [
            Task(id="t1", name="Task 1", imp=Importance.HIGH, cognitive_load=3, duration_min=60, deadline=time(12, 0)),
            Task(id="t2", name="Task 2", imp=Importance.MEDIUM, cognitive_load=2, duration_min=60, deadline=time(15, 0))
        ]
        is_sat, error_msg, conflict_core = verify_schedule_constraints(tasks)
        self.assertTrue(is_sat)
        self.assertIsNone(error_msg)

    def test_infeasible_schedule_unsat(self):
        # Two heavy 3-hour tasks due at 9:00 AM starting at 8:00 AM -> Impossible schedule
        tasks = [
            Task(id="t1", name="Heavy 1", imp=Importance.CRITICAL, cognitive_load=5, duration_min=180, deadline=time(9, 0)),
            Task(id="t2", name="Heavy 2", imp=Importance.CRITICAL, cognitive_load=5, duration_min=180, deadline=time(9, 0))
        ]
        is_sat, error_msg, conflict_core = verify_schedule_constraints(tasks)
        self.assertFalse(is_sat)
        self.assertIsNotNone(error_msg)

if __name__ == "__main__":
    unittest.main()
