# How to Run

## Prerequisites

- Node.js 18 or higher ([nodejs.org](https://nodejs.org))
- npm (comes with Node.js)

## Installation

```bash
cd homework-1
npm install
```

## Start the server

```bash
npm start
```

The API will be available at `http://localhost:3000`.

To use a different port:

```bash
PORT=8080 npm start
```

## Run tests

```bash
# All tests
npm test

# Unit tests only (validators, store)
npm run test:unit

# API integration tests only
npm run test:api
```

## Quick health check

```bash
curl http://localhost:3000/health
# {"status":"ok"}
```

## Demo requests

See `demo/sample-requests.http` for ready-to-use HTTP requests, or run:

```bash
bash demo/run.sh
```
