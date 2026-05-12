import json
import secrets

import frappe


@frappe.whitelist()
def get_user_sites():
    """
    Returns the list of active site mappings for the currently logged-in user.
    Called by the POS app right after login to master, using the master sid.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw("Authentication required.", frappe.AuthenticationError)

    mappings = frappe.get_all(
        "User Site Mapping",
        filters={"user": user, "is_active": 1},
        fields=["site_url", "company_name"],
        order_by="company_name asc",
    )
    return mappings


@frappe.whitelist()
def generate_client_token(site_url: str):
    """
    Generates a short-lived (60 s), single-use token that the POS app can redeem
    on the given client site to get a session there.

    Requires:
    - Caller must be authenticated on master (valid sid).
    - The user must have an active User Site Mapping for the requested site_url.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw("Authentication required.", frappe.AuthenticationError)

    # Verify the user actually has access to this site
    has_mapping = frappe.db.exists(
        "User Site Mapping",
        {"user": user, "site_url": site_url, "is_active": 1},
    )
    if not has_mapping:
        frappe.throw(
            f"You do not have an active mapping to site '{site_url}'.",
            frappe.PermissionError,
        )

    token = secrets.token_urlsafe(32)
    cache_key = f"barakat_client_token:{token}"
    payload = json.dumps({"user": user, "site_url": site_url})

    # Store in Redis for 60 seconds — single use, deleted on first verify
    frappe.cache.set_value(cache_key, payload, expires_in_sec=60)

    return {"token": token}


@frappe.whitelist()
def verify_client_token(token: str, site_url: str):
    """
    Verifies a token previously issued by generate_client_token.
    Called by the client site's barakat app using the master API key/secret.

    - Token is deleted immediately after first successful verification (single-use).
    - Returns {user, site_url} on success.
    - Throws AuthenticationError on any failure.
    """
    if frappe.session.user == "Guest":
        frappe.throw("Authentication required.", frappe.AuthenticationError)

    cache_key = f"barakat_client_token:{token}"
    payload_str = frappe.cache.get_value(cache_key)

    if not payload_str:
        frappe.throw(
            "Token is invalid or has expired.",
            frappe.AuthenticationError,
        )

    # Delete immediately — single use
    frappe.cache.delete_value(cache_key)

    try:
        payload = json.loads(payload_str)
    except Exception:
        frappe.throw("Token payload is corrupt.", frappe.AuthenticationError)

    if payload.get("site_url") != site_url:
        frappe.throw("Token site_url mismatch.", frappe.AuthenticationError)

    return {
        "user": payload["user"],
        "site_url": payload["site_url"],
    }
