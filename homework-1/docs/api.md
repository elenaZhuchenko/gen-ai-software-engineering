# Banking Transactions API — Reference

Base URL: `http://localhost:3000`

---

## Transactions

### POST /transactions

Create a new transaction.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fromAccount` | string | For transfer/withdrawal | Source account (`ACC-XXXXX`) |
| `toAccount` | string | For transfer/deposit | Destination account (`ACC-XXXXX`) |
| `amount` | number | Yes | Positive number, max 2 decimal places |
| `currency` | string | Yes | ISO 4217 code (e.g. `USD`, `EUR`) |
| `type` | string | Yes | `deposit`, `withdrawal`, or `transfer` |

**Responses:**

- `201 Created` — Transaction created

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "fromAccount": "ACC-12345",
  "toAccount": "ACC-67890",
  "amount": 100.50,
  "currency": "USD",
  "type": "transfer",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "status": "completed"
}
```

- `400 Bad Request` — Validation failed

```json
{
  "error": "Validation failed",
  "details": [
    { "field": "amount", "message": "Amount must be a positive number" },
    { "field": "currency", "message": "Invalid currency code" }
  ]
}
```

---

### GET /transactions

List all transactions. Supports optional query filters.

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `accountId` | string | Filter by account ID (matches fromAccount or toAccount) |
| `type` | string | Filter by type: `deposit`, `withdrawal`, `transfer` |
| `from` | string | Start date (ISO 8601: `YYYY-MM-DD`) |
| `to` | string | End date (ISO 8601: `YYYY-MM-DD`) |

**Examples:**

```
GET /transactions
GET /transactions?accountId=ACC-12345
GET /transactions?type=transfer
GET /transactions?from=2024-01-01&to=2024-01-31
GET /transactions?accountId=ACC-12345&type=deposit
```

**Response:** `200 OK` — Array of transaction objects (same shape as POST response)

---

### GET /transactions/:id

Get a single transaction by ID.

**Response:**

- `200 OK` — Transaction object
- `404 Not Found`

```json
{ "error": "Transaction not found" }
```

---

### GET /transactions/export

Export all transactions as a CSV file.

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `format` | string | Yes | Must be `csv` |

**Example:**

```
GET /transactions/export?format=csv
```

**Response:**

- `200 OK` — CSV file download

```
Content-Type: text/csv
Content-Disposition: attachment; filename="transactions.csv"

id,fromAccount,toAccount,amount,currency,type,timestamp,status
550e8400-...,ACC-12345,ACC-67890,100,USD,transfer,2024-01-15T10:30:00.000Z,completed
```

The first row is always the header. Each subsequent row is one transaction. Empty fields (e.g. `fromAccount` for a deposit) appear as blank.

- `400 Bad Request` — Missing or unsupported format

```json
{ "error": "Unsupported format. Use ?format=csv" }
```

---

## Accounts

### GET /accounts/:accountId/balance

Get the current balance for an account.

**Path parameter:** `accountId` — must match format `ACC-XXXXX`

**Response:**

- `200 OK`

```json
{
  "accountId": "ACC-12345",
  "balance": 850.00,
  "currency": "USD"
}
```

Balance is computed from all associated transactions:
- Deposits to the account add to balance
- Withdrawals from the account subtract from balance
- Transfers: the `fromAccount` loses, the `toAccount` gains

- `400 Bad Request` — Invalid account ID format

---

### GET /accounts/:accountId/summary

Get an aggregate summary for an account.

**Response:**

- `200 OK`

```json
{
  "accountId": "ACC-12345",
  "totalDeposits": 1500.00,
  "totalWithdrawals": 200.00,
  "transactionCount": 5,
  "mostRecentTransactionDate": "2024-01-15T10:30:00.000Z"
}
```

- `400 Bad Request` — Invalid account ID format

---

## Error format

All error responses follow this structure:

```json
{ "error": "Human-readable message" }
```

Validation errors include a `details` array:

```json
{
  "error": "Validation failed",
  "details": [
    { "field": "fieldName", "message": "What is wrong" }
  ]
}
```

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Resource created |
| `400` | Invalid request / validation failed |
| `404` | Resource not found |
