"""
Hospital app — post-install setup.
Creates the custom roles required by the Hospital Management module.
"""

import frappe


ROLES = [
	{
		"role_name": "Receptionist",
		"desk_access": 1,
	},
	{
		"role_name": "Doctor",
		"desk_access": 1,
	},
	{
		"role_name": "Lab Technician",
		"desk_access": 1,
	},
	{
		"role_name": "Pharmacist",
		"desk_access": 1,
	},
	{
		"role_name": "Nurse",
		"desk_access": 1,
	},
]


def after_install():
	create_roles()
	frappe.db.commit()


def create_roles():
	for role_def in ROLES:
		name = role_def["role_name"]
		if not frappe.db.exists("Role", name):
			role = frappe.get_doc({"doctype": "Role", **role_def})
			role.insert(ignore_permissions=True)
			frappe.logger().info(f"Hospital: created role '{name}'")
		else:
			frappe.logger().info(f"Hospital: role '{name}' already exists — skipping.")


def sync_workspaces():
	import glob
	import json
	base = frappe.get_app_path("hospital", "hospital_management", "workspace")
	files = glob.glob(f"{base}/*/*.json")
	for f in files:
		with open(f) as fp:
			data = json.load(fp)
		name = data["name"]
		if frappe.db.exists("Workspace", name):
			frappe.delete_doc("Workspace", name, force=1, ignore_permissions=True)
		doc = frappe.get_doc(data)
		doc.insert(ignore_permissions=True)
		print(f"Synced workspace: {name}")
	frappe.db.commit()
