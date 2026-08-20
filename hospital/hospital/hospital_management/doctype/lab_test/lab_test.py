import frappe
from frappe.model.document import Document


class LabTest(Document):

    def validate(self):

        if self.price is not None and self.price < 0:
            frappe.throw(
                "Test price cannot be negative."
            )
