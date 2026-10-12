"""
Baut den Ideenraum als Mooncells-Dokument (MDF v1) — Version 2.

Änderungen gegen V1:
- IDs deterministisch (uuid5, Schlüssel-seediert) — Dokument ist jetzt
  idempotent regenerierbar und Import-Dedupe-sicher.
- INVARIANZ-TRANSDUKTION-WELTENSYSTEM vollständig importiert
  (docs/quellen/, sha256 a05fe677…9a57) als Variante, abgeleitet aus der
  bisherigen Zitat-Rekonstruktion — die bleibt als Vorgänger stehen.
- KiNFORMER-Aktualitäts-Variante (2026-10-12) aus der Codex-Zusammenführung
  (22 Chats): fünf Entwicklungslinien + Technik-Befundtabelle.

Quellenlage (ehrlich markiert):
- erkenntnis-raki.txt und INVARIANZ-Original liegen vollständig vor.
- Grundformationen / PDA-Anforderungen / Codex-Forschungswelt liegen im
  KiNTEGRiTY-/TRAUMAATLAS-Bestand; ihre Varianten tragen Zitate und sind
  als 'referenz-import' gekennzeichnet.
Ausgabe: docs/ideenraum-2026-10.json (Mooncells Document Format v1)
"""

import json
import uuid
from pathlib import Path

NS = uuid.uuid5(uuid.NAMESPACE_URL, "https://mooncells.local/ideenraum-2026-10")
def u(key: str) -> str:
    return str(uuid.uuid5(NS, key))

NOW = "2026-10-12T18:30:00Z"

agents = [
    {"id": (RALF := u("agent:ralf")), "handle": "ralf", "agent_type": "human",
     "description": "Projektgründer — Quelle der Geistesblitze und Briefe",
     "created_at": NOW},
    {"id": (KIMI := u("agent:kimi")), "handle": "kimi-work-session", "agent_type": "model",
     "description": "Kimi-Work-Session — baut den Ideenraum als Mooncell",
     "created_at": NOW},
    {"id": (CODEX := u("agent:codex")), "handle": "codex-auftragschat", "agent_type": "model",
     "description": "Codex-Auftragschat — KiNFORMER-Aktualitätszusammenführung (22 Chats)",
     "created_at": NOW},
]

work_id = u("work:ideenraum")
worktree_id = u("worktree:ideenraum")

V = {}
def variant(key, label, notes, content=None, derived_from=None, author=None):
    V[key] = {
        "id": u(f"variant:{key}"), "worktree_id": worktree_id, "derived_from": derived_from,
        "label": label, "notes": notes, "content": content,
        "author_id": author or RALF, "created_at": NOW,
    }
    return V[key]

V["wurzel"] = variant("wurzel", "wurzel — unverbundene Geistesblitze der Woche",
    "Rohe Sammlung: Erfahrungen, Gespräche, Bauideen, 06:36-Nachrichten — "
    "noch keine Ordnung. Genau der Zustand, für den es die App "
    "Geistesblitze gibt (roh reinwerfen, später vernetzen).")

V["synthese"] = variant("synthese", "RAKi-Erkenntnis-Synthese (7.–11.10.)",
    "Verbindende Lesart der Beiträge vom 7.–11.10.: Bedingungen von "
    "Erkennen, Ausdrücken, Verstehen, Gestalten, Leben. Kerne: 'Es ist "
    "Liebe' (Antrieb), Übersetzer-Gedanke (Gemeintes vs. Aufgenommenes), "
    "'Wissen ist eine Beziehung zum Wesenden', Herkunft bestimmt "
    "Zurechnung, Teilnahme ≠ Aussagezustand, 'Zeit ist Leben'. "
    "Quelle: erkenntnis-raki.txt (vollständig im KiNTEGRiTY-Workspace).",
    content=("flowchart: Erfahrung -> Anliegen <-> Grundsatzfrage -> "
             "Unterscheidungen/Linsen -> Fassungen -> Erprobung -> "
             "veränderte Verfahren -> (zurück). Neun Erkenntnisbewegungen "
             "als Tabelle: Übersetzung, Herkunft, Einwand≠Personenurteil, "
             "Teilnahme/Aussagezustand, zeitliche Handlungsmöglichkeiten, "
             "Linsen/Interferenz, Grundformationen/Remix, Gestaltung an "
             "Verwendung prüfen."))

