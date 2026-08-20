import frappe
from frappe.model.document import Document


class Department(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        department_name: DF.Data
        description: DF.SmallText | None
        status: DF.Literal["Active", "Inactive"]
    # end: auto-generated types

    def before_insert(self):
        if not self.status:
            self.status = "Active"

    def validate(self):
        self.validate_department_name()

    def validate_department_name(self):
        if not self.department_name:
            frappe.throw("Department Name is required.")

        self.department_name = self.department_name.strip()

        existing = frappe.db.exists(
            "Department",
            {
                "department_name": self.department_name,
                "name": ["!=", self.name]
            }
        )

        if existing:
            frappe.throw(
                f"Department '{self.department_name}' already exists."
            )

    def on_trash(self):
        employee_exists = frappe.db.exists(
            "Employee",
            {"department": self.name}
        )

        if employee_exists:
            frappe.throw(
                "Department cannot be deleted because employees "
                "are assigned to it."
            )