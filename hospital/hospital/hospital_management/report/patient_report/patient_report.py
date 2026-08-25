import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
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


@frappe.whitelist(allow_guest=True)
def get_report_html():
	columns, data = execute()
	html_content = """
	<div style="font-family: Arial, sans-serif; padding: 24px; max-width: 900px; margin: 0 auto;">
		<div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: #ffffff; padding: 24px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.15);">
			<div style="display: flex; justify-content: space-between; align-items: center;">
				<div>
					<h2 style="margin: 0; font-size: 24px; font-weight: 700; color: #38bdf8;">🏥 Patient Financial Summary Report</h2>
					<p style="margin: 6px 0 0 0; color: #94a3b8; font-size: 13px;">Updated Design &bull; Live Preview</p>
				</div>
				<div style="background: rgba(56, 189, 248, 0.15); padding: 8px 16px; border-radius: 8px; border: 1px solid rgba(56, 189, 248, 0.3);">
					<span style="font-size: 12px; color: #38bdf8; font-weight: 600;">Status: Active</span>
				</div>
			</div>
		</div>

		<table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.05);" border="1" cellpadding="12">
			<thead>
				<tr style="background-color: #f1f5f9; color: #334155; font-weight: 700;">
					<th style="padding: 12px; border-bottom: 2px solid #cbd5e1;">Patient Name</th>
					<th style="padding: 12px; border-bottom: 2px solid #cbd5e1;">Posting Date</th>
					<th style="padding: 12px; border-bottom: 2px solid #cbd5e1; text-align: right;">Amount</th>
				</tr>
			</thead>
			<tbody>
	"""
	for row in data:
		amount_str = f"${row['amount']:,.2f}"
		html_content += f"""
				<tr>
					<td style="padding: 12px; font-weight: 600; color: #0f172a;">
						<span style="display: inline-block; width: 8px; height: 8px; background-color: #10b981; border-radius: 50%; margin-right: 8px;"></span>
						{row['patient_name']}
					</td>
					<td style="padding: 12px; color: #475569;">{row['posting_date']}</td>
					<td style="padding: 12px; font-weight: 700; color: #059669; text-align: right;">{amount_str}</td>
				</tr>
		"""
	html_content += """
			</tbody>
		</table>
	</div>
	"""
	frappe.response['type'] = 'html'
	frappe.response['result'] = html_content

