"""
Baut den Ideenraum als Mooncells-Dokument (MDF v1).

Ein Work, ein Worktree, Variante je Quelle der Erkenntniswoche
(7.–12.10.2026), typisierte Kanten, Befunde mit ehrlicher Konfidenz.

Quellenlage (ehrlich markiert):
- erkenntnis-raki.txt liegt vollständig im KiNTEGRiTY-Workspace vor.
- INVARIANZ-TRANSDUKTION-WELTENSYSTEM.md und die drei referenzierten
  Brief-MDs liegen im TRAUMAATLAS-Workspace; ihre Varianten hier tragen
  den Inhalt der wörtlichen Zitate/Summarien und sind als
  'referenz-import' gekennzeichnet, nicht als vollständige Kopie.
Ausgabe: docs/ideenraum-2026-10.json (Mooncells Document Format v1)
"""

import json
import uuid
from pathlib import Path

def u() -> str:
    return str(uuid.uuid4())

NOW = "2026-10-12T14:30:00Z"

agents = [
    {"id": (RALF := u()), "handle": "ralf", "agent_type": "human",
     "description": "Projektgründer — Quelle der Geistesblitze und Briefe",
     "created_at": NOW},
    {"id": (KIMI := u()), "handle": "kimi-work-session", "agent_type": "model",
     "description": "Kimi-Work-Session — baut den Ideenraum als Mooncell",
     "created_at": NOW},
]

work_id = u()
worktree_id = u()

V = {}
def variant(key, label, notes, content=None, derived_from=None):
    V[key] = {
        "id": u(), "worktree_id": worktree_id, "derived_from": derived_from,
        "label": label, "notes": notes, "content": content,
        "author_id": RALF, "created_at": NOW,
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
             "veränderte Verfahren -> (zurück zu Erfahrung/Unterscheidungen). "
             "Neun Erkenntnisbewegungen als Tabelle: Übersetzung, Herkunft, "
             "Einwand≠Personenurteil, Teilnahme/Aussagezustand, zeitliche "
             "Handlungsmöglichkeiten, Linsen/Interferenz, Grundformationen/"
             "Remix, Gestaltung an Verwendung prüfen."))

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

V["invarianz_transduktion"] = variant("invarianz_transduktion",
    "INVARIANZ-TRANSDUKTION-WELTENSYSTEM (Brief, neun Abschnitte)",
    "referenz-import aus dem wörtlichen Summary des Briefs: "
    "Vier-Schichten-Modell (Topologie/Metrik/Transduktion/Haut), "
    "Gummiband-Gesetz ('Ein Ort bleibt erkennbar an seinen Nachbarn'), "
    "Architektur im Bestand (atlasGraph, universe/-Module, niemals je "
    "Welt eine Graph-Kopie), Welten-Katalog (Meer/Orbital/Garten/"
    "Oberwelt/Schattenwelt), KiNFORMER-Verankerung. Empfehlung: "
    "Schattenwelt oder Orbital als erste neue Welt.",
    derived_from=V["wurzel"]["id"])

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

E = []
def edge(typ, a, b, note):
    E.append({"id": u(), "edge_type": typ,
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
edge("remixt-aus", "invarianz_transduktion", "gummiband_ursprung",
     "Der Brief verdichtet den rohen Geistesblitz: Zelda-Analogie und "
     "Gummiband werden zu Vier-Schichten-Modell und Gummiband-Gesetz.")
edge("erweitert", "gummiband_ursprung", "invarianz_transduktion",
     "Umgekehrt trägt der Geistesblitz den Brief: 'Die Form soll gleich "
     "sein, sondern die Logik dahinter' ist der Satz, aus dem alles folgt.")
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

F = []
def finding(target_edge, pair, criterion, task, verdict, rationale):
    t = {"target_edge_id": target_edge, "target_variant_ids": pair,
         "criterion": criterion, "task": task, "verdict": verdict,
         "rationale": rationale, "author_id": KIMI, "created_at": NOW}
    F.append(t)

finding(E[0]["id"], None, "Herkunftstiefe des Imports",
        "Ideenraum kuratieren", "teilweise",
        "Inhalte der drei Brief-MDs sind hier nur aus wörtlichen Zitaten "
        "rekonstruiert — volle Tiefe erst nach Original-Import aus dem "
        "TRAUMAATLAS/KiNTEGRiTY-Bestand.")
finding(E[3]["id"], None, "Verdichtungsgrad",
        "TRAUMAATLAS-Welten bauen", "tragfähig",
        "Der Brief fasst den Geistesblitz präziser als der Ursprung: "
        "Vier Schichten, Gummiband-Gesetz, harter Test "
        "(Overlay-Erkennbarkeit). Baue Schattenwelt leicht verzerrt, "
        "nicht deckungsgleich — sonst billiger Skin.")
finding(None, (V["stufung_geistesblitze"]["id"], V["stufung_mooncell"]["id"]),
        "Statusklarheit der Stufung", "Companion-App-Architektur",
        "tragfähig",
        "Geistesblitze = roh, Ideenatelier = fortgeschritten, Mooncell = "
        "verdichtet; der Ideenraum/Ideenwerk ist die Sammlung selbst und "
        "damit der Status davor. Genau dieser Differenzierungspunkt "
        "verdient einen eigenen Tragwerks-Eintrag.")

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
print(f"{out} — {len(V)} Varianten, {len(E)} Kanten, {len(F)} Befunde")
