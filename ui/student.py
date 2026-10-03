import streamlit as st
from agent.grievance_agent import GrievanceAgent
from database.db import fetch_all

def render_student_dashboard():
    st.title("🎓 CampusCare AI")
    st.subheader("Student Grievance Resolution Agent")
    
    st.markdown("Submit your complaint in natural language, and our AI agent will categorize, prioritize, and route it to the right department automatically.")
    
    with st.form("grievance_form"):
        col1, col2 = st.columns(2)
        with col1:
            student_id = st.text_input("Student ID (e.g., STU001)", placeholder="STU001")
        with col2:
            location = st.text_input("Location", placeholder="e.g., Hostel Block B")
            
        complaint = st.text_area("Describe your problem in detail")
        
        submit_btn = st.form_submit_button("Analyze & Submit")
        
    if submit_btn:
        if not student_id or not complaint:
            st.error("Please provide both Student ID and Complaint.")
        else:
            with st.spinner("AI Agent is analyzing your complaint..."):
                agent = GrievanceAgent()
                result = agent.run(student_id=student_id, complaint_text=complaint, location=location)
                
                ticket_info = result["ticket_info"]
                
                st.success(ticket_info["message"])
                
                st.markdown("### AI Analysis Result")
                st.markdown("---")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Category", ticket_info.get("category", "N/A"))
                
                priority = ticket_info.get("priority", "N/A")
                if priority in ["Critical", "High"]:
                    col2.error(f"Priority: {priority}")
                elif priority == "Medium":
                    col2.warning(f"Priority: {priority}")
                else:
                    col2.info(f"Priority: {priority}")
                    
                col3.metric("Department", ticket_info.get("department", "N/A"))
                
                st.info(f"**Agent Reasoning:**\n{ticket_info.get('ai_reason', 'N/A')}")
                
    st.markdown("---")
    st.subheader("Track Your Grievance")
    track_id = st.text_input("Enter Ticket ID to track status", placeholder="GRV-XXXXXX")
    if track_id:
        record = fetch_all("SELECT * FROM grievances WHERE ticket_id = ?", (track_id.strip(),))
        if record:
            st.write(f"**Status:** `{record[0]['status']}`")
            st.write(f"**Assigned Department:** {record[0]['department']}")
            st.write(f"**Submitted On:** {record[0]['created_at']}")
            st.write(f"**AI Initial Assessment:** {record[0]['ai_reason']}")
        else:
            st.warning("Ticket ID not found.")
