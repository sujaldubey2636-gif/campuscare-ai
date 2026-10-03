import streamlit as st
import os
from database.seed import seed_database
from ui.student import render_student_dashboard
from ui.admin import render_admin_dashboard

# Ensure database is seeded on first run
db_path = os.path.join(os.path.dirname(__file__), 'data', 'campuscare.db')
if not os.path.exists(db_path):
    print("Database not found. Initializing and seeding...")
    seed_database()

st.set_page_config(
    page_title="CampusCare AI",
    page_icon="🎓",
    layout="wide"
)

def main():
    st.sidebar.title("CampusCare AI Navigation")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio("Go to", ["Student Dashboard", "Admin Dashboard"])
    
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**Note:** This is a student AI project built with Gemini to automatically resolve and route campus grievances."
    )
    
    if page == "Student Dashboard":
        render_student_dashboard()
    elif page == "Admin Dashboard":
        render_admin_dashboard()

if __name__ == "__main__":
    main()
