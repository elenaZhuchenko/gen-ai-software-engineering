# Test Cases List – Homework 2: Intelligent Customer Support System

> **Note:** This document lists all planned test cases. Actual test code lives in `src/tests/`.
> Coverage target: **>85%** overall.

---

## `test_ticket_api` — API Endpoints (11 tests)

| # | Test name | Method + Endpoint | Description | Expected outcome |
|---|-----------|-------------------|-------------|-----------------|
| 1 | `test_create_ticket_success` | POST `/tickets` | Valid payload with all required fields | 201, ticket returned with generated UUID |
| 2 | `test_create_ticket_missing_required_field` | POST `/tickets` | Payload missing `customer_email` | 422 validation error |
| 3 | `test_create_ticket_invalid_email` | POST `/tickets` | `customer_email` = "not-an-email" | 422 with email validation message |
| 4 | `test_create_ticket_auto_classify_flag` | POST `/tickets` | Payload with `auto_classify: true` | 201, `category` and `priority` populated from classifier |
| 5 | `test_get_ticket_by_id_found` | GET `/tickets/{id}` | Existing ticket ID | 200, ticket body matches |
| 6 | `test_get_ticket_by_id_not_found` | GET `/tickets/{id}` | Random UUID that does not exist | 404 |
| 7 | `test_list_tickets_no_filters` | GET `/tickets` | Store has 3 tickets | 200, `total=3` |
| 8 | `test_list_tickets_filter_by_category` | GET `/tickets?category=billing_question` | 5 tickets, 2 of type billing | 200, `total=2` |
| 9 | `test_update_ticket_success` | PUT `/tickets/{id}` | Change `status` to `in_progress` | 200, updated status reflected |
| 10 | `test_update_ticket_not_found` | PUT `/tickets/{id}` | Non-existent ID | 404 |
| 11 | `test_delete_ticket` | DELETE `/tickets/{id}` | Existing ID | 204; subsequent GET returns 404 |

---

## `test_ticket_model` — Data Validation (9 tests)

| # | Test name | What is validated | Description | Expected outcome |
|---|-----------|-------------------|-------------|-----------------|
| 1 | `test_valid_ticket_creation` | `Ticket` model | All fields valid | Model instantiates without errors |
| 2 | `test_subject_too_short` | `TicketCreate` | `subject=""` | `ValidationError` – min_length 1 |
| 3 | `test_subject_too_long` | `TicketCreate` | `subject` = 201-char string | `ValidationError` – max_length 200 |
| 4 | `test_description_too_short` | `TicketCreate` | `description` = 9 chars | `ValidationError` – min_length 10 |
| 5 | `test_description_too_long` | `TicketCreate` | `description` = 2001 chars | `ValidationError` – max_length 2000 |
| 6 | `test_invalid_category_enum` | `TicketCreate` | `category="unknown"` | `ValidationError` – not a valid enum |
| 7 | `test_invalid_priority_enum` | `TicketCreate` | `priority="critical"` | `ValidationError` – not a valid enum |
| 8 | `test_invalid_status_enum` | `TicketCreate` | `status="pending"` | `ValidationError` – not a valid enum |
| 9 | `test_metadata_defaults` | `Ticket` | No metadata provided | `metadata.source` defaults to `api` |

---

## `test_import_csv` — CSV Parsing (6 tests)

| # | Test name | Input | Description | Expected outcome |
|---|-----------|-------|-------------|-----------------|
| 1 | `test_csv_valid_single_row` | 1-row CSV | All required columns present | ImportSummary: total=1, successful=1, failed=0 |
| 2 | `test_csv_valid_multiple_rows` | 5-row CSV | Mix of categories and priorities | total=5, successful=5 |
| 3 | `test_csv_invalid_row_bad_email` | Row with `customer_email=bad` | Second row has invalid email | total=2, successful=1, failed=1; error contains row number |
| 4 | `test_csv_missing_required_column` | CSV missing `subject` | Header row lacks `subject` column | total=N, all rows fail with missing-field error |
| 5 | `test_csv_empty_file` | Empty CSV string | No header, no rows | HTTP 400 – "CSV file is empty" |
| 6 | `test_csv_tags_comma_separated` | Row with `tags="bug,urgent,p1"` | Tags field as comma string | Parsed into list `["bug", "urgent", "p1"]` |

---

## `test_import_json` — JSON Parsing (5 tests)

| # | Test name | Input | Description | Expected outcome |
|---|-----------|-------|-------------|-----------------|
| 1 | `test_json_valid_array` | JSON array of 3 objects | All valid | total=3, successful=3 |
| 2 | `test_json_single_object` | Single JSON object (not array) | Auto-wrapped to list | total=1, successful=1 |
| 3 | `test_json_invalid_syntax` | `"{not: valid json"` | Malformed JSON | HTTP 400 – "Invalid JSON" message |
| 4 | `test_json_empty_array` | `[]` | Zero records | HTTP 400 – "JSON array is empty" |
| 5 | `test_json_partial_failure` | Array of 3; one with bad enum `priority="SUPER"` | Mixed success/fail | total=3, successful=2, failed=1 |

---

## `test_import_xml` — XML Parsing (5 tests)

