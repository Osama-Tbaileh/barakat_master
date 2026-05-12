import frappe


def after_install():
    _create_user_site_mapping_doctype()
    frappe.db.commit()


def _create_user_site_mapping_doctype():
    if frappe.db.exists("DocType", "User Site Mapping"):
        return

    doc = frappe.get_doc({
        "doctype": "DocType",
        "name": "User Site Mapping",
        "module": "Barakat Master",
        "custom": 1,
        "istable": 0,
        "track_changes": 1,
        "fields": [
            {
                "fieldname": "user",
                "fieldtype": "Link",
                "label": "User",
                "options": "User",
                "reqd": 1,
                "in_list_view": 1,
                "in_standard_filter": 1,
            },
            {
                "fieldname": "site_url",
                "fieldtype": "Data",
                "label": "Site URL",
                "reqd": 1,
                "in_list_view": 1,
                "in_standard_filter": 1,
            },
            {
                "fieldname": "company_name",
                "fieldtype": "Data",
                "label": "Company Name",
                "in_list_view": 1,
            },
            {
                "fieldname": "is_active",
                "fieldtype": "Check",
                "label": "Is Active",
                "default": "1",
                "in_list_view": 1,
            },
        ],
    })
    doc.insert(ignore_permissions=True)
