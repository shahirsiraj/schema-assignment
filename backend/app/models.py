from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class FieldType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"


class FieldDefinition(StrictModel):
    name: str = Field(min_length=1)
    type: FieldType
    required: bool = False
    aggregation: str | None = None


class SchemaDefinition(StrictModel):
    name: str = Field(min_length=1)
    fields: list[FieldDefinition] = Field(min_length=1)

    @model_validator(mode="after") ##using pydantic's model validator to enforce unique field names for the schemas
    def field_names_must_be_unique(self) -> "SchemaDefinition":
        names = [field.name for field in self.fields]
        if len(names) != len(set(names)):
            raise ValueError("schema field names must be unique")
        return self


class IngestRequest(StrictModel):
    schema_name: str = Field(alias="schema", min_length=1)
    rows: list[dict[str, Any]]


class SummaryView(StrictModel):
    type: Literal["summary"]
    field: str = Field(min_length=1)
    aggregation: Literal["sum", "avg", "min", "max", "count"]


class TableView(StrictModel):
    type: Literal["table"]
    columns: list[str] = Field(min_length=1)


DashboardView = SummaryView | TableView


class DashboardConfig(StrictModel):
    name: str = Field(min_length=1)
    schema_name: str = Field(alias="schema", min_length=1)
    views: list[DashboardView] = Field(min_length=1)
