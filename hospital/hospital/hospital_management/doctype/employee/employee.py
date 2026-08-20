import frappe
from frappe.model.document import Document


class Employee(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        address: DF.SmallText | None
        consultation_fee: DF.Currency
        date_of_birth: DF.Date | None
        department: DF.Link | None
        email: DF.Data | None
        employee_name: DF.Data
        employee_type: DF.Literal["Doctor", "Nurse", "Lab Technician", "Receptionist", "Pharmacist", "Administrator"]
        gender: DF.Literal["Male", "Female", "Other"]
        joining_date: DF.Date | None
        phone: DF.Data
        qualification: DF.Data | None
        specialization: DF.Data | None
        status: DF.Literal["Active", "Inactive"]
        user: DF.Link | None
        years_of_experience: DF.Int
    # end: auto-generated types

    def before_insert(self):
        if not self.status:
            self.status = "Active"

    def validate(self):
        self.validate_dates()
        self.validate_department()
        self.validate_doctor_details()
        self.validate_user()

    def validate_dates(self):
        today = frappe.utils.getdate(frappe.utils.today())

        if self.date_of_birth:
            if frappe.utils.getdate(self.date_of_birth) > today:
                frappe.throw(
                    "Date of Birth cannot be in the future."
                )

        if self.joining_date:
            if frappe.utils.getdate(self.joining_date) > today:
                frappe.throw(
                    "Joining Date cannot be in the future."
                )

    def validate_department(self):
        if not self.department:
            frappe.throw("Department is required.")

        status = frappe.db.get_value(
            "Department",
            self.department,
            "status"
        )

        if not status:
            frappe.throw(
                "Selected department does not exist."
            )

        if status != "Active":
            frappe.throw(
                "Employee must belong to an active department."
            )

    def validate_doctor_details(self):
        if self.employee_type != "Doctor":
            return

        if not self.qualification:
            frappe.throw(
                "Qualification is required for a Doctor."
            )

        if not self.specialization:
            frappe.throw(
                "Specialization is required for a Doctor."
            )

        if self.years_of_experience is None:
            frappe.throw(
                "Years of Experience is required for a Doctor."
            )

        if self.years_of_experience < 0:
            frappe.throw(
                "Years of Experience cannot be negative."
            )

        if self.consultation_fee is None:
            frappe.throw(
                "Consultation Fee is required for a Doctor."
            )

        if self.consultation_fee < 0:
            frappe.throw(
                "Consultation Fee cannot be negative."
            )

    def validate_user(self):
        if not self.user:
            return

        existing = frappe.db.exists(
            "Employee",
            {
                "user": self.user,
                "name": ["!=", self.name]
            }
        )

        if existing:
            frappe.throw(
                "This User is already linked to another Employee."
            )

    def on_trash(self):
        if frappe.db.exists(
            "Visit",
            {"doctor": self.name}
        ):
            frappe.throw(
                "Employee cannot be deleted because "
                "visit records exist."
            )