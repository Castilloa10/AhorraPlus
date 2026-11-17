from api.storage import connect
from contextlib import closing
from datetime import date
import sqlite3

from api.demo import demo_home


def initial_payments():
    return [
        {"id": "demo-" + str(index), "name": item.name, "date": item.scheduled_on.isoformat(),
         "cents": item.cents, "kind": "Irregular" if item.name == "Seguro anual" else "Fijo"}
        for index, item in enumerate(demo_home(include_schedule=True)["schedule"])
        if item.charged_on is None
    ]


def read_payments(database):
    if not database.exists():
        return initial_payments()
    with closing(connect(database)) as connection:
        if not connection.execute("SELECT 1 FROM sqlite_master WHERE name='planned_payments' AND type='table'").fetchone():
            return initial_payments()
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(
            "SELECT id, name, date, cents, kind FROM planned_payments ORDER BY date, id"
        )]


def save_payment(database, identifier, name, scheduled, cents, kind):
    if not name.strip() or len(name.strip()) > 120:
        raise ValueError("Introduce un nombre de hasta 120 caracteres")
    if date.fromisoformat(scheduled).isoformat() != scheduled:
        raise ValueError("Usa una fecha AAAA-MM-DD")
    if type(cents) is not int or not 0 < cents <= 100000000:
        raise ValueError("El importe debe ser mayor que cero y como máximo 1.000.000 €")
    if kind not in ("Fijo", "Irregular"):
        raise ValueError("Tipo de gasto no válido")
    with closing(connect(database)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        if not connection.execute("SELECT 1 FROM sqlite_master WHERE name='planned_payments' AND type='table'").fetchone():
            connection.execute("CREATE TABLE planned_payments (id TEXT PRIMARY KEY, name TEXT, date TEXT, cents INTEGER, kind TEXT)")
            connection.executemany(
                "INSERT INTO planned_payments VALUES (:id, :name, :date, :cents, :kind)", initial_payments()
            )
        connection.execute(
            "INSERT INTO planned_payments VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET name=excluded.name, date=excluded.date, cents=excluded.cents, kind=excluded.kind",
            (identifier, name.strip(), scheduled, cents, kind),
        )

