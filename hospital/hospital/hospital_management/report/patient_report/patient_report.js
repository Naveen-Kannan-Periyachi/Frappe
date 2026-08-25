frappe.query_reports["Patient-Report"] = {
	filters: [
		{
			fieldname: "patient_name",
			label: __("Patient Name"),
			fieldtype: "Data",
		},
		{
			fieldname: "gender",
			label: __("Gender"),
			fieldtype: "Select",
			options: "\nMale\nFemale\nOther",
		},
		{
			fieldname: "blood_group",
			label: __("Blood Group"),
			fieldtype: "Select",
			options: "\nA+\nA-\nB+\nB-\nAB+\nAB-\nO+\nO-",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nActive\nInactive",
		},
	],
	html_format: "patient_report",
};
