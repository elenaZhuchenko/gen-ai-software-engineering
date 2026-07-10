# API Reference - Support Ticket System

Consumer reference for the Support Ticket System API. The API is implemented with FastAPI and stores tickets in an in-memory store for the current process.

## Base URL

Local development:

```text
http://localhost:8000
```

Run the API from `homework-2/src`:

```bash
uvicorn main:app --reload
```

## Content Types

- JSON endpoints accept `Content-Type: application/json`.
- Bulk import accepts `multipart/form-data` with a `file` field.
- Import file formats: CSV, JSON, XML.
- Date/time fields are returned as ISO 8601 strings.

## Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Check API health |
| `POST` | `/tickets` | Create a support ticket |
| `GET` | `/tickets` | List tickets with optional filters |
| `GET` | `/tickets/{ticket_id}` | Get one ticket |
| `PUT` | `/tickets/{ticket_id}` | Update one ticket |
| `DELETE` | `/tickets/{ticket_id}` | Delete one ticket |
| `POST` | `/tickets/{ticket_id}/auto-classify` | Classify an existing ticket |
| `POST` | `/tickets/import` | Bulk import tickets from CSV, JSON, or XML |

---

## Health Check

### `GET /health`

Returns a simple service health response.

### Response `200 OK`

```json
{
  "status": "ok"
}
```

### cURL

```bash
curl -X GET "http://localhost:8000/health"
```

---

## Create Ticket

### `POST /tickets`

Creates a support ticket. Set `auto_classify` to `true` to classify the ticket during creation.

### Request Body

```json
{
  "customer_id": "cust-1001",
  "customer_email": "alex@example.com",
  "customer_name": "Alex Rivera",
  "subject": "Cannot access account",
  "description": "I cannot access my account after resetting my password.",
  "category": null,
  "priority": null,
  "status": "new",
  "assigned_to": null,
  "tags": ["login", "password"],
  "metadata": {
    "source": "web_form",
    "browser": "Chrome",
    "device_type": "desktop"
  },
  "auto_classify": true
}
```

Required fields: `customer_id`, `customer_email`, `customer_name`, `subject`, `description`.

### Response `201 Created`

```json
{
  "id": "2bb6c879-5e75-4c6c-84f4-ef52a924a3da",
  "customer_id": "cust-1001",
  "customer_email": "alex@example.com",
  "customer_name": "Alex Rivera",
  "subject": "Cannot access account",
  "description": "I cannot access my account after resetting my password.",
  "category": "account_access",
  "priority": "urgent",
  "status": "new",
  "created_at": "2026-07-03T15:00:00.000000",
  "updated_at": "2026-07-03T15:00:00.000000",
  "resolved_at": null,
  "assigned_to": null,
  "tags": ["login", "password"],
  "metadata": {
    "source": "web_form",
    "browser": "Chrome",
    "device_type": "desktop"
  },
  "classification": {
    "category": "account_access",
    "priority": "urgent",
    "confidence": 0.78,
    "reasoning": "Category 'account_access' matched keywords: password. Priority 'urgent' matched keywords: cannot access",
    "keywords_found": ["password", "cannot access"],
    "classified_at": "2026-07-03T15:00:00.000000",
    "manual_override": false
  }
}
```

### cURL

```bash
curl -X POST "http://localhost:8000/tickets" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust-1001",
    "customer_email": "alex@example.com",
    "customer_name": "Alex Rivera",
    "subject": "Cannot access account",
    "description": "I cannot access my account after resetting my password.",
    "tags": ["login", "password"],
    "metadata": {
      "source": "web_form",
      "browser": "Chrome",
      "device_type": "desktop"
    },
    "auto_classify": true
  }'
```

---

## List Tickets

### `GET /tickets`

Returns all tickets, optionally filtered by query parameters.

### Query Parameters

| Parameter | Type | Allowed values | Required | Description |
| --- | --- | --- | --- | --- |
| `category` | string | See `Category` enum | No | Filter by ticket category |
| `priority` | string | See `Priority` enum | No | Filter by priority |
| `status` | string | See `Status` enum | No | Filter by status |
| `customer_id` | string | Any string | No | Filter by customer ID |

### Response `200 OK`

```json
{
  "total": 1,
  "tickets": [
    {
      "id": "2bb6c879-5e75-4c6c-84f4-ef52a924a3da",
      "customer_id": "cust-1001",
      "customer_email": "alex@example.com",
      "customer_name": "Alex Rivera",
      "subject": "Cannot access account",
      "description": "I cannot access my account after resetting my password.",
      "category": "account_access",
      "priority": "urgent",
      "status": "new",
      "created_at": "2026-07-03T15:00:00.000000",
      "updated_at": "2026-07-03T15:00:00.000000",
      "resolved_at": null,
      "assigned_to": null,
      "tags": ["login", "password"],
      "metadata": {
        "source": "web_form",
        "browser": "Chrome",
        "device_type": "desktop"
      },
      "classification": null
    }
  ]
}
```

