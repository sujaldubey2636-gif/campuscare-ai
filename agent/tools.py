"""
CampusCare AI — Agent Tools
============================
These are the Python functions (tools) that the AI Agent can call.
The Agent DECIDES which tool to use; the tools themselves are deterministic Python.

Tools:
  1. analyze_complaint()      — Extract structured info + assess priority with transparent scoring
  2. check_duplicate_complaints() — TF-IDF + cosine similarity to find existing similar issues
  3. get_student_history()     — Fetch a student's previous grievances from the database
  4. create_grievance_ticket() — Save a new grievance into the database
  5. link_to_existing_grievance() — Link a complaint to an already-open ticket
  6. get_campus_insights()     — Aggregate data about recurring campus problems
"""

import uuid
import json
import datetime
from database.db import execute_query, fetch_all, fetch_one
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ──────────────────────────────────────────────────────────────
# TOOL 1: Structured Complaint Analysis + Priority Scoring
# ──────────────────────────────────────────────────────────────

# Safety keywords that trigger an immediate safety flag
SAFETY_KEYWORDS = [
    "fire", "spark", "electric shock", "electrocution", "flood", "flooding",
    "collapse", "gas leak", "smoke", "harassment", "assault", "stalking",
    "threat", "weapon", "snake", "injury", "bleeding", "unconscious",
    "emergency", "danger", "sparking wire", "short circuit",
]

# Category-to-department mapping (deterministic, not LLM-decided)
DEPARTMENT_MAP = {
    "Academic":     "General Administration",
    "Examination":  "Examination Cell",
    "Hostel":       "Hostel Administration",
    "Finance":      "Finance Office",
    "IT":           "IT Support",
    "Library":      "Library Administration",
    "Transport":    "General Administration",
    "Facilities":   "Maintenance Department",
    "Security":     "Security Office",
    "Other":        "General Administration",
}


