# Agent Guidelines: Virtual Card Lifecycle Service

This document configures AI coding assistants working in this project. Follow every rule below without deviation unless the user explicitly overrides it. When in doubt, apply the more restrictive interpretation.

---

## 1. Project Identity

- **Domain:** FinTech — virtual card lifecycle management in a regulated environment.
- **Primary spec:** `specification.md` in this directory. Read it fully before starting any task.
- **Deliverable type:** Implementation code (Python), tests, migrations, and supporting docs. No UI.
- **Compliance context:** PCI-DSS Level 1, GDPR. Treat cardholder data as the most sensitive class of information in this system.

---

## 2. Technology Stack Assumptions

| Layer | Chosen technology |
|---|---|
| Language | Python 3.11+ |
| Web framework | FastAPI (async) |
| Data validation | Pydantic v2 (`BaseModel`, `model_validator`, `field_validator`) |
| ORM | SQLAlchemy 2.x with async sessions (`AsyncSession`) |
| Database (prod) | PostgreSQL 15+ |
| Database (tests) | SQLite in-memory via `aiosqlite` |
| Migrations | Alembic |
| Testing framework | pytest 7+ with `pytest-asyncio` |
| HTTP test client | `httpx.AsyncClient` |
| Coverage | `pytest-cov` (gate: ≥ 85%) |
| Linting | ruff |
| Type checking | mypy (strict mode) |
| Logging | `structlog` (JSON lines output) |

Do not introduce new dependencies without noting them explicitly. If a task would benefit from a library not listed here, state it as a comment or note — do not silently add it.

---

## 3. Banking Domain Rules

These rules encode FinTech-specific invariants that must never be violated:

### 3.1 Money and Currency
- **Always use `decimal.Decimal`** for monetary values. Never use `float` or `int` for money arithmetic.
- All monetary values in the API are represented as decimal strings (e.g., `"123.45"`), not as floats or integers.
- Currency codes must be ISO 4217 alpha-3. Validate at model level, not just in comments.
- Limit comparisons must use `Decimal` comparison operators; floating-point equality is forbidden.
- When converting between minor units (cents) and decimal amounts, use explicit `Decimal` arithmetic with `quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`.

### 3.2 Sensitive Data — Hard Rules
1. **Never log PAN.** No call to any logger, print statement, exception serializer, debug middleware, or tracing span may include a raw 16-digit card number.
2. **Never log CVV2.** Same constraint. CVV2 exists only in the encrypted store and the one-time creation response.
3. **Never store raw PAN in the application database.** Only the card token (non-reversible HMAC surrogate) and the masked PAN (`masked_pan`, exposing at most the last four digits) may be persisted.
4. **Never return CVV2 in any GET endpoint.** The plaintext CVV2 is returned exclusively in the `POST /cards` 201 response and never again.
5. **Never expose raw card tokens in logs, error messages, or non-privileged API responses.**
6. **PII must not appear in URL paths or query parameters.** Use request bodies for sensitive identifiers.

### 3.3 Audit Trails
- Every state-mutating operation (create, freeze, unfreeze, limit update, close) must produce an `AuditEvent` record before the response is returned.
- Audit records are append-only. Never write an `UPDATE` or `DELETE` query against the `audit_events` table.
- If writing the audit record fails, the transaction must roll back — do not commit a state change without its audit event.
- Audit events must include: `actor_type`, `actor_id`, `previous_state`, `new_state`, `timestamp` (UTC), `request_id`.

### 3.4 Idempotency
- All `POST` and `PUT` endpoints that mutate state must accept and process an `Idempotency-Key` header.
- On duplicate key (same key + same payload within 24 hours): return the stored response with HTTP 200. Do not create a new resource.
- On key collision (same key + different payload): return HTTP 422 with `error: IDEMPOTENCY_KEY_MISMATCH`.
- Idempotency key storage: keyed by `sha256(idempotency_key + user_id)` to prevent cross-user key collisions.

### 3.5 State Machine
- Card status transitions follow a strict machine defined in `specification.md` §Low-Level Task 4.
- Never implement an ad-hoc `if status == X: status = Y` check. Always delegate to `apply_status_transition`.
- `CLOSED` is a terminal state. No transition out of `CLOSED` is ever permitted.

---

## 4. Code Style and Conventions

### Python
- All functions and methods must have type annotations. mypy strict mode must pass.
- Use `async def` for all FastAPI route handlers and service methods that touch the database.
- Import order: stdlib → third-party → local (enforced by ruff `I` rules).
- Maximum line length: 100 characters.
- No bare `except:` clauses. Catch specific exceptions and handle or re-raise with context.
- Do not use `print()` anywhere in production code. Use `structlog.get_logger()`.

