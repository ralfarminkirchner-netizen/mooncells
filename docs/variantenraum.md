# Gesamtgefüge als lebendiger Variantenraum

Dieser zusätzliche Entwurf macht einen begrenzten, öffentlich sicheren Ausschnitt des Gesamtgefüges lesbar. Er verbindet Quellenzuständigkeiten, konkrete Anschlussfragen, Gesamtvarianten und Dissens. Die beteiligten Räume behalten ihre Quellen, Arbeitsbestände und Schreibzuständigkeit. Die Übersicht begründet weder eine zentrale Autorität noch eine gemeinsame Pflichtstrecke.

Der Katalog ist ein bewusst begrenzter öffentlicher Entwurf. Er enthält bewusst ausgewählte Zusammenfassungen. Private Rohquellen, Autoren-E-Mails, lokale private Dateipfade, Zugangsdaten und ungeprüfte persönliche Inhalte gehören nicht hinein. Eine öffentliche Zusammenfassung ist keine Freigabe ihrer privaten Ausgangsquelle.

## Was hier verglichen wird

- **Ausgangsentwurf:** quellengebundene Zuständigkeiten und bisherige reale Übersicht, einschließlich der offenen praktischen Anschlüsse.
- **Föderierter Vergleich:** zusätzlicher Vorschlag für freiwillige Beiträge der unabhängigen Räume, Quellenrückwege und begründete Unterschiede.
- **Revidierte Teilübernahme:** konkrete neue Ableitung nach echten Google-, Grok- und Kimi-Antworten und einer Google↔Grok-Gegenreaktion. Übernommen werden lokale Entscheidungsepochen, genauer Paket-/Kontext-/Mandatsbezug, erhaltene Einwände und gerichtete Konfliktbedingungen. Inhaltskonflikte, unbekannte Abhängigkeiten, produktiver Statusimport und menschliche Annahme bleiben offen.

KiN / TRAGWERK, Mooncells, SPiRALCELLS / MiNDCEL, DER TiSCH, DAS DAZWISCHEN / Kimi, Jev und Laya, PHÄNOMENATLAS, SPEKTRUM und NEURO erscheinen als eigenständige Räume. Jev und Laya besitzen getrennte Bausteine; eine historische Namensähnlichkeit begründet keine Identität. SPEKTRUM hat ausdrücklich einen unbekannten Anschluss und wird nicht mit anderen Atlas-Räumen gleichgesetzt. Historische Zuständigkeitsangaben sind kein Beleg für einen aktuell aktiven Schreiber.

Die vier Achsen **Vorschlag**, **Umsetzung**, **Prüfung** und **menschliche Annahme** sind unabhängig. Eine implementierte Funktion ist nicht automatisch geprüft oder angenommen. Ein übernommener Beitrag ist nicht automatisch ein Mandat. Kontext und Mandat stehen deshalb zusätzlich bei jeder Gesamtvariante.

## Öffentliche Basis und lokale Weiterentwicklung

