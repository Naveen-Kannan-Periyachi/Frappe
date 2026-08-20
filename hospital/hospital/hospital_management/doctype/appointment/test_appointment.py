"""
Automated tests for the Appointment DocType.

Run with:
    cd /home/naveen/Desktop/Project/GPT/gptproject
    bench --site hosp.local run-tests --module hospital.hospital_management.doctype.appointment.test_appointment
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from hospital.hospital_management.doctype.appointment.appointment import (
	cancel_appointment,
	create_visit_from_appointment,
	get_available_slots,
	mark_arrived,
	mark_no_show,
	rebook_appointment,
	start_consultation,
)


def make_department(name="Test Dept"):
	if frappe.db.exists("Department", {"department_name": name}):
		return frappe.db.get_value("Department", {"department_name": name}, "name")
	dept = frappe.get_doc({
		"doctype":         "Department",
		"department_name": name,
		"status":          "Active",
	})
	dept.insert(ignore_permissions=True)
	return dept.name


def make_doctor(department, name="Dr. Test"):
	if frappe.db.exists("Employee", {"employee_name": name}):
		return frappe.db.get_value("Employee", {"employee_name": name}, "name")
	emp = frappe.get_doc({
		"doctype":          "Employee",
		"employee_name":    name,
		"phone":            "9999999999",
		"employee_type":    "Doctor",
		"department":       department,
		"status":           "Active",
		"gender":           "Male",
		"qualification":    "MBBS",
		"specialization":   "General",
		"years_of_experience": 5,
		"consultation_fee": 500,
	})
	emp.insert(ignore_permissions=True)
	return emp.name


def make_patient(name="Test Patient"):
	if frappe.db.exists("Patient", {"patient_name": name}):
		return frappe.db.get_value("Patient", {"patient_name": name}, "name")
	p = frappe.get_doc({
		"doctype":           "Patient",
		"patient_name":      name,
		"date_of_birth":     "1990-01-01",
		"gender":            "Male",
		"phone":             "9876543210",
		"registration_date": frappe.utils.today(),
		"status":            "Active",
	})
	p.insert(ignore_permissions=True)
	return p.name


def make_appointment(doctor, patient, date=None, slot="10:00 - 10:15"):
	appt = frappe.get_doc({
		"doctype":          "Appointment",
		"patient":          patient,
		"doctor":           doctor,
		"appointment_date": date or frappe.utils.today(),
		"slot":             slot,
	})
	appt.insert(ignore_permissions=True)
	return appt.name


class TestAppointment(FrappeTestCase):

	def setUp(self):
		self.dept    = make_department()
		self.doctor  = make_doctor(self.dept)
		self.patient = make_patient()

	# ---- Booking ----

	def test_new_appointment_status_is_scheduled(self):
		name = make_appointment(self.doctor, self.patient,
			date=frappe.utils.add_days(frappe.utils.today(), 90), slot="10:15 - 10:30")
		status = frappe.db.get_value("Appointment", name, "status")
		self.assertEqual(status, "Scheduled")

	def test_double_booking_same_slot_raises(self):
		make_appointment(self.doctor, self.patient, slot="10:30 - 10:45")
		with self.assertRaises(frappe.exceptions.ValidationError):
			make_appointment(self.doctor, self.patient, slot="10:30 - 10:45")

	def test_cancelled_slot_can_be_rebooked(self):
		name = make_appointment(self.doctor, self.patient, slot="10:45 - 11:00")
		cancel_appointment(name, "test reason")
		# Same slot now available again
		name2 = make_appointment(self.doctor, self.patient, slot="10:45 - 11:00")
		self.assertIsNotNone(name2)

	def test_get_available_slots_excludes_booked(self):
		uniq_date = frappe.utils.add_days(frappe.utils.today(), 99)
		make_appointment(self.doctor, self.patient, date=uniq_date, slot="11:00 - 11:15")
		slots = get_available_slots(self.doctor, uniq_date)
		self.assertNotIn("11:00 - 11:15", slots)

	# ---- Workflow ----

	def test_mark_arrived(self):
		name = make_appointment(self.doctor, self.patient, slot="10:00 - 10:15",
			date=frappe.utils.add_days(frappe.utils.today(), 1))
		# Reset to today for test
		frappe.db.set_value("Appointment", name, "appointment_date", frappe.utils.today())
		result = mark_arrived(name)
		self.assertEqual(result["status"], "success")
		self.assertEqual(frappe.db.get_value("Appointment", name, "status"), "Arrived")

	def test_cannot_mark_arrived_twice(self):
		name = make_appointment(self.doctor, self.patient, slot="10:15 - 10:30",
			date=frappe.utils.add_days(frappe.utils.today(), 2))
		frappe.db.set_value("Appointment", name, "appointment_date", frappe.utils.today())
		mark_arrived(name)
		with self.assertRaises(frappe.exceptions.ValidationError):
			mark_arrived(name)

	def test_start_consultation(self):
		name = make_appointment(self.doctor, self.patient, slot="10:30 - 10:45",
			date=frappe.utils.add_days(frappe.utils.today(), 3))
		frappe.db.set_value("Appointment", name, "appointment_date", frappe.utils.today())
		mark_arrived(name)
		result = start_consultation(name)
		self.assertEqual(result["status"], "success")
		self.assertEqual(
			frappe.db.get_value("Appointment", name, "status"), "In Consultation"
		)

	def test_mark_no_show(self):
		name = make_appointment(self.doctor, self.patient, slot="10:45 - 11:00",
			date=frappe.utils.add_days(frappe.utils.today(), 4))
		frappe.db.set_value("Appointment", name, "appointment_date", frappe.utils.today())
		result = mark_no_show(name)
		self.assertEqual(result["status"], "success")
		self.assertEqual(frappe.db.get_value("Appointment", name, "status"), "No Show")

	# ---- Cancellation & Rebooking ----

	def test_cancel_appointment(self):
		name = make_appointment(self.doctor, self.patient, slot="11:00 - 11:15",
			date=frappe.utils.add_days(frappe.utils.today(), 5))
		result = cancel_appointment(name, "Patient request")
		self.assertEqual(result["status"], "success")
		doc = frappe.get_doc("Appointment", name)
		self.assertEqual(doc.status, "Cancelled")
		self.assertEqual(doc.cancellation_reason, "Patient request")

	def test_cancel_requires_reason(self):
		name = make_appointment(self.doctor, self.patient, slot="10:00 - 10:15",
			date=frappe.utils.add_days(frappe.utils.today(), 6))
		with self.assertRaises(frappe.exceptions.ValidationError):
			cancel_appointment(name, "")

	def test_rebook_sets_previous_appointment(self):
		name = make_appointment(self.doctor, self.patient, slot="10:15 - 10:30",
			date=frappe.utils.add_days(frappe.utils.today(), 7))
		cancel_appointment(name, "reschedule")
		result = rebook_appointment(
			name,
			frappe.utils.add_days(frappe.utils.today(), 8),
			"10:30 - 10:45"
		)
		self.assertEqual(result["status"], "success")
		new_name = result["appointment"]
		prev = frappe.db.get_value("Appointment", new_name, "previous_appointment")
		self.assertEqual(prev, name)

	# ---- Create Visit ----

	def test_create_visit_from_arrived_appointment(self):
		name = make_appointment(self.doctor, self.patient, slot="10:45 - 11:00",
			date=frappe.utils.add_days(frappe.utils.today(), 9))
		frappe.db.set_value("Appointment", name, "appointment_date", frappe.utils.today())
		mark_arrived(name)
		result = create_visit_from_appointment(name)
		self.assertEqual(result["status"], "success")
		visit_status = frappe.db.get_value("Visit", result["visit"], "status")
		self.assertEqual(visit_status, "Open")

	def test_create_visit_advances_appointment_to_in_consultation(self):
		name = make_appointment(self.doctor, self.patient, slot="11:00 - 11:15",
			date=frappe.utils.add_days(frappe.utils.today(), 10))
		frappe.db.set_value("Appointment", name, "appointment_date", frappe.utils.today())
		mark_arrived(name)
		create_visit_from_appointment(name)
		status = frappe.db.get_value("Appointment", name, "status")
		self.assertEqual(status, "In Consultation")

	def test_create_duplicate_visit_returns_exists(self):
		name = make_appointment(self.doctor, self.patient, slot="10:00 - 10:15",
			date=frappe.utils.add_days(frappe.utils.today(), 11))
		frappe.db.set_value("Appointment", name, "appointment_date", frappe.utils.today())
		mark_arrived(name)
		create_visit_from_appointment(name)
		result = create_visit_from_appointment(name)
		self.assertEqual(result["status"], "exists")
