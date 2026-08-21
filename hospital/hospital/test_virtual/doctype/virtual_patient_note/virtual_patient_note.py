# Copyright (c) 2026, hospital and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

# Shared in-memory data store for Virtual Patient Notes
VIRTUAL_NOTES_DB = {}


class VirtualPatientNote(Document):
	# -------------------------------------------------------------
	# Virtual DocField: Dynamically calculated property (not stored)
	# -------------------------------------------------------------
	@property
	def word_count(self) -> int:
		"""Calculates total word count of content on the fly."""
		if not self.content:
			return 0
		return len(self.content.strip().split())

	# -------------------------------------------------------------
	# Virtual DocType: CRUD overrides (Bypasses MariaDB table)
	# -------------------------------------------------------------
	def db_insert(self, *args, **kwargs):
		"""Saves new record to in-memory dictionary store."""
		if not self.name:
			self.name = self.title or f"NOTE-{len(VIRTUAL_NOTES_DB) + 1:04d}"
		doc_data = self.as_dict()
		doc_data["name"] = self.name
		VIRTUAL_NOTES_DB[self.name] = doc_data

	def load_from_db(self):
		"""Loads document fields from in-memory dictionary store."""
		record = VIRTUAL_NOTES_DB.get(self.name)
		if not record:
			raise frappe.DoesNotExistError(f"Virtual Patient Note '{self.name}' not found")
		super(Document, self).__init__(record)

	def db_update(self, *args, **kwargs):
		"""Updates record in in-memory dictionary store."""
		doc_data = self.as_dict()
		VIRTUAL_NOTES_DB[self.name] = doc_data

	def delete(self, *args, **kwargs):
		"""Deletes record from in-memory dictionary store."""
		VIRTUAL_NOTES_DB.pop(self.name, None)

	@staticmethod
	def get_list(args=None, **kwargs):
		"""Returns list of all virtual notes for Frappe Desk List View."""
		results = []
		for doc in VIRTUAL_NOTES_DB.values():
			d = frappe._dict(doc)
			# Compute virtual docfield for list view items
			content_str = d.get("content", "") or ""
			d["word_count"] = len(content_str.strip().split()) if content_str else 0
			results.append(d)
		return results

	@staticmethod
	def get_count(args=None, **kwargs):
		"""Returns total record count for pagination in List View."""
		return len(VIRTUAL_NOTES_DB)

	@staticmethod
	def get_stats(args=None, **kwargs):
		"""Returns list view statistics."""
		return {}
