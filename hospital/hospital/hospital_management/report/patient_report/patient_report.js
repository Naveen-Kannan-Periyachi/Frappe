frappe.query_reports["Patient-Report"] = {
	filters: [
		{
			fieldname: "patient_name",
			label: __("Patient Name"),
			fieldtype: "Data",
		},
		{
			fieldname: "blood_group",
			label: __("Blood Group"),
			fieldtype: "Select",
			options: "\nA+\nA-\nB+\nB-\nAB+\nAB-\nO+\nO-",
		},
	],
	html_format: "patient_report",
};