### Naming
- Models: `PascalCase` nouns (`Card`, `CardLimit`, `AuditEvent`).
- Services: `snake_case` modules (`card_service.py`, `audit_service.py`).
- Route files: `snake_case` modules matching the resource (`cards.py`, `ops.py`).
- Constants: `UPPER_SNAKE_CASE`.
- Error codes (machine-readable): `UPPER_SNAKE_CASE` strings (e.g., `CARD_NOT_FOUND`, `EXCEEDS_DAILY_LIMIT`).

### Error Responses
Always return errors in the standard envelope:
```json
{
  "error": "MACHINE_CODE",
  "message": "Human-readable description.",
  "request_id": "uuid"
}
```
Never include stack traces, internal service names, DB query strings, or raw exception messages in API error responses.

### Dependency Injection
- Use FastAPI's `Depends()` for all service and database session injection.
- Do not use module-level singletons for stateful objects (DB sessions, service instances).

---

## 5. Testing and Verification Expectations

### Coverage
- The coverage gate is **≥ 85%** on `app/`. Every PR must pass `pytest --cov=app --cov-fail-under=85`.
- New code without tests will not be merged.

### Test Structure
- `tests/unit/`: test individual service functions with all external dependencies mocked.
- `tests/integration/`: test full HTTP flows. Use `httpx.AsyncClient` with the FastAPI test app.
- Each test must be independent: no shared mutable state between tests. Use pytest fixtures with `scope="function"`.
- Test names follow the pattern: `test_<what>_<condition>_<expected_outcome>`.

### What to Test
- All state machine transition combinations (positive and negative).
- All limit enforcement edge cases (exactly at cap, zero amount, cross-currency).
- Idempotency: duplicate key replay and key mismatch.
- Audit event presence and correct field values after every mutation.
- Role enforcement: each endpoint tested with at least one authorized and one unauthorized role.
- PAN/CVV2 absence in GET responses (assert `cvv2` key not present in response JSON).

### Performance Assertions
- Integration tests for `GET /cards/{id}/transactions` and `GET /ops/cards/{id}/audit` must assert that response time is < 200 ms P50 on a 1,000-record data set, measured with `time.perf_counter`.

---

## 6. Security and Compliance Constraints

1. **Input validation first**: validate all inputs at the Pydantic model boundary before any business logic runs. Reject unknowns with HTTP 422.
2. **Role enforcement before data access**: the auth middleware must run before any route handler. Never check roles inside service functions — enforce at the router level.
3. **No SQL injection**: use SQLAlchemy ORM or parameterized queries exclusively. Never use string concatenation to build SQL.
4. **Key material never in code**: encryption keys, HMAC salts, and JWT secrets must come from environment variables or a secrets manager. Never hard-code them — not even in test fixtures (use test-specific placeholder keys).
5. **External service timeouts**: all calls to `user-service`, `token-vault`, and `encryption-service` must have explicit timeouts (default: 2 seconds). A timeout results in HTTP 503 to the caller; no partial state is committed.
6. **Structured logging compliance**: use `structlog` with a PAN/CVV2 scrubber processor in the processor chain. The scrubber must run before any transport handler.

---

## 7. How to Treat Edge Cases

When implementing any feature, you must:

1. **Identify the failure modes first.** Before writing business logic, list the ways the input can be invalid, the downstream service can fail, or the current state can make the operation impossible.
2. **Implement the unhappy path before the happy path** where the spec provides an error code. Return the error before processing the request further.
3. **Use the edge cases table** in `specification.md` as a checklist. Every row in that table must have a corresponding test.
4. **Never silently swallow errors.** If an operation fails, surface it as an explicit error response or a logged exception. Do not return a 200 with an empty body on failure.
5. **Concurrent modification:** use optimistic locking (`version` column + compare-and-swap in UPDATE) for card status transitions. Do not rely on application-level locks.
6. **Partial failure:** if writing the audit event fails after a state change is persisted, the entire DB transaction must be rolled back. Atomicity is non-negotiable.

---

## 8. What the Agent Must Never Do

- Never write a migration that adds a column named `pan`, `cvv`, `cvv2`, `card_number`, or `raw_pan` to any table.
- Never implement a `GET /cards/{id}` endpoint that returns a CVV2 field.
- Never bypass the state machine for card status transitions.
- Never use `float` for any monetary calculation.
- Never commit a transaction without a corresponding audit event.
- Never skip the `Idempotency-Key` check on a mutating endpoint.
- Never expose an unauthenticated route to card or audit data.
- Never log a value from the request body without first running it through the scrubber.
