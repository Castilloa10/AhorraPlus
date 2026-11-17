from contextlib import closing

from api.storage import connect


def store_secret(database, name, value):
    """Server-only vault for future provider keys and sessions."""
    if name not in ("provider_private_key", "bank_session") or not value:
        raise ValueError("Secreto no válido")
    with closing(connect(database)) as connection, connection:
        connection.execute("CREATE TABLE IF NOT EXISTS local_secrets (name TEXT PRIMARY KEY, value TEXT NOT NULL)")
        connection.execute(
            "INSERT INTO local_secrets VALUES (?, ?) ON CONFLICT(name) DO UPDATE SET value=excluded.value",
            (name, value),
        )


def load_secret(database, name):
    if not database.exists():
        return None
    with closing(connect(database)) as connection:
        if not connection.execute("SELECT 1 FROM sqlite_master WHERE name='local_secrets'").fetchone():
            return None
        row = connection.execute("SELECT value FROM local_secrets WHERE name=?", (name,)).fetchone()
        return row[0] if row else None


def disconnect_local(database):
    if database.exists():
        with closing(connect(database)) as connection, connection:
            if connection.execute("SELECT 1 FROM sqlite_master WHERE name='local_secrets'").fetchone():
                connection.execute("DELETE FROM local_secrets")


def delete_imported(database, confirmation):
    if confirmation != "BORRAR DEMO":
        raise ValueError("Escribe BORRAR DEMO para confirmar")
    if not database.exists():
        return
    with closing(connect(database)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        for table in ("movements", "batches", "movement_categories"):
            if connection.execute("SELECT 1 FROM sqlite_master WHERE name=?", (table,)).fetchone():
                connection.execute(f"DELETE FROM {table} WHERE account=?", ("demo",))
