Validate all transactions in sample-transactions.json without running the full pipeline.

Steps:
1. Load `homework-6/sample-transactions.json` and count the total number of records.
2. Run the validator in dry-run mode — import and call `process_message` from
   `agents/transaction_validator.py` on each transaction without writing any files:
   ```python
   from agents.transaction_validator import process_message
   import json, uuid
   from datetime import datetime, timezone

   with open("homework-6/sample-transactions.json") as f:
       transactions = json.load(f)

   results = []
   for txn in transactions:
       msg = {
           "message_id": str(uuid.uuid4()),
           "timestamp": datetime.now(timezone.utc).isoformat(),
           "source_agent": "integrator",
           "target_agent": "transaction_validator",
           "message_type": "transaction",
           "data": txn,
       }
       out = process_message(msg)
       results.append(out["data"])
   ```
3. Report the following statistics:
   - Total count
   - Valid count (status == "validated")
   - Invalid count (status == "rejected")
   - For each rejected transaction: transaction_id, reason code, human message
4. Display a Markdown table with columns: `transaction_id | amount | currency | status | reason`.
5. Do NOT write any files to disk.
