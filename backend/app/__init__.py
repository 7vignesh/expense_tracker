"""
App factory.  Creates and wires together Flask, SQLAlchemy, and Marshmallow.
Using the factory pattern keeps test setup isolated from production setup.
"""

from __future__ import annotations

import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
ma = Marshmallow()
jwt = JWTManager()

logger = logging.getLogger(__name__)


def create_app(config_override: object | None = None) -> Flask:
    app = Flask(__name__)

    # ── Config ────────────────────────────────────────────────────────────────
    from config import get_config

    app.config.from_object(get_config())
    if config_override:
        app.config.from_object(config_override)

    # ── Extensions ────────────────────────────────────────────────────────────
    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ── Logging ───────────────────────────────────────────────────────────────
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # ── Blueprints ────────────────────────────────────────────────────────────
    from app.routes.auth import bp as auth_bp
    from app.routes.categories import bp as categories_bp
    from app.routes.expenses import bp as expenses_bp
    from app.routes.health import bp as health_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(categories_bp, url_prefix="/api/categories")
    app.register_blueprint(expenses_bp, url_prefix="/api/expenses")

    # ── Error handlers ────────────────────────────────────────────────────────
    from app.errors import register_error_handlers

    register_error_handlers(app)

    # ── DB bootstrap ──────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        logger.info("Database tables ensured.")

    return app
