import logging

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from database import create_tables

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(title="ShopDemo", version="1.0.0")

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

# IMPORTANT: Change the secret_key value before deploying to production.
app.add_middleware(
    SessionMiddleware,
    secret_key="shopdemo-secret-key-change-in-production",
    max_age=3600,
)

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------------------------------------------------------------
# Router mounts (uncomment as each router module is implemented)
# ---------------------------------------------------------------------------

from routers.admin import router as admin_router
from routers.auth import router as auth_router
from routers.cart import router as cart_router
from routers.categories import router as categories_router
from routers.orders import router as orders_router
from routers.store import router as store_router

app.include_router(auth_router)
app.include_router(store_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(admin_router)
app.include_router(categories_router)

# ---------------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------------

logger = logging.getLogger("shopdemo")


@app.on_event("startup")
async def on_startup() -> None:
    create_tables()
    logger.info("ShopDemo started successfully")


# ---------------------------------------------------------------------------
# Root route
# ---------------------------------------------------------------------------


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redirect the root URL to the products listing page."""
    return RedirectResponse(url="/products", status_code=302)
