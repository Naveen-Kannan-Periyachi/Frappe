frappe.ui.form.on("Visit", {

	setup(frm) {
		frm.set_query("appointment", () => ({
			filters: { status: ["in", ["Scheduled", "Arrived", "In Consultation"]] }
		}));
		frm.set_query("doctor", () => ({
			filters: { employee_type: "Doctor", status: "Active" }
		}));
		frm.set_query("patient", () => ({
			filters: { status: "Active" }
		}));
		frm.set_query("medicine", "prescribed_medicines", () => ({
			filters: { status: "Active" }
		}));
	},

	refresh(frm) {
		// Status is always controller-managed
		frm.set_df_property("status", "read_only", 1);

		if (frm.is_new()) return;

		_render_visit_buttons(frm);
		_register_visit_realtime(frm);
	},

	appointment(frm) {
		if (!frm.doc.appointment) return;

		frappe.call({
			method: "hospital.hospital_management.doctype.visit.visit.get_appointment_details",
			args:   { appointment: frm.doc.appointment },
			callback(r) {
				if (!r.message) return;
				const d = r.message;
				if (d.patient) frm.set_value("patient", d.patient);
				if (d.doctor)  frm.set_value("doctor",  d.doctor);
				if (d.appointment_date && !frm.doc.visit_datetime)
					frm.set_value("visit_datetime", d.appointment_date);
			}
		});
	},

	visit_datetime(frm) {
		if (!frm.doc.visit_datetime) return;
		if (frm.doc.visit_datetime > frappe.datetime.now_datetime()) {
			frappe.msgprint({
				title:     __("Invalid Visit Date"),
				message:   __("Visit Date & Time cannot be in the future."),
				indicator: "red"
			});
			frm.set_value("visit_datetime", null);
		}
	},

	follow_up_date(frm) {
		if (!frm.doc.follow_up_date || !frm.doc.visit_datetime) return;
		const visit_date  = frappe.datetime.str_to_obj(frm.doc.visit_datetime);
		const follow_up   = frappe.datetime.str_to_obj(frm.doc.follow_up_date);
		if (follow_up < visit_date) {
			frappe.msgprint({
				title:     __("Invalid Follow-up Date"),
				message:   __("Follow-up Date cannot be earlier than Visit Date."),
				indicator: "red"
			});
			frm.set_value("follow_up_date", null);
		}
	}
});


// =========================================================
// CHILD TABLE — Prescribed Medicine
// =========================================================

frappe.ui.form.on("Prescribed Medicine", {
	medicine(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.medicine) return;

		const duplicate = (frm.doc.prescribed_medicines || []).some(
			item => item.name !== row.name && item.medicine === row.medicine
		);
		if (duplicate) {
			frappe.msgprint({
				title:     __("Duplicate Medicine"),
				message:   __("The same medicine cannot be added twice."),
				indicator: "red"
			});
			frappe.model.set_value(cdt, cdn, "medicine", null);
		}
	}
});


// =========================================================
// ACTION BUTTONS
// =========================================================

function _render_visit_buttons(frm) {
	const s = frm.doc.status;

	// ---- OPEN VISIT ----
	if (s === "Open") {
		// Complete Visit
		frm.add_custom_button(__("Complete Visit"), () => {
			frappe.confirm(__("Mark this visit as Completed?"), () => {
				frm.set_value("status", "Completed");
				frm.save();
			});
		}).addClass("btn-primary");

		// Create Lab Request
		frm.add_custom_button(__("Create Lab Request"), () => {
			_lab_request_dialog(frm);
		}, __("Actions"));

		// View existing lab requests
		frm.add_custom_button(__("View Lab Requests"), () => {
			frappe.set_route("List", "Lab Test Request", { visit: frm.doc.name });
		}, __("Actions"));
	}

	// ---- COMPLETED VISIT ----
	if (s === "Completed") {
		// Create Fee — pre-fills consultation_fee
		frm.add_custom_button(__("Create Fee"), () => {
			_create_fee(frm);
		}, __("Actions")).addClass("btn-primary");

		frm.add_custom_button(__("View Fees"), () => {
			frappe.set_route("List", "Fee", { visit: frm.doc.name });
		}, __("Actions"));

		frm.add_custom_button(__("View Lab Requests"), () => {
			frappe.set_route("List", "Lab Test Request", { visit: frm.doc.name });
		}, __("Actions"));
	}

	// Navigate back to linked appointment
	if (frm.doc.appointment) {
		frm.add_custom_button(__("View Appointment"), () => {
			frappe.set_route("Form", "Appointment", frm.doc.appointment);
		});
	}
}


// =========================================================
// CREATE FEE
// =========================================================

function _create_fee(frm) {
	// Check if fee already exists
	frappe.db.count("Fee", { visit: frm.doc.name }).then(count => {
		if (count > 0) {
			frappe.confirm(__("A fee already exists for this visit. View it?"), () => {
				frappe.set_route("List", "Fee", { visit: frm.doc.name });
			});
			return;
		}

		frappe.call({
			method:         "hospital.hospital_management.doctype.visit.visit.create_fee_from_visit",
			args:           { visit: frm.doc.name },
			freeze:         true,
			freeze_message: __("Creating Fee..."),
			callback(r) {
				if (r.message && r.message.status === "success") {
					frappe.show_alert({ message: r.message.message, indicator: "green" });
					frappe.set_route("Form", "Fee", r.message.fee);
				}
			}
		});
	});
}


// =========================================================
// CREATE LAB REQUEST DIALOG
// =========================================================

function _lab_request_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title:  __("Create Lab Test Request"),
		fields: [
			{
				fieldname: "lab_test",
				fieldtype: "Link",
				label:     __("Lab Test"),
				options:   "Lab Test",
				reqd:      1,
				get_query: () => ({ filters: { enabled: 1 } })
			}
		],
		primary_action_label: __("Create Request"),
		primary_action(values) {
			dialog.hide();
			frappe.call({
				method:         "hospital.hospital_management.doctype.visit.visit.create_lab_request",
				args:           { visit: frm.doc.name, lab_test: values.lab_test },
				freeze:         true,
				freeze_message: __("Creating Lab Request..."),
				callback(r) {
					if (r.message && r.message.status === "success") {
						frappe.show_alert({ message: r.message.message, indicator: "green" });
						frappe.set_route("Form", "Lab Test Request", r.message.request);
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

function _register_visit_realtime(frm) {
	frappe.realtime.on("visit_completed", (data) => {
		if (frm.doc.name === data.visit) {
			frappe.show_alert({ message: data.message, indicator: "green" });
			frm.reload_doc();
		}
	});

	frappe.realtime.on("lab_test_requested", (data) => {
		frappe.show_alert({
			message:   `${data.title}: ${data.message}`,
			indicator: "blue"
		});
	});
}