import unittest
from datetime import time
from models import Task, Importance
from scheduler import plan_day, plan_day_robust

class TestScheduler(unittest.TestCase):

    def test_plan_day_success(self):
        tasks = [
            Task(id="t1", name="Morning Prep", imp=Importance.HIGH, cognitive_load=2, duration_min=30),
            Task(id="t2", name="Deep Work", imp=Importance.CRITICAL, cognitive_load=4, duration_min=90, deadline=time(12, 0))
        ]
        ordered_schedule, feasible = plan_day(tasks, current_energy=0.8)
        self.assertTrue(feasible)
        self.assertEqual(len(ordered_schedule), 2)

    def test_plan_day_robust_overloaded(self):
        # Exceeds total available daylight hours (10 hours + 10 hours)
        tasks = [
            Task(id="t1", name="Task A", imp=Importance.CRITICAL, cognitive_load=4, duration_min=600),
            Task(id="t2", name="Task B", imp=Importance.CRITICAL, cognitive_load=4, duration_min=600),
            Task(id="t3", name="Low Priority", imp=Importance.LOW, cognitive_load=1, duration_min=120)
        ]
        ordered_schedule, dropped_tasks = plan_day_robust(tasks, current_energy=0.5)
        self.assertTrue(len(dropped_tasks) > 0)

if __name__ == "__main__":
    unittest.main()
