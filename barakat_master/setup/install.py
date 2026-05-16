import frappe


def after_install():
    _configure_website()
    _configure_languages()
    frappe.db.commit()


def _configure_website():
    website = frappe.get_doc("Website Settings", "Website Settings")
    website.app_name = "Barakat"
    website.hide_footer_signup = 1
    website.footer_powered = 0
    website.footer = ""
    website.show_language_picker = 1
    website.custom_css = _login_custom_css()
    website.save(ignore_permissions=True)


def _configure_languages():
    system = frappe.get_doc("System Settings", "System Settings")
    system.language = "en"
    system.save(ignore_permissions=True)

    allowed = {"ar", "en", "he"}

    # Disable all languages except our three
    frappe.db.sql("UPDATE `tabLanguage` SET enabled = 0 WHERE language_code NOT IN ('ar', 'en', 'he')")

    # Ensure our three exist and are enabled
    for lang_code, lang_name in [("ar", "Arabic"), ("en", "English"), ("he", "Hebrew")]:
        if not frappe.db.exists("Language", lang_code):
            doc = frappe.new_doc("Language")
            doc.language_code = lang_code
            doc.language_name = lang_name
            doc.enabled = 1
            doc.insert(ignore_permissions=True)
        else:
            frappe.db.set_value("Language", lang_code, "enabled", 1)


def _login_custom_css():
    return """
/* ── Login page ─────────────────────────────────────── */
.login-content .app-logo {
    height: 40px;
    width: auto;
}

/* Language picker */
.lang-selector {
    position: fixed;
    top: 16px;
    right: 20px;
    z-index: 100;
}

.lang-selector select {
    border: 1px solid #e2e6ea;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 0.85rem;
    background: #fff;
    color: #444;
    cursor: pointer;
    outline: none;
}

.lang-selector select:hover {
    border-color: #4361ee;
}

/* Hide the default ugly navbar on login */
.navbar {
    display: none !important;
}

/* Clean up page background */
.for-login .login-content {
    border-radius: 12px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    border: none;
}
"""
