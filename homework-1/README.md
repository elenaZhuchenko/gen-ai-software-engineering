# Banking Transactions API

A lightweight REST API for managing banking transactions built with Node.js and Express.

## Features

- Create and list transactions (transfer, deposit, withdrawal)
- Retrieve individual transactions by ID
- Check account balances
- Transaction history with filtering (by account, type, date range)
- Account summary (total deposits, withdrawals, transaction count)
- Full input validation (amount, account format, ISO 4217 currency codes)
- In-memory storage — zero external dependencies at runtime

## Architecture

```
src/
├── app.js                        # Express app factory
├── index.js                      # Server entry point
├── store.js                      # In-memory transaction store (singleton)
├── routes/
│   ├── transactions.js           # POST/GET /transactions, GET /transactions/:id
│   └── accounts.js               # GET /accounts/:id/balance, GET /accounts/:id/summary
├── validators/
│   └── transactionValidator.js   # Input validation (amount, account, currency, type)
└── utils/
    └── currency.js               # ISO 4217 currency code list
```

## Quick Start

```bash
npm install
npm start
# Server runs on http://localhost:3000
```

## Testing

```bash
npm test              # All tests
npm run test:unit     # Unit tests only
npm run test:api      # API integration tests only
```

## API Reference

See [docs/api.md](docs/api.md) for full API documentation.

## Tech Stack

- **Runtime:** Node.js 18+
- **Framework:** Express 4
- **Testing:** Jest + Supertest
- **ID generation:** uuid v9
