from api.storage import connect
from contextlib import closing
from datetime import date
import re
import sqlite3

from api.categories import CATEGORIES

EXPENSE_CATEGORIES = tuple(category for category in CATEGORIES if category != "Ingresos")


def save_budget(database, month, category, limit_cents):
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        raise ValueError("Mes no válido")
    date.fromisoformat(month + "-01")
    if category not in EXPENSE_CATEGORIES:
        raise ValueError("Categoría de gasto no válida")
    if type(limit_cents) is not int or not 0 <= limit_cents <= 100000000:
        raise ValueError("El límite debe estar entre 0 y 1.000.000 €")
    with closing(connect(database)) as connection, connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS budgets "
            "(account TEXT, month TEXT, category TEXT, limit_cents INTEGER NOT NULL, "
            "PRIMARY KEY(account, month, category))"
        )
        connection.execute(
            "INSERT INTO budgets VALUES (?, ?, ?, ?) "
            "ON CONFLICT(account, month, category) DO UPDATE SET limit_cents=excluded.limit_cents",
            ("demo", month, category, limit_cents),
        )


def budget_summary(database, month, movements):
    limits = {}
    if database.exists():
        with closing(connect(database)) as connection:
            if connection.execute("SELECT 1 FROM sqlite_master WHERE name='budgets' AND type='table'").fetchone():
                limits = dict(connection.execute(
                    "SELECT category, limit_cents FROM budgets WHERE account=? AND month=?",
                    ("demo", month),
                ))
    result = []
    for category in EXPENSE_CATEGORIES:
        spent = max(0, -sum(
            movement["cents"] for movement in movements
            if movement["date"][:7] == month and movement["category"] == category
        ))
        limit = limits.get(category)
        result.append({
            "category": category, "limit_cents": limit, "spent_cents": spent,
            "remaining_cents": None if limit is None else limit - spent,
        })
    return result

