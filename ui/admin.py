import streamlit as st
import json
import pandas as pd
from database.db import fetch_all, execute_query
from agent.tools import get_campus_insights, DEPARTMENT_MAP

import os

def render_admin_dashboard():
    st.title("⚙️ Admin Control Panel")
    st.markdown("Manage and monitor all campus grievances in one place.")

    all_grievances = fetch_all("SELECT * FROM grievances ORDER BY created_at DESC")

    if not all_grievances:
        st.info("No grievances found in the database.")
        return

    df = pd.DataFrame(all_grievances)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📚 AI Policy Manager", "📋 Manage Tickets", "🚨 Escalations & Review", "🧠 Campus Insights"
    ])

    # ──────────────────────────────────────────
    # TAB 1: AI Policy Manager (Dynamic RAG)
    # ──────────────────────────────────────────
    with tab1:
        st.subheader("📚 Dynamic Policy & Knowledge Base (RAG)")
        st.write("Edit the official college rulebook below. The CampusCare AI Agent will **instantly adapt** to these new rules in real-time when interacting with students.")
        
        rulebook_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'college_rulebook.md')
        
        # Read current policy
        if os.path.exists(rulebook_path):
            with open(rulebook_path, 'r', encoding='utf-8') as f:
                current_policy = f.read()
        else:
            current_policy = "# CampusCare Official College Rulebook\n\nAdd your rules here..."
            
        with st.form("policy_form"):
            updated_policy = st.text_area("Live Rulebook Editor (Markdown supported):", value=current_policy, height=350)
            st.caption("💡 Tip: Try adding a fake rule and then switch to the Student Portal to see the AI use it instantly!")
            save_btn = st.form_submit_button("💾 Save & Update AI Knowledge Base", use_container_width=True)
            
        if save_btn:
            os.makedirs(os.path.dirname(rulebook_path), exist_ok=True)
            with open(rulebook_path, 'w', encoding='utf-8') as f:
                f.write(updated_policy)
            st.toast("✅ AI Knowledge Base Updated!", icon="🧠")
            st.success("Rulebook saved successfully. The AI Agent's RAG engine is now using these new rules.")

    # ──────────────────────────────────────────
    # TAB 2: Manage Tickets
    # ──────────────────────────────────────────
    with tab2:
        st.subheader("Filter & Resolve Tickets")
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
            use_container_width=True, hide_index=True
        )

        st.markdown("---")
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

                    # ── Show extracted info if available ──
                    extracted = ticket_data.get('extracted_info')
                    if extracted:
                        try:
                            info = json.loads(extracted) if isinstance(extracted, str) else extracted
                            
                            if info.get('applicable_policy'):
                                st.info(f"📖 **Applicable Policy matched by AI:**\n{info['applicable_policy']}")
                            
                            with st.expander("🔎 AI Extracted Information", expanded=False):
                                e1, e2, e3 = st.columns(3)
                                e1.write(f"**Issue:** {info.get('issue', 'N/A')}")
                                e2.write(f"**Duration:** {info.get('duration', 'N/A')}")
                                e3.write(f"**Affected:** {info.get('affected_count', 0)}")
                                e4, e5, e6 = st.columns(3)
                                e4.write(f"**Equipment:** {info.get('equipment_or_service', 'N/A')}")
                                e5.write(f"**Sentiment:** {info.get('sentiment', 'N/A')}")
                                e6.write(f"**Safety Risk:** {'⚠️ Yes' if info.get('safety_risk') else '✅ No'}")
                                if info.get('root_cause_hypothesis'):
                                    st.caption(f"💡 Hypothesis (needs verification): {info['root_cause_hypothesis']}")
                        except (json.JSONDecodeError, TypeError):
                            pass

                    # ── Show confidence ──
                    conf_data = ticket_data.get('confidence')
                    if conf_data:
                        try:
                            conf = json.loads(conf_data) if isinstance(conf_data, str) else conf_data
                            st.caption(f"🎯 AI Confidence: Category={conf.get('category_confidence', '?')}% | Priority Score={conf.get('priority_score', '?')}/100")
                        except (json.JSONDecodeError, TypeError):
                            pass

                    # ── Safety flag ──
                    if ticket_data.get('safety_flag'):
                        st.error("🚨 SAFETY FLAG: This ticket involves a potential safety hazard.")

                    # ── Needs Review flag ──
                    if ticket_data.get('needs_review'):
                        st.warning("🔍 AI flagged this ticket for manual admin review (low confidence classification).")

                    # ── AI Suggested Response ──
                    st.markdown("**💡 AI Suggested Response:**")
                    suggestion = _get_suggested_response(ticket_data['category'], ticket_data['priority'])
                    st.caption(f"*{suggestion}*")
                    st.caption("(You may accept, modify, or ignore this suggestion.)")

                    # ── Admin Override + Update Form ──
                    with st.form("update_form"):
                        all_statuses = ["Submitted", "Assigned", "In Progress", "Resolved", "Rejected", "Escalated"]
                        current_index = all_statuses.index(ticket_data['status']) if ticket_data['status'] in all_statuses else 0

                        o_col1, o_col2 = st.columns(2)
                        with o_col1:
                            new_status = st.selectbox("Update Status:", all_statuses, index=current_index)
                        with o_col2:
                            # Admin can override category
                            all_categories = list(DEPARTMENT_MAP.keys())
                            current_cat_idx = all_categories.index(ticket_data['category']) if ticket_data['category'] in all_categories else 0
                            override_category = st.selectbox("Override Category (optional):", all_categories, index=current_cat_idx)

                        note = st.text_area("Resolution Note / Internal Comment", placeholder="E.g., Technician dispatched to repair the fan.")
                        update_btn = st.form_submit_button("💾 Save Update", use_container_width=True)

                    if update_btn:
                        # Apply override if category changed
                        new_dept = DEPARTMENT_MAP.get(override_category, ticket_data['department'])
                        execute_query(
                            "UPDATE grievances SET status = ?, category = ?, department = ?, needs_review = 0, updated_at = CURRENT_TIMESTAMP WHERE ticket_id = ?",
                            (new_status, override_category, new_dept, selected_ticket)
                        )
                        execute_query(
                            "INSERT INTO grievance_updates (grievance_id, old_status, new_status, note) VALUES (?, ?, ?, ?)",
                            (ticket_data['id'], ticket_data['status'], new_status, note if note else f"Category overridden to {override_category}")
                        )
                        st.toast(f"Ticket {selected_ticket} updated to {new_status}!", icon="🚀")
                        st.success(f"Ticket {selected_ticket} updated to {new_status} (Category: {override_category})!")
                        import time
                        time.sleep(1)
                        st.rerun()

                # Show update history
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

    # ──────────────────────────────────────────
    # TAB 3: Escalations & Review Queue
    # ──────────────────────────────────────────
    with tab3:
        st.subheader("🚨 Auto-Escalate Overdue Grievances")
        st.info("Escalate all High/Critical tickets still in 'Submitted' status.")

        overdue = df[(df['priority'].isin(['High', 'Critical'])) & (df['status'] == 'Submitted')]

        if len(overdue) > 0:
            st.error(f"⚠️ Found **{len(overdue)}** overdue High/Critical ticket(s).")
            st.dataframe(overdue[['ticket_id', 'department', 'priority', 'created_at']], hide_index=True)
            if st.button("⚡ Auto-Escalate All Overdue Tickets", type="primary"):
                for _, row in overdue.iterrows():
                    execute_query("UPDATE grievances SET status = 'Escalated', updated_at = CURRENT_TIMESTAMP WHERE ticket_id = ?", (row['ticket_id'],))
                    execute_query("INSERT INTO grievance_updates (grievance_id, old_status, new_status, note) VALUES (?, ?, ?, ?)",
                        (row['id'], 'Submitted', 'Escalated', '[AUTO] System escalated: High/Critical ticket was unattended.'))
                st.success(f"Escalated {len(overdue)} ticket(s)!")
                st.rerun()
        else:
            st.success("✅ No overdue tickets.")

        st.markdown("---")
        st.subheader("🔍 AI Review Queue")
        st.caption("Tickets flagged by the AI for manual admin review (low confidence or fallback mode).")

        review_tickets = df[df.get('needs_review', pd.Series([0]*len(df))).astype(int) == 1] if 'needs_review' in df.columns else pd.DataFrame()

        if len(review_tickets) > 0:
            st.warning(f"Found **{len(review_tickets)}** ticket(s) needing admin review.")
            st.dataframe(review_tickets[['ticket_id', 'category', 'priority', 'department', 'status']], hide_index=True)
        else:
            st.success("✅ No tickets currently need review.")

        # Safety flagged tickets
        st.markdown("---")
        st.subheader("🚨 Safety Flagged Tickets")
        safety_tickets = df[df.get('safety_flag', pd.Series([0]*len(df))).astype(int) == 1] if 'safety_flag' in df.columns else pd.DataFrame()

        if len(safety_tickets) > 0:
            st.error(f"⚠️ Found **{len(safety_tickets)}** ticket(s) with safety concerns.")
            st.dataframe(safety_tickets[['ticket_id', 'category', 'priority', 'department', 'status', 'complaint_text']], hide_index=True)
        else:
            st.success("✅ No safety-flagged tickets.")

    # ──────────────────────────────────────────
    # TAB 4: Campus Insights (Interactive Plotly)
    # ──────────────────────────────────────────
    with tab4:
        st.subheader("📊 Interactive Campus Analytics")
        st.caption("Monitor grievance distributions and trends across the campus in real-time.")

        insights = get_campus_insights()

        if "message" in insights and insights.get("total_grievances") is None:
            st.info(insights["message"])
        else:
            i_col1, i_col2, i_col3 = st.columns(3)
            i_col1.metric("📊 Total Grievances", insights.get("total_grievances", 0))
            i_col2.metric("🔥 Top Problem Category", insights.get("top_category", "N/A"))
            i_col3.metric("📍 Top Problem Location", insights.get("top_location", "N/A"))
            st.metric("🚨 Unresolved Critical Issues", insights.get("unresolved_critical", 0))

            st.markdown("---")
            if not df.empty:
                import plotly.express as px
                
                c1, c2 = st.columns(2)
                
                with c1:
                    fig_cat = px.pie(df, names='category', hole=0.4, title='Complaints by Category', 
                                     color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig_cat.update_layout(margin=dict(t=40, b=10, l=10, r=10))
                    st.plotly_chart(fig_cat, use_container_width=True)
                    
                with c2:
                    fig_stat = px.pie(df, names='status', hole=0.4, title='Current Ticket Statuses',
                                      color_discrete_sequence=px.colors.sequential.Teal)
                    fig_stat.update_layout(margin=dict(t=40, b=10, l=10, r=10))
                    st.plotly_chart(fig_stat, use_container_width=True)
                
                st.markdown("---")
                priority_dept_df = df.groupby(['department', 'priority']).size().reset_index(name='count')
                fig_bar = px.bar(priority_dept_df, x='department', y='count', color='priority', 
                                 title='Priority Levels Across Departments',
                                 barmode='stack',
                                 color_discrete_map={'Critical': '#EF4444', 'High': '#F97316', 'Medium': '#EAB308', 'Low': '#22C55E'})
                st.plotly_chart(fig_bar, use_container_width=True)


def _get_suggested_response(category, priority):
    """Generate a deterministic suggested resolution response for the admin."""
    suggestions = {
        ("IT", "Critical"):     "Network team has been alerted. Recommend deploying backup connectivity while main infrastructure is repaired.",
        ("IT", "High"):         "IT Support ticket logged. Technician should inspect the reported area within 4 hours.",
        ("Hostel", "Critical"): "Contact Hostel Warden immediately. Arrange emergency provisions if basic amenities are disrupted.",
        ("Hostel", "High"):     "Maintenance team dispatched. Student should be informed of estimated repair time.",
        ("Finance", "High"):    "Transaction verification initiated. Cross-check bank statement with portal records.",
        ("Finance", "Medium"):  "Forwarded to Finance Office. Expected resolution within 3-5 working days.",
        ("Security", "Critical"): "Campus security has been alerted. Incident report filed. Physical inspection underway.",
    }
    return suggestions.get((category, priority),
        f"Forwarded to the {DEPARTMENT_MAP.get(category, 'General Administration')} for review and resolution.")
