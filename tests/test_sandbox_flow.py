from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from api.sandbox_flow import MockClient, MockFlow, MOCK, CALLBACK, SandboxError, transport
from api.privacy import load_secret

APP = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'
SESSION = 'bbbbbbbb-bbbb-4ccc-8ddd-eeeeeeeeeeee'
ACCOUNT = 'cccccccc-bbbb-4ccc-8ddd-eeeeeeeeeeee'


def application(**changes):
    return dict({'kid': APP, 'environment': 'SANDBOX', 'active': True, 'services': ['AIS'], 'redirect_urls': [CALLBACK]}, **changes)


def session():
    return {'session_id': SESSION, 'aspsp': MOCK, 'accounts': [{'uid': ACCOUNT, 'name': 'Ficticia', 'currency': 'EUR'}],
            'access': {'valid_until': (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()}}


class MockClientTests(unittest.TestCase):
    def test_production_and_wrong_callback_block_authorization(self):
        for app in (application(environment='PRODUCTION'), application(redirect_urls=[])):
            sender = Mock(return_value=app)
            client = MockClient(APP, 'FAKE', sender=sender, signer=lambda *args: 'FAKE')
            with self.assertRaises(SandboxError):
                client.begin('fake-state')
            self.assertEqual(sender.call_count, 1)

    def test_begin_fixed_mock_bank_and_short_expiry(self):
        sender = Mock(side_effect=[application(), {'aspsps': [{**MOCK, 'maximum_consent_validity': 1800}]},
                                   {'url': 'https://auth.enablebanking.com/ais/start?fake=1'}])
        client = MockClient(APP, 'FAKE', sender=sender, signer=lambda *args: 'FAKE')
        self.assertTrue(client.begin('fake-state').startswith('https://auth.enablebanking.com/'))
        payload = sender.call_args.args[3]
        self.assertEqual(payload['aspsp'], MOCK)
        self.assertEqual(payload['redirect_url'], CALLBACK)
        self.assertLessEqual((datetime.fromisoformat(payload['access']['valid_until']) - datetime.now(timezone.utc)).total_seconds(), 1800)

    def test_payment_and_foreign_destinations_never_reach_network(self):
        with patch('api.sandbox_flow.build_opener') as opener:
            for method, path in [('POST', '/payments'), ('GET', '//evil.invalid/accounts'), ('POST', '/accounts/' + ACCOUNT + '/transactions')]:
                with self.assertRaises(SandboxError):
                    transport(method, path, 'FAKE')
            opener.assert_not_called()

    def test_official_sandbox_redirect_and_rejection_of_other_destinations(self):
        urls = [
            ('https://tilisy-sandbox.enablebanking.com/ais/start?fake=1', True),
            ('http://tilisy-sandbox.enablebanking.com/ais/start', False),
            ('https://tilisy-sandbox.enablebanking.com.evil.invalid/', False),
            ('https://evil.invalid/', False),
            ('https://user:password@tilisy-sandbox.enablebanking.com/', False),
            ('https://tilisy-sandbox.enablebanking.com:444/', False),
        ]
        for url, allowed in urls:
            with self.subTest(url=url):
                sender = Mock(side_effect=[application(), {'aspsps': [{**MOCK, 'maximum_consent_validity': 1800}]}, {'url': url}])
                client = MockClient(APP, 'FAKE', sender=sender, signer=lambda *args: 'FAKE')
                if allowed:
                    self.assertEqual(client.begin('fake-state'), url)
                else:
                    with self.assertRaises(SandboxError):
                        client.begin('fake-state')


class MockFlowTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database = Path(directory.name) / 'sandbox.sqlite3'
        self.client = Mock()
        self.client.exchange.return_value = session()
        self.flow = MockFlow(self.database, self.client)
        self.flow.finish('FAKE-CODE')

    def download_responses(self, *pages):
        return [{'status': 'AUTHORIZED', 'aspsp': MOCK, 'accounts': [ACCOUNT]}, {'balances': []}, *pages]

    def test_all_pages_replace_snapshot_and_disconnect_preserves_snapshot(self):
        self.client.call.side_effect = self.download_responses(
            {'transactions': [{'entry_reference': 'first'}], 'continuation_key': 'page 2&x'},
            {'transactions': [{'entry_reference': 'second'}], 'continuation_key': None})
        first = self.flow.download()
        self.assertEqual(len(first['accounts'][0]['transactions']), 2)
        self.assertIn('page+2%26x', self.client.call.call_args.args[1])
        self.client.call.side_effect = self.download_responses({'transactions': [{'entry_reference': 'first'}]})
        self.assertEqual(len(self.flow.download()['accounts'][0]['transactions']), 1)
        self.client.call.side_effect = None
        self.client.call.return_value = {}
        self.flow.disconnect()
        self.assertIsNone(self.flow.session())
        self.assertIsNotNone(self.flow.snapshot())
        self.assertNotIn(SESSION.encode(), self.database.read_bytes())

    def test_partial_download_does_not_overwrite_previous(self):
        self.client.call.side_effect = self.download_responses({'transactions': [{'entry_reference': 'original'}]})
        original = self.flow.download()
        self.client.call.side_effect = self.download_responses(
            {'transactions': [], 'continuation_key': 'repeat'}, {'transactions': [], 'continuation_key': 'repeat'})
        with self.assertRaises(SandboxError):
            self.flow.download()
        self.assertEqual(self.flow.snapshot(), original)

    def test_failed_remote_disconnect_keeps_session_for_retry(self):
        self.client.call.side_effect = SandboxError('offline')
        with self.assertRaises(SandboxError):
            self.flow.disconnect()
        self.assertIsNotNone(load_secret(self.database, 'bank_session'))

    def test_session_guard_and_no_duplicate_exchange(self):
        with self.assertRaises(SandboxError):
            self.flow.finish('SECOND')
        self.assertEqual(self.client.exchange.call_count, 1)
        self.client.call.return_value = {'status': 'AUTHORIZED', 'aspsp': {'name': 'Other', 'country': 'ES'}, 'accounts': [ACCOUNT]}
        with self.assertRaises(SandboxError):
            self.flow.download()
        self.assertEqual(self.client.call.call_count, 1)
