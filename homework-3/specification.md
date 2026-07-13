# Virtual Card Lifecycle Specification

> Ingest the information from this file, implement the Low-Level Tasks, and generate the code that will satisfy the High and Mid-Level Objectives.

---

## High-Level Objective

Enable individual users to create, manage, and monitor virtual payment cards with configurable spending limits, instant freeze/unfreeze controls, and a full transaction history—all within a regulated, PCI-DSS-aware environment.

**Scope boundary:** This specification covers the virtual card resource lifecycle only (create, read, update state, view transactions). It does not cover physical card issuance, payment network clearing, currency conversion, or user identity/KYC onboarding, which are handled by external services. **Real-time authorization decisioning is also out of scope:** this service owns and exposes the state (freeze status, spending limits) that the external authorization path consumes, but the accept/decline decision and its `AUTHORIZATION_DECLINED` audit events originate in that external path. Where the Edge Cases table describes authorization declines, it documents the *expected downstream behavior* given this service's state — not an endpoint implemented here.

---

## Mid-Level Objectives

### MO-1 — Card Creation
A user can request a new virtual card, specifying an optional nickname, currency, and initial spending limit. The system returns a masked PAN, a card ID, an expiry (system-generated), and a CVV2 (encrypted at rest, displayed only once). A compliance event is written to the audit log on every successful creation.

**Observable outcome:** A new card record exists in the card store with status `ACTIVE`, a masked PAN (last 4 digits only), an assigned card token (non-reversible), and an audit log entry containing card ID, user ID, timestamp, and action `CARD_CREATED`.

### MO-2 — Freeze and Unfreeze
A user or ops agent can toggle a card between `ACTIVE` and `FROZEN` states in near-real-time. Frozen cards must be declined at authorization time with reason code `DO_NOT_HONOR`. The state change is atomic and immediately consistent from the authorization path's perspective.

**Observable outcome:** The card's `status` field reflects the new state within one second of the API response. Any authorization attempt against a `FROZEN` card returns a decline with `reason: CARD_FROZEN`. An audit log entry is written for every state transition, identifying who (user or ops agent) initiated it.

### MO-3 — Spending Limits
A user can set or update a per-transaction, daily, or monthly spending cap on each card, denominated in the card's currency. Limit changes take effect immediately for new authorizations. Attempted changes that exceed the account-level policy ceiling are rejected with a clear error.

**Observable outcome:** After a successful limit update, any authorization request whose amount would breach the new limit is declined with reason code `EXCEEDS_LIMIT`. A `LIMIT_UPDATED` audit event is recorded with the previous and new limit values.

### MO-4 — Transaction History
A user can retrieve a paginated, chronologically ordered list of transactions for a given card, with optional date-range and amount filters. The system returns transaction ID, merchant name (masked if PCI-sensitive), authorization amount, final settled amount, currency, status, and timestamp.

**Observable outcome:** Calling the transactions endpoint returns results with stable pagination cursor semantics. Filtering by `from_date`/`to_date` returns only records within that window (inclusive). An ops agent additionally receives the `merchant_name_hash` for each transaction so they can correlate activity for the same merchant across cards; the raw merchant name is never stored by this service (resolution, if ever required, is delegated to the external merchant directory and is out of scope).

### MO-5 — Ops and Compliance Oversight
An internal ops/compliance user can search cards by user ID or card ID, view full card state (excluding plaintext CVV2/PAN), trigger freeze/unfreeze with a mandatory reason note, view the complete audit log for a card or user, and export audit records in CSV format.

**Observable outcome:** Ops actions appear as distinct entries in the audit log (`actor_type: OPS`) and are logically separate from user-initiated events. Any export includes a row count and a generated-at timestamp.

### MO-6 — Customer Support View
A support agent can look up a card by card ID or user ID, view the card status and masked PAN, and check whether a declined transaction fell within limit or freeze boundaries—without ever accessing the raw PAN, CVV2, or full card token.

**Observable outcome:** The support API returns the same safe `CardSummary` object as the user view (`id`, `masked_pan`, `status`, `currency`, `limits`, `nickname`, `created_at`); no additional fields are exposed. The support role cannot modify card state. Any support lookup is logged as a `SUPPORT_LOOKUP` audit event.

---

## Non-Functional & Policy Requirements

### Security

| Requirement | Target |
|---|---|
| PAN storage | Stored only as a non-reversible token (e.g., 128-bit HMAC-SHA256 with a hardware-derived key). Raw PAN never persisted in application DB. |
| CVV2 storage | Encrypted (AES-256-GCM) at rest. Delivered to the user exactly once (on creation response). Never returned in any subsequent API call. |
| Transport | TLS 1.2+ enforced on all endpoints. Mutual TLS required for ops and payment network callbacks. |
| Secret rotation | Key rotation supported without data loss; old keys retired within 30 days. |
| Role-based access | Three roles: `USER`, `SUPPORT`, `OPS_COMPLIANCE`. JWT claims enforced at middleware layer. Privilege escalation is never implicit. |
| Input validation | All monetary values validated as positive Decimal with scale ≤ 2. All enums validated as closed sets. Free-text fields sanitized (no HTML/script injection). |
| Sensitive data in logs | PAN, CVV2, full card token, and personal names must never appear in application logs or error messages. |

### Privacy

- Card data is subject to PCI-DSS Level 1 controls. Data minimization principle applies: the application stores the minimum required to support the feature (masked PAN + token, not raw PAN).
- GDPR Article 17 (right to erasure): card records can be logically deleted (status `CLOSED`); associated audit records are retained for 7 years in accordance with financial regulation and must not be erased even on user request.
- Data residency: all storage must remain within the declared jurisdiction. Cross-region replication is permitted for availability but must remain within that jurisdiction.

### Audit and Logging

