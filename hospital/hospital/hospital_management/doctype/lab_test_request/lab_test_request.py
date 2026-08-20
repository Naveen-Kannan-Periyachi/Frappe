import frappe
from frappe.model.document import Document


class LabTestRequest(Document):

	# =========================================================
	# LIFECYCLE HOOKS
	# =========================================================

	def before_insert(self):
		self._fill_from_visit()

		if not self.request_date:
			self.request_date = frappe.utils.today()
		if not self.status:
			self.status = "Requested"

		self.validate_visit()
		self.validate_duplicate_request()

	def validate(self):
		self.validate_visit()
		self.validate_duplicate_request()

		if self.status == "Completed":
			if not self.result:
				frappe.throw("Result is required before completing the lab test.")
			if not self.result_date:
				self.result_date = frappe.utils.today()

	def on_update(self):
		"""Notify doctor when the lab test result is ready."""
		new_status = self.status
		old_status = frappe.db.get_value("Lab Test Request", self.name, "status")

		if old_status != "Completed" and new_status == "Completed":
			_notify_lab_completed(self)

	# =========================================================
	# HELPERS
	# =========================================================

	def _fill_from_visit(self):
		if not self.visit:
			return
		visit = frappe.get_doc("Visit", self.visit)
		if not self.patient:
			self.patient = visit.patient
		if not self.doctor:
			self.doctor = visit.doctor

	def validate_visit(self):
		if not self.visit:
			return
		visit_status = frappe.db.get_value("Visit", self.visit, "status")
		if visit_status != "Open":
			frappe.throw("Lab tests can only be requested for an open visit.")

	def validate_duplicate_request(self):
		if not (self.visit and self.lab_test):
			return
		existing = frappe.db.exists(
			"Lab Test Request",
			{
				"visit":    self.visit,
				"lab_test": self.lab_test,
				"status":   ["!=", "Cancelled"],
				"name":     ["!=", self.name or ""],
			},
		)
		if existing:
			frappe.throw(
				"This laboratory test has already been requested for this visit."
			)


# =========================================================
# WHITELISTED API
# =========================================================

@frappe.whitelist()
def get_visit_details(visit: str):
	if not visit:
		frappe.throw("Visit is required.")
	doc = frappe.get_doc("Visit", visit)
	return {"patient": doc.patient, "doctor": doc.doctor}


# =========================================================
# NOTIFICATION
# =========================================================

def _notify_lab_completed(lab_request):
	"""Notify the requesting doctor when their lab test is complete."""
	recipients = []

	doctor_user = frappe.db.get_value("Employee", lab_request.doctor, "user")
	if doctor_user:
		recipients.append(doctor_user)

	# Also notify all lab technicians so they know it's logged
	lab_techs = frappe.get_all(
		"Has Role",
		filters={"role": "Lab Technician", "parenttype": "User"},
		pluck="parent",
	)
	recipients.extend(lab_techs)
	recipients = list(set(u for u in recipients if u))

	test_name = frappe.db.get_value("Lab Test", lab_request.lab_test, "test_name") or lab_request.lab_test

	for user in recipients:
		frappe.publish_realtime(
			event="lab_test_completed",
			message={
				"title":       "Lab Test Result Ready",
				"message":     f"Lab test '{test_name}' for patient {lab_request.patient} is complete. Result: {lab_request.result}",
				"lab_request": lab_request.name,
				"patient":     lab_request.patient,
				"lab_test":    lab_request.lab_test,
				"result":      lab_request.result,
			},
			user=user,
		)
