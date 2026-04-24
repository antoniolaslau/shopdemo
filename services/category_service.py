from sqlalchemy.orm import Session

from models import Category, Product


def get_all_categories(db: Session) -> list[Category]:
    return db.query(Category).order_by(Category.name).all()


def get_category_by_slug(db: Session, slug: str) -> Category | None:
    return db.query(Category).filter(Category.slug == slug).first()


def get_category_by_id(db: Session, category_id: int) -> Category | None:
    return db.query(Category).filter(Category.id == category_id).first()


def get_products_in_category(db: Session, category_id: int) -> list[Product]:
    return (
        db.query(Product)
        .filter(Product.category_id == category_id, Product.is_active == True)  # noqa: E712
        .order_by(Product.name)
        .all()
    )


def create_category(db: Session, name: str, slug: str, description: str = "") -> Category:
    category = Category(name=name, slug=slug, description=description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> bool:
    category = get_category_by_id(db, category_id)
    if not category:
        return False
    db.delete(category)
    db.commit()
    return True


def slug_is_taken(db: Session, slug: str, exclude_id: int | None = None) -> bool:
    query = db.query(Category).filter(Category.slug == slug)
    if exclude_id is not None:
        query = query.filter(Category.id != exclude_id)
    return query.first() is not None