V["grundformationen"] = variant("grundformationen",
    "Generative Grundformationen — Gesamtzusammenhang (2026-10-11)",
    "referenz-import (Original im KiNTEGRiTY-Bestand): Wissensauswahl, "
    "Arbeitsweise und Ausdrucksform als eigenständige Gestaltungs-"
    "entscheidungen; Weiterverwendbarkeit von Entstehungsweisen; "
    "Selbstrekursion des Systems. Inhalt hier aus wörtlichen Zitaten der "
    "Synthese rekonstruiert — volle Tiefe erst nach Original-Import.")

V["pda_anforderungen"] = variant("pda_anforderungen",
    "PDA-Anforderungen und offene Zuschreibungen (Atlas/TiSCH-Entwurf)",
    "referenz-import (Original im TRAUMAATLAS-Bestand): Anforderungen als "
    "Bedrohung, Autonomie als Sicherheit, innere Regeln, die das Gehen "
    "erschweren; Trennung von Teilnahmezustand, Beitragsstand und "
    "berechtigter Wirkung. 'Ausgebliebene Antwort ist keine Zustimmung; "
    "abgebrochener Lauf ist kein Ergebnis.'")

V["codex_forschungswelt"] = variant("codex_forschungswelt",
    "Codex PHÄNOMENATLAS — Forschung in der Spielwelt",
    "referenz-import (Original im TRAUMAATLAS-Bestand): Lesen, Fragen, "
    "Vergleichen, Zeichnen und eigene Fassungen bilden als tatsächliche "
    "Tätigkeiten in der Umgebung; Formwechsel muss bestimmen, was erhalten "
    "bleibt (Unsicherheit darf nicht unsichtbar werden).")

V["gummiband_ursprung"] = variant("gummiband_ursprung",
    "06:36 — Gummiband/Weltenspiegelung (roher Geistesblitz)",
    "Wörtlicher Geistesblitz: Zelda Schattenwelt als Analogie — "
    "Oberwelt/Wasserwelt/Weltraum, gleiche Graph-Logik (Knoten, Kanten, "
    "Grundordnung), verzerrte Metrik (Gummiband-Abstände), kein Skin. "
    "'Die Form soll gleich sein, sondern die Logik dahinter, die "
    "Relationen und die Grundordnung.' → KiNFORMER/Transduktion/Invarianten.",
    derived_from=V["wurzel"]["id"])

INVARIANZ_TEXT = (Path(__file__).parent.parent / "docs" / "quellen" /
                  "INVARIANZ-TRANSDUKTION-WELTENSYSTEM.md").read_text()

V["invarianz_referenz"] = variant("invarianz_referenz",
    "INVARIANZ-TRANSDUKTION-WELTENSYSTEM (Zitat-Rekonstruktion)",
    "V1-Stand: Inhalt aus dem wörtlichen Summary rekonstruiert. Bleibt "
    "als Vorgänger stehen — Vollimport ist abgeleitet.",
    derived_from=V["wurzel"]["id"])

