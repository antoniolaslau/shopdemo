# ShopDemo Fix Team — Design Document

**Date:** 2026-03-07
**Project:** AI Agents Demo — Build / Pentest / Fix Pipeline
**Status:** Approved

---

## Overview

A team of 6 specialist agents that remediate the vulnerabilities discovered during the red team engagement. Each fix agent targets a single vulnerability, applies the patch directly to the source code, and verifies the fix via live HTTP requests. A reporter agent aggregates all results into a final remediation report.

---

## Team Structure

```
fix-sqli       — patches SQL Injection in routers/store.py
fix-xss        — patches Stored XSS in admin templates
fix-idor       — patches IDOR in routers/orders.py
fix-csrf       — patches CSRF across cart and order forms
fix-bac        — patches Broken Access Control in routers/admin.py
      ↓ each writes reports/fixes/<vuln>.json
fix-reporter   — aggregates all results into reports/fix_report.md
```

Fix agents run after all pentest agents have completed. There is no orchestrator at this stage — agents are invoked individually or manually sequenced.

---

## Rules of Engagement

- **Source code access.** Agents read and edit Python source files and Jinja2 templates directly.
- **HTTP verification.** Every fix is verified via `curl` against `http://localhost:8001` before the result is written.
- **Single responsibility.** Each agent fixes exactly one vulnerability type.
- **Input:** `reports/pentest_report.md` — agents read only the consolidated report, not individual pentest JSON files.
- **Evidence required.** Every fix result must include the exact `curl` command used for verification and the HTTP response that confirms the fix.

---

## Agent Responsibilities

### `fix-sqli`

- Reads `reports/pentest_report.md` for the SQL Injection finding
- Reads `routers/store.py` to locate the vulnerable raw f-string SQL query in the search endpoint
- Fixes by replacing the raw query with a safe SQLAlchemy ORM filter or parameterized query
- Verifies: `curl GET /search?q=' OR 1=1--` must no longer return all products
- Writes `reports/fixes/sqli.json`

### `fix-xss`

- Reads `reports/pentest_report.md` for the Stored XSS finding
- Reads `routers/admin.py` and `templates/admin/products.html` to locate the `| safe` Jinja2 filter on product descriptions
- Fixes by removing the `| safe` filter so Jinja2 auto-escapes output
- Verifies: posts a `<script>alert('XSS')</script>` payload via admin session, then GETs the page and confirms the tag is escaped in the HTML response
- Writes `reports/fixes/xss.json`

### `fix-idor`

- Reads `reports/pentest_report.md` for the IDOR finding
- Reads `routers/orders.py` to locate the `GET /orders/{order_id}` endpoint lacking an ownership check
- Fixes by adding a server-side check that verifies the order belongs to the current user, returning 403 if not
- Verifies: requests a user A order ID using user B's session cookie — must return 403
- Writes `reports/fixes/idor.json`

### `fix-csrf`

- Reads `reports/pentest_report.md` for the CSRF finding
- Reads `routers/cart.py`, `routers/orders.py`, and relevant templates (`cart/index.html`, `orders/checkout.html`)
- Fixes by implementing CSRF token generation stored in the session, injected as a hidden field in all POST forms, and validated server-side on every POST request
- Verifies: `curl POST /cart/add` without a CSRF token must be rejected with 403
- Writes `reports/fixes/csrf.json`

### `fix-bac`

- Reads `reports/pentest_report.md` for the Broken Access Control finding
- Reads `routers/admin.py` to locate admin endpoints lacking server-side role verification
- Fixes by adding a server-side check on every admin route that verifies `is_admin=True` from the database, returning 403 if not
- Verifies: `curl POST /admin/products/delete/{id}` with a regular user session cookie must return 403
- Writes `reports/fixes/bac.json`

### `fix-reporter`

- Checks that all 5 fix result files exist in `reports/fixes/` — if any are missing, stops and lists which agents have not completed
- Reads all 5 JSON files and `reports/pentest_report.md`
- Produces `reports/fix_report.md` containing:
  - Executive summary
  - Findings table: vulnerability / severity / fix status
  - Detailed section per vulnerability: fix description + verification evidence
  - Final remediation status

---

## Handoff Files

```
reports/fixes/
├── sqli.json       ← fix-sqli output
├── xss.json        ← fix-xss output
├── idor.json       ← fix-idor output
├── csrf.json       ← fix-csrf output
└── bac.json        ← fix-bac output

reports/fix_report.md  ← fix-reporter final output
```

### Fix agent `.json` structure

```json
{
  "vuln_type": "SQL Injection",
  "status": "fixed",
  "fix_applied": "Replaced raw f-string SQL query with SQLAlchemy ORM filter in routers/store.py",
  "verification_curl": "curl -s 'http://localhost:8001/search?q=%27%20OR%201%3D1--'",
  "verification_result": "HTTP 200 — response body returned 0 products, injection no longer bypasses filter",
  "files_modified": ["routers/store.py"]
}
```

---

## Git Strategy

This project uses **Option C** for showcasing both vulnerable and fixed code:

- `vulnerable` branch — permanent frozen snapshot of the intentionally broken application
- `main` branch — fixed version with one commit per vulnerability patch

Each fix is committed separately on `main` so the before/after diff is visible per vulnerability on GitHub.

---

## Fix Report Structure (`fix_report.md`)

```markdown
# ShopDemo Fix Report
**Date:** ...
**Source:** reports/pentest_report.md
**Team:** AI Agent Fix Team

## Executive Summary
...

## Remediation Status

| # | Vulnerability | Severity | Status |
|---|--------------|----------|--------|
| 1 | SQL Injection | High | Fixed |
| 2 | Stored XSS | High | Fixed |
| 3 | Broken Access Control | High | Fixed |
| 4 | CSRF | Medium | Fixed |
| 5 | IDOR | Medium | Fixed |

## Detailed Findings

### Fix #1 — SQL Injection
**File modified:** routers/store.py
**Fix applied:** ...
**Verification:** ...

...

## Conclusion
...
```
