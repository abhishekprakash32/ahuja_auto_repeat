import frappe
import unittest
from datetime import datetime, timedelta
from frappe.utils import getdate, nowdate
from custom_auto_repeat.overrides.auto_repeat import AutoRepeat

class TestAutoRepeat(unittest.TestCase):
   def setUp(self):
      # Create a test task
      self.task = frappe.get_doc({
         "doctype": "Task",
         "subject": "Test Task for Auto Repeat",
         "start_date": "2025-07-07",
         "end_date": "2025-07-08"
      })
      self.task.insert()
      
   def test_daily_frequency(self):
      # Test daily frequency
      auto_repeat = frappe.get_doc({
         "doctype": "Auto Repeat",
         "reference_doctype": "Task",
         "reference_document": self.task.name,
         "frequency": "Daily",
         "start_date": "2025-08-25"  # Today's date as per example
      })
      
      auto_repeat.insert()
      
      # Check if next schedule date is calculated correctly
      expected_date = getdate("2025-08-26")  # Today + 1 day
      self.assertEqual(auto_repeat.next_schedule_date, expected_date)
      
   def test_weekly_frequency(self):
      # Test weekly frequency with specific days
      auto_repeat = frappe.get_doc({
         "doctype": "Auto Repeat",
         "reference_doctype": "Task",
         "reference_document": self.task.name,
         "frequency": "Weekly",
         "start_date": "2025-08-25",
         "repeat_on_days": [
               {"day": "Monday"},
               {"day": "Thursday"}
         ]
      })
      
      auto_repeat.insert()
      
      # Check if next schedule date is calculated correctly
      # Next Thursday after 2025-08-25 is 2025-08-28
      expected_date = getdate("2025-08-28")
      self.assertEqual(auto_repeat.next_schedule_date, expected_date)
      
   def tearDown(self):
      # Clean up
      if frappe.db.exists("Task", self.task.name):
         frappe.delete_doc("Task", self.task.name)
         
      # Delete any auto repeat records created during tests
      auto_repeats = frappe.get_all("Auto Repeat", filters={"reference_document": self.task.name})
      for ar in auto_repeats:
         frappe.delete_doc("Auto Repeat", ar.name)