

"""
Made using LLM
Streamlit interface: ReAct parsing -> Z3 verification -> HMM
check-in -> A* schedule. Wraps the pipeline exercised in
test_pipeline.py; no new logic, just a UI on top of it.
"""

import unittest
from database import init_db, get_all_active_tasks

 
class TestDatabaseModule(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_get_tasks(self):
        tasks = get_all_active_tasks()
        self.assertIsInstance(tasks, list)

