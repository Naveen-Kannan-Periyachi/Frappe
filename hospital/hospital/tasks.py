"""
Scheduled background tasks for the Hospital app.
Registered via hooks.py → scheduler_events.
"""

import frappe
from frappe.utils import add_days, today


def mark_no_show_appointments():
	"""
	Daily job — automatically mark Scheduled appointments whose date has
	passed as 'No Show'.  Runs after midnight so yesterday's missed
	appointments are caught.
	"""
	yesterday = add_days(today(), -1)

	stale = frappe.get_all(
		"Appointment",
		filters={
			"status":           "Scheduled",
			"appointment_date": ["<=", yesterday],
		},
		pluck="name",
	)

	if not stale:
		return

	frappe.logger().info(
		f"mark_no_show_appointments: marking {len(stale)} appointment(s) as No Show."
	)

	for name in stale:
		try:
			doc = frappe.get_doc("Appointment", name)
			doc.status = "No Show"
			doc.save(ignore_permissions=True)
			frappe.db.commit()
		except Exception as e:
			frappe.log_error(
				title=f"No-show marking failed: {name}",
				message=frappe.get_traceback(),
			)



def daily_maintenance():
    frappe.msgprint("Daily Maintenance")
	