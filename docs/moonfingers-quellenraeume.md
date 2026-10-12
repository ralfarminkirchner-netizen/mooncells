# Moonfingers: belegte Quellenräume

Diese Backend-Erweiterung baut auf dem Worktree-Stand von PR #1
(`c3cbfb8`) auf. Sie gibt Moonfingers eine stabile Zuordnung zu vorhandenen
Mooncells-Werken, Worktrees und Varianten; Quelleninhalte werden nicht erfunden.

## API-Vertrag

- `GET /api/health` meldet Dienst, Instanz, tatsächlichen Datenpfad und die
  Fähigkeiten `source-spaces`, `worktrees` und `source-ref`.
- `POST /api/source-spaces` nimmt `source_ref`, `title`, `content`, optional
  `notes` und einen vorhandenen `author_id` entgegen. Es erzeugt Werk,
  Worktree und Quellfassung mit einem gemeinsamen Speichervorgang.
  Die Antwort enthält `work`, `worktree`, `variant` und `created`.
- Quellenidentität ist das exakte Tupel aus `source_ref.system`, `kind` und
  `source_id`. Wiederholte Aufrufe liefern den vorhandenen Quellenraum und
  überschreiben weder Quellinhalt noch Herkunft. Ein vorhandenes Werk ohne
  passende belegte Quellfassung führt zu `409`; es wird nicht repariert oder
  durch eine erfundene Quellfassung ergänzt.
- `source_ref` enthält außerdem den lesbaren `title` sowie optional `locator`
  und `content_sha256`. Es bleibt an Werken, Varianten und Kanten erhalten.
- `POST /api/worktrees` legt einen weiteren Worktree für ein vorhandenes Werk
  und einen vorhandenen Autor an. `GET /api/works/{work_id}` liefert alle
  Worktrees und ihre Varianten; das bisherige Feld `worktree` bleibt erhalten.
- `POST /api/variants` erhält die bestehende Variantenlogik. `derived_from`
  verweist innerhalb desselben Worktrees auf eine vorhandene Variante.
  Werkübergreifende Beziehungen werden ausschließlich durch belegte
  Variantenkanten in `POST /api/edges` geführt, etwa `verweist-auf` mit dem
  ursprünglichen Quellenbezug und dessen unverändertem Prüfstatus.

## Eigentümer und Persistenz

Die konfigurierte Mooncells-Instanz ist der einzige aktive Schreiber ihrer
JSON-Datei. Moonfingers nutzt diese API und führt keinen zweiten
Variantenbestand. Die Originalquelle bleibt bei ihrem bisherigen Schreiber;
eine Mooncells-Quellfassung ist eine belegte Momentaufnahme.

`JsonStore` sperrt innerhalb eines Prozesses, schreibt zuerst eine temporäre
Datei und ersetzt die Zieldatei atomar. Das Anlegen eines Quellenraums ist
gegen parallele Anfragen derselben Instanz geschützt und rollt die drei neuen
Entitäten bei einem Speicherfehler zurück. Diese Zusage gilt nicht für mehrere
Prozesse, die dieselbe Datei beschreiben, oder für ungeprüfte Stromausfallsicherheit.

Der lokale Integrationsbetrieb nutzt ausdrücklich die Instanz
`mooncells-moonfingers`, einen Loopback-Listener und den externen Bestand unter
`Development/AppData/mooncells/state.json`. Nur diese Instanz prüft zusätzlich
Host, Origin und Browser-Fetch-Herkunft; andere Mooncells-Instanzen behalten den
bisherigen Zugriffsvertrag. Konkrete technische Kennungen und Speicherpfade
gehören in eine standardmäßig geschlossene Diagnoseansicht.

In `mooncells-moonfingers` bleibt der ganze Bestand lokal: Schreibzugriffe
starten keinen Auto-Sync, und auch bereits registrierte Peers erhalten keinen
automatischen Export. `POST /api/peers` und `POST /api/sync` antworten mit 403;
die direkten Push-/Pull-Helfer sind ebenfalls gesperrt. Vorhandene Peers können
lokal gelesen und gelöscht werden. Diese Grenze gilt auch für Gesprächsquellen.
Explizite lokale `GET /api/export`, `GET /api/changes` und `POST /api/import`
bleiben nach der Loopback-/Origin-Prüfung verfügbar. Diese Aufrufe öffnen keine
ausgehende Verbindung; ein angeforderter Export ist eine lokale Dokumentantwort.
Die automatische und manuelle Föderation anderer Mooncells-Instanzen bleibt
unverändert.

Railway-Dauerpersistenz ist weiterhin offen: Ein Deployment ohne eingebundenes
persistentes Volume verliert seinen JSON-Bestand beim Ersetzen des Containers.
`MOONCELLS_DATA=/data/state.json` ist nur zusammen mit einem tatsächlich
bereitgestellten Volume und einem geprüften Schreib-/Neustart-/Wiederlesepfad
eine Grundlage für eine Persistenzzusage. Diese Änderung erbringt keinen
Produktions-, Volume-, Vault- oder Deploymentnachweis.

## Prüfung ohne persönliche Daten

Die Python-Prüfungen erstellen ausschließlich bezeichnete Prüfdaten in einem
temporären Bereich. Auch der App-Import wird auf einen temporären Bestand
umgeleitet; auf diesem Mac ist der Prüfbereich auf dem registrierten externen
Volume. Aus der Arbeitskopie:

```sh
PYTHONDONTWRITEBYTECODE=1 \
MOONCELLS_TEST_TMPDIR=/Volumes/ThunderBolt4_2TB/Development/Tmp \
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Die Prüfungen decken Identität, konkurrierende Anlage, Rollback, Beziehungen,
Wiederlesen, Herkunft, die lokale Browsergrenze und eine tatsächliche
Gesprächsquellen-Anlage mit vorhandenem Mock-Peer ohne Export ab. Sie bestätigen keine
menschliche Formabnahme oder Produktionspersistenz.
