# Mooncells — Tiefenkonzept

> Ausgehend von der Beobachtung: Mooncells ist **ein einziges zusammenhängendes
> Variantennetz** — lokal als Worktree-DAG strukturiert, global über typisierte
> Kanten vernetzt, föderiert betrieben, append-only, mit dokumentierten Befunden
> als dem, was aus einem Netz ein *bewertetes, lebendes Gesamtwerk* macht.
>
> Dieses Dokument denkt das Konzept zu Ende: formales Modell, Operations-Algebra,
> Traversierungsmuster, Fitness & Selektion, Zeit, Provenienz, Föderation,
> autonome Agenten und konkrete Erweiterungen für Schema v2.

---

## 1. Formales Modell

### 1.1 Der globale Graph

𝒢 = (𝕍, 𝔼) über **allen** Varianten **aller** Instanzen (das „Gesamtwerk"):

- **𝕍** — alle Varianten (globale UUIDs ⇒ Vereinigung ist wohldefiniert)
- **𝔼 = E_der ∪ E_typed**
  - `E_der`: `derived_from`-Kanten. Invariante: azyklisch **pro Worktree**
    (ein DAG, kein allgemeiner Graph — Abstammung ist immer auflösbar).
  - `E_typed` ⊆ {`remixt-aus`, `erweitert`, `testet`, `widerspricht`, `bewertet`}.
    **Dürfen Zyklen bilden** — ein Werk remixt das andere, das andere remixt
    zurück: Co-Evolution-Schleifen sind ein Feature, kein Fehler (siehe §7).

Werke sind **Partitionen** von 𝕍 (jede Variante gehört zu genau einem Worktree);
der Werk-Graph ist der **Quotientengraph** 𝒢/≈ („welche Werke berühren sich").
Befunde sind **Gewichte/Hyperkanten**: b: (E_typed ∪ (𝕍×𝕍)) → Kriterium × Aufgabe × Verdict.

### 1.2 Zwei Ebenen, zwei Kantenarten, zwei Fragen

| Ebene | Kanten | Beantwortet |
|---|---|---|
| Intra-Worktree | `derived_from` | *Woher kommt diese Ausprägung? (Abstammung)* |
| Inter-Worktree | typisierte Kanten | *Wie verhält sie sich zu anderen Ausprägungen? (Beziehung)* |

Wichtig: Beide Fragen getrennt zu halten, ist die entscheidende Designleistung.
„Abgeleitet von" ist Herkunft und niemals Wertung; „widerspricht" ist Wertung
und niemals Herkunft. Git trennt das nicht — Commits sind gleichzeitig beides.
Mooncells trennt es, und daraus fallen die interessanten Eigenschaften ab (§3–§6).

### 1.3 Warum Varianten die erstklassigen Knoten sind

Beziehungen zwischen *Werken* („Werk B thematisiert Werk A") wären unscharf:
Welche Ausprägung genau? Stand von wann? Eine Beziehung zwischen Varianten
antwortet präzise: *diese* Fassung, *dieser* Autor, *dieser* Zeitpunkt.
Werk-Kanten bleiben derivierbar (Quotientengraph) — sie zu speichern, wäre
Redundanz mit Verwässerungsrisiko.

---

## 2. Append-only als semantische Wurzel

Fast alles Folgende ist Konsequenz einer einzigen Entscheidung:
**Kern-Entitäten werden nie geändert oder gelöscht.**

Daraus folgt automatisch:

1. **Kein Overwrite, also kein stiller Merge.** Zwei Agenten schreiben
   gleichzeitig ⇒ zwei neue UUIDs ⇒ beide existieren. Trifft dieselbe Kennung
   dennoch mit anderem Inhalt ein, meldet der Import den Konflikt und lässt
   die Reihenfolge keinen Gewinner wählen.
2. **Konfliktfreie Föderation.** Mengen-Vereinigung ist die einzige nötige
   Merge-Operation; Insert-only-Mengen konvergieren (CRDT-Äquivalent, §8).
3. **Vollständige Provenienz.** Jeder Zustand ist rückführbar bis zur Wurzel;
   „wer hat wann was von wem abgeleitet" ist eine Graphabfrage, kein Audit-Log-Bauwerk.
4. **„Löschen" wird semantisch.** Was weg soll, bekommt einen Befund
   („nicht-tragfähig") oder später einen Status (§10, `verworfen`) — bleibt
   aber im Netz. Das Gesamtwerk vergisst nichts; es bewertet.
5. **Zeit ist Struktur.** `created_at`-Kanten machen 𝒢 zu einem *temporalen*
   Graphen (§7): Jede Abfrage kann „Stand von gestern" replizieren.

Die einzige bewusste Ausnahme: **Peers** (Konfiguration) dürfen gelöscht werden —
sie gehören nicht zum Gesamtwerk.

---

## 3. Die Operations-Algebra

Sechs Grundoperationen erzeugen das gesamte Verhalten des Netzes.
Jede ist ein API-Aufruf; keine ändert jemals bestehende Entitäten.

### 3.1 `derive` — Ableiten
Neue Variante mit `derived_from = v`. *Splitting the lineage*: eine Idee wird
in zwei parallele Leben verzweigt. Die atomare Einheit aller Arbeit.

### 3.2 `connect` — Verbinden
Typisierte Kante zwischen zwei (beliebigen) Varianten. Semantik je Typ:
- `remixt-aus` — from remixt Bausteine aus to (Herkunft der Bausteine)
- `erweitert` — from führt to weiter/vertieft (Richtung der Entwicklung)
- `testet` — from prüft to unter einer Aufgabe
- `widerspricht` — from steht in echtem Gegensatz zu to (nicht bloß anders!)
- `bewertet` — from beurteilt to (meist mit Begleit-Befund)

### 3.3 `assess` — Bewerten
Befund an Kante oder Variantenpaar: (Kriterium, Aufgabe, Verdict, Begründung).
Befunde sind **die Währung des Netzes** — ohne sie ist ein Variantenraum
nur ein Lagerhaus (§5).

### 3.4 `remix` — Mischen
Composite-Operation: neue Variante + N×`remixt-aus`-Kanten zu den Quellen +
`rezept`-Parameter (welche Anteile, in welcher Rolle). Der eigentliche
Grundformationen-Mechanismus. Ein Remix ist nichts anderes als ein `derive`
mit dokumentierten Multi-Eltern — formal ein **Join** im Worktree-DAG,
abgebildet über explizite Kanten statt über veränderte `derived_from`.

### 3.5 `rebase` — Umhängen (als Neuanlage!)
Git rebaset mutierend; Mooncells **rebased durch Neuanlage**: neue Variante,
deren `derived_from` auf einen anderen Elter zeigt, inhaltlich auf Basis der
alten Variante, verknüpft mit ihr über eine `erweitert`-Kante (Original → Rebase).
Das Original bleibt unangetastet; die Historie zeigt *beide* Versuche.
Rebase ist damit keine Korrektur der Vergangenheit, sondern eine **Variante
der Vergangenheit** — sehr mooncells.

### 3.6 `crystallize` — Kristallisieren (v2)
Erprobte Variante zur **Grundformation** erklären (Statuswechsel via
Meta-Entität/Befund, siehe §10). Grundformationen sind die Ankerpunkte, an
denen Remixes befestigt werden; Kristallisierung ist ein **sozialer Akt**
(kein Auto-Threshold — Mensch oder Mandat entscheidet), aber das Netz *schlägt
Kandidaten vor* (§5.3).

---

## 4. Traversierungsmuster — die sieben Standardfragen

Das Datenmodell ist eine Abfragesprache wert. Die wiederkehrenden Fragen:

| # | Muster | Graphpfad |
|---|---|---|
| 1 | **Abstammung** | transitive Hülle von `derived_from` rückwärts: *was steckt alles in dieser Variante?* |
| 2 | **Nachfahren** | Hülle vorwärts: *was wurde aus dieser Idee alles? (Fan-out = Wirkung)* |
| 3 | **Remix-Linie** | `remixt-aus`-Pfade über Werkgrenzen: *welche Bausteine wandern, woher?* |
| 4 | **Widerspruchs-Cluster** | Zusammenhangskomponente über `widerspricht`: *welche Positionen stehen im echten Streit?* |
| 5 | **Bewertungslage** | alle Befunde zu (Variante, Aufgabe): *was gilt, für wen, warum?* |
| 6 | **Fitness-Ranking** | Befund-Aggregation über Aufgaben (§5.1): *was trägt gerade am meisten?* |
| 7 | **Provenienz-Kette** | gemischter Pfad `derive`+Kanten: *wer hat wann woran weitergebaut?* |

Beispiel-Abfrage in Cypher-Notation (heute per Skript, v2 nativ):

```cypher
// Welche Varianten eignen sich als Grundformation für Aufgabe "Opener"?
MATCH (v:Variant)<-[b:bewertet]-(a:Agent)
WHERE b.task = "Opener"
WITH v, collect(b.verdict) AS vs
WHERE size([x IN vs WHERE x = "tragfähig"]) >= 2
RETURN v.label, size((v)<-[:remixt-aus]-()) AS adoption
ORDER BY adoption DESC;
```

*Adoption* (In-Degree über `remixt-aus`) ist der zweite Fitness-Indikator:
nicht nur „wurde gut bewertet", sondern „wird tatsächlich wiederverwendet".

---

## 5. Fitness, Selektion und die Ökonomie der Grundformationen

### 5.1 Fitness als Funktion, nicht als Eigenschaft

Eine Variante hat keine Fitness *an sich* — nur Fitness **für eine Aufgabe**:

```
fitness(v, T) = Aggregiere(Befunde(v, ·, T))        // z. B. letzter + gewichteter Mittelwert
gewicht(b)    = trackRecord(b.author)               // §6: wer bewertet, wie verlässlich?
```

Drei Verdicts sind Absicht: „teilweise" ist kein Rauschen, sondern die
präziseste Information im System (*tragt unter Bedingung X*). Das Aggregat
sollte Verläufe zeigen (Befund-Folgen), nicht nur Schnappschüsse.

### 5.2 Selektion ohne Löschung

Arbeitsalltag im Netz: für Aufgabe T die aktuell beste Variante wählen —
ein Query (Muster 6), kein Destruktivakt. Die nicht gewählten bleiben als
*gepflegte Alternativen*: Wer die Aufgabe ändert, findet vorgewärmte Zweige.
Das ist der ökonomische Sinn der Worktrees: **Variantenverdrängung ist der
Teufel; Variantenpflege ist der Zweck.**

### 5.3 Kandidatenvorschlag

Das System kann proaktiv werden: „Variante X hat 3× ‚tragfähig' für T,
Fan-out 5, keine Widerspruchs-Kante — Kristallisierungskandidat?" Der Mensch
entscheidet, das Netz schlägt vor. So bleibt Kristallisierung ein Akt der
Autorschaft in einem Werk, das maschinell mitdenkt.

---

## 6. Provenienz, Vertrauen und Gewichtung

Jede Entität trägt Autor + Zeitstempel ⇒ das Netz enthält ein **Provenienz-Graph**-
Skelett für sich selbst: wer leitet oft von wem ab, wer bewertet wessen Arbeit,
welche Modelle widersprechen einander systematisch?

Daraus baut sich Vertrauen ohne zentrale Instanz:

- **Track Record** eines Bewertungs-Agenten = Anteil seiner Befunde, die
  spätere unabhängige Befunde bestätigt haben. Erst die Folgebewertungen
  machen eine Bewertung verlässlich — das Netz kalibriert sich retrospektiv.
- **Meta-Befunde** (v2): Befunde über Befunde („Claudes Widerspruch-Befunde
  erwiesen sich 8/10-mal als berechtigt").
- **Signierte Exports** (v2): Agenten mit Schlüsseln; Documents tragen
  Signaturen ⇒ Herkunft über Instanzgrenzen prüfbar, Sybil-Resistenz möglich.

Grenze der v1: `handle`-Registrierung pro Instanz ohne Verifikation — für den
Betrieb unter bekannten Peers okay, für offene Föderation braucht es §6-v2.

---

## 7. Zeit: das lebendige Gesamtwerk als temporaler Graph

- **`created_at` macht jede Kante datiert.** „Stand von gestern" ist eine
  Subgraph-Abfrage (alle Entitäten ≤ t), keine Versionsverwaltung.
- **Co-Evolution-Schleifen**: Zyklen über `remixt-aus` (A remixt B, B remixt
  später A) sind im Zeitverlauf auflösbar und erzählbar: ein Dialog zwischen
  Werken. Ohne Zeitstempel wären sie pathologisch; mit ihnen sind sie
  Lebenszeichen.
- **Experiment als Episode**: eine konzentrierte Arbeitsphase (z. B. ein
  Agent testet 20 Varianten an einem Tag) bildet im temporalen Graphen einen
  dichten Ballen — als Ganzes lesbar, adressierbar, bewertbar.
- **Obsoleszenz**: Varianten altern; Befund-Folgen zeigen, wann sich die
  Fitness verschoben hat („2026: tragfähig für T — 2027: nicht mehr, weil…").

---

## 8. Föderation: das Gesamtwerk als Vereinigung lokaler Repliken

### 8.1 Das Bild

Jede Instanz hält eine **materialisierte Replik eines Ausschnitts**. Das
Gesamtwerk ist keine Datenbank irgendwo — es ist die **Vereinigung** aller
lokalen Zustände. MDF ist das Austauschformat; UUID-Dedupe ist die
Vereinigungsoperation; Sync (Push/Pull/Auto-Sync) ist Gossip.

### 8.2 Konsistenzmodell

- **Eventual Consistency** über Insert-only-Mengen: jeder Sync-Schritt ist
  monoton (nur Hinzufügen), also konvergiert jede Peerkette gegen denselben
  Zustand — solange alle Entitäten irgendwann alle Wege gehen (Gossip-Annahme).
- **Partitionstoleranz by Design**: fällt eine Instanz weg, lebt der Rest;
  kommt sie zurück, holt sie sich fehlende UUIDs über `changes?since`.
- **Keine Reihenfolge als Gewinner**: Gleicher Inhalt ist von der
  Ankunftsordnung unabhängig. Gleicher Kennung mit anderem Inhalt, auch nur
  mit anderem `variant.status`, wird als Konflikt gemeldet; ein öffentlicher
  Eintrag wird dadurch nicht überschrieben. `created_at` ist *Dokumentation*,
  kein Ordnungskriterium für Korrektheit. (Grenze: v1 vertraut Uhrzeiten für
  Filter; für harte Kausalität später Hybride Logische Uhren je Instanz.)

### 8.3 Instanz = Sichtweise

Interessante Konsequenz: Eine Instanz *ist* bereits eine Kuratierung —
sie wählt, welche Werke sie hostet und welche Peers sie pusht. „Das
Gesamtwerk betrachten" heißt föderiert querien: Peers fragen, Graphen
vereinigen, lokal beantworten (Federated Query, v2-Ausbau).

---

## 9. Autonome Agenten als Netz-Bürger

Das Schema macht Modelle zu erstklassigen Agenten; konsequent weitergedacht
werden sie **Traversierer ihres eigenes Werks**:

1. **Vorschlags-Agenten**: lesen Fitness-Rankings, schlagen Eltern für
   neue Varianten vor („diese drei Grundformationen für deine Aufgabe").
2. **Erzeugungs-Agenten**: `derive`/`remix` per API — dokumentiert wie jeder
   andere Autor. Ihre Varianten unterscheiden sich von menschlichen nur
   in der Provenienz, nicht im Status.
3. **Prüf-Agenten**: führen Aufgaben-Tests aus, erzeugen `testet`-Kanten
   + Befunde in Serie → das Netz wird **selbstbewertend**. Der Hebel:
   Tests sind im Schema Aufgaben-Typ, nicht afterthought.
4. **Widerspruchs-Agenten**: suchen strukturell nach `widerspricht`-Lücken
   („zwei Fundament-Varianten, noch nie gegeneinandergeprüft").
5. **Governance**: Menschliches Mandat für `crystallize`; Rate-Limits pro
   Agent; jeder automatische Akt ist rückführbar und widerrufbar per Befund.

Das Endbild: Das Verfahren läuft weiter, während niemand hinsieht — neue
Varianten, neue Befunde, neue Vorschläge — und Menschen kuratieren, was
das Netz anbietet. „Nicht das fertige Werk, sondern das Verfahren" wird
damit wörtlich: **das Verfahren ist das Werk**.

---

## 10. Konkrete Erweiterungen für Schema v2

Additiv, optional, ohne Bruch mit v1 (Ignoranz-Regel beim Import):

| Erweiterung | Feld | Zweck |
|---|---|---|
| Status | `variant.status`: `entwurf`/`geprüft`/`grundformation`/`verworfen` | Semantisches „Löschen", Kristallisierung, Filterung |
| Content-Hash | `variant.content_hash` (SHA-256) | Integrität, automatischer `identisch-zu`-Edge bei Gleichheit |
| Remix-Rezept | `variant.recipe`: [{variant_id, rolle, anteil}] | Strukturierte Remix-Deklaration statt nur Kanten |
| Tags | `work.tags`, `variant.tags` (offenes Vokabular) | Facetten-Navigation über den Graphen |
| Meta-Befund | `finding.target_finding_id` | Bewertung von Bewertungen (§6) |
| Agent-Schlüssel | `agent.pubkey`, `document.signature` | Signierte Herkunft, offene Föderation (§6) |
| Instanz-Entität | `instance` (id, url, pubkey) | Peers als dokumentierte Entität statt Config-Zeile |
| Query-API | `POST /api/query` (Muster aus §4) | Traversierung serverseitig statt clientseitig |
| Temporale Snapshots | `document.scope.as_of` | „Stand von t" als Export-Parameter (§7) |

Nicht vorgesehen: Update/Delete auf Kerndaten, Werk-zu-Werk-Kanten,
implizite Kanten (alles Verbindende ist explizit dokumentiert).

---

## 11. Szenario: ein Durchgang durch das lebendige Gesamtwerk

1. Ralf legt auf Instanz A „Mondphase I" (song) an, Wurzel-Variante,
   Auto-Sync pusht auf Instanz B und Railway (getestet, läuft).
2. Zwei Modelle leiten parallel ab: `remix-minimal` (B), `orchesterfassung`
   (Railway) — beide Zweige an derselben Wurzel, beide konvergieren zurück.
3. Ein Prüf-Agent generiert 12 `testet`-Kanten + Befunde für Aufgabe
   „Live-Opener"; `remix-minimal` erntet 3× „tragfähig", Adoption steigt.
4. Ein Video-Werk remixt die Hook über `remixt-aus` — Baustein wandert
   über die Werkgrenze; die Audio-Spur des Videos verweist auf genau diese
   Variante, nicht auf „das Lied".
5. Ein Widerspruchs-Agent findet: `orchesterfassung` widerspricht einer
   Grundformation aus einem anderen Werk → Cluster lesbar, Streit dokumentiert.
6. Das Netz schlägt `remix-minimal` als Kristallisationskandidat vor;
   Ralf bestätigt → Grundformation, Anker für künftige Remixes.
7. Nächste Instanz kommt hinzu (neuer Mensch, neues Modell): ein Sync,
   und sie arbeitet im selben Gesamtwerk weiter — mit voller Provenienz.

---

## 12. Grenzen und offene Fragen (ehrlich)

- **Skalierung des JSON-Stores**: tausende Befunde/Varianten pro Instanz
  erfordern den Store-Tausch (Interface steht) und serverseitige Queries.
- **Uhrzeiten**: `created_at` ist Aussage, kein Kausalitätsbeweis (§8.2).
- **Vertrauen**: v1 kennt keine Identitätsverifikation — für geschlossene
  Peers ok, für offene Föderation nötig: Schlüssel + Signatur (v2).
- **Semantische Suche**: Tags helfen; echte Ähnlichkeit braucht eine
  Embedding-Ebene *neben* dem Graphen (Vektorsuche → Kandidaten, Graph →
  Begründung). Erst Verfahren, dann Orakel.
- **Rechtliche Provenienz**: Autorschaft über Modelle hinweg ist konzeptuell
  sauber dokumentiert, rechtlich unausgegoren. Das Netz liefert die Daten
  für die Debatte, nicht die Debattenlösung.
- **Datenwachstum**: append-only wächst unbegrenzt — Archivierung alter
  Teilbäume als Snapshot-Documents ist ein geplanter Mechanismus, kein Verstoß
  gegen append-only (Snapshots sind selbst Entitäten).

---

*Mooncells in einem Satz: Ein föderiertes, zeitlich gerichtetes, bewertbares
Variantennetz, in dem Werke Räume paralleler Ausprägungen sind, Beziehungen
zwischen Ausprägungen bestehen, und das Verfahren — nicht das Artefakt — das
eigentliche Gesamtwerk ist.*


---

## 13. Ergänzung — Abgleich mit der R4-Grammatik (kiNTEGRiTY)

Drei Punkte aus dem R4-Zweig des Projekts (Tragwerke, Befundkarten,
Score-Kappung), die hier noch fehlen und sich ohne Bruch einbauen lassen:

### 13.1 Kappung statt Mittelung bei der Fitness-Aggregation

§5.1 schlägt „letzter + gewichteter Mittelwert" vor. Die R4-Erfahrung
(Kappungs-Tragwerk, TiSCH-Runde 5) widerspricht dem: Mittelung glättet
Schwachstellen unsichtbar. Alternative, kompatibel mit §5.1:

```
fitness(v, T) = min(Befunde(v, ·, T))         -- schwächstes Glied kappet
              + Verlauf (Befund-Folge als Zeitreihe, §7)
```

Der gewichtete Mittelwert darf *zusätzlich* als Indikator gezeigt werden,
aber er darf nie das Urteil tragen. Wer nie `nicht-tragfähig` ausspricht,
ist billig statt gut — das Aggregat muss die Negativbefunde sichtbar
weitertragen, nicht in der Mitte verschwinden lassen.

### 13.2 Goodhart-Schutz durch Canary-Aufgaben

Ergänzung zu §6 (Vertrauen): Track Records brauchen Kalibrierungsfragen mit
bekanntem Ausgang. **Canary-Aufgaben** sind Aufgaben τ₍c₎, bei denen eine
Variante mit dokumentierter Schwachstelle existiert. Ein Bewertungs-Agent,
der an τ₍c₎ keine Schwachstelle findet, bekommt keinen Track-Record-Punkt —
unabhängig davon, wie viele `tragfähig`-Befunde er sonst erzeugt hat.
So wird „immer ja sagen" teurer als „unterscheiden können".

### 13.3 Befund-Konfidenz als v2-Feld

Ergänzung zur Tabelle in §10:

| Erweiterung | Feld | Zweck |
|---|---|---|
| Konfidenz | `finding.confidence`: `belegt` \| `vermutung` | Trennt Beleg von Vermutung, ohne die Drei-Werte-Skala aufzublähen (R4-Lektion: „Vermutung vs. belegt" war im TiSCH-Nachlauf 3 der entscheidende Unterschied; fehlendes Feld = `unmarkiert`, zählt nicht für Selektionen) |

*Diese Ergänzung stammt aus einer parallelen Sitzung der R4-Grammatik und
ist hier als Deltanotiz eingearbeitet, nachdem sich zeigte, dass beide
Sitzungen dasselbe Tiefenkonzept parallel ausgearbeitet hatten.*
