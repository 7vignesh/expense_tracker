"""
Marshmallow schemas — the single source of truth for what the API accepts
and returns.

Validation is kept here, not scattered across routes or services, so that
every entry point (HTTP, CLI, tests) enforces the same rules.

Amount handling:
  - Input:  decimal string / float from the client ("12.50")
  - Storage: integer cents (1250) in the DB via the service layer
  - Output: decimal string ("12.50") serialised by `amount` field below
"""

from __future__ import annotations

import math
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from marshmallow import (
    ValidationError,
    fields,
    post_load,
    pre_load,
    validate,
    validates,
    validates_schema,
)
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from app import ma
from app.models import Category, Expense


# ── helpers ───────────────────────────────────────────────────────────────────


def _to_cents(value: str | float | int) -> int:
    """Convert a client-supplied amount to integer cents.  Raises ValueError."""
    try:
        d = Decimal(str(value))
    except InvalidOperation:
        raise ValueError("Invalid decimal amount.")
    if d.as_tuple().exponent < -2:
        raise ValueError("Amount must have at most 2 decimal places.")
    return int(d * 100)


# ── Category ──────────────────────────────────────────────────────────────────


class CategorySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Category
        load_instance = False
        include_fk = True

    # Trim whitespace before validation
    @pre_load
    def strip_name(self, data: dict, **kwargs) -> dict:
        if isinstance(data.get("name"), str):
            data["name"] = data["name"].strip()
        return data

    @validates("name")
    def validate_name(self, value: str) -> None:
        if not value:
            raise ValidationError("Category name must not be empty.")
        if len(value) > 100:
            raise ValidationError("Category name must be 100 characters or fewer.")


# ── Expense ───────────────────────────────────────────────────────────────────


class ExpenseSchema(ma.Schema):
    """
    Custom (non-auto) schema so we can present `amount` as a human-readable
    decimal while storing cents internally.
    """

    id = fields.Int(dump_only=True)
    description = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    # Clients send a decimal string; we serialise back the same way
    amount = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=Decimal("0.01")),
    )
    date = fields.Date(required=True)
    category_id = fields.Int(required=True, load_only=True)
    # Read-only fields returned to the client
    category = fields.Nested(CategorySchema, dump_only=True, only=("id", "name"))
    created_at = fields.DateTime(dump_only=True)

    @pre_load
    def validate_amount_precision(self, data: dict, **kwargs) -> dict:
        """
        Reject amounts with more than 2 decimal places *before* Marshmallow
        quantizes the value (fields.Decimal with places=2 rounds on load,
        which would hide the error).
        """
        raw = data.get("amount")
        if raw is not None:
            try:
                d = Decimal(str(raw))
                if d.as_tuple().exponent < -2:
                    raise ValidationError(
                        {"amount": ["Amount must have at most 2 decimal places."]}
                    )
            except InvalidOperation:
                pass  # fields.Decimal will surface a better type error
        return data

    @validates("date")
    def date_not_future(self, value: date) -> None:
        if value > date.today():
            raise ValidationError("Expense date cannot be in the future.")

    @post_load
    def convert_amount_to_cents(self, data: dict, **kwargs) -> dict:
        """Replace decimal `amount` with `amount_cents` for the model layer."""
        raw = data.pop("amount")
        data["amount_cents"] = int(Decimal(str(raw)) * 100)
        return data


category_schema = CategorySchema()
categories_schema = CategorySchema(many=True)
expense_schema = ExpenseSchema()
expenses_schema = ExpenseSchema(many=True)
