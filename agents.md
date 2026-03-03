# AI Agents Guide — Expense Tracker

Use this file when directing any AI coding agent (GPT, Claude, Gemini, Copilot, etc.)
to work on this project.

---

## Project Summary

A small expense-tracking web app.  Users can:
1. Create/delete spending categories (Food, Transport, etc.)
2. Log expenses (description, amount, date, category)
3. Filter expenses by category or date range
4. View a spending summary by category

**Backend**: Flask REST API (`backend/`) — Python 3.12  
**Frontend**: React + TypeScript (`frontend/`)  
**DB**: SQLite in dev (swap DATABASE_URL for Postgres in prod)

---

## Agent Workflow (Must Follow)

```
1. Read claude.md (the hard rules)
2. Read the relevant service file before changing it
3. Write / update the code
4. Write / update tests
5. Run: cd backend && pytest
6. Only if tests pass: report done
```

Never report done before seeing green tests.

---

## How to Run

```bash
# Backend
cd backend
pip install -r requirements.txt
python run.py          # → http://localhost:5000

# Frontend
cd frontend
npm install
npm run dev            # → http://localhost:3000

# Tests
cd backend
pytest                 # run all tests
pytest -v -k "expense" # run specific tests
```

---

## Adding a New Feature: Example

**Request**: "Add a monthly budget per category"

**Steps the agent should take**:

1. **Model**: Add `budget_cents` column (nullable Integer) to `Category`.
2. **Schema**: Add `budget` decimal field to `CategorySchema` (optional, nullable).
3. **Service**: Update `create_category` to accept optional `budget_cents`.
   Add `get_budget_status(category_id)` service function.
4. **Route**: `GET /api/categories/<id>/budget` endpoint.
5. **Tests**:
   - `test_create_category_with_budget`
   - `test_budget_status_over_limit`
   - `test_budget_status_under_limit`
   - `test_budget_not_required`

**What NOT to do**:
- Don't add budget calculation logic in the route.
- Don't return `budget_cents` raw — convert to decimal string.

---

## Prohibited Patterns

The agent must never generate code that:

```python
# ❌ Business logic in a route
@bp.route("/", methods=["POST"])
def create():
    data = request.get_json()
    if data["amount"] <= 0:   # ← validation belongs in the schema
        return {"error": "bad"}, 400

# ❌ Raw DB query in a route
@bp.route("/", methods=["GET"])
def list_exp():
    exps = db.session.execute("SELECT * FROM expenses").fetchall()  # ← use service

# ❌ Float for money
expense.amount = 12.50   # ← always integer cents

# ❌ Bare except in service
def create_expense(...):
    try:
        ...
    except Exception:     # ← let it bubble; the error handler catches it
        pass
```

---

## Approved Patterns

```python
# ✅ Thin route
@bp.route("/", methods=["POST"])
def create_expense():
    data = expense_schema.load(request.get_json(force=True) or {})
    exp = expense_service.create_expense(**data)
    return jsonify(expense_schema.dump(exp)), 201

# ✅ Validation in schema
@validates("amount")
def validate_amount(self, value):
    if value <= 0:
        raise ValidationError("Amount must be positive.")

# ✅ Money as cents
expense.amount_cents = int(Decimal(str(amount)) * 100)
```

---

## Test Coverage Expectations

| Layer | Coverage Goal |
|---|---|
| Schema validation | All edge cases (empty, out-of-range, wrong types) |
| Service business rules | Happy path + each error branch |
| Route HTTP wiring | At least one integration test per endpoint |

---

## Risk Register (Known Weaknesses)

| Risk | Mitigation |
|---|---|
| SQLite doesn't enforce FK constraints by default | `PRAGMA foreign_keys = ON` in prod; tests catch the service-level guard |
| No auth layer | Acceptable for this scope; add JWT middleware before any multi-user deploy |
| AI may add logic to routes | `claude.md` rule #1 + code review |
| AI may use floats for money | `claude.md` rule #2 + test `test_amount_stored_as_exact_decimal` |
