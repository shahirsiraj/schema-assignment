import pytest
from fastapi.testclient import TestClient

from app.main import app, store


@pytest.fixture(autouse=True)
def reset_store():
    store.schemas.clear()
    store.rows.clear()
    store.dashboards.clear()


@pytest.fixture
def client():
    return TestClient(app)


def trade_schema():
    return {
        "name": "trade",
        "fields": [
            {"name": "tradeId", "type": "string", "required": True},
            {"name": "amount", "type": "number", "required": True},
            {"name": "status", "type": "string"},
        ],
    }


def register_trade(client):
    response = client.post("/schema", json=trade_schema())
    assert response.status_code == 201


def test_happy_path_generates_summary_and_table(client):
    register_trade(client)
    ingest = client.post(
        "/ingest",
        json={
            "schema": "trade",
            "rows": [
                {"tradeId": "T001", "amount": 1000, "status": "OPEN"},
                {"tradeId": "T002", "amount": 1500, "status": "CLOSED"},
            ],
        },
    )
    assert ingest.status_code == 201

    dashboard = client.post(
        "/dashboard",
        json={
            "name": "trade-dashboard",
            "schema": "trade",
            "views": [
                {"type": "summary", "field": "amount", "aggregation": "sum"},
                {"type": "table", "columns": ["tradeId", "amount", "status"]},
            ],
        },
    )
    assert dashboard.status_code == 201

    result = client.get("/dashboard/trade-dashboard")
    assert result.status_code == 200
    payload = result.json()
    assert payload["views"][0]["value"] == 2500
    assert payload["views"][1]["rows"][0] == {
        "tradeId": "T001",
        "amount": 1000,
        "status": "OPEN",
    }


def test_ingest_rejects_missing_required_field_and_is_atomic(client):
    register_trade(client)
    response = client.post(
        "/ingest",
        json={
            "schema": "trade",
            "rows": [
                {"tradeId": "T001", "amount": 1000},
                {"tradeId": "T002"},
            ],
        },
    )
    assert response.status_code == 422
    assert response.json()["details"][0]["code"] == "required_field_missing"
    assert store.rows["trade"] == []


def test_ingest_rejects_unknown_fields(client):
    register_trade(client)
    response = client.post(
        "/ingest",
        json={
            "schema": "trade",
            "rows": [{"tradeId": "T001", "amount": 1000, "desk": "FX"}],
        },
    )
    assert response.status_code == 422
    assert response.json()["details"][0]["code"] == "unknown_field"


def test_ingest_rejects_boolean_as_number(client):
    register_trade(client)
    response = client.post(
        "/ingest",
        json={"schema": "trade", "rows": [{"tradeId": "T001", "amount": True}]},
    )
    assert response.status_code == 422
    assert response.json()["details"][0]["code"] == "type_mismatch"


def test_dashboard_rejects_numeric_aggregation_on_string_field(client):
    register_trade(client)
    response = client.post(
        "/dashboard",
        json={
            "name": "bad-dashboard",
            "schema": "trade",
            "views": [{"type": "summary", "field": "status", "aggregation": "sum"}],
        },
    )
    assert response.status_code == 422
    assert response.json()["details"][0]["code"] == "invalid_aggregation"


def test_duplicate_schema_returns_conflict(client):
    register_trade(client)
    response = client.post("/schema", json=trade_schema())
    assert response.status_code == 409


def test_dashboard_requires_registered_schema(client):
    response = client.post(
        "/dashboard",
        json={
            "name": "trade-dashboard",
            "schema": "missing",
            "views": [{"type": "summary", "field": "amount", "aggregation": "sum"}],
        },
    )
    assert response.status_code == 404
    assert response.json()["error"] == "Schema 'missing' does not exist"