- Every state-mutating operation (create, freeze, unfreeze, limit update, close) must produce a structured audit event containing: `event_id`, `card_id`, `user_id`, `actor_type` (`USER` | `OPS` | `SUPPORT` | `SYSTEM`), `actor_id`, `action`, `timestamp` (ISO 8601 UTC), `previous_state`, `new_state`, `ip_address` (hashed), and `request_id`.
- Read-only ops and support lookups produce a lighter audit event: `event_id`, `card_id`, `actor_type`, `actor_id`, `action`, `timestamp`, `request_id`.
- Audit log entries are append-only and must not be updatable or deletable via any API path.
- Audit records must be queryable by `card_id`, `user_id`, `actor_id`, and `time_range` with pagination.

### Reliability

| Metric | Assumed Target |
|---|---|
| Availability | 99.9% measured monthly (≤ 43 min downtime/month) |
| Durability | Card state and audit records must survive a single node failure without data loss (synchronous replication to at least one replica before ack). |
| Freeze consistency | The `FROZEN` state must be authoritative within ≤ 1 second of API response for all authorization paths. |
| Idempotency | All create/update endpoints accept a client-supplied `Idempotency-Key` header. Replaying the same key within 24 hours returns the original response with HTTP 200; a new resource is not created. |

### Performance (Assumed Targets — see §Performance section for full rationale)

| Operation | P50 | P99 | Notes |
|---|---|---|---|
| Card create | < 150 ms | < 500 ms | Includes token generation and audit write |
| Freeze / unfreeze | < 80 ms | < 250 ms | Authorization path reads cached state; cache TTL ≤ 500 ms |
| Limit update | < 100 ms | < 300 ms | Effective immediately for new authorizations |
| Transaction list (first page) | < 200 ms | < 600 ms | Max page size 50 records |
| Audit export (CSV) | < 3 s | < 10 s | For up to 10,000 records; background job for larger exports |
| Rate limit | 60 req/min per user token; 120 req/min per support token; 300 req/min per ops/compliance token (see §Performance → Rate Limits) | — | HTTP 429 with `Retry-After` on breach |

---

## Implementation Notes

### Money and Currency

- All monetary amounts must be represented as `decimal.Decimal` (Python) or equivalent arbitrary-precision type. Floating-point (`float`) must never be used for money calculations.
- Currency codes must be ISO 4217 alpha-3 (e.g., `USD`, `EUR`, `GBP`). An unknown currency code is a 422 validation error.
- Amounts stored and returned in minor units where required by the card network; exposed in the API as human-readable decimal strings (e.g., `"123.45"`) with the currency code.
- Limit comparisons must be done in the card's native currency. Cross-currency authorization requests are out of scope and must return `CURRENCY_MISMATCH` decline.

### Identifiers

- Card IDs: UUID v4, formatted as lowercase hyphenated string: `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`.
- Idempotency keys: up to 64 characters, ASCII printable. Stored with a TTL of 24 hours.
- Card tokens (non-reversible surrogate): deterministic HMAC-SHA256 over `(raw_pan + issuer_salt)`, base64url-encoded, 43 characters. Never reversible to PAN.
- Request IDs: generated server-side, UUID v4; returned in `X-Request-ID` response header; included in all log lines for trace correlation.

### Idempotency

- `POST /cards` and `PUT /cards/{id}/limits` and `PUT /cards/{id}/status` accept `Idempotency-Key` header (required for all mutating calls from client SDKs).
- On duplicate key: return HTTP 200 (not 201) and the stored response body unchanged. Write a `IDEMPOTENT_REPLAY` marker to structured logs (not to audit log).
- On key collision with different payload: return HTTP 422 with `error: IDEMPOTENCY_KEY_MISMATCH`.

### Error Semantics

- All error responses follow a consistent envelope: `{ "error": "<MACHINE_CODE>", "message": "<human readable>", "request_id": "<uuid>" }`.
- Never include stack traces, internal service names, or raw database errors in API error responses.
- HTTP status codes: 400 (malformed input), 401 (unauthenticated), 403 (forbidden), 404 (resource not found), 409 (conflict / state violation), 422 (validation failure), 429 (rate limit), 500 (unexpected internal error).

### Sensitive Data Handling Rules

1. **Never log PAN** — no logger call, no exception serializer, no debug middleware may emit a raw PAN.
2. **Never log CVV2** — same constraint; CVV2 exists only in the creation response payload and in encrypted storage.
3. **Mask PAN everywhere** — only the masked PAN (`masked_pan`, formatted `****-****-****-XXXX`, exposing at most the last four digits) is returned in any API response after creation. The raw PAN is never returned.
4. **No PII in URLs** — user names and account numbers must not appear in URL paths or query parameters.
5. **Audit fields are write-once** — no UPDATE or DELETE path touches the audit table.

### API Conventions

- All timestamps in ISO 8601 UTC (`2024-01-15T10:30:00Z`).
- Pagination uses opaque cursor tokens, not offset/limit, to prevent skipped/duplicated records on concurrent writes.
- Every response includes `X-Request-ID` header.
- Bulk ops (e.g., audit export) over 10,000 records are accepted via a background-job endpoint that returns a `job_id`; status is polled via `GET /jobs/{id}`.

---

## Context

### Beginning Context

The following hypothetical systems and artifacts are assumed to exist before work on this feature begins:

| Resource | Description |
|---|---|
| `user-service` | External service providing user identity and KYC status. Exposes `GET /users/{id}` returning `{ id, kyc_status, account_policy }`. |
| `account-policy-store` | Stores per-user maximum card limits and card count caps. Queried by the card service before creation and limit updates. |
| `auth-service` | Provides JWT issuance and validation. Roles: `USER`, `SUPPORT`, `OPS_COMPLIANCE`. |
| `audit-log-store` | An append-only event store (e.g., PostgreSQL with row-level security disabling DELETE/UPDATE on audit tables). |
| `card-store` | Relational DB schema for card records (empty at feature start). Schema migrations are managed by Alembic. |
| `token-vault` | Hardware-based key store (or HSM emulator in staging) providing `tokenize(pan)` and key rotation operations. |
| `encryption-service` | Provides `encrypt(plaintext)` / `decrypt(ciphertext)` using AES-256-GCM. Used only for CVV2. |
| Development environment | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x (async), pytest 7+, `httpx` for test client. |
| CI pipeline | GitHub Actions with lint (ruff), type-check (mypy), unit + integration tests, and coverage gate (≥ 85%). |