| # | Test name | Input | Description | Expected outcome |
|---|-----------|-------|-------------|-----------------|
| 1 | `test_xml_valid_single_ticket` | One `<ticket>` element | All required fields present | total=1, successful=1 |
| 2 | `test_xml_valid_multiple_tickets` | Three `<ticket>` elements | All valid | total=3, successful=3 |
| 3 | `test_xml_malformed_syntax` | `<tickets><ticket>unclosed` | Broken XML | HTTP 400 – "Invalid XML" message |
| 4 | `test_xml_no_ticket_elements` | `<data><row>…</row></data>` | Root exists but no `<ticket>` children | HTTP 400 – "no <ticket> elements" |
| 5 | `test_xml_nested_metadata` | Ticket with nested `<metadata><source>email</source></metadata>` | Nested element mapped to dict | `metadata.source` = `email` |

---

## `test_categorization` — Classification Logic (10 tests)

| # | Test name | Input text | Expected category | Expected priority |
|---|-----------|-----------|-------------------|------------------|
| 1 | `test_classify_account_access_by_login_keyword` | subject="Cannot login" | `account_access` | `urgent` (has "can't access" context) |
| 2 | `test_classify_account_access_by_password_keyword` | description contains "forgot password" | `account_access` | `medium` |
| 3 | `test_classify_billing_by_invoice_keyword` | subject="Invoice overcharge" | `billing_question` | `medium` |
| 4 | `test_classify_feature_request` | description has "please add dark mode suggestion" | `feature_request` | `low` |
| 5 | `test_classify_bug_report_with_steps` | description has "steps to reproduce" | `bug_report` | `medium` |
| 6 | `test_classify_urgent_priority` | subject contains "production down" | any | `urgent` |
| 7 | `test_classify_high_priority_blocking` | description has "blocking our release asap" | any | `high` |
| 8 | `test_classify_low_priority_cosmetic` | subject has "cosmetic issue minor" | any | `low` |
| 9 | `test_classify_fallback_other` | Unrecognisable text, no keywords | `other` | `medium` |
| 10 | `test_classify_manual_override_respected` | Ticket with `manual_override=True`, `override=False` | Existing values unchanged | Returns stored classification, no re-run |

---

## `test_integration` — End-to-End Workflows (5 tests)

| # | Test name | Workflow | Description | Expected outcome |
|---|-----------|----------|-------------|-----------------|
| 1 | `test_full_ticket_lifecycle` | Create → GET → Update status → DELETE | Full CRUD round-trip | Each step returns expected status code and body |
| 2 | `test_csv_import_then_auto_classify` | Import CSV with `auto_classify=true` flag | Bulk import triggers classification for every row | All imported tickets have `category` + `priority` set |
| 3 | `test_create_then_filter_by_priority` | Create 5 tickets of varying priorities → GET with priority filter | Filtering by priority returns correct subset | Filtered count matches created count for that priority |
| 4 | `test_manual_override_after_auto_classify` | Auto-classify ticket → PUT to override category | Manual update replaces auto-assigned category | Updated ticket reflects new category, `manual_override=True` |
| 5 | `test_import_mixed_formats_independent` | Separate CSV, JSON, XML imports into same store | All three imports succeed independently | Store contains sum of all successfully imported tickets |

---

## `test_performance` — Benchmarks (5 tests)

| # | Test name | Operation | SLA / threshold | Description |
|---|-----------|-----------|-----------------|-------------|
| 1 | `test_create_100_tickets_under_1s` | POST `/tickets` × 100 sequential | < 1 second total | Baseline single-endpoint throughput |
| 2 | `test_list_1000_tickets_under_500ms` | GET `/tickets` with 1 000 records in store | < 500 ms | List scan scales linearly |
| 3 | `test_csv_import_50_rows_under_2s` | POST `/tickets/import` with 50-row CSV | < 2 seconds | Parsing + validation overhead |
| 4 | `test_classify_1000_tickets_under_1s` | `classify()` called 1 000 times directly | < 1 second | Keyword matching is O(n·m) constant |
| 5 | `test_concurrent_20_creates` | 20 concurrent POST `/tickets` via `asyncio.gather` | All 20 return 201; no data corruption | Thread/async safety of in-memory store |

---

## Fixtures (`tests/fixtures/`)

| File | Format | Records | Notes |
|------|--------|---------|-------|
| `sample_tickets.csv` | CSV | 50 | Mix of all categories, priorities, and statuses |
| `sample_tickets.json` | JSON | 20 | Array of objects; includes nested `metadata` |
| `sample_tickets.xml` | XML | 30 | Standard `<tickets><ticket>…</ticket></tickets>` structure |
| `invalid_emails.csv` | CSV | 5 | All rows have malformed `customer_email` |
| `malformed.json` | JSON | — | Broken JSON syntax (truncated file) |
| `malformed.xml` | XML | — | Unclosed tags / invalid XML structure |
| `empty.csv` | CSV | 0 | Header row only, no data rows |

---

## Coverage Map

| Source module | Covered by |
|---------------|-----------|
| `routers/tickets.py` | test_ticket_api, test_integration |
| `routers/imports.py` | test_import_csv, test_import_json, test_import_xml, test_integration |
| `services/classifier.py` | test_categorization, test_integration |
| `services/importers.py` | test_import_csv, test_import_json, test_import_xml |
| `models.py` | test_ticket_model, all other suites |
| `database.py` | test_ticket_api, test_integration |
