from api.storage import connect
import sqlite3
from contextlib import closing
from pathlib import Path
from datetime import date

from api.demo import demo_home
from api.categories import CATEGORIES, apply_categories
from api.budgets import budget_summary
from api.planned_payments import read_payments
from api.finance import Commitment, summarize

DATABASE = Path(__file__).resolve().parents[1] / "demo-import.sqlite3"


def imported_home(database=DATABASE):
    summary = demo_home()
    movements = []
    if database.exists():
        with closing(connect(database)) as connection:
            if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='movements'").fetchone():
                movements = [
                    {"id": identifier, "date": charged, "description": description, "cents": cents}
                    for identifier, charged, description, cents in connection.execute(
                        "SELECT external_id, charged_on, description, cents FROM movements "
                        "WHERE account = ? AND charged_on <= ? ORDER BY charged_on DESC, external_id",
                        ("demo", summary["as_of"]),
                    )
                ]
                apply_categories(connection, movements)
    summary["categories"] = CATEGORIES
    balance = sum(row["cents"] for row in movements)
    summary["accounts"].append({"name": "Cuenta DEMO importada", "cents": balance})
    summary["balance_cents"] += balance
    summary["available_cents"] += balance
    planned = read_payments(database)
    summary.update(summarize(
        summary["accounts"],
        [Commitment(item["name"], date.fromisoformat(item["date"]), item["cents"]) for item in planned],
        summary["protected_cents"], date.fromisoformat(summary["as_of"]),
    ))
    summary["planned_payments"] = planned
    summary["imported_movements"] = movements
    summary["budget_month"] = summary["as_of"][:7]
    summary["budgets"] = budget_summary(database, summary["budget_month"], movements)
    return summary

