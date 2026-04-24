# ShopDemo: Build, Pentest, Fix

A full-cycle security demonstration project — a deliberately vulnerable e-commerce web application built with FastAPI, audited by an AI-powered red team, and fully remediated by an AI-powered fix team.

> **Do not deploy this application on a public network.**

---

## Pipeline Overview

This project demonstrates a complete **Build → Pentest → Fix** pipeline, each phase driven by a team of specialized AI agents built with Claude Code.

```
Build Team        →   Pentest Team       →   Fix Team
──────────────────    ─────────────────      ────────────────
build-foundation      pentest-recon          fix-sqli
build-auth            pentest-sqli           fix-xss
build-store           pentest-xss            fix-idor
build-cart-orders     pentest-idor           fix-csrf
build-admin           pentest-csrf           fix-bac
build-finalize        pentest-bac            fix-reporter
                      pentest-reporter
```

- **Build team** — scaffolds the full FastAPI application with intentional vulnerabilities embedded for training purposes
- **Pentest team** — conducts a black-box red team engagement via live HTTP (`curl`), producing structured JSON findings and a consolidated pentest report
- **Fix team** — reads the pentest report, patches each vulnerability directly in the source code, verifies the fix via HTTP, and produces a fix report

All agent definitions are in [`.claude/agents/`](.claude/agents/).

---

## Two-Branch Strategy

| Branch | Purpose |
|--------|---------|
| `vulnerable` | Frozen snapshot of the application **before** any fixes — intentional vulnerabilities intact |
| `main` | Fixed version — each vulnerability patched in a separate commit |

To compare a vulnerability before and after the fix, switch branches on GitHub or use:

```bash
# Run the vulnerable version
git checkout vulnerable
uvicorn main:app --port 8001 --reload

# Run the fixed version in a separate directory
git worktree add ../shopdemo-main main
cd ../shopdemo-main
uvicorn main:app --port 8002 --reload
```

---

## Reports

| Report | Description |
|--------|-------------|
| [`reports/pentest_report.md`](reports/pentest_report.md) | Full red team findings — 3 High, 2 Medium severity vulnerabilities |
| [`reports/fix_report.md`](reports/fix_report.md) | Remediation report — 5/5 vulnerabilities patched and verified |
| [`reports/build_report.md`](reports/build_report.md) | Build team output — file map and known deviations |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Web framework | FastAPI |
| ASGI server | Uvicorn |
| ORM | SQLAlchemy |
| Database | SQLite (`shopdemo.db`) |
| Templating | Jinja2 |
| Session management | Starlette `SessionMiddleware` (cookie-based, signed) |
| Authentication | Session cookies + passlib bcrypt |
| Forms | python-multipart |
| Password hashing | passlib[bcrypt] |
| Linter / formatter | Ruff (configured in `pyproject.toml`) |

---

## Project Structure

```
shopdemo/
├── main.py              # FastAPI app entry point, middleware, router mounts
├── auth.py              # Auth helpers (admin_required, login_required)
├── database.py          # SQLAlchemy engine, session factory, Base
├── models.py            # ORM models: User, Product, Category, CartItem, Order, OrderItem
├── seed.py              # Database seeder (categories, users, products)
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Ruff linter/formatter configuration
├── run.sh               # One-command startup script (drop DB → seed → serve)
├── routers/
│   ├── auth.py          # /auth/* — login, register, logout
│   ├── store.py         # / /products /product/{id} /search
│   ├── cart.py          # /cart /cart/add /cart/remove
│   ├── orders.py        # /checkout /orders /orders/{id}
│   ├── admin.py         # /admin/* — dashboard, products, orders, categories
│   └── categories.py    # /categories /categories/{slug}
├── services/
│   └── category_service.py  # Category business logic (service layer)
├── utils/
│   └── csrf.py          # CSRF token generation and validation
├── templates/           # Jinja2 HTML templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── store/
│   ├── cart/
│   ├── orders/
│   ├── admin/
│   └── categories/
├── static/              # CSS and assets
├── docs/plans/          # Design documents for each pipeline phase
└── reports/
    ├── build_report.md
    ├── pentest_report.md
    ├── fix_report.md
    └── pentest/         # Raw JSON output from each pentest agent
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/antoniolaslau/shopdemo.git
cd shopdemo
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
# Use --no-compile on WSL2 with NTFS-mounted drives (see Notes section)
pip install --no-compile -r requirements.txt
```