### cURL

```bash
curl -X GET "http://localhost:8000/tickets?category=account_access&priority=urgent&status=new"
```

---

## Get Ticket

### `GET /tickets/{ticket_id}`

Returns a single ticket by ID.

### Path Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `ticket_id` | string | Yes | Ticket UUID returned by create or import |

### Response `200 OK`

```json
{
  "id": "2bb6c879-5e75-4c6c-84f4-ef52a924a3da",
  "customer_id": "cust-1001",
  "customer_email": "alex@example.com",
  "customer_name": "Alex Rivera",
  "subject": "Cannot access account",
  "description": "I cannot access my account after resetting my password.",
  "category": "account_access",
  "priority": "urgent",
  "status": "new",
  "created_at": "2026-07-03T15:00:00.000000",
  "updated_at": "2026-07-03T15:00:00.000000",
  "resolved_at": null,
  "assigned_to": null,
  "tags": ["login", "password"],
  "metadata": {
    "source": "web_form",
    "browser": "Chrome",
    "device_type": "desktop"
  },
  "classification": null
}
```

### Error `404 Not Found`

```json
{
  "detail": "Ticket '2bb6c879-5e75-4c6c-84f4-ef52a924a3da' not found"
}
```

### cURL

```bash
curl -X GET "http://localhost:8000/tickets/2bb6c879-5e75-4c6c-84f4-ef52a924a3da"
```

---

## Update Ticket

### `PUT /tickets/{ticket_id}`

Updates any supplied ticket fields. Omitted fields are left unchanged. If `status` is changed to `resolved` or `closed`, `resolved_at` is set automatically when it is currently `null`.

### Request Body

All fields are optional.

```json
{
  "status": "in_progress",
  "assigned_to": "agent-42",
  "tags": ["login", "vip"]
}
```

### Response `200 OK`

```json
{
  "id": "2bb6c879-5e75-4c6c-84f4-ef52a924a3da",
  "customer_id": "cust-1001",
  "customer_email": "alex@example.com",
  "customer_name": "Alex Rivera",
  "subject": "Cannot access account",
  "description": "I cannot access my account after resetting my password.",
  "category": "account_access",
  "priority": "urgent",
  "status": "in_progress",
  "created_at": "2026-07-03T15:00:00.000000",
  "updated_at": "2026-07-03T15:05:00.000000",
  "resolved_at": null,
  "assigned_to": "agent-42",
  "tags": ["login", "vip"],
  "metadata": {
    "source": "web_form",
    "browser": "Chrome",
    "device_type": "desktop"
  },
  "classification": null
}
```

### cURL

```bash
curl -X PUT "http://localhost:8000/tickets/2bb6c879-5e75-4c6c-84f4-ef52a924a3da" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "assigned_to": "agent-42",
    "tags": ["login", "vip"]
  }'
```

---

## Delete Ticket

### `DELETE /tickets/{ticket_id}`

Deletes one ticket.

### Response `204 No Content`

The response body is empty.

### Error `404 Not Found`

```json
{
  "detail": "Ticket '2bb6c879-5e75-4c6c-84f4-ef52a924a3da' not found"
}
```

### cURL

```bash
curl -X DELETE "http://localhost:8000/tickets/2bb6c879-5e75-4c6c-84f4-ef52a924a3da"
```

---

## Auto-Classify Ticket

### `POST /tickets/{ticket_id}/auto-classify`

Runs keyword-based categorization and priority assignment for an existing ticket.

When `override` is `false`, an existing classification with `manual_override=true` is respected. When `override` is `true`, the ticket category, priority, and classification are replaced with the new result.

### Request Body

```json
{
  "override": false
}
```

If the body is omitted, `override` defaults to `false`.

### Response `200 OK`

```json
{
  "ticket_id": "2bb6c879-5e75-4c6c-84f4-ef52a924a3da",
  "category": "account_access",
  "priority": "urgent",
  "confidence": 0.78,
  "reasoning": "Category 'account_access' matched keywords: password. Priority 'urgent' matched keywords: cannot access",
  "keywords_found": ["password", "cannot access"],
  "classified_at": "2026-07-03T15:10:00.000000"
}
```

### cURL

```bash
curl -X POST "http://localhost:8000/tickets/2bb6c879-5e75-4c6c-84f4-ef52a924a3da/auto-classify" \
  -H "Content-Type: application/json" \
  -d '{"override": false}'
```

---

## Bulk Import Tickets

### `POST /tickets/import`

Imports tickets from CSV, JSON, or XML. The file is sent as multipart form data using the `file` field.

