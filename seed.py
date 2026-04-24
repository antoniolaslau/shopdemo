"""
seed.py — ShopDemo database seeder

Idempotent: checks for existing data before inserting.
Run from the project root with the project virtualenv active:

    python seed.py

Hashing: uses passlib bcrypt (same CryptContext as routers/auth.py).
On bcrypt >= 4.x, passlib's internal version detection emits a warning
but still works correctly; we suppress it here.
"""

import sys
import os
import warnings

# Suppress passlib's "error reading bcrypt version" warning caused by
# bcrypt >= 4.x dropping __about__; passlib still operates correctly.
warnings.filterwarnings("ignore", ".*error reading bcrypt version.*")

# Ensure the project root is on the path so database/models import cleanly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from passlib.context import CryptContext

from database import SessionLocal, engine
from models import Base, Category, Product, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

CATEGORIES = [
    {
        "name": "Laptops & Tablets",
        "slug": "laptops-tablets",
        "description": "Portable computers and tablets for work and creativity.",
    },
    {
        "name": "Audio",
        "slug": "audio",
        "description": "Headphones, earbuds, and speakers.",
    },
    {
        "name": "Monitors & Displays",
        "slug": "monitors-displays",
        "description": "Screens for your desktop setup.",
    },
    {
        "name": "Accessories",
        "slug": "accessories",
        "description": "Keyboards, mice, hubs, and other peripherals.",
    },
    {
        "name": "Storage",
        "slug": "storage",
        "description": "SSDs, hard drives, and memory cards.",
    },
    {
        "name": "Single-Board Computers",
        "slug": "single-board-computers",
        "description": "Raspberry Pi and similar embedded computing boards.",
    },
    {
        "name": "Streaming & Content Creation",
        "slug": "streaming-content-creation",
        "description": "Tools for streamers, podcasters, and creators.",
    },
]

USERS = [
    {
        "username": "admin",
        "email": "admin@shopdemo.com",
        "password": "admin123",
        "is_admin": True,
    },
    {
        "username": "user",
        "email": "user@shopdemo.com",
        "password": "user123",
        "is_admin": False,
    },
    {
        "username": "alice",
        "email": "alice@shopdemo.com",
        "password": "alice123",
        "is_admin": False,
    },
]

PRODUCTS = [
    {
        "name": 'MacBook Pro 14" M3',
        "description": (
            "Apple MacBook Pro with the M3 chip, 14-inch Liquid Retina XDR display, "
            "18 GB unified memory, 512 GB SSD. Extraordinary performance for pros."
        ),
        "price": 1999.99,
        "stock": 15,
        "image_url": "https://placehold.co/400x300?text=MacBook+Pro+14",
        "category_slug": "laptops-tablets",
    },
    {
        "name": "Sony WH-1000XM5 Headphones",
        "description": (
            "Industry-leading noise cancellation with 8 microphones and two processors. "
            "Up to 30 hours battery life. Crystal-clear hands-free calling."
        ),
        "price": 349.99,
        "stock": 42,
        "image_url": "https://placehold.co/400x300?text=Sony+WH-1000XM5",
        "category_slug": "audio",
    },
    {
        "name": 'Samsung 4K Monitor 27"',
        "description": (
            "27-inch UHD 4K (3840 x 2160) IPS panel, 60 Hz refresh rate, "
            "HDR10 support, USB-C and HDMI inputs, slim bezel design."
        ),
        "price": 449.99,
        "stock": 28,
        "image_url": "https://placehold.co/400x300?text=Samsung+4K+Monitor",
        "category_slug": "monitors-displays",
    },
    {
        "name": "Logitech MX Master 3S Mouse",
        "description": (
            "8000 DPI precision tracking on any surface including glass. "
            "MagSpeed electromagnetic scroll, USB-C charging, Bluetooth multi-device."
        ),
        "price": 99.99,
        "stock": 60,
        "image_url": "https://placehold.co/400x300?text=MX+Master+3S",
        "category_slug": "accessories",
    },
    {
        "name": "Keychron K2 Mechanical Keyboard",
        "description": (
            "75% compact layout with hot-swappable Gateron G Pro switches. "
            "RGB backlight, Bluetooth 5.1, compatible with Mac and Windows."
        ),
        "price": 89.99,
        "stock": 35,
        "image_url": "https://placehold.co/400x300?text=Keychron+K2",
        "category_slug": "accessories",
    },
    {
        "name": "Anker USB-C Hub 7-in-1",
        "description": (
            "7-in-1 hub with 4K HDMI, 100W Power Delivery, 5 Gbps USB-A x2, "
            "SD and microSD card readers, and USB-C data port."
        ),
        "price": 49.99,
        "stock": 80,
        "image_url": "https://placehold.co/400x300?text=Anker+USB-C+Hub",
        "category_slug": "accessories",
    },
    {
        "name": 'iPad Pro 12.9" M2',
        "description": (
            "Apple iPad Pro with M2 chip, stunning 12.9-inch Liquid Retina XDR display, "
            "Wi-Fi 6E, Apple Pencil hover support, USB 3 speed."
        ),
        "price": 1099.99,
        "stock": 20,
        "image_url": "https://placehold.co/400x300?text=iPad+Pro+12.9",
        "category_slug": "laptops-tablets",
    },
    {
        "name": "WD Black 2TB SSD",
        "description": (
            "NVMe PCIe Gen4 internal solid-state drive. Sequential read up to 7300 MB/s, "
            "write up to 6600 MB/s. Five-year limited warranty."
        ),
        "price": 179.99,
        "stock": 50,
        "image_url": "https://placehold.co/400x300?text=WD+Black+2TB+SSD",
        "category_slug": "storage",
    },
    {
        "name": "Elgato Stream Deck MK.2",
        "description": (
            "15 customisable LCD keys to launch unlimited actions. "
            "Interchangeable faceplates, USB connection, compatible with OBS, Twitch, and more."
        ),
        "price": 149.99,
        "stock": 25,
        "image_url": "https://placehold.co/400x300?text=Stream+Deck+MK.2",
        "category_slug": "streaming-content-creation",
    },
    {
        "name": "Raspberry Pi 5 (8 GB)",
        "description": (
            "The latest Raspberry Pi single-board computer with 8 GB LPDDR4X RAM, "
            "2.4 GHz quad-core Arm Cortex-A76 CPU, dual 4K display output, PCIe 2.0."
        ),
        "price": 80.00,
        "stock": 100,
        "image_url": "https://placehold.co/400x300?text=Raspberry+Pi+5",
        "category_slug": "single-board-computers",
    },
]


