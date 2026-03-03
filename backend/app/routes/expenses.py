"""
Expense routes.

Query-string filters are parsed and validated here before being forwarded
to the service layer.
"""

from datetime import date

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError, fields

from app.errors import AppError
from app.schemas import expense_schema, expenses_schema
from app.services import expense_service

bp = Blueprint("expenses", __name__)


def _parse_date(param: str, name: str) -> date | None:
    raw = request.args.get(param)
    if raw is None:
        return None
    try:
        return fields.Date().deserialize(raw)
    except Exception:
        raise AppError(f"Query param '{name}' must be a valid ISO date (YYYY-MM-DD).")


@bp.route("/", methods=["GET"])
def list_expenses():
    category_id_raw = request.args.get("category_id")
    category_id = int(category_id_raw) if category_id_raw else None
    date_from = _parse_date("date_from", "date_from")
    date_to = _parse_date("date_to", "date_to")

    if date_from and date_to and date_from > date_to:
        raise AppError("'date_from' must be on or before 'date_to'.")

    exps = expense_service.list_expenses(
        category_id=category_id, date_from=date_from, date_to=date_to
    )
    return jsonify(expenses_schema.dump(exps)), 200


@bp.route("/", methods=["POST"])
def create_expense():
    data = expense_schema.load(request.get_json(force=True) or {})
    exp = expense_service.create_expense(
        description=data["description"],
        amount_cents=data["amount_cents"],
        date=data["date"],
        category_id=data["category_id"],
    )
    # Re-fetch to include the nested category data in the response
    from app.services.expense_service import get_expense

    exp = get_expense(exp.id)
    return jsonify(expense_schema.dump(exp)), 201


@bp.route("/summary", methods=["GET"])
def get_summary():
    return jsonify(expense_service.get_summary()), 200


@bp.route("/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id: int):
    expense_service.delete_expense(expense_id)
    return "", 204
