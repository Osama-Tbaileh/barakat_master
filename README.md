### Barakat Master

Master-site app for Barakat multi-site user sync. Installed on the master site only. Pushes user changes to all registered client (POS) sites whenever a user is updated on master.

---

### How it works

- **Client → Master**: When a user is created or updated on a client site (pos3, pos4, …), the `barakat` app pushes the change to master via the Frappe REST API.
- **Master → Client**: When a user is updated on master, `barakat_master` pushes the change to every active client site mapped to that user.
- Loop prevention: client→master syncs carry `X-Barakat-Sync: 1` so master skips pushing back to the originating client.

---

### Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench install-app barakat_master --site master3.localhost
```

---

### Configuration

#### 1. Master site — `sites/master3.localhost/site_config.json`

Add `client_credentials` with one entry per client site. Each entry holds the API key and secret of the **Administrator** user on that client site.

```json
{
  "client_credentials": {
    "pos3.localhost": {
      "api_key": "<pos3 Administrator api_key>",
      "api_secret": "<pos3 Administrator api_secret>"
    },
    "pos4.localhost": {
      "api_key": "<pos4 Administrator api_key>",
      "api_secret": "<pos4 Administrator api_secret>"
    }
  }
}
```

To generate API credentials for a client site's Administrator:

```bash
bench --site pos3.localhost execute frappe.core.doctype.user.user.generate_keys --args '["Administrator"]'
```

Copy the printed `api_key` and `api_secret` into the master config above.

---

#### 2. Client site — `sites/pos3.localhost/site_config.json`

Each client site needs to know where master is and how to authenticate to it.

```json
{
  "master_url": "http://master3.localhost:8000",
  "master_api_key": "<master3 Administrator api_key>",
  "master_api_secret": "<master3 Administrator api_secret>",
  "site_url": "pos3.localhost"
}
```

- `master_url` — full URL of the master site, no port, no trailing slash (e.g. `http://master.baraka-app.com`)
- `master_api_key` / `master_api_secret` — Administrator API token on **master**
- `site_url` — this client's hostname only, no port (e.g. `pos.baraka-app.com`). Master uses this to call `http://{site_url}/api/...` on port 80 via nginx.

---

#### 3. After any config change

Restart the bench so workers and the web server reload `site_config.json`:

```bash
bench restart
```

---

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/barakat_master
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
