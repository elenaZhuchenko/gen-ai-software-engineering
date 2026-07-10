# Homework 3: Specification-Driven Design

**Student:** Elena Zhuchenko  
**Course:** AI-Assisted Software Engineering  
**Homework:** 3 — Specification Package (documentation only)

---

## Task Summary

This submission is a **documentation-only specification package** for a finance-oriented feature. No implementation code is included or required. The graded artifacts are:

| File | Description |
|---|---|
| `specification.md` | Layered product/feature specification with high-level objective, mid-level objectives, non-functional requirements, implementation notes, context (beginning/ending), 19 low-level tasks, edge cases, verification plan, and performance targets |
| `agents.md` | AI agent guidelines: tech stack, banking domain rules, code style, testing expectations, security/compliance constraints |
| `.cursor/rules/virtual-card.mdc` | **Feature-scoped** Cursor rule (globbed to `homework-3/**`) with only virtual-card-specific guardrails: state machine, PAN/CVV2 card data handling, endpoints/role routing, external services, migrations |
| `../.cursor/rules/fintech-safe-defaults.mdc` | **Repo-global** Cursor rule (`alwaysApply: true`) with reusable FinTech guardrails (Decimal money, sensitive-data logging, audit trails, idempotency, auth, SQL safety, testing) shared by all finance homeworks. The feature rule layers on top of it. |
| `README.md` | This file |

The chosen domain is the **Virtual Card lifecycle**: create, freeze/unfreeze, set spending limits, and view transactions. Stakeholders modeled are end-users, internal ops/compliance, and customer support.

---

## Rationale

### Why Virtual Card Lifecycle?

Virtual cards are a high-value FinTech feature that concentrates many regulated concerns in a small surface area: PAN tokenization, CVV2 handling, real-time state transitions, spending controls, and a strict audit trail. This makes the feature an ideal vehicle for demonstrating PCI-DSS-aware specification writing, because every layer of the spec—from the high-level objective down to individual task acceptance criteria—is shaped by compliance constraints rather than generic software practices.

### Why This Layered Structure?

The specification follows a deliberately strict hierarchy (vision → observable objectives → non-functional policy → implementation guardrails → context → executable tasks) because this is the structure an AI coding agent needs to resolve ambiguity at each level:

1. **The high-level objective** gives the agent a north star so it does not over-engineer or wander into out-of-scope territory (e.g., physical card issuance is explicitly excluded).
2. **Mid-level objectives** are phrased as observable outcomes ("a card record exists with status `ACTIVE`") so there is a binary test for whether each objective was met—not a vague "the user can manage cards."
3. **Non-functional and policy requirements** are stated as numeric targets or hard constraints rather than adjectives like "fast" or "secure." An agent presented with a vague "should be secure" requirement will make different trade-offs on each run; explicit rules produce deterministic behavior.
4. **Implementation notes** encode the conventions an agent must never violate (`Decimal` for money, append-only audit table, idempotency key semantics). These are the domain invariants that are easiest for a general-purpose model to miss if not stated explicitly.
5. **Context sections** give the agent a precise mental model of what exists before and after work: specific hypothetical service names, table names, file paths. Without a concrete ending context, agents tend to produce incomplete deliverables.
6. **Low-level tasks** are the executable units. Each task names the file to create/update, states the requirements, and ends with checkable acceptance criteria. The link back to the parent mid-level objective ensures every task has a traceable business justification.

### How Performance Targets Were Chosen

All performance targets in `specification.md §Performance` are labeled **assumed targets** because the spec is hypothetical. The values are based on two principles:

1. **FinTech UX expectations:** Consumer card management actions (freeze, limit change) must complete within a second of user interaction to feel instantaneous. Industry benchmarks from open banking platforms (e.g., Revolut's documented < 100 ms for card freeze, Stripe's API SLAs of < 200 ms P99 for most endpoints) inform the P50/P99 ranges chosen.
2. **Authorization path coupling:** The freeze state cache TTL (≤ 500 ms) is deliberately tighter than typical card network authorization round-trips (2–3 seconds). This prevents a race condition where a user freezes a card after noticing suspicious activity but before the freeze propagates to the authorization path. Documenting this coupling makes it impossible for an implementer to choose an arbitrary cache TTL without understanding the downstream consequence.

### How Verification Depth Was Chosen

The verification section is proportional to the risk profile of each concern:

- **PAN/CVV2 absence** gets explicit acceptance criteria on every relevant task (Tasks 6, 9, 14, plus the support view in Task 18 and the audit write path in Task 19) because a single regression here is a PCI-DSS breach.
- **Audit completeness** is a reconciliation check (not just a unit test) because it must hold at the database level, not just in a single function call.
- **Performance** is documented as an integration test assertion (not just a benchmark target) so it is automatically enforced in CI on every PR.
- **Manual compliance review** is explicitly listed as a checkpoint because some security properties (e.g., no PAN in logs under adversarial input) cannot be fully automated.

---

## Industry Best Practices Applied

The following practices are incorporated into the specification package. Each entry cites the exact location in the deliverables.

