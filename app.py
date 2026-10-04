import streamlit as st
import os
from database.seed import seed_database
from database.db import fetch_one
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
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── SESSION STATE INITIALIZATION ──
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'student_id' not in st.session_state:
    st.session_state.student_id = None

def login_screen():
    st.markdown("<h1 style='text-align: center;'>🎓 CampusCare AI Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Intelligent Grievance Resolution System</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container(border=True):
            tab1, tab2 = st.tabs(["👨‍🎓 Student Login", "⚙️ Admin Login"])
            
            with tab1:
                st.markdown("### Student Access")
                st.caption("Log in with your college email (e.g., alice@college.edu)")
                stu_email = st.text_input("Student Email Address")
                if st.button("Login as Student", type="primary", use_container_width=True):
                    if stu_email.strip():
                        # Verify student exists in DB by email
                        student = fetch_one("SELECT * FROM students WHERE LOWER(email) = ?", (stu_email.strip().lower(),))
                        if student:
                            st.session_state.logged_in = True
                            st.session_state.user_role = "Student"
                            st.session_state.student_id = student['id']
                            st.rerun()
                        else:
                            st.error("Email not found in the student database. Please try again.")
                    else:
                        st.warning("Please enter your email address.")
            
            with tab2:
                st.markdown("### Administrator Access")
                st.caption("Enter the secure admin password (demo: admin123)")
                admin_pass = st.text_input("Admin Password", type="password")
                if st.button("Login as Admin", type="primary", use_container_width=True):
                    if admin_pass == "admin123":  # Hardcoded for demo purposes
                        st.session_state.logged_in = True
                        st.session_state.user_role = "Admin"
                        st.rerun()
                    else:
                        st.error("Incorrect password.")

def main():
    if not st.session_state.logged_in:
        login_screen()
    else:
        # ── SIDEBAR NAVIGATION (Logged In) ──
        st.sidebar.title("CampusCare AI")
        
        if st.session_state.user_role == "Student":
            st.sidebar.success(f"Logged in as: **Student ({st.session_state.student_id})**")
        else:
            st.sidebar.error("Logged in as: **Administrator**")
            
        st.sidebar.markdown("---")
        
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_role = None
            st.session_state.student_id = None
            st.session_state.follow_up_state = None # Clear any pending AI questions
            st.rerun()
            
        st.sidebar.markdown("---")
        st.sidebar.caption("Powered by Gemini AI")
        
        # ── ROUTING ──
        if st.session_state.user_role == "Student":
            # Pass the logged in student ID to the dashboard
            render_student_dashboard(st.session_state.student_id)
        elif st.session_state.user_role == "Admin":
            render_admin_dashboard()

if __name__ == "__main__":
    main()
