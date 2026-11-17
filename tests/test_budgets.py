from api.storage import connect
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from api.budgets import budget_summary, save_budget
from api.categories import set_category
from api.csv_import import confirm
from api.imported_home import imported_home


class BudgetTests(unittest.TestCase):
    def test_persistence_edit_category_and_duplicates(self):
        sample = (Path(__file__).resolve().parents[1] / "samples/movimientos-demo.csv").read_text()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "test.sqlite3"
            save_budget(database, "2026-11", "Alimentación", 20000)
            with closing(connect(database)) as connection:
                confirm(connection, "demo", sample)
            summary = imported_home(database)
            food = next(row for row in summary["budgets"] if row["category"] == "Alimentación")
            self.assertEqual(food["spent_cents"], 4825)
            self.assertEqual(food["remaining_cents"], 15175)
            self.assertEqual(summary["available_cents"], 371295)
            with closing(connect(database)) as connection:
                self.assertEqual(confirm(connection, "demo", sample), 0)
            self.assertEqual(imported_home(database), summary)
            save_budget(database, "2026-11", "Alimentación", 0)
            self.assertEqual(imported_home(database)["budgets"][1]["remaining_cents"], -4825)
            set_category(database, "demo-002", "Suministros")
            self.assertEqual(imported_home(database)["budgets"][1]["spent_cents"], 0)
            self.assertEqual(imported_home(database)["budgets"][2]["spent_cents"], 9315)

    def test_months_refunds_and_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "test.sqlite3"
            save_budget(database, "2026-10", "Alimentación", 1000)
            rows = [
                {"date": "2026-11-01", "category": "Alimentación", "cents": -5000},
                {"date": "2026-11-03", "category": "Alimentación", "cents": 1000},
                {"date": "2026-10-03", "category": "Alimentación", "cents": -9000},
            ]
            food = budget_summary(database, "2026-11", rows)[1]
            self.assertEqual(food["spent_cents"], 4000)
            self.assertIsNone(food["limit_cents"])
            self.assertIsNone(food["remaining_cents"])
            for month, category, amount in [
                ("2026-13", "Alimentación", 100), ("2026-1", "Alimentación", 100),
                ("2026-11", "Ingresos", 100), ("2026-11", "Alimentación", -1),
                ("2026-11", "Alimentación", True), ("2026-11", "Alimentación", 1.5),
            ]:
                with self.assertRaises(ValueError):
                    save_budget(database, month, category, amount)

