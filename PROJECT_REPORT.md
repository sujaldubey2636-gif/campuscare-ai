# 🎓 CampusCare AI
**Autonomous Agentic Grievance Resolution Portal**

*A 2nd-Year B.Tech Artificial Intelligence Project*

---

## 📌 1. Introduction
Traditional college grievance systems are nothing more than digital suggestion boxes. Students submit complaints, and human administrators must manually read, categorize, prioritize, and route every single ticket. This causes massive bottlenecks, delays in resolving critical safety hazards, and poor student experience.

**CampusCare AI** solves this by replacing the static web form with an **Autonomous AI Agent**. Powered by Large Language Models (LLMs), the system actively converses with students, understands their issues, cross-references official college policies, and autonomously routes tickets to the correct department with an algorithmic priority score.

---

## 🚀 2. Key AI Features

### A. Conversational "Agentic" Interface
Instead of filling out a boring form, students interact with a chat interface. If a student submits a vague complaint (e.g., *"The Wi-Fi is broken"*), the AI refuses to blindly create a ticket. Instead, it asks a contextual follow-up question (e.g., *"Which hostel block and room are you in?"*), ensuring the IT department gets complete information.

### B. Retrieval-Augmented Generation (RAG) Policy Engine
The AI possesses a dynamic "Knowledge Base" (the College Rulebook). When a student complains about a fee refund or a library fine, the AI searches the rulebook, finds the exact official policy, and explains it to the student in real-time. Administrators can update these rules live, and the AI adapts instantly without any code changes.

### C. Deep Information Extraction
The AI does not just summarize text. It extracts structured JSON data from natural language, identifying:
- The core issue
- The location
- The duration of the problem
- The student's emotional sentiment (calm, frustrated, panicked)
- Safety hazards (e.g., electrical sparks, fires)

### D. Transparent Priority Scoring
To prevent the LLM from randomly guessing priorities, the system uses a hybrid approach. The AI extracts the facts, but **deterministic Python logic** calculates the final score (e.g., +40 points for safety hazards, +20 points for exam deadlines). This ensures the AI is predictable and reliable.

### E. Interactive Admin Dashboards
Administrators are provided with real-time, interactive data visualization (powered by Plotly) to identify systemic campus issues (e.g., identifying that 40% of all critical issues originate from Hostel Block B). 

---

## 🧠 3. The Agent Workflow (Architecture)

When a student submits a message, the `GrievanceAgent` executes a strict 6-step cognitive loop:

1. **Understand & Check Vagueness:** Is the input actionable? If not, ask the user a follow-up question.
2. **Policy Check (RAG):** Call the `search_college_policy` tool to check if a strict college rule applies to this situation.
3. **Analyze:** Extract all structured metadata (location, sentiment, safety risks) via function calling.
4. **Check History & Duplicates:** Check the database for similar open tickets to prevent spam.
5. **Act:** Autonomously generate the database ticket and route it to the correct department (IT, Maintenance, Finance, etc.).
6. **Respond:** Reply to the student in the chat with a summary, the ticket ID, and any applicable college policies.

---

## 🛠️ 4. Technology Stack
- **Frontend & UI:** Streamlit (Python)
- **AI / LLM Core:** Google Gemini 2.5 Flash
- **Database:** SQLite3
- **Data Visualization:** Plotly & Pandas
- **Architecture:** Tool Calling, RAG (Retrieval-Augmented Generation), Agentic Workflows
