# Security Report — Expense Tracker (Run 001)

## Executive Summary
After the Bug Fixer's changes, the application's security posture is **good**. The
single previously-CRITICAL issue — SEC-001 arbitrary code execution via `eval()` —
is fully resolved and replaced with safe `float()` parsing plus finite/non-negative
validation. Reviewing `src/expense_tracker.py` and `src/main.py` in full surfaced
**no CRITICAL and no HIGH** findings. Remaining items are **2 LOW** (terminal-escape
output injection, uncaught-exception traceback disclosure) and **3 INFO**
(missing length bounds, unpinned dependencies, and a CLI/XSS forward-looking note),
plus **1 resolved** confirmation. Total: 0 CRITICAL / 0 HIGH / 0 MEDIUM / 2 LOW / 3 INFO / 1 RESOLVED.

## Findings

### [RESOLVED] FINDING-001: SEC-001 `eval()` arbitrary code execution — FIXED
- **Severity**: INFO (resolved; was CRITICAL pre-fix)
- **File**: `src/expense_tracker.py`
- **Line**: 39–47
- **Category**: Injection
- **Description**: The original `add_expense()` converted the user-supplied `amount`
  string with `eval(amount)`, allowing arbitrary Python execution (e.g.
  `__import__('os').system(...)`). The Bug Fixer replaced this with `float()` inside a
  `try/except` that raises `ValueError`, followed by an explicit finite/non-negative
  check. This closes the RCE vector.
- **Code**:
  ```python
  # SEC-001 FIX: safe numeric conversion instead of eval()
  try:
      value = float(amount)
  except (ValueError, TypeError) as exc:
      raise ValueError(
          f"Invalid amount {amount!r}: must be a numeric value (e.g. '9.99')."
      ) from exc

  if not math.isfinite(value) or value < 0:
      raise ValueError(f"Amount must be a finite non-negative number, got {value}.")
  ```
- **Impact**: None remaining. Confirmed resolved; corroborated by passing tests
  `test_add_expense_code_injection_is_rejected` and the `TestAddExpenseSec001Fix`
  suite (exec/import payloads rejected). `float()` also cannot be tricked into code
  execution, and `math.isfinite()` rejects `nan`/`inf` payloads.
- **Remediation**: No action required. Keep the `float()` + `math.isfinite()` guard;
  do not reintroduce `eval`/`exec` for parsing user input.

### [LOW] FINDING-002: Terminal escape-sequence injection via unsanitized output
- **Severity**: LOW
- **File**: `src/main.py`
- **Line**: 57–60 (add echo), 70–74 (list echo)
- **Category**: Missing Input Validation / Information Disclosure (CLI output)
- **Description**: `category` and `description` are stored verbatim (only
  emptiness/whitespace of `category` is checked) and later written directly to the
  terminal via `print()`. Neither field is sanitized for ANSI/control characters. A
  crafted value containing escape sequences (e.g. `\x1b[2J`, cursor-move, or color
  codes) is emitted unmodified when a user runs `list`, allowing terminal
  manipulation (screen clearing, spoofed output, misleading formatting).
- **Code**:
  ```python
  for e in expenses:
      print(
          f"  #{e['id']:>3} | {e['category']:<12} | "
          f"${e['amount']:>8.2f} | {e['description']}"
      )
  ```
- **Impact**: A malicious record could obscure or spoof CLI output for a local
  operator; limited to the terminal session, no code execution or data loss.
- **Remediation**: Strip or escape control characters before display. For example,
  filter with `"".join(ch for ch in value if ch.isprintable())` when reading input in
  the `add` branch, or sanitize at print time (e.g.
  `value.encode("unicode_escape").decode("ascii")`). Apply to both `category` and
  `description`.

### [LOW] FINDING-003: Uncaught non-`ValueError` exceptions leak tracebacks to CLI
- **Severity**: LOW
- **File**: `src/main.py`
- **Line**: 61–62 (narrow `except`), 64–80 (`list`/`total` have no guard)
- **Category**: Information Disclosure
- **Description**: The `add` handler catches only `ValueError`; `list` and `total`
  catch nothing. Any unexpected exception propagates to the top level and Python
  prints a full stack trace (file paths, internal function names, line numbers) to the
  console. While the current logic only raises `ValueError`, the narrow handling is
  fragile — a future change or unforeseen runtime error would expose internals.
