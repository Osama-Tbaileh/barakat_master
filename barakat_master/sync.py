import frappe
import requests

# Must stay identical to barakat/sync.py SYNC_FIELDS
SYNC_FIELDS = [
	"first_name", "middle_name", "last_name", "username",
	"phone", "mobile_no", "birth_date", "location", "gender",
	"bio", "interest", "language", "time_zone", "enabled",
	"desk_theme", "search_bar", "notifications", "list_sidebar",
	"bulk_actions", "view_switcher", "form_sidebar", "form_navigation_buttons",
	"timeline", "dashboard", "show_absolute_datetime_in_timeline",
	"code_editor_type", "mute_sounds", "default_workspace", "default_app",
	"thread_notify", "send_me_a_copy", "allowed_in_mentions",
	"document_follow_notify", "document_follow_frequency",
	"follow_created_documents", "follow_commented_documents",
	"follow_liked_documents", "follow_shared_documents",
	"follow_assigned_documents",
]

_SKIP_USERS = {"Administrator", "Guest"}


# ---------------------------------------------------------------------------
# Hooks
# ---------------------------------------------------------------------------

def capture_new_password(doc, method):
	"""before_validate hook — stash plaintext password before Frappe clears it."""
	if doc.new_password:
		doc.flags.sync_new_password = doc.new_password


def enqueue_user_sync_to_clients(doc, method):
	"""on_update hook — push user updates to all mapped client sites."""
	if doc.name in _SKIP_USERS:
		return

	# If this save was triggered by a client sync (X-Barakat-Sync header),
	# skip pushing back — the originating client already has the data.
	if frappe.get_request_header("X-Barakat-Sync"):
		return

	mappings = frappe.get_all(
		"User Site Mapping",
		filters={"user": doc.name, "is_active": 1},
		fields=["site_url"],
	)
	if not mappings:
		return

	payload = {field: doc.get(field) for field in SYNC_FIELDS}
	payload["email"] = doc.name

	new_password = doc.flags.get("sync_new_password")
	if new_password:
		payload["new_password"] = new_password

	for mapping in mappings:
		frappe.enqueue(
			"barakat_master.sync.sync_user_to_client",
			queue="short",
			enqueue_after_commit=True,
			email=doc.name,
			site_url=mapping.site_url,
			payload=payload,
		)


# ---------------------------------------------------------------------------
# Background job: master → client
# ---------------------------------------------------------------------------

def sync_user_to_client(email, site_url, payload):
	"""
	Background worker job — push user update to a single client site.

	Requires master's site_config.json to have:
	  "client_credentials": {
	      "pos3.localhost": {"api_key": "...", "api_secret": "..."},
	      "pos4.localhost": {"api_key": "...", "api_secret": "..."}
	  }
	Each entry is a valid Frappe API token for a user on that client site.
	"""
	client_creds = frappe.conf.get("client_credentials", {}).get(site_url, {})
	api_key = client_creds.get("api_key")
	api_secret = client_creds.get("api_secret")

	if not api_key or not api_secret:
		frappe.log_error(
			f"No client_credentials configured for {site_url} in master site_config.json.",
			"User Sync to Client",
		)
		return

	port = frappe.conf.get("webserver_port", 8000)
	url = f"http://{site_url}:{port}/api/method/barakat.sync.receive_user_from_master"

	new_password = payload.get("new_password")
	user_data = {k: v for k, v in payload.items() if k != "new_password"}

	body = {"user_data": user_data}
	if new_password:
		body["new_password"] = new_password

	try:
		resp = requests.post(
			url,
			headers={
				"Authorization": f"token {api_key}:{api_secret}",
				"Content-Type": "application/json",
			},
			json=body,
			timeout=10,
		)
		resp.raise_for_status()
	except Exception as e:
		frappe.log_error(
			f"Failed to sync user {email} to client site {site_url}: {e}",
			"User Sync to Client",
		)
		raise  # re-raise so the queue retries
