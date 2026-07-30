# Copyright (c) 2026, naveen and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.docstatus import DocStatus


class LibraryTransaction(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		article: DF.Link | None
		date: DF.Date | None
		library_member: DF.Link | None
		type: DF.Literal["Issue", "Return"]
	# end: auto-generated types

	_DOCTYPE_NAME = "Library Transaction"


	def before_submit(self):
		if self.type == "Issue":
			self.validate_issue()
			self.validate_max_limit()
			article =frappe.get_doc("Article", self.article)
			article.status = "Issued"
			article.save()

		if self.type == "Return":
			self.validate_return()
			article = frappe.get_doc("Article", self.article)
			article.status="Available"
			article.save()

	def validate_issue(self):
		article = frappe.get_doc("Article", self.article)
		if article.status == "Issued":
			frappe.throw("Article is already issued and not available for issue.")
	
	def validate_return(self):
		article = frappe.get_doc("Article", self.article)
		if article.status == "Available":
			frappe.throw("Article is already available and not issued.")

	def validate_max_limit(self):
		max_article = frappe.db.get_single_value("Library Settings", "max_articles")
		count = frappe.db.count(
			"Library Transaction",
			{
				"library_member": self.library_member,
				"type": "Issue",
				"docstatus": DocStatus.submitted(),
			}
		)
		if count >= max_article:
			frappe.throw(
				f"Maximum limit of {max_article} articles has been reached for this member."
			)

	def validate_membership(self):
		valid_membership = frappe.db.exists(
			"Library Membership",
			{
				"library_member": self.library_member,
				"docstatus": docstatus.submitted(),
				"from_date": ["<=", self.date],
				"to_date": [">=", self.date],
				
			}
		)

		if not valid_membership:
			frappe.throw(
				"Library Membership is not valid for the given date. Please ensure that the membership is active."
			)
