"""
Expense routes.

Query-string filters are parsed and validated here before being forwarded
to the service layer.  All routes require a valid JWT; the user's identity
is extracted from the token and passed to the service layer rather than
being trusted from user-controlled input.
"""

from datetime import date

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
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
@jwt_required()
def list_expenses():
    user_id = int(get_jwt_identity())
    category_id_raw = request.args.get("category_id")
    category_id = int(category_id_raw) if category_id_raw else None
    date_from = _parse_date("date_from", "date_from")
    date_to = _parse_date("date_to", "date_to")

    if date_from and date_to and date_from > date_to:
        raise AppError("'date_from' must be on or before 'date_to'.")

    exps = expense_service.list_expenses(
        user_id=user_id, category_id=category_id, date_from=date_from, date_to=date_to
    )
    return jsonify(expenses_schema.dump(exps)), 200


@bp.route("/", methods=["POST"])
@jwt_required()
def create_expense():
    user_id = int(get_jwt_identity())
    data = expense_schema.load(request.get_json(force=True) or {})
    exp = expense_service.create_expense(
        description=data["description"],
        amount_cents=data["amount_cents"],
        date=data["date"],
        category_id=data["category_id"],
        user_id=user_id,
    )
    # Re-fetch to include the nested category data in the response
    from app.services.expense_service import get_expense

    exp = get_expense(exp.id)
    return jsonify(expense_schema.dump(exp)), 201


@bp.route("/summary", methods=["GET"])
@jwt_required()
def get_summary():
    user_id = int(get_jwt_identity())
    return jsonify(expense_service.get_summary(user_id=user_id)), 200


@bp.route("/<int:expense_id>", methods=["DELETE"])
@jwt_required()
def delete_expense(expense_id: int):
    user_id = int(get_jwt_identity())
    expense_service.delete_expense(expense_id, user_id=user_id)
    return "", 204
