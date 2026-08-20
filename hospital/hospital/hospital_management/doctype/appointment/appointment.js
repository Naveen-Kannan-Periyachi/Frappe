// =========================================================
// APPOINTMENT FORM CONTROLLER
// =========================================================

frappe.ui.form.on("Appointment", {

	setup(frm) {
		frm.set_query("doctor", () => ({
			filters: { employee_type: "Doctor" }
		}));
	},

	refresh(frm) {
		frm.toggle_display("status",              !frm.is_new());
		frm.toggle_display("cancellation_reason", frm.doc.status === "Cancelled");
		frm.toggle_display("arrival_time",        frm.doc.status !== "Scheduled");

		if (frm.is_new()) return;

		_render_action_buttons(frm);
		_register_realtime_listeners(frm);
	},

	doctor(frm)           { _update_available_slots(frm); },
	appointment_date(frm) { _update_available_slots(frm); },
});


// =========================================================
// ACTION BUTTONS (state-driven)
// =========================================================

function _render_action_buttons(frm) {
	const s = frm.doc.status;

	// --- SCHEDULED ---
	if (s === "Scheduled") {
		frm.add_custom_button(__("Mark Arrived"), () => {
			_call_api(frm,
				"hospital.hospital_management.doctype.appointment.appointment.mark_arrived",
				{}, __("Marking as Arrived..."), "green"
			);
		}, __("Actions")).addClass("btn-primary");

		frm.add_custom_button(__("Mark No Show"), () => {
			frappe.confirm(__("Mark this patient as No Show? This cannot be undone."), () => {
				_call_api(frm,
					"hospital.hospital_management.doctype.appointment.appointment.mark_no_show",
					{}, __("Updating..."), "orange"
				);
			});
		}, __("Actions"));

		frm.add_custom_button(__("Cancel Appointment"), () => {
			_cancel_dialog(frm);
		}, __("Actions"));
	}

	// --- ARRIVED ---
	if (s === "Arrived") {
		frm.add_custom_button(__("Start Consultation"), () => {
			_call_api(frm,
				"hospital.hospital_management.doctype.appointment.appointment.start_consultation",
				{}, __("Starting consultation..."), "blue"
			);
		}, __("Actions")).addClass("btn-primary");

		frm.add_custom_button(__("Create Visit"), () => {
			_create_visit(frm);
		}, __("Actions"));

		frm.add_custom_button(__("Mark No Show"), () => {
			frappe.confirm(__("Mark as No Show?"), () => {
				_call_api(frm,
					"hospital.hospital_management.doctype.appointment.appointment.mark_no_show",
					{}, __("Updating..."), "orange"
				);
			});
		}, __("Actions"));
	}

	// --- IN CONSULTATION ---
	if (s === "In Consultation") {
		frm.add_custom_button(__("Create Visit"), () => {
			_create_visit(frm);
		}, __("Actions")).addClass("btn-primary");
	}

	// --- CANCELLED ---
	if (s === "Cancelled") {
		frm.add_custom_button(__("Rebook Appointment"), () => {
			_rebook_dialog(frm);
		}, __("Actions")).addClass("btn-warning");
	}

	// Previous appointment link
	if (frm.doc.previous_appointment) {
		frm.add_custom_button(__("View Previous Appointment"), () => {
			frappe.set_route("Form", "Appointment", frm.doc.previous_appointment);
		});
	}
}


// =========================================================
// API HELPERS
// =========================================================

function _call_api(frm, method, extra_args, freeze_msg, indicator) {
	frappe.call({
		method,
		args:           { appointment: frm.doc.name, ...extra_args },
		freeze:         true,
		freeze_message: freeze_msg,
		callback(r) {
			if (r.message && r.message.status === "success") {
				frappe.show_alert({ message: r.message.message, indicator });
				frm.reload_doc();
			}
		},
		error(r) {
			console.error("API call failed:", r);
		}
	});
}

function _create_visit(frm) {
	frappe.call({
		method:         "hospital.hospital_management.doctype.appointment.appointment.create_visit_from_appointment",
		args:           { appointment: frm.doc.name },
		freeze:         true,
		freeze_message: __("Creating Visit..."),
		callback(r) {
			if (!r.message) return;

			if (r.message.status === "exists") {
				frappe.confirm(
					__("A visit already exists for this appointment. Open it?"),
					() => frappe.set_route("Form", "Visit", r.message.visit)
				);
				return;
			}

			frappe.show_alert({ message: r.message.message, indicator: "green" });
			frappe.set_route("Form", "Visit", r.message.visit);
		}
	});
}


