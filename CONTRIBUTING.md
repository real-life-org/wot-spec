# Contributing

Dieses Repository ist die neutrale Spezifikationsquelle fuer das Web-of-Trust-Protokoll. Beitraege sind willkommen, muessen aber klar zwischen normativer Spec, Research und Implementierungsdetails trennen.

## Arten von Beitraegen

- **Spec-Klarstellung:** Praezisiert bestehende Anforderungen ohne Format- oder Verhaltensaenderung.
- **Spec-Aenderung:** Aendert normative Anforderungen, Wire-Formate, Testvektoren oder Conformance-Regeln.
- **Research:** Sammeln, Vergleichen oder Bewerten von Alternativen ohne normative Wirkung.
- **Testvektor:** Ergaenzt konkrete Werte, die Implementierungen reproduzieren muessen.
- **Schema:** Ergaenzt JSON Schemas fuer normative Payloads.

## Normative Sprache

Normative Dokumente verwenden deutsche RFC-2119-Begriffe:

- `MUSS` / `MUESSEN` fuer verpflichtende Anforderungen
- `SOLLTE` / `SOLLTEN` fuer empfohlene Anforderungen
- `DARF` / `DUERFEN` fuer erlaubte Optionen

Research-Dokumente duerfen freier formulieren, muessen aber als Research erkennbar bleiben.

## Pull Requests

Ein Pull Request sollte enthalten:

1. Kurze Beschreibung der Aenderung und Motivation.
2. Hinweis, ob die Aenderung normativ ist.
3. Wenn normativ: Impact auf `CONFORMANCE.md`, `VERSIONING.md`, Schemas oder Testvektoren.
4. Wenn Breaking Change: explizite Markierung und Changelog-Eintrag.

## Breaking Changes

Breaking Changes sind vor `v1.0.0` erlaubt, muessen aber sichtbar dokumentiert werden. Beispiele stehen in `VERSIONING.md`.

## Issues

Issues sollten moeglichst einem Arbeitsblock aus `ROADMAP.md` zugeordnet werden. Gute Issues enthalten:

- Problem oder Ziel
- Betroffene Dokumente
- Akzeptanzkriterien
- Hinweise auf Implementierungsfolgen

## Lizenz

Beitraege zur Spezifikation werden unter derselben Lizenz wie das Repository veroeffentlicht: CC-BY 4.0. Mit einem Beitrag bestaetigst du, dass du die notwendigen Rechte daran hast.
