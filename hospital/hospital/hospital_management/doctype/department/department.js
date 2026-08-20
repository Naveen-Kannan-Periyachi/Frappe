frappe.ui.form.on("Department", {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("View Employees"), () => {
                frappe.set_route("List", "Employee", {
                    department: frm.doc.name
                });
            });
        }
    },

    department_name(frm) {
        if (frm.doc.department_name) {
            frm.set_value(
                "department_name",
                frm.doc.department_name.trim()
            );
        }
    }
});