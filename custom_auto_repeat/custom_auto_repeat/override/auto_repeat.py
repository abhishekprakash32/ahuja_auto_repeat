from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
import calendar

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate
from frappe.desk.form import assign_to

# Import the original Auto Repeat class
from frappe.automation.doctype.auto_repeat.auto_repeat import AutoRepeat as OriginalAutoRepeat

class AutoRepeat(OriginalAutoRepeat):
   def set_dates(self):
      """Override the set_dates method with enhanced logic"""
      if self.disabled:
         self.next_schedule_date = None
      else:
         # Use the enhanced date calculation logic
         reference_doc = frappe.get_doc(self.reference_doctype, self.reference_document)
         schedule_date = getdate(self.start_date)
         
         # Calculate next schedule date using the new logic
         self.next_schedule_date = self.get_next_schedule_date_enhanced(
               reference_doc, schedule_date
         )
         
         if self.end_date and getdate(self.end_date) < getdate(self.next_schedule_date):
               frappe.throw(_("The Next Scheduled Date cannot be later than the End Date."))
               
         # Create the first document immediately when Auto Repeat is set
         if not self.is_new() and self.status == "Active" and not self.disabled:
               self.create_documents()

   def get_next_schedule_date_enhanced(self, reference_doc, schedule_date):
      """
      Enhanced date calculation based on the problem statement requirements
      """
      frequency = self.frequency
      ref_start = reference_doc.get('start_date') or reference_doc.creation
      ref_end = reference_doc.get('end_date') or ref_start
      
      if isinstance(ref_start, str):
         ref_start = getdate(ref_start)
      if isinstance(ref_end, str):
         ref_end = getdate(ref_end)
         
      duration = ref_end - ref_start
      
      if frequency == "Daily":
         next_start = getdate(nowdate()) + timedelta(days=1)
         
      elif frequency == "Weekly":
         if not self.repeat_on_days:
               frappe.throw(_("Repeat on days required for weekly frequency"))
               
         # Get the days to repeat on
         repeat_days = [d.day for d in self.repeat_on_days]
         day_map = {day: idx for idx, day in enumerate(calendar.day_name)}
         target_days = [day_map[day] for day in repeat_days]
         
         # Find the next target day
         next_start = self._find_next_weekday(target_days)
         
      elif frequency in ["Monthly", "Quarterly", "Half-yearly", "Yearly"]:
         if frequency == "Monthly":
               months_to_add = 1
         elif frequency == "Quarterly":
               months_to_add = 3
         elif frequency == "Half-yearly":
               months_to_add = 6
         else:  # Yearly
               months_to_add = 12
               
         # Start with the reference date and keep adding increments until we reach or pass today
         next_start = ref_start
         while getdate(next_start) < getdate(nowdate()):
               next_start = self._add_months(next_start, months_to_add)
         
      else:
         frappe.throw(_("Unsupported frequency: {0}").format(frequency))
         
      return next_start

   def _find_next_weekday(self, target_days):
      """Find the next weekday from today from the list of target days"""
      current = getdate(nowdate())
      for _ in range(7):  # Check the next 7 days to find the target
         current += timedelta(days=1)
         if current.weekday() in target_days:
               return current
      return current

   def _add_months(self, source_date, months):
      """Add months to a date, handling end-of-month edge cases"""
      return source_date + relativedelta(months=months)

   def make_new_document(self):
      """Override to include assignment copying"""
      reference_doc = frappe.get_doc(self.reference_doctype, self.reference_document)
      new_doc = frappe.copy_doc(reference_doc, ignore_no_copy=False)
      self.update_doc(new_doc, reference_doc)
      
      # Carry forward assignments
      self.copy_assignments(reference_doc, new_doc)
      
      new_doc.insert(ignore_permissions=True)

      if self.submit_on_creation:
         new_doc.submit()

      return new_doc

   def copy_assignments(self, source_doc, target_doc):
      """Copy assignments from source document to target document"""
      assignments = frappe.get_all("ToDo", 
                                 filters={"reference_type": source_doc.doctype,
                                          "reference_name": source_doc.name,
                                          "status": "Open"},
                                 fields=["owner", "description", "priority"])
      
      for assignment in assignments:
         assign_to.add({
               "assign_to": assignment.owner,
               "doctype": target_doc.doctype,
               "name": target_doc.name,
               "description": assignment.description,
               "priority": assignment.priority
         })

   def after_insert(self):
      """Create the first document immediately when Auto Repeat is created"""
      if not self.disabled and self.status == "Active":
         self.create_documents()
         # Update next schedule date after creating the first document
         reference_doc = frappe.get_doc(self.reference_doctype, self.reference_document)
         self.next_schedule_date = self.get_next_schedule_date_enhanced(
               reference_doc, getdate(self.next_schedule_date)
         )
         self.save()