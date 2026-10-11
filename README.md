# Mooncells — Prototyp

Lebendiges Gesamtwerk, Verfahren im Zentrum: Werke mit Worktrees paralleler
Varianten, typisierte Kanten, dokumentierte Befunde — föderiert betrieben
(Menschen + Modelle auf beliebig vielen Instanzen).

- `docs/schema.md` — **Teil 1:** Datenmodell + Mooncells Document Format v1;
  **Teil 2:** das Netz (zweistufiger Graph, Operations-Algebra, Traversierung,
  Fitness/Selektion, Zeit, Provenienz, Föderation, autonome Agenten, Schema-v2)
- `server/` — FastAPI-Server mit JSON-Datei-Storage und Browser-Oberfläche

## Voraussetzungen

```bash
pip install -r requirements.txt
```

## Server starten

Eine Instanz:

```bash
python -m server.app --port 8400 --data data/state.json --instance "instanz-ralf"
```

Dann im Browser öffnen: **http://127.0.0.1:8400**

Alternativ direkt mit uvicorn (Instanz-Name dann via Umgebungsvariable):

```bash
MOONCELLS_INSTANCE=instanz-ralf MOONCELLS_DATA=data/state.json \
  uvicorn server.app:app --port 8400
```

Der komplette Zustand liegt in einer einzigen JSON-Datei (`--data`),
atomar geschrieben (tmp + rename). Die Storage-Klasse (`server/store.py`)
kann später 1:1 durch eine Datenbank-Implementierung ersetzt werden.

## Zwei Instanzen mit Export/Import testen

```bash
# Instanz A (Port 8400) und Instanz B (Port 8401), getrennte Datenordner
python -m server.app --port 8400 --data runs/a/state.json --instance instanz-a &
python -m server.app --port 8401 --data runs/b/state.json --instance instanz-b &

# 1) A exportiert (per API oder Download-Button in der Oberfläche)
curl -s http://127.0.0.1:8400/api/export > export-a.json

# 2) B importiert — Merge per UUID-Dedupe, nichts wird überschrieben
curl -s -X POST http://127.0.0.1:8401/api/import \
  -H 'Content-Type: application/json' -d @export-a.json

# 3) B ergänzt eigene Varianten, exportiert, A importiert → Konvergenz
curl -s http://127.0.0.1:8401/api/export > export-b.json
curl -s -X POST http://127.0.0.1:8400/api/import \
  -H 'Content-Type: application/json' -d @export-b.json

# 4) Beide Seiten identisch?
diff <(curl -s http://127.0.0.1:8400/api/graph) <(curl -s http://127.0.0.1:8401/api/graph)
```

Der Import-Report zeigt je Collection `added` (neu) und `skipped` (bekannte UUID,
nicht überschrieben). Gleicher Import zweimal → alles `skipped`, Zustand unverändert.

## API-Übersicht

| Endpunkt | Zweck |
|---|---|
| `POST /api/agents` · `GET /api/agents` | Agent registrieren/auflisten |
| `POST /api/works` · `GET /api/works` | Werk anlegen (legt Worktree mit an)/lesen |
| `POST /api/variants` | Variante im Worktree (`derived_from: null` = Wurzel) |
| `POST /api/edges` | Kante setzen (`remixt-aus`, `erweitert`, `testet`, `widerspricht`, `bewertet`) |
| `POST /api/findings` | Befund an Kante oder Variantenpaar |
| `GET /api/graph` | Alles auf einmal (für die Oberfläche) |
| `GET /api/export?work_ids=…&since=…` | Mooncells Document (gesamt oder Ausschnitt) |
| `POST /api/import` | Document importieren (UUID-Dedupe-Merge) |
| `GET /api/changes?since=…` | Nur Neu-Einfügungen seit Zeitstempel (Pull-Sync-Feed) |
| `POST /api/sync` | `{peer: "http://…"}` — bidirektional: push + pull, beide Seiten konvergieren |

## Live-Synchronisation zwischen Instanzen

**Per Klick:** In der Oberfläche oben auf **⇄ Sync**, Peer-URL eingeben
(z. B. `http://127.0.0.1:8401`). Der Server pusst dann seinen Zustand an den
Peer und holt den Peer-Zustand zurück — Merge per UUID-Dedupe, konfliktfrei.

**Per API:**

```bash
curl -s -X POST http://127.0.0.1:8400/api/sync \
  -H 'Content-Type: application/json' -d '{"peer":"http://127.0.0.1:8401"}'
```

**Pull-basiert** (für regelmäßigen Abgleich ohne Gegenaktion):

```bash
# Peer fragt periodisch nach Neuem
curl -s "http://127.0.0.1:8401/api/changes?since=2026-10-11T09:00:00" \
  | curl -s -X POST http://127.0.0.1:8400/api/import -H 'Content-Type: application/json' -d @-
```

Getestetes Szenario: A befüllt → Sync → B hat alles; B ergänzt parallel →
Sync zurück → beide Instanzen identisch (`diff` der `/api/graph`-Ausgaben leer).
Nicht erreichbare Peers werden mit `502` und lesbarer Meldung abgelehnt.

## Auto-Sync

Peers werden pro Instanz registriert (`POST /api/peers {"url": "https://…"}`,
in der Oberfläche im Panel „Peers & Auto-Sync"). **Jeder lokale Schreibzugriff**
(Agent, Werk, Variante, Kante, Befund) pusht danach automatisch den eigenen
Export an alle registrierten Peers — asynchron im Hintergrund, Fehler beim
Peer blockieren oder verwerfen den lokalen Schreibzugriff nie. Ergebnisse der
letzten Läufe: `GET /api/autosync-log`. Getestet lokal (zwei Instanzen) und
über das Internet (lokal ⇄ Railway).

## Deployment

- **GitHub:** <https://github.com/ralfarminkirchner-netizen/mooncells>
- **Railway:** live unter <https://mooncells-production.up.railway.app> —
  Deploy via `Procfile` (`python -m server.app --host 0.0.0.0 --port $PORT`),
  Host/Port/Instanz werden aus `MOONCELLS_HOST`/`PORT`/`MOONCELLS_INSTANCE` gelesen.
  Neu deployen: `railway up` im Projektverzeichnis.
- **Hinweis:** das JSON-File-Storage ist auf Railway flüchtig (neuer Deploy =
  leerer Zustand). Für dauerhaften Betrieb dort: Railway-Volume mounten und
  `MOONCELLS_DATA=/data/state.json` setzen — oder auf die Datenbank-Ausbaustufe warten.

## Oberfläche

Liste der Werke mit eingerückten Variantenbäumen (Wurzel + abgeleitete Zweige),
Kanten- und Befundstabellen, Formulare für alle Grundoperationen, Peer-Verwaltung
mit Auto-Sync-Log, Export-Download und Import-Upload direkt im Browser.

## Ausblick: nächste Ausbaustufen

1. **GitHub-gesteuertes Deployment:** Railway-Service an das Repo koppeln, dann
   reicht `git push` für Auto-Deploys.
2. **Persistenz:** Volume-Template für Railway (`MOONCELLS_DATA=/data/state.json`)
   oder `JsonStore`-Interface gegen SQLite/Postgres implementieren.
3. **Echte Verteilung:** Websocket/Server-Sent-Events broadcasten neue
   Entitäten an registrierte Peers; die Merge-Logik (`store.import_document`)
   bleibt unverändert — nur der Transport wechselt von Request zu Stream.
4. **Identität auf Netzwerkebene:** Peers als registrierte Agents mit
   Instanz-URL im `description`-Feld, später Signatur je Document.
