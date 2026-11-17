from pathlib import Path
import tempfile
import unittest

from api.imported_home import imported_home
from api.planned_payments import read_payments, save_payment


class PaymentTests(unittest.TestCase):
    def test_save_retry_edit_and_month_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "demo.sqlite3"
            before = imported_home(database)
            for _ in range(2):
                save_payment(database, "test", "Seguro de prueba", "2026-11-25", 12000, "Irregular")
            after = imported_home(database)
            self.assertEqual(after["committed_cents"], before["committed_cents"] + 12000)
            self.assertEqual(after["available_cents"], before["available_cents"] - 12000)
            self.assertEqual(len(read_payments(database)), 5)
            save_payment(database, "test", "Seguro de prueba", "2026-12-01", 12000, "Irregular")
            self.assertEqual(imported_home(database)["committed_cents"], before["committed_cents"])
            save_payment(database, "demo-1", "Alquiler editado", "2026-11-20", 80000, "Fijo")
            self.assertEqual(imported_home(database)["committed_cents"], before["committed_cents"] + 5000)
            with self.assertRaises(ValueError):
                save_payment(database, "bad", "Fecha imposible", "2026-02-30", 100, "Fijo")
            self.assertEqual(len(read_payments(database)), 5)
