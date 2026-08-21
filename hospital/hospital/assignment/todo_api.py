import frappe
from frappe.utils import now


@frappe.whitelist(allow_guest=True)
def get_recent_todos():
	
	todos = frappe.get_list(
		"ToDo",
		fields=["name", "description", "owner", "creation"],
		order_by="creation desc",
		limit_page_length=5
	)

	for todo in todos:
		owner_email = frappe.db.get_value("User", todo.get("owner"), "email")
		todo["owner_email"] = owner_email

	timestamp = now()

	return {
		"timestamp": timestamp,
		"records": todos
	}
