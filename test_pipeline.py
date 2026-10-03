
from dotenv import load_dotenv
load_dotenv()

from datetime import time
from react_loop import ReactAgent
from models import CognitiveHMM, Observation
from scheduler import plan_day
#from adaptive_pilot import APQLearning, Action

def run_project_pipeline():
    print("=" * 60)
    print("STEP 1 & 2: ReAct Parsing & Z3 Verification (Slides 1-3)")
    print("=" * 60)
    agent = ReactAgent()
    user_input = "Finish ML essay due at noon, sync with team, and do laundry."
    is_sat, tasks, msg = agent.process_n_vefify(user_input)
    print(f"Verification Result: {'SAT' if is_sat else 'UNSAT'}")
    for log in agent.context_history:
        print("  ", log)

    print("\n" + "=" * 60)
    print("STEP 3: HMM Cognitive Perception Filter (Slide 5)")
    print("=" * 60)
    hmm = CognitiveHMM()
    # User submits a check-in: FATIGUED
    hmm.forward_update(Observation.Fatigue)
    energy_scalar = hmm.get_expected_energy()
    dominant_stamina = hmm.get_dominant_state()
    print(f"Updated HMM Beliefs: {np_round(hmm.belief, 3)}")
    print(f"Dominant Stamina: {dominant_stamina.name}")
    print(f"Dynamic Energy Capacity E(t): {energy_scalar:.3f}")

    print("\n" + "=" * 60)
    print("STEP 4: A* Minimum-Mismatch Planning (Slide 4)")
    print("=" * 60)
    schedule, feasible = plan_day(tasks, current_energy=energy_scalar)
    print(f"A* Search Succeeded: {feasible}")
    for task, start_time in schedule:
        print(f"  {start_time.strftime('%H:%M')} - {task.name} (Load: {task.cognitive_load}, Deadline: {task.deadline})")

    print("\n" + "=" * 60)
    print("STEP 5: Runtime Slippage & Q-Learning Recovery (Slide 6)")
    print("=" * 60)
    print("NOT WIRED IN -- adaptive_pilot.py (the Q-learning reschedule")
    print("policy can be done later.")

def np_round(arr, decimals):
    return [round(float(x), decimals) for x in arr]

if __name__ == "__main__":
    run_project_pipeline()
