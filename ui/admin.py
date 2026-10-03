import streamlit as st
import pandas as pd
from database.db import fetch_all, execute_query

def render_admin_dashboard():
    st.title("⚙️ Admin Dashboard")
    st.subheader("CampusCare Grievance Management")
    
    # Dashboard Metrics
    all_grievances = fetch_all("SELECT * FROM grievances ORDER BY created_at DESC")
    
    if not all_grievances:
        st.info("No grievances found in the database.")
        return
        
    df = pd.DataFrame(all_grievances)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Grievances", len(df))
    col2.metric("Pending", len(df[df['status'].isin(['Submitted', 'Assigned', 'In Progress'])]))
    col3.metric("High/Critical Priority", len(df[df['priority'].isin(['High', 'Critical'])]))
    col4.metric("Escalated", len(df[df['status'] == 'Escalated']))
    
    st.markdown("---")
    st.subheader("All Grievances")
    
    # Filters
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        status_filter = st.multiselect("Filter by Status", df['status'].unique(), default=df['status'].unique())
    with f_col2:
        dept_filter = st.multiselect("Filter by Department", df['department'].unique(), default=df['department'].unique())
        
    filtered_df = df[(df['status'].isin(status_filter)) & (df['department'].isin(dept_filter))]
    
    st.dataframe(
        filtered_df[['ticket_id', 'student_id', 'category', 'priority', 'department', 'status', 'created_at']],
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    st.subheader("Update Grievance Status")
    
    ticket_ids = filtered_df['ticket_id'].tolist()
    if ticket_ids:
        selected_ticket = st.selectbox("Select Ticket ID", ticket_ids)
        
        if selected_ticket:
            ticket_data = filtered_df[filtered_df['ticket_id'] == selected_ticket].iloc[0]
            
            st.write(f"**Complaint:** {ticket_data['complaint_text']}")
            st.write(f"**AI Reason:** {ticket_data['ai_reason']}")
            st.write(f"**Current Status:** `{ticket_data['status']}`")
            
            with st.form("update_form"):
                new_status = st.selectbox("New Status", ["Submitted", "Assigned", "In Progress", "Resolved", "Rejected", "Escalated"], index=["Submitted", "Assigned", "In Progress", "Resolved", "Rejected", "Escalated"].index(ticket_data['status']))
                note = st.text_area("Resolution Note / Internal Comment")
                
                update_btn = st.form_submit_button("Update Status")
                
            if update_btn:
                # Update main table
                execute_query("UPDATE grievances SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE ticket_id = ?", (new_status, selected_ticket))
                # Add to history table
                execute_query("INSERT INTO grievance_updates (grievance_id, old_status, new_status, note) VALUES (?, ?, ?, ?)", (ticket_data['id'], ticket_data['status'], new_status, note))
                
                st.success(f"Ticket {selected_ticket} updated to {new_status} successfully!")
                st.rerun()
    else:
        st.write("No tickets match the current filters.")
