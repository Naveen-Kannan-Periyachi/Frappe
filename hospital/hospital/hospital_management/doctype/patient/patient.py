import frappe
from frappe.model.document import Document


class Patient(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        address: DF.SmallText | None
        blood_group: DF.Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        date_of_birth: DF.Date
        email: DF.Data | None
        emergency_contact_name: DF.Data | None
        emergency_contact_phone: DF.Data | None
        gender: DF.Literal["Male", "Female", "Other"]
        known_allergies: DF.SmallText | None
        medical_conditions: DF.SmallText | None
        patient_name: DF.Data
        phone: DF.Data
        registration_date: DF.Date
        status: DF.Literal["Active", "Inactive"]
    # end: auto-generated types

    def before_insert(self):
        if not self.registration_date:
            self.registration_date = frappe.utils.today()

        if not self.status:
            self.status = "Active"

    def validate(self):
        self.validate_dates()
        self.validate_email()

    def validate_dates(self):
        today = frappe.utils.getdate(frappe.utils.today())

        if self.date_of_birth:
            dob = frappe.utils.getdate(self.date_of_birth)

            if dob > today:
                frappe.throw(
                    "Date of Birth cannot be in the future."
                )

        if self.registration_date:
            registration_date = frappe.utils.getdate(
                self.registration_date
            )

            if registration_date > today:
                frappe.throw(
                    "Registration Date cannot be in the future."
                )

    def validate_email(self):
        if self.email:
            if not frappe.utils.validate_email_address(self.email):
                frappe.throw(
                    "Please enter a valid email address."
                )

    def on_trash(self):
        if frappe.db.exists("Visit", {"patient": self.name}):
            frappe.throw(
                "Patient cannot be deleted because visit records exist."
            )

        if frappe.db.exists("Fee", {"patient": self.name}):
            frappe.throw(
                "Patient cannot be deleted because fee records exist."
            )