Die Ausgangsbasis ist [Mooncells auf GitHub](https://github.com/ralfarminkirchner-netizen/mooncells/tree/95f7923eb58b6a1ed540c2daa86c255998e39c0d), fest gebunden an den Commit `95f7923eb58b6a1ed540c2daa86c255998e39c0d` (kurz `95f7923`). Die dortige [README](https://github.com/ralfarminkirchner-netizen/mooncells/blob/95f7923eb58b6a1ed540c2daa86c255998e39c0d/README.md), das [Schema](https://github.com/ralfarminkirchner-netizen/mooncells/blob/95f7923eb58b6a1ed540c2daa86c255998e39c0d/docs/schema.md) und das [Konzept](https://github.com/ralfarminkirchner-netizen/mooncells/blob/95f7923eb58b6a1ed540c2daa86c255998e39c0d/docs/konzept.md) beschreiben die damalige Grundlage.

Der neue Ordner `server/static/variantenraum/`, der Katalog und das ergänzende isolierte Variantenmodell sind im [veröffentlichten Ergänzungscommit](https://github.com/ralfarminkirchner-netizen/mooncells/commit/ac1935653d9d10365bd4d473dbf881e14ce39c4c) nachweisbar. [Entwurfs-PR #4](https://github.com/ralfarminkirchner-netizen/mooncells/pull/4) führt diesen Stand gegen `main`; bei dieser Dokumentationsergänzung ist er offen und nicht zusammengeführt. Die öffentliche Ausgangsbasis enthält diese Ergänzungen noch nicht. Ihr Basislink bleibt die reproduzierbare Herkunft; Commit und PR belegen die veröffentlichte Entwicklung, keine menschliche Annahme oder produktive Integration.

Dieser Entwurf verwendet keine Mooncells-Zustands-API und verändert keinen kanonischen Systemzustand. Lokale Ableitungen bleiben im isolierten Modell und werden nicht automatisch in fremde Speicher, Produktionsräume oder Quellenbestände geschrieben. Bestehende Ressourcensperren und Schutzgrenzen bleiben unberührt; geschützte Laufzeitdienste wurden für diese Bestandszusammenfassung weder gestartet noch abgefragt. Der unten beschriebene zusätzliche lokale Rundwegbroker führt ein eigenes begrenztes Übergabejournal; er ist keine kanonische Mooncells-Zustands-API.

## Quellenbindung und Reproduzierbarkeit

Der Datenvertrag steht in `server/static/variantenraum/catalog.json`: `schemaVersion`, `title`, `revision`, `sources`, `rooms`, `components`, `variants`, `relations` und `dissent`. Quellen und Bausteine bleiben über ihre Kennungen zugeordnet. Diese Kennungen, Hashes und beobachteten Git-Stände gehören in Daten und eine ausdrücklich geöffnete technische Detailansicht, nicht in normale Titel, Hilfetexte oder Accessibility-Namen.

Jede verfügbare Quelle enthält eine bewusst ausgewählte öffentliche `summary`. `contentHash` ist **SHA-256 exakt der UTF-8-Zeichenfolge dieses Feldes**, ohne zusätzliches Zeilenende. Er ist kein Hash der privaten Originaldatei und kein Integritätsnachweis ihrer Laufzeit. Die Zusammenfassungsfassung steht in `revision`; eine Bindung mit `bindingStatus: "pinned"` übernimmt dieselbe Fassung und denselben Hash. Sie bindet diesen öffentlichen Bezug, nicht einen eingefrorenen ausführbaren Gesamtstand. Eine unbekannte Quelle behält `revision: null`, `contentHash: null` und `bindingStatus: "unknown"`.

Beobachtete lokale Git-Zeiger stehen ausschließlich unter `technicalDetails.observedHead`. Die damit verbundenen Arbeitsbäume waren verändert (`workingTree: "dirty"`). Ein solcher Zeiger ist **kein** reproduzierbares Abbild dieser Änderungen und wird ausdrücklich mit `executableSnapshot: false` geführt. Die Bestandsprüfung war begrenzt; sie hat weder Vollständigkeit noch aktuelle Laufzeit, aktiven Schreiber oder menschliche Gesamtannahme nachgewiesen.

Quellenstatus `verified` bedeutet hier, dass der angegebene Bezug beziehungsweise die ausgewählte Zusammenfassung für diesen Katalog geprüft wurde. Er bedeutet weder sachliche Vollständigkeit jeder Ausgangsbehauptung noch eine heute wiederholte praktische Prüfung. Die Varianten halten diese Grenzen in ihren eigenen Prüf- und Annahmeachsen fest.

Der Hashbezug lässt sich ohne private Quellen prüfen:

```sh
python3 - <<'PY_HASH'
import hashlib, json
from pathlib import Path
catalog = json.loads(Path("server/static/variantenraum/catalog.json").read_text())
for source in catalog["sources"]:
    if source["contentHash"] is not None:
        actual = hashlib.sha256(source["summary"].encode("utf-8")).hexdigest()
        assert actual == source["contentHash"]
print("Öffentliche Zusammenfassungsbindungen stimmen.")
PY_HASH
```

## Konvergenzaussagen der bisherigen Dokumentation

Die öffentliche Basis beschreibt Deduplizierung über Kennungen, unveränderte Eltern, Ableitungen und Mengenvereinigung. Diese Aussagen sind unter ihren benannten Modellannahmen zu lesen. Überspringt ein Import vorhandene Kennungen, verhindert das doppelte Einfügen; daraus folgt keine allgemeine Konvergenz, wenn unter derselben Kennung unterschiedliche Inhalte geliefert werden. Dann kann der zuerst übernommene Inhalt je Instanz verschieden bleiben. Die damalige Statusänderung von Varianten ist außerdem eine dokumentierte Ausnahme von unveränderlichen Feldern und braucht eine eigene Konflikt- und Reihenfolgeregel.

Historische Sync- und Testaussagen sind daher begrenzte Belege des damaligen Bausteins. Sie werden hier nicht als neuer Nachweis für beliebige veränderliche Daten, heutige Interoperabilität, den praktischen Gesamtweg oder menschliche Annahme übernommen. Diese Einordnung korrigiert keine fremden Quellen stillschweigend; der Katalog hält sie als dokumentierten Einwand neben dem Ausgangsentwurf fest.

Eine isolierte Ausführung des tatsächlichen öffentlichen `JsonStore.import_document` mit künstlichen, durch die öffentlichen Modelle validierten Daten bestätigt diese Grenze in **29 gezielten Prüfaussagen**: Bei gleicher Kennung und abweichenden Notizen oder Labels behält A→B den Inhalt A und B→A den Inhalt B; der zweite Inhalt wird ohne Konfliktbericht übersprungen. Beim Status gewinnt dagegen der zuletzt importierte Wert. Ein unmittelbar wiederholtes identisches Paket lässt den gespeicherten Zustand bytegleich. Wird ein früheres Statuspaket nach einer zwischenzeitlichen Statusänderung erneut importiert, überschreibt es den Status wieder; eine Aktualitätsprüfung fehlt. Dies prüft den tatsächlichen Store, keinen HTTP-Austausch oder produktiven Systemweg, und repariert den Import nicht.

Die portable Probe `tests/public-import-probe.py` benötigt Python ab 3.9, bereits vorhandenes Pydantic 2 und den öffentlichen Basiscommit im lokalen Git-Bestand. Sie prüft Git-Blob und SHA-256 von `server/store.py` und `server/models.py` am fest gebundenen Commit `95f7923eb58b6a1ed540c2daa86c255998e39c0d`; Arbeitskopiedateien werden nicht geladen. Prüfverzeichnis und Elternordner der JSON-Ergebnisdatei müssen bereits bestehen; beide Argumente sind explizite absolute Pfade. Das Skript schreibt die angegebene Ergebnisdatei, installiert nichts und entfernt seine temporären Quellen und Kunst-Daten nach dem Lauf:

```sh
python3 tests/public-import-probe.py \
  --temp-root /absoluter/bestehender/pruefordner \
  --output /absoluter/bestehender/pruefordner/ergebnis.json
```

## Isoliert ansehen

Im Repository-Stamm lässt sich ausschließlich der zusätzliche statische Ordner auf einem freien lokalen Port ausliefern:

```sh
python3 -m http.server 8767 --bind 127.0.0.1 --directory server/static/variantenraum
```

Danach `http://127.0.0.1:8767/` öffnen. Das startet einen einfachen statischen Dateiserver. Es benötigt weder Datenbank noch produktiven Mooncells-Server, keine Zustands-API und keine KiN-, TiSCH-, Kimi- oder Atlas-Laufzeit. Falls der Port belegt ist, einen anderen freien Port verwenden; keinen bestehenden Dienst beenden. Der Dateiserver dient einer lokalen Vorschau und veröffentlicht den Entwurf nicht auf GitHub. Er liefert weder die Rundweg-API noch den DAZ-Build aus; dafür gilt der gesonderte Startbefehl weiter unten.

Der zu prüfende menschliche Weg lautet: verständlicher Einstieg → Gesamtvariante → zuständiger Raum und sein Beitrag → abweichende oder weiterentwickelte Variante → begründeter Vergleich → nachvollziehbare Herkunft. Reload, Tastaturbedienung und schmale Ansicht brauchen praktische Oberflächenbelege. Bestehende Implementierungs- oder Modelltests ersetzen diese Annahme nicht.

## Historische Prüfbelege des Katalogstands

Leitchat und Kernagent melden **34 bestandene Node-Tests** mit `node --test tests/variantenraum.test.mjs`; der Oberflächenagent meldet **44 bestandene DOM-Szenarien**. Die Modelltests prüfen unter anderem Originalerhalt, genaue Paket-/Kontext-/Mandatsbindung, Inhaltskonflikte, gerichtete Abhängigkeiten, lokale Entscheidungsepochen, Quellenreferenzen und den Unterschied zwischen ungeprüft und geprüft verworfen. Diese Belege gelten für das isolierte Modell und die zusätzliche Oberfläche.

Der Leitchat hat nativ die drei Fassungen, Vergleich und DAS-DAZWISCHEN-Raumfassung geprüft. Reload erhält Variante, Raumfassung und Vergleich. Der Enter-Rückweg führt zum genauen Vergleich und zur Variantenkarte zurück; Suche, Filterung und Fokus bleiben erhalten. Eine zunächst beobachtete Überbreite wurde korrigiert. Der anschließende native Wiederholungstest von Variante, Vergleich und Raumbeitrag bei **390 × 844** ergab jeweils `document.scrollWidth = 390`; auf dem Desktop ergaben **1675** Pixel Breite `document.scrollWidth = 1675`. Technische Details waren geschlossen; Browserwarnungs- und Fehlerprotokoll waren leer.

Diese ausgewählten Wege waren für diesen Katalogstand belegt. Eine vollständige Geräte- und Browserprüfung, der praktische Weg durch fremde Räume, ein tatsächlicher eigener DAZWISCHEN-Quittungseintrag und menschliche Annahme blieben damals offen. Die beiden neuen Varianten führen Umsetzung und Prüfung deshalb als **teilweise belegt**. Der nachfolgend dokumentierte lokale Rundweg ergänzt die technische Umsetzung; er schreibt diese historischen Quellenfassungen, Hashes und Variantenbindungen nicht rückwirkend um.

Die sichere Belegzusammenfassung steht als eigene Quelle im Katalog, nun in ihrer zweiten Fassung. Ihre Fassung und ihr SHA-256-Hash binden die Prüfachsen der beiden neuen Varianten. Verweise auf `tests/variantenraum.test.mjs` und dieses Dokument erlauben die spätere Prüfung im tatsächlich veröffentlichten Stand; der historische Basislink allein enthält diese Belege nicht.

## Öffentlicher Quellenfall mit Rückweg

In der Mooncells-Raumansicht führen **Quellen und Herkunft** zu zwei getrennten öffentlichen Quellen am exakt gebundenen Basiscommit:

- [Importanleitung, README Zeilen 40–64](https://github.com/ralfarminkirchner-netizen/mooncells/blob/95f7923eb58b6a1ed540c2daa86c255998e39c0d/README.md#L40-L64): Die Anleitung erklärt Deduplizierung und einen Austausch, der konvergieren soll. Die README nennt den Status später selbst als [veränderliche Ausnahme, Zeilen 82–89](https://github.com/ralfarminkirchner-netizen/mooncells/blob/95f7923eb58b6a1ed540c2daa86c255998e39c0d/README.md#L82-L89).
- [Importentscheidung, store.py Zeilen 162–199](https://github.com/ralfarminkirchner-netizen/mooncells/blob/95f7923eb58b6a1ed540c2daa86c255998e39c0d/server/store.py#L162-L199): Neue Kennungen werden eingefügt. Bei bekannter Variante und abweichendem Status wird ausschließlich der Status aktualisiert; sonst wird der bekannte Eintrag übersprungen. Ein anderer Inhalt unter derselben Kennung erhält in dieser Funktion keine Konfliktmeldung und keine neue Ableitung.

Der konkrete Gegenbefund begrenzt die allgemeine Nichtüberschreibungs- und Konvergenzaussage: bekannte Kennung, unveränderlicher Inhalt und veränderlicher Status brauchen unterschiedliche Regeln. Die Rückwege führen zu den genauen öffentlichen Zeilen; private Passagen werden dafür nicht benötigt. Das ist ein nachlesbarer Quellenvergleich. Gemeinsame Graphintegration, produktive Konfliktreparatur und daraus abgeleitete kanonische Werkbeziehungen sind damit weiterhin offen.

## Echte Gegenlese und begründete Teilübernahme

Der dritte Entwurf ist aus tatsächlichen, im Leitchat sichtbar gelesenen Antworten entstanden. Die öffentliche Fassung enthält ausschließlich freigegebene Paraphrasen. Anbieter, Reviewkey, tatsächliche Vorvariante und Reaktion bleiben in den technischen Quelldaten erhalten. Die Vorvariante ist der **Föderierte Vergleich** der ersten Katalogfassung; der Ausgangsentwurf bleibt daneben bestehen. Die Originaldialoge sind öffentlich nicht vollständig rekonstruierbar. Der Digest belegt hier nachvollziehbare Auswahl und Grenzen, keinen unabhängig öffentlich prüfbaren vollständigen Dialog.

1. **Grok:** Urteil, Geltungsbereich und genauer Quittungsbezug getrennt halten; öffentliche Importgrenzen berücksichtigen; Teilübernahme als neue Ableitung mit erhaltenem Dissens führen. Drei Botrollen in einer Grok-Gruppe zählen als ein Anbieterkontext.
2. **Google / Gemini:** Eine späte Quittung nach Rückzug darf keine überholte Annahme wieder aktivieren; Rollenwechsel darf Urheber und Zuständigkeit offener Einwände nicht verlieren. Übernommen wird eine monotone **lokale Entscheidungsepoche je Raum**, ohne globale Uhr. Werk und Fassung allein reichen nicht als Quittungsbindung: Paket, Kontext und Mandat bleiben erhalten.
3. **Google nach Grok, Grok nach Google:** In einem rautenförmigen Ableitungsfall kann ein Baustein eine gesperrte Voraussetzung indirekt weitertragen. Bekannte gerichtete Abhängigkeiten übernehmen diese Konfliktbedingung. Unbekannte Abhängigkeiten bleiben unklar. Die Sperre einer Beziehung klärt keinen abweichenden Inhalt unter derselben Kennung; Notiz, Titel oder Status brauchen einen eigenen Inhaltseinwand oder eine neue Ableitung. Gesamtpassung wird nicht aus Teilpassung abgeleitet.
4. **Kimi:** Neue Schnitte erhalten die Originale; ein fehlerhafter Teil sperrt nicht pauschal alles. Quittung ist keine stellvertretende menschliche Zustimmung. Öffentliche Basis und lokale Weiterentwicklung bleiben prominent unterscheidbar. DAS DAZWISCHEN bleibt ein eigenständiger Quellenraum mit Rückweg. Die vorgeschlagenen Tests für Inhalt, Beziehung, Originalerhalt, Status, exakten Empfang und Quellenrückkehr sind einzeln nachzuweisen. Im tatsächlichen zweiten Rücklauf bestätigt Kimi gerichtete Abhängigkeiten statt einer globalen Sperre und ergänzt den Quittungsrückweg: wer verantwortlich ist, auf welchen Befund und welchen genauen Testlauf sich der Beleg bezieht. **Geprüft und verworfen** bleibt von **nie geprüft** unterscheidbar. Im damaligen Antwort- und Katalogstand war der tatsächliche eigene Quittungseintrag von DAS DAZWISCHEN offen; eine Schreibintegration war nicht behauptet. Wer mit welchem fachlichen Mandat einen Inhaltskonflikt auflöst, bleibt weiterhin offen. Der unten ergänzte technische Ausführungsauftrag beantwortet diese fachliche Zuständigkeit nicht. Zwei Fassungen und ein Einwand übertragen kein Eigentum.

Die neue Fassung übernimmt diese begrenzten Teile. Sie übernimmt weder eine globale Freigabepflicht noch eine globale Uhr, pauschale transitive Passung oder die Behauptung einer reparierten Produktionssynchronisation. Ein Konflikt betrifft die konkrete Beziehung und nachweislich davon abhängige Beziehungen; die Gesamtkompatibilität bleibt `unknown`. Der Katalog enthält keine erfundenen konkreten Werkbeziehungen, um das Modellbeispiel als Bestand erscheinen zu lassen.

Die neuen Bausteine sind an die jeweilige sichere Zusammenfassungsfassung gebunden. Die lokale Modellimplementierung und ihre Tests sind von diesen Konzept- und Antwortbelegen zu unterscheiden. Umsetzung, Prüfung und menschliche Annahme werden getrennt weitergeführt. Bei weiteren Antworten erhält jede sichere Zusammenfassung ihre eigene Revision und ihren Hash; übernommene und bewusst nicht übernommene Teile bleiben nachvollziehbar. Private Antworten werden nicht pauschal kopiert.

## Lokaler Rundweg mit DAS DAZWISCHEN

Der ergänzte lokale Rundweg verbindet die Variantenoberfläche mit dem tatsächlich gebauten DAZ-Adapter einer kontrollierten isolierten Arbeitskopie. `scripts/serve-rundweg.py` verwendet ausschließlich die Python-Standardbibliothek und bindet an `127.0.0.1`. Unter derselben Adresse liegen `/variantenraum/`, `/dazwischen/` und die begrenzte `/api/rundweg/`-API. Der zusätzliche Browserclient prüft Paket-, Fassungs- und Quittungsbindung; ohne diesen Broker bleibt die statische Variantenansicht lesbar. Produktive Räume und die kanonische Mooncells-Zustands-API werden dadurch nicht angebunden.

Die Übergabe enthält die ausgewählte Gesamtfassung als Snapshot, ihre genaue Katalog- und Inhaltsbindung, die zu DAS DAZWISCHEN gehörenden Bausteinbindungen, öffentliche Quellenzusammenfassungen und zugehörigen Dissens. Der gespeicherte Rückpfad hält die Ausgangsansicht mit Auswahl, Vergleich, Suche, Filter und Raumzustand fest. **Öffentliche Zusammenfassungen sind keine Originalpassagen.** Ein privater Quelleninhalt, genauer privater Quellenfokus oder privater Verlauf wird weder übertragen noch durch diesen Rundweg erschlossen. DAZ-Quellenparser bleiben eigenständig.

Der technische Ausführer ist fest **Codex**, mit der Rolle **Technische Ausführung**. Das Paket bindet den aktuellen Userauftrag wortgetreu: „Mach jetzt mit dem echten Rundweg weiter: vom Variantenraum nach DAS DAZWISCHEN, mit verantworteter Quittung und nachvollziehbarer Rückkehr in die Gesamtfassung. Setze die fehlenden Anschlüsse um und prüfe den Weg praktisch.“ Dieser Umfang erlaubt lokalen Übergang, technischen Empfang und nachvollziehbaren Rückweg. Er erteilt weder fachliche Entscheidungshoheit noch menschliche Annahme. Ein bewusster Empfangsklick verlangt einen kurzen Befund; die Quittung bleibt `transport: received`, `review: not-reviewed`, `humanAcceptance: open`. Auch ein ausgefüllter Befund ändert diese Grenzen nicht.

### Journal, Wiederholung und neue Ableitung

Das lokale Journal `rundweg.json` enthält Pakete mit öffentlichen Snapshots/Zusammenfassungen, Quittungen, Rücknahmen und ausdrücklich erzeugte Ableitungen. Es ist keine Sammlung privater Originalquellen. Der Startbefehl hält genau einen Schreiber über eine Dateisperre; parallele Zugriffe desselben Prozesses werden serialisiert. Speichern erfolgt über eine neue Datei mit restriktiven Rechten, `fsync` und atomarem Austausch. Das Journal ist auf 500 Übergaben und acht Millionen kanonische JSON-Byte begrenzt. Ein nach dem Dateiaustausch auftretender Sicherungsfehler wird als ungewisser Speicherabschluss behandelt; erneutes Laden und dieselbe Operation erlauben die Klärung.

Paket, Ausgangsfassung und Quittung besitzen getrennte Inhaltsdigests. Eine wiederholte identische Operation liefert dasselbe gespeicherte Ergebnis; dieselbe Operationskennung mit anderem Inhalt wird verworfen. Neue Übergaben und Ableitungen prüfen die aktuelle Ausgangsfassung. Neue Übergaben, Quittungen und Ableitungen prüfen zusätzlich den tatsächlichen DAZ-Build gegen die beim Brokerstart gebundene Fassung. Ein geänderter Build verlangt eine neue Serverbindung; bestehende Historie wird dadurch nicht umgeschrieben.

**Rücknahme** markiert die Übergabe als zurückgezogen und erhält ihren bisherigen Verlauf. Danach dürfen weder eine neue Quittung noch eine neue Ableitung daran angehängt werden. Eine schon vorhandene Ableitung bleibt als historische Fassung bestehen. **Ableitung** ist ein eigener ausdrücklicher Schritt nach dem technischen Empfang: Der Broker erzeugt eine neue Gesamtfassung mit Herkunfts- und Quittungsbezug, erhält Ausgangsfassung und Einwände und speichert die neue Fassung im lokalen Journal. Ihre menschliche Annahme bleibt offen, auch wenn eine Elternfassung anders bewertet war. Nach Reload werden gespeicherte Ableitungen vor der Auflösung der URL-Auswahl eingelesen. Dieser Schreibweg verändert keinen produktiven DAZ-Quellenbestand und entscheidet keinen fachlichen Inhaltskonflikt.

### Adapter und Start

Der weitergebbare [DAZ-Adapter samt genauer Basis- und Anwendungsprüfung](../integrations/README.md) besteht aus sechs Dateien beziehungsweise Dateiänderungen. Er setzt die tatsächlich kopierte, lokal weiterentwickelte DAZ-Basis voraus und ist kein allgemeiner Patch gegen deren Git-HEAD. Das gesamte DAZ-Arbeitsverzeichnis, private Quellen, Abhängigkeiten und Builddateien werden nicht in dieses Repository kopiert.

Nach geprüfter Adapteranwendung und einem DAZ-Build mit `--base=/dazwischen/` aus dem Mooncells-Repository-Stamm starten. Das folgende Beispiel verwendet ausschließlich registrierte externe Speicherorte; der Journalordner ist ein eigener lokaler Laufzeitbestand:

```sh
python3 scripts/serve-rundweg.py \
  --dazwischen-dist /Volumes/ThunderBolt4_2TB/Development/Projects/dazwischen-rundweg-20261027/dist \
  --state-dir /Volumes/ThunderBolt4_2TB/Development/Projects/mooncells-rundweg-state \
  --port 8834
```

Danach `http://127.0.0.1:8834/variantenraum/index.html` öffnen. Der Broker prüft Zielpfade und registriertes Volume vor dem Start. Einen freien Port verwenden und vorhandene Dienste nicht beenden. Ein zweiter Schreiber mit demselben Journal wird abgewiesen. Die API akzeptiert Änderungen nur am lokalen Ursprung mit ausdrücklichem Rundweg-Header und JSON; sie ist keine extern erreichbare Schreibschnittstelle.

Für diesen ergänzten Implementierungsstand meldet der Leitchat **47 bestandene Node-Tests und 11 bestandene Python-Tests**. Der DAZ-Agent meldet **114 bestandene Node-Tests**, darin **16 Adaptertests**, sowie erfolgreiche TypeScript-, Adapter-Lint- und Vite-Buildprüfungen. Die Tests betreffen unter anderem Digestbindung, Wiederholung, veraltete Fassungen, Rücknahme, Ableitung, exklusiven Schreiber und Speicherfehler. Diese technischen Belege sind von den historischen Anbieterantworten getrennt: Google, Grok und Kimi haben den aktuellen PR-Code und diesen Testlauf nicht unabhängig bestätigt. Menschliche Annahme bleibt offen.

### Praktisch begangener Rundweg

Am 27. Oktober 2026 wurde der Weg im tatsächlichen Browser gegen den lokalen Broker und den isolierten DAZ-Build durchlaufen: Aus der Raumansicht von DAS DAZWISCHEN in der revidierten Teilübernahme wurde die gebundene Übergabe geöffnet, der lesbare Beitrag samt Quellenzusammenfassungen und Einwänden geprüft und der technische Empfang mit Befund quittiert. Ein leerer oder zu kurzer Befund erlaubte keine Quittung. Nach Neuladen blieb die Quittung sichtbar. Der Rücklink wurde mit der Tastatur ausgelöst und führte exakt zur gespeicherten Ansicht einschließlich Vergleich, Raumfassung, Suche und Filter.

Anschließend wurde ausdrücklich eine neue Gesamtfassung mit diesem Rundwegbeleg erzeugt. Sie blieb nach Neuladen auswählbar; die drei Katalogfassungen blieben erhalten. Zehn zusätzliche Prüfungen am tatsächlichen Journal bestätigten unter anderem unveränderten Ausgangssnapshot, erhaltene Bausteinbindungen, Einwände und Prüfstände, die Bindung der Quittung an Paket und Zielbuild sowie offene menschliche Annahme. Eine zweite Übergabe wurde ohne Quittung zurückgenommen; nach erneutem Öffnen und Neuladen zeigte DAZ nur den historischen Beleg und bot keinen neuen Empfang an.

Beide Oberflächen wurden bei 390 × 844 Pixeln ohne horizontale Überbreite geprüft. Technische Details waren geschlossen; in den geprüften sichtbaren Texten erschienen keine technischen Kennungen. Die erfassten Browser-Warnungs- und Fehlerprotokolle waren leer. Die praktische Probe belegt diesen lokalen technischen Rundweg mit öffentlichen Zusammenfassungen und konfiguriertem Codex-Ausführer. Sie belegt keine persönliche Identitätsprüfung, keine fachliche Annahme und keine Integration in den produktiven DAZ-Werkraum.
