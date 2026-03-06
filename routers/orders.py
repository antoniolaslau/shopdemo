"""
Order routes for ShopDemo.
Intentional vulnerabilities for demo/educational purposes:
- VULN:IDOR — GET /orders/{id} and GET /orders/{id}/confirm fetch order by ID only, no ownership check
- VULN:CSRF — POST /checkout does not validate CSRF token
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import CartItem, Order, OrderItem

router = APIRouter(prefix="", tags=["orders"])
templates = Jinja2Templates(directory="templates")


@router.get("/checkout")
async def checkout_page(request: Request, db: Session = Depends(get_db)):
    """Show checkout summary of current cart."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    total = sum(item.product.price * item.quantity for item in items)
    return templates.TemplateResponse(
        "orders/checkout.html",
        {"request": request, "items": items, "total": total},
    )


@router.post("/checkout")  # VULN:CSRF — no CSRF token validation
async def checkout_submit(request: Request, db: Session = Depends(get_db)):
    """Convert cart to an order and clear the cart."""
    # VULN:CSRF — form token not validated here
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    if not items:
        return RedirectResponse(url="/cart", status_code=303)

    total = sum(item.product.price * item.quantity for item in items)
    order = Order(user_id=user_id, status="pending", total=total)
    db.add(order)
    db.flush()

    for item in items:
        db.add(OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.product.price,
        ))
        db.delete(item)

    db.commit()
    return RedirectResponse(url="/orders", status_code=303)


@router.get("/orders")
async def orders_list(request: Request, db: Session = Depends(get_db)):
    """List all orders belonging to the current authenticated user."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    orders = (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "orders/list.html",
        {"request": request, "orders": orders},
    )


@router.get("/orders/{order_id}")
async def order_detail(request: Request, order_id: int, db: Session = Depends(get_db)):
    """View a single order's details."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden: you do not own this order.")

    return templates.TemplateResponse(
        "orders/detail.html",
        {"request": request, "order": order},
    )


@router.get("/orders/{order_id}/confirm")
async def order_confirm(request: Request, order_id: int, db: Session = Depends(get_db)):
    """Show order confirmation page."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden: you do not own this order.")

    return templates.TemplateResponse(
        "orders/confirm.html",
        {"request": request, "order": order},
    )
