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

def inject_custom_css():
    st.markdown("""
    <style>
        /* Modern Button Styling */
        .stButton>button[kind="primary"] {
            background-color: #6366F1; /* Indigo */
            color: white;
            border-radius: 8px;
            font-weight: bold;
            border: none;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            transition: all 0.2s ease;
        }
        .stButton>button[kind="primary"]:hover {
            background-color: #4F46E5;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            transform: translateY(-1px);
        }
        
        /* Softer Cards/Containers */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px;
            border: 1px solid #E5E7EB;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
            background-color: #FFFFFF;
        }
        
        /* Main Text Color */
        .stMarkdown {
            color: #374151;
        }
        
        /* Hide default Streamlit footer */
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

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
            
            # Fast-switch to Admin
            with st.sidebar.expander("⚙️ Switch to Admin Portal"):
                st.caption("Enter admin password to switch views:")
                switch_pass = st.text_input("Password", type="password", key="switch_admin_pass")
                if st.button("Switch to Admin", use_container_width=True, key="btn_switch_admin"):
                    if switch_pass == "admin123":
                        st.session_state.user_role = "Admin"
                        st.session_state.student_id = None
                        st.session_state.follow_up_state = None
                        st.rerun()
                    else:
                        st.error("Incorrect password.")
        else:
            st.sidebar.error("Logged in as: **Administrator**")
            
            # Fast-switch to Student
            with st.sidebar.expander("👨‍🎓 Switch to Student Portal"):
                st.caption("Enter student email to switch views:")
                switch_email = st.text_input("Email", key="switch_stu_email")
                if st.button("Switch to Student", use_container_width=True, key="btn_switch_stu"):
                    student = fetch_one("SELECT * FROM students WHERE LOWER(email) = ?", (switch_email.strip().lower(),))
                    if student:
                        st.session_state.user_role = "Student"
                        st.session_state.student_id = student['id']
                        st.session_state.follow_up_state = None
                        st.rerun()
                    else:
                        st.error("Email not found.")
            
        st.sidebar.markdown("---")
        
        if st.sidebar.button("🚪 Logout completely", use_container_width=True):
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
