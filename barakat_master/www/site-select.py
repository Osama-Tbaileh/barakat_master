import frappe

no_cache = True


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/site-select"
        raise frappe.Redirect

    if frappe.session.data.get("user_type") == "System User":
        frappe.local.flags.redirect_location = "/desk"
        raise frappe.Redirect
