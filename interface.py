
import os
import pandas as pd
import streamlit as st
from datetime import time
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

from models import CognitiveHMM, Observation, Importance, Task
from react_loop import ReactAgent
from scheduler import plan_day_robust
from database import (init_db, get_all_active_tasks, mark_task_status, update_task_details, update_task_order, delete_tasks, save_task_to_db, clear_db)

 

try:
    init_db()
except Exception as e:
    st.error(f" Failed to initialize Database: {e}")
    
st.set_page_config(page_title="Task_ Scheduler", layout="wide")

api_key = os.getenv("OPENAI_API_KEY")
if "agent" not in st.session_state:
  llm_client = OpenAI(api_key=api_key) if api_key else None
  st.session_state.agent = ReactAgent(llm_client=llm_client)

 
if "agent" not in st.session_state:
    st.session_state.agent = ReactAgent(llm_client=your_llm_client)
if "hmm" not in st.session_state:
    st.session_state.hmm = CognitiveHMM()
#if "tasks" not in st.session_state:
 #   st.session_state.tasks = []
if "pending_draft" not in st.session_state:
    st.session_state.pending_draft = None
if "clarification_msg" not in st.session_state:
    st.session_state.clarification_msg = ""
      
#page
st.title("Task Scheduler")

tasks = get_all_active_tasks()
if not tasks:
    st.info("No active tasks in database. Enter a task below to get started.")
else:
    #1A. Data Editor & Bulk Operations Table
    df = pd.DataFrame(
        tasks,
        columns=[
            "ID",
            "Name",
            "Importance",
            "Load",
            "Duration (min)",
            "Deadline",
            "Priority",
            "Status",
            "Order",
        ],
    )
    df.insert(0, "Select", False)

    edited_df = st.data_editor(
        df,
        column_config={
        "Select": st.column_config.CheckboxColumn("Select"),
        "ID": None,
        "Status": None,
        "Order": None,
        "Priority": None,
        "Load": st.column_config.NumberColumn("Load (1-5)", disabled=True),
        "Name": st.column_config.TextColumn("Task Name", disabled=True),
        "Duration (min)": st.column_config.NumberColumn(
            "Duration (min)", min_value=5, max_value=480, step=5
        ),
        "Importance": st.column_config.SelectboxColumn(
            "Importance",
            options=["CRITICAL", "HIGH", "MEDIUM", "LOW", "FUTURE"],
        ),
        "Deadline": st.column_config.TextColumn("Deadline (HH:MM)"),
    },
        hide_index=True,
        use_container_width=True,
        key="task_data_editor",
    )

    
    selected_rows = edited_df[edited_df["Select"] == True]
    selected_ids = selected_rows["ID"].tolist()

    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1.5, 1.5, 1.5, 3])

    with btn_col1:
        if st.button("Done", type="primary", disabled=len(selected_ids) == 0):
            for t_id in selected_ids:
                mark_task_status(t_id, status="completed")
            st.success(f"Marked {len(selected_ids)} task(s) done!")
            st.rerun()

    with btn_col2:
        if st.button("Delete ", type="secondary", disabled=len(selected_ids) == 0):
            delete_tasks(selected_ids)
            st.warning(f"Deleted {len(selected_ids)} task(s)!")
            st.rerun()

    with btn_col3:
        if st.button("Save Edits"):
            for idx_row, row in edited_df.iterrows():
                orig_row = df.iloc[idx_row]
                if (
                    row["Duration (min)"] != orig_row["Duration (min)"]
                    or row["Deadline"] != orig_row["Deadline"]
                    or row["Importance"] != orig_row["Importance"]
                ):
                    update_task_details(
                        task_id=row["ID"],
                        new_duration=int(row["Duration (min)"]),
                        new_deadline=str(row["Deadline"]),
                        new_importance=str(row["Importance"]),
                    )
            st.success("Updated task details saved!")
            st.rerun()
    with btn_col4:
        if st.button("Clear DB", type="secondary"):
            clear_db()
            st.warning("All tasks cleared from database!")
            st.rerun()
            
    #for reshuffle
    with st.expander("Reset Order", expanded=False):
        st.caption("Reorder tasks below. Click arrows to update sequence priority in SQLite.")
        task_ids = [t[0] for t in tasks]

        for idx, task_row in enumerate(tasks):
            t_id, t_name, t_imp, t_load, t_dur, t_dl = task_row[:6]
            c_label, c_up, c_down = st.columns([4, 1, 1])

            with c_label:
                st.write(
                    f"**{idx + 1}. {t_name}** | Imp: `{t_imp}` | Dur: `{t_dur}m` | Due: `{t_dl or 'None'}`"
                )
            with c_up:
                if idx > 0 and st.button("UP", key=f"up_{t_id}"):
                    task_ids[idx], task_ids[idx - 1] = task_ids[idx - 1], task_ids[idx]
                    update_task_order(task_ids)
                    st.rerun()
            with c_down:
                if idx < len(tasks) - 1 and st.button("DOWN", key=f"down_{t_id}"):
                    task_ids[idx], task_ids[idx + 1] = task_ids[idx + 1], task_ids[idx]
                    update_task_order(task_ids)
                    st.rerun()

st.divider()


###section for input
#input section
st.subheader("1. Describe your day")

if st.session_state.pending_draft:
    st.warning(f" **Clarification Requested:** {st.session_state.clarification_msg}")
    
