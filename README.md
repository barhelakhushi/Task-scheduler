## Autonomous Task Scheduler
An intelligent task scheduling assistant designed to reduce decision fatigue and make workloads more manageable for individuals with ADHD.
Built with Python, Streamlit, ReAct Agent Architecture, Z3 SMT Solver, and SQLite.
Key Features
Natural Language Task Input — Extracts task details such as duration, deadline, importance, and cognitive load.
Smart Scheduling — Creates schedules while considering deadlines, available time, and task constraints.
SMT Verification — Uses Z3 to verify whether a schedule is mathematically feasible.
Autonomous Rescheduling — Removes lower-priority tasks when the workload cannot fit within the available time.
SQLite Database — Stores tasks persistently across sessions.
ADHD-Friendly Interface — Simple Streamlit dashboard for adding, editing, and viewing tasks.
### Project Structure

```
Final_project/
- interface.py      # Streamlit interface
-  react_loop.py     # ReAct agent and task parsing
- verifier.py       # Z3 schedule verification
- database.py       # SQLite database operations
- models.py         # Task and importance definitions
- scheduler.py      # Task scheduling algorithms
- requirements.txt  # Project dependencies
- tests             # Diffent test files
- README.md 
```

#### Tools Used
Language: Python 3.10+
UI: Streamlit
Agent: ReAct Agent Architecture
Verification: Z3 SMT Solver
Database: SQLite
Environment: python-dotenv


### Getting Started
1. Create a virtual environment
python3 -m venv auto_ai
source auto_ai/bin/activate
2. Install dependencies
pip install -r requirements.txt
3. Configure API Key
Create a .env file in the project folder:
OPENAI_API_KEY=your_api_key_here
4. Run the application
streamlit run interface.py
The application will open in your browser.

