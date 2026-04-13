# Web of Trust — Protokoll-Spezifikation

Eine offene, implementierungsunabhängige Spezifikation für ein dezentrales Web of Trust — Identität, Attestations und Vertrauensnetzwerke basierend auf echten Begegnungen.

## Ziel

Ein modulares Protokoll das ermöglicht:

- **Dezentrale Identität** — Selbstbestimmt, basierend auf etablierten kryptografischen Standards (BIP39, Ed25519, did:key)
- **Attestations** — Signierte Aussagen basierend auf echten Begegnungen (W3C Verifiable Credentials)
- **Vertrauensgraph** — Pfade zwischen Menschen, sichtbar und verifizierbar
- **Interoperabilität** — Verschiedene Implementierungen in verschiedenen Sprachen können zusammenarbeiten

## Struktur

Das Repository ist in vier Bereiche gegliedert:

### `core/` — WoT Core

Das Fundament. Was jede Implementierung verstehen muss um Teil des Web of Trust zu sein.

| # | Dokument | Beschreibung |
|---|----------|-------------|
| 001 | [Identität und Schlüsselableitung](core/001-identitaet-und-schluesselableitung.md) | BIP39 → Ed25519 → did:key |
| 002 | [Signaturen und Verifikation](core/002-signaturen-und-verifikation.md) | Ed25519, JWS, JCS, SHA-256 |
| 003 | [Attestations](core/003-attestations.md) | W3C Verifiable Credentials als signierte Aussagen |

### `sync/` — Sync Layer

Die Infrastruktur für verschlüsselte Datensynchronisation. Nicht WoT-spezifisch — jede Local-First-App könnte das nutzen.

| # | Dokument | Beschreibung |
|---|----------|-------------|
| 005 | [Verschlüsselung](sync/005-verschluesselung.md) | AES-256-GCM, ECIES, Gruppen-Verschlüsselung |
| 006 | [Device-Keys und Delegation](sync/006-device-keys-und-delegation.md) | Geräte-Identität, Master-Delegation |
| 007 | [Sync-Protokoll](sync/007-sync-protokoll.md) | Append-only Logs, Sedimentree, RIBLT |
| 008 | [Transport und Broker](sync/008-transport-und-broker.md) | Broker, Inbox, Push, Multi-Broker |
| 009 | [Discovery](sync/009-discovery.md) | Peer- und Broker-Findung |

### `extensions/` — Extensions

Implementierungsspezifische Erweiterungen die auf dem WoT Core aufbauen.

| Extension | Beschreibung |
|-----------|-------------|
| [Real Life: Display](extensions/reallife-display.md) | Badges (Emoji, Farbe, Form), Event- und Ortsbezüge |
| [Human Money: Trust-Scores](extensions/humanmoney-trust-scores.md) | Quantitative Vertrauensstufen, Propagation, Hop-Limits |
| [Human Money: Payment](extensions/humanmoney-payment.md) | Gutscheine, Double-Spend-Prevention, SecureContainer |

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
│  Real Life       │  Human Money         │
│  Extension       │  Extension           │
├──────────────────┴──────────────────────┤
│  Sync Layer (Verschlüsselung, Sync,    │
│  Transport, Device-Keys, Discovery)     │
├─────────────────────────────────────────┤
│  WoT Core (Identität, Signaturen,      │
│  Attestations)                          │
└─────────────────────────────────────────┘
```

Der WoT Core ist der gemeinsame Standard. Der Sync Layer ist die Infrastruktur. Extensions erweitern beides für spezifische Anwendungsfälle.

## Implementierungen

Diese Spezifikation wird aktuell von zwei unabhängigen Implementierungen informiert:

- [Web of Trust](https://github.com/real-life-org/web-of-trust) — TypeScript, Web Crypto API
- [Human Money Core](https://github.com/minutogit/human-money-core) — Rust, Ed25519 (dalek)

Die Spec ist an keine der beiden Implementierungen gebunden.

## Status

Alle Dokumente sind im Status **Entwurf**. Die Spec ist Gegenstand aktiver Diskussion zwischen den Autoren.

## Mitwirken

Dies ist eine offene Spezifikation. Beiträge von allen sind willkommen die an dezentralen Vertrauenssystemen arbeiten.

## Lizenz

Diese Spezifikation ist lizenziert unter [CC-BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
