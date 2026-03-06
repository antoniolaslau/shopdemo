from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from models import Product

router = APIRouter(prefix="", tags=["store"])

templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# Homepage — GET /
# ---------------------------------------------------------------------------

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def homepage(request: Request, db: Session = Depends(get_db)):
    """Show featured products on the homepage (up to 8 active products)."""
    products = db.query(Product).filter(Product.is_active == True).limit(8).all()
    return templates.TemplateResponse(
        "store/index.html",
        {
            "request": request,
            "products": products,
            "page_title": "Welcome to ShopDemo",
        },
    )


# ---------------------------------------------------------------------------
# Full catalog — GET /products
# ---------------------------------------------------------------------------

@router.get("/products", response_class=HTMLResponse)
async def catalog(
    request: Request,
    page: int = 1,
    per_page: int = 12,
    category: str = None,
    db: Session = Depends(get_db),
):
    """Paginated product catalog with optional category filter."""
    query = db.query(Product).filter(Product.is_active == True)

    # Category filter — stored as a prefix convention in product name for demo purposes
    if category:
        query = query.filter(Product.name.ilike(f"{category}%"))

    offset = (page - 1) * per_page
    products = query.offset(offset).limit(per_page).all()

    return templates.TemplateResponse(
        "store/catalog.html",
        {
            "request": request,
            "products": products,
            "page": page,
            "per_page": per_page,
            "category": category,
            "page_title": "All Products",
        },
    )


# ---------------------------------------------------------------------------
# Product detail — GET /product/{id}
# ---------------------------------------------------------------------------

@router.get("/product/{id}", response_class=HTMLResponse)
async def product_detail(id: int, request: Request, db: Session = Depends(get_db)):
    """Show detail page for a single product."""
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return templates.TemplateResponse(
        "store/detail.html",
        {
            "request": request,
            "product": product,
            "page_title": product.name,
        },
    )


# ---------------------------------------------------------------------------
# Search — GET /search   [INTENTIONAL VULNERABILITY — for security training]
# ---------------------------------------------------------------------------

@router.get("/search", response_class=HTMLResponse)
async def search(q: str = "", request: Request = None, db: Session = Depends(get_db)):
    """Search products by name or description.

    WARNING: This endpoint intentionally contains a SQL injection vulnerability
    for security-training purposes. Do NOT use this pattern in production code.
    """
    results = db.query(Product).filter(
        Product.name.ilike(f"%{q}%") | Product.description.ilike(f"%{q}%")
    ).all()

    return templates.TemplateResponse(
        "store/search.html",
        {
            "request": request,
            "results": results,
            "query": q,
            "page_title": f"Search: {q}",
        },
    )
