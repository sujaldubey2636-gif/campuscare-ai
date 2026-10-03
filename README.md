# CampusCare AI — Intelligent College Grievance Resolution Agent

## 1. Project Title
CampusCare AI

## 2. Problem Statement
College students face problems related to hostels, academics, examinations, fees, IT, and campus facilities. However, they often don't know which department to contact, how to express the urgency, or whether someone else has already reported the same issue (like a power outage). 

## 3. Motivation
To build an AI-powered system that removes the friction from grievance reporting. By using an AI Agent, the system intelligently processes raw natural-language complaints and completely automates the classification, prioritization, routing, and deduplication of grievances.

## 4. Objectives
- Automatically classify student complaints into predefined campus categories.
- Assess the priority level based on the context of the complaint.
- Route the complaint to the correct administrative department.
- Detect highly similar, existing complaints to prevent duplicate ticket spam.
- Provide a clear, transparent explanation for every AI decision.

## 5. Features
- **Student Dashboard:** Submit grievances in natural language and track their status.
- **Admin Dashboard:** Monitor, update, and manage grievances with filters and analytics.
- **AI Agent Orchestration:** Uses the Gemini model with Tool Calling (Function Calling).
- **Duplicate Detection:** Uses TF-IDF and Cosine Similarity to find matching active complaints.

## 6. AI Agent Explanation
This project does **not** use a simple Chatbot (User -> LLM -> Response). Instead, it implements an **AI Agent**. The Agent reads the user's complaint, determines what needs to be done, and then *calls specific Python tools* (`check_duplicate_complaints`, `create_grievance_ticket`, `link_to_existing_grievance`). The Agent makes active decisions and interacts with the database.

## 7. LLM Usage
The Large Language Model (Gemini 2.5 Flash) is strictly used for its **Natural Language Understanding (NLU)** and reasoning capabilities. It understands the context, extracts entities (like location and number of people affected), and decides which tools to invoke. Deterministic operations (saving to the database, generating IDs) are strictly handled by Python.

## 8. Architecture
```mermaid
flowchart TD
    A[Student (Streamlit UI)] -->|Submits Complaint| B[Backend / Grievance Agent]
    B -->|Analyzes Text| C{Agent Tool Selection}
    C -->|Classify, Prioritize, Route| D[check_duplicate_complaints]
    D -->|If Duplicate| E[link_to_existing_grievance]
    D -->|If New| F[create_grievance_ticket]
    E --> G[(SQLite Database)]
    F --> G
    G --> H[Admin (Streamlit UI)]
```

## 9. Workflow
1. Student enters ID, location, and complaint text.
2. The `GrievanceAgent` (powered by Gemini) receives the prompt.
3. The Agent analyzes the text and decides to call the `check_duplicate_complaints` tool.
4. Python runs TF-IDF vectorization against existing database entries.
5. If a duplicate exists, the Agent calls `link_to_existing_grievance`. Otherwise, it calls `create_grievance_ticket` with the determined Category, Priority, and Department.
6. The frontend displays the ticket ID and the AI's reasoning.

## 10. Technology Stack
- **Frontend / UI:** Streamlit
- **Backend Language:** Python 3
- **AI / LLM:** Google Gemini API (`google-genai` SDK)
- **Database:** SQLite3
- **Machine Learning (Similarity):** `scikit-learn` (TF-IDF & Cosine Similarity)

## 11. Database Design
- `students`: `id` (PK), `name`, `email`, `course`, `year`
- `departments`: `id` (PK), `department_name`
- `grievances`: `id` (PK), `ticket_id`, `student_id`, `complaint_text`, `category`, `priority`, `department`, `location`, `status`, `ai_reason`
- `grievance_updates`: `id` (PK), `grievance_id`, `old_status`, `new_status`, `note`

---

