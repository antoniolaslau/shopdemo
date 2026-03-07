# Standard library
from typing import Optional

# Third-party
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

# Local
from auth import admin_required, require_admin
from database import get_db
from models import Order, Product, User

router = APIRouter(prefix="/admin", tags=["admin"])

templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# Dashboard — GET /admin/dashboard
# ---------------------------------------------------------------------------


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """Display the admin dashboard with high-level store statistics."""
    total_products = db.query(func.count(Product.id)).scalar() or 0
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_revenue = db.query(func.sum(Order.total_price)).scalar() or 0.0

    stats = {
        "total_products": total_products,
        "total_orders": total_orders,
        "total_users": total_users,
        "total_revenue": total_revenue,
    }

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "stats": stats,
            "current_user": current_user,
        },
    )


# Convenience redirect: GET /admin → GET /admin/dashboard
@router.get("", response_class=HTMLResponse, include_in_schema=False)
async def admin_root(
    request: Request,
    current_user: User = Depends(admin_required),
):
    """Redirect /admin to /admin/dashboard."""
    return RedirectResponse(url="/admin/dashboard", status_code=302)


# ---------------------------------------------------------------------------
# Products list + create — GET /admin/products
# ---------------------------------------------------------------------------


@router.get("/products", response_class=HTMLResponse)
async def products_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """List all products and display the create-product form."""
    products = db.query(Product).order_by(Product.id).all()
    return templates.TemplateResponse(
        "admin/products.html",
        {
            "request": request,
            "products": products,
            "current_user": current_user,
        },
    )


# ---------------------------------------------------------------------------
# Create product — POST /admin/products
# ---------------------------------------------------------------------------


@router.post("/products")
async def products_create(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    stock: int = Form(0),
):
    """Create a new product and persist it to the database."""
    product = Product(
        name=name,
        description=description,  # VULN:XSS — stored exactly as submitted, no sanitization
        price=price,
        stock=stock,
    )
    db.add(product)
    db.commit()
    return RedirectResponse(url="/admin/products", status_code=303)


# ---------------------------------------------------------------------------
# Delete product — POST /admin/products/delete/{id}
# VULN:BAC — no is_admin check, any authenticated user can delete products
# ---------------------------------------------------------------------------


@router.post("/products/delete/{product_id}")
async def products_delete(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a product by ID.

    Requires the requesting user to have is_admin=True in the database.
    Returns HTTP 403 Forbidden if the user is unauthenticated or not an admin.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return RedirectResponse(url="/admin/products", status_code=303)


# ---------------------------------------------------------------------------
# Orders list — GET /admin/orders
# ---------------------------------------------------------------------------


@router.get("/orders", response_class=HTMLResponse)
async def orders_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """List all orders joined with customer information."""
    orders = db.query(Order).order_by(Order.id.desc()).all()
    return templates.TemplateResponse(
        "admin/orders.html",
        {
            "request": request,
            "orders": orders,
            "current_user": current_user,
        },
    )
