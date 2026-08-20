frappe.ui.form.on("Medicine", {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("Check Usage"), () => {
                frappe.call({
                    method: "hospital.hospital_management.doctype.medicine.medicine.get_medicine_usage",
                    args: {
                        medicine: frm.doc.name
                    },
                    callback(r) {
                        frappe.msgprint(
                            __("This medicine has been used in {0} prescription(s).", [
                                r.message || 0
                            ])
                        );
                    }
                });
            });
        }
    }
});