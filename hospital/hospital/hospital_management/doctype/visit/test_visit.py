"""
Automated unit tests for Visit DocType.
"""

import frappe
from frappe.tests.utils import FrappeTestCase


def _setup_visit_records():
	# Department
	dept_name = "Visit Test Dept"
	if not frappe.db.exists("Department", {"department_name": dept_name}):
		frappe.get_doc({
			"doctype": "Department", "department_name": dept_name, "status": "Active"
		}).insert(ignore_permissions=True)
	dept = frappe.db.get_value("Department", {"department_name": dept_name}, "name")

	# Doctor
	doc_name = "Dr Visit Test"
	if not frappe.db.exists("Employee", {"employee_name": doc_name}):
		frappe.get_doc({
			"doctype": "Employee", "employee_name": doc_name, "phone": "8888000011",
			"employee_type": "Doctor", "department": dept, "status": "Active",
			"gender": "Male", "qualification": "MBBS", "specialization": "General",
			"years_of_experience": 3, "consultation_fee": 600,
		}).insert(ignore_permissions=True)
	doctor = frappe.db.get_value("Employee", {"employee_name": doc_name}, "name")

	# Patient
	pat_name = "Visit Test Patient"
	if not frappe.db.exists("Patient", {"patient_name": pat_name}):
		frappe.get_doc({
			"doctype": "Patient", "patient_name": pat_name, "date_of_birth": "1992-04-10",
			"gender": "Male", "phone": "7777000011",
			"registration_date": frappe.utils.today(), "status": "Active",
		}).insert(ignore_permissions=True)
	patient = frappe.db.get_value("Patient", {"patient_name": pat_name}, "name")

	return doctor, patient


class TestVisit(FrappeTestCase):

	def setUp(self):
		self.doctor, self.patient = _setup_visit_records()

	def test_create_visit_defaults_to_open(self):
		visit = frappe.get_doc({
			"doctype":        "Visit",
			"patient":        self.patient,
			"doctor":         self.doctor,
			"visit_datetime": frappe.utils.now_datetime(),
		})
		visit.insert(ignore_permissions=True)
		self.assertEqual(visit.status, "Open")

	def test_invalid_visit_status_transition_raises(self):
		visit = frappe.get_doc({
			"doctype":        "Visit",
			"patient":        self.patient,
			"doctor":         self.doctor,
			"visit_datetime": frappe.utils.now_datetime(),
			"status":         "Completed",
		})
		visit.insert(ignore_permissions=True)

		# Completed -> Open is blocked
		visit.status = "Open"
		with self.assertRaises(frappe.exceptions.ValidationError):
			visit.save(ignore_permissions=True)
