frappe.ui.form.on("Fee", {

	setup(frm) {
		frm.set_query("patient", () => ({ filters: { status: "Active" } }));
	},

	refresh(frm) {
		if (frm.is_new()) return;
		_render_fee_buttons(frm);
		_register_fee_realtime(frm);
	},

	patient(frm) {
		if (!frm.doc.patient) {
			frm.set_value("visit",  null);
			frm.set_value("doctor", null);
			return;
		}
		frm.set_query("visit", () => ({
			filters: { patient: frm.doc.patient, status: ["!=", "Cancelled"] }
		}));
		frm.set_value("visit",  null);
		frm.set_value("doctor", null);
	},

	visit(frm) {
		if (!frm.doc.visit) {
			frm.set_value("doctor", null);
			return;
		}
		frappe.db.get_value("Visit", frm.doc.visit, ["patient", "doctor"], (r) => {
			if (!r) return;
			if (r.patient !== frm.doc.patient) {
				frappe.msgprint({
					title:     __("Invalid Visit"),
					message:   __("This visit does not belong to the selected patient."),
					indicator: "red"
				});
				frm.set_value("visit",  null);
				frm.set_value("doctor", null);
				return;
			}
			frm.set_value("doctor", r.doctor);
		});
	},

	payment_method(frm) {
		const requires_ref = ["Card", "UPI", "Bank Transfer"].includes(frm.doc.payment_method);
		frm.toggle_reqd("reference_number", requires_ref);
		frm.toggle_display("reference_number", requires_ref);
	},

	payment_date(frm) {
		if (frm.doc.payment_date && frm.doc.payment_date > frappe.datetime.get_today()) {
			frappe.msgprint({
				title:     __("Invalid Payment Date"),
				message:   __("Payment Date cannot be in the future."),
				indicator: "red"
			});
			frm.set_value("payment_date", frappe.datetime.get_today());
		}
	}
});


// =========================================================
// ACTION BUTTONS
// =========================================================

function _render_fee_buttons(frm) {
	const ps = frm.doc.payment_status;

	if (ps === "Pending") {
		// Mark as Paid
		frm.add_custom_button(__("Mark as Paid"), () => {
			_mark_paid_dialog(frm);
		}).addClass("btn-primary");

		// Cancel Fee
		frm.add_custom_button(__("Cancel Fee"), () => {
			frappe.confirm(__("Are you sure you want to cancel this fee?"), () => {
				frappe.call({
					method:         "hospital.hospital_management.doctype.fee.fee.cancel_fee",
					args:           { fee: frm.doc.name },
					freeze:         true,
					freeze_message: __("Cancelling fee..."),
					callback(r) {
						if (r.message && r.message.status === "success") {
							frappe.show_alert({ message: r.message.message, indicator: "orange" });
							frm.reload_doc();
						}
					}
				});
			});
		});
	}

	// Navigate to linked visit
	if (frm.doc.visit) {
		frm.add_custom_button(__("View Visit"), () => {
			frappe.set_route("Form", "Visit", frm.doc.visit);
		});
	}
}


// =========================================================
// MARK AS PAID DIALOG
// =========================================================

function _mark_paid_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title:  __("Confirm Payment"),
		fields: [
			{
				fieldname: "payment_method",
				fieldtype: "Select",
				label:     __("Payment Method"),
				options:   "Cash\nCard\nUPI\nBank Transfer\nOther",
				reqd:      1,
				default:   frm.doc.payment_method || "Cash"
			},
			{
				fieldname:  "reference_number",
				fieldtype:  "Data",
				label:      __("Reference Number"),
				depends_on: "eval: ['Card','UPI','Bank Transfer'].includes(doc.payment_method)"
			},
			{
				fieldname:  "amount_display",
				fieldtype:  "HTML",
				options:    `<p class="text-muted">
								${__("Fee Amount")}: 
								<strong>${frappe.format(frm.doc.fee_amount, { fieldtype: "Currency" })}</strong>
							</p>`
			}
		],
		primary_action_label: __("Confirm Payment"),
		primary_action(values) {
			const requires_ref = ["Card", "UPI", "Bank Transfer"].includes(values.payment_method);
			if (requires_ref && !values.reference_number) {
				frappe.msgprint(__("Reference Number is required for this payment method."));
				return;
			}
			dialog.hide();
			frappe.call({
				method:         "hospital.hospital_management.doctype.fee.fee.mark_as_paid",
				args:           {
					fee:              frm.doc.name,
					payment_method:   values.payment_method,
					reference_number: values.reference_number || ""
				},
				freeze:         true,
				freeze_message: __("Processing payment..."),
				callback(r) {
					if (r.message && r.message.status === "success") {
						frappe.show_alert({ message: r.message.message, indicator: "green" });
						frm.reload_doc();
					}
				}
			});
		}
	});
	dialog.show();
}


// =========================================================
// REALTIME
// =========================================================

function _register_fee_realtime(frm) {
	frappe.realtime.on("payment_received", (data) => {
		frappe.show_alert({
			message:   `${data.title}: ${data.message}`,
			indicator: "green"
		});
		if (frm.doc.name === data.fee) {
			frm.reload_doc();
		}
	});
}