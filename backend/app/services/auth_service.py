"""
Authentication service.

Responsible for registering users and issuing JWT tokens.
Password hashing is handled here via werkzeug (already a Flask dependency).
Token creation is delegated to Flask-JWT-Extended so the signing logic is
not hand-rolled.
"""

from __future__ import annotations

from flask_jwt_extended import create_access_token

from app import db
from app.errors import AppError, ConflictError
from app.models import User


def register_user(username: str, password: str) -> User:
    if User.query.filter_by(username=username).first():
        raise ConflictError(f"Username '{username}' is already taken.")
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def login_user(username: str, password: str) -> str:
    """Return a signed JWT access token, or raise AppError on bad credentials."""
    user = User.query.filter_by(username=username).first()
    # Intentionally vague error message — do not reveal whether the username exists
    if user is None or not user.check_password(password):
        raise AppError("Invalid username or password.", status_code=401)
    # identity is the user id (int); str conversion required by Flask-JWT-Extended 4.x
    return create_access_token(identity=str(user.id))
