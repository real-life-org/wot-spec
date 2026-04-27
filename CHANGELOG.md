# Changelog

Alle relevanten Aenderungen an der Web-of-Trust-Spezifikation werden in diesem Dokument festgehalten.

Das Format folgt grob [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versionierung folgt `VERSIONING.md`.

## Unreleased

### Added

- `GLOSSARY.md` fuer normative Begriffe und konsistente Terminologie.
- `wot-identity@0.1` und `wot-trust@0.1` ersetzen das bisherige `wot-core@0.1`-Profil.

### Changed

- Erste Terminologie-Korrekturen in Sync-Dokumenten: `Master Key`/`Space Private Key`/`authorDid` durch aktuelle Begriffe ersetzt.
- Normative Dokumente in profilbezogene Ordner verschoben und Nummerierung pro Profil neu gestartet (`01-wot-identity/`, `02-wot-trust/`, `03-wot-sync/`).

## v0.1.0-draft - 2026-04-24

Erster oeffentlicher Draft-Snapshot der Spezifikation.

### Enthaltene Profile

- `wot-core@0.1` als Draft
- `wot-sync@0.1` als Draft
- `wot-rls@0.1` als Draft
- `wot-hmc@0.1` als Draft

### Added

- GitHub als kanonischer Publikationsort fuer die Spec eingefuehrt.
- `ROADMAP.md` fuer Milestones, Arbeitsbloecke und Release-Kriterien.
- `VERSIONING.md` fuer Repository-Releases, Spec-Profile und Wire-Versionen.
- `CONFORMANCE.md` fuer Identity-, Trust-, Sync- und Extension-Konformitaet.
- `CONTRIBUTING.md` fuer Beitragsregeln.
- `LICENSE` mit CC-BY-4.0-Hinweis.
- `.github/ISSUE_TEMPLATE/` fuer Spec- und Research-Issues.
- `schemas/` als geplanter Ort fuer JSON Schemas.
- `test-vectors/` als normativer Ort fuer Interop-Testvektoren.
- GitHub Actions Workflow fuer Schema-, Testvektor- und DIDComm-Envelope-Validierung.
- Maschinenlesbare Phase-1-Interop-Testvektoren als JSON.
- Valide und invalide Schema-Beispiele fuer alle aktuellen Payload-Schemas.

### Changed

- Testvektoren aus `research/` in den normativen Bereich verschoben.
- README um Governance-, Versionierungs- und Konformitaetsverweise erweitert.
- Trust 002 begruendet explizit, warum Verification-Attestations die QR-Challenge nur ueber die Nonce binden und keinen `challengeHash` verwenden.
- JSON Schemas fuer die zentralen Identity-, Trust-, Sync- und HMC-Payloads ergaenzt.
- Zusaetzliche Testvektoren fuer DIDComm-Plaintext-Envelopes, DID-Resolution, ECIES, deterministische Nonces, Log-JWS, Capability-JWS, Admin-Key-Ableitung und SD-JWT VC ergaenzt.
- Identity 002 und Sync 003 klaeren `kid` fuer Space-Capabilities als `wot:space:<spaceId>#cap-<generation>`.
- Sync 003 macht `typ: "application/didcomm-plain+json"` verpflichtend, damit Plaintext-Envelopes mit etablierten DIDComm-v2-Libraries validierbar sind.
