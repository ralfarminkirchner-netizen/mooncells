# Mooncells — Schema & Document Format (v1)

> **Designziel:** Ein minimales, erweiterbares Datenmodell, das föderierten Betrieb
> (Menschen + Modelle auf beliebig vielen Instanzen) ohne zentrale Koordination erlaubt.
> Jede Entität ist selbstbeschreibend (Ursprung, Zeit) und global eindeutig (UUID).

---

## 0. Einordnung: Mooncells als zweistufiger Graph

Mooncells ist ein einziges zusammenhängendes **Variantennetz** mit zwei Ebenen:

```
Werk A ○─────remixt-aus──────○ Werk B         ← Ebene 1: Netz der Werke
  │  Worktree                    │  Worktree
  ▼                              ▼
wurzel ──► variant-2            wurzel ──► variant-7     ← Ebene 2: Varianten-DAGs
   └──► variant-3 (claude)         └──► variant-8
             ↑ Befund: „hängt sofort, aber…" an Kante/Paar
```

- **Ebene 1 (inter-worktree):** Werke sind die großen Knoten des Gesamtwerks.
  Verbunden werden sie nicht durch die Werke selbst, sondern durch ihre Varianten:
  typisierte Kanten (`remixt-aus`, `erweitert`, `testet`, `widerspricht`, `bewertet`)
  zwischen Varianten — auch quer über Werkgrenzen. Hier lebt das Remix-Prinzip.
- **Ebene 2 (intra-worktree):** Jeder Werk-Knoten enthält seinen Worktree, einen
  **Varianten-DAG**, dessen innere Kanten die append-only-`derived_from`-Referenzen
  sind. Hier passiert parallele Arbeit: N Agenten hängen Zweige an dieselbe Wurzel.
- **Befunde** sind dokumentierte Annotationen an Kanten und Variantenpaaren — sie
  machen aus einem Netz ein *bewertetes* Gesamtwerk.

Präzisierung: erstklassige Graphelemente sind die **Varianten**, nicht die Werke.
Werke/Worktrees sind Container, die den Variantenraum organisieren; Beziehungen
bestehen immer zwischen konkreten Ausprägungen — das hält Rückführbarkeit scharf.

Vertiefung: `docs/konzept.md` — formales Modell, Operationen, Traversierung,
Fitness/Selektion, Zeit, Provenienz, Föderation, autonome Agenten, Schema-v2.

---

## 1. Entitätstypen

### 1.1 Agent — wer etwas erzeugt hat

```typescript
interface Agent {
  id: string;              // UUIDv4, bei Registrierung vergeben
  handle: string;          // Kennung, z. B. "ralf", "claude-sonnet-4.6", "gpt-5.2"
  agent_type: "human" | "model";
  description?: string;    // optional: Rolle, Modellversion, Kontext
  created_at: string;      // ISO-8601-UTC
}
```

### 1.2 Work (Werk / Knoten)

```typescript
type WorkType =
  | "text" | "song" | "app" | "video" | "program" | "skill" | "automation"
  | string;               // offen erweiterbar — neue Typen sind keine Schema-Änderung

interface Work {
  id: string;              // UUID
  work_type: WorkType;
  title: string;
  author_id: string;       // → Agent.id
  created_at: string;
}
```

### 1.3 Worktree — der Variantenraum eines Werks

```typescript
interface Worktree {
  id: string;              // UUID
  work_id: string;         // → Work.id (1 Worktree pro Werk)
  author_id: string;
  created_at: string;
}
```

### 1.4 Variant — eine parallele Ausprägung im Worktree

```typescript
interface Variant {
  id: string;              // UUID
  worktree_id: string;     // → Worktree.id
  derived_from: string | null;  // → Variant.id (null = Wurzel des Baums)
  label: string;           // z. B. "v1-heroisch", "remix-minimal"
  notes: string;           // Was weicht ab? Parameter, Idee, Abweichungsbeschreibung
  content?: string;        // optionaler Artefakt-Payload (Text, Code, JSON …)
  author_id: string;       // → Agent.id
  created_at: string;
}
```

