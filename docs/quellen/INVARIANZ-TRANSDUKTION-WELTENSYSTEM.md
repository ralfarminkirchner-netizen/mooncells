# Invarianz & Transduktion — das Weltensystem des Atlas

**Konzept-Arbeitsgrundlage** · 2026-10-12 · Status: Diskussionsgrundlage, kein Bau-Auftrag
Bezüge: `traumaatlas-5/src/data/graph.ts` (139 Knoten / 395 Kanten),
`src/ocean/world.ts` (Store, Phänomen-Physik), `src/views/kosmos/layout.ts`
(Einbettung), `docs/pda-profil/PDA-PROFIL.md` (erstes Neuroprofil)

---

## 0. Auslöser und Kernidee

Ein großes Graph-System hält konsistent, während seine Darstellung zwischen
Welten wechselt: Die **Wasserwelt** (stehend) und eine **Weltraumwelt**
aufgelegt sind nicht deckungsgleich — im All sind die Kanten länger, alles
ist auseinandergezerrt — aber die Anordnung der Knoten, die Kanten selbst
und alle Verbindungen sind exakt dieselben. Übertragbar, ohne die identische
Map mehrfach zu besitzen. Vorbild: Zelda — A Link to the Past (Oberwelt /
Schattenwelt), aber radikalisiert: nicht deckungsgleiche Spiegelung,
sondern **verzerrte Kohärenz**. Die Form verändert sich, die Logik dahinter
— Relationen und Grundordnung — bleibt invariant.

Das führt direkt zu KiNFORMER, Transduktion und Invarianz: Der KiNFORMER
liest die Invariante; jede Welt ist eine Transduktion derselben in ein
anderes Vokabular — relationstreu, formverzerrend.

---

## 1. Das Vier-Schichten-Modell

Jede Welt des Atlas ist eine Projektion desselben Kerns in vier klar
getrennten Schichten. Verwechslung der Schichten ist die Hauptfehlerquelle
bei der Umsetzung.

### Schicht 1 — Topologie (INVARIANTE)

Knoten, Kanten, Relationstypen, Nachbarschaft. Der `atlasGraph`:
139 Knoten, 395 Kanten, 8+2 Typen. Ändert sich in **keiner** Welt.
Hier leben auch: Persistenz, Sog/Barriere-Physik (als abstrakte Kraft),
Direktsteuerung, „Integration, niemals Abweisung", PDA-Prinzipien,
KiNFORMER-Befund. Weltunabhängig.

### Schicht 2 — Metrik (GUMMIBAND)

Abstände, Skalierung, Dichte, Verzerrung, Clustering. Pro Welt ein
**Metrik-Profil**: globale Stretch-Faktoren, regionale Dehnung, Dichte-
Gradienten. Kanten**länge** ist Welt-Parameter; Kanten**existenz** ist
Invariante.

### Schicht 3 — Transduktion (VOKABULAR)

Dieselbe ID, anderes Erscheinen und andere Grammatik pro Welt:
Ein Symptom ist im Meer ein Wildling, im All ein Mond, im Garten eine
Pflanze, in der Schattenwelt eine Schutzgestalt. Implementiert als
Tabelle (nodeType/edgeType → Welt-Vokabular), IDs unverändert. Nicht
Anstrich — neue Sprache, 1:1 auf dieselbe Struktur abgebildet.

### Schicht 4 — Haut (austauschbar)

Farben, Licht, Material, Sound. Die billigste Schicht. Darf niemals als
„neue Welt" verkauft werden; dient nur der Abstimmung innerhalb einer Welt.

---

## 2. Das Gummiband-Gesetz (Lernbarkeitsbedingung)

Verzerrung ohne Desorientierung braucht eine harte Regel:

> **Ein Ort bleibt erkennbar an seinen Nachbarn.**

Zwei Phänomene, die im Meer eng beieinanderliegen, dürfen im All weit
auseinanderragen — sie bleiben Nachbarn, und der erfahrene Nutzer
„erkennt die Küste". Das Erkennungsmerkmal einer Welt ist nie die
Geometrie, sondern die **Adjazenz**.

Daraus folgen drei Konstruktionsregeln:

1. **Basis-Einbettung einmal, verzerren oft.** Ein Referenz-Layout
   (Force-Layout aus der Topologie) wird genau einmal berechnet und ist
   der unsichtbare Maßstab. Jede Welt ist eine *verzerrte Projektion*
   davon, keine handgebaute neue Map.
