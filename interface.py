
"""
Made using LLM
Streamlit interface: ReAct parsing -> Z3 verification -> HMM
check-in -> A* schedule. Wraps the pipeline exercised in
test_pipeline.py; no new logic, just a UI on top of it.
"""
from dotenv import load_dotenv
load_dotenv()  #
 
from models import CognitiveHMM, Observation
from react_loop import ReactAgent
from scheduler import plan_day_robust
 
import streamlit as st
 
st.set_page_config(page_title="ADHD Day Scheduler", layout="wide")
st.title("ADHD Day Scheduler")
 
if "agent" not in st.session_state:
    st.session_state.agent = ReactAgent()
if "hmm" not in st.session_state:
    st.session_state.hmm = CognitiveHMM()
if "tasks" not in st.session_state:
    st.session_state.tasks = []
 
st.subheader("1. Describe your day")
st.caption("Uses your ANTHROPIC_API_KEY if set in .env; otherwise falls "
           "back to a fixed demo task list (see react_loop.py).")
user_input = st.text_area(
    "What do you need to get done today?",
    placeholder="e.g. Finish ML essay due at noon, sync with team, do laundry",
)
if st.button("Parse & verify"):
    is_sat, tasks, msg = st.session_state.agent.process_n_vefify(user_input)
    st.session_state.tasks = tasks
    (st.success if is_sat else st.warning)(msg)
    with st.expander("Agent reasoning trace"):
        for log in st.session_state.agent.context_history:
            st.write(log)
 
st.subheader("2. Check in — how are you feeling right now?")
obs_choice = st.selectbox("Current state", [o.name for o in Observation])
if st.button("Log check-in"):
    st.session_state.hmm.forward_update(Observation[obs_choice])
    st.write(f"Belief (HighFocus, Baseline, Burnout): "
             f"{[round(float(x), 3) for x in st.session_state.hmm.belief]}")
    st.write(f"Dominant state: {st.session_state.hmm.get_dominant_state().name}")
 
st.subheader("3. Today's schedule")
if st.session_state.tasks:
    energy = st.session_state.hmm.get_expected_energy()
    st.caption(f"Current estimated energy (from HMM): {energy:.2f}")
    ordered, dropped = plan_day_robust(st.session_state.tasks, current_energy=energy)
 
    if dropped:
        st.warning("Didn't fit today:")
        for t, reason in dropped:
            st.write(f"- **{t.name}**: {reason}")
 
    for task, start in ordered:
        st.write(f"**{start.strftime('%H:%M')}** — {task.name} (load {task.cognitive_load})")
else:
    st.write("_Parse some tasks above first._")
 
st.divider()
st.caption("Adaptive-pilot (RL reschedule-on-slippage) is not wired in yet — "
           "see README limitations.")
 
