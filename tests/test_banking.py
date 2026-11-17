from contextlib import closing
from copy import deepcopy
import json
import sqlite3
import unittest

from api.banking import FIXTURE, normalize_page, simulated_import
from api.csv_import import confirm, preview


class BankingTests(unittest.TestCase):
    def test_simulation_and_idempotent_confirmation(self):
        result = simulated_import()
        rows, errors = preview(result["content"])
        self.assertFalse(errors)
        self.assertEqual(result["skipped"], 1)
        self.assertEqual([row[3] for row in rows], [-3000, 1000])
        with closing(sqlite3.connect(":memory:")) as connection:
            self.assertEqual(confirm(connection, "demo", result["content"]), 2)
            self.assertEqual(confirm(connection, "demo", result["content"]), 0)
            self.assertEqual(connection.execute("SELECT SUM(cents) FROM movements").fetchone()[0], -2000)

    def test_reject_incomplete_or_ambiguous_data(self):
        fixture = json.loads(FIXTURE.read_text())
        changes = [
            {"entry_reference": ""},
            {"booking_date": "2026-02-30"},
            {"credit_debit_indicator": "OTHER"},
            {"transaction_amount": {"currency": "USD", "amount": "1.00"}},
            {"transaction_amount": {"currency": "EUR", "amount": "1.001"}},
            {"transaction_amount": {"currency": "EUR", "amount": "NaN"}},
        ]
        for change in changes:
            page = deepcopy(fixture)
            page["transactions"][0].update(change)
            with self.assertRaises(ValueError):
                normalize_page(page)
        fixture["continuation_key"] = "another-page"
        with self.assertRaises(ValueError):
            normalize_page(fixture)
