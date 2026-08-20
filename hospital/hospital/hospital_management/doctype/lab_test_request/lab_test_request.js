frappe.ui.form.on("Lab Test Request", {

    setup(frm) {
        frm.set_query("lab_test", () => {
            return {
                filters: {
                    enabled: 1
                }
            };
        });

        frm.set_query("doctor", () => {
            return {
                filters: {
                    employee_type: "Doctor",
                    status: "Active"
                }
            };
        });

        frm.set_query("visit", () => {
            return {
                filters: {
                    status: "Open"
                }
            };
        });
    },

    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        if (frm.doc.status === "Requested") {
            frm.add_custom_button(
                __("Collect Sample"),
                () => {
                    frm.set_value("status", "Sample Collected");
                    frm.save();
                }
            ).addClass("btn-primary");
        }

        if (frm.doc.status === "Sample Collected") {
            frm.add_custom_button(
                __("Start Processing"),
                () => {
                    frm.set_value("status", "Processing");
                    frm.save();
                }
            ).addClass("btn-primary");
        }

        if (frm.doc.status === "Processing") {
            frm.add_custom_button(
                __("Complete Test"),
                () => {
                    if (!frm.doc.result) {
                        frappe.msgprint(
                            __("Enter the test result before completing.")
                        );
                        return;
                    }

                    frm.set_value("status", "Completed");
                    frm.set_value("result_date", frappe.datetime.get_today());
                    frm.save();
                }
            ).addClass("btn-primary");
        }
    },

    visit(frm) {
        if (!frm.doc.visit) {
            return;
        }

        frappe.call({
            method: "hospital.hospital_management.doctype.lab_test_request.lab_test_request.get_visit_details",
            args: {
                visit: frm.doc.visit
            },
            callback(response) {
                if (!response.message) {
                    return;
                }

                const data = response.message;

                if (data.patient) {
                    frm.set_value("patient", data.patient);
                }

                if (data.doctor) {
                    frm.set_value("doctor", data.doctor);
                }
            }
        });
    }

});

// =========================================================
// REALTIME — Lab Test Events
// =========================================================

frappe.realtime.on("lab_test_completed", function (data) {
    frappe.show_alert({
        message:   `${data.title}: ${data.message}`,
        indicator: "green"
    });
});

frappe.realtime.on("lab_test_requested", function (data) {
    frappe.show_alert({
        message:   `${data.title}: ${data.message}`,
        indicator: "blue"
    });
});
