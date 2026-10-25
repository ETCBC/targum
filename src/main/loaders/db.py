import atexit
from contextlib import contextmanager
from typing import Generator, Union

from psycopg import Connection, Cursor
from psycopg_pool import ConnectionPool

from main.config.env import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

try:
    from typing import Self
except ImportError:
    Self = "Database"


class Database:
    """
    PostgreSQL database connection pool manager using the `psycopg_pool` driver.

    This class handles the lifecycle of a connection pool, providing thread-safe
    context managers (`get_cursor` and `transaction`) to safely execute SQL queries
    and manage database transactions in concurrent environments.
    """

    def __init__(self, conn_str: str, min_size: int = 4, max_size: int = 20):
        self.conn_str = conn_str
        self.min_size = min_size
        self.max_size = max_size
        self.pool: ConnectionPool | None = None

    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close_pool(self):
        self.close()

    def connect(self):
        if self.pool is None:
            self.pool = ConnectionPool(
                conninfo=self.conn_str,
                min_size=self.min_size,
                max_size=self.max_size,
                open=True,
            )
        else:
            self.pool.open()

    def close(self):
        """Close the pool and discard the reference, so that the next use builds a fresh one.

        Discarding the reference is the substance of this method. The module-level instance below
        is a singleton, and several modules hold it in a context manager whose exit lands here. A
        connection pool cannot be reopened once it has been closed, and the lazy guards on the
        accessors below all test whether the attribute is set, a condition that a closed pool
        satisfies because a closed pool is still a truthy object. Leaving the attribute in place
        therefore meant that the first module to finish with the singleton closed it for every
        later caller in the same process, and the next request for a connection raised rather
        than reconnecting.

        That cost nothing while each module was its own invocation, which is how all of them had
        previously been run. The consolidated build runs eleven stages in a single process by
        calling each module in turn, so the second stage to require the database was the first to
        pay the cost, and the first authorised run of that build failed partway through for this
        reason.
        """
        if self.pool is not None:
            self.pool.close()
            self.pool = None

    def flush(self, resource: Union[Connection, Cursor]):
        if hasattr(resource, "commit"):
            resource.commit()
        elif hasattr(resource, "connection"):
            resource.connection.commit()

    @contextmanager
    def get_connection(self) -> Generator[Connection, None, None]:
        """Yields a connection from the pool."""
        if not self.pool:
            self.connect()
        with self.pool.connection() as conn:
            yield conn

    @contextmanager
    def get_cursor(self) -> Generator[Cursor, None, None]:
        """Yields a cursor from a pooled connection."""
        if not self.pool:
            self.connect()
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                yield cur

    @contextmanager
    def transaction(self) -> Generator[Connection, None, None]:
        """Yields a pooled connection wrapped in a transaction block."""
        if not self.pool:
            self.connect()
        with self.pool.connection() as conn:
            with conn.transaction():
                yield conn


db = Database(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
atexit.register(db.close_pool)
