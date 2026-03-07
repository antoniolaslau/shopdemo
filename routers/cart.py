"""
Cart routes for ShopDemo.
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import CartItem, Product
from utils.csrf import generate_csrf_token, verify_csrf_token

router = APIRouter(prefix="", tags=["cart"])
templates = Jinja2Templates(directory="templates")


@router.get("/cart")
async def cart_page(request: Request, db: Session = Depends(get_db)):
    """Display the current user's cart."""
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    items = (
        db.query(CartItem)
        .filter(CartItem.user_id == user["id"])
        .all()
    )
    total = sum(item.product.price * item.quantity for item in items)
    csrf_token = generate_csrf_token(request.session)
    return templates.TemplateResponse(
        "cart/index.html",
        {"request": request, "items": items, "total": total, "csrf_token": csrf_token},
    )


@router.post("/cart/add", dependencies=[Depends(verify_csrf_token)])
async def cart_add(
    request: Request,
    product_id: int = Form(...),
    quantity: int = Form(1),
    db: Session = Depends(get_db),
):
    """Add a product to the cart. Upserts if item already exists."""
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse(url="/", status_code=303)

    existing = (
        db.query(CartItem)
        .filter(CartItem.user_id == user["id"], CartItem.product_id == product_id)
        .first()
    )
    if existing:
        existing.quantity += quantity
    else:
        db.add(CartItem(user_id=user["id"], product_id=product_id, quantity=quantity))
    db.commit()
    return RedirectResponse(url="/cart", status_code=303)


@router.post("/cart/remove", dependencies=[Depends(verify_csrf_token)])
async def cart_remove(
    request: Request,
    cart_item_id: int = Form(...),
    db: Session = Depends(get_db),
):
    """Remove an item from the cart."""
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    item = (
        db.query(CartItem)
        .filter(CartItem.id == cart_item_id, CartItem.user_id == user["id"])
        .first()
    )
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(url="/cart", status_code=303)
