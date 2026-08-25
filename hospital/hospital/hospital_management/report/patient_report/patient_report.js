frappe.query_reports["Patient-Report"] = {
	filters: [
		{
			fieldname: "patient_name",
			label: __("Patient Name"),
			fieldtype: "Data",
		},
	],
	html_format: "patient_report",
};