2. **Verzerrung ist ein Tensor, kein Zufall.** Pro Welt definiert ein
   Metrik-Profil, *welche Regionen* gedehnt, geschrumpft oder geclustert
   werden (z. B. All: radiale Dehnung nach außen, Faktor 3–5; Garten:
   hohe Dichte, verwachsene Pfade; Meeresenge: zwei Cluster werden
   künstlich genähert).
3. **Overlay-Erkennbarkeit als Test.** Legt man zwei Welten deckungsgleich
   übereinander, muss man dieselbe Anordnung erkennen, andere Maßstäbe
   sehen — sonst ist die Verzerrung zu frei und die Kohärenz gebrochen.

---

## 3. Architektur im Bestand

Der Kern existiert bereits; das Modell erklärt ihn und zeigt die
Erweiterungsstellen.

```
atlasGraph (graph.ts)          ← Schicht 1, einzige Invariante
  ├─ world.ts (Store, Kräfte)  ← Schicht 1 (abstrakte Physik)
  ├─ kosmos/layout.ts          ← eine Metrik-Einbettung (Referenzmuster
  │                               für Schicht 2: clusterAnchor, Force-Sim)
  ├─ OceanStage / Meer-3D      ← Schichten 2+3+4 für die Wasserwelt
  └─ GraphFallback             ← medium-agnostischer Invarianten-Ausdruck
                                  (Reduced Motion / No-WebGL) — bleibt
                                  in allen Welten gültig
```

**Neue Bausteine (konzeptionell):**

- `src/universe/baseEmbedding.ts` — Basis-Einbettung: Force-Layout aus
  `atlasGraph`, einmal deterministisch (seeded, wie `layout.ts` heute).
