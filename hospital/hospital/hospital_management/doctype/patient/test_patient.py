"""
Automated unit tests for Patient DocType.
"""

import frappe
from frappe.tests.utils import FrappeTestCase


class TestPatient(FrappeTestCase):

	def test_create_patient(self):
		patient = frappe.get_doc({
			"doctype":           "Patient",
			"patient_name":      "Unit Test Patient",
			"date_of_birth":     "1995-06-15",
			"gender":            "Female",
			"phone":             "9123456789",
			"registration_date": frappe.utils.today(),
			"status":            "Active",
		})
		patient.insert(ignore_permissions=True)
		self.assertTrue(patient.name)
		self.assertEqual(patient.status, "Active")

	def test_patient_requires_name(self):
		with self.assertRaises(frappe.exceptions.ValidationError):
			frappe.get_doc({
				"doctype":       "Patient",
				"date_of_birth": "1995-06-15",
				"gender":        "Female",
			}).insert(ignore_permissions=True)
