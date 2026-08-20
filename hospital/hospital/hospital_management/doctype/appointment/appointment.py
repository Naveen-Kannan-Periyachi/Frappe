import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class Appointment(Document):

	# =========================================================
	# LIFECYCLE HOOKS
	# =========================================================

	def before_insert(self):
		self.status = "Scheduled"
		self.validate_slot_availability()

	def before_save(self):
		if not self.is_new():
			self._validate_status_transition()

	def _validate_status_transition(self):
		old_status = frappe.db.get_value("Appointment", self.name, "status")
		if not old_status or old_status == self.status:
			return

		allowed_transitions = {
			"Scheduled":       ["Arrived", "Cancelled", "No Show"],
			"Arrived":         ["In Consultation", "No Show"],
			"In Consultation": ["Completed"],
			"Completed":       [],
			"Cancelled":       [],
			"No Show":         [],
		}

		if self.status not in allowed_transitions.get(old_status, []):
			frappe.throw(
				f"Cannot change appointment status from '{old_status}' to '{self.status}'."
			)

	def validate_slot_availability(self):
		existing = frappe.db.exists(
			"Appointment",
			{
				"doctor":           self.doctor,
				"appointment_date": self.appointment_date,
				"slot":             self.slot,
				"status":           ["not in", ["Cancelled", "No Show"]],
				"name":             ["!=", self.name or ""],
			},
		)
		if existing:
			frappe.throw("This slot is already booked for the selected doctor.")

	def after_insert(self):
		if not getattr(self, "_is_rebooking", False):
			notify_appointment(
				self,
				event="appointment_created",
				title="New Appointment",
				message=(
					f"New appointment {self.name} has been booked "
					f"for {self.appointment_date} at {self.slot}."
				),
			)

	def on_update(self):
		old_status = getattr(self, "_prev_status", None)
		if old_status and old_status != self.status:
			_dispatch_status_notification(self, old_status, self.status)


# =========================================================
# APPOINTMENT STATUS TRANSITION APIs
# =========================================================

@frappe.whitelist()
def mark_arrived(appointment: str):
	"""Scheduled → Arrived. Records arrival time."""
	doc = _get_appointment_with_write_perm(appointment)

	if doc.status != "Scheduled":
		frappe.throw("Only Scheduled appointments can be marked as Arrived.")

	doc._prev_status = doc.status
	doc.status = "Arrived"
	doc.arrival_time = now_datetime().strftime("%H:%M:%S")
	doc.save()

	return {"status": "success", "message": "Patient marked as Arrived."}


@frappe.whitelist()
def start_consultation(appointment: str):
	"""Arrived → In Consultation."""
	doc = _get_appointment_with_write_perm(appointment)

	if doc.status != "Arrived":
		frappe.throw("Appointment must be Arrived before starting consultation.")

	doc._prev_status = doc.status
	doc.status = "In Consultation"
	doc.save()

	return {"status": "success", "message": "Consultation started."}


@frappe.whitelist()
def mark_no_show(appointment: str):
	"""Scheduled or Arrived → No Show."""
	doc = _get_appointment_with_write_perm(appointment)

	if doc.status not in ["Scheduled", "Arrived"]:
		frappe.throw("Only Scheduled or Arrived appointments can be marked as No Show.")

	doc._prev_status = doc.status
	doc.status = "No Show"
	doc.save()

	return {"status": "success", "message": "Appointment marked as No Show."}


@frappe.whitelist()
def create_visit_from_appointment(appointment: str):
	"""
	Create a Visit linked to this Appointment.
	Also advances Arrived → In Consultation.
	Returns the visit name.
	"""
	doc = frappe.get_doc("Appointment", appointment)

	if doc.status not in ["Arrived", "In Consultation"]:
		frappe.throw(
			"A visit can only be created for an Arrived or In Consultation appointment."
		)

	# Check if a visit already exists for this appointment
	existing_visit = frappe.db.get_value(
		"Visit", {"appointment": appointment}, "name"
	)
	if existing_visit:
		return {
			"status": "exists",
			"visit":  existing_visit,
			"message": "A visit already exists for this appointment.",
		}

	visit = frappe.get_doc({
		"doctype":        "Visit",
		"appointment":    appointment,
		"patient":        doc.patient,
		"doctor":         doc.doctor,
		"visit_datetime": now_datetime(),
		"status":         "Open",
	})
	visit.insert()

	# Advance appointment status if it was still Arrived
	if doc.status == "Arrived":
		frappe.db.set_value("Appointment", appointment, "status", "In Consultation")

	return {
		"status":  "success",
		"visit":   visit.name,
		"message": f"Visit {visit.name} created successfully.",
	}


# =========================================================
# AVAILABLE SLOTS
# =========================================================