Supported content types:

- `text/csv`
- `application/json`
- `text/xml`
- `application/xml`

If the content type is missing or unsupported, the API also attempts to infer the parser from `.csv`, `.json`, or `.xml` file extensions.

### Query Parameters

| Parameter | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| `auto_classify` | boolean | `false` | No | Auto-classify each successfully imported ticket |

### CSV Example

```csv
customer_id,customer_email,customer_name,subject,description,category,priority,status,tags
cust-2001,jordan@example.com,Jordan Lee,Invoice overcharge,Please review this invoice overcharge,billing_question,medium,new,"billing,invoice"
```

### JSON Example

The JSON importer accepts either a single object or an array of objects.

```json
[
  {
    "customer_id": "cust-2002",
    "customer_email": "sam@example.com",
    "customer_name": "Sam Chen",
    "subject": "Dark mode suggestion",
    "description": "Please add dark mode as a new user preference.",
    "tags": ["feature", "ui"],
    "metadata": {
      "source": "api",
      "device_type": "desktop"
    }
  }
]
```

### XML Example

```xml
<tickets>
  <ticket>
    <customer_id>cust-2003</customer_id>
    <customer_email>morgan@example.com</customer_email>
    <customer_name>Morgan Patel</customer_name>
    <subject>App crash on mobile</subject>
    <description>The app crashes on startup after the latest update.</description>
    <metadata>
      <source>email</source>
      <device_type>mobile</device_type>
    </metadata>
  </ticket>
</tickets>
```

### Response `200 OK`

```json
{
  "total": 2,
  "successful": 1,
  "failed": 1,
  "errors": [
    {
      "row": 2,
      "error": "customer_email: value is not a valid email address"
    }
  ],
  "tickets": [
    {
      "id": "9f30ee3d-7dc9-48d2-8d9e-4f740198a88a",
      "customer_id": "cust-2001",
      "customer_email": "jordan@example.com",
      "customer_name": "Jordan Lee",
      "subject": "Invoice overcharge",
      "description": "Please review this invoice overcharge.",
      "category": "billing_question",
      "priority": "medium",
      "status": "new",
      "created_at": "2026-07-03T15:15:00.000000",
      "updated_at": "2026-07-03T15:15:00.000000",
      "resolved_at": null,
      "assigned_to": null,
      "tags": ["billing", "invoice"],
      "metadata": {
        "source": "api",
        "browser": null,
        "device_type": null
      },
      "classification": null
    }
  ]
}
```

### Error `400 Bad Request`

```json
{
  "detail": "Unsupported file type 'application/pdf'. Accepted formats: CSV, JSON, XML"
}
```

Other import-level `400` errors include invalid file encoding, invalid JSON syntax, empty JSON arrays, malformed XML, XML with no `<ticket>` elements, and empty CSV files. Row-level validation failures do not reject the full request; they are returned in the `errors` array with `successful` and `failed` counts.

### cURL

CSV:

```bash
curl -X POST "http://localhost:8000/tickets/import?auto_classify=true" \
  -F "file=@sample_tickets.csv;type=text/csv"
```

JSON:

```bash
curl -X POST "http://localhost:8000/tickets/import" \
  -F "file=@sample_tickets.json;type=application/json"
```

XML:

```bash
curl -X POST "http://localhost:8000/tickets/import" \
  -F "file=@sample_tickets.xml;type=application/xml"
```

---

## Data Models And Schemas

### TicketCreate

Used by `POST /tickets`.

| Field | Type | Required | Constraints / default |
| --- | --- | --- | --- |
| `customer_id` | string | Yes | Any non-null string |
| `customer_email` | email string | Yes | Must be a valid email address |
| `customer_name` | string | Yes | Any non-null string |
| `subject` | string | Yes | 1-200 characters |
| `description` | string | Yes | 10-2000 characters |
| `category` | `Category` or `null` | No | Default `null` |
| `priority` | `Priority` or `null` | No | Default `null` |
| `status` | `Status` | No | Default `new` |
| `assigned_to` | string or `null` | No | Default `null` |
| `tags` | string array | No | Default `[]` |
| `metadata` | `TicketMetadata` | No | Default `{ "source": "api" }` |
| `auto_classify` | boolean | No | Default `false` |

### TicketUpdate

Used by `PUT /tickets/{ticket_id}`. Every field is optional.

| Field | Type | Constraints |
| --- | --- | --- |
| `customer_id` | string | Any string |
| `customer_email` | email string | Must be a valid email address |
| `customer_name` | string | Any string |
| `subject` | string | 1-200 characters |
| `description` | string | 10-2000 characters |
| `category` | `Category` | Enum value |
| `priority` | `Priority` | Enum value |
| `status` | `Status` | Enum value |
| `assigned_to` | string or `null` | Any string or null |
| `tags` | string array | Replaces the full tag list |
| `metadata` | `TicketMetadata` | Replaces metadata |
| `resolved_at` | datetime or `null` | ISO 8601 datetime |

