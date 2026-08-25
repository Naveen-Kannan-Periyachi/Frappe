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
            frm.add_custom_button(__("Get Blood Group"), () => {
                frappe.call({
                    method: "hospital.hospital_management.doctype.patient.patient.get_patient_blood_group",
                    args: {
                        patient: frm.doc.name
                    },
                    callback: function (r) {
                        frappe.msgprint(r.message);
                    }
                });
            });
            frm.add_custom_button(__("Update Blood Group"), () => {
                frappe.call({
                    method: "hospital.hospital_management.doctype.patient.patient.update_patient_age",
                    args: {
                        patient: frm.doc.name, blood: "B+"
                    },
                    callback: function (r) {
                        frappe.msgprint(r.message);
                    }
                });
            });
            frm.add_custom_button(__("Patient Details"), () => {
                frappe.call({
                    method: "hospital.hospital_management.doctype.patient.patient.patient_details",
                    args: {
                        patient: frm.doc.name
                    },
                    callback: function (r) {
                        frappe.msgprint("details: " + r.message);
                    }
                });
            });
            frappe.ui.form.on("Patient", {
                refresh(frm) {
                    frm.add_custom_button(__("Create Task Dialog"), () => {
                        let d = new frappe.ui.Dialog({
                            title: __('Create New Task'),
                            fields: [
                                {
                                    label: __('Task Subject'),
                                    fieldname: 'task_subject',
                                    fieldtype: 'Data',
                                    reqd: 1
                                }
                            ],
                            primary_action_label: __('Create Task'),
                            primary_action(values) {
                                frappe.call({
                                    method: 'hospital.gptassignment.create_task',
                                    args: {
                                        task_subject: values.task_subject
                                    },
                                    callback: function (r) {
                                        if (r.message) {
                                            d.hide();
                                            frappe.msgprint({
                                                title: __('Task Created'),
                                                message: __('Task <b>{0}</b> created successfully.', [r.message]),
                                                indicator: 'green'
                                            });
                                        }
                                    }
                                });
                            }
                        });
                        d.show();
                    });
                }
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