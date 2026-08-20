frappe.ui.form.on("Lab Test", {

    refresh(frm) {

        frm.set_intro(
            __("Maintain the standard laboratory test details used by the hospital.")
        );
    },

    price(frm) {

        if (frm.doc.price < 0) {
            frappe.msgprint(
                __("Test price cannot be negative.")
            );

            frm.set_value("price", 0);
        }
    }

});