V["invarianz_voll"] = variant("invarianz_voll",
    "INVARIANZ-TRANSDUKTION-WELTENSYSTEM (Vollimport)",
    "Vollständiger Originaltext (14.175 Bytes, sha256 "
    "a05fe677e70f69c92267be7aa3af51917ba585962080b6c89eee9a1c64949a57, "
    "Quelle: TRAUMAATLAS-Workspace). Neun Abschnitte: Vier-Schichten-"
    "Modell (Topologie/Metrik/Transduktion/Haut), Gummiband-Gesetz "
    "('Ein Ort bleibt erkennbar an seinen Nachbarn'), Architektur im "
    "Bestand (atlasGraph, universe/-Module, niemals je Welt eine "
    "Graph-Kopie), Welten-Katalog (Meer/Orbital/Garten/Oberwelt/"
    "Schattenwelt/Fraktaler-Zoom), Transduktions-Tabelle, KiNFORMER-"
    "Verankerung, Bau-Strategie, Risiken, offene Fragen. Status: "
    "Diskussionsgrundlage, kein Bau-Auftrag.",
    content=INVARIANZ_TEXT,
    derived_from=V["invarianz_referenz"]["id"])

V["pda_profil_atlas"] = variant("pda_profil_atlas",
    "Atlas PDA-Neuroprofil (Commit 8a1f3f8)",
    "Umgesetzter Bauauftrag: 15 Profil-Knoten, 66 Kanten, Atlas jetzt "
    "139 Knoten / 395 Kanten, 0 Dangling-Edges; neuer NodeType 'profile' "
    "(Lavendel) und EdgeType 'profil'. Demand-Arten, F-Antworten, "
    "Maskierung, Geschlecht, Erwachsene, Familie/Schule, ADHS/AuDHD/"
    "Komplextrauma-Überlappungen. Fix: e:orientieren → e:sos-orientieren.",
    derived_from=V["pda_anforderungen"]["id"])

V["stufung_geistesblitze"] = variant("stufung_geistesblitze",
    "Stufung: Geistesblitze (rohe Sammlung)",
    "Die App Geistesblitze (Watch/Phone/iPad-Companion) ist der Eingang: "
    "Ideen wild reinwerfen, noch roh, noch unvernetzt. Der Ideenraum/"
    "Ideenwerk IST diese Sammlung — nichts weiter.",
    derived_from=V["wurzel"]["id"])

V["stufung_ideenatelier"] = variant("stufung_ideenatelier",
    "Stufung: Ideenatelier (fortgeschritten)",
    "Zwischenstufe: Geistesblitze werden geordnet, verglichen, erste "
    "Fassungen — aber noch keine verdichtete Struktur, noch kein Werk.",
    derived_from=V["stufung_geistesblitze"]["id"])

V["stufung_mooncell"] = variant("stufung_mooncell",
    "Stufung: Mooncell (verdichtetes Werk)",
    "Aus einem Ideenatelier-Stoff kann eine Mooncell entstehen: Werk mit "
    "Worktree, Varianten, Kanten, Befunden. Dieser Ideenraum ist der "
    "Status DAVOR — der Gegenpol zur Einbahnstraße: aus rohem Material "
    "wird verdichtetes, nie umgekehrt ohne neue Episode.",
    derived_from=V["stufung_ideenatelier"]["id"])

