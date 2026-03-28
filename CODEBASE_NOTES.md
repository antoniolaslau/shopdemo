# ShopDemo — Codebase Notes

## 1. FastAPI — the web framework

FastAPI is a Python web framework. The core idea: you define Python functions and decorate them with HTTP methods + paths.

```python
@router.get("/products")          # GET /products
async def catalog(request: Request, db: Session = Depends(get_db)):
    ...
```

**The key concepts:**

**`async def`** — FastAPI is async-native. Most route handlers are `async` which means they don't block while waiting for I/O (DB queries, etc.). You can also write normal `def` functions and FastAPI handles the threading.

**`Depends()`** — FastAPI's dependency injection system. Instead of calling `get_db()` manually in every function, you declare it as a dependency and FastAPI injects it automatically. This is used for:
- `db: Session = Depends(get_db)` — injects a database session
- `current_user: User = Depends(admin_required)` — injects the current user after checking they're an admin
- `dependencies=[Depends(verify_csrf_token)]` — runs a check before the handler, no return value needed

**`APIRouter`** — Like a blueprint/module for routes. Each file in `routers/` creates its own router with a prefix, then `main.py` mounts them all with `app.include_router(...)`. This keeps the code organized.

**`Form(...)`** — When a browser submits an HTML form (POST), the data comes as form-encoded data, not JSON. `Form(...)` tells FastAPI to read the field from the form body. The `...` means required.

**`HTTPException`** — The standard way to return error responses. `raise HTTPException(status_code=403, detail="Forbidden")` immediately returns a 403 response.

**`RedirectResponse`** — Returns an HTTP redirect. Status 302 = GET redirect, 303 = redirect after POST (POST → redirect → GET pattern, prevents double-submit on refresh).

---

## 2. SQLAlchemy — the database ORM

SQLAlchemy maps Python classes to database tables. You never write raw SQL (except when you intentionally introduced the SQLi vuln).

**`models.py`** defines the tables:
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True)
    is_admin = Column(Boolean, default=False)
    orders = relationship("Order", back_populates="user")  # JOIN shortcut
```

**`database.py`** creates the engine and session factory:
```python
engine = create_engine("sqlite:///./shopdemo.db")   # creates shopdemo.db file
SessionLocal = sessionmaker(bind=engine)             # session factory
```

**`get_db()`** is a generator that creates a session, yields it to your route handler, then closes it — even if an exception occurs:
```python
def get_db():
    db = SessionLocal()
    try:
        yield db       # route handler runs here
    finally:
        db.close()     # always runs, even on error
```

**Querying pattern** you'll see everywhere:
```python
# SELECT * FROM users WHERE email = ? LIMIT 1
user = db.query(User).filter(User.email == email).first()

# SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC
orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()

# INSERT
db.add(new_user)
db.commit()

# DELETE
db.delete(item)
db.commit()
```

**`relationship()`** sets up JOINs transparently. When you access `order.user`, SQLAlchemy automatically fetches the related User. `cascade="all, delete-orphan"` means deleting an Order also deletes its OrderItems.

---

## 3. Jinja2 — the templating engine

Templates live in `templates/`. Routes pass data to them via a context dict:

```python
return templates.TemplateResponse(
    "store/catalog.html",
    {"request": request, "products": products, "page_title": "All Products"}
)
```

In the template you use `{{ variable }}` to output values (auto-escaped by default — this is how XSS was fixed, by removing `| safe`), and `{% for %}` / `{% if %}` for logic.

The `request` object is always required in the context because Starlette needs it.

---

## 4. Sessions (Starlette middleware)

Sessions are signed cookies. `SessionMiddleware` in `main.py` handles this. The session is a dict stored in the cookie, signed with the `secret_key` so it can't be tampered with by the client.

```python
request.session["user_id"] = user.id    # write
user_id = request.session.get("user_id")  # read
request.session.clear()                  # logout
```

This is server-stateless (no DB lookup per request for auth) — the session is decoded from the cookie on every request.

---

## 5. The auth system in `auth.py`

There are **three auth functions** used as dependencies, and they're subtly different:

| Function | How it guards | What it does on failure |
|---|---|---|
| `get_current_user()` | Helper, not a dependency | Returns `None` |
| `login_required()` | Any logged-in user | Redirects to `/auth/login` |
| `admin_required()` | Admin only | Redirects to `/` |
| `require_admin()` | Admin only | Returns **HTTP 403** |

`require_admin` vs `admin_required` — `require_admin` raises a proper `HTTPException(403)` while `admin_required` raises a redirect wrapped in a generic `Exception`. The 403 approach is correct for API-like endpoints where curl/automated tools are used (the BAC fix). The redirect approach is fine for browser navigation.

**Password hashing:** `routers/auth.py` uses `passlib` with `bcrypt` (correct). The `auth.py` helper (`hash_password`) uses plain `SHA-256` with no salt — that's the known weakness, but it's not actually called anywhere in the current codebase (the router has its own `_hash_password`).

---

## 6. CSRF protection (`utils/csrf.py`)

The **synchronizer token pattern**:
1. When rendering a form, generate a random token and store it in the session: `generate_csrf_token(request.session)`
2. Embed the token as a hidden field in the HTML form
3. On POST, the `verify_csrf_token` dependency reads the submitted token and compares it to the session's token using `secrets.compare_digest` (constant-time, prevents timing attacks)

A cross-site attacker can't forge the token because they can't read the victim's session cookie.

---

## 7. The vulnerability map (what changed between `vulnerable` and `main`)

| Vuln | Where | The bad code | The fix |
|---|---|---|---|
| **SQLi** | `store.py /search` | Raw f-string in `text()` query | SQLAlchemy ORM `.ilike()` — parameterized automatically |
| **XSS** | `admin/products.html` template | `{{ description \| safe }}` | Remove `\| safe` — Jinja2 auto-escapes by default |
| **BAC** | `admin.py /products/delete/{id}` | No auth check | `Depends(require_admin)` |
| **CSRF** | `cart.py`, `orders.py` POST routes | No token check | `dependencies=[Depends(verify_csrf_token)]` |
| **IDOR** | `orders.py /orders/{id}` | Fetches order by ID, no ownership check | `if order.user_id != user_id: raise HTTPException(403)` |

---

## 8. Known inconsistency

`cart.py` reads the session as `request.session.get("user")` (a dict `{"id": ...}`), but the rest of the app stores `request.session["user_id"]` (an integer). The cart routes would break at runtime. The correct pattern used everywhere else is `request.session.get("user_id")`.
