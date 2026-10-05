import streamlit as st
import json
from agent.grievance_agent import GrievanceAgent
from database.db import fetch_all, fetch_one

def render_student_dashboard(logged_in_student_id: str):
    st.title("🎓 CampusCare AI")
    st.markdown("👋 **Welcome to the intelligent campus support portal.** Describe your issue naturally, and our AI will route it to the correct department instantly.")
    st.markdown("---")

    tab1, tab2 = st.tabs(["📝 Submit a Grievance", "🔍 Track My Status"])

    with tab1:
        st.subheader("How can we help you today?")

        # Show Student Profile first since they are logged in
        student = fetch_one("SELECT * FROM students WHERE id = ?", (logged_in_student_id,))
        student_display_name = (student['name'].split()[0]) if (student and student.get('name')) else "Student"
        if student:
            st.info(f"👤 **Identified Student:** {student['name']} ({student.get('course', 'Student')}, Year {student.get('year', 'N/A')})")
        
        col_chat1, col_chat2 = st.columns([4, 1])
        with col_chat1:
            st.markdown("### 💬 Chat with CampusCare AI")
        with col_chat2:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = [{"role": "assistant", "content": f"Hi {student_display_name}! I am the CampusCare AI. How can I help you today?"}]
                st.session_state.follow_up_state = None
                st.rerun()
        
        # Initialize chat history
        if "chat_history" not in st.session_state or not st.session_state.chat_history:
            st.session_state.chat_history = [{"role": "assistant", "content": f"Hi {student_display_name}! I am the CampusCare AI. How can I help you today?"}]
            
        # Display history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg.get("ticket_result"):
                    _display_result(msg["ticket_result"])
                    
        # Accept input
        prompt = st.chat_input("Describe your campus issue (e.g. 'The WiFi in Block B is down')...")
        if prompt:
            # Append user message
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
                
            # Process with AI
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    context_prompt = prompt
                    follow_up = st.session_state.get('follow_up_state')
                    if follow_up:
                        context_prompt = f"Previous context: {follow_up}\nUser reply: {prompt}"
                        
                    agent = GrievanceAgent()
                    result = agent.run(student_id=logged_in_student_id, complaint_text=context_prompt, location="Parsed from chat")
                    
                    if result.get("follow_up_question") and not result.get("ticket_info"):
                        st.write(result["follow_up_question"])
                        st.session_state.chat_history.append({"role": "assistant", "content": result["follow_up_question"]})
                        st.session_state.follow_up_state = context_prompt
                    else:
                        st.write(result["agent_response"])
                        _display_result(result)
                        st.session_state.chat_history.append({"role": "assistant", "content": result["agent_response"], "ticket_result": result})
                        st.session_state.follow_up_state = None

    with tab2:
        st.subheader("Track an Existing Ticket")
        track_id = st.text_input("Enter your Ticket ID", placeholder="GRV-XXXXXX")

        if track_id and track_id.strip():
            clean_track_id = track_id.strip()
            record = fetch_all("SELECT * FROM grievances WHERE UPPER(ticket_id) = UPPER(?)", (clean_track_id,))
            if record:
                r = record[0]
                with st.container(border=True):
                    # ── Visual Status Timeline ──
                    status = r.get('status', 'Submitted')
                    stages = ["Submitted", "Assigned", "In Progress", "Resolved"]
                    
                    if status == "Escalated":
                        st.error("🚨 This ticket has been **Escalated** for urgent review.")
                        st.progress(0.75)
                    elif status == "Rejected":
                        st.warning("🚫 This ticket was **Rejected**.")
                        st.progress(1.0)
                    else:
                        try:
                            progress_idx = stages.index(status)
                            progress_val = (progress_idx + 1) / len(stages)
                            st.progress(progress_val)
                            st.caption(f"**Current Stage:** {status} (Step {progress_idx + 1} of 4)")
                        except ValueError:
                            st.info(f"**Status:** {status}")
                    
                    t_col1, t_col2, t_col3 = st.columns(3)
                    t_col1.write(f"**🏢 Department:** {r.get('department', 'N/A')}")
                    t_col2.write(f"**📌 Category:** {r.get('category', 'N/A')}")
                    t_col3.write(f"**📅 Submitted:** {(r.get('created_at') or '')[:10]}")
                    
                    st.markdown("---")
                    st.markdown(f"**📝 Issue Description:**  \n{r.get('complaint_text', '')}")
                    st.markdown(f"**🤖 AI Assessment:**  \n*{r.get('ai_reason', '')}*")

                    # Show safety flag
                    if r.get('safety_flag'):
                        st.error("🚨 **SAFETY ALERT:** This complaint involves a potential safety hazard. Please also contact campus security directly.")

                history = fetch_all(
                    "SELECT old_status, new_status, note, updated_at FROM grievance_updates WHERE grievance_id = ? ORDER BY updated_at DESC",
                    (r['id'],)
                )
                if history:
                    with st.expander("📜 View Ticket Update History", expanded=True):
                        for h in history:
                            st.markdown(f"**{h.get('updated_at', '')}** — 🔄 `{h.get('old_status')}` -> `{h.get('new_status')}`  \n> *{h.get('note', '')}*")
                            st.divider()
            else:
                st.warning("❌ Ticket ID not found in the system.")

        # Show all grievances for this student
        if logged_in_student_id and logged_in_student_id.strip():
            my_grievances = fetch_all(
                "SELECT ticket_id, category, priority, department, status, created_at FROM grievances WHERE student_id = ? ORDER BY created_at DESC",
                (logged_in_student_id.strip(),)
            )
            if my_grievances:
                st.markdown("---")
                st.subheader(f"📂 Your Grievance History")
                
                # Render beautifully as cards instead of a boring table
                for g in my_grievances:
                    with st.container(border=True):
                        c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
                        c1.markdown(f"**🆔 {g['ticket_id']}**")
                        c2.markdown(f"🏢 {g['department']}")
                        
                        # Add colored status badge
                        status_str = g['status']
                        if status_str == 'Resolved':
                            c3.success("✅ Resolved")
                        elif status_str == 'Escalated':
                            c3.error("🚨 Escalated")
                        elif status_str in ['Assigned', 'In Progress']:
                            c3.warning(f"🔄 {status_str}")
                        else:
                            c3.info(f"📥 {status_str}")
                            
                        c4.caption(f"📅 {g['created_at'][:10]}")


