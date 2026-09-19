# Contributing

Dieses Repository ist die neutrale Spezifikationsquelle fuer das Web-of-Trust-Protokoll. Beitraege sind willkommen, muessen aber klar zwischen normativer Spec, Research und Implementierungsdetails trennen.

## Arten von Beitraegen

- **Spec-Klarstellung:** Praezisiert bestehende Anforderungen ohne Format- oder Verhaltensaenderung.
- **Spec-Aenderung:** Aendert normative Anforderungen, Wire-Formate, Testvektoren oder Conformance-Regeln.
- **Research:** Sammeln, Vergleichen oder Bewerten von Alternativen ohne normative Wirkung.
- **Testvektor:** Ergaenzt konkrete Werte, die Implementierungen reproduzieren muessen.
- **Schema:** Ergaenzt JSON Schemas fuer normative Payloads.

## Normative Sprache

Die Konvention gilt fuer alle Repositories der Familie und steht einmal in
[real-life-org/meta → CONVENTIONS.md](https://github.com/real-life-org/meta/blob/main/CONVENTIONS.md).
Sie wird hier nicht wiederholt, damit sie nicht auseinanderlaeuft. Das Kurzmass
fuer dieses Repository:

Dieses Repository fuehrt **beide Dokumentklassen**:

- **Deutsch** — `01-wot-identity/`, `02-wot-trust/`, `03-wot-sync/`,
  `research/`. Deutsche RFC-2119-Begriffe.
- **Englisch** — `rltp/`. IETF-Editor's-Drafts mit BCP-14-Boilerplate, weil
  sie bei IIW, DIF und IETF zitierbar sein muessen. Dazu die beiden Dokumente,
  die sich an externe Implementierer richten:
  `conformance/rust-hmc-checklist.md` und `research/autonomous-pipeline.md`.

Ein Dokument gehoert zu genau einer Klasse. Die Wortsaetze werden nicht
gemischt.

Die deutschen Begriffe:

- `MUSS` / `MÜSSEN` fuer verpflichtende Anforderungen
- `DARF NICHT` / `DÜRFEN NICHT` fuer Verbote
- `SOLLTE` / `SOLLTEN` fuer Empfehlungen
- `DARF` / `DÜRFEN` fuer echte Optionen

`SOLL` ist **kein** Schluesselwort: Eine Empfehlung heisst `SOLLTE`, eine
Pflicht `MUSS`. Umlaute werden geschrieben, also `MÜSSEN` und nicht `MUESSEN`.

Geprueft wird das maschinell, nicht durch Lesen:

```
python3 scripts/check-normative-words.py
```

Laeuft in der CI mit.

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
