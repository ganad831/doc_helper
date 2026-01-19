"""SQLite connection management."""

import sqlite3
from pathlib import Path
from typing import Optional


class SqliteConnection:
    """Manages SQLite database connections.

    Provides context manager support for automatic connection cleanup
    and transaction management.

    Example:
        with SqliteConnection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")
            results = cursor.fetchall()
    """

    def __init__(self, db_path: str | Path) -> None:
        """Initialize SQLite connection.

        Args:
            db_path: Path to SQLite database file
        """
        if not isinstance(db_path, (str, Path)):
            raise TypeError("db_path must be a string or Path")

        self.db_path = Path(db_path)
        self._connection: Optional[sqlite3.Connection] = None

    def __enter__(self) -> sqlite3.Connection:
        """Enter context manager.

        Returns:
            Active SQLite connection
        """
        if self._connection is not None:
            raise RuntimeError("Connection already open")

        self._connection = sqlite3.connect(str(self.db_path))
        self._connection.row_factory = sqlite3.Row  # Enable dict-like access
        return self._connection

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager.

        Commits transaction if no exception, rolls back otherwise.
        """
        if self._connection is None:
            return

        try:
            if exc_type is None:
                self._connection.commit()
            else:
                self._connection.rollback()
        finally:
            self._connection.close()
            self._connection = None

    @property
    def exists(self) -> bool:
        """Check if database file exists.

        Returns:
            True if database file exists
        """
        return self.db_path.exists()

    def ensure_exists(self) -> None:
        """Ensure database file exists.

        Creates parent directories if needed.

        Raises:
            FileNotFoundError: If database file does not exist
        """
        if not self.exists:
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
