from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .errors import DomainError
from .models import DashboardConfig, IngestRequest, SchemaDefinition
from .services import generate_dashboard, ingest_rows, register_dashboard, register_schema
from .store import InMemoryStore

app = FastAPI(title="Schema API Assignment", version="1.0.0")
store = InMemoryStore()

# Convert domain errors into consistent API responses.
@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    body = {"error": exc.message}
    if exc.details is not None:
        body["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content=body)


@app.post("/schema", status_code=201)
def create_schema(schema: SchemaDefinition):
    created = register_schema(store, schema)
    return {"schema": created}


@app.post("/ingest", status_code=201)
def ingest(request: IngestRequest):
    accepted = ingest_rows(store, request.schema_name, request.rows)
    return {"schema": request.schema_name, "accepted": accepted}


@app.post("/dashboard", status_code=201)
def create_dashboard(config: DashboardConfig):
    created = register_dashboard(store, config)
    return {"dashboard": created}


@app.get("/dashboard/{name}")
def get_dashboard(name: str):
    return generate_dashboard(store, name)