// =========================================================
// CANCEL DIALOG
// =========================================================

function _cancel_dialog(frm) {
	frappe.prompt(
		[{ fieldname: "reason", fieldtype: "Small Text", label: __("Cancellation Reason"), reqd: 1 }],
		(values) => {
			frappe.call({
				method:         "hospital.hospital_management.doctype.appointment.appointment.cancel_appointment",
				args:           { appointment: frm.doc.name, reason: values.reason },
				freeze:         true,
				freeze_message: __("Cancelling appointment..."),
				callback(r) {
					if (r.message && r.message.status === "success") {
						frappe.show_alert({ message: r.message.message, indicator: "green" });
						frm.reload_doc();
					}
				}
			});
		},
		__("Cancel Appointment"),
		__("Confirm Cancellation")
	);
}


// =========================================================
// REBOOK DIALOG
// =========================================================

function _rebook_dialog(frm) {
	frappe.prompt(
		[
			{
				fieldname: "appointment_date",
				fieldtype: "Date",
				label:     __("New Appointment Date"),
				reqd:      1,
				default:   frappe.datetime.get_today()
			},
			{
				fieldname: "slot",
				fieldtype: "Select",
				label:     __("New Slot"),
				options:   _get_slot_options(frm),
				reqd:      1
			}
		],
		(values) => {
			frappe.call({
				method:         "hospital.hospital_management.doctype.appointment.appointment.rebook_appointment",
				args:           {
					appointment:      frm.doc.name,
					appointment_date: values.appointment_date,
					slot:             values.slot
				},
				freeze:         true,
				freeze_message: __("Rebooking appointment..."),
				callback(r) {
					if (r.message && r.message.status === "success") {
						frappe.show_alert({ message: r.message.message, indicator: "green" });
						frappe.set_route("Form", "Appointment", r.message.appointment);
					}
				}
			});
		},
		__("Rebook Appointment"),
		__("Confirm Rebooking")
	);
}

function _get_slot_options(frm) {
	const field = frappe.meta.get_docfield("Appointment", "slot", frm.doc.name);
	if (!field || !field.options) return [];
	return field.options.split("\n").filter(s => s.trim());
}


// =========================================================
// DYNAMIC SLOT AVAILABILITY
// =========================================================

function _update_available_slots(frm) {
	if (!frm.is_new() || !frm.doc.doctor || !frm.doc.appointment_date) return;

	frappe.call({
		method: "hospital.hospital_management.doctype.appointment.appointment.get_available_slots",
		args:   { doctor: frm.doc.doctor, appointment_date: frm.doc.appointment_date },
		callback(r) {
			if (r.exc) return;

			const slots = r.message || [];
			frm.set_df_property("slot", "options", slots.join("\n"));
			frm.refresh_field("slot");

			if (frm.doc.slot && !slots.includes(frm.doc.slot)) {
				frm.set_value("slot", "");
			}
		}
	});
}


// =========================================================
// REALTIME NOTIFICATIONS
// =========================================================

function _register_realtime_listeners(frm) {
	const events = {
		"appointment_created":      { indicator: "blue",   label: "New Appointment" },
		"appointment_arrived":      { indicator: "green",  label: "Patient Arrived" },
		"appointment_consultation": { indicator: "blue",   label: "Consultation Started" },
		"appointment_completed":    { indicator: "green",  label: "Appointment Completed" },
		"appointment_cancelled":    { indicator: "red",    label: "Appointment Cancelled" },
		"appointment_rebooked":     { indicator: "green",  label: "Appointment Rebooked" },
		"appointment_no_show":      { indicator: "orange", label: "Patient No Show" },
	};

	Object.entries(events).forEach(([event, cfg]) => {
		frappe.realtime.on(event, (data) => {
			frappe.show_alert({
				message:   `${cfg.label}: ${data.message}`,
				indicator: cfg.indicator
			});
			// Reload if this is the currently open appointment
			if (frm.doc.name === data.appointment) {
				frm.reload_doc();
			}
		});
	});
}