### Ending Context

After all Low-Level Tasks are implemented, the following artifacts and states exist:

| Artifact | Description |
|---|---|
| `app/models/card.py` | Pydantic and ORM models for `Card`, `CardLimit`, `CardStatus`, `CardToken`. |
| `app/models/transaction.py` | Pydantic and ORM models for `Transaction`, `TransactionStatus`. |
| `app/models/audit.py` | Append-only ORM model for `AuditEvent`. |
| `app/routers/cards.py` | Card CRUD endpoints: create, get, freeze/unfreeze, update limits, close. |
| `app/routers/transactions.py` | Transaction list endpoint with pagination and filtering. |
| `app/routers/ops.py` | Ops/compliance endpoints: card search, audit log query, audit CSV export. |
| `app/routers/support.py` | Read-only support endpoints: card summary lookup. |
| `app/services/card_service.py` | Business logic: state machine, limit enforcement, idempotency, tokenization call. |
| `app/services/audit_service.py` | Audit event construction and write; ensures no PII in event fields. |
| `app/middleware/auth.py` | JWT validation and role enforcement middleware. |
| `app/middleware/logging.py` | Structured JSON logging middleware with PAN/CVV2 scrubber. |
| `tests/unit/` | Unit tests for service logic, model validation, state machine. |
| `tests/integration/` | Integration tests for all API endpoints via test client. |
| `tests/fixtures/` | Data fixtures: valid/invalid card creation payloads, transaction sets, audit event samples. |
| `alembic/versions/` | DB migrations for card, transaction, and audit tables. |
| `docs/api/openapi.yaml` | Auto-generated OpenAPI 3.1 spec. |
| Card store | Contains at least the card records created during test/seed runs; all in states `ACTIVE`, `FROZEN`, or `CLOSED`. |
| Audit log store | Contains all mutation events from test/seed runs, append-only. |

---

## Low-Level Tasks

### Task 1 — Define Card and Limit Data Models
*Serves: MO-1, MO-3*

Create Pydantic v2 and SQLAlchemy ORM models for the `Card` entity and its embedded `CardLimit` sub-model.

**Files:** `app/models/card.py`

**Requirements:**
- `Card` fields: `id` (UUID4), `user_id` (UUID4), `nickname` (optional, max 50 chars), `masked_pan` (str, exactly 19 chars: `****-****-****-XXXX`), `card_token` (str, 43 chars), `currency` (ISO 4217, validated), `status` (enum: `ACTIVE | FROZEN | CLOSED`), `expiry` (str, `MM/YY`, system-generated at creation), `created_at` (datetime UTC), `updated_at` (datetime UTC).
- `CardLimit` fields: `per_transaction` (Decimal, ≥ 0), `daily` (Decimal, ≥ 0), `monthly` (Decimal, ≥ 0). All optional; `None` means uncapped.
- Decimal fields use `condecimal(ge=0, decimal_places=2)` or equivalent.
- ORM model maps to table `cards`; `CardLimit` stored as three columns on the same table.
- No field may store raw PAN or CVV2.

**Acceptance Criteria:**
- [ ] `Card` model rejects a `currency` value not in ISO 4217 (test: `currency="XYZ"` → `ValidationError`).
- [ ] `Card` model rejects `status` values outside the enum.
- [ ] `CardLimit` rejects negative values and values with > 2 decimal places.
- [ ] ORM model round-trips to/from a SQLite in-memory DB in tests without data loss.

---

### Task 2 — Define Transaction Data Model
*Serves: MO-4*

Create Pydantic v2 and SQLAlchemy ORM models for the `Transaction` entity.

**Files:** `app/models/transaction.py`

**Requirements:**
- Fields: `id` (UUID4), `card_id` (UUID4, FK to `cards.id`), `merchant_name_masked` (str, max 100 chars, last two words replaced with `***`), `merchant_name_hash` (str, HMAC of original for ops lookup), `authorization_amount` (Decimal), `settled_amount` (Decimal, nullable until settlement), `currency` (ISO 4217), `status` (enum: `AUTHORIZED | SETTLED | DECLINED | REVERSED`), `decline_reason` (optional str), `authorized_at` (datetime UTC), `settled_at` (optional datetime UTC).
- No raw merchant name stored in the main table (only masked + hash).

**Acceptance Criteria:**
- [ ] Model rejects `authorization_amount < 0`.
- [ ] `decline_reason` is required when `status = DECLINED`.
- [ ] ORM foreign key from `transactions.card_id` to `cards.id` enforced in migration.

---

### Task 3 — Define Audit Event Model (Append-Only)
*Serves: MO-1, MO-2, MO-3, MO-5, MO-6*

Create the append-only `AuditEvent` ORM model and ensure the DB table has no UPDATE/DELETE path.

**Files:** `app/models/audit.py`

**Requirements:**
- Fields: `event_id` (UUID4, PK), `card_id` (UUID4, nullable for user-level events), `user_id` (UUID4), `actor_type` (enum: `USER | OPS | SUPPORT | SYSTEM`), `actor_id` (UUID4), `action` (str, machine code, e.g., `CARD_CREATED`), `timestamp` (datetime UTC), `previous_state` (JSON, nullable), `new_state` (JSON, nullable), `ip_address_hash` (str, SHA-256 of IP), `request_id` (UUID4).
- Service layer must only ever call `INSERT`; no update/delete methods exposed.
- Index on `(card_id, timestamp)` and `(user_id, timestamp)` for query performance.

