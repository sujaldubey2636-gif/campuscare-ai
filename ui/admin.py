import streamlit as st
import pandas as pd
from database.db import fetch_all, execute_query

def render_admin_dashboard():
    st.title("⚙️ Admin Control Panel")
    st.markdown("Manage and monitor all campus grievances in one place.")
    
    # Fetch all data
    all_grievances = fetch_all("SELECT * FROM grievances ORDER BY created_at DESC")
    
    if not all_grievances:
        st.info("No grievances found in the database.")
        return
        
    df = pd.DataFrame(all_grievances)
    
    # ── Modern Tabbed Layout ──
    tab1, tab2, tab3 = st.tabs(["📊 Analytics Overview", "📋 Manage Tickets", "🚨 Escalations"])
    
    with tab1:
        st.subheader("Campus Operations Health")
        # ── Top-Level Metric Cards ──
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total", len(df))
        col2.metric("Pending", len(df[df['status'].isin(['Submitted', 'Assigned', 'In Progress'])]))
        col3.metric("High/Critical", len(df[df['priority'].isin(['High', 'Critical'])]))
        col4.metric("Escalated", len(df[df['status'] == 'Escalated']))
        col5.metric("Resolved", len(df[df['status'] == 'Resolved']))
        
        st.markdown("---")
        
        # ── Visual Analytics Charts ──
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.markdown("**Complaints by Category**")
            st.bar_chart(df['category'].value_counts())
    
        with chart_col2:
            st.markdown("**Complaints by Priority**")
            st.bar_chart(df['priority'].value_counts())
        
        chart_col3, chart_col4 = st.columns(2)
        with chart_col3:
            st.markdown("**Complaints by Department**")
            st.bar_chart(df['department'].value_counts())
        
        with chart_col4:
            st.markdown("**Status Distribution**")
            st.bar_chart(df['status'].value_counts())
            
    with tab2:
        st.subheader("Filter & Resolve Tickets")
        
        # Filters in an expander to save space
        with st.expander("🔍 Filter Tickets", expanded=True):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                status_filter = st.multiselect("Status", df['status'].unique(), default=df['status'].unique())
            with f_col2:
                dept_filter = st.multiselect("Department", df['department'].unique(), default=df['department'].unique())
            with f_col3:
                priority_filter = st.multiselect("Priority", df['priority'].unique(), default=df['priority'].unique())
            
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
        st.subheader("✏️ Update Grievance Status")
        ticket_ids = filtered_df['ticket_id'].tolist()
        
        if ticket_ids:
            selected_ticket = st.selectbox("Select a Ticket to Update", ticket_ids)
            
            if selected_ticket:
                ticket_data = filtered_df[filtered_df['ticket_id'] == selected_ticket].iloc[0]
                
                with st.container(border=True):
                    st.write(f"**👤 Student ID:** {ticket_data['student_id']}")
                    st.write(f"**📝 Complaint:** {ticket_data['complaint_text']}")
                    st.write(f"**🤖 AI Reason:** {ticket_data['ai_reason']}")
                    st.write(f"**🏷️ Current Status:** `{ticket_data['status']}`")
                
                    with st.form("update_form"):
                        all_statuses = ["Submitted", "Assigned", "In Progress", "Resolved", "Rejected", "Escalated"]
                        current_index = all_statuses.index(ticket_data['status']) if ticket_data['status'] in all_statuses else 0
                        
                        new_status = st.selectbox("Update Status To:", all_statuses, index=current_index)
                        note = st.text_area("Resolution Note / Internal Comment", placeholder="E.g., Technician dispatched to repair the fan.")
                        
                        update_btn = st.form_submit_button("💾 Save Update", use_container_width=True)
                        
                    if update_btn:
                        execute_query(
                            "UPDATE grievances SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE ticket_id = ?",
                            (new_status, selected_ticket)
                        )
                        execute_query(
                            "INSERT INTO grievance_updates (grievance_id, old_status, new_status, note) VALUES (?, ?, ?, ?)",
                            (ticket_data['id'], ticket_data['status'], new_status, note)
                        )
                        st.success(f"Ticket {selected_ticket} successfully updated to {new_status}!")
                        st.rerun()
                        
                # Show update history for this ticket
                history = fetch_all(
                    "SELECT old_status, new_status, note, updated_at FROM grievance_updates WHERE grievance_id = ? ORDER BY updated_at DESC",
                    (ticket_data['id'],)
                )
                if history:
                    with st.expander("📜 View Ticket History", expanded=False):
                        for h in history:
                            st.caption(f"🔄 `{h['old_status']}` → `{h['new_status']}` — {h['note']} ({h['updated_at']})")
        else:
            st.info("No tickets match your filters.")

    with tab3:
        st.subheader("🚨 Auto-Escalate Overdue Grievances")
        st.info("This system checks for High and Critical priority tickets that have been ignored (still in 'Submitted' status) and auto-escalates them.")
        
        overdue = df[
            (df['priority'].isin(['High', 'Critical'])) & 
            (df['status'] == 'Submitted')
        ]
        
        if len(overdue) > 0:
            st.error(f"⚠️ Found **{len(overdue)}** overdue High/Critical ticket(s) requiring immediate attention.")
            
            # Show which ones are overdue
            st.dataframe(overdue[['ticket_id', 'department', 'priority', 'created_at']], hide_index=True)
            
            if st.button("⚡ Auto-Escalate All Overdue Tickets", type="primary"):
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
            st.success("✅ No overdue High/Critical tickets. Operations are running smoothly.")
