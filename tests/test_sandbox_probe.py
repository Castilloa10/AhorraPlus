import unittest
from unittest.mock import Mock, patch

from api.sandbox_probe import SandboxError, probe, get_json, NoRedirect

APP = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'


class SandboxProbeTests(unittest.TestCase):
    def application(self, **changes):
        return dict({'kid': APP, 'environment': 'SANDBOX', 'active': True, 'services': ['AIS']}, **changes)

    def test_success_only_catalog_and_no_credentials_in_result(self):
        transport = Mock(side_effect=[self.application(), {'aspsps': [
            {'name': 'Mock ASPSP', 'country': 'FI', 'sandbox': {'users': [{'password': 'FAKE'}]}}
        ]}])
        result = probe(APP, 'FAKE-KEY', transport=transport, signer=lambda *args: 'FAKE-TOKEN')
        self.assertFalse(result['bank_connected'])
        self.assertEqual(result['banks'], [{'name': 'Mock ASPSP', 'country': 'FI'}])
        self.assertEqual([call.args[0] for call in transport.call_args_list], ['/application', '/aspsps?country=ES'])

    def test_production_unknown_environment_and_inactive_fail_before_catalog(self):
        for app in (self.application(environment='PRODUCTION'), self.application(environment=None),
                    self.application(active=False), self.application(kid='other'), self.application(services=[])):
            with self.subTest(app=app):
                transport = Mock(return_value=app)
                with self.assertRaises(SandboxError):
                    probe(APP, 'FAKE', transport=transport, signer=lambda *args: 'FAKE')
                self.assertEqual(transport.call_count, 1)

    def test_missing_configuration_does_not_contact_provider(self):
        transport, signer = Mock(), Mock()
        for app_id, key in ((None, None), ('invalid', 'FAKE'), (APP, None)):
            with self.assertRaises(SandboxError):
                probe(app_id, key, transport=transport, signer=signer)
        transport.assert_not_called()
        signer.assert_not_called()

    def test_financial_paths_and_redirects_blocked(self):
        with patch('api.sandbox_probe.build_opener') as opener:
            for path in ('/auth', '/sessions', '/accounts/123/balances', '/payments', 'https://other.invalid'):
                with self.assertRaises(SandboxError):
                    get_json(path, 'FAKE')
            opener.assert_not_called()
        with self.assertRaises(SandboxError):
            NoRedirect().redirect_request(None, None, 302, None, None, 'https://other.invalid')

    def test_broken_catalog_is_not_a_success(self):
        transport = Mock(side_effect=[self.application(), {'aspsps': [None]}])
        with self.assertRaises(SandboxError):
            probe(APP, 'FAKE', transport=transport, signer=lambda *args: 'FAKE')
