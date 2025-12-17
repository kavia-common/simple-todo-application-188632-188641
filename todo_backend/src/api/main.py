from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import sqlite3
import os
from datetime import datetime

# Database file path (created under backend container directory)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Fallback to a local db file within backend container if database container path is not used
DB_PATH = os.path.join(BASE_DIR, "todo.db")


def _get_conn() -> sqlite3.Connection:
    """
    Create a SQLite connection with row factory as dict-like (tuples converted later).
    Ensures the database file exists.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Ensure foreign keys pragma
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _init_db() -> None:
    """
    Auto-create the SQLite schema on startup. Creates todos table if it doesn't exist.
    """
    conn = _get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


# PUBLIC_INTERFACE
class TodoIn(BaseModel):
    """Payload for creating a new Todo item."""

    title: str = Field(..., description="Title of the todo item")


# PUBLIC_INTERFACE
class TodoUpdate(BaseModel):
    """Payload for updating an existing Todo item."""

    title: Optional[str] = Field(None, description="Updated title of the todo")
    completed: Optional[bool] = Field(None, description="Updated completion status")


# PUBLIC_INTERFACE
class Todo(BaseModel):
    """Todo item representation returned by the API."""

    id: int = Field(..., description="Unique identifier")
    title: str = Field(..., description="Title of the todo item")
    completed: bool = Field(..., description="Whether the todo is completed")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO 8601)")


app = FastAPI(
    title="Todo API",
    description="Simple Todo API with SQLite persistence",
    version="0.1.0",
    openapi_tags=[
        {"name": "health", "description": "Service health and info"},
        {"name": "todos", "description": "Operations on todo items"},
    ],
)

# Restrict CORS to frontend default port as requested
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Initialize database schema on application startup."""
    # Ensure parent dir exists (it should), create DB schema
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    _init_db()


@app.get("/", tags=["health"], summary="Health Check")
def health_check():
    """Return a simple health payload."""
    return {"message": "Healthy"}


def _row_to_todo(row: sqlite3.Row) -> Todo:
    """Convert a sqlite row to Todo model."""
    return Todo(
        id=row["id"],
        title=row["title"],
        completed=bool(row["completed"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# PUBLIC_INTERFACE
@app.get(
    "/todos",
    response_model=List[Todo],
    tags=["todos"],
    summary="List all todos",
    description="Retrieve all todo items.",
)
def list_todos():
    """
    List all todos in the database.

    Returns a JSON array of todos.
    """
    conn = _get_conn()
    try:
        cur = conn.execute("SELECT * FROM todos ORDER BY id DESC")
        rows = cur.fetchall()
        return [_row_to_todo(r) for r in rows]
    finally:
        conn.close()


# PUBLIC_INTERFACE
@app.post(
    "/todos",
    response_model=Todo,
    status_code=status.HTTP_201_CREATED,
    tags=["todos"],
    summary="Create a new todo",
    description="Create a todo with the provided title.",
)
def create_todo(payload: TodoIn):
    """
    Create a new todo item.

    Parameters:
      - payload: JSON body with 'title' (string, required)

    Returns the created todo item.
    """
    # Trim and validate title
    title = (payload.title or "").strip()
    if not title:
        # 422 Unprocessable Entity for empty/whitespace-only title
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Title must not be empty")

    now = datetime.utcnow().isoformat()
    conn = _get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO todos (title, completed, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (title, 0, now, now),
        )
        conn.commit()
        new_id = cur.lastrowid
        cur = conn.execute("SELECT * FROM todos WHERE id = ?", (new_id,))
        row = cur.fetchone()
        return _row_to_todo(row)
    finally:
        conn.close()


# PUBLIC_INTERFACE
@app.put(
    "/todos/{todo_id}",
    response_model=Todo,
    tags=["todos"],
    summary="Update a todo",
    description="Update a todo's title and/or completion status.",
)
def update_todo(todo_id: int, payload: TodoUpdate):
    """
    Update a todo item by ID.

    Parameters:
      - todo_id: Path parameter for the todo id
      - payload: JSON body with optional 'title' and/or 'completed'

    Returns the updated todo item or 404 if not found.
    """
    conn = _get_conn()
    try:
        cur = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        existing = cur.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Todo not found")

        # If title is provided, trim and validate it; otherwise, keep existing title
        if payload.title is not None:
            new_title = (payload.title or "").strip()
            if not new_title:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Title must not be empty")
        else:
            new_title = existing["title"]

        # Handle completed robustly: accept booleans; None means leave as-is
        if payload.completed is not None:
            new_completed = 1 if bool(payload.completed) else 0
        else:
            new_completed = existing["completed"]

        now = datetime.utcnow().isoformat()

        conn.execute(
            "UPDATE todos SET title = ?, completed = ?, updated_at = ? WHERE id = ?",
            (new_title, new_completed, now, todo_id),
        )
        conn.commit()

        cur = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        row = cur.fetchone()
        return _row_to_todo(row)
    finally:
        conn.close()


# PUBLIC_INTERFACE
@app.delete(
    "/todos/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["todos"],
    summary="Delete a todo",
    description="Delete a todo by ID. Returns no content on success.",
)
def delete_todo(todo_id: int):
    """
    Delete a todo by ID.

    Parameters:
      - todo_id: Path parameter for the todo id

    Returns 204 on success or 404 if not found.
    """
    conn = _get_conn()
    try:
        cur = conn.execute("SELECT id FROM todos WHERE id = ?", (todo_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Todo not found")
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        conn.commit()
        return
    finally:
        conn.close()
