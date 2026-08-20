"""
Automated tests for the Fee DocType and payment workflow.

Run with:
    bench --site hosp.local run-tests --module hospital.hospital_management.doctype.fee.test_fee
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from hospital.hospital_management.doctype.fee.fee import cancel_fee, mark_as_paid
from hospital.hospital_management.doctype.visit.visit import create_fee_from_visit


def _setup_records():
	"""Create minimal records for fee testing."""
	# Department
	dept_name = "Fee Test Dept"
	if not frappe.db.exists("Department", {"department_name": dept_name}):
		frappe.get_doc({
			"doctype": "Department", "department_name": dept_name, "status": "Active"
		}).insert(ignore_permissions=True)
	dept = frappe.db.get_value("Department", {"department_name": dept_name}, "name")

	# Doctor
	doc_name = "Dr Fee Test"
	if not frappe.db.exists("Employee", {"employee_name": doc_name}):
		frappe.get_doc({
			"doctype": "Employee", "employee_name": doc_name, "phone": "8888888888",
			"employee_type": "Doctor", "department": dept, "status": "Active",
			"gender": "Male", "qualification": "MBBS", "specialization": "General",
			"years_of_experience": 3, "consultation_fee": 750,
		}).insert(ignore_permissions=True)
	doctor = frappe.db.get_value("Employee", {"employee_name": doc_name}, "name")

	# Patient
	pat_name = "Fee Test Patient"
	if not frappe.db.exists("Patient", {"patient_name": pat_name}):
		frappe.get_doc({
			"doctype": "Patient", "patient_name": pat_name, "date_of_birth": "1985-05-15",
			"gender": "Female", "phone": "7777777777",
			"registration_date": frappe.utils.today(), "status": "Active",
		}).insert(ignore_permissions=True)
	patient = frappe.db.get_value("Patient", {"patient_name": pat_name}, "name")

	# Visit
	visit = frappe.get_doc({
		"doctype": "Visit", "patient": patient, "doctor": doctor,
		"visit_datetime": frappe.utils.now_datetime(), "status": "Open",
	})
	visit.insert(ignore_permissions=True)

	return doctor, patient, visit.name


class TestFee(FrappeTestCase):

	def setUp(self):
		self.doctor, self.patient, self.visit = _setup_records()

	def _make_fee(self, amount=500):
		fee = frappe.get_doc({
			"doctype":        "Fee",
			"patient":        self.patient,
			"visit":          self.visit,
			"fee_amount":     amount,
			"payment_method": "Cash",
			"payment_status": "Pending",
		})
		fee.insert(ignore_permissions=True)
		return fee.name

	# ---- Validation ----

	def test_fee_amount_must_be_positive(self):
		with self.assertRaises(frappe.exceptions.ValidationError):
			frappe.get_doc({
				"doctype": "Fee", "patient": self.patient,
				"visit": self.visit, "fee_amount": -100, "payment_method": "Cash",
			}).insert(ignore_permissions=True)

	def test_digital_payment_requires_reference(self):
		with self.assertRaises(frappe.exceptions.ValidationError):
			frappe.get_doc({
				"doctype": "Fee", "patient": self.patient,
				"visit": self.visit, "fee_amount": 500,
				"payment_method": "UPI",
			}).insert(ignore_permissions=True)

	# ---- create_fee_from_visit ----

	def test_create_fee_from_visit_uses_consultation_fee(self):
		consultation_fee = frappe.db.get_value("Employee", self.doctor, "consultation_fee")
		result = create_fee_from_visit(self.visit)
		self.assertEqual(result["status"], "success")
		fee_amount = frappe.db.get_value("Fee", result["fee"], "fee_amount")
		self.assertEqual(fee_amount, consultation_fee)

	# ---- Payment Workflow ----

	def test_mark_as_paid_transitions_to_paid(self):
		name = self._make_fee()
		result = mark_as_paid(name, "Cash")
		self.assertEqual(result["status"], "success")
		self.assertEqual(frappe.db.get_value("Fee", name, "payment_status"), "Paid")

	def test_cannot_pay_already_paid_fee(self):
		name = self._make_fee()
		mark_as_paid(name, "Cash")
		with self.assertRaises(frappe.exceptions.ValidationError):
			mark_as_paid(name, "Cash")

	def test_cancel_pending_fee(self):
		name = self._make_fee()
		result = cancel_fee(name)
		self.assertEqual(result["status"], "success")
		self.assertEqual(frappe.db.get_value("Fee", name, "payment_status"), "Cancelled")

	def test_cannot_cancel_paid_fee(self):
		name = self._make_fee()
		mark_as_paid(name, "Cash")
		with self.assertRaises(frappe.exceptions.ValidationError):
			cancel_fee(name)

	def test_status_transition_paid_to_refunded(self):
		name = self._make_fee()
		mark_as_paid(name, "Cash")
		# Direct set for refund (no separate API yet)
		doc = frappe.get_doc("Fee", name)
		doc.payment_status = "Refunded"
		doc.save(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("Fee", name, "payment_status"), "Refunded")

	def test_invalid_status_transition_raises(self):
		name = self._make_fee()
		doc = frappe.get_doc("Fee", name)
		doc.payment_status = "Refunded"  # Pending → Refunded is not allowed
		with self.assertRaises(frappe.exceptions.ValidationError):
			doc.save(ignore_permissions=True)
