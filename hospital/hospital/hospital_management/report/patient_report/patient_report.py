import frappe


def execute(filters=None):
	columns = [
		{"label": "Patient ID", "fieldname": "name", "fieldtype": "Link", "options": "Patient", "width": 120},
		{"label": "Patient Name", "fieldname": "patient_name", "fieldtype": "Data", "width": 150},
		{"label": "Blood Group", "fieldname": "blood_group", "fieldtype": "Data", "width": 120},
	]

	conditions = {}
	if filters and filters.get("patient_name"):
		conditions["patient_name"] = ["like", f"%{filters.get('patient_name')}%"]
	if filters and filters.get("blood_group"):
		conditions["blood_group"] = filters.get("blood_group")

	# Fetch all real Patient documents from MariaDB database table
	data = frappe.get_all(
		"Patient",
		fields=["name", "patient_name", "blood_group"],
		filters=conditions,
		order_by="creation desc",
	)

	return columns, data
