from api.storage import connect
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from api.csv_import import confirm
from api.imported_home import imported_home


class ImportedHomeTests(unittest.TestCase):
    def test_balance_persistence_duplicates_and_cutoff(self):
        sample = (Path(__file__).resolve().parents[1] / "samples/movimientos-demo.csv").read_text()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "demo.sqlite3"
            self.assertEqual(imported_home(database)["accounts"][-1]["cents"], 0)
            with closing(connect(database)) as connection:
                self.assertEqual(confirm(connection, "demo", sample), 3)
            result = imported_home(database)
            self.assertEqual(result["accounts"][-1]["cents"], 200685)
            self.assertEqual(result["balance_cents"], 525525)
            self.assertEqual(result["available_cents"], 371295)
            self.assertEqual(len(result["imported_movements"]), 3)
            with closing(connect(database)) as connection:
                self.assertEqual(confirm(connection, "demo", sample), 0)
                confirm(connection, "demo", "id,fecha,concepto,importe\nfuture,2026-12-01,Futuro,500\n")
                confirm(connection, "other", sample)
            self.assertEqual(imported_home(database), result)