> **Append-only:** `derived_from` wird nach dem Anlegen nie geändert. Varianten
> werden nicht überschrieben, sondern *abgeleitet* — wie Commits in Git.
> Parallelarbeit ist dadurch konfliktfrei: Zwei Agenten leiten von derselben
> Variante ab und erzeugen zwei neue Zweige statt einander zu verdrängen.

### 1.5 Edge — typisierte Kante zwischen Varianten (auch quer über Werke)

```typescript
type EdgeType =
  | "remixt-aus" | "erweitert" | "testet" | "widerspricht" | "bewertet"
  | string;               // offen erweiterbar

interface Edge {
  id: string;              // UUID
  edge_type: EdgeType;
  from_variant_id: string; // → Variant.id
  to_variant_id: string;   // → Variant.id
  note?: string;
  author_id: string;       // → Agent.id
  created_at: string;
}
```

> Gerichtet: `from` → `to`. Bei `remixt-aus` bedeutet das: die Variante *from*
> remixt Bausteine aus der Variante *to* (Kante über Werkgrenzen hinweg erlaubt).

### 1.6 Finding (Befund) — dokumentierte Bewertung

```typescript
type Verdict = "tragfähig" | "teilweise" | "nicht-tragfähig";

interface Finding {
  id: string;              // UUID
  target_edge_id: string | null;        // Befund an einer Kante …
  target_variant_ids: [string, string] | null;  // … oder an einem Variantenpaar
  // genau eines der beiden Zielfelder ist gesetzt
  criterion: string;       // Bewertungskriterium, z. B. "klare Linienführung"
  task: string;            // Aufgabe, für die bewertet wurde
  verdict: Verdict;
  rationale: string;       // Kurzbegründung
  author_id: string;       // → Agent.id
  created_at: string;      // = Datum des Befunds
}
```

---

## 2. Mooncells Document Format (MDF) — kanonischer Export/Import

Eine Instanz exportiert ihren Zustand (oder einen Ausschnitt) **immer** in dieser
exakten Struktur. Importierende Instanzen führen per UUID-Dedupe zusammen.

```typescript
interface MooncellsDocument {
  format: "mooncells-document";
  version: "1";
  instance_id: string;     // Kennung der exportierenden Instanz (frei wählbar, eindeutig)
  exported_by: string;     // → Agent.id des Auslösers
  exported_at: string;     // ISO-8601-UTC
  scope?: {                // optional: beschreibt den Ausschnitt, falls gefiltert
    work_ids?: string[];
    since?: string;        // nur Entitäten mit created_at >= since
  };
  data: {
    agents: Agent[];
    works: Work[];
    worktrees: Worktree[];
    variants: Variant[];
    edges: Edge[];
    findings: Finding[];
  };
}
```

### Beispieldokument (abgekürzt)

```json
{
  "format": "mooncells-document",
  "version": "1",
  "instance_id": "mooncells-ralf-lokal",
  "exported_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "exported_at": "2026-10-11T09:30:00Z",
  "data": {
    "agents": [
      { "id": "3fa85f64-…", "handle": "ralf", "agent_type": "human",
        "description": "Projektgründer", "created_at": "2026-10-11T09:20:00Z" }
    ],
    "works": [
      { "id": "7c9e…", "work_type": "song", "title": "Mondphase I",
        "author_id": "3fa85f64-…", "created_at": "2026-10-11T09:21:00Z" }
    ],
    "worktrees": [
      { "id": "2b1c…", "work_id": "7c9e…",
        "author_id": "3fa85f64-…", "created_at": "2026-10-11T09:21:00Z" }
    ],
    "variants": [
      { "id": "aa11…", "worktree_id": "2b1c…", "derived_from": null,
        "label": "wurzel", "notes": "Ausgangsidee: zwei Strophen, vier Takte Intro",
        "author_id": "3fa85f64-…", "created_at": "2026-10-11T09:22:00Z" },
      { "id": "bb22…", "worktree_id": "2b1c…", "derived_from": "aa11…",
        "label": "remix-minimal", "notes": "ohne Intro, nur Gesang + Bass",
        "author_id": "9f0e…", "created_at": "2026-10-11T09:45:00Z" }
    ],
    "edges": [
      { "id": "e55e…", "edge_type": "remixt-aus",
        "from_variant_id": "bb22…", "to_variant_id": "aa11…",
        "note": "Strophenstruktur übernommen",
        "author_id": "9f0e…", "created_at": "2026-10-11T09:46:00Z" }
    ],
    "findings": [
      { "id": "f77f…", "target_edge_id": "e55e…", "target_variant_ids": null,
        "criterion": "Wiedererkennbarkeit", "task": "Live-Set eröffnen",
        "verdict": "teilweise",
        "rationale": "Strophen tragen, aber der Fehlen des Intros kostet Einstieg",
        "author_id": "3fa85f64-…", "created_at": "2026-10-11T10:05:00Z" }
    ]
  }
}
```

