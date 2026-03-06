# ShopDemo

A deliberately vulnerable e-commerce web application built with FastAPI, designed for security training and educational demonstrations. It ships with intentional vulnerabilities (SQL injection, CSRF, IDOR, Broken Access Control, XSS, weak secrets) so that learners can practice identifying and exploiting common web security issues in a safe, controlled environment.

**Do not deploy this application on a public network.**

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Web framework | FastAPI 0.x |
| ASGI server | Uvicorn |
| ORM | SQLAlchemy |
| Database | SQLite (`shopdemo.db`) |
| Templating | Jinja2 |
| Session management | Starlette `SessionMiddleware` (cookie-based, signed) |
| Authentication | Session cookies + passlib bcrypt (login flow), SHA-256 (auth.py helper — intentional weakness) |
| Forms | python-multipart |
| Password hashing | passlib\[bcrypt\] (login router), hashlib SHA-256 (auth.py utility — intentional) |

---

## Project Structure

```
shopdemo-v3/
├── main.py              # FastAPI app entry point, middleware, router mounts
├── auth.py              # Root-level auth helpers (admin_required, login_required)
├── database.py          # SQLAlchemy engine, session factory, Base
├── models.py            # ORM models: User, Product, CartItem, Order, OrderItem
├── seed.py              # Database seeder (users + products)
├── requirements.txt     # Python dependencies
├── routers/
│   ├── auth.py          # /auth/* — login, register, logout
│   ├── store.py         # / /products /product/{id} /search
│   ├── cart.py          # /cart /cart/add /cart/remove
│   ├── orders.py        # /checkout /orders /orders/{id}
│   └── admin.py         # /admin/* — dashboard, products, orders
├── templates/           # Jinja2 HTML templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── store/
│   ├── cart/
│   ├── orders/
│   └── admin/
├── static/              # CSS, JS, images
└── reports/
    └── build_report.md  # Automated build report
```

---

## Setup Instructions

### 1. Clone / obtain the project

```bash
cd /path/to/shopdemo-v3
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Linux / macOS / WSL2
source venv/bin/activate

# Windows (cmd)
venv\Scripts\activate.bat

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
# The --no-compile flag is required on WSL2 with NTFS-mounted drives (see Notes section)
pip install --no-compile -r requirements.txt
```

### 4. Seed the database

```bash
python seed.py
```

This creates `shopdemo.db` and populates it with 3 user accounts and 10 products.

### 5. Start the development server

```bash
uvicorn main:app --reload --port 8001
```

Open your browser at `http://localhost:8001`.

---

## API Endpoints

### Authentication (`/auth`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/login` | Render login page |
| POST | `/auth/login` | Submit credentials, create session |
| GET | `/auth/register` | Render registration page |
| POST | `/auth/register` | Create new account and auto-login |
| GET | `/auth/logout` | Destroy session and redirect to login |
| POST | `/auth/clear-flash` | Remove flash message from session |

### Store

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Homepage — featured products (redirects to `/products`) |
| GET | `/products` | Paginated product catalog with optional category filter |
| GET | `/product/{id}` | Product detail page |
| GET | `/search?q=...` | Product search (**intentionally vulnerable to SQL injection**) |

### Cart

| Method | Path | Description |
|--------|------|-------------|
| GET | `/cart` | View current user's cart |
| POST | `/cart/add` | Add product to cart (**no CSRF protection**) |
| POST | `/cart/remove` | Remove item from cart (**no CSRF protection**) |

### Orders

| Method | Path | Description |
|--------|------|-------------|
| GET | `/checkout` | Show cart summary before placing order |
| POST | `/checkout` | Convert cart to order (**no CSRF protection**) |
| GET | `/orders` | List authenticated user's orders |
| GET | `/orders/{order_id}` | Order detail (**IDOR — no ownership check**) |
| GET | `/orders/{order_id}/confirm` | Order confirmation (**IDOR — no ownership check**) |