| Practice | Where it appears |
|---|---|
| **PCI-DSS: No raw PAN storage** | `specification.md §Non-Functional & Policy → Security` (table row "PAN storage"); `specification.md §Implementation Notes → Sensitive Data Handling Rules` (rule 3); `agents.md §3.2` (hard rule 3); `.cursor/rules/virtual-card.mdc §Card Data Handling — PAN and CVV2`; `../.cursor/rules/fintech-safe-defaults.mdc §Database and SQL Safety` |
| **PCI-DSS: CVV2 display once, never store plaintext** | `specification.md §Task 6` (acceptance criterion 1); `agents.md §3.2` (hard rule 4); `.cursor/rules/virtual-card.mdc §Card Data Handling — PAN and CVV2` |
| **PCI-DSS: Encrypted key management** | `specification.md §Beginning Context` (`token-vault`, `encryption-service`); `agents.md §6` (rule 4: keys from env vars); `../.cursor/rules/fintech-safe-defaults.mdc §Secrets and External Calls`; `.cursor/rules/virtual-card.mdc §External Services` |
| **GDPR Article 17: Audit retention overrides erasure** | `specification.md §Non-Functional & Policy → Privacy` (audit records retained 7 years, cannot be erased on user request) |
| **Append-only audit log** | `specification.md §Task 3` (ORM model, no UPDATE/DELETE path); `agents.md §3.3`; `../.cursor/rules/fintech-safe-defaults.mdc §Audit Trails` |
| **Idempotent writes** | `specification.md §Non-Functional & Policy → Reliability` (idempotency target); `specification.md §Implementation Notes → Idempotency`; `agents.md §3.4`; `../.cursor/rules/fintech-safe-defaults.mdc §Idempotency` |
| **Decimal arithmetic for money** | `specification.md §Implementation Notes → Money and Currency`; `agents.md §3.1`; `../.cursor/rules/fintech-safe-defaults.mdc §Money and Decimals` |
| **ISO 4217 currency codes** | `specification.md §Implementation Notes → Money and Currency`; `agents.md §3.1`; `../.cursor/rules/fintech-safe-defaults.mdc §Money and Decimals` |
| **Role-based access control (RBAC)** | `specification.md §Non-Functional & Policy → Security` (table row "Role-based access"); `specification.md §Task 13`; `specification.md §Task 18` (support view isolated under `/support/*`); `agents.md §6` (rule 2); `../.cursor/rules/fintech-safe-defaults.mdc §Authentication and Role Enforcement`; `.cursor/rules/virtual-card.mdc §Endpoints and Role Routing` |
| **Structured logging with scrubbing** | `specification.md §Task 14`; `agents.md §6` (rule 6); `../.cursor/rules/fintech-safe-defaults.mdc §Sensitive Data in Logs` |
| **Optimistic locking for concurrent state transitions** | `specification.md §Edge Cases` (Concurrent freeze+unfreeze row); `agents.md §7` (rule 5) |
| **Explicit performance/SLO targets** | `specification.md §Performance` (full section with P50/P99 table, pagination rules, rate limits, FinTech justification) |
| **Pagination with cursor tokens** | `specification.md §Implementation Notes → API Conventions`; `specification.md §Task 10`; `specification.md §Performance → Pagination Rules` |
| **External service timeouts and graceful degradation** | `specification.md §Edge Cases` (Token-vault unavailable row); `agents.md §6` (rule 5); `../.cursor/rules/fintech-safe-defaults.mdc §Secrets and External Calls`; `.cursor/rules/virtual-card.mdc §External Services` |
| **Test coverage gate (≥ 85%)** | `specification.md §Beginning Context` (CI pipeline entry); `specification.md §Verification → Review Checkpoints` (coverage gate row); `agents.md §5`; `../.cursor/rules/fintech-safe-defaults.mdc §Testing` |
| **Data minimization** | `specification.md §Non-Functional & Policy → Privacy` (masked PAN + token only, raw PAN not stored) |

---

## How AI Tools Were Used

This specification package was authored collaboratively with Cursor AI (Claude Sonnet) in Plan mode and Agent mode:

- **Plan mode:** Used to decompose the homework requirements into a structured plan with ordered todos, ensuring no deliverable section was missed.
- **Agent mode (this session):** The agent drafted the specification package (spec, `agents.md`, the two Cursor rule files, and this README) in order, following the plan, then applied a consistency review pass that reconciled the rate-limit tables, the `actor_type` enum, the masked-PAN representation, added a system-generated card `expiry`, split the low-level tasks out to 19 (adding the dedicated support endpoint and audit-service tasks), and factored the reusable guardrails into the global rule. The domain rules, compliance constraints, and performance rationale were drawn from the project's workspace rules, the `specification-TEMPLATE-example.md` baseline, and the author's domain knowledge of PCI-DSS and FinTech API design patterns.
- **Cursor rules (two layers):** Reusable FinTech guardrails were factored into a repo-global rule, `../.cursor/rules/fintech-safe-defaults.mdc` (`alwaysApply: true`), so every finance homework benefits from them without duplication. The feature-scoped `.cursor/rules/virtual-card.mdc` (globbed to `homework-3/**`) then adds only what is unique to the virtual-card feature — the card state machine, PAN/CVV2 storage rules, endpoint/role routing, external services, and migration constraints — and layers on top of the global rule. This split demonstrates that single-feature rules are not "pointless": generic policy belongs in a shared always-on rule, while feature invariants stay scoped so they never pollute unrelated homeworks.