- `src/universe/metrics.ts` — Metrik-Profile pro Welt: verzerrbare
  Projektion der Basis-Einbettung (Stretch pro Region/Cluster, Dichte,
  ggf. dimensionsarme Zwangsbedingungen wie „Ringe um Zentren").
- `src/universe/transduction.ts` — Transduktionstabellen: pro Welt eine
  Abbildung nodeType/edgeType → Welt-Vokabular (Avatar, Begriff, Physik-
  Metapher). IDs bleiben; nur die Lesart wechselt.
- `src/universe/worlds.ts` — Welt-Registry: jede Welt = { Metrik-Profil,
  Transduktion, Haut, Physik-Modul }.
- KiNFORMER bleibt auf Schicht 1: Der Befund ist weltkonstant. Die Welt
  liefert nur die Metapher, in der der Befund sich zeigt.

**Entscheidend:** Niemals je Welt eine Kopie des Graphen, der Daten,
der Texte. Eine Invariante, beliebig viele Transduktionen.

---

## 4. Der Welten-Katalog

Jede Welt muss einen **semantischen Mehrwert** liefern — sonst ist sie
Anstrich. Fünf Welten mit je eigenem Anspruch sind auch fünfmal
Inhaltsarbeit (jede Transduktion muss textlich und fachlich stehen).

### 4.1 Wasserwelt — „Die Welle" (steht, Referenz)

- **Physik:** Gerstner-Wellen, Druckfeld, Sog/Barriere, Tauchen
- **Semantik:** Durchdringen, Integrieren — „das Meer trägt"
- **Metrik:** mittlere Dichte, Insel-Cluster, Untiefen
- **Status:** Stand `traumaatlas-5`, definiert das Vokabular, gegen das
  alle anderen Welten transduziert werden

### 4.2 Orbital — „Der Komet" (All-Welt)

- **Physik:** Gravitation statt Druck, Kepler-Orbits statt Schwimmpfade,
  Inertialflug; das Wellenpaket wird zum Kometen (Energie ∝ v² bleibt;
  Ablation ersetzt Gischt); Sog/Barriere wird wörtlich: Anziehung und
  Strahlungsdruck
- **Semantik:** Weite und Perspektive — Abstand macht Muster sichtbar.
  Verzerrung nach außen (der Satz des Anstoßes: alles auseinandergezerrt)
- **Metrik:** starke radiale Dehnung, Faktor 3–5; lange Kanten, leere
  Zwischenräume lebendig halten (Partikel, Schiffe, Staub)
- **Besonderheit:** Der Gerstner-/Wellenpaket-Ansatz transduziert fast
  wörtlich in Gravitationswellen-Pakete (Dispersion gilt im Vakuum)

### 4.3 Garten — „Anbau statt Behandlung"

- **Physik:** Wachstum, Saison, verwachsene Pfade; keine Flut, kein
  Abgrund — alles wächst langsam; Pflege als Interaktion
- **Semantik:** Integration als Gärtnern. **Die PDA-wahrste aller
  Welten:** Ein Garten verlangt nichts, er lädt ein. Kein Countdown,
  kein Sammelzwang — Dinge reifen, wenn sie reifen
- **Metrik:** hohe Dichte, enge verwachsene Strukturen, enge Kanten
  (Gegenteil All); Saison als eigener milder Zyklus neben Tag/Nacht
- **Transduktions-Beispiele:** Symptom = Pflanze (manchmal stachlig,
  immer gewachsen aus einem Grund); Übung = Pflegehandlung; Verfahren =
  Gartenbaustil; Neuroprofil = Bodenart/Standort

### 4.4 Oberwelt Landkarte — „Die klassische Karte"

- **Physik:** Kartografie: Wege, Höhenlinien, Legende, Kompass;
  ruhigste aller Welten — beinahe die Ansicht der Karte (Overview),
  aber bewohnbar
- **Semantik:** Orientierung, Übersicht, Einstieg; **direkter Spiegel der
  AD(H)S-/Neurospiele-Grammatik**: Interesse als Kompass, Minimap-Logik,
  keine Fail-States, sofortige Reversibilität — die Welt, in der
  spielerische Vertrautheit abgeholt wird
- **Metrik:** kartografisch gedrungen, verzerrt wie alte Karten
  (zielgerichtete Verzerrung im Dienst der Lesbarkeit)

### 4.5 Schattenwelt — „Die Schutz-Lesart" (der eigentliche Treffer)

Nicht eine Haut, sondern eine **zweite Wahrheit über dieselbe Karte**.
Vorbild: Zeldas Dark World — dieselben Orte, umgedrehte Bedeutung.
Traumapedagogisch exakt: Jedes Symptom ist eine Überlebensstrategie,
die ausgedient hat.

- **Physik:** gespiegelte Metrik, andere Lichtsetzung (dämmrig, aber
  niemals bedrohlich — die Schattenwelt ist sicher); Übergang frei
  betretbar und verlassbar (PDA-kompatibel: nie als Befehl)
- **Semantik:** Auf der Karte stehen nicht die Symptome, sondern ihre
  Schutzfunktionen:
  - `erstarrung` → „die Notbremse, die dich damals gerettet hat"
  - `hypervigilanz` → „der Wächter, der nie Feierabend macht"
  - `vermeidung` → „der Leibwächter, der die gefährlichen Orte kennt"
  - `scham` → „das Urteil, das du dir abgenommen hast, um es zu tragen"
- **Metrik:** Topologie identisch; Metrik leicht verzerrt (die Welt
  „atmet" langsamer); Beschilderung und Avatar vollständig transduziert
- **Durchgang:** passt zum Tag-/Nacht-Zyklus und zum Tauch-Modus —
  Oberfläche = Symptom-Lesart, Tauch-/Schattenebene = Schutz-Lesart

### 4.6 Fraktaler Zoom (durch alle Welten)

Knoten aufklappbar: Jede Nachbarschaft ist selbst eine kleine Welt —
Insel → Planet → Gartengrundstück, je nach Haut. Dasselbe Gesetz,
drei Vergrößerungen. Der Kosmos (heute: Kapitel „Der große Graph") ist
der Sonderfall „Zoom = maximal": die ganze Karte als Konstellation.

---

## 5. Transduktion — Arbeitsbeispiel

| Knoten (ID, invariant) | Wasserwelt | Orbital | Garten | Schattenwelt |
|---|---|---|---|---|
| `flashbacks` | Wildling, treibend | heißer Mond, unruhiger Orbit | Distel, sticht nur bei Berührung | „der Bote, der die Wahrheit wiederholt, bis sie gehört wird" |
| `e:pendeln` | Übung: Pendeln | Manöver: Hin-und-Her mit Rückkehrrecht | Pflege: zwischen Beet und Bank wechseln | „der Weg, der immer nach Hause führt" |
| `m:se` | Verfahren-Insel | Raumstation, Titration-Kuppel | Gartenbaustil: Schrittweise, nie reißen | „das Handwerk des sanften Zurückweichens" |
| `p:pda` | Profil-Tiefsee-Form | Asteroidengürtel um Autonomie-Zentrum | Standort: karger, freier Boden | „der Wächter der Selbstbestimmung" |
| `state:dorsal` | Tiefwasser-Schicht | fernes, kaltes Außensystem | Winterbeet, Ruhephase | „der Schutz des Zurückziehens" |

Regel: Die Schattenwelt transduziert **immer in die Schutzfunktion**,
nie in Pathologie und nie in Kitsch. Jede Formulierung fachlich gegenlesen.

---

## 6. KiNFORMER, Transduktion, Invarianz — die begriffliche Verankerung

- **Invarianz** = Schicht 1. Was KiNFORMER liest, ändert sich zwischen
  Welten nicht: Befund, Relationen, Tiefgang-Stufen, QuerLeser-Wege.
- **Transduktion** = Schicht 3. Der Übergang von einer Welt in die
  nächste ist eine relationstreue Abbildung: Struktur bleibt, Vokabular
  wechselt. „Transduktion bewahrt die Relation, während die Form sich
  verzerrt" — Spezifikation statt Slogan.
- **Metrik-Verzerrung** = Schicht 2. Das Gummiband zwischen den Welten:
  die Freiheitsgrade, die jede Welt hat, ohne die Kohärenz zu brechen.
- Praktisch: Ein im Meer erkannter Ort (`erstarrung`, neben `state:dorsal`)
  ist im All, im Garten und in der Schattenwelt *derselbe Ort* — nur
  anders ausgesprochen. Erkenntnis des Nutzers: „Ich kenne diese Küste."

---

## 7. Bau-Strategie (Empfehlung, kein Auftrag)

1. **Gerüst zuerst:** `universe/`-Module (Basis-Einbettung, Metrik,
   Transduktion, Welt-Registry) gegen den Bestand — ohne neue Welt.
   Bildbeweis: dieselbe Karte in zwei Metrik-Profilen übereinandergelegt
   (Overlay-Test aus §2).
2. **Zwei Welten bauen:** Wasserwelt bleibt Referenz; **eine** neue Welt
   zuerst. Empfehlung: Schattenwelt (höchster semantischer Mehrwert,
   geringster Grafik-Aufwand — Metrik nur leicht verzerrt, Haut
   existiert als Nacht-Modus bereits) **oder** Orbital (höchster
   visueller Impact, Physik-Verwandtschaft zum Wellenpaket).
3. **Rest als Registry-Eintrag:** Garten, Oberwelt, Zoom-Stufen als
   Profile anlegen, aber nicht bauen — erst wenn Inhalte (Transduktions-
   Texte) stehen.
4. **Inhalt vor Haut:** Jede Welt braucht ihre transduzierten Texte
   (Schattenwelt-Beschilderungen, Garten-Vokabular) *vor* dem
   Grafik-Feinschliff. Das ist der teuerste Teil und der, der den Atlas
   von der Spielerei unterscheidet.

## 8. Risiken und Warnungen

- **Anstrich-Falle:** Welten ohne semantischen Mehrwert zerstören die
  Glaubwürdigkeit des Atlas. Jede Welt muss beantworten: Was kann der
  Nutzer *hier* verstehen, was er dort nicht konnte?
- **Orientierungsbudget:** Zu viele verzerrte Welten ohne Anker
  überfordern. Anker = Nachbarschaft (§2) + ein fester Übergangsritus
  (Weltwechsel als erkennbarer, reversibler Akt).
- **Ton im Vakuum:** Das All ist kühl; der Atlas ist warm (Ruhe, Wärme,
  Würde). Orbital braucht explizite Wärme-Regie (Sonnennähe als
  Verbundenheit, Komet als „schmutziger Schneeball" — verletzlich,
  nicht heroisch).
- **Semantische Doppelbelastung:** Symptom- und Schutz-Lesart dürfen
  nie widersprüchlich wirken — die Schattenwert-Formulierungen sind
  therapeutische Statements und brauchen Fach-Review.
- **PDA in allen Welten:** Kein Sammelzwang, keine Fail-States, keine
  unumkehrbaren Übergänge — das Garten-Prinzip („einladen, nicht
  verlangen") gilt universell.

## 9. Offene Fragen

- Weltwechsel: frei wählbarer Skin oder narrative Ebene (Orte, die den
  Übergang *sind*)? — Empfehlung: zuerst frei wählbar, später verorten.
- Wie viele Welten maximal gleichzeitig sichtbar? (Empfehlung: eine, mit
  sanftem Übergang — Split-Screen bricht die Immersion.)
- Zoom-Stufen: fest (3) oder kontinuierlich? (Empfehlung: fest, mit
  Marker-Anker.)
- Soll die Schattenwelt als Spiegel (deckungsgleich) oder als Verzerrung
  gebaut werden? (Empfehlung: leichte Verzerrung — sonst droht der
  billige Skin-Eindruck, den das Gummiband-Gesetz gerade vermeidet.)
