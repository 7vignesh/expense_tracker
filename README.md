# Expense Tracker

This is a cozy little expense tracker with a modern React/Vite frontend and a Flask-based
API. It is intentionally focused on layering concerns, keeping money safe as cents, and
making it easy to reason about validation, testing, and incremental polish.

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

## Running locally

Start the backend and frontend in separate terminals:

```bash
cd backend
pip install -r requirements.txt
python run.py
```

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api/*` to the Flask server, so the frontend only talks to relative paths.

To exercise the backend tests:

```bash
cd backend
pytest        # all tests
pytest -k expense   # focus on the expense flow
```

---

## Architecture

```
backend/
├── app/
│   ├── __init__.py        # App factory (Flask + SQLAlchemy + Marshmallow)
│   ├── models.py          # SQLAlchemy models (Category, Expense, User)
│   ├── schemas.py         # Marshmallow schemas — validation + serialization
│   ├── errors.py          # Centralised error types + handlers
│   ├── routes/
│   │   ├── auth.py        # /api/auth endpoints
│   │   ├── categories.py  # /api/categories endpoints
│   │   ├── expenses.py    # /api/expenses endpoints
│   │   └── health.py      # /health endpoint
│   └── services/
│       ├── auth_service.py
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

## AI usage

Most of the work was hand-crafted, but AI tools helped scaffold repetitive
pieces like schema definitions, test fixtures, and the elaborate CSS.
Every AI-suggested snippet was reviewed and aligned with the rules detailed in
`claude.md` before landing in the repo.

For transparency, here are the checks that guard against the usual
pitfalls:

| Risk | What was verified |
|---|---|
| Logic sneaks into routes | Routes only orchestrate schemas → services → schema dumps |
| Money stored as floats | `amount_cents` stays an integer and tests validate that path |
| Bare `except` blocks | Grepped for `except Exception` and found none outside `app/errors.py` |
| Validation scattered across layers | Inputs are gatekept by the schemas, not routes or services |

The policy files (`claude.md`, `agents.md`) were drafted before calling any
AI-assisted edits so the agents had strict guardrails.

---

## Known Weaknesses & Extension Path

### Weaknesses

- **Auth is basic** — JWT protects the current user but there is still no
  onboarding flow or refresh tokens.
- **SQLite in dev lacks FK enforcement** — the service layer protects the
  integrity, but PostgreSQL in prod would enforce cascades and constraints by
  default.
- **No pagination** — the `expenses` list loads everything, so large datasets
  may slow down the UI.

### How to extend

| Feature | Where to add it |
|---|---|
| Edit an expense | `expense_service.update_expense` + `PATCH /api/expenses/<id>` + schema |
| Monthly budget per category | `budget_cents` on `Category` model + `get_budget_status` service |
| CSV export | `GET /api/expenses/export` route + `csv` stdlib |
| Authentication | Already wired: JWT middleware, `User` model, login + register UI |
| Postgres in prod | Set `DATABASE_URL` env var — SQLAlchemy handles the rest |

Follow the agent workflow in `agents.md` for any of the above so that
the layer boundaries and test coverage are preserved.
