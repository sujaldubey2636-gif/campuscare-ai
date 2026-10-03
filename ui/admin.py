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
    
    # ── Top-Level Metric Cards ──
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total", len(df))
    col2.metric("Pending", len(df[df['status'].isin(['Submitted', 'Assigned', 'In Progress'])]))
    col3.metric("High/Critical", len(df[df['priority'].isin(['High', 'Critical'])]))
    col4.metric("Escalated", len(df[df['status'] == 'Escalated']))
    col5.metric("Resolved", len(df[df['status'] == 'Resolved']))
    
    st.markdown("---")
    
    # ── Visual Analytics Charts ──
    st.subheader("📊 Analytics Overview")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("**Complaints by Category**")
        category_counts = df['category'].value_counts()
        st.bar_chart(category_counts)

    with chart_col2:
        st.markdown("**Complaints by Priority**")
        priority_counts = df['priority'].value_counts()
        # Use specific colors for priority levels
        st.bar_chart(priority_counts)
    
    chart_col3, chart_col4 = st.columns(2)
    
    with chart_col3:
        st.markdown("**Complaints by Department**")
        dept_counts = df['department'].value_counts()
        st.bar_chart(dept_counts)
    
    with chart_col4:
        st.markdown("**Status Distribution**")
        status_counts = df['status'].value_counts()
        st.bar_chart(status_counts)
    
    st.markdown("---")
    
    # ── Auto-Escalation Button ──
    st.subheader("🚨 Auto-Escalate Overdue Grievances")
    st.caption("Automatically escalate all High/Critical priority tickets that are still in 'Submitted' status.")
    
    overdue = df[
        (df['priority'].isin(['High', 'Critical'])) & 
        (df['status'] == 'Submitted')
    ]
    
    if len(overdue) > 0:
        st.warning(f"Found **{len(overdue)}** overdue High/Critical ticket(s) still in 'Submitted' status.")
        if st.button("⚡ Auto-Escalate All Overdue Tickets"):
            for _, row in overdue.iterrows():
                execute_query(
                    "UPDATE grievances SET status = 'Escalated', updated_at = CURRENT_TIMESTAMP WHERE ticket_id = ?",
                    (row['ticket_id'],)
                )
                execute_query(
                    "INSERT INTO grievance_updates (grievance_id, old_status, new_status, note) VALUES (?, ?, ?, ?)",
                    (row['id'], 'Submitted', 'Escalated', '[AUTO] System escalated: High/Critical ticket was unattended.')
                )
            st.success(f"Successfully escalated {len(overdue)} ticket(s)!")
            st.rerun()
    else:
        st.success("✅ No overdue High/Critical tickets. Everything is attended to.")
    
    st.markdown("---")
    
    # ── All Grievances Table with Filters ──
    st.subheader("All Grievances")
    
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        status_filter = st.multiselect("Filter by Status", df['status'].unique(), default=df['status'].unique())
    with f_col2:
        dept_filter = st.multiselect("Filter by Department", df['department'].unique(), default=df['department'].unique())
    with f_col3:
        priority_filter = st.multiselect("Filter by Priority", df['priority'].unique(), default=df['priority'].unique())
        
    filtered_df = df[
        (df['status'].isin(status_filter)) & 
        (df['department'].isin(dept_filter)) &
        (df['priority'].isin(priority_filter))
    ]
    
    st.dataframe(
        filtered_df[['ticket_id', 'student_id', 'category', 'priority', 'department', 'status', 'created_at']],
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    # ── Update Grievance Status ──
    st.subheader("Update Grievance Status")
    
    ticket_ids = filtered_df['ticket_id'].tolist()
    if ticket_ids:
        selected_ticket = st.selectbox("Select Ticket ID", ticket_ids)
        
        if selected_ticket:
            ticket_data = filtered_df[filtered_df['ticket_id'] == selected_ticket].iloc[0]
            
            st.write(f"**Student ID:** {ticket_data['student_id']}")
            st.write(f"**Complaint:** {ticket_data['complaint_text']}")
            st.write(f"**AI Reason:** {ticket_data['ai_reason']}")
            st.write(f"**Current Status:** `{ticket_data['status']}`")
            
            # Show update history for this ticket
            history = fetch_all(
                "SELECT old_status, new_status, note, updated_at FROM grievance_updates WHERE grievance_id = ? ORDER BY updated_at DESC",
                (ticket_data['id'],)
            )
            if history:
                st.markdown("**Update History:**")
                for h in history:
                    st.caption(f"🔄 `{h['old_status']}` → `{h['new_status']}` — {h['note']} ({h['updated_at']})")
            
            with st.form("update_form"):
                all_statuses = ["Submitted", "Assigned", "In Progress", "Resolved", "Rejected", "Escalated"]
                current_index = all_statuses.index(ticket_data['status']) if ticket_data['status'] in all_statuses else 0
                new_status = st.selectbox("New Status", all_statuses, index=current_index)
                note = st.text_area("Resolution Note / Internal Comment")
                
                update_btn = st.form_submit_button("Update Status")
                
            if update_btn:
                execute_query(
                    "UPDATE grievances SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE ticket_id = ?",
                    (new_status, selected_ticket)
                )
                execute_query(
                    "INSERT INTO grievance_updates (grievance_id, old_status, new_status, note) VALUES (?, ?, ?, ?)",
                    (ticket_data['id'], ticket_data['status'], new_status, note)
                )
                st.success(f"Ticket {selected_ticket} updated to {new_status} successfully!")
                st.rerun()
    else:
        st.write("No tickets match the current filters.")
