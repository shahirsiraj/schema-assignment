# Schema API Assignment - FastAPI

A small in-memory backend for registering data schemas, validating ingested rows, registering dashboard configurations, and generating dashboard-ready data.

## Why this design

The assignment intentionally leaves the configuration format flexible. I made one relationship explicit: each dashboard configuration contains a `schema` property identifying the dataset it reads from. This avoids inferring the source schema from the dashboard name and allows dashboard configuration to be validated when it is registered.

Validation is split into two layers:

- **API/request validation** - Pydantic validates the shape of schema, ingest, and dashboard requests.
- **Runtime domain validation** - ingested rows are checked against the schema registered by the user because that schema is dynamic data rather than a statically known Python model.

Ingestion uses **atomic batch semantics**: all rows are validated first; if any row fails, no rows from that request are stored. Errors include the row index, field, and error code.

## Supported field types

- `string`
- `number`
- `integer`
- `boolean`

## Supported dashboard views

- `summary` with `sum`, `avg`, `min`, `max`, or `count`
- `table` with selected columns

## Run

cd backend

python -m venv .venv

# Windows PowerShell

.\.venv\Scripts\Activate.ps1

# macOS/Linux

# source .venv/bin/activate

python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload

FastAPI exposes interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

## Test

cd backend
python -m pytest -q

The tests cover the end-to-end happy path and important validation behavior, including required fields, unknown fields, type mismatches, invalid aggregations, duplicate schemas, missing schemas, and atomic ingestion.

## Example flow

### 1. Register a schema

`POST /schema`

```json
{
  "name": "trade",
  "fields": [
    { "name": "tradeId", "type": "string", "required": true },
    { "name": "amount", "type": "number", "required": true },
    { "name": "status", "type": "string" }
  ]
}
```

### 2. Ingest data

`POST /ingest`

```json
{
  "schema": "trade",
  "rows": [
    { "tradeId": "T001", "amount": 1000, "status": "OPEN" },
    { "tradeId": "T002", "amount": 1500, "status": "CLOSED" }
  ]
}
```

### 3. Register a dashboard

`POST /dashboard`

```json
{
  "name": "trade-dashboard",
  "schema": "trade",
  "views": [
    { "type": "summary", "field": "amount", "aggregation": "sum" },
    { "type": "table", "columns": ["tradeId", "amount", "status"] }
  ]
}
```

### 4. Generate dashboard data

`GET /dashboard/trade-dashboard`

Example response:

```json
{
  "name": "trade-dashboard",
  "schema": "trade",
  "views": [
    {
      "type": "summary",
      "field": "amount",
      "aggregation": "sum",
      "value": 2500
    },
    {
      "type": "table",
      "columns": ["tradeId", "amount", "status"],
      "rows": [
        { "tradeId": "T001", "amount": 1000, "status": "OPEN" },
        { "tradeId": "T002", "amount": 1500, "status": "CLOSED" }
      ]
    }
  ]
}
```

## Assumptions and deliberate choices

- Duplicate schema and dashboard names return `409 Conflict` rather than silently overwriting existing definitions.
- Numeric aggregations are only allowed on `number` or `integer` fields; `count` can be used for any field type.
- Empty summary inputs return `null` for `sum`, `avg`, `min`, and `max`; `count` returns `0`. This is an API-contract choice and could be changed if product requirements specify different semantics.
- In-memory state is process-local and intentionally not production-safe. Multiple workers would not share data and restarts lose state; persistence is outside the assignment scope.

## If extending this further

The next features I would consider are schema versioning, richer field constraints (`enum`, ranges, nullable), dashboard filters/grouping/sorting/pagination, and a persistence-backed repository. I would not add those to the time-boxed submission unless specifically requested.
