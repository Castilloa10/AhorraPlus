import importlib.util
from pathlib import Path
import tempfile
import unittest

from api.sandbox_config import configure
from api.sandbox_probe import SandboxError, sign_token
from api.privacy import load_secret


@unittest.skipUnless(importlib.util.find_spec('jwt') and importlib.util.find_spec('cryptography'), 'Dependencias de firma opcionales')
class SandboxConfigTests(unittest.TestCase):
    def test_encrypted_import_repeat_and_signed_token(self):
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import jwt
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
        app_id = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'
        with tempfile.TemporaryDirectory() as directory:
            source, db = Path(directory) / 'test.pem', Path(directory) / 'vault.sqlite3'
            source.write_bytes(pem)
            configure(source, app_id, db)
            configure(source, app_id, db)
            self.assertEqual(source.read_bytes(), pem)
            self.assertNotIn(b'PRIVATE KEY', db.read_bytes())
            self.assertEqual(load_secret(db, 'provider_app_id'), app_id)
            token = sign_token(app_id, load_secret(db, 'provider_private_key'))
            claims = jwt.decode(token, key.public_key(), algorithms=['RS256'], audience='api.enablebanking.com', issuer='enablebanking.com')
            self.assertEqual(claims['exp'] - claims['iat'], 300)
            self.assertEqual(jwt.get_unverified_header(token)['kid'], app_id)
            with self.assertRaises(SandboxError):
                configure(source, 'bbbbbbbb-bbbb-4ccc-8ddd-eeeeeeeeeeee', db)
            self.assertEqual(load_secret(db, 'provider_app_id'), app_id)

    def test_invalid_key_creates_no_vault(self):
        with tempfile.TemporaryDirectory() as directory:
            source, db = Path(directory) / 'invalid.pem', Path(directory) / 'vault.sqlite3'
            source.write_text('not-a-key')
            with self.assertRaises(SandboxError):
                configure(source, 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee', db)
            self.assertFalse(db.exists())
