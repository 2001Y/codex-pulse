import sqlite3
from pathlib import Path


SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS trigger_runs (
        run_id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        profile_id TEXT NOT NULL,
        occurred_at TEXT NOT NULL,
        output_mode TEXT,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS connector_cursors (
        connector_id TEXT PRIMARY KEY,
        cursor TEXT,
        last_poll_at TEXT,
        last_success_at TEXT,
        last_error TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS source_registry_state (
        registry_id TEXT PRIMARY KEY,
        last_poll_at TEXT,
        last_seen_item_ids TEXT,
        last_promoted_item_ids TEXT,
        authority_tier TEXT,
        notes TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS deliveries (
        delivery_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        destination TEXT NOT NULL,
        delivered_at TEXT NOT NULL,
        status TEXT NOT NULL
    )
    """,
)


def initialize_database(path: str | Path) -> None:
    with sqlite3.connect(Path(path)) as connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        connection.commit()