st.caption("Enter the task you need to complete along with thier importance level from 1-5 , expected time it will take to finish, and deadline if you want.")
with st.form(key="schedule_form", clear_on_submit=True):
    user_input = st.text_input(
    "What do you need to get done today?",
    placeholder="e.g. Finish Pol paper due at noon, Assignment by midnight(due today), Lunch at 3 PM, do laundry. Allot 2 hrs for pol paper ")
    submit_button = st.form_submit_button("Schedule Day", type="primary")
    
    
if submit_button and user_input and user_input.strip():   # handle_schedule_submission()
    text_to_process = user_input.strip()
    print(f"Task added")
    
    #def handle_schedule_submission():
    #"""Processes input, runs verification/scheduling pipeline, and resets text input."""
    #input_text = st.session_state.user_input.strip()
    #if not input_text:
    #    return
    #st.session_state.user_input = ""

    # Validate and verify task against ReAct & Z3 verifier
    try:
        agent = st.session_state.agent
        task_obj = None
        is_complete = True
        is_sat = True
        msg = ""
        if hasattr(st.session_state.agent, "validate_and_verify"):
            is_complete, task_obj, msg, is_sat =  st.session_state.agent.validate_and_verify(
            user_input, pending_draft=st.session_state.pending_draft
        )
        elif hasattr(st.session_state.agent, "process_n_vefify"):
            is_sat, task_obj, msg =     st.session_state.agent.process_n_vefify(user_input)
            is_complete = True
        else:
            is_sat, task_obj, msg = st.session_state.agent.process_and_verify(user_input)
            is_complete = True

        if not is_complete:
            st.session_state.pending_draft = task_obj
            st.session_state.clarification_msg = msg
        #st.rerun()
        else:
            st.session_state.pending_draft = None
            st.session_state.clarification_msg = ""
            if task_obj:
                if isinstance(task_obj, list):
                    for t in task_obj:
                        save_task_to_db(t)
                else:
                    save_task_to_db(task_obj)
                st.toast(f" Task Saved {msg}")
            else:
                st.error(f" Task not saved")
                fallback_task = Task(
                    id=os.urandom(4).hex(),
                    name=text_to_process,
                    imp=Importance.MEDIUM,
                    cognitive_load=3,
                    duration_min=30,
                    deadline=None)
                save_task_to_db(fallback_task)
                st.toast("Task Saved via fallback!")
        
    except Exception as e:
        print(f"[ERROR] Coundnt process: {e}")
        st.error(f"Processing Error: {str(e)}")
    st.rerun()
st.divider()
    
### HMM

def parse_importance(val):
  """Safely converts numeric strings ('4'), integers (4), or names ('HIGH') into an Importance enum."""
  if not val:
    return Importance.MEDIUM

  val_str = str(val).strip().upper()

  # 1. Match Enum member name (e.g., 'HIGH', 'CRITICAL')
  if hasattr(Importance, "__members__") and val_str in Importance.__members__:
    return Importance[val_str]

  # 2. Match Enum value (e.g., '4', '3', '1')
  try:
    val_int = int(val_str)
    for member in Importance:
      if member.value == val_int: return member
  except (ValueError, TypeError):
    pass
  return Importance.MEDIUM

col_check, col_sched = st.columns([1, 2])
with col_check:
    st.subheader("Focus Check-in")
    obs_choice = st.selectbox("Current Feeling", [o.name for o in Observation])
    if st.button("Log Observation"):
        st.session_state.hmm.forward_update(Observation[obs_choice])
        energy = st.session_state.hmm.get_expected_energy()
        st.success(f"Estimated Energy Capacity: {energy:.2f}")
        st.write(f"Dominant Focus State: **{st.session_state.hmm.get_dominant_state().name}**")

with col_sched:
    st.subheader("Optimized Schedule")
    active_db_rows = get_all_active_tasks()
    if active_db_rows:
        tasks_to_plan = []
        for r in active_db_rows:
            dl_time = None
            if len(r) > 5 and r[5]:
                try:
                    h, m = map(int, str(r[5]).split(":"))
                    dl_time = time(h, m)
                except (ValueError, TypeError):
                    dl_time = None

            ##imp_enum = (
            imp_enum = parse_importance(r[2])

            tasks_to_plan.append(
                Task(
                    id=str(r[0]),
                    name=str(r[1]),
                    imp=imp_enum,
                    cognitive_load=int(r[3]) if r[3] is not None else 3,
                    duration_min=int(r[4]) if r[4] is not None else 30,
                    deadline=dl_time,
                )
            )

        energy = st.session_state.hmm.get_expected_energy()
        ordered, dropped = plan_day_robust(tasks_to_plan, current_energy=energy)

        if dropped:
            st.warning("Could not fit into today's timeline:")
            for t_item, reason in dropped:
                st.write(f"- **{t_item.name}**: {reason}")

        for t_obj, start_t in ordered:
            st.markdown(
                f" **{start_t.strftime('%H:%M')}** — `{t_obj.name}` | "
                f"Importance: `{t_obj.imp.name if hasattr(t_obj.imp, 'name') else t_obj.imp}` | "
                f"Load: `{t_obj.cognitive_load}/5` | Duration: `{t_obj.duration_min}m`"
            )
    else:
        st.caption("Add tasks above to generate a daily schedule.")
    


else:
    st.write("_Parse some tasks above first._")
 
st.divider()
st.caption("Adaptive-pilot (RL reschedule-on-slippage) is not wired in yet — "
           "see README limitations.")
 
