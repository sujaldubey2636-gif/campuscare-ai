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
if 'follow_up_state' not in st.session_state:
    st.session_state.follow_up_state = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def login_screen():
    # ── HERO SECTION ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #4F46E5; font-size: 3.5rem; font-weight: 800; margin-bottom: 0;'>🎓 CampusCare AI</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #6B7280; font-weight: 400; margin-top: 0;'>Autonomous Agentic Grievance Resolution Portal</h3>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, space, col2 = st.columns([1.2, 0.1, 1.0])
    
    with col1:
        st.markdown("### 🚀 Redefining Campus Operations")
        st.write("CampusCare is not a standard web form. It is an **intelligent autonomous agent** that actively reads, reasons about, and resolves campus issues in real-time.")
        
        st.info("""
        **What makes this system smart?**
        - 🧠 **Deep Extraction:** The AI extracts the core issue, location, duration, and student sentiment.
        - ⚖️ **Transparent Priority Scoring:** Urgency is calculated based on strict parameters like safety hazards and affected student count.
        - 📖 **RAG Policy Engine:** Automatically matches student issues against the official College Rulebook.
        - 🚨 **Safety Intelligence:** Instantly flags critical hazards (fires, short circuits) for immediate human review.
        """)
        st.caption("Powered by Gemini LLM • Agentic Workflow • RAG Architecture")
    
    with col2:
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center;'>Portal Login</h3>", unsafe_allow_html=True)
            st.markdown("---")
            tab1, tab2 = st.tabs(["👨‍🎓 Student Access", "⚙️ Admin Access"])
            
            with tab1:
                st.caption("Use your college email and password")
                stu_email = st.text_input("Student Email Address", placeholder="alice@college.edu")
                stu_pass = st.text_input("Password", type="password", placeholder="pass123")
                if st.button("Secure Login", type="primary", use_container_width=True):
                    if stu_email.strip() and stu_pass.strip():
                        # Verify student exists in DB by email and password
                        student = fetch_one("SELECT * FROM students WHERE LOWER(email) = ? AND password = ?", (stu_email.strip().lower(), stu_pass.strip()))
                        if student:
                            st.session_state.logged_in = True
                            st.session_state.user_role = "Student"
                            st.session_state.student_id = student['id']
                            st.rerun()
                        else:
                            st.error("Invalid email or password. Please try again.")
                    else:
                        st.warning("Please enter both email and password.")
            
            with tab2:
                st.caption("Restricted Administrator Access")
                admin_pass = st.text_input("Admin Password", type="password", placeholder="admin123")
                if st.button("Enter Dashboard", type="primary", use_container_width=True):
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
                st.caption("Enter student credentials to switch views:")
                switch_email = st.text_input("Email", key="switch_stu_email")
                switch_pass = st.text_input("Password", type="password", key="switch_stu_pass")
                if st.button("Switch to Student", use_container_width=True, key="btn_switch_stu"):
                    student = fetch_one("SELECT * FROM students WHERE LOWER(email) = ? AND password = ?", (switch_email.strip().lower(), switch_pass.strip()))
                    if student:
                        st.session_state.user_role = "Student"
                        st.session_state.student_id = student['id']
                        st.session_state.follow_up_state = None
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
            
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