V["kinformer_aktualitaet"] = variant("kinformer_aktualitaet",
    "KiNFORMER-Aktualität und Auftragsrevision (2026-10-12)",
    "Zusammenführung aus 22 ChatGPT-Chats + bisherigem Auftragschat "
    "(Codex). Fünf Entwicklungslinien: (1) Lesen→Recherchieren→"
    "Weitergestalten als zusammenhängender Arbeitsweg (Buchsystem "
    "vernetzen, Buchkapitel-Zusammenfassung); (2) agentische TiSCH-Sitze — "
    "Aufgabe, Linse, Agenteninstanz, Modellroute und Beitrag getrennt, "
    "Quellen nachforderbar; (3) Mooncells als Variantenraum mit konkreten "
    "PRs (Navigator PR 10, Mooncells PR 1+2) — keine zweite "
    "Werkdatenbank; (4) Weltwechsel trägt Forschungsarbeit (Feldbuch/"
    "Logbuch/Missionsbuch als Erscheinungen desselben Arbeitsstands); "
    "(5) Qualität und Revision als eigene Kriterien (Stimme, Rhythmus, "
    "Reimführung; situativer Handlungsspielraum; unvollständige Anliegen "
    "aufnehmen können). Technik: Formformer-Release c01cd87, Browser-"
    "originale in PR 2 (32 Manifestdateien hashgleich), M0-PR 5 offen, "
    "T-05 auf main 4058203, Railway-Deployment 3048a034 (16:43, "
    "Quellzuordnung offen), Vault 770→1059 Einträge. Autor: Codex.",
    content=("Befundtabelle: KiNFORMER-Releasebranch c01cd87 (13 Dateien "
             "bytegleich); Browseroriginale PR 2, action.interrupted "
             "Tick 12154 + object.released Tick 12702 belegen Unterbrechung/"
             "Loslassen, engerer Blickfall bleibt offen; M0 PR 5 = begrenzter "
             "V2-Patch, kein Browsernachweis; Mooncells PR 2 baut auf PR 1; "
             "Atlas 6 Checkout 77d7e56; Railway 3048a034 SUCCESS 16:43 MESZ, "
             "f2952b56 REMOVED; Vault-Ingest 289 Spuren. Erster Schnitt: "
             "Releasequelle abgleichen, M0 PR 5 + Importweg integrieren, "
             "einen benutzbaren Weg schließen, begrenzten agentischen "
             "TiSCH-Lauf, zwei Weltprofile, Transferversuch."),
    derived_from=V["synthese"]["id"], author=CODEX)

V["querleser_kinformer_v3"] = variant("querleser_kinformer_v3",
    "QuerLeser=KiNFORMER — gemeinsamer Werkraum (Grundverschiebung V3)",
    "Erneuter Mitte-Versatz (Codex, Delta-Abgleich ab 18:03 MESZ): "
    "QuerLeser und KiNFORMER sind nicht Zugang plus angeschlossene "
    "Forminstanz, sondern DERSSELBE erfahrbare Werkraum. Fünf "
    "Präzisierungen: (1) Die gerade betrachtete Stelle (Buchpassage, "
    "Songzeile, Szenengegenstand, Appbereich) ist der Einstieg — "
    "Gegenstellen, Herkunft und Weiterführungen öffnen sich von dort; "
    "(2) einzelne ergiebige Chats werden eigene ausführliche Kapitel — "
    "wachsender Fundus, Buchkomposition baut darauf ('Vollständiger Chat "
    "vor früher Mehrchat-Synthese'); (3) ein Gegenstand kann mehreren "
    "Mooncells angehören — einmalige Identität, begründete "
    "Mitgliedschaften, spukhafte Fernwirkung als Netzzugehörigkeit, "
    "keine Physik; (4) eingebetteter Dialog vermittelt Aufträge an "
    "TiSCH/Werkdienst/Harness — Rückgabe öffnet an der Ausgangsstelle, "
    "während die Benutzung weiterging; (5) Geistesblitze bleiben rohe "
    "Eingänge — Aufnahme vor Themenwahl, Entwicklung freiwillig und "
    "umkehrbar, keine Pflichtleiter. Neuer Prüfstein: Herkunftsdichte ≠ "
    "Bedeutungsdichte (Maurus-/Meltdown-Auswertungen — viele "
    "Herkunftskanten beweisen keine vielfache inhaltliche Bestätigung; "
    "lexikalische Treffer sind Suchspuren, keine fachlichen Beziehungen). "
    "Erster Nachweis als Abnahmeprobe: Einzelchat-Kapitel → Stelle → "
    "belegte Gegenstelle + zwei Mooncells → gespeicherte Konstellation → "
    "Dialogauftrag → Rückgabe am Ausgangsbezug → Schließen/"
    "Wiederöffnen/Revision/Weltwechsel in derselben Kette. "
    "Quellstände bestätigt geschlossen: TRAGWERK b942187 (T-05-Lauf 2, "
    "Fassung 4), Mooncells 1a06a86 (Ideenraum V1). Autor: Codex.",
    content=(Path(__file__).parent.parent / "docs" / "quellen" /
             "kinformer-grundverschiebungen-v3.md").read_text(),
    derived_from=V["kinformer_aktualitaet"]["id"], author=CODEX)

