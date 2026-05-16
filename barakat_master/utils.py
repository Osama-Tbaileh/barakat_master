import frappe


def get_user_home_page(user):
	if user == "Guest":
		return "login"

	if frappe.session.data.get("user_type") == "System User":
		return None  # Frappe's default logic will send System Users to /desk

	return "site-select"
