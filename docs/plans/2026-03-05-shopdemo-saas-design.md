# ShopDemo SaaS — Design Document

**Date:** 2026-03-05
**Project:** AI Agents Demo — Build / Pentest / Fix Pipeline
**Status:** Approved

---

## Overview

A functional e-commerce SaaS called **ShopDemo** built as a demo application for learning AI agent orchestration. Three teams of agents work sequentially: build the app, pentest it, and fix the findings.

---

## Domain & Scope

**Domain:** E-commerce / Online Store
**Focus:** Full store — products, cart, checkout, orders, user accounts, admin panel

### Core Pages & Features

| Area      | Features                                           |
|-----------|----------------------------------------------------|
| Auth      | Register, Login, Logout (session + cookie)         |
| Store     | Product listing, product detail, search            |
| Cart      | Add/remove items, view cart                        |
| Checkout  | Place order, confirmation page                     |
| Account   | Order history, order detail                        |
| Admin     | Product CRUD, order list                           |

---

## Tech Stack

| Layer      | Technology                              |
|------------|-----------------------------------------|
| Backend    | Python 3.11+ / FastAPI                  |
| Frontend   | Jinja2 templates + Bootstrap 5          |
| Database   | SQLite (file-based, zero setup)         |
| Auth       | Server-side sessions + signed cookies   |
| API Docs   | Swagger UI at `/docs` (built-in)        |
| Dev server | Uvicorn with `--reload`                 |

---

## Project Structure

```
shopdemo/
├── app/
│   ├── main.py              # FastAPI app entry, mounts routes & static
│   ├── database.py          # SQLite engine, session factory, seed data
│   ├── models.py            # SQLAlchemy ORM models
│   ├── auth.py              # Session helpers, login_required decorator
│   ├── routes/
│   │   ├── auth.py          # /register, /login, /logout
│   │   ├── store.py         # /, /products, /product/{id}, /search
│   │   ├── cart.py          # /cart, /cart/add, /cart/remove
│   │   ├── orders.py        # /checkout, /orders, /orders/{id}
│   │   └── admin.py         # /admin/* (products CRUD, orders list)
│   ├── templates/
│   │   ├── base.html        # Layout + Bootstrap navbar/footer
│   │   ├── auth/            # login.html, register.html
│   │   ├── store/           # index.html, product.html, search.html
│   │   ├── cart/            # cart.html, checkout.html, confirm.html
│   │   ├── orders/          # orders.html, order_detail.html
│   │   └── admin/           # dashboard.html, products.html, orders.html
│   └── static/
│       └── css/style.css    # Bootstrap + minimal custom CSS
├── seed.py                  # Seeds DB with products + sample accounts
├── reports/
│   ├── build_report.md      # Build team output
│   ├── pentest_report.md    # Pentest team findings
│   └── fix_report.md        # Fix team remediation log
├── requirements.txt
└── README.md
```

---

## Data Models

```python
User        — id, email, password_hash, is_admin, created_at
Product     — id, name, description, price, stock, image_url
CartItem    — id, user_id, product_id, quantity
Order       — id, user_id, total, status, created_at
OrderItem   — id, order_id, product_id, quantity, price
```

---

## Seeded Sample Accounts

Created automatically by `seed.py` on first run:

| Role    | Email                  | Password   |
|---------|------------------------|------------|
| Admin   | admin@shopdemo.com     | admin123   |
| User 1  | user@shopdemo.com      | user123    |
| User 2  | alice@shopdemo.com     | alice123   |

Two regular users exist to enable IDOR demonstration (User 1 accessing User 2's orders).

---

## Seeded Vulnerabilities

Built alongside normal code. Marked with `# VULN:<type>` comments for agent discoverability.

| # | Type                    | Location                        | How it manifests                                          |
|---|-------------------------|---------------------------------|-----------------------------------------------------------|
| 1 | **SQL Injection**       | `routes/store.py` — search      | Raw f-string: `WHERE name LIKE '%{term}%'`                |
| 2 | **IDOR**                | `routes/orders.py` — `/orders/{id}` | No ownership check on order access                   |
| 3 | **Stored XSS**          | Admin product create — description | Rendered unescaped: `{{ desc \| safe }}`              |
| 4 | **CSRF**                | Checkout + cart forms           | No CSRF token on POST forms                               |
| 5 | **Broken Access Control** | `routes/admin.py`             | Admin role checked via client-side field, not server role |

Fix agents can locate tagged vulnerabilities via `grep -r "VULN:"` and also find untagged real mistakes.

---

## Local Run

```bash
cd shopdemo
pip install -r requirements.txt
python seed.py                              # Create DB + seed data
uvicorn app.main:app --reload --port 8000   # Start server

# App:      http://localhost:8000
# API docs: http://localhost:8000/docs
```

---

## Agent Interaction Model

| Team              | Interaction method                                                     |
|-------------------|------------------------------------------------------------------------|
| **Build agents**  | Write/Edit source files directly, run uvicorn via Bash                 |
| **Pentest agents**| HTTP requests via curl (Bash), Read/Grep source files, inspect DB file |
| **Fix agents**    | Read pentest_report.md → Edit source files → Re-run curl tests         |

### Handoff Files

Each team produces a structured report consumed by the next team:

- `reports/build_report.md` — what was built, known deviations, file map
- `reports/pentest_report.md` — findings: vuln type, severity, PoC, location
- `reports/fix_report.md` — what was fixed, how, verification steps

---

*Vrei mai multe materiale ca acestea? Alătură-te comunității AI Wizard: [ai-wizard.tech/comunitate](https://ai-wizard.tech/comunitate)*