---

## 3. Designentscheidungen

### 3.1 UUIDs als einzige Identität

- Jede Entität bekommt beim Erzeugen eine **UUIDv4** — lokal, ohne zentrale
  Vergabestelle. Damit können N Instanzen gleichzeitig schreiben, ohne
  ID-Kollisionen oder Koordinations-Lock.
- Referenzen sind **schwach typisiert** (`author_id: string`) — bewusst: ein
  Document ist portabel, und Fremd-Referenzen (auf nicht importierte Entitäten)
  können entstehen; Validierung erfolgt logisch, nicht schema-erzwungen.
  Importe fügen *niemals* abhängige Entitäten ohne ihre Ziele ein? Nein —
  simpler: Referenzen werden beim Import nur geprüft (Warnung im Report),
  niemals erzwungen. Das hält Teilausschnitte (scope) gültig.

### 3.2 Append-only-Varianten

- `derived_from` ist nach dem Anlegen immutable. „Ändern" = neue Variante mit
  neuer `derived_from`. Der gesamte Variantenraum ist damit ein DAG (Baum +
  Remix-Verbindungen).
- Folge: Es gibt **keine Update- und Delete-Operationen** im Kern-Protokoll —
  nur *Anlegen*. Was als „gelöscht" gilt, entscheidet sich später auf
  Anwendungsebene (z. B. per Befund/Statusfeld), nicht im Speicher-Layer.

### 3.3 Merge beim Import — UUID-Dedupe, kein Überschreiben

Import-Algorithmus (pro Entitätstyp, in Abhängigkeitsreihenfolge):

1. Index der vorhandenen UUIDs je Typ aufbauen.
2. Für jede eingehende Entität: UUID schon bekannt → **überspringen** (skip),
   unbekannt → **einfügen** (add).
3. Bei gleicher UUID wird **kein Feld verglichen und nichts aktualisiert** —
   „first write wins". Konflikte zwischen zwei unterschiedlichen Entitäten mit
   gleicher UUID können per Definition nicht auftreten, solange UUIDs korrekt
   vergeben werden (UUIDv4-Kollision ist vernachlässigbar).
4. Ergebnis: `{"agents": {"added": n, "skipped": n}, …}` als Import-Report.

Konsequenz: Zwei Instanzen, die gegenseitig exportieren/importieren, konvergieren
gegen denselben Zustand (CRDT-ähnlich für Insert-only-Mengen), ohne dass ein
Conflict-Resolution-Protokoll nötig wäre.

### 3.4 Zukunftsfelder ohne Schema-Bruch

- `WorkType`, `EdgeType`: offene Strings — neue Kantentypen sind reine Konvention.
- Optionale Felder (`content`, `note`, `description`) dürfen fehlen.
- Schema-Erweiterungen (neue Felder) werden als *additive, optionale* Felder
  eingeführt; alte Instanzen ignorieren unbekannte Felder beim Import (Toleranz-Regel).

---

## 4. Validierungsregeln (Referenzimplementierung)

