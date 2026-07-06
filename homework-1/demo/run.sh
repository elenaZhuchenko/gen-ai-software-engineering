#!/usr/bin/env bash
set -e

BASE="http://localhost:3000"

# Start the server from the project root and stop it when this script exits
cd "$(dirname "$0")/.."
npm install --silent
npm start &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null' EXIT

# Wait until the server is ready
for i in $(seq 1 10); do
  if curl -sf "$BASE/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

echo "=== Health check ==="
curl -s "$BASE/health"
echo

echo "=== Create deposit ==="
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-12345","amount":1000,"currency":"USD","type":"deposit"}'
echo

echo "=== Create transfer ==="
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-12345","toAccount":"ACC-67890","amount":250.50,"currency":"USD","type":"transfer"}'
echo

echo "=== List all transactions ==="
curl -s "$BASE/transactions"
echo

echo "=== Account balance ==="
curl -s "$BASE/accounts/ACC-12345/balance"
echo

echo "=== Account summary ==="
curl -s "$BASE/accounts/ACC-12345/summary"
echo
