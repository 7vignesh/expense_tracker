"""
Health-check endpoint.

Used by load balancers and monitoring tools to verify the service is alive.
Returns DB connectivity status so operators can distinguish app crashes from
DB failures.
"""

from flask import Blueprint, jsonify

from app import db

bp = Blueprint("health", __name__)


@bp.route("/health", methods=["GET"])
def health():
    db_ok = True
    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception:
        db_ok = False

    status = "ok" if db_ok else "degraded"
    return jsonify({"status": status, "db": db_ok}), 200 if db_ok else 503