def search_college_policy(query_topic: str) -> dict:
    """
    Search the official CampusCare College Rulebook for policies matching the student's issue.
    Call this to check if a student's request is governed by a strict college rule 
    (e.g., refund policies, library fines, hostel curfews).

    Args:
        query_topic: A short phrase describing the rule to look up (e.g., 'fee refund', 'hostel curfew').

    Returns:
        dict with the most relevant policy text, or a message if no policy was found.
    """
    import os
    rulebook_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'college_rulebook.md')
    
    if not os.path.exists(rulebook_path):
        return {"policy_found": False, "message": "Rulebook not found."}
        
    try:
        with open(rulebook_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        sections = content.split('##')
        best_section = None
        
        query_lower = query_topic.lower()
        # Basic keyword match against sections
        for section in sections[1:]: # Skip the main title
            if any(word in section.lower() for word in query_lower.split()):
                best_section = section.strip()
                break # Just grab the first matching section for simplicity
                
        if best_section:
            return {
                "policy_found": True, 
                "policy_text": best_section,
                "message": f"Found matching policy in section: {best_section.splitlines()[0]}"
            }
        else:
            return {"policy_found": False, "message": "No specific policy found for this query."}
    except Exception as e:
        return {"policy_found": False, "message": f"Error reading policy: {str(e)}"}


def analyze_complaint(
    complaint_text: str,
    category: str,
    category_confidence: int,
    sentiment: str,
    issue: str,
    location: str = "",
    duration: str = "",
    affected_count: int = 0,
    equipment_or_service: str = "",
    has_deadline_pressure: bool = False,
    safety_risk_detected: bool = False,
    root_cause_hypothesis: str = "",
    applicable_policy: str = "",
) -> dict:
    """
    Analyze a student's complaint and compute structured information and priority.
    The LLM fills in the arguments by understanding the complaint text.
    The priority is then computed by deterministic Python scoring, NOT by the LLM.

    Args:
        complaint_text: The original complaint text.
        category: One of Academic, Examination, Hostel, Finance, IT, Library, Transport, Facilities, Security, Other.
        category_confidence: How confident the AI is about the category (0-100).
        sentiment: One of calm, frustrated, angry, panicked.
        issue: A short summary of the core problem (e.g., "Wi-Fi outage").
        location: Where on campus the issue is (e.g., "Block B, Floor 3").
        duration: How long the issue has persisted (e.g., "since yesterday").
        affected_count: Approximate number of students affected.
        equipment_or_service: What specific equipment/service is involved.
        has_deadline_pressure: True if the student mentions exams, deadlines, or submissions.
        safety_risk_detected: True if the complaint involves any potential safety hazard.
        root_cause_hypothesis: AI's best guess at the underlying technical/admin cause.
        applicable_policy: If a college rule applies, the exact text of the rule.

    Returns:
        dict with priority, department, safety_flag, confidence, extracted_info, needs_review, ai_reason.
    """
    text_lower = complaint_text.lower()

    # ── DETERMINISTIC PRIORITY SCORING ──
    # The LLM provides the facts; Python computes the score transparently.
    score = 0
    factors = []

    # Factor 1: Safety
    is_safety = safety_risk_detected or any(kw in text_lower for kw in SAFETY_KEYWORDS)
    if is_safety:
        score += 40
        factors.append("Safety hazard detected (+40)")

    # Factor 2: Number of people affected
    if affected_count >= 50:
        score += 25
        factors.append(f"{affected_count} students affected (+25)")
    elif affected_count >= 10:
        score += 15
        factors.append(f"{affected_count} students affected (+15)")
    elif affected_count >= 2:
        score += 5
        factors.append(f"{affected_count} students affected (+5)")

    # Factor 3: Duration / ongoing issue
    duration_lower = duration.lower() if duration else ""
    if any(w in duration_lower for w in ["days", "week", "month"]):
        score += 15
        factors.append(f"Issue ongoing for {duration} (+15)")
    elif any(w in duration_lower for w in ["yesterday", "last night", "hours", "since"]):
        score += 10
        factors.append(f"Issue ongoing since {duration} (+10)")

    # Factor 4: Deadline/exam pressure
    if has_deadline_pressure or any(w in text_lower for w in ["exam", "deadline", "submission", "viva"]):
        score += 10
        factors.append("Academic deadline pressure (+10)")

    # Factor 5: Service interruption
    if any(w in text_lower for w in ["not working", "broken", "down", "outage", "disconnected", "failed"]):
        score += 10
        factors.append("Service interruption detected (+10)")

    # Factor 6: Sentiment escalation
    if sentiment in ["angry", "panicked"]:
        score += 5
        factors.append(f"Student sentiment: {sentiment} (+5)")

    # ── CONVERT SCORE TO PRIORITY LEVEL ──
    if score >= 40:
        priority = "Critical"
    elif score >= 25:
        priority = "High"
    elif score >= 10:
        priority = "Medium"
    else:
        priority = "Low"

    # ── DEPARTMENT ROUTING (deterministic) ──
    department = DEPARTMENT_MAP.get(category, "General Administration")

    # ── CONFIDENCE & REVIEW FLAGS ──
    needs_review = 1 if category_confidence < 70 else 0
    confidence_data = {
        "category_confidence": category_confidence,
        "priority_score": score,
        "priority_factors": factors,
    }

    # ── BUILD EXTRACTED INFO ──
    extracted = {
        "issue": issue,
        "location": location,
        "duration": duration,
        "affected_count": affected_count,
        "equipment_or_service": equipment_or_service,
        "has_deadline_pressure": has_deadline_pressure,
        "sentiment": sentiment,
        "safety_risk": is_safety,
        "root_cause_hypothesis": root_cause_hypothesis,
        "applicable_policy": applicable_policy,
    }

    # ── BUILD AI REASON ──
    reason_parts = [
        f"Sentiment: {sentiment}",
        f"Issue: {issue}",
    ]
    if root_cause_hypothesis:
        reason_parts.append(f"Hypothesis: {root_cause_hypothesis}")
    reason_parts.append(f"Priority Score: {score}/100 ({' -> '.join(factors) if factors else 'No escalation factors'})")
    if is_safety:
        reason_parts.append("⚠️ SAFETY FLAG: Immediate human review recommended")
    if needs_review:
        reason_parts.append("🔍 LOW CONFIDENCE: AI is uncertain about classification — admin review required")
    ai_reason = " | ".join(reason_parts)

    return {
        "category": category,
        "priority": priority,
        "department": department,
        "safety_flag": 1 if is_safety else 0,
        "needs_review": needs_review,
        "confidence": json.dumps(confidence_data),
        "extracted_info": json.dumps(extracted),
        "ai_reason": ai_reason,
        "priority_score": score,
        "priority_factors": factors,
    }


# ──────────────────────────────────────────────────────────────
# TOOL 2: Duplicate Detection (TF-IDF + Cosine Similarity)
# ──────────────────────────────────────────────────────────────

def check_duplicate_complaints(complaint_text: str, category: str = None) -> dict:
    """
    Search the database for similar existing complaints using TF-IDF and Cosine Similarity.

    Args:
        complaint_text: The text of the new complaint.
        category: The category of the complaint to narrow the search.

    Returns:
        dict with is_duplicate, matching ticket_id, similarity_score, and reason.
    """
    query = "SELECT ticket_id, complaint_text, status FROM grievances WHERE status != 'Resolved' AND status != 'Rejected'"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)

    existing = fetch_all(query, params)

    if not existing:
        return {"is_duplicate": False, "message": "No existing complaints to compare against."}

    texts = [g['complaint_text'] for g in existing]
    ticket_ids = [g['ticket_id'] for g in existing]
    statuses = [g['status'] for g in existing]

    texts.append(complaint_text)

    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(texts)
        cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
        best_idx = cosine_sim.argmax()
        best_score = cosine_sim[best_idx]

        if best_score > 0.65:
            return {
                "is_duplicate": True,
                "ticket_id": ticket_ids[best_idx],
                "similarity_score": round(best_score, 2),
                "existing_status": statuses[best_idx],
                "reason": f"Found {round(best_score*100)}% similar ongoing complaint ({ticket_ids[best_idx]})."
            }
    except Exception as e:
        print(f"Error in similarity check: {e}")

    return {"is_duplicate": False, "message": "No duplicates found."}