**Acceptance Criteria:**
- [ ] `AuditService` has no `.update()` or `.delete()` method.
- [ ] Inserting two events with the same `event_id` raises an integrity error (PK uniqueness).
- [ ] Test fixture inserts 100 events and queries by `card_id` in < 50 ms (SQLite in-memory).

---

### Task 4 — Implement Card State Machine
*Serves: MO-1, MO-2*

Implement a pure-function state machine that validates and applies card status transitions.

**Files:** `app/services/card_service.py` (function `apply_status_transition`)

**Requirements:**
- Allowed transitions: `ACTIVE → FROZEN`, `FROZEN → ACTIVE`, `ACTIVE → CLOSED`, `FROZEN → CLOSED`.
- Disallowed: `CLOSED → *` (any), `ACTIVE → ACTIVE`, `FROZEN → FROZEN`.
- Returns `(new_state, audit_action_code)` on success, raises `CardStateTransitionError` on invalid transition.
- `CLOSED` is terminal: no further transitions permitted.

**Acceptance Criteria:**
- [ ] All 9 transition combinations (3 statuses × 3 targets: ACTIVE, FROZEN, CLOSED) have explicit unit tests covering 4 allowed and 5 disallowed paths.
- [ ] `CardStateTransitionError` message includes current state and attempted target state.
- [ ] `ACTIVE → CLOSED` produces audit action `CARD_CLOSED`; `ACTIVE → FROZEN` produces `CARD_FROZEN`.

---

### Task 5 — Implement Spending Limit Enforcement
*Serves: MO-3*

Implement the limit check function that is called before each authorization attempt and before each limit update.

**Files:** `app/services/card_service.py` (function `check_authorization_limits`)

**Requirements:**
- Inputs: `card_limits: CardLimit`, `amount: Decimal`, `currency: str`, `daily_spent: Decimal`, `monthly_spent: Decimal`.
- Returns `LimitCheckResult(allowed: bool, reason: Optional[str])`.
- Checks: amount > `per_transaction` limit → reason `EXCEEDS_PER_TRANSACTION_LIMIT`; `daily_spent + amount` > `daily` → `EXCEEDS_DAILY_LIMIT`; `monthly_spent + amount` > `monthly` → `EXCEEDS_MONTHLY_LIMIT`.
- A `None` limit means uncapped for that dimension.
- Raises `CurrencyMismatchError` if card currency ≠ request currency.

**Acceptance Criteria:**
- [ ] `None` limit passes check for that dimension regardless of amount.
- [ ] All three limit types independently trigger the correct reason code.
- [ ] `daily_spent + amount == daily` (exactly at cap) is ALLOWED (inclusive).
- [ ] Cross-currency input raises `CurrencyMismatchError`.

---

### Task 6 — Card Create Endpoint
*Serves: MO-1*

Implement `POST /cards` endpoint.

**Files:** `app/routers/cards.py`, `app/services/card_service.py`

**Requirements:**
- Request body: `CreateCardRequest { nickname?: str, currency: str, limits?: CardLimitRequest }`.
- Calls `user-service` to verify user KYC status; rejects with 422 if `kyc_status != VERIFIED`.
- Calls `account-policy-store` to check user has not exceeded max card count; rejects with 409 if at cap.
- Calls `token-vault` to tokenize a system-generated PAN; stores token + masked PAN; discards raw PAN after tokenization.
- Generates CVV2, encrypts via `encryption-service`, stores ciphertext; returns plaintext CVV2 **once** in response, then discards.
- Accepts `Idempotency-Key` header; replays stored response on duplicate.
- Writes `CARD_CREATED` audit event.
- Returns 201 with `CardCreatedResponse { id, masked_pan, cvv2_plaintext, expiry, currency, status, limits, created_at }`.

**Acceptance Criteria:**
- [ ] Response contains `cvv2_plaintext` field only on HTTP 201; GET card endpoint must not return CVV2.
- [ ] Duplicate `Idempotency-Key` returns HTTP 200 with identical body and does not create a second card record.
- [ ] `CARD_CREATED` audit event exists with correct `card_id`, `user_id`, `actor_type: USER`.
- [ ] A user with KYC `PENDING` receives HTTP 422 with `error: KYC_NOT_VERIFIED`.

---

### Task 7 — Freeze and Unfreeze Endpoint
*Serves: MO-2*

Implement `PUT /cards/{card_id}/status` endpoint.

**Files:** `app/routers/cards.py`, `app/services/card_service.py`

**Requirements:**
- Request body: `UpdateStatusRequest { status: "FROZEN" | "ACTIVE" | "CLOSED", reason?: str }`.
- Ops role: `reason` field is required; user role: `reason` optional.
- Delegates to `apply_status_transition`; propagates `CardStateTransitionError` as HTTP 409.
- Publishes cache invalidation event so the authorization path sees updated state within 500 ms.
- Writes `CARD_FROZEN` / `CARD_UNFROZEN` / `CARD_CLOSED` audit event with `reason` in `new_state`.
- Accepts `Idempotency-Key`.

**Acceptance Criteria:**
- [ ] `ACTIVE → FROZEN` returns 200 and card status in response is `FROZEN`.
- [ ] `FROZEN → FROZEN` returns HTTP 409.
- [ ] Ops freeze without `reason` returns HTTP 422.
- [ ] Audit event `previous_state` and `new_state` reflect actual state values.

---

### Task 8 — Update Spending Limits Endpoint
*Serves: MO-3*

Implement `PUT /cards/{card_id}/limits` endpoint.

**Files:** `app/routers/cards.py`, `app/services/card_service.py`

