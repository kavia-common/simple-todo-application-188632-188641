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
- If you serve the frontend from a different origin/port, add that origin to `allow_origins` in `src/api/main.py` to avoid CORS errors.

Endpoints:
- GET /           (health)
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

Integration verification:
1) Health and docs
   - curl http://localhost:3001/        -> {"message":"Healthy"}
   - Open http://localhost:3001/docs    -> Swagger UI loads
2) CRUD quick check
   - Create:
     curl -s -X POST http://localhost:3001/todos -H "Content-Type: application/json" -d '{"title":"Test task"}'
   - List:
     curl -s http://localhost:3001/todos
   - Update first id:
     curl -s -X PUT http://localhost:3001/todos/1 -H "Content-Type: application/json" -d '{"completed": true}'
   - Delete:
     curl -s -X DELETE http://localhost:3001/todos/1 -i
3) Persistence
   - DB file at: simple-todo-application-188632-188641/todo_backend/todo.db
   - Example:
     sqlite3 "simple-todo-application-188632-188641/todo_backend/todo.db" "SELECT COUNT(*) FROM todos;"

Troubleshooting:
- CORS errors in browser console:
  - Ensure frontend origin matches `allow_origins` (default http://localhost:3000).
  - For non-localhost or https origins, add them to `allow_origins`.
- Mixed content (https frontend, http backend):
  - Use both over http in dev, or proxy requests via the frontend dev server.
