"""
Auth routes — register and login.

POST /api/auth/register  →  201, { id, username, created_at }
POST /api/auth/login     →  200, { access_token }
"""

from flask import Blueprint, jsonify, request

from app.schemas import user_schema
from app.services import auth_service

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["POST"])
def register():
    data = user_schema.load(request.get_json(force=True) or {})
    user = auth_service.register_user(
        username=data["username"],
        password=data["password"],
    )
    return jsonify(user_schema.dump(user)), 201


@bp.route("/login", methods=["POST"])
def login():
    data = user_schema.load(request.get_json(force=True) or {})
    token = auth_service.login_user(
        username=data["username"],
        password=data["password"],
    )
    return jsonify({"access_token": token}), 200
