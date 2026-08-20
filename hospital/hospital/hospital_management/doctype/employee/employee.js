frappe.ui.form.on("Employee", {
    refresh(frm) {
        frm.trigger("toggle_doctor_fields");
    },

    employee_type(frm) {
        frm.trigger("toggle_doctor_fields");
    },

    toggle_doctor_fields(frm) {
        const is_doctor = frm.doc.employee_type === "Doctor";

        const doctor_fields = [
            "qualification",
            "specialization",
            "years_of_experience",
            "consultation_fee"
        ];

        doctor_fields.forEach(fieldname => {
            frm.toggle_display(fieldname, is_doctor);
            frm.toggle_reqd(fieldname, is_doctor);
        });

        if (!is_doctor) {
            frm.set_value("qualification", null);
            frm.set_value("specialization", null);
            frm.set_value("years_of_experience", null);
            frm.set_value("consultation_fee", null);
        }
    },

    joining_date(frm) {
        if (!frm.doc.joining_date) {
            return;
        }

        const today = frappe.datetime.get_today();

        if (frm.doc.joining_date > today) {
            frappe.msgprint({
                title: __("Invalid Joining Date"),
                message: __("Joining Date cannot be in the future."),
                indicator: "red"
            });

            frm.set_value("joining_date", null);
        }
    }
});