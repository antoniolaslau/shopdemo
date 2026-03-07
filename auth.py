import hashlib
from typing import Optional

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from models import User


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 and return the hex digest."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_current_user(request: Request, db: Session) -> Optional[User]:
    """Read user_id from session and return the corresponding User or None."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    return user


def login_required(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency that enforces authentication.

    Redirects to /auth/login if no authenticated user is found.
    """
    user = get_current_user(request, db)
    if not user:
        response = RedirectResponse(url="/auth/login", status_code=302)
        # Raise an HTTPException-compatible response by returning a redirect.
        # FastAPI dependencies can return RedirectResponse directly.
        raise Exception(response)
    return user


def admin_required(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency that enforces admin-level authentication.

    Redirects to / if no authenticated admin user is found.
    """
    user = get_current_user(request, db)
    if not user or not user.is_admin:
        response = RedirectResponse(url="/", status_code=302)
        raise Exception(response)
    return user


def require_admin(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency that enforces admin-level authorization.

    Returns HTTP 403 Forbidden (not a redirect) if the requesting user is
    not authenticated or does not have is_admin=True in the database.
    This is the correct authorization check for state-changing admin routes.
    """
    from fastapi import HTTPException

    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    return user