### Admin (`/admin`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin` | Redirect to dashboard |
| GET | `/admin/dashboard` | Admin statistics dashboard |
| GET | `/admin/products` | List all products + create form |
| POST | `/admin/products` | Create new product (**stored XSS in description**) |
| POST | `/admin/products/delete/{id}` | Delete product (**no auth check — Broken Access Control**) |
| GET | `/admin/orders` | List all orders |

### Interactive API Docs

| Path | Description |
|------|-------------|
| `/docs` | Swagger UI (auto-generated) |
| `/redoc` | ReDoc documentation |

---

## Test Accounts

These accounts are created by `seed.py`:

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@shopdemo.com` | `admin123` |
| Regular user | `user@shopdemo.com` | `user123` |
| Regular user | `alice@shopdemo.com` | `alice123` |

---

## Known Intentional Vulnerabilities

This application is an intentional vulnerable target. The following vulnerabilities are present for educational purposes:

| # | Vulnerability | Type | Location | Severity | Description |
|---|--------------|------|----------|----------|-------------|
| 1 | SQL Injection in search | SQLi | `routers/store.py:101` — `search()` | Critical | Raw user input from `?q=` is interpolated directly into a `text()` SQL query without parameterisation. Attacker can dump tables, bypass filters, or cause errors. |
| 2 | Hardcoded session secret | Weak Secret | `main.py:23` — `SessionMiddleware` | High | The `secret_key` is hardcoded as `"shopdemo-secret-key-change-in-production"`. An attacker who knows this key can forge arbitrary session cookies. |
| 3 | CSRF on cart add | CSRF | `routers/cart.py:40` — `cart_add()` | High | `POST /cart/add` accepts form submissions without any CSRF token check. A malicious page can silently add items to a logged-in user's cart. |
| 4 | CSRF on cart remove | CSRF | `routers/cart.py:70` — `cart_remove()` | High | `POST /cart/remove` has no CSRF token validation. Any cross-site request can remove items from a victim's cart. |
| 5 | CSRF on checkout | CSRF | `routers/orders.py:35` — `checkout_submit()` | High | `POST /checkout` has no CSRF token validation. A malicious page can force a logged-in user to place an order. |
| 6 | IDOR on order detail | IDOR | `routers/orders.py:91` — `order_detail()` | High | `GET /orders/{order_id}` fetches any order by ID with no ownership check. Any authenticated user can view another user's order details by enumerating IDs. |
| 7 | IDOR on order confirmation | IDOR | `routers/orders.py:108` — `order_confirm()` | High | `GET /orders/{order_id}/confirm` has the same missing ownership check as `order_detail`. |
| 8 | Broken Access Control on product delete | BAC | `routers/admin.py:121` — `products_delete()` | Critical | `POST /admin/products/delete/{id}` has no authentication or admin check. Any unauthenticated request can permanently delete any product. |
| 9 | Stored XSS in product description | XSS | `routers/admin.py:106` — `products_create()` | High | Product `description` is stored as-is with no HTML sanitisation. If rendered unescaped in templates, malicious script tags execute in every visitor's browser. |
| 10 | Weak password hashing utility | Insecure Crypto | `auth.py:14` — `hash_password()` | Medium | The root-level `auth.py` utility uses raw SHA-256 (no salt, no iterations) to hash passwords. SHA-256 is trivially brute-forced with GPU hardware; bcrypt/argon2 should be used instead. |
| 11 | No rate limiting on login | Missing Control | `routers/auth.py:87` — `login_post()` | Medium | The `POST /auth/login` endpoint has no rate limiting or account lockout. Attackers can attempt unlimited password combinations without throttling. |
| 12 | Username enumeration via timing | Information Disclosure | `routers/auth.py:95-105` — `login_post()` | Low | The login response time differs between "user not found" (fast path) and "wrong password" (bcrypt verify) paths, leaking whether an email address is registered. |

---

## Notes for WSL2 Users

When running on WSL2 with the project on a Windows NTFS-mounted filesystem (e.g., `/mnt/c/...`), always install packages with the `--no-compile` flag:

```bash
pip install --no-compile -r requirements.txt
```

Without `--no-compile`, pip may fail or hang while trying to write `.pyc` bytecode files to NTFS mount points, which do not support the same file locking semantics as native Linux filesystems.
