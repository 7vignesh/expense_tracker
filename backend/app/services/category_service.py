"""
Category service — all business logic for categories lives here.

Services are the only place that talks to the DB (via SQLAlchemy).
Routes call services; routes do NOT query the DB directly.
This keeps routes thin and makes business logic easy to test in isolation.
"""

from __future__ import annotations

from app import db
from app.errors import ConflictError, NotFoundError
from app.models import Category


def list_categories() -> list[Category]:
    return Category.query.order_by(Category.name).all()


def get_category(category_id: int) -> Category:
    cat = db.session.get(Category, category_id)
    if cat is None:
        raise NotFoundError("Category", category_id)
    return cat


def create_category(name: str) -> Category:
    name = name.strip()
    if Category.query.filter_by(name=name).first():
        raise ConflictError(f"Category '{name}' already exists.")
    cat = Category(name=name)
    db.session.add(cat)
    db.session.commit()
    return cat


def delete_category(category_id: int) -> None:
    cat = get_category(category_id)
    if cat.expenses.count() > 0:
        raise ConflictError(
            f"Cannot delete category '{cat.name}' — it has existing expenses."
        )
    db.session.delete(cat)
    db.session.commit()
