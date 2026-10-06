from collections import defaultdict

from .models import DashboardConfig, SchemaDefinition


class InMemoryStore:
    def __init__(self) -> None:
        self.schemas: dict[str, SchemaDefinition] = {}
        self.rows: dict[str, list[dict]] = defaultdict(list)
        self.dashboards: dict[str, DashboardConfig] = {}
