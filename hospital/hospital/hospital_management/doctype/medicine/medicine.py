import frappe
from frappe.model.document import Document


class Medicine(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        description: DF.SmallText | None
        generic_name: DF.Data | None
        manufacturer: DF.Data | None
        medicine_name: DF.Data
        medicine_type: DF.Literal["Tablet", "Capsule", "Syrup", "Injection", "Cream", "Ointment", "Drops", "Other"]
        status: DF.Literal["Active", "Inactive"]
        strength: DF.Data | None
        unit: DF.Data | None
    # end: auto-generated types

    def before_insert(self):
        if not self.status:
            self.status = "Active"

    def validate(self):
        self.validate_required_values()
        self.validate_duplicate_medicine()

    def validate_required_values(self):
        if not self.medicine_name:
            frappe.throw("Medicine Name is required.")

        if not self.generic_name:
            frappe.throw("Generic Name is required.")

        if not self.medicine_type:
            frappe.throw("Medicine Type is required.")

        if not self.strength:
            frappe.throw("Strength is required.")

        if not self.unit:
            frappe.throw("Unit is required.")

    def validate_duplicate_medicine(self):
        existing = frappe.db.exists(
            "Medicine",
            {
                "medicine_name": self.medicine_name,
                "strength": self.strength,
                "name": ["!=", self.name]
            }
        )

        if existing:
            frappe.throw(
                "A medicine with the same name and strength already exists."
            )

    def on_trash(self):
        if frappe.db.exists(
            "Prescribed Medicine",
            {"medicine": self.name}
        ):
            frappe.throw(
                "Medicine cannot be deleted because it is used "
                "in existing prescriptions."
            )


@frappe.whitelist()
def get_medicine_usage(medicine):
    return frappe.db.count(
        "Prescribed Medicine",
        {"medicine": medicine}
    )