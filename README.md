# Expense Tracker

A small full-stack expense-tracking application built to demonstrate
structure, validation, testability, and resilience to change — not feature count.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript (Vite) |
| Backend | Python 3.12 + Flask |
| Database | SQLite (dev) / any SQLAlchemy-compatible DB (prod) |
| Validation | Marshmallow (backend), TypeScript strict mode (frontend) |
| Tests | pytest + pytest-flask |

---

## Running Locally

### Backend

```bash
cd backend
pip install -r requirements.txt
python run.py
# API available at http://localhost:5000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# UI available at http://localhost:3000
```

The Vite dev server proxies `/api/*` to `localhost:5000`, so no CORS
config or hard-coded URLs are needed in the frontend.

### Tests

```bash
cd backend
pytest            # all tests
pytest -v         # verbose
pytest -k expense # filter by name
```

---

## Architecture

```
backend/
├── app/
│   ├── __init__.py        # App factory (Flask + SQLAlchemy + Marshmallow)
│   ├── models.py          # SQLAlchemy models (Category, Expense)
│   ├── schemas.py         # Marshmallow schemas — validation + serialization
│   ├── errors.py          # Centralised error types + handlers
│   ├── routes/
│   │   ├── categories.py  # /api/categories endpoints
│   │   ├── expenses.py    # /api/expenses endpoints
│   │   └── health.py      # /health endpoint
│   └── services/
│       ├── category_service.py
│       └── expense_service.py
├── tests/
│   ├── conftest.py
│   ├── test_categories.py
│   ├── test_expenses.py
│   └── test_health.py
├── config.py
├── requirements.txt
└── run.py

frontend/
├── src/
│   ├── api/index.ts          # Typed API client
│   ├── types/index.ts        # Domain types (mirrors backend schemas)
│   ├── components/
│   │   ├── CategoryManager.tsx
│   │   ├── ExpenseForm.tsx
│   │   ├── ExpenseList.tsx
│   │   └── SummaryPanel.tsx
│   ├── App.tsx
│   └── main.tsx
└── vite.config.ts

claude.md     # AI agent hard rules
agents.md     # AI agent workflow + approved/prohibited patterns
```

### Layer Boundaries

```
HTTP Request
    ↓
  Route        (parse HTTP, call schema, call service, serialize response)
    ↓
  Schema       (validate + deserialize input / serialize output)
    ↓
  Service      (business logic, DB access via SQLAlchemy)
    ↓
  Model        (SQLAlchemy ORM)
```

Each layer has one responsibility.  Routes do not query the DB.
Services do not parse HTTP.  This makes each layer independently testable.

---

## Key Technical Decisions

### 1. Amount stored as integer cents

Floating-point cannot represent `0.10` exactly, which causes rounding
drift when summing many expenses.  Storing `amount_cents: int` (e.g.
`1250` for `$12.50`) eliminates this entirely.  The API accepts and
returns a decimal string (`"12.50"`) via Marshmallow, so clients never
see cents.

### 2. Marshmallow as the single validation boundary

All input validation lives in `app/schemas.py`.  Every code path
(HTTP routes, future CLI tools, test fixtures) that creates data must
pass through a schema.  This prevents validation drift — it's impossible
to create an invalid expense by calling the service directly.

### 3. App factory pattern (`create_app`)

The Flask application is created by a factory function, not as a module-
level global.  This means each test gets a fresh, isolated application
instance with an in-memory SQLite database.  Tests cannot accidentally
share state.

### 4. Consistent error shape

Every error response has the shape `{ "error": "..." }`.  Clients
(and tests) never need to parse HTML or guess the response format.
A single `register_error_handlers` function wires this up for
validation errors, domain errors, HTTP exceptions, and unexpected
exceptions.

### 5. Vite proxy instead of hard-coded API URL

The frontend proxies `/api/*` to the Flask server.  The React code
references only relative paths.  Changing the backend port or moving to
a different host requires changing one line in `vite.config.ts`, not
hunting through components.

### 6. TypeScript strict mode + mirrored types

`tsconfig.json` enables `strict: true`.  The `src/types/index.ts` file
mirrors the backend schemas.  If the backend changes a field name,
TypeScript surfaces the mismatch at compile time rather than at runtime
in the browser.

---

## AI Usage

AI assistance (GitHub Copilot / Claude) was used for:

- Generating boilerplate (schema field declarations, test fixtures)
- Suggesting test case names for edge cases
- Writing CSS

All AI-generated code was reviewed against the rules in `claude.md`
before being committed.  The key risks and the mitigations applied:

| Risk | What was checked |
|---|---|
| AI puts logic in routes | Ensured routes only call `schema.load` → `service.*` → `schema.dump` |
| AI uses floats for money | Verified `amount_cents` integer path end-to-end, test `test_amount_stored_as_exact_decimal` |
| AI adds bare `except` | Grep for `except Exception` — only in `app/errors.py` (the handler) |
| AI duplicates validation | Checked no `if amount <= 0` in services or routes |

The files `claude.md` and `agents.md` were written first and used as
the system prompt context when invoking AI agents.

---

## Known Weaknesses & Extension Path

### Weaknesses

- **No authentication** — all data is globally visible. Adding JWT
  middleware + a `User` model is the natural next step.
- **SQLite in dev has no enforcement by default** — the service-layer
  guard (`NotFoundError` on unknown category) compensates, but a prod
  deployment should use Postgres which enforces FKs natively.
- **No pagination** — large datasets will slow the expense list query.

### How to Extend

| Feature | Where to add it |
|---|---|
| Edit an expense | `expense_service.update_expense` + `PATCH /api/expenses/<id>` + schema |
| Monthly budget per category | `budget_cents` on `Category` model + `get_budget_status` service |
| CSV export | `GET /api/expenses/export` route + `csv` stdlib |
| Authentication | Flask-JWT-Extended middleware + `User` model + token validation |
| Postgres in prod | Set `DATABASE_URL` env var — SQLAlchemy handles the rest |

Follow the agent workflow in `agents.md` for any of the above so that
the layer boundaries and test coverage are preserved.