- **Code**:
  ```python
  except ValueError as exc:
      print(f"  Error: {exc}")
  ```
- **Impact**: Local disclosure of internal paths/structure; low likelihood given
  current code paths, no direct compromise.
- **Remediation**: Wrap each command dispatch in a broad guard that prints a concise
  message and suppresses the traceback, e.g.
  `except Exception as exc: print(f"  Error: {exc}")` (or a generic
  "unexpected error" message), while logging full details separately if needed.

### [INFO] FINDING-004: No length/size bounds on `category` and `description`
- **Severity**: INFO
- **File**: `src/expense_tracker.py`
- **Line**: 49–57
- **Category**: Missing Input Validation
- **Description**: `category` is checked only for non-emptiness; `description` is
  unchecked. There are no maximum-length or size limits, and `main.py` reads input via
  `input()` with no bound. Unbounded strings could accumulate in the in-memory
  `EXPENSES` store (memory pressure) or distort the fixed-width display formatting.
- **Code**:
  ```python
  if not category or not category.strip():
      raise ValueError("Category must be a non-empty string.")

  expense: dict = {
      "id": _next_id,
      "category": category,
      "amount": value,
      "description": description,
  }
  ```
- **Impact**: Minor local resource/usability concern; not remotely exploitable.
- **Remediation**: Enforce reasonable maximum lengths, e.g.
  `if len(category) > 64: raise ValueError(...)` and a similar bound (e.g. 256) for
  `description`; optionally `strip()` stored values.

### [INFO] FINDING-005: Unpinned dependency versions (supply-chain hygiene)
- **Severity**: INFO
- **File**: `requirements.txt`
- **Line**: 2–7
- **Category**: Unsafe Dependencies
- **Description**: All dependencies use open-ended `>=` ranges
  (`cursor-sdk>=1.0.24`, `PyYAML>=6.0`, `pytest>=7.4`, `pytest-cov>=4.1`). No
  currently-pinned known-vulnerable versions were found, and `PyYAML>=6.0` avoids the
  legacy unsafe-default `yaml.load` issue. However, unpinned ranges allow future
  installs to silently pull in a compromised or breaking release. Note `PyYAML` is not
  imported anywhere under `src/`.
- **Code**:
  ```text
  cursor-sdk>=1.0.24
  PyYAML>=6.0
  pytest>=7.4
  pytest-cov>=4.1
  ```
- **Impact**: Potential future exposure to a vulnerable transitive/direct release; no
  present vulnerability.
- **Remediation**: Pin exact versions (`==`) or use a lockfile
  (`pip-compile`/`requirements.lock`), enable dependency scanning (e.g. `pip-audit`),
  and remove unused runtime deps (`PyYAML`) if not needed by the app.

### [INFO] FINDING-006: XSS/CSRF not applicable to CLI — guidance for future web surface
- **Severity**: INFO
- **File**: `src/main.py`, `src/expense_tracker.py`
- **Line**: N/A
- **Category**: XSS / CSRF
- **Description**: The application is a local interactive CLI with no HTTP surface, so
  XSS and CSRF do not currently apply. The stored `category`/`description` values are,
  however, untrusted free-text (see FINDING-002/004). If these are ever rendered in a
  web UI or API response, they become an XSS vector.
- **Impact**: None today; forward-looking note.
- **Remediation**: If a web/API surface is added, HTML-escape all stored fields on
  output (or use an auto-escaping template engine), set appropriate response
  `Content-Type`, and add CSRF protection (tokens/SameSite cookies) for state-changing
  endpoints.

## Verdict
PASS — No CRITICAL or HIGH findings. The former CRITICAL (SEC-001 `eval()`) is
confirmed resolved. Remaining items are 2 LOW and 3 INFO, none blocking.

## References
- Fix summary: `context/bugs/001/fix-summary.md`
- Files reviewed: `src/expense_tracker.py`, `src/main.py`
- Supporting: `requirements.txt`, `src/__init__.py`, test evidence in `fix-summary.md`
