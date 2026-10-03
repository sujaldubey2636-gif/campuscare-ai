from database.db import get_connection, init_db
import sqlite3

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
        pass # Departments already exist
        
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
            pass # Student already exists

    # Seed Sample Grievances (so the Admin Dashboard looks populated)
    grievances = [
        ('GRV-DEMO01', 'STU002', 'The library AC is not working and it is extremely hot inside. Students cannot concentrate on studies.',
         'Facilities', 'Medium', 'Maintenance Department', 'Central Library', 'Submitted',
         'Identified as a Facilities issue. Medium priority as it affects comfort but not safety.'),

        ('GRV-DEMO02', 'STU003', 'My semester fee payment was deducted twice from my bank account but the portal still shows unpaid.',
         'Finance', 'High', 'Finance Office', 'Admin Block', 'In Progress',
         'Financial double-deduction is a High priority issue requiring urgent verification.'),

        ('GRV-DEMO03', 'STU001', 'The hostel water supply has been disrupted since yesterday morning. Over 50 students are affected.',
         'Hostel', 'Critical', 'Hostel Administration', 'Hostel Block A', 'Escalated',
         'Critical: Water supply disruption affecting 50+ students for over 24 hours. Safety concern.'),

        ('GRV-DEMO04', 'STU004', 'I lost my library card last week and need a replacement. The library staff said I need to apply online.',
         'Library', 'Low', 'Library Administration', 'Central Library', 'Resolved',
         'Low priority administrative request for library card replacement.'),

        ('GRV-DEMO05', 'STU005', 'The projector in Room 301 is not displaying colors correctly. It has a pink tint on the screen.',
         'Facilities', 'Medium', 'Maintenance Department', 'Academic Block C, Room 301', 'Assigned',
         'Medium priority: Classroom equipment malfunction affecting lecture quality.'),
    ]

    for g in grievances:
        try:
            cursor.execute(
                '''INSERT INTO grievances (ticket_id, student_id, complaint_text, category, priority, 
                   department, location, status, ai_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                g
            )
        except sqlite3.IntegrityError:
            pass # Grievance already exists

    # Seed some update history for the demo grievances
    updates = [
        # GRV-DEMO02: Submitted -> In Progress
        (2, 'Submitted', 'In Progress', 'Finance team is verifying the bank transaction records.'),
        # GRV-DEMO03: Submitted -> Escalated
        (3, 'Submitted', 'Escalated', 'Unresolved for 24+ hours. Escalated to Hostel Warden.'),
        # GRV-DEMO04: Submitted -> Resolved
        (4, 'Submitted', 'Resolved', 'Replacement library card issued successfully.'),
        # GRV-DEMO05: Submitted -> Assigned
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
    print("Database seeded successfully with sample data.")

if __name__ == '__main__':
    seed_database()
