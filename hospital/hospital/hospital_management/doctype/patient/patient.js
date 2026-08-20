frappe.ui.form.on("Patient", {

    onload(frm) {
        if (frm.is_new() && !frm.doc.registration_date) {
            frm.set_value("registration_date", frappe.datetime.get_today());
        }
    },
    refresh(frm) {
        frm.set_df_property("status", "read_only", frm.is_new() ? 0 : 0);

        if (!frm.is_new()) {
            frm.add_custom_button(__("View Visits"), () => {
                frappe.set_route("List", "Visit", {
                    patient: frm.doc.name
                });
            });

            frm.add_custom_button(__("View Fees"), () => {
                frappe.set_route("List", "Fee", {
                    patient: frm.doc.name
                });
            });
        }
    },

    date_of_birth(frm) {
        if (!frm.doc.date_of_birth) {
            return;
        }

        const today = frappe.datetime.get_today();

        if (frm.doc.date_of_birth > today) {
            frappe.msgprint({
                title: __("Invalid Date of Birth"),
                message: __("Date of Birth cannot be in the future."),
                indicator: "red"
            });

            frm.set_value("date_of_birth", null);
        }
    },

    registration_date(frm) {
        if (!frm.doc.registration_date) {
            return;
        }

        const today = frappe.datetime.get_today();

        if (frm.doc.registration_date > today) {
            frappe.msgprint({
                title: __("Invalid Registration Date"),
                message: __("Registration Date cannot be in the future."),
                indicator: "red"
            });

            frm.set_value("registration_date", today);
        }
    }
});