1. `Agent.handle` ist pro Instanz eindeutig.
2. `Worktree.work_id` existiert; pro Work genau ein Worktree.
3. `Variant.derived_from` zeigt auf existierende Variante desselben Worktrees
   (oder `null` als einzige Wurzel).
4. `Edge.from/to_variant_id` existieren (quer über Werke erlaubt).
5. `Finding`: genau eines von `target_edge_id`, `target_variant_ids` gesetzt;
   Ziele existieren.
6. Alle `*_id`-Referenzen zeigen auf Entitäten, die im selben Document enthalten
   sind **oder** bereits lokal bekannt sind — sonst Warnung, kein Fehler.


---

# Teil 2 — Das Netz: zweistufiger Graph, Algebra, Zeit, Föderation

> **Fragestellung:** Was *ist* mooncells formal — und welche Operationen, Abfragen
> und Erweiterungen folgen aus dem Datenmodell von Teil 1, wenn man es als
> ein einziges zusammenhängendes Variantennetz liest?

## 5. Zweistufige Graphenstruktur — die Kurzform

Mooncells ist ein **zweistufiger Graph**. Die erste Ebene ist das Netz der
Werke, die zweite der Varianten-DAG im Inneren jedes Werks. Erstklassige
Graphelemente sind die **Varianten** — Werke und Worktrees sind Container, die
den Variantenraum organisieren.

```
Werk A ○───── remixt-aus ─────○ Werk B        ← Ebene 1: Netz der Werke
  │  Worktree                     │  Worktree
  ▼                               ▼
wurzel ──► variant-2             wurzel ──► variant-7     ← Ebene 2: Varianten-DAGs
   └──► variant-3 (claude)           └──► variant-8
              ▲
              └── Befund: „trägt sofort, aber verliert Wiedererkennbarkeit"
                  an Variante 3, bezogen auf Aufgabe „Live-Set eröffnen"
```

Ebene 1 ist keine eigenständige Datenstruktur, sondern eine **Ableitung**
(Quotient): Eine Kante `remixt-aus` von Variante x (Werk A) nach Variante y
(Werk B) wird zur Kante A → B im Werk-Graphen. Ebene 2 ist der gespeicherte
Zustand; Ebene 1 ist die Sicht darauf. Konsequenz: Beziehungen bestehen immer
zwischen konkreten Ausprägungen, nie zwischen Werken als Platzhaltern — das
hält die Rückführbarkeit scharf (welche Fassung remixt welche Fassung, mit
welchem Befund belegt).

## 6. Formales Modell

### 6.1 Definitionen

Sei eine Instanz ein Tupel `S = (A, W, T, V, E, F)` mit

- `A` Agenten, `W` Werke, `T` Worktrees (Bijektion `T ↔ W`, §4.2),
- `V` Varianten, `E` Kanten (beide global, über Werkgrenzen hinweg),
- `F` Befunde.

**Varianten-DAG eines Werks.** Für `w ∈ W` mit Worktree `t`:
`D_w = (V_t, A_t)` mit `V_t = { v ∈ V | v.worktree_id = t }` und
Ablenkungskanten `A_t = { (v', v) | v.derived_from = v' }`.
`D_w` ist ein **DAG mit genau einer Wurzel** (§4.3: `derived_from = null`
genau einmal; jede weitere Variante verweist kausal auf eine ältere —
Azyklizität folgt aus der Zeitbedingung).

**Globaler Variantengraph.** `G_V = (V, E')` mit `E' = A ∪ E`, d. h.
Ablenkungskanten und typisierte Kanten in einem Graphen. `G_V` ist i. Allg.
**zyklisch** (`remixt-aus`-Ketten können zurückführen) — erlaubt und
semantisch gewollt: Ein Zyklus markiert einen Re-Import oder eine
wechselseitige Remix-Fütterung, keinen Widerspruch.