def _display_result(result):
    """Display the full AI analysis result with all intelligence features."""
    ticket_info = result.get("ticket_info")
    if not ticket_info:
        st.error("Something went wrong. Please try again.")
        return

    st.toast("✅ Analysis complete! Ticket processed.", icon="🎉")
    st.success(f"✅ {ticket_info['message']}")

    # ── Safety Warning (top priority visibility) ──
    if ticket_info.get('safety_flag'):
        st.error("🚨 **SAFETY ALERT:** This complaint involves a potential safety hazard. In addition to this ticket, please contact campus security or relevant authority directly. The AI cannot handle emergencies on its own.")

    # ── AI Analysis Card ──
    st.markdown("### 🧠 AI Analysis Result")
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("📌 Category", ticket_info.get("category", "N/A"))

        priority = ticket_info.get("priority", "N/A")
        if priority in ["Critical", "High"]:
            col2.error(f"🔴 Priority: {priority}")
        elif priority == "Medium":
            col2.warning(f"🟡 Priority: {priority}")
        else:
            col2.info(f"🟢 Priority: {priority}")

        col3.metric("🏢 Department", ticket_info.get("department", "N/A"))

        # Show confidence
        confidence_data = ticket_info.get("confidence")
        if confidence_data:
            try:
                conf = json.loads(confidence_data) if isinstance(confidence_data, str) else confidence_data
                cat_conf = conf.get("category_confidence", "N/A")
                st.caption(f"🎯 Category Confidence: **{cat_conf}%** | Priority Score: **{conf.get('priority_score', 'N/A')}/100**")
            except (json.JSONDecodeError, TypeError):
                pass

        # Show needs_review flag
        if ticket_info.get('needs_review'):
            st.warning("🔍 **Note:** The AI is not fully confident about this classification. An administrator will review it.")

        st.caption(f"**Agent Reasoning:** {ticket_info.get('ai_reason', 'N/A')}")

    # ── Extracted Information ──
    extracted = ticket_info.get("extracted_info")
    if extracted:
        try:
            info = json.loads(extracted) if isinstance(extracted, str) else extracted
            
            # ── Policy Checker (RAG) ──
            policy = info.get("applicable_policy")
            if policy:
                st.markdown("### 📖 Official College Policy Match")
                st.info(f"The AI found a relevant rule in the College Rulebook:\n\n*{policy}*\n\nYour ticket has still been routed to the department, but please note this official policy.")
            
            st.markdown("### 🔎 Extracted Information")
            with st.container(border=True):
                e_col1, e_col2, e_col3 = st.columns(3)
                e_col1.write(f"**Issue:** {info.get('issue', 'N/A')}")
                e_col2.write(f"**Duration:** {info.get('duration', 'N/A')}")
                e_col3.write(f"**Affected:** {info.get('affected_count', 0)} student(s)")

                e_col4, e_col5, e_col6 = st.columns(3)
                e_col4.write(f"**Equipment:** {info.get('equipment_or_service', 'N/A')}")
                e_col5.write(f"**Sentiment:** {info.get('sentiment', 'N/A')}")
                e_col6.write(f"**Deadline Pressure:** {'Yes' if info.get('has_deadline_pressure') else 'No'}")

                if info.get('root_cause_hypothesis'):
                    st.caption(f"💡 **Root Cause Hypothesis** (needs verification): {info['root_cause_hypothesis']}")
        except (json.JSONDecodeError, TypeError):
            pass

    # ── Priority Factors (Transparency) ──
    factors = ticket_info.get("priority_factors")
    if factors:
        with st.expander("📊 How was priority calculated?", expanded=False):
            for f in factors:
                st.markdown(f"• {f}")
            st.caption("Priority is calculated by deterministic Python scoring, not by the AI model.")

    # ── Recommended Action ──
    st.markdown("### 📋 Recommended Next Action")
    _show_recommended_action(
        ticket_info.get("category", "Other"),
        ticket_info.get("priority", "Medium"),
        ticket_info.get("department", "General Administration"),
    )


