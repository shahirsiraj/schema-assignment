# Schema-Driven Dashboard Platform

A lightweight, configuration-driven backend built with **Python and FastAPI**.

The platform allows clients to:

- Register arbitrary data schemas
- Ingest and validate rows against registered schemas
- Register dashboard configurations
- Generate dashboard-ready summary and table data

All state is stored in memory, as persistence is outside the scope of the assignment.

---

## Technology

- Python 3.10+
- FastAPI
- Pydantic v2
- Uvicorn
- Pytest
- HTTPX

---

## Project Structure

```text
.
├── README.md
├── AI_REPORT.md
└── backend/
    ├── requirements.txt
    ├── pytest.ini
    ├── app/
    │   ├── __init__.py
    │   ├── errors.py
    │   ├── main.py
    │   ├── models.py
    │   ├── services.py
    │   └── store.py
    └── tests/
        └── test_api.py
```

The backend is intentionally small:

- `main.py` - FastAPI routes and HTTP error handling
- `models.py` - Pydantic request/configuration models
- `services.py` - schema validation, ingestion, and dashboard generation logic
- `store.py` - in-memory application state
- `errors.py` - domain error representation
- `tests/` - API-level tests covering the main platform behavior

---

## Design Overview

The platform is intentionally **schema-driven** rather than being tied to a specific domain such as trades or customers.

For example, the same backend can support:

```text
Trade
├── tradeId
├── amount
└── status
```

or:

```text
Customer
├── customerId
├── name
└── country
```

without requiring new backend logic for each use case.

### Dashboard-to-schema relationship

The assignment leaves the dashboard configuration format flexible.

I made one relationship explicit: every dashboard configuration contains a `schema` property identifying the registered dataset it reads from.

For example:

```json
{
  "name": "trade-dashboard",
  "schema": "trade",
  "views": []
}
```

This avoids deriving the source schema from a dashboard naming convention and allows dashboard references to be validated when the dashboard is registered.

### Validation model

Validation is split into two layers:

1. **API / structural validation**

   Pydantic validates the structure of schema, ingestion, and dashboard requests.

2. **Runtime domain validation**

   Ingested rows are validated against schemas previously registered through the API. These schemas are dynamic application data and therefore cannot be represented by a single statically defined Python model.

Runtime ingestion validation checks:

- Required fields
- Field data types
- Unknown fields

Unexpected properties on API configuration models are also rejected.

### Atomic ingestion

Ingestion uses **request-level atomic semantics**.

All rows in an ingestion request are validated before application state is modified.

If any row fails validation:

```text
validate all rows
        |
        v
validation error found
        |
        v
store nothing
```

If every row succeeds:

```text
validate all rows
        |
        v
all valid
        |
        v
store entire batch
```

Validation errors include the affected row index, field, and machine-readable error code.

---

## Supported Field Types

Schemas currently support:

- `string`
- `number`
- `integer`
- `boolean`

Example field definition:

```json
{
  "name": "amount",
  "type": "number",
  "required": true
}
```

---

## Supported Dashboard Views

### Summary

Produces an aggregated value for a field.

Supported aggregations:

- `sum`
- `avg`
- `min`
- `max`
- `count`

Example:

```json
{
  "type": "summary",
  "field": "amount",
  "aggregation": "sum"
}
```

### Table

Projects selected fields from ingested rows.

Example:

```json
{
  "type": "table",
  "columns": ["tradeId", "amount", "status"]
}
```

---

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/schema` | Register a data schema |
| `POST` | `/ingest` | Validate and ingest rows |
| `POST` | `/dashboard` | Register a dashboard configuration |
| `GET` | `/dashboard/{name}` | Generate dashboard data |

---

## Setup and Run

### 1. Enter the backend directory

```bash
cd backend
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 5. Start the API

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI interactive documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

## Example Flow

### 1. Register a schema

`POST /schema`

```json
{
  "name": "trade",
  "fields": [
    {
      "name": "tradeId",
      "type": "string",
      "required": true
    },
    {
      "name": "amount",
      "type": "number",
      "required": true
    },
    {
      "name": "status",
      "type": "string"
    }
  ]
}
```

---

### 2. Ingest data

`POST /ingest`

```json
{
  "schema": "trade",
  "rows": [
    {
      "tradeId": "T001",
      "amount": 1000,
      "status": "OPEN"
    },
    {
      "tradeId": "T002",
      "amount": 1500,
      "status": "CLOSED"
    }
  ]
}
```

Example response:

```json
{
  "schema": "trade",
  "accepted": 2
}
```

---

### 3. Register a dashboard

`POST /dashboard`

```json
{
  "name": "trade-dashboard",
  "schema": "trade",
  "views": [
    {
      "type": "summary",
      "field": "amount",
      "aggregation": "sum"
    },
    {
      "type": "table",
      "columns": [
        "tradeId",
        "amount",
        "status"
      ]
    }
  ]
}
```

---

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
      "columns": [
        "tradeId",
        "amount",
        "status"
      ],
      "rows": [
        {
          "tradeId": "T001",
          "amount": 1000,
          "status": "OPEN"
        },
        {
          "tradeId": "T002",
          "amount": 1500,
          "status": "CLOSED"
        }
      ]
    }
  ]
}
```

---

## Running Tests

From the `backend` directory:

```bash
python -m pytest -q
```

The test suite covers the main end-to-end flow and important validation behavior, including:

- Successful schema -> ingestion -> dashboard generation flow
- Missing required fields
- Unknown fields
- Type mismatches
- Numeric aggregation validation
- Duplicate schema registration
- Missing referenced schemas
- Atomic ingestion behavior

---

## Assumptions and Design Decisions

### Duplicate names

Duplicate schema and dashboard names return:

```text
409 Conflict
```

rather than silently replacing existing definitions.

Allowing schemas to be overwritten after rows have already been ingested would introduce consistency and schema-migration concerns that are outside the scope of this implementation.

### Numeric aggregation

`sum`, `avg`, `min`, and `max` are only valid for `number` or `integer` fields.

`count` can be used with any supported field type.

### Missing optional values

Summary aggregations operate only on rows containing the configured field.

For an optional field, `count(field)` therefore counts rows where that field is present rather than all rows.

### Empty aggregations

When no values exist:

- `count` returns `0`
- `sum`, `avg`, `min`, and `max` return `null`

This is an explicit API-contract decision and can be changed if different product semantics are required.

### In-memory storage

State is intentionally stored in process memory.

As a result:

- Data is lost when the application restarts
- Multiple Uvicorn worker processes would not share state
- The implementation is not intended to provide production persistence

This matches the scope of the assignment.

---

## Potential Extensions

If the platform were extended beyond the scope of this exercise, possible next steps include:

- Schema versioning and migration rules
- Additional schema constraints such as `enum`, ranges, formats, and nullable fields
- Dashboard filtering, grouping, sorting, and pagination
- Persistent storage behind a repository/data-access layer
- Standardized API error models
- Authentication and authorization
- Idempotency controls for ingestion
- Production observability and deployment configuration

These features were intentionally excluded from the time-boxed implementation to keep the solution focused on the requirements of the assignment.

---

## AI Usage

AI-assisted development was permitted for this assignment.

Details of how AI tools were used, including accepted and rejected suggestions and how the implementation was validated, are documented in:

```text
AI_REPORT.md
```
