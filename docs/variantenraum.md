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

Der neue Ordner `server/static/variantenraum/`, der Katalog und das ergänzende isolierte Variantenmodell sind lokale Weiterentwicklung. Die öffentliche Basis enthält diese Ergänzungen noch nicht. Der Basislink ist eine reproduzierbare Herkunft, kein Beleg dafür, dass dieser Entwurf dort bereits veröffentlicht wurde. Ein späterer GitHub-Nachweis braucht den tatsächlich veröffentlichten Commit mit diesen Dateien.

Dieser Entwurf verwendet keine Mooncells-Zustands-API und verändert keinen kanonischen Systemzustand. Lokale Ableitungen bleiben im isolierten Modell und werden nicht automatisch in fremde Speicher, Produktionsräume oder Quellenbestände geschrieben. Bestehende Ressourcensperren und Schutzgrenzen bleiben unberührt; geschützte Laufzeitdienste wurden für diese Bestandszusammenfassung weder gestartet noch abgefragt.

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

## Isoliert ansehen

Im Repository-Stamm lässt sich ausschließlich der zusätzliche statische Ordner auf einem freien lokalen Port ausliefern:

```sh
python3 -m http.server 8767 --bind 127.0.0.1 --directory server/static/variantenraum
```

Danach `http://127.0.0.1:8767/` öffnen. Das startet einen einfachen statischen Dateiserver. Es benötigt weder Datenbank noch produktiven Mooncells-Server, keine Zustands-API und keine KiN-, TiSCH-, Kimi- oder Atlas-Laufzeit. Falls der Port belegt ist, einen anderen freien Port verwenden; keinen bestehenden Dienst beenden. Der Dateiserver dient einer lokalen Vorschau und veröffentlicht den Entwurf nicht auf GitHub.

Der zu prüfende menschliche Weg lautet: verständlicher Einstieg → Gesamtvariante → zuständiger Raum und sein Beitrag → abweichende oder weiterentwickelte Variante → begründeter Vergleich → nachvollziehbare Herkunft. Reload, Tastaturbedienung und schmale Ansicht brauchen praktische Oberflächenbelege. Bestehende Implementierungs- oder Modelltests ersetzen diese Annahme nicht.

## Begrenzte aktuelle Prüfbelege

Leitchat und Kernagent melden **34 bestandene Node-Tests** mit `node --test tests/variantenraum.test.mjs`; der Oberflächenagent meldet **44 bestandene DOM-Szenarien**. Die Modelltests prüfen unter anderem Originalerhalt, genaue Paket-/Kontext-/Mandatsbindung, Inhaltskonflikte, gerichtete Abhängigkeiten, lokale Entscheidungsepochen, Quellenreferenzen und den Unterschied zwischen ungeprüft und geprüft verworfen. Diese Belege gelten für das isolierte Modell und die zusätzliche Oberfläche.

Der Leitchat hat nativ die drei Fassungen, Vergleich und DAS-DAZWISCHEN-Raumfassung geprüft. Reload erhält Variante, Raumfassung und Vergleich. Der Enter-Rückweg führt zum genauen Vergleich und zur Variantenkarte zurück; Suche, Filterung und Fokus bleiben erhalten. Eine zunächst beobachtete Überbreite wurde korrigiert. Der anschließende native Wiederholungstest von Variante, Vergleich und Raumbeitrag bei **390 × 844** ergab jeweils `document.scrollWidth = 390`; auf dem Desktop ergaben **1675** Pixel Breite `document.scrollWidth = 1675`. Technische Details waren geschlossen; Browserwarnungs- und Fehlerprotokoll waren leer.

Diese ausgewählten Wege sind belegt. Eine vollständige Geräte- und Browserprüfung, der praktische Weg durch fremde Räume, ein tatsächlicher eigener DAZWISCHEN-Quittungseintrag und menschliche Annahme bleiben offen. Die beiden neuen Varianten führen Umsetzung und Prüfung deshalb weiterhin als **teilweise belegt**.

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
4. **Kimi:** Neue Schnitte erhalten die Originale; ein fehlerhafter Teil sperrt nicht pauschal alles. Quittung ist keine stellvertretende menschliche Zustimmung. Öffentliche Basis und lokale Weiterentwicklung bleiben prominent unterscheidbar. DAS DAZWISCHEN bleibt ein eigenständiger Quellenraum mit Rückweg. Die vorgeschlagenen Tests für Inhalt, Beziehung, Originalerhalt, Status, exakten Empfang und Quellenrückkehr sind einzeln nachzuweisen. Im tatsächlichen zweiten Rücklauf bestätigt Kimi gerichtete Abhängigkeiten statt einer globalen Sperre und ergänzt den Quittungsrückweg: wer verantwortlich ist, auf welchen Befund und welchen genauen Testlauf sich der Beleg bezieht. **Geprüft und verworfen** bleibt von **nie geprüft** unterscheidbar. Der tatsächliche eigene Quittungseintrag von DAS DAZWISCHEN ist offen; eine Schreibintegration ist nicht behauptet. Wer mit welchem Mandat einen Inhaltskonflikt in eine neue Ableitung überführt, bleibt ebenfalls offen. Zwei Fassungen und ein Einwand übertragen kein Eigentum.

Die neue Fassung übernimmt diese begrenzten Teile. Sie übernimmt weder eine globale Freigabepflicht noch eine globale Uhr, pauschale transitive Passung oder die Behauptung einer reparierten Produktionssynchronisation. Ein Konflikt betrifft die konkrete Beziehung und nachweislich davon abhängige Beziehungen; die Gesamtkompatibilität bleibt `unknown`. Der Katalog enthält keine erfundenen konkreten Werkbeziehungen, um das Modellbeispiel als Bestand erscheinen zu lassen.

Die neuen Bausteine sind an die jeweilige sichere Zusammenfassungsfassung gebunden. Die lokale Modellimplementierung und ihre Tests sind von diesen Konzept- und Antwortbelegen zu unterscheiden. Umsetzung, Prüfung und menschliche Annahme werden getrennt weitergeführt. Bei weiteren Antworten erhält jede sichere Zusammenfassung ihre eigene Revision und ihren Hash; übernommene und bewusst nicht übernommene Teile bleiben nachvollziehbar. Private Antworten werden nicht pauschal kopiert.
