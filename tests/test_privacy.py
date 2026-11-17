import os
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from api.storage import connect
from api.protection import read_protected
from api.privacy import store_secret, load_secret, disconnect_local, delete_imported
from api.csv_import import confirm
from api.budgets import save_budget


@unittest.skipUnless(os.name == 'nt', 'Windows DPAPI')
class PrivacyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / 'test.sqlite3'

    def test_migration_rollback_and_failed_write_preserve_data(self):
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute('CREATE TABLE sample(value TEXT)')
            db.execute("INSERT INTO sample VALUES ('fictitious-private-value')")
        with closing(connect(self.database)) as db:
            self.assertEqual(db.execute('SELECT value FROM sample').fetchone()[0], 'fictitious-private-value')
            with self.assertRaises(ValueError):
                with db:
                    db.execute("UPDATE sample SET value='rollback'")
                    raise ValueError('test')
        original = self.database.read_bytes()
        self.assertTrue(original.startswith(b'AHORRA-DPAPI-1\n'))
        self.assertNotIn(b'fictitious-private-value', original)
        with closing(connect(self.database)) as db:
            with patch('api.protection.os.replace', side_effect=OSError('test')):
                with self.assertRaises(OSError):
                    with db:
                        db.execute("UPDATE sample SET value='failed-write'")
        self.assertEqual(self.database.read_bytes(), original)
        with closing(connect(self.database)) as db:
            self.assertEqual(db.execute('SELECT value FROM sample').fetchone()[0], 'fictitious-private-value')

    def test_corruption_fails_closed(self):
        self.database.write_bytes(b'AHORRA-DPAPI-1\nbroken')
        with self.assertRaises(OSError):
            connect(self.database)
        self.assertEqual(self.database.read_bytes(), b'AHORRA-DPAPI-1\nbroken')

    def test_concurrent_updates_and_local_disconnect(self):
        def save(index):
            with closing(connect(self.database)) as db, db:
                db.execute('CREATE TABLE IF NOT EXISTS sample(value INTEGER)')
                db.execute('INSERT INTO sample VALUES (?)', (index,))
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(save, range(12)))
        with closing(connect(self.database)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM sample').fetchone()[0], 12)
        store_secret(self.database, 'bank_session', 'FAKE-SECRET-ONLY')
        self.assertEqual(load_secret(self.database, 'bank_session'), 'FAKE-SECRET-ONLY')
        self.assertNotIn(b'FAKE-SECRET-ONLY', self.database.read_bytes())
        disconnect_local(self.database)
        disconnect_local(self.database)
        self.assertIsNone(load_secret(self.database, 'bank_session'))
        self.assertNotIn(b'FAKE-SECRET-ONLY', read_protected(self.database))

    def test_delete_requires_confirmation_preserves_other_data_and_allows_reimport(self):
        sample = 'id,fecha,concepto,importe\na,2026-11-01,Ficticio,10.00\n'
        with closing(connect(self.database)) as db:
            confirm(db, 'demo', sample)
            confirm(db, 'other', sample)
        save_budget(self.database, '2026-11', 'Alimentación', 5000)
        with self.assertRaises(ValueError):
            delete_imported(self.database, 'no')
        with closing(connect(self.database)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM movements').fetchone()[0], 2)
        delete_imported(self.database, 'BORRAR DEMO')
        delete_imported(self.database, 'BORRAR DEMO')
        with closing(connect(self.database)) as db:
            self.assertEqual(db.execute('SELECT account FROM movements').fetchall(), [('other',)])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM budgets').fetchone()[0], 1)
            self.assertEqual(confirm(db, 'demo', sample), 1)
