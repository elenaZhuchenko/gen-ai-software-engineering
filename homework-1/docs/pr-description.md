## Homework 1: Banking Transactions API

### ✅ What was implemented

A lightweight REST API for banking transactions built with **Node.js + Express**, covering all required tasks:

**Task 1 — Core API**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/transactions` | Create a transaction (deposit / withdrawal / transfer) |
| `GET` | `/transactions` | List all transactions |
| `GET` | `/transactions/:id` | Get transaction by ID |
| `GET` | `/accounts/:accountId/balance` | Calculate account balance from transaction history |

All transactions are stored in-memory (no database). Appropriate HTTP codes are returned: 200, 201, 400, 404.

**Task 2 — Validation**
- Amount: must be positive, max 2 decimal places
- Account format: must match `ACC-XXXXX` (alphanumeric)
- Currency: validated against full ISO 4217 list (170+ codes)
- All errors return a structured `{ error, details[] }` response

**Task 3 — Transaction filtering**
`GET /transactions` supports query filters:
- `?accountId=ACC-12345` — filter by account (matches `fromAccount` or `toAccount`)
- `?type=transfer` — filter by type
- `?from=2024-01-01&to=2024-01-31` — date range
- Filters can be combined freely

**Task 4 — Additional features (2 of 4)**
- **Option A:** `GET /accounts/:accountId/summary` — returns total deposits, total withdrawals, transaction count, most recent date
- **Option C:** `GET /transactions/export?format=csv` — exports all transactions as a downloadable CSV file

**Test coverage: 49 tests, all passing**
```
PASS tests/api/transactions.test.js
PASS tests/api/accounts.test.js
PASS tests/unit/transactionValidator.test.js
PASS tests/unit/store.test.js
Tests: 49 passed, 49 total
```

---

### 🛠️ AI tools used

**Tool:** Cursor IDE with Claude Sonnet (agent mode)

**Workflow:**
1. Used AI to scaffold the initial project structure and `package.json`
2. Prompted AI to implement each route incrementally, reviewing generated code before accepting
3. Asked AI to generate validation logic for amount, account format, and ISO 4217 currencies
4. Used AI to write Jest + Supertest tests for all endpoints
5. AI suggested the `trap`-based approach for `demo/run.sh` to auto-start and stop the server

**What I verified manually:**
- Ran `npm test` to confirm all 49 tests pass
- Tested the API manually with curl and `demo/run.sh`
- Reviewed every generated file for correctness before committing
- Confirmed error responses match the format specified in TASKS.md

---

### ⚠️ Challenges and how I addressed them

**1. `GET /transactions/export` vs `GET /transactions/:id` route conflict**
Express matched `/export` as an `:id` parameter. Fixed by placing the `/export` route *before* the `/:id` route in `transactions.js`.

**2. 404 error when opening URL with trailing slash**
On first run, requests to paths ending with `/` (e.g. `http://localhost:3000/transactions/`) returned an error. Diagnosed and fixed with Cursor agent by adding a root `GET /` handler that returns API info, and ensuring the catch-all 404 middleware is placed last.

**3. `git push` failing with HTTP 400**
The commit contained ~1.4MB of screenshot files, exceeding git's default 1MB HTTP buffer. Fixed with:
```bash
git config http.postBuffer 524288000
```

**4. Validator edge case — amounts like `1.005`**
JavaScript floating point can produce numbers with more than 2 decimal places. The validator converts the number to a string and runs a regex check (`/^\d+(\.\d{1,2})?$/`) to catch this correctly.

---

### 🚀 How to run

```bash
cd homework-1
npm install
npm start
# API available at http://localhost:3000
```

Run the full demo (starts server, fires requests, stops server):
```bash
bash demo/run.sh
```

Run tests:
```bash
npm test
```

Full instructions: [`HOWTORUN.md`](HOWTORUN.md)
API reference: [`docs/api.md`](docs/api.md)

---

### 📸 Screenshots

| | |
|---|---|
| AI prompt — generating core routes | ![ai-prompt-1](https://github.com/elenaZhuchenko/gen-ai-software-engineering/blob/homework-1-submission/homework-1/docs/screenshots/ai-prompt-1.png?raw=true) |
| AI prompt — validation logic | ![ai-prompt-2](https://github.com/elenaZhuchenko/gen-ai-software-engineering/blob/homework-1-submission/homework-1/docs/screenshots/ai-prompt-2.png?raw=true) |
| AI fixing a bug | ![ai-prompt-fixing](https://github.com/elenaZhuchenko/gen-ai-software-engineering/blob/homework-1-submission/homework-1/docs/screenshots/ai-prompt-fixing.png?raw=true) |
| AI-generated result | ![ai-prompt-result-1](https://github.com/elenaZhuchenko/gen-ai-software-engineering/blob/homework-1-submission/homework-1/docs/screenshots/ai-prompt-result-1.png?raw=true) |
| Running via AI agent | ![run-via-ai](https://github.com/elenaZhuchenko/gen-ai-software-engineering/blob/homework-1-submission/homework-1/docs/screenshots/run-via-ai.png?raw=true) |
| API running — terminal demo | ![api-running-demo](https://github.com/elenaZhuchenko/gen-ai-software-engineering/blob/homework-1-submission/homework-1/docs/screenshots/api-running-demo.png?raw=true) |
| API running — health check | ![api-running](https://github.com/elenaZhuchenko/gen-ai-software-engineering/blob/homework-1-submission/homework-1/docs/screenshots/api-running.png?raw=true) |
