import frappe
from frappe import _


def execute(filters: dict | None = None):
	columns = [
		{
			"label": _("Patient Name"),
			"fieldname": "patient_name",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"label": _("Amount"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			"width": 120,
		},
	]

	data = [
		{
			"patient_name": "John Doe",
			"posting_date": "2026-08-01",
			"amount": 150.00,
		},
		{
			"patient_name": "Jane Smith",
			"posting_date": "2026-08-10",
			"amount": 250.50,
		},
		{
			"patient_name": "Alex Johnson",
			"posting_date": "2026-08-15",
			"amount": 180.00,
		},
	]

	return columns, data
