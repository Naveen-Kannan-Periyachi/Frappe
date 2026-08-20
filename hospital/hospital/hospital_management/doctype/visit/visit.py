import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class Visit(Document):
	# begin: auto-generated types
	from typing import TYPE_CHECKING
	if TYPE_CHECKING:
		from frappe.types import DF
		from hospital.hospital_management.doctype.prescribed_medicine.prescribed_medicine import PrescribedMedicine

		appointment:          DF.Link | None
		diagnosis:            DF.TextEditor | None
		doctor:               DF.Link
		follow_up_date:       DF.Date | None
		notes:                DF.TextEditor | None
		patient:              DF.Link
		prescribed_medicines: DF.Table[PrescribedMedicine]
		reason:               DF.SmallText | None
		status:               DF.Literal["Open", "Completed", "Cancelled"]
		symptoms:             DF.TextEditor | None
		visit_datetime:       DF.Datetime
	# end: auto-generated types

	# =========================================================
	# LIFECYCLE HOOKS
	# =========================================================

	def before_insert(self):
		if self.appointment and not self.patient:
			appt = frappe.get_doc("Appointment", self.appointment)
			self.patient = appt.patient
			self.doctor  = appt.doctor

		if not self.status:
			self.status = "Open"

		if not self.visit_datetime:
			self.visit_datetime = now_datetime()

	def before_save(self):
		if not self.is_new():
			self._validate_status_transition()

	def _validate_status_transition(self):
		old_status = frappe.db.get_value("Visit", self.name, "status")
		if not old_status or old_status == self.status:
			return

		allowed = {
			"Open":      ["Completed", "Cancelled"],
			"Completed": [],
			"Cancelled": [],
		}

		if self.status not in allowed.get(old_status, []):
			frappe.throw(
				f"Cannot change visit status from '{old_status}' to '{self.status}'."
			)

	def validate(self):
		self.validate_patient()
		self.validate_doctor()
		self.validate_dates()
		self.validate_appointment()
		self.validate_duplicate_visit()
		self.validate_prescribed_medicines()

	def on_update(self):
		if self.status == "Completed":
			self._complete_visit()

	# =========================================================
	# VALIDATORS
	# =========================================================

	def validate_patient(self):
		if not self.patient:
			frappe.throw("Patient is required.")
		status = frappe.db.get_value("Patient", self.patient, "status")
		if not status:
			frappe.throw("Selected patient does not exist.")
		if status != "Active":
			frappe.throw("Only active patients can have visits.")

	def validate_doctor(self):
		if not self.doctor:
			frappe.throw("Doctor is required.")
		doctor = frappe.db.get_value(
			"Employee", self.doctor, ["employee_type", "status"], as_dict=True
		)
		if not doctor:
			frappe.throw("Selected doctor does not exist.")
		if doctor.employee_type != "Doctor":
			frappe.throw("Selected employee is not a Doctor.")
		if doctor.status != "Active":
			frappe.throw("Selected Doctor is inactive.")

	def validate_dates(self):
		now = now_datetime()
		if self.visit_datetime:
			if frappe.utils.get_datetime(self.visit_datetime) > now:
				frappe.throw("Visit Date & Time cannot be in the future.")
		if self.follow_up_date and self.visit_datetime:
			if (
				frappe.utils.getdate(self.follow_up_date)
				< frappe.utils.getdate(self.visit_datetime)
			):
				frappe.throw("Follow-up Date cannot be earlier than Visit Date.")

	def validate_appointment(self):
		if self.appointment:
			appt_status = frappe.db.get_value("Appointment", self.appointment, "status")
			if appt_status in ["Completed", "Cancelled", "No Show"]:
				frappe.throw(
					f"Visit cannot be linked to an appointment with status '{appt_status}'."
				)

	def validate_duplicate_visit(self):
		if self.appointment:
			existing = frappe.db.exists(
				"Visit",
				{"appointment": self.appointment, "name": ["!=", self.name]},
			)
			if existing:
				frappe.throw("A visit already exists for this appointment.")

	def validate_prescribed_medicines(self):
		medicines = set()
		for row in self.prescribed_medicines:
			if not row.medicine:
				frappe.throw("Medicine is required in prescribed medicines table.")
			if row.medicine in medicines:
				frappe.throw(f"Medicine '{row.medicine}' is duplicated in the prescription.")
			medicines.add(row.medicine)

			status = frappe.db.get_value("Medicine", row.medicine, "status")
			if status and status != "Active":
				frappe.throw(f"Medicine '{row.medicine}' is inactive.")

			if not row.dosage:
				frappe.throw(f"Dosage is required for '{row.medicine}'.")
			if not row.frequency:
				frappe.throw(f"Frequency is required for '{row.medicine}'.")
			if not row.duration:
				frappe.throw(f"Duration is required for '{row.medicine}'.")

	# =========================================================
	# COMPLETION
	# =========================================================

	def _complete_visit(self):
		if self.appointment:
			appt_status = frappe.db.get_value(
				"Appointment", self.appointment, "status"
			)
			if appt_status not in ["Completed"]:
				frappe.db.set_value(
					"Appointment", self.appointment, "status", "Completed"
				)

		# Notify doctor / receptionist
		_notify_visit_completed(self)


