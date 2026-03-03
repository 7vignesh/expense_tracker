"""
Centralised error handling.

All errors are returned as JSON with a consistent shape:
  { "error": "<human-readable message>" }

This makes it easy for clients to display messages and for tests to assert
on specific conditions without parsing HTML.
"""

from __future__ import annotations

import logging

from flask import Flask, jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Raised by service layer for domain violations."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, resource: str, id: int) -> None:
        super().__init__(f"{resource} with id={id} not found.", status_code=404)


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409)


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(exc: AppError):
        logger.warning("AppError: %s", exc.message)
        return jsonify({"error": exc.message}), exc.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(exc: ValidationError):
        # Flatten marshmallow messages to a single string for simplicity
        messages = exc.messages
        logger.warning("Validation error: %s", messages)
        return jsonify({"error": messages}), 422

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        return jsonify({"error": exc.description}), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        logger.exception("Unexpected error: %s", exc)
        return jsonify({"error": "An unexpected error occurred."}), 500