def _show_recommended_action(category, priority, department):
    """Deterministic recommended action based on category and priority."""
    if priority == "Critical":
        urgency = "Immediate attention required within 1 hour."
    elif priority == "High":
        urgency = "Should be addressed within 4 hours."
    elif priority == "Medium":
        urgency = "Should be addressed within 24 hours."
    else:
        urgency = "Can be addressed within 48 hours."

    actions = {
        "Hostel":       f"Create urgent maintenance request and notify the Hostel Warden. {urgency}",
        "IT":           f"Log a network/systems ticket with {department}. Dispatch IT technician. {urgency}",
        "Finance":      f"Flag for manual verification by {department}. Cross-check bank records. {urgency}",
        "Examination":  f"Forward to {department} for review. Verify exam records. {urgency}",
        "Library":      f"Notify {department} for processing. {urgency}",
        "Facilities":   f"Dispatch maintenance crew to reported location. {urgency}",
        "Security":     f"⚠️ Alert {department} immediately. Contact campus security directly. {urgency}",
        "Transport":    f"Notify transport coordinator. {urgency}",
        "Academic":     f"Forward to relevant faculty head via {department}. {urgency}",
    }
    action = actions.get(category, f"Forward to {department} for review. {urgency}")

    if priority in ["Critical", "High"]:
        st.error(f"**{action}**")
    elif priority == "Medium":
        st.warning(f"**{action}**")
    else:
        st.info(f"**{action}**")