### 4. Start the application

```bash
bash run.sh
```

`run.sh` drops any existing `shopdemo.db`, reseeds it (7 categories, 3 users, 10 products), and starts Uvicorn on port 8001. Open `http://localhost:8001` in your browser.

**Or manually:**

```bash
python seed.py
uvicorn main:app --reload --port 8001
```

---

## Test Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@shopdemo.com` | `admin123` |
| Regular user | `user@shopdemo.com` | `user123` |
| Regular user | `alice@shopdemo.com` | `alice123` |

---

## Vulnerabilities

### Fixed (on `main`)

| # | Vulnerability | Severity | Location | Fix Applied |
|---|--------------|----------|----------|-------------|
| 1 | SQL Injection | High | `routers/store.py` — `search()` | Replaced raw f-string SQL with SQLAlchemy ORM `ilike()` filter |
| 2 | Stored XSS | High | `templates/admin/products.html` | Removed `\| safe` filter — Jinja2 auto-escaping now active |
| 3 | Broken Access Control | High | `routers/admin.py` — `products_delete()` | Added `require_admin` dependency with server-side `is_admin` check |
| 4 | CSRF | Medium | `routers/cart.py`, `routers/orders.py` | Implemented synchronizer token pattern via `utils/csrf.py` |
| 5 | IDOR | Medium | `routers/orders.py` — `order_detail()` | Added ownership check — returns 403 if order does not belong to current user |

### Known Remaining Issues

| # | Vulnerability | Severity | Location | Notes |
|---|--------------|----------|----------|-------|
| 1 | Hardcoded session secret | High | `main.py` — `SessionMiddleware` | `secret_key` is hardcoded — must be replaced with an environment variable in production |
| 2 | CSRF coverage incomplete | Medium | `routers/auth.py`, `routers/admin.py` | 5 additional POST endpoints not yet covered by CSRF validation |
| 3 | No rate limiting on login | Medium | `routers/auth.py` — `login_post()` | No throttling or account lockout on failed login attempts |
| 4 | Weak password hashing utility | Medium | `auth.py` — `hash_password()` | Root-level utility uses SHA-256 without salt — bcrypt used in the login router but not everywhere |
| 5 | Username enumeration via timing | Low | `routers/auth.py` — `login_post()` | Response time differs between unknown email and wrong password paths |

---

## Reproducing the Vulnerabilities

> First checkout the `vulnerable` branch and start the server on port 8001. Full reproduction details are in [`reports/pentest_report.md`](reports/pentest_report.md).

| # | Vulnerability | How to Reproduce |
|---|--------------|-----------------|
| 1 | **SQL Injection** | Go to `http://localhost:8001/search`, type `' OR 1=1--` in the search box and submit. All products are returned instead of a filtered result. |
| 2 | **Stored XSS** | Login as admin, go to `http://localhost:8001/admin/products`, create a product with description `<script>alert('XSS')</script>`. Reload the page — a browser alert popup executes. |
| 3 | **Broken Access Control** | Login as `user@shopdemo.com`, open browser console and run `fetch('/admin/products/delete/1', {method: 'POST'})`. Product is deleted despite the user not being an admin. |
| 4 | **CSRF** | While logged in as any user, run `fetch('/cart/add', {method: 'POST', body: new URLSearchParams({product_id: '1', quantity: '1'})})` from any page — no CSRF token required, request succeeds. |
| 5 | **IDOR** | Login as `alice@shopdemo.com`, navigate to `http://localhost:8001/orders/1` — Alice can view orders placed by other users by enumerating IDs. |

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

### Store

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Homepage — featured products |
| GET | `/products` | Paginated product catalog with category filter sidebar |
| GET | `/product/{id}` | Product detail page |
| GET | `/search?q=...` | Product search |

### Categories

