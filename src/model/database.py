"""Database access layer.

Wraps the SQLite connection and exposes small helper methods. Only the
``calculation_history`` table is used by this project.
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator, List, Optional

from ..config import Config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS calculation_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    expression  TEXT    NOT NULL,
    result      TEXT    NOT NULL,
    created_at  TEXT    NOT NULL
);
"""


class Database:
    """Thin wrapper around a single SQLite database file."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or Config.DB_PATH

    @property
    def path(self) -> str:
        return self._db_path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Yield a connection that is committed on success."""
        directory = os.path.dirname(self._db_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_schema(self) -> None:
        """Create the table if it does not exist yet."""
        with self.connection() as conn:
            conn.execute(_SCHEMA)

    # -- queries ----------------------------------------------------------
    def insert_history(self, expression: str, result: str, created_at: str) -> int:
        """Insert one record and return its generated id."""
        with self.connection() as conn:
            cursor = conn.execute(
                "INSERT INTO calculation_history (expression, result, created_at) "
                "VALUES (?, ?, ?)",
                (expression, result, created_at),
            )
            return int(cursor.lastrowid)

    def list_history(self, limit: int = 200) -> List[sqlite3.Row]:
        """Return history rows, newest first."""
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT id, expression, result, created_at "
                "FROM calculation_history ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return cursor.fetchall()

    def get_history(self, record_id: int) -> Optional[sqlite3.Row]:
        """Return a single record or ``None``."""
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT id, expression, result, created_at "
                "FROM calculation_history WHERE id = ?",
                (record_id,),
            )
            return cursor.fetchone()

    def delete_history(self, record_id: int) -> bool:
        """Delete one record. Returns ``True`` if a row was removed."""
        with self.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM calculation_history WHERE id = ?", (record_id,)
            )
            return cursor.rowcount > 0

    def clear_history(self) -> int:
        """Delete every record and return the number of removed rows."""
        with self.connection() as conn:
            cursor = conn.execute("DELETE FROM calculation_history")
            return cursor.rowcount
