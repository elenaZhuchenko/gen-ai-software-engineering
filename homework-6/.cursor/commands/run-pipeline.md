Run the multi-agent banking pipeline end-to-end.

Steps:
1. Check that `homework-6/sample-transactions.json` exists; abort with a clear message if missing.
2. Clear the `shared/input/`, `shared/processing/`, and `shared/output/` directories (the integrator does this automatically, but confirm before running).
3. Run the pipeline from the `homework-6/` directory:
   ```
   cd homework-6 && .venv/bin/python integrator.py
   ```
4. Show a summary of results from `shared/results/pipeline-summary.json` — include total, approved, fraud_review, and rejected counts.
5. List all files written to `shared/results/` and their statuses.
6. Report any transactions that were rejected and why (read the `reason` field from each result JSON).
7. If the pipeline exits non-zero, show the full error output and suggest a fix.