# ──────────────────────────────────────────────────────────────
# TOOL 3: Student History Lookup
# ──────────────────────────────────────────────────────────────

def get_student_history(student_id: str) -> dict:
    """
    Fetch a student's previous grievance history from the database.
    Useful for detecting recurring issues or frequent complainers.

    Args:
        student_id: The student's ID (e.g., STU001).

    Returns:
        dict with total_complaints, open_complaints, categories, and recent complaints.
    """
    all_complaints = fetch_all(
        "SELECT ticket_id, category, priority, status, created_at FROM grievances WHERE student_id = ? ORDER BY created_at DESC",
        (student_id,)
    )

    if not all_complaints:
        return {"total_complaints": 0, "message": "No previous complaints found for this student."}

    open_complaints = [c for c in all_complaints if c['status'] not in ('Resolved', 'Rejected')]
    categories = list(set(c['category'] for c in all_complaints))

    return {
        "total_complaints": len(all_complaints),
        "open_complaints": len(open_complaints),
        "categories_reported": categories,
        "recent": all_complaints[:3],  # last 3
        "message": f"Student has {len(all_complaints)} total complaint(s), {len(open_complaints)} currently open."
    }


# ──────────────────────────────────────────────────────────────
# TOOL 4: Create Grievance Ticket
# ──────────────────────────────────────────────────────────────