**Requirements:**
- Request body: `UpdateLimitsRequest { per_transaction?: Decimal, daily?: Decimal, monthly?: Decimal }`.
- Validates that new limits do not exceed the account-policy ceiling; returns 422 with `error: EXCEEDS_ACCOUNT_POLICY` if they do.
- Partial update: omitted fields retain their current value.
- Validates logical consistency: `per_transaction ≤ daily ≤ monthly` when all three are set; returns 422 if violated.
- Accepts `Idempotency-Key`.
- Writes `LIMIT_UPDATED` audit event with `previous_state` and `new_state` containing full limit snapshot.

**Acceptance Criteria:**
- [ ] Setting `per_transaction = 1000` when `daily = 500` returns HTTP 422 with `error: LIMIT_CONSISTENCY_VIOLATION`.
- [ ] Omitting `monthly` in the request leaves the current `monthly` limit unchanged.
- [ ] `LIMIT_UPDATED` audit event captures both old and new limit values.
- [ ] Limit changes are visible in subsequent `GET /cards/{id}` responses immediately.

---

### Task 9 — Get Card and List Cards Endpoints
*Serves: MO-1*

Implement `GET /cards/{card_id}` and `GET /cards` (user-scoped list). These are `USER`-role endpoints under `/cards/*`; the support view is a separate `/support/*` endpoint (see Task 18).

**Files:** `app/routers/cards.py`

**Requirements:**
- `GET /cards/{card_id}`: returns `CardSummary { id, masked_pan, currency, status, limits, nickname, expiry, created_at }`. Never returns CVV2, raw token, or raw PAN.
- `GET /cards`: returns only cards owned by the authenticated user. Supports `?status=ACTIVE|FROZEN|CLOSED` filter.
- `OPS_COMPLIANCE` may reach a card via the ops search endpoint (Task 11); this task does not grant `SUPPORT` access to `/cards/*`.

**Acceptance Criteria:**
- [ ] CVV2 is absent from GET response (test: response JSON keys must not contain `cvv2`).
- [ ] User A cannot retrieve User B's card (returns HTTP 404, not 403, to avoid enumeration).
- [ ] A `SUPPORT`-role request to `GET /cards/{card_id}` returns HTTP 403 (support must use the `/support/*` endpoint in Task 18).

---

### Task 10 — Transaction List Endpoint
*Serves: MO-4*

Implement `GET /cards/{card_id}/transactions` endpoint.

**Files:** `app/routers/transactions.py`

**Requirements:**
- Pagination: cursor-based, default page size 20, max 50. Returns `{ data: [...], next_cursor: str|null, total_count: int }`.
- Filters: `from_date` (ISO 8601), `to_date` (ISO 8601), `status`, `min_amount`, `max_amount`.
- Date filters are inclusive on both ends.
- Sorting: `authorized_at` descending (newest first), stable across pages.
- Returns the `masked` merchant name for user/support; ops role receives `merchant_name_hash` in addition, used only to correlate transactions for the same merchant. The raw merchant name is not stored by this service, so there is no endpoint that resolves it.

**Acceptance Criteria:**
- [ ] Requesting page 2 with the cursor from page 1 returns the next 20 records without duplication.
- [ ] `from_date = to_date` returns only transactions on that calendar day (UTC).
- [ ] `next_cursor` is `null` when there are no more records.
- [ ] Response time < 200 ms P50 on a data set of 1,000 transactions (measured in integration test using `time.perf_counter`).

---

### Task 11 — Ops Card Search and Audit Log Endpoint
*Serves: MO-5*

Implement `GET /ops/cards` (search) and `GET /ops/cards/{card_id}/audit` (audit log query).

**Files:** `app/routers/ops.py`

**Requirements:**
- `GET /ops/cards`: accepts `?user_id=` or `?card_id=` query param (one required); returns list of `CardSummary` objects (same as user view—no raw PAN or CVV2).
- `GET /ops/cards/{card_id}/audit`: returns paginated audit events for the card sorted by `timestamp` descending. Supports `from_date`, `to_date`, `action` filters.
- Both endpoints require `OPS_COMPLIANCE` role; return 403 for other roles.
- Audit query results include all fields except `ip_address_hash` (which is excluded to avoid IP-to-action correlation outside authorized forensic use).

**Acceptance Criteria:**
- [ ] Request by a `USER` role returns HTTP 403.
- [ ] Search with neither `user_id` nor `card_id` returns HTTP 400.
- [ ] Audit log for a card with 200 events returns correct first page with cursor.

---

### Task 12 — Audit CSV Export Endpoint
*Serves: MO-5*

Implement `POST /ops/exports/audit` (background job) and `GET /ops/exports/{job_id}` (poll).

**Files:** `app/routers/ops.py`, `app/services/export_service.py`

**Requirements:**
- `POST /ops/exports/audit`: accepts `{ card_id?: UUID, user_id?: UUID, from_date: datetime, to_date: datetime }`. Requires at least one of `card_id` or `user_id`. Starts background job; returns `{ job_id: UUID, status: "QUEUED" }` with HTTP 202.
- Background job writes CSV to a temporary signed URL or in-memory buffer. CSV columns match audit event fields (excluding `ip_address_hash`).
- First row is a header row. Last data row is followed by a row: `# total_records: N, generated_at: <ISO 8601>`.
- `GET /ops/exports/{job_id}`: returns `{ job_id, status: QUEUED|RUNNING|DONE|FAILED, download_url?: str, row_count?: int, generated_at?: datetime }`.
- For exports ≤ 10,000 records: completes synchronously (within the 10 s P99 budget) and sets status to `DONE` immediately.

**Acceptance Criteria:**
- [ ] CSV contains a header row matching the defined column names.
- [ ] `row_count` in the job status response equals the number of data rows in the CSV (excluding header and trailer).
- [ ] A request missing both `card_id` and `user_id` returns HTTP 400.
- [ ] `DONE` job status contains a non-null `download_url`.

---

### Task 13 — Authentication and Role Enforcement Middleware
*Serves: MO-1 through MO-6 (cross-cutting)*

