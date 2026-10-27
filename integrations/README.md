# Adapter für den lokalen Rundweg nach DAS DAZWISCHEN

[dazwischen-rundweg.patch](dazwischen-rundweg.patch) enthält ausschließlich den ergänzten Rundwegadapter: drei TypeScript-Dateien für Paketprüfung und Empfangsansicht, deren CSS, gezielte Tests und zwei Einfügungen in `src/App.tsx`. Er enthält weder den gesamten DAZ-Bestand noch private Quellen, Laufzeitdaten, Abhängigkeiten oder einen fertigen Build.

Die Ausgangsbasis ist die am 27. Oktober 2026 tatsächlich angelegte isolierte Kopie des damals **lokal veränderten** DAZ-Arbeitsbaums. Dessen bereits vorhandene Quellen-, Verlaufs- und Erscheinungsfunktionen bleiben Voraussetzung; sie werden mit diesem Patch nicht ausgeliefert. Ein sauberer Checkout des beobachteten Git-Stands ist daher keine passende Ersatzbasis. Die bereits adaptierte isolierte Kopie benötigt den Patch nicht nochmals.

## Gegen die genaue Basis anwenden

Nur in einer dafür vorgesehenen externen Arbeitskopie der unten gebundenen Ausgangsbasis arbeiten. Vorher Zielvolume und fremde Änderungen prüfen. Nicht auf den aktiven DAZ-Werkraum, einen beliebigen `HEAD` oder bei abweichender Vorprüfung anwenden. Keine Konfliktauflösung erzwingen; eine andere Basis benötigt eine gesondert geprüfte Übertragung.

<details>
<summary>Technische Bindung und ausführbare Vorprüfung</summary>

Der bei der Kopie beobachtete Git-Zeiger war `97d39da5ff5ab87c044016fa90fa6b88f94ff60b` auf `codex/quellen-verlauf-20261026`; der Arbeitsbaum war verändert. Dieser Zeiger beschreibt die Herkunft, kein ausführbares Abbild der kopierten Änderungen.

Die einzige veränderte Bestandsdatei des Patches ist `src/App.tsx`. Vor Anwendung muss sie exakt **46.607 Byte** groß sein und SHA-256 `15670c62bad869540ca2026f6ca6fa5aeec27995c030ffe6274ef55f760b908b` besitzen. Die fünf weiteren Patchziele müssen noch fehlen. Patch-SHA-256: `d968652a0db77efcbb0c0e01e6d864d7eddda1d3a7ee3d37ad5407ef820dc239`.

Im Stamm der passenden, noch nicht adaptierten DAZ-Kopie ausführen; den Patchpfad gegebenenfalls an den registrierten externen Speicherort anpassen:

```sh
RUNDWEG_PATCH=/Volumes/ThunderBolt4_2TB/Development/Projects/mooncells-variantenraum-20261027/integrations/dazwischen-rundweg.patch
python3 - "$RUNDWEG_PATCH" <<'PY'
from pathlib import Path
import hashlib, sys
patch = Path(sys.argv[1])
assert hashlib.sha256(patch.read_bytes()).hexdigest() == 'd968652a0db77efcbb0c0e01e6d864d7eddda1d3a7ee3d37ad5407ef820dc239', 'Andere Patchfassung'
app = Path('src/App.tsx')
assert app.stat().st_size == 46607, 'Andere App-Basis'
assert hashlib.sha256(app.read_bytes()).hexdigest() == '15670c62bad869540ca2026f6ca6fa5aeec27995c030ffe6274ef55f760b908b', 'Andere App-Basis'
for name in ('src/types/variantHandoff.ts', 'src/lib/variantHandoff.ts',
             'src/components/VariantHandoffPanel.tsx', 'src/components/VariantHandoffPanel.css',
             'tests/variantHandoff.test.ts'):
    assert not Path(name).exists(), 'Adapterziel ist bereits vorhanden'
print('Gebundene App-Basis und neue Adapterziele stimmen.')
PY
```

Nur nach erfolgreicher Vorprüfung:

```sh
git apply --check "$RUNDWEG_PATCH"
git apply "$RUNDWEG_PATCH"
```

Die Übergabeprüfung hat in einem wegwerfbaren externen Prüfverzeichnis genau diese sechs Dateien rückwärts auf die gebundene Ausgangsbasis und anschließend vorwärts angewendet. Alle sechs Ergebnisse stimmten bytegleich mit dem isolierten Adapterstand überein. Das belegt die Patchanwendung, nicht die Vollständigkeit eines fremden DAZ-Checkouts.

</details>

## Bauen und verbinden

Vorhandene externe Abhängigkeiten verwenden; dieser Patch installiert nichts. In der passenden DAZ-Kopie prüfen und für den gemeinsamen Pfad bauen:

```sh
node --experimental-strip-types --test tests/*.test.ts
./node_modules/.bin/tsc -p tsconfig.app.json --noEmit
./node_modules/.bin/tsc -p tsconfig.node.json --noEmit
./node_modules/.bin/eslint src/components/VariantHandoffPanel.tsx src/lib/variantHandoff.ts src/types/variantHandoff.ts tests/variantHandoff.test.ts
./node_modules/.bin/vite build --base=/dazwischen/
```

Der DAZ-Agent meldet für diese isolierte Kopie 114 bestandene Node-Tests, darin 16 Adaptertests, sowie erfolgreiche TypeScript-, Adapter-Lint- und Vite-Prüfungen. Diese Bestandsprüfung wurde nicht durch eine Kopie aller Bestandsdateien in dieses Repository ersetzt.

Der Start des lokalen Pythonbrokers und seine Grenzen stehen in [docs/variantenraum.md](../docs/variantenraum.md#lokaler-rundweg-mit-das-dazwischen). Der Broker liefert den tatsächlichen DAZ-Build und den Variantenraum unter derselben Loopback-Adresse aus. Nach einem neuen DAZ-Build muss der Broker mit der neuen Buildbindung erneut geöffnet werden; ein laufender Broker verwirft weitere neue Übergaben, Quittungen und Ableitungen bei geändertem Zielbuild.

## Inhalt und Verantwortung

Der Adapter empfängt die ausgewählte Gesamtfassung, öffentliche Quellenzusammenfassungen und die gebundenen DAZ-Bezüge. Eine Zusammenfassung ist keine Originalpassage. Private Quellenparser, private Quellenbestände und genaue private Quellen-/Verlaufsfokusse werden nicht angebunden oder veröffentlicht.

Die Quittung dokumentiert einen ausdrücklich ausgelösten technischen Empfang mit Befund. Ausführer ist der fest konfigurierte Codex im genauen aktuellen Userauftrag. Fachliche Prüfung und menschliche Annahme folgen daraus nicht. Der Rückweg führt zur gespeicherten Variantenansicht; eine daraus ausdrücklich erzeugte neue Gesamtfassung bleibt eine lokale, separat gespeicherte Ableitung.

Der Patch wurde auf fremde und private Nutzdaten geprüft. Seine einzigen absoluten Beispielpfade und die Beispielkennung stehen in einem synthetischen Test, der ihre Unterdrückung in menschlichen Ausgaben prüft. Die unveränderten App-Kontextzeilen sind keine Übernahme der übrigen lokalen Weiterentwicklung.