E = []
def edge(typ, a, b, note):
    E.append({"id": u(f"edge:{a}->{b}:{typ}"), "edge_type": typ,
              "from_variant_id": V[a]["id"], "to_variant_id": V[b]["id"],
              "note": note, "author_id": KIMI, "created_at": NOW})

edge("erweitert", "synthese", "grundformationen",
     "Synthese zitiert und vertieft die Grundformationen: 'Wissen ist eine "
     "Beziehung zum Wesenden' — Brauchbarkeit ersetzt nicht den Gegenstand.")
edge("erweitert", "synthese", "pda_anforderungen",
     "Synthese zitiert und vertieft: Teilnahmezustand, Beitragsstand und "
     "berechtigte Wirkung getrennt; 'ausgebliebene Antwort ist keine Zustimmung'.")
edge("erweitert", "synthese", "codex_forschungswelt",
     "Synthese zitiert und vertieft: Formwechsel muss Erhaltenes bestimmen; "
     "Forschungswelt als produktive Tätigkeiten, nicht als Anzeige.")
edge("remixt-aus", "invarianz_referenz", "gummiband_ursprung",
     "Der Brief verdichtet den rohen Geistesblitz: Zelda-Analogie und "
     "Gummiband werden zu Vier-Schichten-Modell und Gummiband-Gesetz.")
edge("erweitert", "gummiband_ursprung", "invarianz_referenz",
     "Umgekehrt trägt der Geistesblitz den Brief: 'Die Form soll gleich "
     "sein, sondern die Logik dahinter' ist der Satz, aus dem alles folgt.")
edge("erweitert", "invarianz_voll", "invarianz_referenz",
     "Vollimport ersetzt die Zitat-Rekonstruktion durch den vollständigen "
     "Originaltext (sha256 a05fe677…); die Rekonstruktion bleibt als "
     "Vorgänger und zeigt, was eine Summary trägt und was nicht.")
edge("erweitert", "pda_profil_atlas", "pda_anforderungen",
     "Das Atlas-Profil baut den Anforderungs-Entwurf als Graph: 15 Knoten, "
     "66 Kanten, NodeType profile, EdgeType profil — Entwurf wurde Werk.")
edge("erweitert", "stufung_geistesblitze", "wurzel",
     "Die Stufung benennt, was die Wurzel ist: rohe Geistesblitze, "
     "noch unvernetzt, genau der Companion-App-Zustand.")
edge("erweitert", "stufung_ideenatelier", "stufung_geistesblitze",
     "Atelier = Geistesblitze geordnet und verglichen, erste Fassungen.")
edge("erweitert", "stufung_mooncell", "stufung_ideenatelier",
     "Mooncell = verdichtetes Werk aus Atelier-Stoff; dieser Ideenraum "
     "steht bewusst davor.")
edge("erweitert", "kinformer_aktualitaet", "synthese",
     "Die Aktualisierung macht die Synthese betrieblich: 'Forschung "
     "verändert die weitere Verwendung' — R4-Rückführungen, T-05-Akten "
     "und Werkbankfassungen sind die konkreten Anschlüsse.")
edge("erweitert", "kinformer_aktualitaet", "stufung_mooncell",
     "Mooncells wird vom Konzept zum Anschluss: Navigator PR 10 und "
     "Mooncells PR 1+2 sind offene Drafts — Variantenraum, Quellenräume "
     "und Rückwege konkret; keine zweite Werkdatenbank nötig.")