Implement JWT validation middleware and role-based access enforcement.

**Files:** `app/middleware/auth.py`

**Requirements:**
- Validate Bearer JWT on every request; reject with HTTP 401 if absent or invalid.
- Extract `sub` (user ID), `role`, `jti` (token ID) from claims.
- Attach `auth_context: AuthContext` to `request.state` for downstream use.
- Role guard decorator `@require_role(*roles)` usable on route handlers.
- `OPS_COMPLIANCE` role can access all `/ops/*` and `/support/*` paths. `SUPPORT` role can access only `/support/*`. `USER` role can access only `/cards/*` and `/cards/{id}/transactions`.

**Acceptance Criteria:**
- [ ] Missing `Authorization` header returns HTTP 401 with `error: UNAUTHENTICATED`.
- [ ] Expired JWT returns HTTP 401 with `error: TOKEN_EXPIRED`.
- [ ] `USER` role accessing `/ops/cards` returns HTTP 403 with `error: FORBIDDEN`.
- [ ] `AuthContext` is available in `request.state` for all authenticated requests.

---

### Task 14 — Logging Middleware with PAN/CVV2 Scrubber
*Serves: MO-1 through MO-6 (cross-cutting security)*

Implement structured JSON request/response logging middleware that scrubs sensitive values.

**Files:** `app/middleware/logging.py`

**Requirements:**
- Log `request_id`, `method`, `path`, `status_code`, `duration_ms` for every request.
- Scrub any value matching a 16-digit sequence (PAN pattern), a 3-digit CVV pattern adjacent to card fields, or a field named `cvv2`, `pan`, `card_number`, `raw_pan` from log output.
- Log level: `INFO` for 2xx/3xx, `WARNING` for 4xx, `ERROR` for 5xx.
- Scrubber must be applied to both request body logs and response body logs.
- Output format: JSON lines (one JSON object per line), compatible with log aggregation pipelines.

**Acceptance Criteria:**
- [ ] A request body containing `"pan": "4111111111111111"` logs `"pan": "***REDACTED***"`.
- [ ] A response body containing `"cvv2": "123"` logs `"cvv2": "***REDACTED***"`.
- [ ] Log output for a normal card-create request contains `request_id`, `duration_ms`, and `status_code`.

---

### Task 15 — Integration Test Suite (Happy Paths)
*Serves: All MOs*

Write integration tests for the primary success flows of each endpoint.

**Files:** `tests/integration/test_cards.py`, `tests/integration/test_transactions.py`, `tests/integration/test_ops.py`

**Requirements:**
- Use `httpx.AsyncClient` with FastAPI test app.
- Cover: create card (201), get card (200), freeze (200), unfreeze (200), update limits (200), list transactions (200), ops search (200), ops audit log (200), support lookup (200).
- Assert response schema, HTTP status, and presence of audit event after each mutation.
- Each test is independent: database seeded and torn down per test.

**Acceptance Criteria:**
- [ ] All integration tests pass with a clean database.
- [ ] Each mutation test asserts at least one corresponding audit event in the audit store.
- [ ] Test coverage ≥ 85% across `app/` (measured by `pytest-cov`).

---

### Task 16 — Unit Test Suite (Edge Cases and Error Paths)
*Serves: All MOs*

Write unit tests for the service layer covering all error and edge-case paths.

**Files:** `tests/unit/test_card_service.py`, `tests/unit/test_audit_service.py`, `tests/unit/test_limit_enforcement.py`

**Requirements:**
- Test all invalid state transitions (Task 4 matrix).
- Test all limit enforcement edge cases: exactly-at-cap, cross-currency, `None` limits.
- Test idempotency key replay (same key, same payload vs. different payload).
- Test audit event construction: fields present, no PAN/CVV2 in any field.
- Mocked dependencies (token-vault, encryption-service, user-service) using `unittest.mock.AsyncMock`.

**Acceptance Criteria:**
- [ ] All 9 state transition combinations are explicitly tested (4 valid, 5 invalid).
- [ ] Audit event fixture contains no field value matching a 16-digit number.
- [ ] Idempotency key mismatch (same key, different payload) raises correct exception.

---

### Task 17 — DB Migration Scripts
*Serves: MO-1, MO-3, MO-4, MO-5*

Write Alembic migration files for all tables.

**Files:** `alembic/versions/0001_create_cards.py`, `alembic/versions/0002_create_transactions.py`, `alembic/versions/0003_create_audit_events.py`

**Requirements:**
- `cards` table: columns per Task 1 model plus timestamps; no column for raw PAN or CVV2 plaintext.
- `transactions` table: columns per Task 2 model; FK to `cards.id` with `ON DELETE RESTRICT`.
- `audit_events` table: columns per Task 3 model; composite indexes on `(card_id, timestamp)` and `(user_id, timestamp)`; no FK cascade delete from `cards` (audit records persist after card closure).
- Each migration has a `downgrade()` path.

**Acceptance Criteria:**
- [ ] `alembic upgrade head` runs without error on a fresh database.
- [ ] `alembic downgrade -1` cleanly removes the most recent migration.
- [ ] No column in `cards` or `audit_events` is named `pan`, `cvv2`, or `card_number`.

---

### Task 18 — Support Card Summary Endpoint
*Serves: MO-6*

Implement the read-only support lookup endpoint under `/support/*`, kept separate from `/cards/*` so the role model in Task 13 (`SUPPORT` → `/support/*` only) holds without exception.

**Files:** `app/routers/support.py`

**Requirements:**
- `GET /support/cards/{card_id}` and `GET /support/cards?user_id=...`: return the same safe `CardSummary` object as Task 9 (`id`, `masked_pan`, `status`, `currency`, `limits`, `nickname`, `expiry`, `created_at`). No raw PAN, CVV2, or full card token.
- Requires `SUPPORT` or `OPS_COMPLIANCE` role; any other role returns HTTP 403.
- The endpoint is read-only: no state-mutating verb is exposed.
- Writes a `SUPPORT_LOOKUP` audit event (`actor_type: SUPPORT`) for every lookup.

