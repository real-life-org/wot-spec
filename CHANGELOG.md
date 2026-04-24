# Changelog

Alle relevanten Aenderungen an der Web-of-Trust-Spezifikation werden in diesem Dokument festgehalten.

Das Format folgt grob [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versionierung folgt `VERSIONING.md`.

## Unreleased

### Added

- GitHub als kanonischer Publikationsort fuer die Spec eingefuehrt.
- `VERSIONING.md` fuer Repository-Releases, Spec-Profile und Wire-Versionen.
- `CONFORMANCE.md` fuer Core-, Sync- und Extension-Konformitaet.
- `test-vectors/` als normativer Ort fuer Interop-Testvektoren.

### Changed

- Testvektoren aus `research/` in den normativen Bereich verschoben.
- README um Governance-, Versionierungs- und Konformitaetsverweise erweitert.

## v0.1.0-draft - geplant

Erster oeffentlicher Draft-Snapshot der Spezifikation.

### Enthaltene Profile

- `wot-core@0.1` als Draft
- `wot-sync@0.1` als Draft
- `wot-rls@0.1` als Draft
- `wot-hmc@0.1` als Draft

### Release-Kriterien

- Alle vorhandenen normativen Dokumente haben expliziten Draft-Status.
- Krypto-Testvektoren sind unter `test-vectors/` verfuegbar.
- `CONFORMANCE.md` beschreibt den erwarteten Mindestumfang fuer `wot-core@0.1`.
