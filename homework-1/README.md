# Banking Transactions API

A lightweight REST API for managing banking transactions built with Node.js and Express.

**Author:** Elena Zhuchenko
**AI tool used:** Cursor IDE with Claude Sonnet (agent mode)

## Features

- Create and list transactions (transfer, deposit, withdrawal)
- Retrieve individual transactions by ID
- Check account balances
- Transaction history with filtering (by account, type, date range)
- Account summary (total deposits, withdrawals, transaction count, most recent date)
- Export all transactions as CSV (`GET /transactions/export?format=csv`)
- Full input validation (amount, account format `ACC-XXXXX`, ISO 4217 currency codes)
- In-memory storage — zero external dependencies at runtime
- 49 tests covering all endpoints and validation logic

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/transactions` | Create a transaction |
| `GET` | `/transactions` | List transactions (with filters) |
| `GET` | `/transactions/:id` | Get transaction by ID |
| `GET` | `/transactions/export?format=csv` | Export as CSV |
| `GET` | `/accounts/:accountId/balance` | Get account balance |
| `GET` | `/accounts/:accountId/summary` | Get account summary |

## Architecture

```
src/
├── app.js                        # Express app factory
├── index.js                      # Server entry point
├── store.js                      # In-memory transaction store (singleton)
├── routes/
│   ├── transactions.js           # Transaction endpoints + CSV export
│   └── accounts.js               # Balance and summary endpoints
├── validators/
│   └── transactionValidator.js   # Input validation (amount, account, currency, type)
└── utils/
    └── currency.js               # ISO 4217 currency code list (170+ codes)
```

## Quick Start

```bash
npm install
npm start
# Server runs on http://localhost:3000
```

Run the full demo (starts server, sends sample requests, stops server):

```bash
bash demo/run.sh
```

## Testing

```bash
npm test              # All tests (49)
npm run test:unit     # Unit tests only (validators, store)
npm run test:api      # API integration tests only
```

## API Reference

See [docs/api.md](docs/api.md) for full API documentation.

## Demo Files

| File | Description |
|------|-------------|
| `demo/run.sh` | Starts the server and runs sample requests |
| `demo/sample-requests.http` | Ready-to-use HTTP requests (VS Code REST Client) |
| `demo/sample-data.json` | Sample transaction data |

## Tech Stack

- **Runtime:** Node.js 18+
- **Framework:** Express 4
- **Testing:** Jest + Supertest
- **ID generation:** uuid v9
