import frappe
from frappe.query_builder import DocType


@frappe.whitelist(allow_guest=True)
def get_appointment_summary():
	Appointment = DocType("Appointment")
	Patient = DocType("Patient")

	records = (
		frappe.qb.from_(Appointment)
		.inner_join(Patient)
		.on(Appointment.patient == Patient.name)
		.select(Appointment.name, Appointment.patient, Patient.patient_name, Appointment.status)
		.limit(5)
	).run(as_dict=True)

	if records:
		# Document API: Fetch record and save
		doc = frappe.get_doc("Appointment", records[0]["name"])
		doc.save()

		# Database API: Simple direct update
		frappe.db.set_value("Appointment", records[0]["name"], "status", "Scheduled")

	return records