### Ticket

Returned by create, list, get, update, and import.

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Generated UUID |
| `customer_id` | string | Customer identifier |
| `customer_email` | string | Customer email |
| `customer_name` | string | Customer display name |
| `subject` | string | Ticket subject |
| `description` | string | Ticket details |
| `category` | `Category` or `null` | Ticket category |
| `priority` | `Priority` or `null` | Ticket priority |
| `status` | `Status` | Ticket status |
| `created_at` | datetime | Server-generated creation time |
| `updated_at` | datetime | Server-generated update time |
| `resolved_at` | datetime or `null` | Set when resolved or closed |
| `assigned_to` | string or `null` | Assignee identifier |
| `tags` | string array | Labels attached to the ticket |
| `metadata` | `TicketMetadata` | Source and client metadata |
| `classification` | `ClassificationResult` or `null` | Stored classifier result |

### TicketMetadata

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `source` | `Source` | `api` | Channel where the ticket originated |
| `browser` | string or `null` | `null` | Browser name/version if known |
| `device_type` | `DeviceType` or `null` | `null` | Client device type |

### ClassificationResult

| Field | Type | Description |
| --- | --- | --- |
| `category` | `Category` | Classified category |
| `priority` | `Priority` | Classified priority |
| `confidence` | number | Score from `0.0` to `1.0` |
| `reasoning` | string | Human-readable classifier explanation |
| `keywords_found` | string array | Keywords used for the decision |
| `classified_at` | datetime | Classification timestamp |
| `manual_override` | boolean | Whether a manual override exists |

### ImportSummary

Returned by `POST /tickets/import`.

| Field | Type | Description |
| --- | --- | --- |
| `total` | integer | Number of parsed records |
| `successful` | integer | Number of tickets created |
| `failed` | integer | Number of records that failed validation |
| `errors` | array | Row-level import errors |
| `tickets` | `Ticket[]` | Created tickets |

### AutoClassifyRequest

Used by `POST /tickets/{ticket_id}/auto-classify`.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `override` | boolean | `false` | Whether to replace an existing classification |

### TicketListResponse

Returned by `GET /tickets`.

| Field | Type | Description |
| --- | --- | --- |
| `total` | integer | Number of tickets in the response |
| `tickets` | `Ticket[]` | Matching tickets |

## Enumerations

### Category

```text
account_access
technical_issue
billing_question
feature_request
bug_report
other
```

### Priority

```text
urgent
high
medium
low
```

### Status

```text
new
in_progress
waiting_customer
resolved
closed
```

### Source

```text
web_form
email
api
chat
phone
```

### DeviceType

```text
desktop
mobile
tablet
```

---

## Error Response Formats

### HTTPException Error

Used for not found resources, unsupported imports, bad file encoding, and file parse errors.

```json
{
  "detail": "Ticket '2bb6c879-5e75-4c6c-84f4-ef52a924a3da' not found"
}
```

### Validation Error `422 Unprocessable Entity`

Returned by FastAPI/Pydantic for invalid request bodies, invalid query enum values, missing required fields, and multipart form validation errors.

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "customer_email"],
      "msg": "Field required",
      "input": {
        "customer_id": "cust-1001",
        "customer_name": "Alex Rivera",
        "subject": "Cannot access account",
        "description": "I cannot access my account after resetting my password."
      }
    }
  ]
}
```

### Import Row Error

Bulk import may return `200 OK` even when some rows fail validation. Per-row failures are reported in `errors`.

```json
{
  "total": 2,
  "successful": 1,
  "failed": 1,
  "errors": [
    {
      "row": 2,
      "error": "customer_email: value is not a valid email address"
    }
  ],
  "tickets": []
}
```

## Status Codes

| Status | Used by | Meaning |
| --- | --- | --- |
| `200 OK` | `GET /health`, `GET /tickets`, `GET /tickets/{ticket_id}`, `PUT /tickets/{ticket_id}`, `POST /tickets/{ticket_id}/auto-classify`, `POST /tickets/import` | Request succeeded |
| `201 Created` | `POST /tickets` | Ticket created |
| `204 No Content` | `DELETE /tickets/{ticket_id}` | Ticket deleted |
| `400 Bad Request` | `POST /tickets/import` | Unsupported file, invalid encoding, or malformed import content |
| `404 Not Found` | Ticket ID endpoints | Ticket does not exist |
| `422 Unprocessable Entity` | JSON body, query, or multipart validation | Invalid field, missing required field, invalid enum, invalid email, or constraint violation |