**Acceptance Criteria:**
- [ ] A `SUPPORT`-role request returns `CardSummary` with no `cvv2`, raw PAN, or raw token field present.
- [ ] A `USER`-role request to `/support/cards/{card_id}` returns HTTP 403.
- [ ] A `SUPPORT_LOOKUP` audit event with `actor_type: SUPPORT` is written for each successful lookup.
- [ ] No support route accepts `POST`, `PUT`, `PATCH`, or `DELETE`.

---

### Task 19 — Audit Service Write Path
*Serves: MO-1, MO-2, MO-3, MO-5, MO-6 (cross-cutting)*

Implement the single write path all endpoints use to persist audit events, guaranteeing append-only semantics and atomicity with the state change.

**Files:** `app/services/audit_service.py`

**Requirements:**
- Expose a single `record_event(...)` coroutine that performs an `INSERT` into `audit_events`. No `update`/`delete` methods exist on the service.
- The audit write must run inside the same DB transaction as the state mutation it accompanies; if the audit write fails, the whole transaction rolls back (no state change is committed without its audit event).
- Construct the full event payload (`event_id`, `card_id`, `user_id`, `actor_type`, `actor_id`, `action`, `timestamp` UTC, `previous_state`, `new_state`, `ip_address_hash`, `request_id`) and guarantee no PAN, CVV2, or raw token value can appear in any field.
- Read-only lookups (ops/support) use a lighter event variant per §Audit and Logging.

**Acceptance Criteria:**
- [ ] `AuditService` exposes no `.update()` or `.delete()` method (reuses the Task 3 guarantee at the service layer).
- [ ] A simulated audit-write failure rolls back the accompanying state change (test asserts the card row is unchanged).
- [ ] No constructed audit-event field value matches a 16-digit number (PAN) or a stored CVV2.

---

## Edge Cases and Failure Modes

| Scenario | Expected User-Visible Behavior | Audit / Compliance Implication |
|---|---|---|
| Create card when user KYC is `PENDING` | HTTP 422, `error: KYC_NOT_VERIFIED` | No card created, no `CARD_CREATED` event written |
| Create card when user is at account card cap | HTTP 409, `error: CARD_CAP_EXCEEDED` | No card created; ops may investigate via account-policy-store |
| Duplicate `Idempotency-Key` (same payload) | HTTP 200 with original response body | `IDEMPOTENT_REPLAY` marker in structured log; no new audit event |
| Duplicate `Idempotency-Key` (different payload) | HTTP 422, `error: IDEMPOTENCY_KEY_MISMATCH` | No mutation; warning log entry with key and request ID |
| Freeze already-frozen card | HTTP 409, `error: INVALID_STATE_TRANSITION` | No state change; no audit event |
| Close a card that has unsettled transactions | HTTP 409, `error: UNSETTLED_TRANSACTIONS_EXIST`; user directed to wait for settlement | No state change; compliance note appended to card record |
| Set `per_transaction` limit > `daily` limit | HTTP 422, `error: LIMIT_CONSISTENCY_VIOLATION` | No limit update; no audit event |
| Set limit exceeding account-policy ceiling | HTTP 422, `error: EXCEEDS_ACCOUNT_POLICY` | No limit update; suspicious repeated attempts logged as `WARNING` |
| Authorization against a `FROZEN` card | Decline response to payment network: `DO_NOT_HONOR`; user sees "card frozen" in UI | `AUTHORIZATION_DECLINED` audit event with `reason: CARD_FROZEN` |
| Authorization amount > `per_transaction` limit | Decline: `EXCEEDS_LIMIT` | `AUTHORIZATION_DECLINED` event with `reason: EXCEEDS_PER_TRANSACTION_LIMIT` |
| Monthly spend cap reached mid-month | All subsequent authorizations declined: `EXCEEDS_MONTHLY_LIMIT` | Each declined auth produces an audit event; ops can view via audit log |
| Transaction currency ≠ card currency | Decline: `CURRENCY_MISMATCH` | Audit event; if repeated from same merchant in short window → fraud signal (out of scope to act, but log) |
| Token-vault service unavailable during card create | HTTP 503 to user; request fails fast (< 2 s timeout) | No partial card record persisted; `EXTERNAL_SERVICE_FAILURE` log event |
| Encryption-service unavailable during card create | HTTP 503; no card created | Same as above; encrypted CVV2 never stored if service is unreachable |
| Concurrent freeze+unfreeze requests for the same card | Optimistic lock; one succeeds (200), the other receives HTTP 409 with `error: CONCURRENT_MODIFICATION` | Both attempts logged; winning state is authoritative |
| Ops agent accesses another user's card without authorization | HTTP 403 (ops cannot cross-user unless they have `OPS_COMPLIANCE` role) | `UNAUTHORIZED_ACCESS_ATTEMPT` log event with actor ID |
| Request with expired JWT | HTTP 401, `error: TOKEN_EXPIRED` | No audit event; structured log includes `jti` of expired token |
| Request missing required `Idempotency-Key` header on mutable endpoint | HTTP 400, `error: MISSING_IDEMPOTENCY_KEY` | No mutation attempted |
| Audit export job for 50,000 records | HTTP 202 immediately; job runs asynchronously; `GET /ops/exports/{id}` polls until `DONE`; download URL provided | Entire export lifecycle logged; large export triggers `WARNING` if duration > 30 s |
| Stale read: card status read immediately after freeze | Authorization path reads from cache (TTL ≤ 500 ms); user should retry after 1 s for UI reflection | Stale-read window is bounded and documented in operations runbook |

---

## Verification

### Review Checkpoints