# ---------------------------------------------------------------------------
# Seeding logic
# ---------------------------------------------------------------------------

def seed_categories(db) -> tuple[int, int]:
    """Insert seed categories; returns (inserted, skipped) counts."""
    inserted = 0
    skipped = 0
    for c in CATEGORIES:
        existing = db.query(Category).filter(Category.slug == c["slug"]).first()
        if existing:
            skipped += 1
            continue
        category = Category(
            name=c["name"],
            slug=c["slug"],
            description=c["description"],
        )
        db.add(category)
        inserted += 1
    db.commit()
    return inserted, skipped


def seed_users(db) -> tuple[int, int]:
    """Insert seed users; returns (inserted, skipped) counts."""
    inserted = 0
    skipped = 0
    for u in USERS:
        existing = db.query(User).filter(User.email == u["email"]).first()
        if existing:
            skipped += 1
            continue
        user = User(
            username=u["username"],
            email=u["email"],
            password_hash=pwd_context.hash(u["password"]),
            is_admin=u["is_admin"],
        )
        db.add(user)
        inserted += 1
    db.commit()
    return inserted, skipped


def seed_products(db) -> tuple[int, int]:
    """Insert seed products; returns (inserted, skipped) counts."""
    inserted = 0
    skipped = 0
    category_map = {c.slug: c for c in db.query(Category).all()}
    for p in PRODUCTS:
        existing = db.query(Product).filter(Product.name == p["name"]).first()
        if existing:
            skipped += 1
            continue
        product = Product(
            name=p["name"],
            description=p["description"],
            price=p["price"],
            stock=p["stock"],
            image_url=p["image_url"],
            is_active=True,
            category_id=category_map[p["category_slug"]].id,
        )
        db.add(product)
        inserted += 1
    db.commit()
    return inserted, skipped


def main():
    print("ShopDemo — Database Seeder")
    print("=" * 40)

    # Create tables if they don't exist
    print("Creating database tables (if not already present)...")
    Base.metadata.create_all(bind=engine)
    print("  Tables ready.")

    db = SessionLocal()
    try:
        # Seed categories (must come before products)
        c_ins, c_skip = seed_categories(db)
        print(f"\nCategories:")
        print(f"  Inserted : {c_ins}")
        print(f"  Skipped  : {c_skip} (already exist)")
        for c in CATEGORIES:
            print(f"    [{c['slug']}]  {c['name']}")

        # Seed users
        u_ins, u_skip = seed_users(db)
        print(f"\nUsers:")
        print(f"  Inserted : {u_ins}")
        print(f"  Skipped  : {u_skip} (already exist)")
        for u in USERS:
            role = "admin" if u["is_admin"] else "user"
            print(f"    [{role:5s}] {u['email']}  /  {u['password']}")

        # Seed products
        p_ins, p_skip = seed_products(db)
        print(f"\nProducts:")
        print(f"  Inserted : {p_ins}")
        print(f"  Skipped  : {p_skip} (already exist)")
        for p in PRODUCTS:
            print(f"    ${p['price']:>8.2f}  [{p['category_slug']}]  {p['name']}")

    finally:
        db.close()

    print("\nSeeding complete.")


if __name__ == "__main__":
    main()
