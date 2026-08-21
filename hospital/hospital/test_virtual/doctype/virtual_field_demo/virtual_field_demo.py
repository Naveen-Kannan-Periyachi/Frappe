# Copyright (c) 2026, hospital and contributors
# For license information, please see license.txt

from datetime import datetime
from frappe.model.document import Document


class VirtualFieldDemo(Document):
	# -------------------------------------------------------------
	# Virtual DocField 1: Combined Full Name (Not stored in DB column)
	# -------------------------------------------------------------
	@property
	def full_name(self) -> str:
		"""Combines first_name and last_name dynamically."""
		return f"{self.first_name or ''} {self.last_name or ''}".strip()

	# -------------------------------------------------------------
	# Virtual DocField 2: Calculated Age (Not stored in DB column)
	# -------------------------------------------------------------
	@property
	def calculated_age(self) -> int:
		"""Calculates age dynamically from birth_year."""
		if not self.birth_year:
			return 0
		current_year = datetime.now().year
		return max(0, current_year - self.birth_year)
