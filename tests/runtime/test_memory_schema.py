import sqlite3

from sona.runtime.memory import SCHEMA_VERSION
from sona.runtime.memory.advanced import SQLiteMemoryStore


def test_schema_initialization_creates_expected_metadata(tmp_path):
    db_path = tmp_path / "memory.db"
    store = SQLiteMemoryStore(db_path)

    store.initialize()

    conn = sqlite3.connect(db_path)
    version = conn.execute(
        "SELECT value FROM schema_meta WHERE key = 'schema_version'"
    ).fetchone()[0]
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    conn.close()

    assert version == SCHEMA_VERSION
    expected = {
        "episodes",
        "claims",
        "facts",
        "procedures",
        "goals",
        "checkpoints",
        "links",
        "receipt_refs",
    }
    assert expected.issubset(tables)
