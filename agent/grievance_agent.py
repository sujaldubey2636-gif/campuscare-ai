"""
CampusCare AI — Grievance Resolution Agent
============================================
This is the CORE AI AGENT. It follows this decision workflow:

    Observe → Understand → Ask (if needed) → Reason → Decide → Use Tools → Act

Architecture:
    Phase 1 (Analyze):  LLM reads the complaint and calls analyze_complaint()
                        to extract structured info. Priority is computed by Python.
    Phase 2 (Act):      Agent checks for duplicates, checks student history,
                        and creates or links a ticket based on its analysis.

The LLM is used for understanding natural language.
Priority scoring, ticket creation, and database operations are handled by Python.
"""

import os
import json
from google import genai
from google.genai import types
from agent.tools import (
    analyze_complaint,
    check_duplicate_complaints,
    get_student_history,
    create_grievance_ticket,
    link_to_existing_grievance,
    search_college_policy,
    SAFETY_KEYWORDS,
    DEPARTMENT_MAP,
)
from dotenv import load_dotenv

load_dotenv()


class GrievanceAgent:
    """
    The central AI Agent for CampusCare.
    It orchestrates LLM understanding + deterministic Python tools.
    """

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            self.client = None
            print("Warning: GEMINI_API_KEY is not set. Agent will run in fallback/demo mode.")
        else:
            self.client = genai.Client(api_key=api_key)
            self.model_id = os.environ.get("MODEL_NAME", "gemini-3.8-flash")

    # ──────────────────────────────────────────────────────
    # MAIN ENTRY POINT
    # ──────────────────────────────────────────────────────

    def run(self, student_id: str, complaint_text: str, location: str):
        """
        Main agentic loop. Returns a result dict containing:
          - ticket_info: the created/linked ticket data
          - agent_response: the final text response from the agent
          - follow_up_question: (optional) if the agent needs more info
          - analysis: (optional) structured analysis data
        """
        if not self.client:
            return self._fallback_mode(student_id, complaint_text, location)

        # Resilient Model Failover: Try primary model first, then fallback to flash-latest if spike/error occurs
        candidate_models = [self.model_id, "gemini-flash-latest", "gemini-3.8-flash"]
        # Remove duplicates while preserving order
        candidate_models = list(dict.fromkeys(candidate_models))

        for model in candidate_models:
            try:
                return self._agentic_loop(student_id, complaint_text, location, active_model=model)
            except Exception as e:
                print(f"Agent warning with {model}: {e}. Trying next candidate...")

        print("All remote model candidates encountered errors. Engaging deterministic fallback mode.")
        return self._fallback_mode(student_id, complaint_text, location)

    # ──────────────────────────────────────────────────────
    # AGENTIC LOOP (Gemini with Tool Calling)
    # ──────────────────────────────────────────────────────

    def _agentic_loop(self, student_id: str, complaint_text: str, location: str, active_model: str = None):
        target_model = active_model or self.model_id
        system_instruction = """
You are CampusCare AI, an advanced college grievance resolution agent.
You act as an intelligent campus administrator who THINKS before acting.

YOUR WORKFLOW (follow strictly):

STEP 1 — UNDERSTAND & CHECK VAGUENESS
Read the complaint carefully. If the complaint is too vague to classify properly
(e.g., "things are bad", "help me", "there's a problem"), you MUST respond with
a short, helpful follow-up question. Do NOT call any tools yet.
Only ask ONE follow-up question maximum. Keep it specific and actionable.

STEP 2 — POLICY CHECK (RAG)
Call `search_college_policy` with a keyword based on the student's issue to check if there is an official college rule governing it (e.g., refunds, library fines, hostel leave).

STEP 3 — ANALYZE
Call `analyze_complaint` with these arguments:
- complaint_text: the original text
- category: your best classification (Academic/Examination/Hostel/Finance/IT/Library/Transport/Facilities/Security/Other)
- category_confidence: how confident you are (0-100)
- sentiment: one of calm/frustrated/angry/panicked
- issue: a short 3-8 word summary of the core problem
- location: where on campus (use the student's provided location if available)
- duration: how long the issue has existed (extract from text, or "" if unknown)
- affected_count: approximate number of students affected (0 if unknown)
- equipment_or_service: what specific thing is broken/affected
- has_deadline_pressure: true if exams/deadlines are mentioned
- safety_risk_detected: true if there is ANY potential physical danger
- root_cause_hypothesis: your best guess at the underlying cause (present as hypothesis, not fact)
- applicable_policy: the exact text of the policy returned by search_college_policy (if any)

STEP 4 — CHECK HISTORY & DUPLICATES
After analyzing, call `get_student_history` to check if this student has prior related issues.
Then call `check_duplicate_complaints` to see if a similar complaint already exists.

STEP 5 — ACT
Based on the analysis and duplicate check results:
- If a duplicate exists (is_duplicate=True): call `link_to_existing_grievance`
- If no duplicate: call `create_grievance_ticket` using the data from your analysis result.
  Pass ALL fields from the analyze_complaint result (category, priority, department, ai_reason,
  extracted_info, confidence, safety_flag, needs_review).

STEP 6 — RESPOND
After acting, provide a brief, empathetic student-facing summary. Mention the ticket ID.
If there's a safety concern, clearly recommend the student also contact campus security directly.
If an official policy applies to their case, clearly mention the policy in your response so the student is immediately informed.
"""

        # All tools the agent can call
        tools = [
            search_college_policy,
            analyze_complaint,
            check_duplicate_complaints,
            get_student_history,
            create_grievance_ticket,
            link_to_existing_grievance,
        ]

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=tools,
            temperature=0.1,
        )

        prompt = (
            f"Student ID: {student_id}\n"
            f"Location: {location}\n"
            f"Complaint: {complaint_text}\n\n"
            f"Follow your workflow: understand -> policy check -> analyze -> check history -> check duplicates -> act."
        )

        chat = self.client.chats.create(model=target_model, config=config)
        response = chat.send_message(prompt)

        # Track state across tool-calling turns
        analysis_result = None
        final_ticket_info = None
        follow_up_question = None

        # The agent may need several turns
        for _ in range(8):
            if response.function_calls:
                for fc in response.function_calls:
                    name = fc.name
                    args = fc.args

                    # Execute the tool
                    if name == "search_college_policy":
                        result = search_college_policy(**args)
                    elif name == "analyze_complaint":
                        result = analyze_complaint(**args)
                        analysis_result = result
                    elif name == "check_duplicate_complaints":
                        result = check_duplicate_complaints(**args)
                    elif name == "get_student_history":
                        result = get_student_history(**args)
                    elif name == "create_grievance_ticket":
                        result = create_grievance_ticket(**args)
                        final_ticket_info = result
                        # Merge analysis data into ticket info
                        if analysis_result:
                            final_ticket_info.update({
                                'category': analysis_result.get('category', args.get('category', 'Unknown')),
                                'priority': analysis_result.get('priority', args.get('priority', 'Unknown')),
                                'department': analysis_result.get('department', args.get('department', 'Unknown')),
                                'ai_reason': analysis_result.get('ai_reason', args.get('ai_reason', '')),
                                'extracted_info': analysis_result.get('extracted_info', ''),
                                'confidence': analysis_result.get('confidence', ''),
                                'safety_flag': analysis_result.get('safety_flag', 0),
                                'needs_review': analysis_result.get('needs_review', 0),
                                'priority_score': analysis_result.get('priority_score', 0),
                                'priority_factors': analysis_result.get('priority_factors', []),
                            })
                        else:
                            final_ticket_info.update({
                                'category': args.get('category', 'Unknown'),
                                'priority': args.get('priority', 'Unknown'),
                                'department': args.get('department', 'Unknown'),
                                'ai_reason': args.get('ai_reason', ''),
                            })
                    elif name == "link_to_existing_grievance":
                        result = link_to_existing_grievance(**args)
                        final_ticket_info = result
                        if analysis_result:
                            final_ticket_info.update({
                                'category': analysis_result.get('category', 'N/A'),
                                'priority': analysis_result.get('priority', 'N/A'),
                                'department': analysis_result.get('department', 'N/A'),
                                'ai_reason': "Linked to existing duplicate issue.",
                                'extracted_info': analysis_result.get('extracted_info', ''),
                                'confidence': analysis_result.get('confidence', ''),
                                'safety_flag': analysis_result.get('safety_flag', 0),
                                'needs_review': 0,
                            })

                    # Send tool result back to the model
                    response = chat.send_message(
                        types.Part.from_function_response(name=name, response={"result": result})
                    )
            else:
                # No function calls — the model is responding with text
                # Check if this is a follow-up question (no ticket created yet)
                if not final_ticket_info:
                    follow_up_question = response.text
                break

        # If the agent asked a follow-up question instead of creating a ticket
        if follow_up_question and not final_ticket_info:
            return {
                "follow_up_question": follow_up_question,
                "ticket_info": None,
                "agent_response": follow_up_question,
                "analysis": analysis_result,
            }

        # If somehow no ticket was created, use fallback
        if not final_ticket_info:
            return self._fallback_mode(student_id, complaint_text, location)

        return {
            "ticket_info": final_ticket_info,
            "agent_response": response.text if response.text else "Ticket processed successfully.",
            "analysis": analysis_result,
            "follow_up_question": None,
        }

    # ──────────────────────────────────────────────────────
    # FALLBACK MODE (No API Key / Offline Demo)
    # ──────────────────────────────────────────────────────

    def _fallback_mode(self, student_id: str, complaint_text: str, location: str):
        """Deterministic fallback when the Gemini API is unavailable."""
        text_lower = complaint_text.lower()

        # ── Classify by keywords ──
        keyword_map = {
            "IT":          ["wi-fi", "wifi", "internet", "network", "server", "login", "password"],
            "Hostel":      ["hostel", "room", "electricity", "water supply", "mess", "warden"],
            "Finance":     ["fee", "payment", "refund", "scholarship", "challan"],
            "Examination": ["exam", "hall ticket", "result", "marksheet", "revaluation"],
            "Library":     ["library", "book", "library card", "journal"],
            "Transport":   ["bus", "transport", "shuttle", "route"],
            "Facilities":  ["projector", "chair", "fan", "classroom", "lab", "ac", "air conditioning"],
            "Security":    ["security", "theft", "safety", "guard", "cctv", "stranger"],
            "Academic":    ["professor", "lecture", "attendance", "syllabus", "assignment"],
        }

        category = "Other"
        for cat, keywords in keyword_map.items():
            if any(kw in text_lower for kw in keywords):
                category = cat
                break

        department = DEPARTMENT_MAP.get(category, "General Administration")

        # ── Safety check ──
        is_safety = any(kw in text_lower for kw in SAFETY_KEYWORDS)

        # ── Extract basic info ──
        # Simple number extraction for affected count
        affected = 0
        for word in complaint_text.split():
            if word.isdigit():
                affected = int(word)
                break

        # ── Call our own analyze tool for transparent scoring ──
        analysis = analyze_complaint(
            complaint_text=complaint_text,
            category=category,
            category_confidence=60,  # Lower confidence in fallback
            sentiment="frustrated" if any(w in text_lower for w in ["urgent", "please", "help"]) else "calm",
            issue=f"{category} related issue",
            location=location,
            duration="unknown",
            affected_count=affected,
            equipment_or_service="",
            has_deadline_pressure=any(w in text_lower for w in ["exam", "deadline", "submission"]),
            safety_risk_detected=is_safety,
            root_cause_hypothesis="Unable to determine in fallback mode — requires staff verification.",
        )

        priority = analysis['priority']

        # ── Check duplicates ──
        dup_check = check_duplicate_complaints(complaint_text, category)
        if dup_check.get("is_duplicate"):
            res = link_to_existing_grievance(student_id, complaint_text, dup_check["ticket_id"])
            res.update({
                'category': category,
                'priority': priority,
                'department': department,
                'ai_reason': analysis['ai_reason'],
                'extracted_info': analysis['extracted_info'],
                'confidence': analysis['confidence'],
                'safety_flag': analysis['safety_flag'],
                'needs_review': 1,
                'priority_score': analysis['priority_score'],
                'priority_factors': analysis['priority_factors'],
            })
            return {"ticket_info": res, "agent_response": "Processed using fallback mode.", "analysis": analysis}

        # ── Create ticket ──
        res = create_grievance_ticket(
            student_id=student_id,
            complaint_text=complaint_text,
            category=category,
            priority=priority,
            department=department,
            location=location,
            ai_reason=analysis['ai_reason'],
            extracted_info=analysis['extracted_info'],
            confidence=analysis['confidence'],
            safety_flag=analysis['safety_flag'],
            needs_review=1,  # Always flag fallback tickets for review
        )
        res.update({
            'category': category,
            'priority': priority,
            'department': department,
            'ai_reason': analysis['ai_reason'],
            'extracted_info': analysis['extracted_info'],
            'confidence': analysis['confidence'],
            'safety_flag': analysis['safety_flag'],
            'needs_review': 1,
            'priority_score': analysis['priority_score'],
            'priority_factors': analysis['priority_factors'],
        })

        return {
            "ticket_info": res,
            "agent_response": "[Fallback Mode] Processed without AI — admin review recommended.",
            "analysis": analysis,
            "follow_up_question": None,
        }
