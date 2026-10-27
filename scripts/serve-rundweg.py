#!/usr/bin/env python3
"""Local, metadata-only connection between Variantenraum and the real DAZ build."""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, unquote, urlsplit

FORMAT = 'kintegrity.roundtrip.v1'
MANDATE = ('Mach jetzt mit dem echten Rundweg weiter: vom Variantenraum nach DAS DAZWISCHEN, '
           'mit verantworteter Quittung und nachvollziehbarer Rückkehr in die Gesamtfassung. '
           'Setze die fehlenden Anschlüsse um und prüfe den Weg praktisch.')
VOLUME = Path('/Volumes/ThunderBolt4_2TB')
VOLUME_UUID = 'A03B10FD-5F22-4366-A71C-2D95AC701BD2'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def seal(value):
    return {**value, 'digest': digest(value)}


def valid_seal(value):
    return isinstance(value, dict) and value.get('digest') == digest({k: v for k, v in value.items() if k != 'digest'})


def now():
    return datetime.now(timezone.utc).isoformat()


class Rejected(Exception):
    def __init__(self, message, status=409):
        super().__init__(message)
        self.status = status


def require(condition, message='Der Vorgang passt nicht zu dieser Übergabe.', status=409):
    if not condition:
        raise Rejected(message, status)


def operation_id(value):
    require(isinstance(value, str) and len(value) == 36, 'Die Übergabe ist nicht gültig.', 400)
    try:
        require(str(uuid.UUID(value)) == value, status=400)
    except ValueError:
        raise Rejected('Die Übergabe ist nicht gültig.', 400)
    return value


