"""
Expense service — all business logic for expenses lives here.

Expenses are user-scoped: every query and mutation requires a user_id so
one user can never see or modify another user's data.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app import db
from app.errors import ForbiddenError, NotFoundError
from app.models import Expense
from app.services.category_service import get_category


def list_expenses(
    user_id: int,
    category_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[Expense]:
    query = (
        Expense.query
        .filter(Expense.user_id == user_id)
        .order_by(Expense.date.desc(), Expense.id.desc())
    )
    if category_id is not None:
        query = query.filter(Expense.category_id == category_id)
    if date_from is not None:
        query = query.filter(Expense.date >= date_from)
    if date_to is not None:
        query = query.filter(Expense.date <= date_to)
    return query.all()


def get_expense(expense_id: int) -> Expense:
    exp = db.session.get(Expense, expense_id)
    if exp is None:
        raise NotFoundError("Expense", expense_id)
    return exp


def create_expense(
    description: str,
    amount_cents: int,
    date: date,
    category_id: int,
    user_id: int,
) -> Expense:
    # Verify the category exists (raises NotFoundError if not)
    get_category(category_id)
    exp = Expense(
        description=description,
        amount_cents=amount_cents,
        date=date,
        category_id=category_id,
        user_id=user_id,
    )
    db.session.add(exp)
    db.session.commit()
    return exp


def delete_expense(expense_id: int, user_id: int) -> None:
    exp = get_expense(expense_id)
    if exp.user_id != user_id:
        raise ForbiddenError("You can only delete your own expenses.")
    db.session.delete(exp)
    db.session.commit()


def get_summary(user_id: int) -> dict:
    """
    Return total spending and a per-category breakdown for a single user.
    All amounts are returned as decimal strings (dollars, 2 d.p.) so the
    client never has to know about cents.
    """
    expenses = Expense.query.filter(Expense.user_id == user_id).all()
    total_cents = sum(e.amount_cents for e in expenses)

    breakdown: dict[str, int] = {}
    for exp in expenses:
        cat_name = exp.category.name
        breakdown[cat_name] = breakdown.get(cat_name, 0) + exp.amount_cents

    return {
        "total": f"{total_cents / 100:.2f}",
        "by_category": {
            name: f"{cents / 100:.2f}" for name, cents in sorted(breakdown.items())
        },
    }

