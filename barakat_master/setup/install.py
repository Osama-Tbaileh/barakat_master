import frappe


def after_install():
    # reload_doc reads the DocType JSON from disk and syncs the definition,
    # permissions (DocPerm records), and DB table in one shot.
    # This is the correct pattern — never manually insert DocType records.
    frappe.reload_doc("barakat_master", "doctype", "user_site_mapping")
    frappe.db.commit()