class Journal:
    """One lock and one atomic replacement cover packet, receipt and derivation."""
    def __init__(self, catalog_path, state_dir, target_revision, target_root=None):
        self.catalog_path = Path(catalog_path)
        self.state_dir = Path(state_dir)
        self.path = self.state_dir / 'rundweg.json'
        self.target_revision = target_revision
        self.target_root = Path(target_root) if target_root else None
        self.lock = threading.RLock()
        self.state = json.loads(self.path.read_text()) if self.path.exists() else {'format': FORMAT, 'handoffs': [], 'variants': []}
        require(self.state.get('format') == FORMAT, 'Das Rundwegjournal kann nicht sicher geöffnet werden.', 503)
        for entry in self.state['handoffs']:
            require(valid_seal(entry['packet']) and (not entry['receipt'] or valid_seal(entry['receipt'])),
                    'Das Rundwegjournal kann nicht sicher geöffnet werden.', 503)

    def catalog(self):
        return json.loads(self.catalog_path.read_text())

    def check_target(self):
        require(self.target_root is None or tree_digest(self.target_root) == self.target_revision,
                'Die DAZ-Fassung hat sich geändert. Öffne den lokalen Rundweg mit der neuen Fassung erneut.', 409)

    def variant(self, catalog, variant_id):
        value = next((v for v in catalog['variants'] + self.state['variants'] if v['id'] == variant_id), None)
        require(value is not None, 'Die Ausgangsfassung ist nicht mehr verfügbar.')
        return value

    def persist(self, candidate):
        require(len(candidate['handoffs']) <= 500 and len(canonical(candidate)) <= 8_000_000,
                'Das lokale Rundwegjournal ist voll. Sichere es vor weiteren Übergaben.', 507)
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = self.state_dir / ('rundweg-' + str(uuid.uuid4()) + '.tmp')
        try:
            with temporary.open('x', encoding='utf-8') as stream:
                os.chmod(temporary, 0o600)
                json.dump(candidate, stream, ensure_ascii=False, indent=2, allow_nan=False)
                stream.write('\n')
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            # Once replaced, disk and memory must advance together even if directory fsync fails.
            self.state = candidate
            directory = os.open(self.state_dir, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            temporary.unlink(missing_ok=True)
        self.state = candidate

    @staticmethod
    def envelope(entry):
        return copy.deepcopy({**entry, 'dazwischenUrl': '/dazwischen/?rundweg=' + entry['packet']['operationId']})

    def read(self, op):
        entry = next((e for e in self.state['handoffs'] if e['packet']['operationId'] == op), None)
        require(entry is not None, 'Diese Übergabe ist hier nicht verfügbar.', 404)
        return self.envelope(entry)

    def snapshot(self):
        with self.lock:
            return {'handoffs': [self.envelope(e) for e in self.state['handoffs']], 'variants': copy.deepcopy(self.state['variants'])}

    def create(self, request):
        with self.lock:
            require(set(request) == {'operationId', 'catalogRevision', 'variantId', 'roomId', 'navigation', 'expectedVariantDigest'}, status=400)
            op = operation_id(request['operationId'])
            previous = next((e for e in self.state['handoffs'] if e['packet']['operationId'] == op), None)
            if previous:
                require(previous['requestDigest'] == digest(request), 'Diese Übergabe wurde bereits mit anderem Inhalt angelegt.')
                return self.envelope(previous)
            self.check_target()
            catalog = self.catalog()
            require(request['roomId'] == 'room-dazwischen' and request['catalogRevision'] == catalog['revision'],
                    'Die Katalogfassung hat sich geändert. Öffne den Variantenraum erneut.')
            variant = self.variant(catalog, request['variantId'])
            require(digest(variant) == request['expectedVariantDigest'], 'Die Ausgangsfassung hat sich geändert. Öffne sie erneut.')
            navigation = request['navigation']
            require(isinstance(navigation, dict) and set(navigation) == {'hash'}, status=400)
            fragment = navigation['hash']
            require(isinstance(fragment, str) and fragment.startswith('#') and len(fragment) <= 8000 and not re.search(r'[\r\n\x00]', fragment), status=400)
            pairs = parse_qsl(fragment[1:], keep_blank_values=True, max_num_fields=12)
            params = dict(pairs)
            require(len(params) == len(pairs) and set(params) <= {'variante', 'ansicht', 'vergleich', 'filter', 'raum', 'raumfassung', 'suche', 'rueckweg'}, status=400)
            require(params.get('ansicht') in {'variant', 'room', 'compare'} and params.get('filter') in {'all', 'open', 'dissent'}, status=400)
            known = {v['id'] for v in catalog['variants'] + self.state['variants']}
            require(params.get('variante') in known and params.get('vergleich') in known, status=400)
            require((params.get('raumfassung') if params['ansicht'] == 'room' else params.get('variante')) == variant['id'], status=400)
            if params['ansicht'] == 'room':
                require(params.get('raum') == 'room-dazwischen' and params.get('rueckweg') in {'variant', 'compare'}, status=400)
            components = {c['id']: c for c in catalog['components']}
            bindings = [b for b in variant['componentBindings'] if b.get('roomId') == 'room-dazwischen' or components[b['componentId']].get('roomId') == 'room-dazwischen']
            require(bindings, 'Diese Fassung enthält keinen gebundenen DAZ-Beitrag.')
            source_ids = {b['sourceId'] for b in bindings}
            sources = [{k: s.get(k) for k in ('id', 'title', 'summary', 'revision', 'contentHash', 'visibility')}
                       for s in catalog['sources'] if s['id'] in source_ids]
            require(all(s['visibility'] == 'public' for s in sources), 'Dieser Anschluss erlaubt nur öffentliche Zusammenfassungen.')
            component_ids = {b['componentId'] for b in bindings}
            dissent = [d for d in catalog['dissent'] if d['id'] in variant['dissentIds'] and
                       ('room-dazwischen' in d.get('roomIds', []) or component_ids.intersection(d.get('componentIds', [])))]
            packet = seal({'format': FORMAT, 'operationId': op, 'createdAt': now(),
                'source': {'catalogRevision': catalog['revision'], 'variantId': variant['id'], 'variantDigest': digest(variant),
                           'variantSnapshot': copy.deepcopy(variant),
                           'roomId': 'room-dazwischen', 'bindings': [{**b, 'componentTitle': components[b['componentId']]['title']} for b in bindings],
                           'sourceSummaries': sources, 'dissent': copy.deepcopy(dissent)},
                'navigation': copy.deepcopy(navigation), 'returnUrl': '/variantenraum/index.html' + fragment,
                'mandate': {'text': MANDATE, 'executor': 'Codex', 'role': 'Technische Ausführung',
                            'scope': 'Lokalen Übergang, technischen Empfang und nachvollziehbaren Rückweg umsetzen und prüfen; keine fachliche oder menschliche Annahme.'},
                'target': {'name': 'DAS DAZWISCHEN', 'revision': self.target_revision}})
            entry = {'packet': packet, 'receipt': None, 'withdrawn': False, 'adoption': None, 'requestDigest': digest(request)}
            candidate = copy.deepcopy(self.state)
            candidate['handoffs'].append(entry)
            self.persist(candidate)
            return self.envelope(entry)

    def mutate(self, op, action, request):
        with self.lock:
            operation_id(op)
            candidate = copy.deepcopy(self.state)
            entry = next((e for e in candidate['handoffs'] if e['packet']['operationId'] == op), None)
            require(entry is not None, 'Diese Übergabe ist hier nicht verfügbar.', 404)
            packet = entry['packet']
            if action == 'withdraw':
                require(request == {}, status=400)
                if not entry['withdrawn']:
                    entry['withdrawn'] = True
                    entry['withdrawnAt'] = now()
            elif action == 'receipt':
                require(set(request) == {'packetDigest', 'finding', 'disposition'} and request['disposition'] == 'received', status=400)
                require(request['packetDigest'] == packet['digest'], 'Der Beleg gehört zu einer anderen Übergabe.')
                finding = request['finding']
                require(isinstance(finding, str) and 10 <= len(finding.strip()) <= 2000, 'Beschreibe den technischen Empfang in einem kurzen Befund.', 400)
                require(not entry['withdrawn'], 'Diese Übergabe wurde zurückgezogen. Der bisherige Beleg bleibt historisch erhalten.')
                if entry['receipt']:
                    require(entry['receiptRequestDigest'] == digest(request), 'Der Empfang ist bereits mit einem anderen Befund quittiert.')
                    return self.envelope(entry)
                self.check_target()
                require(packet['target']['revision'] == self.target_revision, 'Die DAZ-Fassung hat sich geändert. Lege eine neue Übergabe an.')
                receipt = seal({'id': str(uuid.uuid4()), 'packetDigest': packet['digest'], 'createdAt': now(),
                    'actor': {'name': 'Codex', 'role': packet['mandate']['role'], 'mandate': packet['mandate']['text'],
                              'scope': packet['mandate']['scope'], 'identityBasis': 'configured-local-technical-executor'},
                    'transport': 'received', 'review': 'not-reviewed', 'humanAcceptance': 'open', 'finding': finding.strip(),
                    'targetRevision': self.target_revision, 'returnUrl': packet['returnUrl']})
                entry['receipt'] = receipt
                entry['receiptRequestDigest'] = digest(request)
            elif action == 'adopt':
                require(set(request) == {'operationId', 'receiptDigest', 'expectedVariantDigest'}, status=400)
                operation_id(request['operationId'])
                if entry['adoption']:
                    require(entry['adoptionRequestDigest'] == digest(request), 'Für diese Quittung besteht bereits eine abgeleitete Fassung.')
                    return self.envelope(entry)
                self.check_target()
                require(not entry['withdrawn'], 'Diese Übergabe wurde zurückgezogen. Ein neuer Beleg braucht einen neuen Versuch.')
                require(entry['receipt'] and entry['receipt']['digest'] == request['receiptDigest'], 'Es fehlt eine passende Quittung aus DAS DAZWISCHEN.')
                catalog = self.catalog()
                variant = self.variant(catalog, packet['source']['variantId'])
                require(catalog['revision'] == packet['source']['catalogRevision'] and digest(variant) == packet['source']['variantDigest'] == request['expectedVariantDigest'],
                        'Die Ausgangsfassung ist inzwischen verändert. Der Beleg bleibt historisch; lege für die neue Fassung einen neuen Versuch an.')
                require(packet['target']['revision'] == self.target_revision, 'Die DAZ-Fassung hat sich geändert. Der Beleg bleibt historisch.')
                derived = copy.deepcopy(variant)
                derived.update({'id': 'variant-rundweg-' + request['operationId'],
                                'title': variant['title'] + ' · mit quittiertem Rundweg', 'parentIds': [variant['id']]})
                derived['provenance'] = {'kind': 'responsible-room-receipt', 'sourceVariantIds': [variant['id']],
                    'operationId': request['operationId'], 'roomReceiptDigest': entry['receipt']['digest'],
                    'originalProvenance': copy.deepcopy(variant['provenance'])}
                derived['roomReceipts'] = copy.deepcopy(variant.get('roomReceipts', [])) + [{'packetDigest': packet['digest'], 'receiptDigest': entry['receipt']['digest'], 'roomId': 'room-dazwischen'}]
                # A derived whole needs its own human decision; the parent remains untouched.
                if derived['humanAcceptance']['status'] != 'open':
                    derived['humanAcceptance'] = {'status': 'open', 'summary': 'Die neue Gesamtfassung mit Rundwegbeleg wurde noch nicht menschlich angenommen.'}
                # A transport receipt changes no content, dissent or source binding.
                require(not any(v['id'] == derived['id'] for v in candidate['variants']), 'Dieser Ableitungsversuch gehört bereits zu einem anderen Rundweg.')
                candidate['variants'].append(derived)
                entry['adoption'] = {'variantId': derived['id'], 'createdAt': now(), 'receiptDigest': entry['receipt']['digest'],
                                     'operationId': request['operationId'], 'parentVariantId': variant['id']}
                entry['adoptionRequestDigest'] = digest(request)
            else:
                raise Rejected('Dieser Rundwegschritt ist nicht verfügbar.', 404)
            self.persist(candidate)
            return self.envelope(entry)


def make_handler(journal, static_root, daz_root):
    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass  # No identifiers, request URLs or local paths in ordinary logs.

        def end_headers(self):
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
            super().end_headers()

        def host_ok(self):
            return self.headers.get('Host') == '127.0.0.1:' + str(self.server.server_port)

        def reply(self, value, status=200):
            data = canonical(value)
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            try:
                require(self.host_ok(), 'Dieser lokale Anschluss ist hier nicht verfügbar.', 403)
                path = urlsplit(self.path).path
                if path == '/api/rundweg/state':
                    return self.reply(journal.snapshot())
                match = re.fullmatch(r'/api/rundweg/handoffs/([a-z0-9-]+)', path)
                if match:
                    with journal.lock:
                        return self.reply(journal.read(operation_id(match[1])))
                if path.startswith('/api/'):
                    raise Rejected('Dieser Rundwegschritt ist nicht verfügbar.', 404)
                if path.startswith('/dazwischen/'):
                    root, relative = daz_root, path[len('/dazwischen/'):]
                elif path.startswith('/variantenraum/'):
                    root, relative = static_root, path[len('/variantenraum/'):]
                else:
                    raise Rejected('Dieser Raum ist hier nicht verfügbar.', 404)
                target = (root / unquote(relative or 'index.html')).resolve()
                require(target.is_relative_to(root) and target.is_file() and not any(p.startswith('.') for p in target.relative_to(root).parts), 'Diese Seite ist hier nicht verfügbar.', 404)
                self.path = '/' + target.relative_to(root).as_posix()
                self.directory = str(root)
                super().do_GET()
            except Rejected as error:
                self.reply({'error': str(error)}, error.status)
            except Exception:
                self.reply({'error': 'Der lokale Rundweg kann gerade nicht sicher gelesen werden.'}, 503)

        def do_HEAD(self):
            self.reply({'error': 'Öffne den lokalen Raum über seinen Einstieg.'}, 405)

        def do_POST(self):
            try:
                require(self.host_ok() and self.headers.get('Origin') == 'http://' + self.headers.get('Host', '')
                        and self.headers.get('X-Rundweg-Request') == '1'
                        and self.headers.get_content_type() == 'application/json', 'Der Schreibaufruf stammt nicht aus dem lokalen Rundweg.', 403)
                length = int(self.headers.get('Content-Length', '0'))
                require(0 < length <= 16000, 'Der Rundwegschritt ist zu groß oder unvollständig.', 400)
                request = json.loads(self.rfile.read(length))
                require(isinstance(request, dict), status=400)
                path = urlsplit(self.path).path
                if path == '/api/rundweg/handoffs':
                    return self.reply(journal.create(request))
                match = re.fullmatch(r'/api/rundweg/handoffs/([a-z0-9-]+)/(receipt|withdraw|adopt)', path)
                require(match is not None, 'Dieser Rundwegschritt ist nicht verfügbar.', 404)
                self.reply(journal.mutate(match[1], match[2], request))
            except Rejected as error:
                self.reply({'error': str(error)}, error.status)
            except (ValueError, TypeError, KeyError):
                self.reply({'error': 'Dieser Rundwegschritt ist unvollständig oder ungültig.'}, 400)
            except Exception:
                self.reply({'error': 'Die Speicherung konnte nicht sicher bestätigt werden. Lade den Rundweg erneut, bevor du denselben Schritt wiederholst.'}, 503)
    return Handler


def tree_digest(root):
    return digest({p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dazwischen-dist', type=Path, required=True)
    parser.add_argument('--state-dir', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8834)
    args = parser.parse_args()
    static = Path(__file__).resolve().parents[1] / 'server/static/variantenraum'
    daz = args.dazwischen_dist.resolve()
    state_dir = args.state_dir.resolve()
    require(all(p.is_relative_to(VOLUME) for p in (static, daz, state_dir)), 'Die vorgesehenen externen Speicherorte fehlen.', 503)
    volume_info = subprocess.run(['diskutil', 'info', '-plist', str(VOLUME)], check=True, capture_output=True).stdout
    import plistlib
    require(plistlib.loads(volume_info).get('VolumeUUID') == VOLUME_UUID, 'Das vorgesehene externe Volume fehlt.', 503)
    require((daz / 'index.html').is_file(), 'Der gebaute DAZ-Raum fehlt.', 503)
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    writer_lock = (state_dir / 'writer.lock').open('a')
    os.chmod(state_dir / 'writer.lock', 0o600)
    try:
        fcntl.flock(writer_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise Rejected('Dieses Rundwegjournal hat bereits einen schreibenden Dienst.', 503)
    journal = Journal(static / 'catalog.json', state_dir, tree_digest(daz), daz)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), make_handler(journal, static, daz))
    print('Lokaler Rundweg ist bereit: http://127.0.0.1:' + str(args.port) + '/variantenraum/index.html', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
