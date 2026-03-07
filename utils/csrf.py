"""
CSRF protection utilities for ShopDemo.

Implements the synchronizer token pattern:
- generate_csrf_token: create or retrieve a per-session token
- validate_csrf_token: constant-time comparison to prevent timing attacks
- verify_csrf_token: FastAPI dependency for POST endpoint protection
"""

import secrets

from fastapi import Depends, Form, HTTPException, Request

_SESSION_KEY = "csrf_token"


def generate_csrf_token(session: dict) -> str:
    """Return the session's CSRF token, creating one if absent.

    Tokens are per-session (not per-request) so multi-tab usage is not broken.
    The token is stored under the key 'csrf_token' in the Starlette session.
    """
    token = session.get(_SESSION_KEY)
    if not token:
        token = secrets.token_hex(32)
        session[_SESSION_KEY] = token
    return token


def validate_csrf_token(session: dict, submitted_token: str | None) -> None:
    """Validate the submitted token against the session token.

    Uses secrets.compare_digest for constant-time comparison to prevent
    timing side-channel attacks.

    Raises HTTPException(403) on mismatch or if either token is absent.
    """
    stored_token = session.get(_SESSION_KEY)
    if not stored_token or not submitted_token:
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    if not secrets.compare_digest(stored_token, submitted_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")


async def verify_csrf_token(
    request: Request,
    csrf_token: str | None = Form(default=None),
) -> None:
    """FastAPI dependency that validates the CSRF token on POST requests.

    Extract the 'csrf_token' field from submitted form data and compare it
    against the value stored in the session. Raises HTTP 403 on failure.
    """
    validate_csrf_token(request.session, csrf_token)
