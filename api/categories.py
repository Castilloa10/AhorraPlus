from api.storage import connect
from contextlib import closing
import sqlite3

CATEGORIES = ("Sin categoría", "Ingresos", "Alimentación", "Suministros")
DEMO_CATEGORIES = {
    "Ingreso ficticio": "Ingresos",
    "Supermercado ficticio": "Alimentación",
    "Internet ficticio": "Suministros",
}


def apply_categories(connection, movements):
    overrides = {}
    if connection.execute("SELECT 1 FROM sqlite_master WHERE name='movement_categories' AND type='table'").fetchone():
        overrides = dict(connection.execute(
            "SELECT external_id, category FROM movement_categories WHERE account=?", ("demo",)
        ))
    for movement in movements:
        movement["category"] = overrides.get(
            movement["id"], DEMO_CATEGORIES.get(movement["description"], "Sin categoría")
        )


def set_category(database, identifier, category):
    if category not in CATEGORIES:
        raise ValueError("Categoría no válida")
    if not database.exists():
        raise LookupError("Movimiento no encontrado")
    with closing(connect(database)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        if not connection.execute("SELECT 1 FROM sqlite_master WHERE name='movements' AND type='table'").fetchone():
            raise LookupError("Movimiento no encontrado")
        if not connection.execute(
            "SELECT 1 FROM movements WHERE account=? AND external_id=?", ("demo", identifier)
        ).fetchone():
            raise LookupError("Movimiento no encontrado")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS movement_categories "
            "(account TEXT, external_id TEXT, category TEXT NOT NULL, PRIMARY KEY(account, external_id))"
        )
        connection.execute(
            "INSERT INTO movement_categories VALUES (?, ?, ?) "
            "ON CONFLICT(account, external_id) DO UPDATE SET category=excluded.category",
            ("demo", identifier, category),
        )

