"""
Category routes.

Routes are kept thin: they parse/validate input via schemas, call a service,
and serialize the result.  No business logic lives here.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app.schemas import category_schema, categories_schema
from app.services import category_service

bp = Blueprint("categories", __name__)


@bp.route("/", methods=["GET"])
@jwt_required()
def list_categories():
    cats = category_service.list_categories()
    return jsonify(categories_schema.dump(cats)), 200


@bp.route("/", methods=["POST"])
@jwt_required()
def create_category():
    data = category_schema.load(request.get_json(force=True) or {})
    cat = category_service.create_category(name=data["name"])
    return jsonify(category_schema.dump(cat)), 201


@bp.route("/<int:category_id>", methods=["DELETE"])
@jwt_required()
def delete_category(category_id: int):
    category_service.delete_category(category_id)
    return "", 204
