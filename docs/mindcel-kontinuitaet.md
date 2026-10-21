# MiNDCEL → Mooncells: Variantenräume im Gesamtsystem

## Ralfs Erklärung vom 12. Oktober 2026

Mooncells ist die Umbenennung und Weiterentwicklung des über Monate ausgearbeiteten MiNDCEL-Konzepts. Das Gesamtnetz ist ein Variantenraum. Seine Knoten enthalten Worktrees als Variantenräume einer Sache. Diese Sache ist wiederum eine Ausprägung des Ganzen und steht über Beziehungen mit anderen Ausprägungen in Verbindung.

Ralfs Bild: Blätter sind nebeneinander Varianten des Gleichen; der Baum verbindet sie. Der Baum ist seinerseits ein Knoten im größeren Netz. Dieses Bild bestimmt die gewünschte Organisation und Navigation. Es ist keine durch die Software bewiesene Aussage über die Realität.

Mooncells soll fundamental in das Gesamtsystem integriert werden. Es ersetzt in der aktuellen Arbeitsrichtung die frühere Musterstudio-Zuordnung. Historische Quellen behalten ihre ursprünglichen Namen und Inhalte.

## Vorhandene Ausarbeitungen

- [MiNDCEL README](https://github.com/ralfarminkirchner-netizen/mindcel/blob/main/README.md): begehbares Netzwerk, lesbares Notizbuch und Remixer; Ring ohne festen Kern; jeder Knoten eine Perspektive.
- [Moonfingers-Ring](https://github.com/ralfarminkirchner-netizen/mindcel/blob/main/MOONFiNGERS-RING.md): Kohärenz durch Beziehungen, Familien verwandter Perspektiven, keine automatische Wahrheit aus Dichte oder Knotengröße. Der historische Text trägt den Status `proposed`.
- [Mooncells-Tiefenkonzept](konzept.md): ein zusammenhängendes Variantennetz, lokal Abstammung im Worktree, global typisierte Beziehungen. Varianten sind die präzisen Endpunkte dieser Beziehungen; die Werkansicht lässt sich daraus ableiten.

## Zuordnung zum bestehenden Code

| Perspektive | Bestehende Darstellung im Datenmodell |
|---|---|
| Sache als Knoten der Übersicht | `Work` bündelt zugehörige Worktrees. |
| Variantenraum innerhalb dieser Sache | `Worktree` enthält Varianten mit `derived_from`. |
| Konkrete Ausprägung | `Variant` mit Inhalt, Autor und Herkunft. |
| Beziehung zu einer anderen Ausprägung | `Edge` zwischen konkreten Varianten, auch über Werkgrenzen. |
| Ganzes Netz | Zusammenhängende Ansicht aus Abstammung und typisierten Beziehungen; Zusammenhang einzelner Datensätze muss tatsächlich vorliegen. |

Eine Übersicht darf Beziehungen auf Werkebene zusammenfassen. Beim Öffnen muss sie zu den konkreten beteiligten Varianten zurückführen. Der Wechsel der Betrachtungsebene darf Herkunft, Inhalt und Beziehung nicht verlieren.

## Noch offene Integration

Der aktuelle Code belegt Werk → Worktree → Variante und Beziehungen zwischen Varianten. Er belegt noch keine beliebig rekursive Verschachtelung von Variantenräumen, keine Vault-Anbindung und keinen durchgängigen Moonfingers-Nutzerweg. Diese Lücken dürfen nicht als bereits implementiert dargestellt werden.

Der nächste konkrete Nutzerweg ist: in Moonfingers eine vorhandene Sache wählen, ihren zugehörigen Variantenraum öffnen, eine Ausprägung lesen und über eine belegte Beziehung zu einer anderen Sache wechseln; danach zur Ausgangsstelle zurückkehren. Die Zuordnung muss aus bestehenden Quellen und Konfigurationen stammen. Keine Titelgleichheit als Identitätsbeweis, keine erfundene Kante, kein zusätzlicher konkurrierender Wahrheitsbestand.

Die rekursive Idee soll die Navigation und Ansichten tragen. Ob sie zusätzliche persistente Containment-Beziehungen benötigt, ist erst am tatsächlichen Bestand und diesem Nutzerweg zu entscheiden. Das Bild allein rechtfertigt keine sofortige Schema-Migration. Befunde bleiben begründete Einschätzungen; menschliche Freigabe bleibt eine eigene Entscheidung.
