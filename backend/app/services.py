from typing import Any

from .errors import DomainError
from .models import (
    DashboardConfig,
    FieldDefinition,
    FieldType,
    SchemaDefinition,
    SummaryView,
    TableView,
)
from .store import InMemoryStore


NUMERIC_TYPES = {FieldType.NUMBER, FieldType.INTEGER}
# Aggregations that require numeric fields.
NUMERIC_AGGREGATIONS = {"sum", "avg", "min", "max"}


def register_schema(store: InMemoryStore, schema: SchemaDefinition) -> SchemaDefinition:
    if schema.name in store.schemas:
        raise DomainError(409, f"Schema '{schema.name}' already exists")

    store.schemas[schema.name] = schema
    return schema


def _matches_type(value: Any, field: FieldDefinition) -> bool:
    if field.type == FieldType.STRING:
        return isinstance(value, str)
    if field.type == FieldType.BOOLEAN:
        return isinstance(value, bool)
    if field.type == FieldType.INTEGER:
        return isinstance(value, int) and not isinstance(value, bool)
    if field.type == FieldType.NUMBER:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return False


def _validate_row(schema: SchemaDefinition, row: dict[str, Any], row_index: int) -> list[dict[str, Any]]:
    field_map = {field.name: field for field in schema.fields}
    errors: list[dict[str, Any]] = []

    unknown_fields = sorted(set(row) - set(field_map))
    for field_name in unknown_fields:
        errors.append(
            {
                "row": row_index,
                "field": field_name,
                "code": "unknown_field",
                "message": f"Unknown field '{field_name}'",
            }
        )

    for field in schema.fields:
        if field.required and field.name not in row:
            errors.append(
                {
                    "row": row_index,
                    "field": field.name,
                    "code": "required_field_missing",
                    "message": f"Required field '{field.name}' is missing",
                }
            )
            continue

        if field.name in row and not _matches_type(row[field.name], field):
            errors.append(
                {
                    "row": row_index,
                    "field": field.name,
                    "code": "type_mismatch",
                    "message": f"Field '{field.name}' must be of type '{field.type.value}'",
                    "actual_type": type(row[field.name]).__name__,
                }
            )

    return errors


def ingest_rows(store: InMemoryStore, schema_name: str, rows: list[dict[str, Any]]) -> int:
    schema = store.schemas.get(schema_name)
    if not schema:
        raise DomainError(404, f"Schema '{schema_name}' does not exist")

    validation_errors: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        validation_errors.extend(_validate_row(schema, row, index))

   # Validate the entire batch before mutating stored state.
    if validation_errors:
        raise DomainError(422, "Row validation failed", validation_errors)

    store.rows[schema_name].extend(rows)
    return len(rows)


def register_dashboard(store: InMemoryStore, config: DashboardConfig) -> DashboardConfig:
    if config.name in store.dashboards:
        raise DomainError(409, f"Dashboard '{config.name}' already exists")

    schema = store.schemas.get(config.schema_name)
    if not schema:
        raise DomainError(404, f"Schema '{config.schema_name}' does not exist")

    field_map = {field.name: field for field in schema.fields}
    errors: list[dict[str, Any]] = []

    for view_index, view in enumerate(config.views):
        if isinstance(view, SummaryView):
            field = field_map.get(view.field)
            if not field:
                errors.append(
                    {
                        "view": view_index,
                        "field": view.field,
                        "code": "unknown_field",
                        "message": f"Summary field '{view.field}' is not defined by schema '{schema.name}'",
                    }
                )
            elif view.aggregation in NUMERIC_AGGREGATIONS and field.type not in NUMERIC_TYPES:
                errors.append(
                    {
                        "view": view_index,
                        "field": view.field,
                        "code": "invalid_aggregation",
                        "message": f"Aggregation '{view.aggregation}' requires a numeric field",
                    }
                )
        elif isinstance(view, TableView):
            for column in view.columns:
                if column not in field_map:
                    errors.append(
                        {
                            "view": view_index,
                            "field": column,
                            "code": "unknown_field",
                            "message": f"Table column '{column}' is not defined by schema '{schema.name}'",
                        }
                    )

    if errors:
        raise DomainError(422, "Dashboard configuration is invalid", errors)

    store.dashboards[config.name] = config
    return config


def _aggregate(values: list[Any], aggregation: str) -> Any:
    if aggregation == "count":
        return len(values)
    if not values:
        return None
    if aggregation == "sum":
        return sum(values)
    if aggregation == "avg":
        return sum(values) / len(values)
    if aggregation == "min":
        return min(values)
    if aggregation == "max":
        return max(values)
    raise ValueError(f"Unsupported aggregation: {aggregation}")


def generate_dashboard(store: InMemoryStore, dashboard_name: str) -> dict[str, Any]:
    config = store.dashboards.get(dashboard_name)
    if not config:
        raise DomainError(404, f"Dashboard '{dashboard_name}' does not exist")

    rows = store.rows[config.schema_name]
    output_views: list[dict[str, Any]] = []

    for view in config.views:
        if isinstance(view, SummaryView):
            values = [row[view.field] for row in rows if view.field in row]
            output_views.append(
                {
                    "type": "summary",
                    "field": view.field,
                    "aggregation": view.aggregation,
                    "value": _aggregate(values, view.aggregation),
                }
            )
        elif isinstance(view, TableView):
            projected_rows = [
                {column: row.get(column) for column in view.columns}
                for row in rows
            ]
            output_views.append(
                {
                    "type": "table",
                    "columns": view.columns,
                    "rows": projected_rows,
                }
            )

    return {
        "name": config.name,
        "schema": config.schema_name,
        "views": output_views,
    }
