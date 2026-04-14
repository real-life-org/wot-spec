# Web of Trust — Protokoll-Spezifikation

Eine offene, implementierungsunabhängige Spezifikation für ein dezentrales Web of Trust — Identität, Attestations und Vertrauensnetzwerke basierend auf echten Begegnungen.

## Ziel

Ein modulares Protokoll das ermöglicht:

- **Dezentrale Identität** — Selbstbestimmt, basierend auf etablierten kryptografischen Standards (BIP39, Ed25519, did:key)
- **Attestations** — Signierte Aussagen basierend auf echten Begegnungen (W3C Verifiable Credentials)
- **Vertrauensgraph** — Pfade zwischen Menschen, sichtbar und verifizierbar
- **Interoperabilität** — Verschiedene Implementierungen in verschiedenen Sprachen können zusammenarbeiten

## Abgrenzung: Was gehört wohin?

| Was | Ordner | Ziel-Repository | Warum |
|-----|--------|----------------|-------|
| Identität, Signaturen, Attestations | `01-wot-core/` | web-of-trust | Das Protokoll. Gemeinsam mit Sebastian. |
| Verschlüsselung, Sync, Transport, Discovery | `02-wot-sync/` | web-of-trust | Die Infrastruktur. Jede Local-First-App könnte das nutzen. |
| Datenmodell, Gruppen, Badges | `03-rls-extensions/` | real-life-stack | Unsere Erweiterungen. |
| Trust-Scores, Transactions | `04-hmc-extensions/` | human-money-core | Sebastians Erweiterungen. |

Die Trennung folgt der Frage: **Braucht Sebastian das?** Ja → WoT Core. Hilfreich → WoT Sync. Nein → Extensions oder anderes Repo.

Dieses Repository ist ein **Research-Repository**. Die Dokumente werden nach Fertigstellung und Abstimmung in ihre jeweiligen Ziel-Repositories umziehen.

## Struktur

### `01-wot-core/` — WoT Core

Das Fundament. Was jede Implementierung verstehen muss um Teil des Web of Trust zu sein.

| # | Dokument | Beschreibung |
|---|----------|-------------|
| 001 | [Identität und Schlüsselableitung](01-wot-core/001-identitaet-und-schluesselableitung.md) | BIP39 → Ed25519 → did:key |
| 002 | [Signaturen und Verifikation](01-wot-core/002-signaturen-und-verifikation.md) | Ed25519, JWS, JCS, SHA-256 |
| 003 | [Attestations](01-wot-core/003-attestations.md) | W3C Verifiable Credentials als signierte Aussagen |

### `02-wot-sync/` — Sync Layer

Die Infrastruktur für verschlüsselte Datensynchronisation. Nicht WoT-spezifisch — jede Local-First-App könnte das nutzen.

| # | Dokument | Beschreibung |
|---|----------|-------------|
| 004 | [Verschlüsselung](02-wot-sync/004-verschluesselung.md) | AES-256-GCM, ECIES, Gruppen-Verschlüsselung |
| 005 | [Sync-Protokoll](02-wot-sync/005-sync-protokoll.md) | Append-only Logs, Sedimentree, RIBLT |
| 006 | [Transport und Broker](02-wot-sync/006-transport-und-broker.md) | Broker, Inbox, Push, Multi-Broker |
| 007 | [Discovery](02-wot-sync/007-discovery.md) | Peer- und Broker-Findung |

### `03-rls-extensions/` — Real Life Stack Extensions

Implementierungsspezifische Erweiterungen für die Real Life App.

| # | Extension | Beschreibung |
|---|-----------|-------------|
| R01 | [Datenmodell](03-rls-extensions/R01-datenmodell.md) | Items, Spaces, Relations |
| R02 | [Gruppen](03-rls-extensions/R02-gruppen.md) | Rollen, Einladungen, Key Rotation |
| R03 | [Badges](03-rls-extensions/R03-badges.md) | Badges (Emoji, Farbe, Form), Event- und Ortsbezüge |

### `04-hmc-extensions/` — Human Money Core Extensions

Implementierungsspezifische Erweiterungen für Sebastians Payment-System.

| # | Extension | Beschreibung |
|---|-----------|-------------|
| H01 | [Trust-Scores](04-hmc-extensions/H01-trust-scores.md) | Quantitative Vertrauensstufen, Propagation, Hop-Limits |
| H02 | [Transactions](04-hmc-extensions/H02-transactions.md) | Gutscheine, Double-Spend-Prevention, SecureContainer |

### `research/` — Forschung

Hintergrundmaterial, Analysen und Architektur-Entwürfe.

| Dokument | Beschreibung |
|----------|-------------|
| [Sync & Transport Forschung](research/sync-and-transport.md) | Design-Space Exploration (10 Projekte, 4 Papers, 9 Talks) |
| [Sync-Architektur](research/sync-architektur.md) | Drei-Schichten-Modell (Deutsch) |
| [Identity Migration](research/identity-migration.md) | Schlüsselrotation bei DID-Wechsel |

## Architektur

```
┌─────────────────────────────────────────┐
│  Apps (WoT App, Real Life, Human Money) │
├──────────────────┬──────────────────────┤
│  RLS Extension   │  HMC Extension       │
├──────────────────┴──────────────────────┤
│  WoT Sync (Verschlüsselung, Sync,      │
│  Transport, Discovery)                  │
├─────────────────────────────────────────┤
│  WoT Core (Identität, Signaturen,      │
│  Attestations)                          │
└─────────────────────────────────────────┘
```

## Big Picture: Implementierung vs. Spec

### WoT Core (001-003)

| Spec | WoT (TypeScript) | Human Money Core (Rust) | Status |
|------|-------------------|------------------------|--------|
| 001 Identität | ✅ WotIdentity.ts | ✅ crypto_utils.rs | Beide implementiert, Details divergieren |
| 002 Signaturen | ✅ jws.ts, envelope-auth.ts | ✅ signature_manager.rs | Verschiedene Formate (JWS vs. Detached) |
| 003 Attestations | ✅ attestation.ts, VerificationHelper.ts | ✅ Trust Lists (SD-JWT) | Verschiedene Modelle |

### WoT Sync (004-007)

| Spec | WoT (TypeScript) | Human Money Core (Rust) | Status |
|------|-------------------|------------------------|--------|
| 004 Verschlüsselung | ✅ EncryptedSyncService.ts | ✅ secure_container_manager.rs | Verschiedene Algorithmen |
| 005 Sync-Protokoll | ⚠️ Full State Exchange (Bug) | ❌ Gossip via Piggybacking | Wir: muss umgebaut werden |
| 006 Transport/Broker | ✅ wot-relay, wot-vault | ❌ Serverlos (P2P) | Verschiedene Philosophie |
| 007 Discovery | ✅ wot-profiles | ❌ Direkter Austausch | Verschiedene Philosophie |

## Implementierungen

Diese Spezifikation wird aktuell von zwei unabhängigen Implementierungen informiert:

- [Web of Trust](https://github.com/real-life-org/web-of-trust) — TypeScript, Web Crypto API
- [Human Money Core](https://github.com/minutogit/human-money-core) — Rust, Ed25519 (dalek)

Die Spec ist an keine der beiden Implementierungen gebunden.

## Status

Alle Dokumente sind im Status **Entwurf**. Die Spec ist Gegenstand aktiver Diskussion zwischen den Autoren.

## Lizenz

Diese Spezifikation ist lizenziert unter [CC-BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
