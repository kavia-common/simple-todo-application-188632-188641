# Todo Backend (FastAPI)

Simple FastAPI service exposing CRUD endpoints for a SQLite-backed Todo list.

Run locally:
- Install deps: pip install -r requirements.txt
- Start server: uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload
- API docs: http://localhost:3001/docs

Validation and behavior:
- Title trimming: On POST /todos and PUT /todos/{id}, the `title` is trimmed of whitespace.
- Empty titles are rejected: If the trimmed title is empty (e.g., "   "), the API responds with HTTP 422 and `{"detail": "Title must not be empty"}`.
- Robust booleans: The `completed` field accepts standard boolean values. When omitted on PUT, the existing value is preserved.

CORS:
- CORS is restricted to the frontend at http://localhost:3000

Endpoints:
- GET /todos
- POST /todos
  - body: { "title": "string (required, non-empty after trimming)" }
- PUT /todos/{id}
  - body: { "title"?: "string (non-empty after trimming)", "completed"?: boolean }
- DELETE /todos/{id}

OpenAPI:
- Regenerate the OpenAPI JSON after code changes with:
  - python -m src.api.generate_openapi
- The spec is written to interfaces/openapi.json
- Swagger UI available at /docs