@frappe.whitelist()
def get_available_slots(doctor: str, appointment_date: str):
	all_slots = get_slot_options()

	if not doctor or not appointment_date:
		return all_slots

	booked_slots = frappe.get_all(
		"Appointment",
		filters={
			"doctor":           doctor,
			"appointment_date": appointment_date,
			"status":           ["not in", ["Cancelled", "No Show"]],
		},
		pluck="slot",
	)

	return [slot for slot in all_slots if slot not in booked_slots]


def get_slot_options():
	field = frappe.get_meta("Appointment").get_field("slot")
	if not field:
		frappe.throw("Slot field is missing in Appointment.")
	return [
		opt.strip()
		for opt in (field.options or "").split("\n")
		if opt.strip()
	]


# =========================================================
# CANCEL APPOINTMENT
# =========================================================

@frappe.whitelist()
def cancel_appointment(appointment: str, reason: str):
	if not appointment:
		frappe.throw("Appointment is required.")
	if not reason or not reason.strip():
		frappe.throw("Cancellation reason is required.")

	doc = _get_appointment_with_write_perm(appointment)

	if doc.status != "Scheduled":
		frappe.throw("Only Scheduled appointments can be cancelled.")

	doc._prev_status = doc.status
	doc.status = "Cancelled"
	doc.cancellation_reason = reason.strip()
	doc.save()

	return {"status": "success", "message": "Appointment cancelled successfully."}


# =========================================================
# REBOOK APPOINTMENT
# =========================================================

@frappe.whitelist()
def rebook_appointment(appointment: str, appointment_date: str, slot: str):
	if not appointment:
		frappe.throw("Appointment is required.")
	if not appointment_date:
		frappe.throw("Appointment date is required.")
	if not slot:
		frappe.throw("Appointment slot is required.")

	old_doc = frappe.get_doc("Appointment", appointment)

	if old_doc.status != "Cancelled":
		frappe.throw("Only cancelled appointments can be rebooked.")

	new_appointment = frappe.get_doc({
		"doctype":              "Appointment",
		"patient":              old_doc.patient,
		"doctor":               old_doc.doctor,
		"appointment_date":     appointment_date,
		"slot":                 slot,
		"previous_appointment": old_doc.name,
	})
	new_appointment._is_rebooking = True
	new_appointment.insert()

	notify_appointment(
		new_appointment,
		event="appointment_rebooked",
		title="Appointment Rebooked",
		message=(
			f"Appointment {new_appointment.name} has been rebooked "
			f"for {new_appointment.appointment_date} at {new_appointment.slot}."
		),
	)

	return {
		"status":      "success",
		"appointment": new_appointment.name,
		"message":     "Appointment rebooked successfully.",
	}


# =========================================================
# PRIVATE HELPERS
# =========================================================

def _get_appointment_with_write_perm(appointment: str):
	doc = frappe.get_doc("Appointment", appointment)
	if not frappe.has_permission("Appointment", "write", doc):
		frappe.throw("You do not have permission to update this appointment.")
	return doc


def _dispatch_status_notification(appointment, old_status: str, new_status: str):
	event_map = {
		"Arrived":         ("appointment_arrived",      "Patient Arrived",         f"Patient has arrived for appointment {appointment.name}."),
		"In Consultation": ("appointment_consultation", "Consultation Started",    f"Consultation started for appointment {appointment.name}."),
		"Completed":       ("appointment_completed",    "Appointment Completed",   f"Appointment {appointment.name} has been completed."),
		"No Show":         ("appointment_no_show",      "Patient No Show",         f"Patient did not show up for appointment {appointment.name}."),
		"Cancelled":       ("appointment_cancelled",    "Appointment Cancelled",   f"Appointment {appointment.name} was cancelled. Reason: {appointment.cancellation_reason}"),
	}

	if new_status not in event_map:
		return

	event, title, message = event_map[new_status]
	notify_appointment(appointment, event=event, title=title, message=message)


def get_doctor_user(doctor):
	if not doctor:
		return None
	employee_meta = frappe.get_meta("Employee")
	for fieldname in ["user", "user_id"]:
		if employee_meta.get_field(fieldname):
			return frappe.db.get_value("Employee", doctor, fieldname)
	return None


def get_notification_recipients(appointment):
	recipients = []

	doctor_user = get_doctor_user(appointment.doctor)
	if doctor_user:
		recipients.append(doctor_user)

	receptionists = frappe.get_all(
		"Has Role",
		filters={"role": "Receptionist", "parenttype": "User"},
		pluck="parent",
	)
	recipients.extend(receptionists)

	return list(set(u for u in recipients if u))


def notify_appointment(appointment, event, title, message):
	recipients = get_notification_recipients(appointment)
	for user in recipients:
		frappe.publish_realtime(
			event=event,
			message={
				"title":            title,
				"message":          message,
				"appointment":      appointment.name,
				"patient":          appointment.patient,
				"doctor":           appointment.doctor,
				"appointment_date": str(appointment.appointment_date),
				"slot":             appointment.slot,
				"status":           appointment.status,
			},
			user=user,
		)