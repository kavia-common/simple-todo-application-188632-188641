# Todo Backend (FastAPI)

Simple FastAPI service exposing CRUD endpoints for a SQLite-backed Todo list.

Run locally:
- Install deps: pip install -r requirements.txt
- Start server: uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload
- API docs: http://localhost:3001/docs

Notes:
- SQLite database file auto-created at startup at todo_backend/todo.db
- CORS enabled for http://localhost:3000
- Endpoints:
  - GET /todos
  - POST /todos {title}
  - PUT /todos/{id} {title?, completed?}
  - DELETE /todos/{id}
