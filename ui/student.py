import streamlit as st
from agent.grievance_agent import GrievanceAgent
from database.db import fetch_all, fetch_one

def render_student_dashboard():
    st.title("🎓 CampusCare AI")
    st.markdown("👋 **Welcome to the intelligent campus support portal.** Describe your issue naturally, and our AI will route it to the correct department instantly.")
    st.markdown("---")
    
    # ── Modern Tabbed Layout ──
    tab1, tab2 = st.tabs(["📝 Submit a Grievance", "🔍 Track My Status"])
    
    with tab1:
        st.subheader("How can we help you today?")
        
        # We put the form inside a neat container
        with st.container(border=True):
            with st.form("grievance_form"):
                col1, col2 = st.columns(2)
                with col1:
                    student_id = st.text_input("🆔 Student ID", placeholder="e.g., STU001")
                with col2:
                    location = st.text_input("📍 Location", placeholder="e.g., Hostel Block B, Room 102")
                    
                complaint = st.text_area("🗣️ Describe your problem in detail", height=100, placeholder="The internet on our floor has been disconnecting frequently since yesterday...")
                
                submit_btn = st.form_submit_button("🚀 Analyze & Submit", use_container_width=True)
            
        # Show Student Profile if ID is entered (outside form so it updates)
        if student_id:
            student = fetch_one("SELECT * FROM students WHERE id = ?", (student_id.strip(),))
            if student:
                st.info(f"👤 **Identified Student:** {student['name']} ({student['course']}, Year {student['year']})")
            elif student_id.strip():
                st.caption("⚠️ Student ID not found. You can still submit.")

        if submit_btn:
            if not student_id or not complaint:
                st.error("❌ Please provide both your Student ID and a Complaint description.")
            else:
                with st.spinner("🤖 CampusCare AI is analyzing your complaint..."):
                    agent = GrievanceAgent()
                    result = agent.run(student_id=student_id, complaint_text=complaint, location=location)
                    
                    ticket_info = result["ticket_info"]
                    
                    st.success(f"✅ {ticket_info['message']}")
                    
                    # Clean presentation of AI Results
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
                        
                        st.caption(f"**Agent Reasoning:** {ticket_info.get('ai_reason', 'N/A')}")

                    st.markdown("### 📋 Recommended Next Action")
                    _show_recommended_action(
                        ticket_info.get("category", "Other"),
                        ticket_info.get("priority", "Medium"),
                        ticket_info.get("department", "General Administration")
                    )

    with tab2:
        st.subheader("Track an Existing Ticket")
        track_id = st.text_input("Enter your Ticket ID", placeholder="GRV-XXXXXX")
        
        if track_id:
            record = fetch_all("SELECT * FROM grievances WHERE ticket_id = ?", (track_id.strip(),))
            if record:
                r = record[0]
                with st.container(border=True):
                    t_col1, t_col2, t_col3 = st.columns(3)
                    
                    status = r['status']
                    if status == 'Resolved':
                        t_col1.success(f"**Status:** {status} ✅")
                    elif status == 'Escalated':
                        t_col1.error(f"**Status:** {status} 🚨")
                    elif status in ['In Progress', 'Assigned']:
                        t_col1.warning(f"**Status:** {status} 🔄")
                    else:
                        t_col1.info(f"**Status:** {status} 📥")
                    
                    t_col2.write(f"**🏢 Department:** {r['department']}")
                    t_col3.write(f"**📅 Submitted:** {r['created_at'][:10]}")
                    
                    st.markdown(f"**📝 Issue:** {r['complaint_text']}")
                    st.markdown(f"**🤖 AI Initial Assessment:** {r['ai_reason']}")
                
                # Show update history nicely
                history = fetch_all(
                    "SELECT old_status, new_status, note, updated_at FROM grievance_updates WHERE grievance_id = ? ORDER BY updated_at DESC",
                    (r['id'],)
                )
                if history:
                    with st.expander("📜 View Ticket Update History", expanded=True):
                        for h in history:
                            st.markdown(f"**{h['updated_at']}** — 🔄 `{h['old_status']}` → `{h['new_status']}`  \n*Note: {h['note']}*")
                            st.divider()
            else:
                st.warning("❌ Ticket ID not found in the system.")
        
        # Show all grievances for this student
        if student_id and student_id.strip():
            my_grievances = fetch_all(
                "SELECT ticket_id, category, priority, department, status, created_at FROM grievances WHERE student_id = ? ORDER BY created_at DESC",
                (student_id.strip(),)
            )
            if my_grievances:
                st.markdown("---")
                st.subheader(f"📂 Previous Grievances for {student_id}")
                import pandas as pd
                my_df = pd.DataFrame(my_grievances)
                st.dataframe(my_df, use_container_width=True, hide_index=True)


def _show_recommended_action(category: str, priority: str, department: str):
    """
    Shows a recommended next action based on the complaint's category and priority.
    This is deterministic Python logic, NOT generated by the LLM.
    """
    # Priority-based urgency
    if priority == "Critical":
        urgency = "Immediate attention required within 1 hour."
    elif priority == "High":
        urgency = "Should be addressed within 4 hours."
    elif priority == "Medium":
        urgency = "Should be addressed within 24 hours."
    else:
        urgency = "Can be addressed within 48 hours."
    
    # Category-based specific action
    actions = {
        "Hostel": f"Create urgent maintenance request and notify the Hostel Warden. {urgency}",
        "IT": f"Log a network/systems ticket with {department}. Dispatch IT technician to inspect. {urgency}",
        "Finance": f"Flag for manual verification by {department}. Cross-check bank records. {urgency}",
        "Examination": f"Forward to {department} for review. Verify exam records. {urgency}",
        "Library": f"Notify {department} for processing. {urgency}",
        "Facilities": f"Dispatch maintenance crew to the reported location. {urgency}",
        "Security": f"⚠️ Alert {department} immediately. If this involves personal safety, contact campus security directly. {urgency}",
        "Transport": f"Notify transport coordinator under {department}. {urgency}",
        "Academic": f"Forward to the relevant faculty head via {department}. {urgency}",
    }
    
    action = actions.get(category, f"Forward to {department} for review. {urgency}")
    
    if priority in ["Critical", "High"]:
        st.error(f"**{action}**")
    elif priority == "Medium":
        st.warning(f"**{action}**")
    else:
        st.info(f"**{action}**")