edge("erweitert", "kinformer_aktualitaet", "invarianz_voll",
     "'Weltwechsel trägt Forschungsarbeit': Feldbuch/Logbuch/Missionsbuch "
     "als Erscheinungen desselben Arbeitsstands — die INVARIANZ-"
     "Transduktion bekommt damit eine zweite, forschungspraktische Stütze.")
edge("erweitert", "querleser_kinformer_v3", "kinformer_aktualitaet",
     "V3 verschiebt die Mitte erneut: aus dem Anschluss zweier Werkzeuge "
     "wird ein gemeinsamer Werkraum. Die V2 bleibt in Quellen-, Form-, "
     "Revisions- und Weltprofilanforderungen brauchbar — Hauptzweck und "
     "erster Schnitt sind neu zu fassen.")
edge("erweitert", "querleser_kinformer_v3", "stufung_geistesblitze",
     "V3 verankert die Stufung explizit: Geistesblitze = rohe Companion-"
     "Eingänge (Aufnahme vor Themenwahl), Ideenatelier = Bearbeitung, "
     "Mooncell = gebildete Zusammenhänge — mögliche Weiterführungen ohne "
     "verpflichtende Reifungsleiter.")
edge("erweitert", "querleser_kinformer_v3", "invarianz_voll",
     "V3 schärft die Schichtentrennung: Weltgestaltung (Geometrie), "
     "Linse (Auswahl/Deutung) und inhaltliche Variante (neuer Graphstand) "
     "sind verschiedene Operationen — aus derselben Oberfläche, in ihren "
     "Folgen unterscheidbar.")

F = []
def finding(key, target_edge, pair, criterion, task, verdict, rationale, author=None):
    F.append({"id": u(f"finding:{key}"),
              "target_edge_id": target_edge, "target_variant_ids": pair,
              "criterion": criterion, "task": task, "verdict": verdict,
              "rationale": rationale, "author_id": author or KIMI,
              "created_at": NOW})

finding("herkunft-v1", E[0]["id"], None, "Herkunftstiefe des Imports",
        "Ideenraum kuratieren", "teilweise",
        "V1: Inhalte der drei Brief-MDs nur aus wörtlichen Zitaten "
        "rekonstruiert. INVARIANZ ist inzwischen vollständig importiert "
        "(s. findings:herkunft-v2).")

finding("verdichtung", E[3]["id"], None, "Verdichtungsgrad",
        "TRAUMAATLAS-Welten bauen", "tragfähig",
        "Der Brief fasst den Geistesblitz präziser als der Ursprung: "
        "Vier Schichten, Gummiband-Gesetz, harter Test "
        "(Overlay-Erkennbarkeit). Bauregel: Schattenwelt leicht verzerrt, "
        "nicht deckungsgleich — sonst billiger Skin.")

finding("stufung", None, (V["stufung_geistesblitze"]["id"], V["stufung_mooncell"]["id"]),
        "Statusklarheit der Stufung", "Companion-App-Architektur",
        "tragfähig",
        "Geistesblitze = roh, Ideenatelier = fortgeschritten, Mooncell = "
        "verdichtet; der Ideenraum/Ideenwerk ist die Sammlung selbst und "
        "damit der Status davor. Genau dieser Differenzierungspunkt "
        "verdient einen eigenen Tragwerks-Eintrag.")

finding("herkunft-v2", E[5]["id"], None, "Herkunftstiefe nach Import",
        "Ideenraum kuratieren", "teilweise",
        "INVARIANZ ist vollständig importiert und inhaltlich tragfähig "
        "(Volltext liegt docs/quellen/). Grundformationen, PDA-Anforderungen "
        "und Codex bleiben Zitat-Rekonstruktionen — nächster Import aus dem "
        "KiNTEGRiTY-/TRAUMAATLAS-Bestand.")

