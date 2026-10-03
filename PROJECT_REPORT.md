# Complete Project Report: CampusCare AI

This document provides a deep dive into every detail of the CampusCare AI project. It explains the purpose, how to use it, and exactly how the underlying code works so you can easily understand and explain it to your professors.

---

## 1. What is the Use of this Project? (Real-World Application)
In typical college environments, students face numerous daily issues: broken hostel Wi-Fi, electricity outages, fee payment errors, or lost library cards. 

**The Problem:** 
Currently, students usually have to figure out which specific department to email, how to format their complaint, or they end up spamming a general admin email. Admins then have to manually read, categorize, prioritize, and forward these emails to the right people.

**The Solution (This Project):** 
CampusCare AI automates this entire administrative bottleneck. A student simply types their problem in plain English (e.g., *"My fan is broken"*). The AI Agent acts as an intelligent digital administrator that instantly:
1. Understands the problem is related to "Facilities" or "Hostel".
2. Knows that it should be routed to "Hostel Maintenance".
3. Determines it is a "Medium" priority.
4. Checks if someone else in that same room already reported it.
5. Files the ticket perfectly into the database.

---

## 2. How to Use the Project

### A. First-Time Setup
1. Open your terminal in the `campuscare-ai` folder.
2. Install the required Python libraries: `pip install -r requirements.txt`
3. Rename the `.env.example` file to `.env`.
4. Open the `.env` file and paste your Gemini API Key: `GEMINI_API_KEY=your_key_here` (You can get a free one from Google AI Studio).

### B. Running the App
1. In the terminal, run: `streamlit run app.py`
2. A browser window will automatically open showing the app.

### C. The Student Workflow
1. Go to the **Student Dashboard**.
2. Enter your ID (e.g., `STU001`) and Location (e.g., `Block A`).
3. Type a complaint naturally: *"The internet has been disconnected for 3 days in our block."*
4. Click **Analyze & Submit**.
5. You will see the AI process it, generate a `GRV-XXXX` ticket, assign it `High` priority, and route it to `IT Support`.

### D. The Admin Workflow
1. Use the sidebar on the left to switch to the **Admin Dashboard**.
2. Here, you (as the administrator) can see all tickets.
3. You can filter by "Pending" or "High Priority".
4. Select a ticket, write a resolution note (e.g., *"Technician dispatched"*), and change the status to **In Progress** or **Resolved**.

---

## 3. How the Code Works (Module-by-Module)

Here is exactly what happens behind the scenes in your code:

### 1. `app.py` (The Main UI Entry Point)
- **What it does:** This is the file that Streamlit runs. It creates the sidebar navigation menu.
- **How it works:** It uses `st.sidebar.radio` to let the user switch between the Student UI and Admin UI. Depending on what you click, it calls functions from either `ui/student.py` or `ui/admin.py`.

### 2. `database/db.py` & `database/seed.py` (The Database)
- **What it does:** Manages the SQLite database where all tickets are stored.
- **How it works:** 
  - `db.py` contains SQL commands (`CREATE TABLE`, `INSERT`, `SELECT`). It creates tables for `students`, `departments`, and `grievances`. 
  - `seed.py` runs automatically the first time you start the app. It inserts dummy departments and student records into the database so you have data to work with immediately.

### 3. `ui/student.py` & `ui/admin.py` (The Dashboards)
- **What it does:** Draws the buttons, text boxes, and tables on the screen.
- **How it works:** 
  - In `student.py`, we use `st.text_area` to get the complaint. When the user clicks submit, it takes that text and sends it to the AI Agent (`GrievanceAgent().run(...)`).
  - In `admin.py`, we use `pandas` to take the database data and display it as a nice, filterable table using `st.dataframe`.

### 4. `agent/tools.py` (The AI's Hands)
- **What it does:** These are standard Python functions that the AI is allowed to "press" or "call".
- **How it works:**
  - `create_grievance_ticket(...)`: Takes the extracted data, generates a random `GRV-` ID, and saves it to the database.
  - `check_duplicate_complaints(...)`: This uses Machine Learning (`scikit-learn`). It converts all existing complaints into mathematical vectors (TF-IDF) and measures the angle between them (Cosine Similarity). If the similarity score is high (above 0.65), it means the complaints are basically saying the same thing, so it marks it as a duplicate!

### 5. `agent/grievance_agent.py` (The AI Brain) **[MOST IMPORTANT]**
- **What it does:** This is where the magic happens. It connects to Google Gemini and manages the "Agentic Loop".
- **How it works:**
  1. We give Gemini a **System Prompt**: *"You are an AI agent. You must classify complaints, assign priority, and use tools..."*
  2. We give Gemini a list of the tools from `tools.py`.
  3. We send the student's complaint to Gemini.
  4. Gemini reads it, thinks, and replies not with a chat message, but with a **Tool Call request** (e.g., *"Run the duplicate checker tool on this text"*).
  5. Our Python code automatically runs that tool, gets the result, and feeds the result back to Gemini.
  6. Gemini then decides on the final action (e.g., *"Okay, no duplicates found. Now call the create ticket tool with Priority=High"*).
  7. If you don't have internet or an API key, the script detects this and safely falls back to a basic Python `if/else` keyword checker (`_fallback_mode`) so your app never crashes during a demo.

---

## 4. Summary for Viva/Presentation
If a professor asks what you built, you can say:
> *"I built an Agentic AI workflow for campus management. Instead of a standard chatbot that just talks to the user, my system uses an LLM as a reasoning engine. The AI understands the complaint, decides whether to check for duplicates using TF-IDF vector similarity, calculates priority based on context, and autonomously triggers Python functions to insert structured data into a local SQLite database."*
