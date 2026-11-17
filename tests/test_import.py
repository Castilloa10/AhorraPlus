import sqlite3
import unittest
from contextlib import closing

from api.csv_import import confirm, preview

HEADER = 'id,fecha,concepto,importe\n'


class ImportTests(unittest.TestCase):
    def test_preview_validation(self):
        rows, errors = preview(HEADER + '1,2026-02-30,Compra,-1.00\n2,2026-02-28,Compra,1.001\n')
        self.assertEqual(rows, [])
        self.assertEqual(len(errors), 2)

    def test_reimport_overlap_and_atomic_conflict(self):
        with closing(sqlite3.connect(':memory:')) as db:
            content = HEADER + '1,2026-11-01,Compra,-4.25\n'
            self.assertEqual(confirm(db, 'demo', content), 1)
            self.assertEqual(confirm(db, 'demo', content), 0)
            with self.assertRaises(ValueError):
                confirm(db, 'demo', HEADER + '2,2026-11-02,Otra,-5\n1,2026-11-01,Compra,-9\n')
            self.assertEqual(db.execute('SELECT COUNT(*) FROM movements').fetchone()[0], 1)
            self.assertEqual(confirm(db, 'demo', content + '2,2026-11-02,Otra,-5\n'), 1)
