# Research Notes — context7 Queries

Documentation lookups performed via context7 MCP server during development of the banking pipeline.

---

## Query 1: Python decimal module for monetary arithmetic

- **Search**: "Use context7 to look up the Python decimal module documentation for monetary arithmetic" → `resolve-library-id` for "Python's decimal module documentation"
- **context7 library ID**: first resolve attempt returned no match for the standard-library `decimal` module (only third-party `decimal` packages in Go/Elixir/JS, or unrelated hits) — re-resolved against "Python standard library documentation" instead, which returned `/python/cpython` (official CPython source, 36,847 code snippets, "High" source reputation, benchmark score 81.55) as the correct match, alongside a lower-signal alternative `/websites/python_3`. Used `/python/cpython`.
- **Applied**: Used `decimal.Decimal` throughout `transaction_validator.py` and `fraud_detector.py` for all amount comparisons. Replaced every `float` comparison with `Decimal(str(raw["amount"]))` to avoid IEEE 754 floating-point drift. Applied `Decimal("10000")` as the exact fraud threshold, ensuring `9999.99 < 10000 < 10000.01` comparisons are always correct. The `str()` conversion before `Decimal()` prevents issues when values come in as Python `float` from JSON parsing.

**Key insight**: Always convert via `str()` first — `Decimal(1500.00)` produces `Decimal('1499.9999...')` due to float representation, but `Decimal("1500.00")` is exact. Also: `decimal` has no dedicated context7 library of its own — it's documented as part of the general `/python/cpython` library, so resolving by module name alone can fail and you need to fall back to resolving the parent language/stdlib.

---

## Query 2: FastMCP resource definition and tool registration

- **Search**: "FastMCP resource URI scheme tool decorator Python"
- **context7 library ID**: `/jlowin/fastmcp`
- **Applied**: Used `@mcp.resource("pipeline://summary")` decorator syntax for the resource in `mcp/server.py`. Resources use URI templates and return plain strings (JSON-serialised); tools use `@mcp.tool()` and return dicts. The distinction is important: resources are read-only "data views" while tools are callable "functions". Learned that `fastmcp` wraps the standard `mcp` protocol automatically — no manual JSON-RPC handling needed.

**Key insight**: FastMCP separates concerns cleanly — `@mcp.tool()` for callable actions, `@mcp.resource("uri://...")` for static/computed data views. Both are registered on the same `FastMCP` instance and served over stdio by default, which is what Cursor's MCP client expects.

---

## Query 3: pytest tmp_path fixture for isolating filesystem tests

- **Search**: "pytest tmp_path fixture filesystem isolation"
- **context7 library ID**: `/pytest-dev/pytest`
- **Applied**: Used `tmp_path` (a built-in pytest fixture providing a unique temporary directory per test) in all tests that write to `shared/results/` or `shared/input/`. This ensures tests are independent and leave no side-effects. Example:

```python
def test_process_message_writes_file(tmp_path):
    result_dir = str(tmp_path / "results")
    msg = make_test_message("TXN001", "1500.00", "USD")
    report_msg = process_message(msg, results_dir=result_dir)
    assert (tmp_path / "results" / "TXN001.json").exists()
```

**Key insight**: `tmp_path` is automatically cleaned up after each test and is unique across parallel runs — no manual `setUp`/`tearDown` needed.
