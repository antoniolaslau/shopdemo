"""
Authentication router — handles login, registration, logout, and flash
management for ShopDemo.

Session keys (flat, matching base.html expectations):
    user_id  : int  — primary key of the authenticated user
    is_admin : bool — whether the user has admin privileges
    flash_message : str  — one-shot UI notification
    flash_type    : str  — Bootstrap alert variant (success, danger, info, …)
"""
from passlib.context import CryptContext
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import User

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _set_flash(request: Request, message: str, flash_type: str = "info") -> None:
    request.session["flash_message"] = message
    request.session["flash_type"] = flash_type


def _seed_demo_accounts(db: Session) -> None:
    """Create demo admin and regular user accounts if they don't already exist."""
    # Demo admin
    if not db.query(User).filter(User.email == "admin@shopdemo.com").first():
        admin = User(
            username="admin",
            email="admin@shopdemo.com",
            password_hash=_hash_password("admin123"),
            is_admin=True,
        )
        db.add(admin)

    # Demo regular user
    if not db.query(User).filter(User.email == "user@shopdemo.com").first():
        user = User(
            username="user",
            email="user@shopdemo.com",
            password_hash=_hash_password("user123"),
            is_admin=False,
        )
        db.add(user)

    db.commit()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request, db: Session = Depends(get_db)):
    """Render the login page; redirect home if already authenticated."""
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=302)
    _seed_demo_accounts(db)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None},
    )


@router.post("/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Validate credentials and create a session on success."""
    user = db.query(User).filter(User.email == email).first()

    if not user or not _verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid email or password. Please try again.",
            },
            status_code=401,
        )

    # Store flat session keys expected by base.html
    request.session["user_id"] = user.id
    request.session["is_admin"] = user.is_admin

    _set_flash(request, f"Welcome back, {user.username}!", "success")
    return RedirectResponse(url="/", status_code=303)


@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request, db: Session = Depends(get_db)):
    """Render the registration page; redirect home if already authenticated."""
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=302)
    _seed_demo_accounts(db)
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "error": None},
    )


@router.post("/register")
async def register_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Validate registration data, create user account, and auto-login."""
    # Password match check
    if password != confirm_password:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Passwords do not match."},
            status_code=422,
        )

    # Minimum password length
    if len(password) < 6:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Password must be at least 6 characters."},
            status_code=422,
        )

    # Duplicate email check
    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "An account with that email already exists."},
            status_code=409,
        )

    # Derive a username from the email local-part; ensure uniqueness
    base_username = email.split("@")[0][:50]
    username = base_username
    suffix = 1
    while db.query(User).filter(User.username == username).first():
        username = f"{base_username}{suffix}"
        suffix += 1

    new_user = User(
        username=username,
        email=email,
        password_hash=_hash_password(password),
        is_admin=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Auto-login after successful registration
    request.session["user_id"] = new_user.id
    request.session["is_admin"] = new_user.is_admin

    _set_flash(request, "Account created successfully. Welcome!", "success")
    return RedirectResponse(url="/", status_code=303)


@router.get("/logout")
async def logout(request: Request):
    """Clear the session and redirect to login."""
    request.session.clear()
    return RedirectResponse(url="/auth/login", status_code=302)


@router.post("/clear-flash")
async def clear_flash(request: Request):
    """Remove flash message from session after it has been displayed by base.html."""
    request.session.pop("flash_message", None)
    request.session.pop("flash_type", None)
    return {"ok": True}
