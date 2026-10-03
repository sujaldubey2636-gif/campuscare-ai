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
    ]
    
    for student in students:
        try:
            cursor.execute(
                'INSERT INTO students (id, name, email, course, year) VALUES (?, ?, ?, ?, ?)',
                student
            )
        except sqlite3.IntegrityError:
            pass # Student already exists
            
    conn.commit()
    conn.close()
    print("Database seeded successfully.")

if __name__ == '__main__':
    seed_database()
