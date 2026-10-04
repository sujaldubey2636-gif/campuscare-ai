from database.db import get_connection, init_db
import sqlite3
import json

def seed_database():
    """Seeds the database with initial required data."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    # Seed Departments
    departments = [
        ('Hostel Administration',),
        ('IT Support',),
        ('Finance Office',),
        ('Examination Cell',),
        ('Library Administration',),
        ('Maintenance Department',),
        ('Security Office',),
        ('General Administration',)
    ]
    
    try:
        cursor.executemany(
            'INSERT INTO departments (department_name) VALUES (?)',
            departments
        )
    except sqlite3.IntegrityError:
        pass
        
    # Seed Sample Students
    students = [
        ('STU001', 'Alice Smith', 'alice@college.edu', 'B.Tech CS', 2),
        ('STU002', 'Bob Johnson', 'bob@college.edu', 'B.Tech Mechanical', 3),
        ('STU003', 'Charlie Brown', 'charlie@college.edu', 'BCA', 1),
        ('STU004', 'Diana Patel', 'diana@college.edu', 'B.Tech ECE', 2),
        ('STU005', 'Ethan Kumar', 'ethan@college.edu', 'B.Tech IT', 4),
    ]
    
    for student in students:
        try:
            cursor.execute(
                'INSERT INTO students (id, name, email, course, year) VALUES (?, ?, ?, ?, ?)',
                student
            )
        except sqlite3.IntegrityError:
            pass

    # Dummy extracted info to simulate AI extraction
    extracted_hostel = json.dumps({
        "issue": "Water supply disrupted",
        "location": "Hostel Block A",
        "duration": "over 24 hours",
        "affected_count": 50,
        "equipment_or_service": "water supply",
        "has_deadline_pressure": False,
        "sentiment": "angry",
        "safety_risk": True,
        "root_cause_hypothesis": "Main water line burst or pump failure."
    })
    
    extracted_it = json.dumps({
        "issue": "Pink tint on projector",
        "location": "Room 301",
        "duration": "unknown",
        "affected_count": 0,
        "equipment_or_service": "projector",
        "has_deadline_pressure": False,
        "sentiment": "calm",
        "safety_risk": False,
        "root_cause_hypothesis": "VGA/HDMI cable loose or bulb failing."
    })

    conf_high = json.dumps({"category_confidence": 95, "priority_score": 60, "priority_factors": ["Safety hazard detected", "50 students affected"]})
    conf_med = json.dumps({"category_confidence": 80, "priority_score": 15, "priority_factors": []})

    # Seed Sample Grievances (now including the intelligence columns)
    grievances = [
        ('GRV-DEMO01', 'STU002', 'The library AC is not working and it is extremely hot inside.',
         'Facilities', 'Medium', 'Maintenance Department', 'Central Library', 'Submitted',
         'Priority Score: 10', '{}', conf_med, 0, 0),

        ('GRV-DEMO02', 'STU003', 'My semester fee payment was deducted twice.',
         'Finance', 'High', 'Finance Office', 'Admin Block', 'In Progress',
         'Priority Score: 30', '{}', conf_med, 0, 0),

        ('GRV-DEMO03', 'STU001', 'The hostel water supply has been disrupted since yesterday morning. Over 50 students are affected.',
         'Hostel', 'Critical', 'Hostel Administration', 'Hostel Block A', 'Escalated',
         'Priority Score: 60', extracted_hostel, conf_high, 1, 0),

        ('GRV-DEMO04', 'STU004', 'I lost my library card last week and need a replacement.',
         'Library', 'Low', 'Library Administration', 'Central Library', 'Resolved',
         'Priority Score: 0', '{}', conf_med, 0, 0),

        ('GRV-DEMO05', 'STU005', 'The projector in Room 301 is not displaying colors correctly. It has a pink tint.',
         'Facilities', 'Medium', 'Maintenance Department', 'Academic Block C, Room 301', 'Assigned',
         'Priority Score: 15', extracted_it, conf_med, 0, 1), # 1 for needs_review to test UI
    ]

    for g in grievances:
        try:
            cursor.execute(
                '''INSERT INTO grievances (ticket_id, student_id, complaint_text, category, priority, 
                   department, location, status, ai_reason, extracted_info, confidence, safety_flag, needs_review) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                g
            )
        except sqlite3.IntegrityError:
            pass

    # Seed update history
    updates = [
        (2, 'Submitted', 'In Progress', 'Finance team is verifying the bank transaction records.'),
        (3, 'Submitted', 'Escalated', 'Unresolved for 24+ hours. Escalated to Hostel Warden.'),
        (4, 'Submitted', 'Resolved', 'Replacement library card issued successfully.'),
        (5, 'Submitted', 'Assigned', 'Assigned to AV technician Mr. Sharma.'),
    ]

    for u in updates:
        try:
            cursor.execute(
                'INSERT INTO grievance_updates (grievance_id, old_status, new_status, note) VALUES (?, ?, ?, ?)',
                u
            )
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()
    print("Database seeded successfully with sample AI data.")

if __name__ == '__main__':
    seed_database()
