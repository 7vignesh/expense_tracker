"""
Domain models.

Design choices:
- `amount` stored as INTEGER cents to avoid floating-point drift.
  The API accepts/returns a decimal string (e.g. "12.50") but persistence
  is always an integer (1250).  This prevents rounding disagreements between
  client and server.
- `date` is a plain DATE column (no time component) because expenses belong
  to a calendar day, not an instant.
- Category name has a unique constraint enforced at the DB level *and*
  validated at the service level, giving a friendly error before any DB round-trip.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class User(db.Model):
    """
    Application user.  Passwords are stored as bcrypt hashes via werkzeug
    (already a Flask dependency — no extra package required).
    The plaintext password is never persisted.
    """

    __tablename__ = "users"

    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(80), nullable=False, unique=True)
    password_hash: str = db.Column(db.String(256), nullable=False)
    created_at: datetime = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    expenses = db.relationship("Expense", back_populates="owner", lazy="dynamic")

    def set_password(self, plaintext: str) -> None:
        self.password_hash = generate_password_hash(plaintext)

    def check_password(self, plaintext: str) -> bool:
        return check_password_hash(self.password_hash, plaintext)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} username={self.username!r}>"


class Category(db.Model):
    __tablename__ = "categories"

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False, unique=True)
    created_at: datetime = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    expenses = db.relationship(
        "Expense", back_populates="category", lazy="dynamic"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Category id={self.id} name={self.name!r}>"


class Expense(db.Model):
    __tablename__ = "expenses"

    id: int = db.Column(db.Integer, primary_key=True)
    description: str = db.Column(db.String(255), nullable=False)
    # Stored in cents (integer).  e.g. $12.50 → 1250
    amount_cents: int = db.Column(db.Integer, nullable=False)
    date: date = db.Column(db.Date, nullable=False)
    category_id: int = db.Column(
        db.Integer, db.ForeignKey("categories.id"), nullable=False
    )
    # Every expense is owned by exactly one user
    user_id: int = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    created_at: datetime = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    category = db.relationship("Category", back_populates="expenses")
    owner = db.relationship("User", back_populates="expenses")

    @property
    def amount(self) -> "Decimal":
        """Convenience property so schemas can read amount as Decimal."""
        from decimal import Decimal
        return Decimal(self.amount_cents) / Decimal(100)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Expense id={self.id} amount_cents={self.amount_cents}>"
