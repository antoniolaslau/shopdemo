from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from services import category_service

router = APIRouter(prefix="/categories", tags=["categories"])

templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def category_list(request: Request, db: Session = Depends(get_db)):
    categories = category_service.get_all_categories(db)
    return templates.TemplateResponse(
        "categories/index.html",
        {"request": request, "categories": categories, "page_title": "Browse by Category"},
    )


@router.get("/{slug}", response_class=HTMLResponse)
async def category_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    category = category_service.get_category_by_slug(db, slug)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    products = category_service.get_products_in_category(db, category.id)
    return templates.TemplateResponse(
        "categories/detail.html",
        {
            "request": request,
            "category": category,
            "products": products,
            "page_title": category.name,
        },
    )
