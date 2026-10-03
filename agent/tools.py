import uuid
import datetime
from database.db import execute_query, fetch_all, fetch_one
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def check_duplicate_complaints(complaint_text: str, category: str = None) -> dict:
    """
    Search the database for similar existing complaints using TF-IDF and Cosine Similarity.
    
    Args:
        complaint_text (str): The text of the new complaint.
        category (str, optional): The category of the complaint to filter by.
        
    Returns:
        dict: Information about a matching duplicate if found, otherwise None.
    """
    # Fetch existing complaints
    query = "SELECT ticket_id, complaint_text, status FROM grievances WHERE status != 'Resolved' AND status != 'Rejected'"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
        
    existing_grievances = fetch_all(query, params)
    
    if not existing_grievances:
        return {"is_duplicate": False, "message": "No existing complaints to compare against."}
        
    texts = [g['complaint_text'] for g in existing_grievances]
    ticket_ids = [g['ticket_id'] for g in existing_grievances]
    statuses = [g['status'] for g in existing_grievances]
    
    # Add the new complaint for vectorization
    texts.append(complaint_text)
    
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        # Calculate cosine similarity of the new complaint (last element) with all others
        cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
        
        # Find the most similar complaint
        best_match_idx = cosine_sim.argmax()
        best_score = cosine_sim[best_match_idx]
        
        # Threshold for similarity
        if best_score > 0.65:
            return {
                "is_duplicate": True,
                "ticket_id": ticket_ids[best_match_idx],
                "similarity_score": round(best_score, 2),
                "existing_status": statuses[best_match_idx],
                "reason": "Found highly similar ongoing complaint in the system."
            }
    except Exception as e:
        print(f"Error in similarity check: {e}")
        
    return {"is_duplicate": False, "message": "No duplicates found."}

def create_grievance_ticket(student_id: str, complaint_text: str, category: str, priority: str, department: str, location: str, ai_reason: str) -> dict:
    """
    Create a new grievance ticket in the database.
    
    Args:
        student_id (str): The ID of the student.
        complaint_text (str): The description of the issue.
        category (str): The categorized domain of the issue.
        priority (str): Priority level (Low, Medium, High, Critical).
        department (str): Responsible department.
        location (str): Specific location on campus.
        ai_reason (str): Reason for AI's classification and priority.
        
    Returns:
        dict: The created ticket information.
    """
    ticket_id = f"GRV-{uuid.uuid4().hex[:6].upper()}"
    status = "Submitted"
    
    query = '''
        INSERT INTO grievances (
            ticket_id, student_id, complaint_text, category, priority, 
            department, location, status, ai_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    
    execute_query(query, (
        ticket_id, student_id, complaint_text, category, priority, 
        department, location, status, ai_reason
    ))
    
    return {
        "ticket_id": ticket_id,
        "status": status,
        "message": f"Successfully created ticket {ticket_id}."
    }

def link_to_existing_grievance(student_id: str, complaint_text: str, existing_ticket_id: str) -> dict:
    """
    Link a new complaint to an existing grievance instead of creating a new one.
    
    Args:
        student_id (str): The student's ID.
        complaint_text (str): The student's complaint text.
        existing_ticket_id (str): The ID of the existing grievance ticket.
        
    Returns:
        dict: Information about the linked ticket.
    """
    # Simply note the complaint in the updates or return a linked reference.
    # For this project, we return the existing ticket ID.
    return {
        "ticket_id": existing_ticket_id,
        "status": "Linked",
        "message": f"Your complaint has been linked to existing ticket {existing_ticket_id} which is already being handled."
    }
