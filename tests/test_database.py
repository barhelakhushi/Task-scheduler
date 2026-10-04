
import unittest
import os
from datetime import time
from models import Task, Importance
import database

class TestDatabase(unittest.TestCase):

    def setUp(self):
        database.DB_FILE = "test_tasks.db"
        if os.path.exists("test_tasks.db"):
            os.remove("test_tasks.db")
        database.init_db()

    def tearDown(self):
        if os.path.exists("test_tasks.db"):
            os.remove("test_tasks.db")

    def test_save_and_retrieve_task(self):
        task = Task(id="db_t1", name="Database Task", imp=Importance.HIGH, cognitive_load=3, duration_min=30, deadline=time(14, 0))
        database.save_task_to_db(task)
        
        active_tasks = database.get_all_active_tasks()
        self.assertEqual(len(active_tasks), 1)
        self.assertEqual(active_tasks[0][1], "Database Task")

    def test_mark_task_status(self):
        task = Task(id="db_t2", name="Completion Test", imp=Importance.LOW, cognitive_load=1, duration_min=15)
        database.save_task_to_db(task)
        
        database.mark_task_status("db_t2", "completed")
        active_tasks = database.get_all_active_tasks()
        self.assertEqual(len(active_tasks), 0)

if __name__ == "__main__":
    unittest.main()
