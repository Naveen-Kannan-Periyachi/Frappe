import frappe
from frappe.model.document import Document


class Fee(Document):
	# begin: auto-generated types
	from typing import TYPE_CHECKING
	if TYPE_CHECKING:
		from frappe.types import DF
		doctor:           DF.Link | None
		fee_amount:       DF.Currency
		patient:          DF.Link
		payment_date:     DF.Date
		payment_method:   DF.Literal["Cash", "Card", "UPI", "Bank Transfer", "Other"]
		payment_status:   DF.Literal["Pending", "Paid", "Cancelled", "Refunded"]
		reference_number: DF.Data | None
		visit:            DF.Link
	# end: auto-generated types

	# =========================================================
	# LIFECYCLE HOOKS
	# =========================================================

	def before_insert(self):
		if not self.payment_date:
			self.payment_date = frappe.utils.today()
		if not self.payment_status:
			self.payment_status = "Pending"

	def before_save(self):
		if not self.is_new():
			self._validate_status_transition()

	def validate(self):
		self.validate_patient()
		self.validate_visit()
		self.validate_amount()
		self.validate_payment_date()
		self.validate_reference_number()

	def on_update(self):
		old_status = frappe.db.get_value("Fee", self.name, "payment_status")
		if old_status != self.payment_status and self.payment_status == "Paid":
			_notify_payment_received(self)

	# =========================================================
	# STATUS TRANSITION GUARD
	# =========================================================

	def _validate_status_transition(self):
		old_status = frappe.db.get_value("Fee", self.name, "payment_status")
		if not old_status or old_status == self.payment_status:
			return

		allowed = {
			"Pending":   ["Paid", "Cancelled"],
			"Paid":      ["Refunded"],
			"Cancelled": [],
			"Refunded":  [],
		}

		if self.payment_status not in allowed.get(old_status, []):
			frappe.throw(
				f"Cannot change payment status from '{old_status}' to '{self.payment_status}'."
			)

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
			frappe.throw("Only active patients can have fees created.")

	def validate_visit(self):
		if not self.visit:
			frappe.throw("Visit is required.")
		visit = frappe.db.get_value(
			"Visit", self.visit, ["patient", "doctor", "status"], as_dict=True
		)
		if not visit:
			frappe.throw("Selected visit does not exist.")
		if visit.patient != self.patient:
			frappe.throw("Selected visit does not belong to the selected patient.")
		if visit.status == "Cancelled":
			frappe.throw("Cannot create a fee for a cancelled visit.")
		# Auto-fill doctor from visit
		self.doctor = visit.doctor

	def validate_amount(self):
		if self.fee_amount is None:
			frappe.throw("Fee Amount is required.")
		if self.fee_amount <= 0:
			frappe.throw("Fee Amount must be greater than zero.")

	def validate_payment_date(self):
		if not self.payment_date:
			frappe.throw("Payment Date is required.")
		if (
			frappe.utils.getdate(self.payment_date)
			> frappe.utils.getdate(frappe.utils.today())
		):
			frappe.throw("Payment Date cannot be in the future.")

	def validate_reference_number(self):
		digital_methods = ["Card", "UPI", "Bank Transfer"]
		if self.payment_method in digital_methods and not self.reference_number:
			frappe.throw(
				f"Reference Number is required for {self.payment_method} payments."
			)


# =========================================================
# PAYMENT API
# =========================================================

@frappe.whitelist()
def mark_as_paid(fee: str, payment_method: str, reference_number: str = None):
	"""Transition Fee from Pending → Paid."""
	if not fee:
		frappe.throw("Fee is required.")
	if not payment_method:
		frappe.throw("Payment Method is required.")

	doc = frappe.get_doc("Fee", fee)

	if not frappe.has_permission("Fee", "write", doc):
		frappe.throw("You do not have permission to update this fee.")

	if doc.payment_status != "Pending":
		frappe.throw(f"Only Pending fees can be marked as Paid (current: {doc.payment_status}).")

	digital_methods = ["Card", "UPI", "Bank Transfer"]
	if payment_method in digital_methods and not reference_number:
		frappe.throw(f"Reference Number is required for {payment_method} payments.")

	doc.payment_method   = payment_method
	doc.payment_status   = "Paid"
	doc.payment_date     = frappe.utils.today()
	if reference_number:
		doc.reference_number = reference_number

	doc.save()

	return {
		"status":  "success",
		"message": f"Fee {fee} marked as Paid successfully.",
	}


@frappe.whitelist()
def cancel_fee(fee: str):
	"""Transition Fee from Pending → Cancelled."""
	if not fee:
		frappe.throw("Fee is required.")

	doc = frappe.get_doc("Fee", fee)

	if not frappe.has_permission("Fee", "write", doc):
		frappe.throw("You do not have permission to cancel this fee.")

	if doc.payment_status != "Pending":
		frappe.throw("Only Pending fees can be cancelled.")

	doc.payment_status = "Cancelled"
	doc.save()

	return {"status": "success", "message": f"Fee {fee} cancelled."}


# =========================================================
# NOTIFICATION HELPER
# =========================================================

def _notify_payment_received(fee):
	"""Notify receptionists when a payment is marked as Paid."""
	recipients = frappe.get_all(
		"Has Role",
		filters={"role": "Receptionist", "parenttype": "User"},
		pluck="parent",
	)
	recipients = list(set(u for u in recipients if u))

	for user in recipients:
		frappe.publish_realtime(
			event="payment_received",
			message={
				"title":      "Payment Received",
				"message":    f"Payment received for Fee {fee.name}. Amount: {fee.fee_amount}.",
				"fee":        fee.name,
				"patient":    fee.patient,
				"fee_amount": fee.fee_amount,
				"method":     fee.payment_method,
			},
			user=user,
		)