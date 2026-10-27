"""Real journal/HTTP failure and recovery tests; no DAZ private archive is loaded."""
import concurrent.futures
import copy
import http.client
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rundweg', ROOT / 'scripts/serve-rundweg.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class RoundtripTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='rundweg-test-', dir=ROOT / 'tests')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.catalog = json.loads((ROOT / 'server/static/variantenraum/catalog.json').read_text())
        self.catalog_path = self.root / 'catalog.json'
        self.catalog_path.write_text(json.dumps(self.catalog))
        self.store = r.Journal(self.catalog_path, self.root / 'journal', 'build-evidence-one')

    def request(self, variant=None):
        variant = variant or self.catalog['variants'][0]
        return {'operationId': str(uuid.uuid4()), 'catalogRevision': self.catalog['revision'], 'variantId': variant['id'],
                'roomId': 'room-dazwischen', 'expectedVariantDigest': r.digest(variant),
                'navigation': {'hash': '#variante=variant-ausgang&ansicht=room&vergleich=variant-foederiert&filter=dissent&raum=room-dazwischen&raumfassung=' + variant['id'] + '&suche=DAZWISCHEN&rueckweg=compare'}}

    def receive(self, entry):
        request = {'packetDigest': entry['packet']['digest'], 'disposition': 'received',
                   'finding': 'Öffentliche Quellenbindung und exakter Rückweg im DAZ-Eingang gelesen.'}
        return self.store.mutate(entry['packet']['operationId'], 'receipt', request), request

    def adoption(self, entry):
        return {'operationId': str(uuid.uuid4()), 'receiptDigest': entry['receipt']['digest'],
                'expectedVariantDigest': entry['packet']['source']['variantDigest']}

    def test_lost_response_replay_restart_and_exact_return(self):
        request = self.request()
        first = self.store.create(request)
        op = first['packet']['operationId']
        self.assertEqual(first, self.store.create(request))
        received, receipt_request = self.receive(first)
        reopened = r.Journal(self.catalog_path, self.root / 'journal', 'build-evidence-one')
        self.assertEqual(received, reopened.mutate(op, 'receipt', receipt_request))
        self.assertEqual(received['receipt']['returnUrl'], '/variantenraum/index.html' + request['navigation']['hash'])
        self.assertEqual(len(reopened.snapshot()['handoffs']), 1)
        self.assertTrue(r.valid_seal(received['packet']))
        self.assertTrue(r.valid_seal(received['receipt']))
        self.assertEqual(received['receipt']['actor']['name'], 'Codex')
        self.assertEqual(received['receipt']['actor']['mandate'], r.MANDATE)
        self.assertEqual(received['receipt']['review'], 'not-reviewed')
        self.assertEqual(received['receipt']['humanAcceptance'], 'open')
        self.assertNotIn('locator', received['packet']['source']['sourceSummaries'][0])

    def test_conflicting_replays_do_not_mutate(self):
        request = self.request()
        first = self.store.create(request)
        altered = copy.deepcopy(request)
        altered['navigation']['hash'] += '&extra=conflict'
        with self.assertRaises(r.Rejected):
            self.store.create(altered)
        received, receipt_request = self.receive(first)
        receipt_request['finding'] = 'Ein anderer technischer Befund für denselben Versuch.'
        before = self.store.snapshot()
        with self.assertRaises(r.Rejected):
            self.store.mutate(first['packet']['operationId'], 'receipt', receipt_request)
        self.assertEqual(before, self.store.snapshot())
        self.assertEqual(received['receipt'], self.store.read(first['packet']['operationId'])['receipt'])

    def test_withdrawal_blocks_late_receipt_and_adoption(self):
        first = self.store.create(self.request())
        op = first['packet']['operationId']
        self.store.mutate(op, 'withdraw', {})
        with self.assertRaises(r.Rejected):
            self.receive(first)
        second, _ = self.receive(self.store.create(self.request()))
        op2 = second['packet']['operationId']
        self.store.mutate(op2, 'withdraw', {})
        with self.assertRaises(r.Rejected):
            self.store.mutate(op2, 'adopt', self.adoption(second))
        self.assertEqual(self.store.read(op2)['receipt'], second['receipt'])
        self.assertEqual(self.store.snapshot()['variants'], [])

    def test_derivation_preserves_original_sources_dissent_and_acceptance(self):
        entry, _ = self.receive(self.store.create(self.request()))
        request = self.adoption(entry)
        op = entry['packet']['operationId']
        adopted = self.store.mutate(op, 'adopt', request)
        self.assertEqual(adopted, self.store.mutate(op, 'adopt', request))
        state = r.Journal(self.catalog_path, self.root / 'journal', 'build-evidence-one').snapshot()
        self.assertEqual(len(state['variants']), 1)
        original, derived = self.catalog['variants'][0], state['variants'][0]
        for key in ('componentBindings', 'dissentIds', 'proposal', 'implementation', 'verification', 'humanAcceptance', 'mandate', 'context'):
            self.assertEqual(original[key], derived[key])
        self.assertEqual(derived['parentIds'], [original['id']])
        self.assertEqual(derived['provenance']['roomReceiptDigest'], entry['receipt']['digest'])
        self.assertEqual(json.loads(self.catalog_path.read_text()), self.catalog)

    def test_old_catalog_or_build_cannot_be_adopted(self):
        entry, _ = self.receive(self.store.create(self.request()))
        self.catalog['revision'] += '-changed'
        self.catalog_path.write_text(json.dumps(self.catalog))
        with self.assertRaises(r.Rejected):
            self.store.mutate(entry['packet']['operationId'], 'adopt', self.adoption(entry))
        new_store = r.Journal(self.catalog_path, self.root / 'journal', 'new-daz-build')
        another = new_store.create(self.request())
        with self.assertRaises(r.Rejected):
            self.store.mutate(another['packet']['operationId'], 'receipt', {'packetDigest': another['packet']['digest'], 'disposition': 'received', 'finding': 'Fremde aktuelle DAZ-Fassung darf keinen alten Empfang behaupten.'})

    def test_runtime_build_change_and_cross_handoff_adoption_collision(self):
        entry, _ = self.receive(self.store.create(self.request()))
        another, _ = self.receive(self.store.create(self.request()))
        request = self.adoption(entry)
        self.store.mutate(entry['packet']['operationId'], 'adopt', request)
        collision = {**self.adoption(another), 'operationId': request['operationId']}
        with self.assertRaises(r.Rejected):
            self.store.mutate(another['packet']['operationId'], 'adopt', collision)
        self.assertEqual(len(self.store.snapshot()['variants']), 1)
        build = self.root / 'build'
        build.mkdir()
        (build / 'index.html').write_text('initial build')
        guarded = r.Journal(self.catalog_path, self.root / 'guarded', r.tree_digest(build), build)
        pending = guarded.create(self.request())
        (build / 'index.html').write_text('changed build')
        with self.assertRaises(r.Rejected):
            guarded.create(self.request())
        with self.assertRaises(r.Rejected):
            guarded.mutate(pending['packet']['operationId'], 'receipt', {'packetDigest': pending['packet']['digest'], 'disposition': 'received', 'finding': 'Die Fassung wurde inzwischen auf dem Datenträger verändert.'})

    def test_new_whole_does_not_inherit_parent_human_acceptance(self):
        self.catalog['variants'][0]['humanAcceptance'] = {'status': 'accepted', 'summary': 'Nur die alte Fassung war angenommen.'}
        self.catalog_path.write_text(json.dumps(self.catalog))
        entry, _ = self.receive(self.store.create(self.request()))
        self.store.mutate(entry['packet']['operationId'], 'adopt', self.adoption(entry))
        self.assertEqual(self.store.snapshot()['variants'][0]['humanAcceptance']['status'], 'open')
        self.assertEqual(json.loads(self.catalog_path.read_text())['variants'][0]['humanAcceptance']['status'], 'accepted')

    def test_missing_receipt_wrong_binding_identity_and_navigation_are_rejected(self):
        first = self.store.create(self.request())
        op = first['packet']['operationId']
        with self.assertRaises(r.Rejected):
            self.store.mutate(op, 'adopt', {'operationId': str(uuid.uuid4()), 'receiptDigest': 'wrong', 'expectedVariantDigest': first['packet']['source']['variantDigest']})
        with self.assertRaises(r.Rejected):
            self.store.mutate(op, 'receipt', {'packetDigest': 'wrong', 'disposition': 'received', 'finding': 'Dieser Befund hat die falsche Paketbindung.'})
        with self.assertRaises(r.Rejected):
            self.store.mutate(op, 'receipt', {'packetDigest': first['packet']['digest'], 'disposition': 'received', 'finding': 'Frei behauptete menschliche Annahme ist nicht erlaubt.', 'actor': 'Ralf'})
        for fragment in ('#variante=variant-foederiert&ansicht=variant&vergleich=variant-ausgang&filter=all', '#variante=variant-ausgang&ansicht=variant&vergleich=variant-foederiert&filter=all&redirect=https://example.com'):
            request = self.request()
            request['navigation']['hash'] = fragment
            with self.assertRaises(r.Rejected):
                self.store.create(request)

    def test_atomic_failure_and_concurrent_duplicate(self):
        request = self.request()
        with patch.object(r.os, 'replace', side_effect=OSError('simulated disk failure')):
            with self.assertRaises(OSError):
                self.store.create(request)
        self.assertEqual(self.store.snapshot()['handoffs'], [])
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as workers:
            results = list(workers.map(lambda _: self.store.create(request), range(8)))
        self.assertTrue(all(x == results[0] for x in results))
        self.assertEqual(len(self.store.snapshot()['handoffs']), 1)

    def test_directory_sync_failure_retains_replaced_state_for_recovery(self):
        request = self.request()
        real_fsync = r.os.fsync
        calls = []
        def fail_directory_sync(fd):
            calls.append(fd)
            if len(calls) == 2:
                raise OSError('directory durability uncertain')
            real_fsync(fd)
        with patch.object(r.os, 'fsync', side_effect=fail_directory_sync):
            with self.assertRaises(OSError):
                self.store.create(request)
        self.assertEqual(len(self.store.snapshot()['handoffs']), 1)
        recovered = r.Journal(self.catalog_path, self.root / 'journal', 'build-evidence-one')
        self.assertEqual(self.store.create(request), recovered.create(request))
        self.store.create(self.request())
        self.assertEqual(len(self.store.snapshot()['handoffs']), 2)

    def test_http_origin_path_and_body_limits(self):
        static, daz = self.root / 'static', self.root / 'daz'
        static.mkdir(); daz.mkdir()
        (static / 'index.html').write_text('variants')
        (daz / 'index.html').write_text('real DAZ test build')
        (self.root / 'private.txt').write_text('must never be served')
        server = r.ThreadingHTTPServer(('127.0.0.1', 0), r.make_handler(self.store, static, daz))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        port = server.server_port

        def call(method, path, body=None, headers=None):
            connection = http.client.HTTPConnection('127.0.0.1', port)
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            result = response.status, response.read()
            connection.close()
            return result

        self.assertEqual(call('GET', '/dazwischen/')[1], b'real DAZ test build')
        self.assertEqual(call('GET', '/variantenraum/index.html')[1], b'variants')
        self.assertEqual(call('GET', '/variantenraum/%2e%2e/private.txt')[0], 404)
        self.assertEqual(call('GET', '/api/rundweg/state', headers={'Host': 'evil.example'})[0], 403)
        body = json.dumps(self.request())
        headers = {'Content-Type': 'application/json', 'X-Rundweg-Request': '1', 'Origin': f'http://127.0.0.1:{port}'}
        self.assertEqual(call('POST', '/api/rundweg/handoffs', body, {**headers, 'Origin': 'https://evil.example'})[0], 403)
        self.assertEqual(call('POST', '/api/rundweg/handoffs', body, {'Content-Type': 'text/plain'})[0], 403)
        self.assertEqual(call('POST', '/api/rundweg/handoffs', 'x' * 16001, headers)[0], 400)
        self.assertEqual(call('POST', '/api/rundweg/handoffs', body, headers)[0], 200)


if __name__ == '__main__':
    unittest.main()