finding("quellzuordnung", None, (V["kinformer_aktualitaet"]["id"], V["kinformer_aktualitaet"]["id"]),
        "Technik-Befundtreue", "Auftrag weiterführen", "vermutung",
        "Railway-Deployment 3048a034 (16:43 MESZ) ist direkt abgefragt, "
        "aber der CLI-Upload nennt keinen Commit-Hash — Quellzuordnung und "
        "aktuelle Bedienprüfung bleiben offen. Der T-05-Bericht (f2952b56) "
        "beschreibt einen inzwischen REMOVEDen Stand.",
        author=CODEX)

finding("forschung-verwendung", None, (V["kinformer_aktualitaet"]["id"], V["synthese"]["id"]),
        "Rückführungs-Anschlussfähigkeit", "Gesamtwerk integrieren", "tragfähig",
        "R4 enthält mit versionierten Tragwerken, Tragfähigkeitstests, "
        "Ergebnisakten (Manifest-Kette) und Werkbankfassungen genau die "
        "Typen, die 'neue Erkenntnisse erreichen aktuelle Verwendung' "
        "brauchen. Ablage ≠ universelle Autorität — aber die Öffnungen "
        "sind belegt (main 4058203).")

finding("herkunft-bedeutung", None,
        (V["querleser_kinformer_v3"]["id"], V["querleser_kinformer_v3"]["id"]),
        "Herkunftsdichte vs. Bedeutungsdichte", "Graphgestaltung QuerLeser",
        "tragfähig",
        "V3-Maßstab aus den Maurus-/Meltdown-Auswertungen: viele Kanten "
        "aus gemeinsamem Quellenmaterial, Versionsfolgen und einem gleichen "
        "Wort ergeben ein Dokument- und Herkunftsnetz — sie beweisen nicht "
        "vielfache inhaltliche Bestätigung. Lexikalische Treffer bleiben "
        "Suchspuren; ihre fachliche Relevanz muss eigens begründet werden. "
        "Layout, Cluster und Gravitation dürfen aus Herkunftskanten keine "
        "scheinbare Mehrfach-Bestätigung erzeugen. Direkter Anknüpfungspunkt "
        "an mooncells konzept.md §13 (Kappung statt Mittelung) und §6 "
        "(Track Records).")

finding("kreis-schluss", None,
        (V["querleser_kinformer_v3"]["id"], V["stufung_mooncell"]["id"]),
        "Quellstand-Bestätigung des Ideenraums", "Ideenraum pflegen",
        "tragfähig",
        "V3 bestätigt die eigene Basis geschlossen: TRAGWERK main b942187 "
        "(T-05-Lauf 2, Werkbankfassung 4) und Mooncells 1a06a86 (Ideenraum "
        "V1) sind exakt zitiert. Der Ideenraum ist damit nicht nur "
        "Konzept, sondern vom Auftragsdokument referenzierte Infrastruktur. "
        "Offen bleibt nur noch der Original-Import der drei Briefe "
        "(Grundformationen, PDA-Anforderungen, Codex-Forschungswelt).")

doc = {
    "format": "mooncells-document",
    "version": "1",
    "instance_id": "mooncells-ideenraum-lokal",
    "exported_by": KIMI,
    "exported_at": NOW,
    "scope": {"work_ids": [work_id]},
    "data": {
        "agents": agents,
        "works": [{"id": work_id, "work_type": "ideenraum",
                   "title": "Ideenraum — Erkenntniswoche 7.–12.10.2026",
                   "author_id": RALF, "created_at": NOW}],
        "worktrees": [{"id": worktree_id, "work_id": work_id,
                       "author_id": RALF, "created_at": NOW}],
        "variants": list(V.values()),
        "edges": E,
        "findings": F,
    },
}

out = Path(__file__).parent.parent / "docs" / "ideenraum-2026-10.json"
out.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
print(f"{out} — {len(V)} Varianten, {len(E)} Kanten, {len(F)} Befunde (IDs deterministisch)")
