import json
import unittest
from datetime import date
from pathlib import Path

from api.demo import demo_home
from api.finance import Commitment, summarize


class FinanceTests(unittest.TestCase):
    def test_demo_reconciles_and_matches_app(self):
        demo = demo_home()
        self.assertEqual(demo["balance_cents"], 324840)
        self.assertEqual(demo["committed_cents"], 94230)
        self.assertEqual(demo["protected_cents"], 60000)
        self.assertEqual(demo["available_cents"], 170610)
        path = Path(__file__).resolve().parents[1] / "app" / "demo.json"
        self.assertEqual(demo, json.loads(path.read_text(encoding="utf-8")))

    def test_cutoff_overdue_future_actual_charge_and_deficit(self):
        cutoff = date(2028, 2, 29)
        payments = [
            Commitment("Vencido", date(2028, 1, 30), 100),
            Commitment("Hoy", cutoff, 150),
            Commitment("Conciliado", cutoff, 300, cutoff),
            Commitment("Marzo", date(2028, 3, 1), 400),
            Commitment("Cargo posterior al corte", cutoff, 200, date(2028, 3, 1)),
        ]
        result = summarize([{"name": "Cuenta", "cents": 200}], payments, 50, cutoff)
        self.assertEqual(result["through"], "2028-02-29")
        self.assertEqual(result["committed_cents"], 450)
        self.assertEqual(result["available_cents"], -300)