| Method | Path | Description |
|--------|------|-------------|
| GET | `/categories` | Category listing page |
| GET | `/categories/{slug}` | All active products in a category |

### Cart

| Method | Path | Description |
|--------|------|-------------|
| GET | `/cart` | View current user's cart |
| POST | `/cart/add` | Add product to cart |
| POST | `/cart/remove` | Remove item from cart |

### Orders

| Method | Path | Description |
|--------|------|-------------|
| GET | `/checkout` | Show cart summary before placing order |
| POST | `/checkout` | Convert cart to order |
| GET | `/orders` | List authenticated user's orders |
| GET | `/orders/{order_id}` | Order detail |
| GET | `/orders/{order_id}/confirm` | Order confirmation |

### Admin (`/admin`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/dashboard` | Admin statistics dashboard |
| GET | `/admin/products` | List all products + create form |
| POST | `/admin/products` | Create new product |
| POST | `/admin/products/delete/{id}` | Delete product |
| GET | `/admin/orders` | List all orders |
| GET | `/admin/categories` | List all categories + create form |
| POST | `/admin/categories` | Create new category |
| POST | `/admin/categories/delete/{id}` | Delete category |

### Interactive API Docs

| Path | Description |
|------|-------------|
| `/docs` | Swagger UI (auto-generated) |
| `/redoc` | ReDoc documentation |

---

## Agent Architecture

Each agent in this project was designed with a single responsibility — one job, one input, one output. Just like hiring specialists instead of generalists: you don't ask your security auditor to also write the code, and you don't ask your developer to also run the penetration tests.

Every agent knows exactly what it receives (a report or a JSON file), what it must do, and what it must produce before handing off to the next. This makes the pipeline reliable, traceable, and easy to extend — add a new agent without touching the others.

The full design decisions behind each team are documented in [`docs/plans/`](docs/plans/).

---

## Software Engineering Practices

Beyond the security pipeline, this project demonstrates several software engineering techniques applied to a real codebase.

### Service Layer Pattern

The categories feature was built with a deliberate architectural separation that the original routers do not have:

```
Request → Router (HTTP only) → Service (business logic) → Database
```

- **`routers/categories.py`** — thin HTTP layer. Each route handler is a single call into the service and a template response. No database queries, no business logic.
- **`services/category_service.py`** — owns all category logic: fetching, creating, deleting, slug uniqueness checks. No HTTP concepts here — just functions that take a `db` session and return data.

This makes the business logic independently testable and reusable. Compare `routers/categories.py` to `routers/admin.py` — the contrast between the two styles is intentional and visible in the same codebase.

### Code Quality Tooling

`pyproject.toml` configures **Ruff** as the project's linter and formatter:

```bash
# Check for issues
ruff check .

# Auto-fix and format
ruff format .
```

The active ruleset covers style (E/W), unused imports (F), import ordering (I), modern Python syntax (UP), common bugs (B), and comprehension improvements (C4). Line-length formatting is delegated to `ruff format`.

---

## Future Enhancements

- **Offensive tools for pentest agents** — integrate `sqlmap`, `nikto`, and `ffuf` into the pentest pipeline for deeper, automated vulnerability discovery (agents currently use `curl` only)
- **CSRF coverage** — extend token validation to all remaining unprotected POST endpoints (`/auth`, `/admin`)
- **Fix pipeline orchestrator** — a single agent that runs all fix agents sequentially and produces the final report automatically
- **Environment variables** — replace hardcoded session secret with `.env` file support
- **Service layer expansion** — apply the service layer pattern to the existing auth, store, cart, and order routers
- **Unit tests** — add a `tests/` layer with pytest; the service layer in `services/` is already structured for easy unit testing without HTTP
- **README badges** — add Python version, FastAPI, SQLite, and license badges

---

## Notes for WSL2 Users

When running on WSL2 with the project on a Windows NTFS-mounted filesystem (e.g., `/mnt/c/...`), always install packages with the `--no-compile` flag:

```bash
pip install --no-compile -r requirements.txt
```

Without `--no-compile`, pip may fail or hang while writing `.pyc` bytecode files to NTFS mount points, which do not support the same file locking semantics as native Linux filesystems.
