# Claude Guidance — Expense Tracker

This file constrains how Claude (and other AI agents) should interact
with this codebase.  Follow these rules **strictly** — violating them
will cause subtle bugs, security regressions, or broken tests.

---

## Project Context

A small full-stack expense tracker:
- **Backend**: Python 3.12 + Flask + SQLAlchemy + Marshmallow (SQLite in dev)
- **Frontend**: React 18 + TypeScript (Vite)
- **Tests**: pytest

---

## Hard Rules (Never Break These)

### 1. Layer Boundaries
- Routes MUST NOT query the database directly.  All DB access goes through services.
- Services MUST NOT import anything from `app.routes`.
- Schemas are the only place validation logic lives.  Do not duplicate validation in routes or services.

### 2. Amount Handling
- Amounts are stored as **integer cents** (`amount_cents` column).
- The API accepts/returns decimal strings (`"12.50"`), never floats.
- Never store a float in the DB.  Never return a raw `amount_cents` integer to the client.
- The conversion happens in `ExpenseSchema.convert_amount_to_cents` (post_load).
  Do not move or duplicate this logic.

### 3. Date Rules
- Expense dates must not be in the future.  This rule is in `ExpenseSchema.date_not_future`.
- Do not relax this rule without updating the corresponding test.

### 4. No Orphaned Expenses
- Deleting a category that has expenses MUST return 409 Conflict.
- This is enforced in `category_service.delete_category`.  Never bypass it.

### 5. Error Responses
- All errors are returned as `{ "error": "<msg>" }` or `{ "error": { "field": [...] } }`.
- Never return plain text errors or HTML in API responses.
- HTTP status codes must match: 400 bad input, 404 not found, 409 conflict, 422 validation, 500 unexpected.

### 6. Tests
- Every new service function MUST have at least one positive test and one negative test.
- Never delete existing tests to make new tests pass.
- Use the `client` fixture (see `tests/conftest.py`) — never create a new fixture that bypasses DB teardown.

---

## What You Should Do

- Extend functionality by adding new service functions + new route handlers + new schema fields.
- Add new tests in the same file as the feature under test.
- Keep functions short (< 30 lines ideally).
- Prefer explicit over implicit.  No magic.

## What You Should NOT Do

- Do NOT add business logic to route handlers.
- Do NOT add new ORM models without a corresponding schema.
- Do NOT change `amount_cents` to float or Decimal in the model.
- Do NOT use `db.session.execute(raw_sql)` except in the health check.
- Do NOT add dependencies to `requirements.txt` without explaining why in the PR description.
- Do NOT use `*` imports.
- Do NOT catch bare `except Exception` in service code — let errors bubble to the registered handlers.

---

## File Ownership Map

| File | Purpose | Who changes it |
|---|---|---|
| `app/models.py` | DB schema | Only when adding/removing DB columns |
| `app/schemas.py` | Validation + serialization | When input/output contract changes |
| `app/services/` | Business logic | Primary target for new features |
| `app/routes/` | HTTP wiring | Thin; change only when adding/removing endpoints |
| `app/errors.py` | Error handling | When adding new error types |
| `tests/` | Tests | Alongside every feature change |

---

## Naming Conventions

- Services: `verb_noun` e.g. `create_expense`, `get_category`
- Schemas: `<Model>Schema`, instances `<model>_schema` / `<model>s_schema`
- Routes: Blueprint named after the resource e.g. `bp = Blueprint("expenses", __name__)`
- Tests: `test_<what>_<condition>` e.g. `test_create_expense_future_date_rejected`

---

## Checklist Before Submitting AI-Generated Code

- [ ] Tests pass (`cd backend && pytest`)
- [ ] No validation logic added to routes
- [ ] No raw DB queries added to routes
- [ ] Amount handling uses cents — not floats
- [ ] Error responses match the `{ "error": ... }` shape
- [ ] No new `except Exception` bare catches in services
