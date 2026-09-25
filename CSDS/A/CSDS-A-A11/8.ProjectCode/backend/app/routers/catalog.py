"""Catalogue browsing: categories, product list, product detail, reviews."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Product, Review
from ..recommender.orchestrator import orchestrator
from ..schemas import (
    CategoryOut,
    ProductDetailOut,
    ProductListOut,
    ReviewListOut,
)

router = APIRouter(tags=["catalog"])

SORTS = {
    "relevance": (Product.review_count.desc(), Product.rating.desc()),
    "newest": (Product.created_at.desc(),),
    "price_asc": (Product.price.asc(),),
    "price_desc": (Product.price.desc(),),
    "rating": (Product.rating.desc(), Product.review_count.desc()),
    "popular": (Product.review_count.desc(),),
}


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Product.category, func.count(Product.id)).group_by(Product.category).order_by(Product.category)
    ).all()
    return [
        CategoryOut(id=_slugify(name), name=name, slug=_slugify(name), product_count=count)
        for name, count in rows
    ]


@router.get("/products", response_model=ProductListOut)
def list_products(
    category: str | None = None,
    q: str | None = None,
    sort: str = "relevance",
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(Product)

    if category:
        # Accept either the display name or the slug the category list returns.
        names = {p["category"] for p in orchestrator.products} or set()
        match = next((n for n in names if _slugify(n) == _slugify(category)), category)
        stmt = stmt.where(Product.category == match)

    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Product.name.ilike(pattern),
                Product.short_description.ilike(pattern),
                Product.description.ilike(pattern),
                Product.subcategory.ilike(pattern),
                Product.category.ilike(pattern),
            )
        )

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

    for clause in SORTS.get(sort, SORTS["relevance"]):
        stmt = stmt.order_by(clause)

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    items = db.execute(stmt).scalars().all()

    return ProductListOut(items=items, total=total, page=page, page_size=page_size)


def _resolve(db: Session, product_id: str) -> Product:
    product = None
    if product_id.isdigit():
        product = db.get(Product, int(product_id))
    if product is None:
        product = db.execute(select(Product).where(Product.slug == product_id)).scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail=f"No product matching '{product_id}'")
    return product


@router.get("/products/{product_id}", response_model=ProductDetailOut)
def get_product(product_id: str, db: Session = Depends(get_db)):
    product = _resolve(db, product_id)

    related_ids: list[int] = []
    idx = orchestrator.index_by_id.get(product.id)
    if idx is not None and orchestrator.content is not None:
        import numpy as np

        neighbours = np.argsort(-orchestrator.content.item_sim[idx])[:8]
        related_ids = [orchestrator.products[int(i)]["id"] for i in neighbours]

    payload = ProductDetailOut.model_validate(product, from_attributes=True)
    payload.related_ids = related_ids
    return payload


@router.get("/products/{product_id}/reviews", response_model=ReviewListOut)
def get_reviews(
    product_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    product = _resolve(db, product_id)
    base = select(Review).where(Review.product_id == product.id)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
    items = (
        db.execute(
            base.order_by(Review.helpful_count.desc(), Review.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    return ReviewListOut(items=items, total=total, page=page, page_size=page_size)
