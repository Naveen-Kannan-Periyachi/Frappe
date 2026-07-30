# Copyright (c) 2026, naveen and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.docstatus import DocStatus


class LibraryMembership(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		from_date: DF.Date | None
		full_name: DF.Data | None
		library_member: DF.Link
		paid: DF.Check
		to_date: DF.Date | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Library Membership"

	def before_save(self):
		exist=frappe.db.exists(
			"Library Membership",
			{
				"library_member": self.library_member,
				"docstatus": DocStatus.submitted(),
				"to_date": [">=", self.from_date],
			},
		)
		if exist:
			frappe.throw(
				("Library Membership already exists for this member in the given date range.")
			)
		
		loan_period = frappe.get_doc("Library Settings").loan_period
		self.to_date = frappe.utils.add_days(self.from_date, loan_period)