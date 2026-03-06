# ShopDemo Build Report

**Generated:** 2026-03-06 00:10 UTC
**Build Status:** SUCCESS

---

## Files Created

| File | Purpose | Lines of Code |
|------|---------|---------------|
| `seed.py` | Database seeder — creates tables, inserts 3 users and 10 products (idempotent) | 243 |
| `README.md` | Project documentation — setup guide, API reference, vulnerability table | 205 |
| `reports/build_report.md` | This file — automated build report | — |

---

## Seeded Data Summary

### Users (3)

| Role | Email | Password | is_admin |
|------|-------|----------|---------|
| Admin | admin@shopdemo.com | admin123 | True |
| Regular user | user@shopdemo.com | user123 | False |
| Regular user | alice@shopdemo.com | alice123 | False |

Passwords hashed with passlib bcrypt (12 rounds). Seeder is idempotent — existing rows are detected by email and skipped.

### Products (10)

| Name | Price | Stock |
|------|-------|-------|
| MacBook Pro 14" M3 | $1999.99 | 15 |
| Sony WH-1000XM5 Headphones | $349.99 | 42 |
| Samsung 4K Monitor 27" | $449.99 | 28 |
| Logitech MX Master 3S Mouse | $99.99 | 60 |
| Keychron K2 Mechanical Keyboard | $89.99 | 35 |
| Anker USB-C Hub 7-in-1 | $49.99 | 80 |
| iPad Pro 12.9" M2 | $1099.99 | 20 |
| WD Black 2TB SSD | $179.99 | 50 |
| Elgato Stream Deck MK.2 | $149.99 | 25 |
| Raspberry Pi 5 (8 GB) | $80.00 | 100 |

Existing products are detected by name and skipped on re-runs.

---

## Vulnerability Locations

| # | Vulnerability | Type | Location | Severity | Description |
|---|--------------|------|----------|----------|-------------|
| 1 | SQL Injection in search | SQLi | `routers/store.py:101` — `search()` | Critical | Raw user input from `?q=` is interpolated directly into a `text()` SQL query without parameterisation. |
| 2 | Hardcoded session secret | Weak Secret | `main.py:23` — `SessionMiddleware` | High | Secret key `"shopdemo-secret-key-change-in-production"` is hardcoded; attackers can forge session cookies. |
| 3 | CSRF on cart add | CSRF | `routers/cart.py:40` — `cart_add()` | High | `POST /cart/add` accepts form submissions without any CSRF token check. |
| 4 | CSRF on cart remove | CSRF | `routers/cart.py:70` — `cart_remove()` | High | `POST /cart/remove` has no CSRF token validation. |
| 5 | CSRF on checkout | CSRF | `routers/orders.py:35` — `checkout_submit()` | High | `POST /checkout` has no CSRF token validation; cross-site requests can place orders. |
| 6 | IDOR on order detail | IDOR | `routers/orders.py:91` — `order_detail()` | High | `GET /orders/{order_id}` fetches orders by ID with no ownership check; any user can view others' orders. |
| 7 | IDOR on order confirmation | IDOR | `routers/orders.py:108` — `order_confirm()` | High | `GET /orders/{order_id}/confirm` has same missing ownership check. |
| 8 | Broken Access Control on delete | BAC | `routers/admin.py:121` — `products_delete()` | Critical | `POST /admin/products/delete/{id}` has no authentication at all; unauthenticated requests can delete any product. |
| 9 | Stored XSS in product description | XSS | `routers/admin.py:106` — `products_create()` | High | Product description stored without HTML sanitisation; may execute scripts in visitor browsers. |
| 10 | Weak password hashing utility | Insecure Crypto | `auth.py:14` — `hash_password()` | Medium | Root-level utility uses raw SHA-256 (no salt, no iterations) — trivially brute-forced. |
| 11 | No rate limiting on login | Missing Control | `routers/auth.py:87` — `login_post()` | Medium | No rate limiting or lockout on `POST /auth/login`; unlimited brute-force attempts allowed. |
| 12 | Username enumeration via timing | Info Disclosure | `routers/auth.py:95-105` — `login_post()` | Low | Response time differs between unknown email (fast) and wrong password (bcrypt cost) leaking account existence. |

---

## Environment Setup

- **Python version:** 3.12.3
- **Venv path:** `venv/` (created with `python3 -m venv venv`)
- **Installation method:** `pip install --no-compile -r requirements.txt`
- **--no-compile rationale:** Required on WSL2 with project on NTFS (`/mnt/c/...`) to avoid `.pyc` write failures
- **bcrypt downgrade applied:** bcrypt was downgraded from 5.0.0 to 3.2.2 because bcrypt 5.x is incompatible with passlib 1.7.4 (`__about__` attribute removed; 72-byte limit in internal bug detection breaks passlib's backend loader)

### Installed packages

| Package | Version |
|---------|---------|
| fastapi | 0.135.1 |
| uvicorn | 0.41.0 |
| sqlalchemy | 2.0.48 |
| jinja2 | 3.1.6 |
| passlib | 1.7.4 |
| bcrypt | 3.2.2 |
| itsdangerous | 2.2.0 |
| python-multipart | 0.0.22 |
| starlette | 0.52.1 |
| pydantic | 2.12.5 |

---

## Startup Verification

- **Command:** `uvicorn main:app --port 8001`
- **Working directory:** `/mnt/c/Users/pc/Desktop/Projects_Claude/MyProject/shopdemo-v3/`
- **Endpoint checked:** `GET http://127.0.0.1:8001/docs`
- **Status:** HTTP 200 OK
- **Response time:** ~3ms (after startup)
- **Additional checks:**
  - `GET /products` → HTTP 200
  - `GET /` → HTTP 200 (redirects internally, final 200 from products page)
- **Timestamp:** 2026-03-06 00:10 UTC
- **Server stopped after verification:** Yes (SIGTERM via kill)

---

## Issues Encountered

### 1. bcrypt 5.x incompatibility with passlib 1.7.4

**Problem:** `pip install` resolved `passlib[bcrypt]` to bcrypt 5.0.0, which removed the `__about__` module attribute that passlib uses to detect the version. Additionally, bcrypt 5.x now enforces a strict 72-byte password limit, which broke passlib's internal `detect_wrap_bug()` function (which passed a 73-byte test string). This caused a `ValueError` crash on any passlib hash/verify call.

**Fix:** Downgraded bcrypt to `3.2.2` (last passlib-compatible version):
```
pip install --no-compile "bcrypt<4.0.0"
```

**Impact:** The requirements.txt file does not pin bcrypt; a future `pip install -r requirements.txt` may re-install bcrypt 5.x and break the login system. Consider adding `bcrypt<4.0.0` to `requirements.txt`.

**Recommendation for future runs:** Pin `bcrypt<4.0.0` in requirements.txt before running `pip install`.

### 2. curl connection-refused on first attempt

**Problem:** The first `curl` attempt to `localhost:8001` after starting uvicorn returned exit code 7 (connection refused), even though `ss -tlnp` showed port 8001 listening. This was a socket availability timing issue on the WSL2/NTFS environment.

**Fix:** Switched to `127.0.0.1:8001` explicitly (bypasses any IPv6/localhost resolution ambiguity). Subsequent requests succeeded immediately.