**Quotientengraph (Ebene 1).** `G_W = (W, E_W)` mit
`E_W = { (W(x), W(y)) | ∃ Kante x→y in E }`, wobei `W(v)` das Werk der
Variante v ist. `G_W` ist eine *Multigraph-Reduktion*: parallele Kanten
mehrerer Variantenpaare desselben Werkpaars werden zu einem Kantenbündel
(„Werk B remixt Werk A an n Stellen, s. Befunde").

**Befundgraph.** `G_F`: Hyperkanten von Befunden auf `(Kante)` oder
`(Variantenpaar)` plus Pflichtfelder `criterion`, `task`, `verdict`. Der
Befund ist die einzige bewertende Instanz im System — er ersetzt Update und
Delete (§6.4).

### 6.2 Invarianten (erweitert um Teil 2)

7. `derived_from`-Kanten bilden pro Worktree einen Baum-DAG mit genau einer Wurzel.
8. Jede Kante `e ∈ E` verbindet existierende Varianten; Selbstkanten sind
   erlaubt (Selbst-Remix einer Folgevariante als Dokumentationskante).
9. Ein Befund hat genau ein Ziel (exklusiv); `verdict` bezieht sich immer auf
   das Tripel (Ziel, criterion, task) — nie auf die Variante „an sich".
10. Jede Operation trägt `author_id` eines registrierten Agenten — der Graph
    kennt keine anonymen Schreibvorgänge.

### 6.3 Leere Strukturen sind gültig

Ein Werk ohne Kanten, eine Variante ohne Befunde, ein Befund ohne Kante
(Ziel = Variantenpaar) sind valide Zustände. Das Modell erzwingt keine
Vollständigkeit — es erzwingt nur *Begründungspflicht dort, wo bewertet wird*.

## 7. Operations-Algebra

Das Kern-Protokoll (Teil 1, §3.2) hat nur Anlegen-Operationen. Erweitert um
Export/Import und die abgeleitete Selektion ergibt sich eine kleine Algebra:

```
register_agent(handle, type)                     → Agent
spawn_work(work_type, title)                     → (Work, Worktree, Wurzelvariante)
derive(v: Variant, label, notes, content?)       → Variant     -- v.derived_from = v
link(x: Variant, y: Variant, edge_type, note?)   → Edge        -- auch x.work ≠ y.work
assess(target: Edge | (Variant, Variant),
       criterion, task, verdict, rationale)      → Finding
select(w: Work, task, variant_ids: [Variant],
       ordnung, blend)                           → Variant     -- Selektion ist
                                                    selbst eine Variante im
                                                    Worktree von w, abgeleitet
                                                    aus der letzten gewählten
export(scope?)                                   → MDF-Dokument
import(doc)                                      → Import-Report
```

### 7.1 Algebra-Eigenschaften

- **Insert-only-Monotonie:** Jede Operation vergrößert `S` (mengen-monoton).
  Es gibt keine Verkleinerung — Kompensation geschieht durch *Gegeninhalt*,
  nicht durch Löschen (§9.3).
- **Kommutativität der Vereinigung:** `import(S, doc₁)` und `import(S, doc₂)`
  kommutieren auf Entitäts-Ebene (UUID-Dedupe, §3.3). Nicht kommutativ ist
  nur die *Anzeige-Reihenfolge* — die ist Präsentation, nicht Zustand.
- **Idempotenz:** `import(import(S, d), d) = import(S, d)`.
- **Konfliktfreiheit der Parallelarbeit:** `derive` ist der einzige
  schreibende Zugriff auf einen bestehenden Knoten (lesend), zwei Agenten
  erzeugen zwei Zweige statt einander zu verdrängen. Der DAG *ist* das
  Konfliktprotokoll: Divergenz ist sichtbarer Zustand, kein Fehler.
- **Begründungspflicht nur dort, wo sie trägt:** `link` und `assess` verlangen
  `note`/`rationale` mit Mindestlänge; `derive` verlangt `notes` (Abweichung
  beschreiben). `spawn_work` nicht — eine Intention darf ungeschönt beginnen.

### 7.2 Nicht-Operationen (bewusst ausgelassen)

- `update`, `delete` — ersetzt durch `derive` + Befund.
- `merge` zweier Varianten — ersetzt durch eine Selektions-Variante, die
  beide referenziert. Merge würde Abstammung verwischen; Selektion hält sie.
- `move` einer Variante in einen anderen Worktree — Werkgrenze ist Provenienz,
  kein Ordnungskriterium. Werke wechseln nur als Kopie mit `remixt-aus`-Kante.

## 8. Traversierungsmuster (kanonische Abfragen)

Die sechs Muster, aus denen sich der Rest zusammensetzt:

1. **Abstammung:** `ancestors(v)` / `descendants(v)` — Vorfahren-/Nachfahren-
   Hülle in `A_t`. Nutzen: „Welche Entscheidungen stecken in dieser Fassung?"
2. **Zweigdiff:** für `v₁, v₂` mit gemeinsamem Vorfahren `u`: der eindeutige
   Weg `v₁ ↝ u ↝ v₂` plus Befunde auf den Pfadkanten. Nutzen: „Was trennt die
   claude-Spur von meiner, und was trug jeweils?"
3. **Remix-Ketten:** Pfade in `E` mit Typfilter (`remixt-aus` only), über
   Werkgrenzen. Nutzen: Wanderung eines Bausteins durch das Gesamtwerk —
   die Grundformationen-These als Abfrage.
4. **Befundlastige Pfade:** Pfade, sortiert nach der *schlechtesten* Befund-
   Bewertung auf dem Weg (Kappung statt Mittelung, §9.1). Nutzen: Wo zerreißt
   die Kette, wenn man sie als Argument verwendet?
5. **Aufgaben-Selektion:** alle Varianten mit Befunden zu Aufgabe τ, besten-
   falls sortiert; Ergebnis wird per `select` verfestigt. Nutzen: die
   Tisch-Runde als Graphoperation.
6. **Erreichbarkeit der Werk-Ebene:** `G_W`-Erreichbarkeit mit Kantenbündel-
   Auflösung („welche Fassungpaare tragen diese Werk-Kante?").

Formale Gemeinsamkeit: Alle Muster sind *Pfadfragen auf `G_V = A ∪ E` mit
Befundgewichten*. Eine zukünftige Query-Schicht braucht daher nur einen
Pfadalgebra-Kern (Reichweite, Typfilter, Befund-Aggregation) — keine
vollwertige Graphdatenbank.

## 9. Fitness, Selektion, Kompensation

### 9.1 Fitness ist kontextbezogen und gekappt

Es gibt keine globale Fitness einer Variante. Fitness existiert nur als
`fitness(v, τ) = min { verdict(f) | f zielt auf v oder eine Abstammungskante
von v, f.task = τ }` — das schwächste Glied in der Kette zur Aufgabe τ
kappiert die Bewertung, Mittelung ist verboten (Analogie: Score-Kappung im
R4-Katalog; Widersprüche werden gespeichert, nicht geglättet). Dreiwertigkeit
(`tragfähig` > `teilweise` > `nicht-tragfähig`) ist bewusst grob —
Feinheit steckt im `rationale`, nicht im Wert.

### 9.2 Selektion

Eine `select`-Operation erzeugt eine Variante, die eine geordnete Teilmenge
mit Mischregeln referenziert (Feld `selection`, §14.4). Sie ist selbst im DAG
abgelegt und damit befundfähig, ableitbar, remixbar. Eine Selektion ist die
antwortbare Form der Frage „welche Fassung gilt gerade?": beantwortet durch
einen Knoten mit Provenienz, nicht durch ein Update auf dem Werk.

### 9.3 Kompensation statt Löschen

Etwas soll „weg"? Dann kommt Inhalt darüber: ein Befund
`verdict = nicht-tragfähig` mit criterion `verwahrung` und einem
`widerspricht`-/`bewertet`-Bezug, oder eine Selektion, die die Variante
schlicht nicht mehr enthält. Der DAG behält alles — was nicht mehr gilt,
ist als *begründeter Negativbefund* besser aufgehoben als als gelöschte
Zeile (Negativkarte statt Datenverlust; vgl. R4-Profilkarten).

### 9.4 Goodhart-Schutz

Bewertungsziel-Monotonie ist ein Angriffspfad: Wer Befunde erzeugt, um ein
Werk hochzurechnen, demontiert das Bewertungssystem. Schutz ist Protokoll,
nicht Technik: (a) Befunde brauchen `task` — Häufung auf dieselbe Aufgabe
ist sichtbar; (b) Canary-Aufgaben (Aufgaben mit bekannter nicht-tragfähiger
Variante) messen Bewertungstrennschärfe — wer nie `nicht-tragfähig` sagt,
ist billig statt gut; (c) Befund-Autoren sind Agenten-Knoten, deren eigene
Befund-Historie abfragbar ist.

## 10. Zeit — zwei Uhren

- **Physische Zeit** `created_at`: ISO-Wanduhr der erzeugenden Instanz.
  Nicht monoton über Instanzen hinweg (Uhren lügen, Reihenfolge bei
  Fast-Folge-Operationen unscharf).
- **Kausale Zeit** (Ablenkungskanten + Import): `v'` ist Vorgänger von `v`,
  wenn `v.derived_from = v'`; Import übernimmt Entitäten *als Ganzes* und
  erhält deren interne Kausalität, verschiebt aber ihre *Weltposition* (§12).
  Kausale Zeit ist die verlässlichere Ordnung — Abstammung ist immer
  azyklisch, Wanduhr nicht.

Konsequenzen: (1) Sortierungen nach `created_at` sind Präsentation, niemals
Semantik. (2) Befund-Datum ≠ Gegenstands-Datum: ein Befund kann eine alte
Variante bewerten; das ist Kern der Negativkarten-Logik. (3) Schema-v2 führt
optional eine Lamport-Zahl ein (§14.1), die Kausalität monoton macht, wo
`created_at` schweigt.

## 11. Provenienz

Jede Entität trägt Herkunft: `author_id`, `created_at`, Instanz-Kontext des
Exports. Dazu kommen zwei abgeleitete Sichten:

- **Herkunftskette eines Knotens:** `ancestors` projiziert auf Agenten —
  „wer hat diese Fassung mit wem erzeugt?" (Mitautorenschaft als Pfad).
- **Import-Kette einer Entität:** über welche Instanz-Pfade ist sie in die
  lokale Sicht gelangt? Schema-v2 ergänzt `origin` (§14.2), damit Import
  nicht als Erzeugung aussieht — ein häufiger Provenienz-Fehler in
  föderierten Systemen.

Provenienz-Regel: *Import dokumentiert Herkunft, er erfindet sie nicht neu.*

## 12. Föderation als globale Vereinigung

Der „Weltzustand" `S* = ⋃ᵢ Sᵢ` ist die Vereinigung aller Instanzzustände —
mathematisch wohldefiniert, praktisch nie vollständig sichtbar. Drei Sätze
prägen den Umgang damit:

1. **Konvergenz:** Zwei Instanzen, die sich gegenseitig vollständig
   exportieren, konvergieren gegen denselben Zustand (Insert-only +
   first-write-wins, §3.3). Peers sind *Transport*, nicht Identität — der
   Peer-Graph ist kein Konsens-Protokoll, sondern ein Übertragungsnetz.
2. **Partielle Sicht:** Eine Instanz darf Referenzen auf nicht importierte
   Entitäten halten (§3.1, Validierung als Warnung). Dangling references
   sind Normalzustand, kein Fehlerbild — sie markieren, wo die Welt noch
   nicht eingetroffen ist.
3. **Auto-Sync als ständige Vereinigung:** Push-nach-Schreiben (v1) ist die
   ungeduldige Form derselben Konvergenz. Jede lokale Schreiboperation ist
   bereits Teil von `S*`, sobald mindestens ein Pfad existiert; bis dahin ist
   sie lokal wahr und replizierbar bereit. Nichts wartet auf Koordination.

## 13. Autonome Agenten

Agenten sind **Knoten im Graph, nicht Außensteuerung**: `A` ist eine
Entitätsmenge wie `V`, und jede Schreiboperation verweist auf einen Agenten.
Daraus folgen drei Verhaltensregeln für autonome (model-)Agenten:

- **Lesen heißt Traversieren:** Ein Agent arbeitet auf `G_V` mit den Mustern
  aus §8 — typisch: Befundlage prüfen (Muster 4/5), dann `derive` oder
  `assess`.
- **Schreiben heißt Verantwortbarkeit:** Jede Kante und jeder Befund eines
  Agenten trägt dessen ID; `ancestors` auf Agenten macht Arbeitsweisen
  vergleichbar (welcher Agent begründet gut? wer bewertet nie negativ?).
- **Selbstbegrenzung ist Protokoll, nicht Höflichkeit:** Budget-Felder
  (max. Ableitungen pro Aufgabe, §14.6) und die Canary-Pflicht aus §9.4
  sind die Guardrails; ein Agent ohne sichtbare Kompensations-Befunde bei
  Fehlschlag ist ein Datenqualitätsproblem, kein Pech.

Menschen und Modelle unterscheiden sich im Graph nur über `agent_type` —
dieselben Operationen, dieselben Pflichten, dieselbe Befundbarkeit.

## 14. Schema-v2-Erweiterungen (additiv-optional, keine Brüche)

Toleranz-Regel aus §3.4 gilt: alles Neue ist optional, alte Instanzen
ignorieren Unbekanntes beim Import.

1. **`Variant.lamport: number?`** — kausale Uhr, `max(Eltern) + 1` bei
   `derive`, Import übernimmt Wert. Motivation: monotone Ordnung ohne
   Wanduhr (§10). Migration: fehlt = unbekannt, Queries fallen auf
   Abstammungstiefe zurück.
2. **`Variant.origin: { instance_id: string, imported_at: string }?`** —
   gesetzt beim *ersten* Import dieser Entität auf dieser Instanz.
   Motivation: Import ≠ Erzeugung (§11). Migration: fehlt = lokal erzeugt
   oder vor v2 importiert.
3. **`Finding.confidence: "belegt" | "vermutung"?`** (Default beim Fehlen:
   `belegt` retroaktiv nicht annehmbar → Queries behandeln fehlendes Feld
   als unmarkiert). Motivation: Vermutungen sichtbar machen, ohne die
   Drei-Werte-Skala aufzublähen; Anknüpfung an den R4-Befund, dass
   „vermutung vs. beleg" im TiSCH-Nachlauf 3 Rolle spielte.
4. **`Work.selection: { variant_ids: UUID[], ordnung: string, blend: string,
   task: string }?`** — die letzte verfestigte Selektion am Werk (§9.2).
   Motivation: „welche Fassung gilt gerade?" als Feld, nicht als Konvention.
5. **`Agent.trust: { introduced_by: UUID, canary_score?: number }?`** —
   wer hat den Agenten ins Netz gebracht, und wie schneidet er an Canaries ab
   (§9.4). Motivation: Bewertungstrennschärke als Erreichbarkeitsfrage.
6. **`Edge.evidence?: string`** — Verweis auf eine Variante oder einen
   Befund, der die Kante stützt. Motivation: Kanten ohne Begründung sind
   Netzinflation (R4-Grundregel 2); `note` bleibt Pflicht, `evidence` macht
   die Stütze adressierbar.

Grenze der Erweiterbarkeit: Nichts davon darf ein Pflichtfeld werden, solange
es Instanzen gibt, die ohne es exportieren. Wer Pflicht braucht, führt ihn
auf Query-Ebene ein („unmarkierte Befunde zählen nicht für Selektionen") —
nie auf Speicher-Ebene.

---

*Teil 2 entstand aus der Frage „ist mooncells ein riesiges Variantennetz?" —
Antwort: ein einziges zusammenhängendes Netz aus Varianten, lokal als
Worktree-DAG strukturiert, global über typisierte Kanten verbunden,
föderiert betrieben, append-only, mit dokumentierten Befunden als dem, was
aus einem Netz ein bewertetes Gesamtwerk macht.*