| Checkpoint | Owner | Criteria |
|---|---|---|
| Model review | Tech lead + compliance | All Pydantic and ORM models reviewed for PCI-DSS field exposure. No raw PAN or CVV2 column in any model. |
| API contract review | Tech lead + product | OpenAPI spec reviewed against this specification. Every endpoint, status code, and error code documented. |
| Security review | Security engineer | Middleware scrubber validated against OWASP Logging Guide. Token vault and encryption-service integration reviewed. |
| Edge-case walkthrough | QA + product | Every row in the Edge Cases table reviewed with a "how would a tester verify this?" answer. |
| Performance benchmark | Engineering | P50/P99 targets in the Performance section met or documented with a remediation plan. |
| Coverage gate | CI | `pytest --cov=app --cov-fail-under=85` must pass on every PR. |

### Test Categories (Documentation-Level)

**Unit tests** (`tests/unit/`) cover individual service functions in isolation with mocked dependencies. Target: all business logic branches, all state machine paths, all limit enforcement conditions.

**Integration tests** (`tests/integration/`) cover full HTTP request/response cycles against an in-memory SQLite DB. Target: every endpoint's happy path + at least two error paths per endpoint.

**Contract tests** (documented; not automated) validate that the OpenAPI spec and the actual API responses remain synchronized. Run `openapi-spec-validator` in CI.

**Compliance review tests** (manual) verify: no PAN in logs, no CVV2 in GET responses, audit events present after each mutation. Reviewed by security/compliance during release.

### Data Fixtures

The following fixtures must exist under `tests/fixtures/`:

| Fixture | Contents |
|---|---|
| `valid_create_card.json` | Minimal valid card creation request (EUR, no limits) |
| `invalid_create_card_bad_currency.json` | Card creation with `currency: "XYZ"` |
| `create_card_with_limits.json` | Card creation with all three limit fields set |
| `freeze_request.json` | Valid freeze request body |
| `invalid_limit_consistency.json` | `per_transaction > daily` (should fail) |
| `transactions_50.json` | 50 synthetic transaction records for card `test-card-001` |
| `audit_events_100.json` | 100 synthetic audit events for `test-card-001` |

### Reconciliation Checks

1. **Card count**: `SELECT COUNT(*) FROM cards WHERE user_id = X` must match the value returned by the user's account-policy-store.
2. **Audit completeness**: for every record in `cards` with `status != 'ACTIVE'`, there must exist an audit event with `action IN ('CARD_FROZEN', 'CARD_CLOSED')`.
3. **No raw PAN**: a SQL query across all tables for values matching `[0-9]{16}` must return zero rows (run as a post-deploy smoke test).
4. **Limit consistency**: for every card with all three limits set, `per_transaction ≤ daily ≤ monthly` must hold in the DB.

---

## Performance

### Assumed Targets and Rationale

All numbers below are **assumed targets** appropriate for a consumer FinTech card management service. They are set based on the following FinTech UX and ops principles:

- **Sub-second feedback for interactive operations**: Users toggling card freeze or viewing balances expect near-instant feedback. Exceeding 1 second for a freeze response erodes trust and may cause repeated taps/clicks, leading to duplicate requests (hence the idempotency requirement).
- **Authorization path must be faster than the freeze propagation**: The freeze state cache TTL (500 ms) is chosen to be within the expected card network authorization round-trip window (~2–3 seconds). This ensures that a user who freezes a card before a fraudulent attempt sees the card actually declined.
- **Pagination prevents runaway queries**: Ops and compliance queries over large data sets (audit exports) are background jobs to avoid blocking the API worker pool.

| Operation | P50 target | P99 target | Measurement method |
|---|---|---|---|
| `POST /cards` | < 150 ms | < 500 ms | Integration test with `time.perf_counter` over 100 sequential calls |
| `PUT /cards/{id}/status` (freeze/unfreeze) | < 80 ms | < 250 ms | Integration test; also manual load test with `locust` (5 concurrent users) |
| `PUT /cards/{id}/limits` | < 100 ms | < 300 ms | Integration test |
| `GET /cards/{id}` | < 50 ms | < 150 ms | Integration test |
| `GET /cards/{id}/transactions` (first page, 20 records) | < 200 ms | < 600 ms | Integration test on 1,000 seeded transactions |
| `GET /ops/cards/{id}/audit` (first page, 20 events) | < 150 ms | < 400 ms | Integration test on 1,000 seeded audit events |
| Audit CSV export (≤ 10,000 records) | < 3 s | < 10 s | Measured via job `created_at` → `done_at` delta |
| Cache invalidation after freeze | ≤ 500 ms | ≤ 1,000 ms | Measured by polling authorization-path cache endpoint after PUT |

### Pagination Rules

- Default page size: 20 records.
- Maximum page size: 50 records. Requests with `page_size > 50` are rejected with HTTP 400.
- Cursors are opaque base64-encoded strings encoding the sort key + last-seen ID; they are valid for 10 minutes.
- Expired cursors return HTTP 410 (`CURSOR_EXPIRED`), prompting the client to restart from page 1.

### Rate Limits

| Actor | Limit | Behavior on breach |
|---|---|---|
| `USER` token | 60 requests/minute | HTTP 429, `Retry-After: 60` header |
| `SUPPORT` token | 120 requests/minute | HTTP 429 |
| `OPS_COMPLIANCE` token | 300 requests/minute | HTTP 429 |
| Global (all tokens) | 2,000 requests/minute | HTTP 503 (circuit breaker, not per-user) |

Rate limit windows are sliding (not fixed bucket) to prevent burst at window boundaries.

### Throughput Assumptions

- The service is designed for a single-tenant deployment handling up to **10,000 active cards** and **500,000 transactions per month** (approximately 17,000/day, 12/minute at peak).
- Audit exports up to 10,000 rows synchronously; beyond that, background job with poll-based status is mandatory.
- Background export job concurrency: maximum 5 concurrent exports per ops actor; additional requests are queued with HTTP 202.
