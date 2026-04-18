# Web of Trust — Protokoll-Spezifikation

Ein Protokoll für dezentrale Vertrauensnetzwerke basierend auf echten Begegnungen.

Zwei Menschen treffen sich, verifizieren ihre Identität, und stellen sich gegenseitig signierte Aussagen aus — kryptographisch verifizierbar, offline-fähig, ohne zentrale Instanz.

Das Protokoll besteht aus zwei Paketen:

**WoT Core** — Dezentrale Identität (DID), signierte Aussagen (W3C Verifiable Credentials) und ein Challenge-Response-Verifikationsverfahren für physische Begegnungen.

**WoT Sync** — Verschlüsselter Local-First Sync mit E2EE, Append-only Logs und Broker-as-Peer.

WoT definiert keine neuen Standards — es kombiniert bestehende zu einem interoperablen Profil:

| Standard | Verwendung |
|----------|-----------|
| [DID](https://www.w3.org/TR/did-core/) (W3C) | Dezentrale Identität (`did:key`) |
| [Verifiable Credentials](https://www.w3.org/TR/vc-data-model-2.0/) (W3C) | Signierte Aussagen (Attestations) |
| [DIDComm v2](https://identity.foundation/didcomm-messaging/spec/v2.0/) (DIF) | Nachrichtenformat und Verschlüsselung |
| [Ed25519](https://datatracker.ietf.org/doc/html/rfc8032) (RFC 8032) | Signaturen |
| [JWS](https://datatracker.ietf.org/doc/html/rfc7515) / [JWE](https://datatracker.ietf.org/doc/html/rfc7516) (RFC 7515/7516) | Signatur- und Verschlüsselungsformat |
| [JCS](https://datatracker.ietf.org/doc/html/rfc8785) (RFC 8785) | Kanonisierung |
| [BIP39](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki) | Mnemonic-Seed für Schlüsselableitung |
| [X25519](https://datatracker.ietf.org/doc/html/rfc7748) (RFC 7748) | Key Agreement (Authcrypt / ECDH-1PU) |
| [AES-256-GCM](https://csrc.nist.gov/publications/detail/sp/800-38d/final) (NIST) | Symmetrische Verschlüsselung |

## Architektur

```
┌─────────────────────────────────────────┐
│  Apps (WoT App, Real Life, Human Money) │
├──────────────────┬──────────────────────┤
│  RLS Extension   │  HMC Extension       │
├──────────────────┴──────────────────────┤
│  WoT Sync (Verschlüsselung, Sync,      │
│  Transport, Discovery, Gruppen)         │
├─────────────────────────────────────────┤
│  WoT Core (Identität, Signaturen,      │
│  Attestations, Verifikation)            │
└─────────────────────────────────────────┘
```

## Dokumente

### WoT Core — Das Fundament

Was jede Implementierung verstehen muss um Teil des Web of Trust zu sein.

| # | Dokument | Beschreibung |
|---|----------|-------------|
| 001 | [Identität und Schlüsselableitung](01-wot-core/001-identitaet-und-schluesselableitung.md) | BIP39 → Ed25519 → did:key |
| 002 | [Signaturen und Verifikation](01-wot-core/002-signaturen-und-verifikation.md) | Ed25519, JWS, JCS, SHA-256 |
| 003 | [Attestations](01-wot-core/003-attestations.md) | W3C Verifiable Credentials als signierte Aussagen |
| 004 | [Verifikation](01-wot-core/004-verifikation.md) | QR-Code-Austausch, Challenge-Response, In-Person-Verifikation |

### WoT Sync — Verschlüsselte Infrastruktur

Nicht WoT-spezifisch — jede Local-First-App könnte das nutzen.

| # | Dokument | Beschreibung |
|---|----------|-------------|
| 005 | [Verschlüsselung](02-wot-sync/005-verschluesselung.md) | AES-256-GCM, ECIES, Gruppen-Verschlüsselung |
| 006 | [Sync-Protokoll](02-wot-sync/006-sync-protokoll.md) | Append-only Logs, Sedimentree, RIBLT |
| 007 | [Transport und Broker](02-wot-sync/007-transport-und-broker.md) | Broker, Authentisierung, Capabilities, Inbox, Push |
| 008 | [Discovery](02-wot-sync/008-discovery.md) | Broker-Discovery, Profil-Service |
| 009 | [Gruppen und Mitgliedschaft](02-wot-sync/009-gruppen.md) | Rollen, Einladungen, Key Rotation |
| 010 | [Personal Doc und Cross-Device Sync](02-wot-sync/010-personal-doc.md) | Struktur, Key-Derivation, Device-Management |

### Extensions

| # | Dokument | Beschreibung |
|---|----------|-------------|
| R01 | [Badges](03-rls-extensions/R01-badges.md) | Badges (Emoji, Farbe, Form), Event- und Ortsbezüge |
| H01 | [Trust-Scores](04-hmc-extensions/H01-trust-scores.md) | Quantitative Vertrauensstufen, Propagation, Hop-Limits |
| H02 | [Transactions](04-hmc-extensions/H02-transactions.md) | Gutscheine, Double-Spend-Prevention, SecureContainer |
| H03 | [Gossip-Propagation](04-hmc-extensions/H03-gossip.md) | Trust-List-Verteilung über Inbox, Forward-Logik |

### Forschung

| Dokument | Beschreibung |
|----------|-------------|
| [Sync & Transport](research/sync-and-transport.md) | Design-Space Exploration (10 Projekte, 4 Papers, 9 Talks) |
| [Sync-Architektur](research/sync-architektur.md) | Drei-Schichten-Modell |
| [Identity Migration](research/identity-migration.md) | Schlüsselrotation bei DID-Wechsel |
| [Test-Vektoren](research/test-vektoren.md) | Kanonische Krypto-Werte für Interoperabilitäts-Tests |
| [Briefing Sebastian](research/briefing-sebastian.md) | Zusammenfassung und offene Fragen für Sebastian |
| [Interop und Zielgruppe](research/interop-und-zielgruppe.md) | Standards (DIDComm, OpenID4VC), Zielgruppen, eIDAS-Kontext |
| [DIDComm Migration](research/didcomm-migration.md) | Analyse, Roadmap, fehlende Teile, Sicherheitsanalyse |
| [Verbreitungsstrategie](research/verbreitungsstrategie.md) | 5-Jahres-Vision, Schlüsselpartner, eIDAS-Kontext |

## Implementierungen

Diese Spezifikation wird von zwei unabhängigen Implementierungen informiert:

- **[Web of Trust](https://github.com/real-life-org/web-of-trust)** — TypeScript, Web Crypto API
- **[Human Money Core](https://github.com/minutogit/human-money-core)** — Rust, Ed25519 (dalek)

Die Spec ist an keine der beiden Implementierungen gebunden. Abweichungen zwischen Spec und Implementierungen sind in den einzelnen Dokumenten dokumentiert.

## Status

Alle Dokumente sind im Status **Entwurf**. Dieses Repository ist ein Research-Repository — die Dokumente werden nach Fertigstellung in ihre jeweiligen Ziel-Repositories umziehen (WoT Core + Sync → `web-of-trust`, RLS Extensions → `real-life-stack`, HMC Extensions → `human-money-core`).

## Lizenz

[CC-BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
