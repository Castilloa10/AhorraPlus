from api.storage import connect
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from api.categories import set_category
from api.csv_import import confirm
from api.imported_home import imported_home


class CategoryTests(unittest.TestCase):
    def test_existing_import_manual_override_and_reimport(self):
        sample = (Path(__file__).resolve().parents[1] / "samples/movimientos-demo.csv").read_text()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "demo.sqlite3"
            with closing(connect(database)) as connection:
                confirm(connection, "demo", sample)
            before = imported_home(database)
            self.assertEqual(
                [row["category"] for row in before["imported_movements"]],
                ["Suministros", "Alimentación", "Ingresos"],
            )
            identifier = before["imported_movements"][0]["id"]
            set_category(database, identifier, "Sin categoría")
            set_category(database, identifier, "Sin categoría")
            with closing(connect(database)) as connection:
                self.assertEqual(confirm(connection, "demo", sample), 0)
            after = imported_home(database)
            self.assertEqual(after["imported_movements"][0]["category"], "Sin categoría")
            self.assertEqual(after["balance_cents"], before["balance_cents"])
            self.assertEqual(after["available_cents"], before["available_cents"])
            with self.assertRaises(ValueError):
                set_category(database, identifier, "Inventada")
            with self.assertRaises(LookupError):
                set_category(database, "inexistente", "Ingresos")
            self.assertEqual(imported_home(database), after)

    def test_other_account_is_not_editable_and_unknown_description(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "demo.sqlite3"
            sample = "id,fecha,concepto,importe\nunknown,2026-11-01,Otro concepto,-2\n"
            with closing(connect(database)) as connection:
                confirm(connection, "other", sample)
            with self.assertRaises(LookupError):
                set_category(database, "unknown", "Alimentación")
            with closing(connect(database)) as connection:
                confirm(connection, "demo", sample)
            self.assertEqual(imported_home(database)["imported_movements"][0]["category"], "Sin categoría")

