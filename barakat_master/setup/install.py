import frappe


def after_install():
    _configure_website()
    _configure_languages()
    frappe.db.commit()


def _configure_website():
    website = frappe.get_doc("Website Settings", "Website Settings")
    website.hide_footer_signup = 1
    website.footer = ""
    website.save(ignore_permissions=True)


def _configure_languages():
    system = frappe.get_doc("System Settings", "System Settings")
    system.language = "en"
    system.save(ignore_permissions=True)

    # Install Arabic, English and Hebrew so the language picker appears on login
    for lang_code, lang_name in [("ar", "Arabic"), ("en", "English"), ("he", "Hebrew")]:
        if not frappe.db.exists("Language", lang_code):
            doc = frappe.new_doc("Language")
            doc.language_code = lang_code
            doc.language_name = lang_name
            doc.enabled = 1
            doc.insert(ignore_permissions=True)
        else:
            frappe.db.set_value("Language", lang_code, "enabled", 1)