def create_grievance_ticket(
    student_id: str,
    complaint_text: str,
    category: str,
    priority: str,
    department: str,
    location: str,
    ai_reason: str,
    extracted_info: str = "",
    confidence: str = "",
    safety_flag: int = 0,
    needs_review: int = 0,
) -> dict:
    """
    Create a new grievance ticket in the database.

    Args:
        student_id: The ID of the student.
        complaint_text: The description of the issue.
        category: The categorized domain of the issue.
        priority: Priority level (Low, Medium, High, Critical).
        department: Responsible department.
        location: Specific location on campus.
        ai_reason: AI's reasoning for its decisions.
        extracted_info: JSON string of structured extracted information.
        confidence: JSON string of confidence scores.
        safety_flag: 1 if safety concern detected, else 0.
        needs_review: 1 if AI is uncertain and needs admin review, else 0.

    Returns:
        dict with ticket_id, status, and message.
    """
    ticket_id = f"GRV-{uuid.uuid4().hex[:6].upper()}"
    status = "Submitted"

    query = '''
        INSERT INTO grievances (
            ticket_id, student_id, complaint_text, category, priority,
            department, location, status, ai_reason,
            extracted_info, confidence, safety_flag, needs_review
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''

    execute_query(query, (
        ticket_id, student_id, complaint_text, category, priority,
        department, location, status, ai_reason,
        extracted_info, confidence, safety_flag, needs_review,
    ))

    return {
        "ticket_id": ticket_id,
        "status": status,
        "message": f"Successfully created ticket {ticket_id}."
    }


# ──────────────────────────────────────────────────────────────
# TOOL 5: Link to Existing Grievance
# ──────────────────────────────────────────────────────────────

def link_to_existing_grievance(student_id: str, complaint_text: str, existing_ticket_id: str) -> dict:
    """
    Link a new complaint to an existing grievance instead of creating a new one.

    Args:
        student_id: The student's ID.
        complaint_text: The student's complaint text.
        existing_ticket_id: The ID of the existing grievance ticket.

    Returns:
        dict with ticket_id, status, and message.
    """
    # Add a note to the existing ticket's update history
    existing = fetch_one("SELECT id FROM grievances WHERE ticket_id = ?", (existing_ticket_id,))
    if existing:
        execute_query(
            "INSERT INTO grievance_updates (grievance_id, old_status, new_status, note) VALUES (?, ?, ?, ?)",
            (existing['id'], 'N/A', 'N/A', f"[LINKED] Additional report from {student_id}: {complaint_text[:100]}...")
        )

    return {
        "ticket_id": existing_ticket_id,
        "status": "Linked",
        "message": f"Your complaint has been linked to existing ticket {existing_ticket_id} which is already being handled."
    }


# ──────────────────────────────────────────────────────────────
# TOOL 6: Campus Insights (for Admin Dashboard)
# ──────────────────────────────────────────────────────────────

def get_campus_insights() -> dict:
    """
    Analyze all grievance data to identify campus-wide trends and recurring problems.

    Returns:
        dict with top categories, problem locations, unresolved critical issues, and trends.
    """
    all_data = fetch_all("SELECT category, priority, department, location, status, created_at FROM grievances")

    if not all_data:
        return {"message": "No data available for insights."}

    # Count by category
    cat_counts = {}
    loc_counts = {}
    unresolved_critical = 0

    for row in all_data:
        cat_counts[row['category']] = cat_counts.get(row['category'], 0) + 1
        if row['location']:
            loc_counts[row['location']] = loc_counts.get(row['location'], 0) + 1
        if row['priority'] in ('High', 'Critical') and row['status'] not in ('Resolved', 'Rejected'):
            unresolved_critical += 1

    # Top problem category
    top_category = max(cat_counts, key=cat_counts.get) if cat_counts else "N/A"
    # Top problem location
    top_location = max(loc_counts, key=loc_counts.get) if loc_counts else "N/A"

    return {
        "total_grievances": len(all_data),
        "top_category": f"{top_category} ({cat_counts.get(top_category, 0)} complaints)",
        "top_location": f"{top_location} ({loc_counts.get(top_location, 0)} complaints)",
        "unresolved_critical": unresolved_critical,
        "category_breakdown": cat_counts,
        "location_breakdown": loc_counts,
    }
