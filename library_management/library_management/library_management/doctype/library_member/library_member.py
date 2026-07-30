# Copyright (c) 2026, naveen and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class LibraryMember(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		email_address: DF.Data | None
		first_name: DF.Data
		full_name: DF.Data | None
		last_name: DF.Data | None
		phone: DF.Data | None
	# end: auto-generated types

	def before_save(self):
		self.full_name = f"{self.first_name} {self.last_name or ''}".strip()

	_DOCTYPE_NAME = "Library Member"