## 12. Installation Steps
1. Ensure you have Python 3.9+ installed.
2. Open a terminal and navigate to the project folder.
3. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 13. Environment Setup
1. Copy `.env.example` to a new file named `.env`.
2. Get an API key from Google AI Studio (https://aistudio.google.com/).
3. Paste the API key into the `.env` file:
   ```env
   GEMINI_API_KEY=your_actual_api_key
   ```

## 14. How to Run
Run the Streamlit application using this exact command:
```bash
streamlit run app.py
```
> **Note:** The application will automatically initialize and seed the SQLite database on its first run.

## 15. Demo Instructions
1. **Start the app** and open the `Student Dashboard`.
2. **Enter Student ID:** `STU001`
3. **Submit a Complaint:** "The Wi-Fi in Block B has not been working since yesterday. I have an online exam tomorrow."
4. **Observe AI Analysis:** The app will output `Category: IT`, `Priority: High/Critical`, and `Department: IT Support`.
5. **Switch to Admin Dashboard:** Use the sidebar to switch views.
6. **Update Status:** Find your new ticket, add a resolution note, and change the status from `Submitted` to `In Progress` or `Resolved`.
7. **Demonstrate Duplicates (Optional):** Submit the exact same Wi-Fi complaint again from the Student Dashboard. The AI should detect it and link it rather than creating a new ticket.

## 16. Example Inputs and Outputs
**Input:** "My hostel room has no electricity."
**Output:** Category = Hostel, Priority = High, Department = Hostel Administration. Action = Create Ticket.

**Input:** "My fee payment has been deducted from my bank account but still shows unpaid."
**Output:** Category = Finance, Priority = Medium, Department = Finance Office. Action = Create Ticket.

## 17. Limitations
- Duplicate detection uses simple TF-IDF which relies on keyword overlap; it might miss semantically identical complaints that use completely different vocabulary.
- The system relies on a third-party LLM API, meaning it requires internet access to fully function (though a basic keyword-based fallback is included).

## 18. Future Scope
- Replace TF-IDF with semantic embeddings (e.g., Gemini Embeddings) for better duplicate detection.
- Add email or SMS notifications for students when their ticket status changes.
- Implement automated assignment to specific staff members based on workload.

---

## 19. Academic Explanation
This project demonstrates several core AI concepts:
- **Intelligent Agents:** We implemented a goal-directed Agent that perceives its environment (the complaint text and database state), reasons about it, and takes actions (invoking tools).
- **Knowledge Representation / Rule-based reasoning:** We map specific categories to specific departments (Router Tool), combining AI with deterministic rules.
- **Uncertainty/Similarity:** The duplicate detection tool calculates a cosine similarity score (0.0 to 1.0) and uses a threshold to handle the uncertainty of whether two texts represent the same real-world issue.
- **Natural Language Understanding:** The LLM extracts structured data from unstructured text, bypassing the need for complex, brittle Regex rules.

---

## 20. Viva Questions & Answers

**Q1: Where is the AI Agent located in your code?**
A: The agent logic is located in `agent/grievance_agent.py`. It uses the Gemini SDK to configure tools and process the student's prompt.

**Q2: How is this different from a normal chatbot like ChatGPT?**
A: A normal chatbot just returns text to the user. This AI Agent has access to specific functions (Tools) in `agent/tools.py`. It decides *which* tool to call, and uses the tool to actually write data into our SQLite database.

**Q3: How does the AI decide which department to route the complaint to?**
A: The AI analyzes the complaint to determine its Category. In our prompt instructions and agent design, we map categories to specific departments (e.g., IT category goes to IT Support).

**Q4: How did you implement duplicate detection? Did you use the LLM for it?**
A: No, using an LLM for every database search would be slow and expensive. I used `scikit-learn`'s `TfidfVectorizer` and `cosine_similarity` in `agent/tools.py`. It mathematically compares the new text against existing unresolved tickets.

**Q5: What happens if the Gemini API is down or the internet disconnects?**
A: The application has a fallback mode in `grievance_agent.py`. It uses basic Python keyword matching (e.g., checking for words like "wi-fi" or "fee") to categorize and create the ticket deterministically.

**Q6: Why did you use SQLite instead of MySQL or MongoDB?**
A: SQLite is serverless and stores data in a simple `.db` file. This makes the project highly portable, easy to set up without installing database servers, and perfect for a demonstration or student project.

**Q7: Can a student manipulate the AI into changing their grades?**
A: No. The AI is constrained by the tools it has. The tools only allow it to create or link grievance tickets. It does not have access to a "change_grade" function or database table. 

**Q8: What is Streamlit and why did you use it?**
A: Streamlit is a Python framework for building data web applications quickly. I used it because it allows me to build both the student and admin UI entirely in Python without needing to write HTML/CSS or React.

**Q9: How did you ensure the AI's response is structured and not just a paragraph of text?**
A: By using "Function Calling" (Tool Calling). We define the strict schema (arguments like `student_id`, `priority`, `category`) that the AI must output when calling the `create_grievance_ticket` tool.

**Q10: What is the purpose of the `.env` file?**
A: It securely stores environment variables, specifically the `GEMINI_API_KEY`. This ensures the private API key is not hard-coded directly into the source code, which is a major security best practice.