# =========================================================
# WHITELISTED APIs — called from client
# =========================================================

@frappe.whitelist()
def get_appointment_details(appointment: str):
	"""Return patient, doctor and date for a Scheduled appointment."""
	if not appointment:
		frappe.throw("Appointment is required.")
	doc = frappe.get_doc("Appointment", appointment)
	if doc.status not in ["Scheduled", "Arrived", "In Consultation"]:
		frappe.throw(
			f"Cannot create a visit for an appointment with status '{doc.status}'."
		)
	return {
		"patient":          doc.patient,
		"doctor":           doc.doctor,
		"appointment_date": doc.appointment_date,
	}


@frappe.whitelist()
def create_fee_from_visit(visit: str):
	"""
	Create a Fee document pre-filled with the doctor's consultation fee.
	Returns the new Fee name so the client can navigate to it.
	"""
	doc = frappe.get_doc("Visit", visit)

	# Fetch doctor's consultation fee
	consultation_fee = frappe.db.get_value(
		"Employee", doc.doctor, "consultation_fee"
	)
	if not consultation_fee or consultation_fee <= 0:
		frappe.throw(
			f"Doctor '{doc.doctor}' does not have a valid consultation fee configured in Employee profile."
		)

	fee = frappe.get_doc({
		"doctype":        "Fee",
		"patient":        doc.patient,
		"visit":          visit,
		"doctor":         doc.doctor,
		"fee_amount":     consultation_fee,
		"payment_status": "Pending",
	})
	fee.insert()

	return {
		"status":  "success",
		"fee":     fee.name,
		"message": f"Fee {fee.name} created with amount {consultation_fee}.",
	}


@frappe.whitelist()
def create_lab_request(visit: str, lab_test: str):
	"""Create a Lab Test Request linked to this visit."""
	if not visit:
		frappe.throw("Visit is required.")
	if not lab_test:
		frappe.throw("Lab Test is required.")

	visit_doc = frappe.get_doc("Visit", visit)

	if visit_doc.status != "Open":
		frappe.throw("Lab tests can only be requested for an open visit.")

	# Check duplicate
	existing = frappe.db.exists(
		"Lab Test Request",
		{"visit": visit, "lab_test": lab_test, "status": ["!=", "Cancelled"]},
	)
	if existing:
		frappe.throw("This lab test has already been requested for this visit.")

	req = frappe.get_doc({
		"doctype":  "Lab Test Request",
		"visit":    visit,
		"patient":  visit_doc.patient,
		"doctor":   visit_doc.doctor,
		"lab_test": lab_test,
	})
	req.insert()

	# Notify lab technicians
	_notify_lab_requested(req)

	return {
		"status":  "success",
		"request": req.name,
		"message": f"Lab Test Request {req.name} created.",
	}


# =========================================================
# NOTIFICATION HELPERS
# =========================================================

def _notify_visit_completed(visit):
	"""Notify doctor that a visit has been completed (if triggered externally)."""
	recipients = _get_role_users(["Receptionist"])

	doctor_user = frappe.db.get_value("Employee", visit.doctor, "user")
	if doctor_user:
		recipients.append(doctor_user)

	recipients = list(set(u for u in recipients if u))

	for user in recipients:
		frappe.publish_realtime(
			event="visit_completed",
			message={
				"title":   "Visit Completed",
				"message": f"Visit {visit.name} for patient {visit.patient} has been completed.",
				"visit":   visit.name,
				"patient": visit.patient,
				"doctor":  visit.doctor,
			},
			user=user,
		)


def _notify_lab_requested(lab_request):
	"""Notify lab technicians of a new lab test request."""
	recipients = _get_role_users(["Lab Technician"])
	for user in recipients:
		frappe.publish_realtime(
			event="lab_test_requested",
			message={
				"title":        "New Lab Test Request",
				"message":      f"Lab test '{lab_request.lab_test}' requested for patient {lab_request.patient}.",
				"lab_request":  lab_request.name,
				"patient":      lab_request.patient,
				"lab_test":     lab_request.lab_test,
			},
			user=user,
		)


def _get_role_users(roles: list) -> list:
	if not roles:
		return []
	return frappe.get_all(
		"Has Role",
		filters={"role": ["in", roles], "parenttype": "User"},
		pluck="parent",
	)