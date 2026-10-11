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
