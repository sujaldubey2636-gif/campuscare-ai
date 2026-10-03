import os
import unittest
from agent.grievance_agent import GrievanceAgent
from agent.tools import check_duplicate_complaints
from database.db import get_connection, init_db

class TestCampusCareAI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure database is set up
        init_db()

    def setUp(self):
        # We test using the fallback mode to ensure tests run without API key
        self.agent = GrievanceAgent()
        self.agent.client = None # Force fallback mode for deterministic tests

    def test_hostel_complaint(self):
        res = self.agent.run("STU001", "My hostel room has no electricity.", "Block A")
        self.assertEqual(res['ticket_info']['category'], 'Hostel')
        self.assertEqual(res['ticket_info']['department'], 'Hostel Administration')

    def test_it_complaint(self):
        res = self.agent.run("STU001", "The college Wi-Fi is not working.", "Library")
        self.assertEqual(res['ticket_info']['category'], 'IT')
        self.assertEqual(res['ticket_info']['department'], 'IT Support')

    def test_finance_complaint(self):
        res = self.agent.run("STU001", "My fee payment has been deducted but shows unpaid.", "Admin Block")
        self.assertEqual(res['ticket_info']['category'], 'Finance')
        self.assertEqual(res['ticket_info']['department'], 'Finance Office')

    def test_duplicate_complaint(self):
        # Create first ticket
        self.agent.run("STU001", "The Wi-Fi in Block B is broken and completely down.", "Block B")
        # Second ticket with similar text
        res = self.agent.run("STU002", "The Wi-Fi in Block B is broken and completely down.", "Block B")
        # Fallback mode also checks duplicates
        self.assertEqual(res['ticket_info']['status'], 'Linked')

if __name__ == '__main__':
    unittest.main()
