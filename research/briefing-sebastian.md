# Briefing für Sebastian

> **Nicht normativ:** Dieses Dokument ist Hintergrund, Analyse oder Planung. Normative Anforderungen stehen in den Spec-Dokumenten und in `CONFORMANCE.md`.

*Stand: 19. April 2026*

Lieber Sebastian,

hier ist der Stand der WoT-Spezifikation, als Grundlage für deine Review. Das Wichtigste zuerst: wir möchten dich bitten, dir die **H01 Trust-Scores** Extension anzuschauen und zu prüfen, ob sie deine Anforderungen für dein quantitatives Modell abdeckt — und natürlich die Einbettung in W3C Verifiable Credentials.

## Was ist WoT?

Ein Protokoll für dezentrale Vertrauensnetzwerke basierend auf echten Begegnungen. Zwei Menschen treffen sich, verifizieren ihre Identität, und stellen sich gegenseitig signierte Aussagen aus — kryptographisch verifizierbar, offline-fähig, ohne zentrale Instanz.

WoT definiert keine neuen Standards — es kombiniert bestehende (DID, W3C VC, DIDComm, Ed25519, JWS, AES-256-GCM) zu einem interoperablen Profil.

## Die Spec

Die Spec liegt auf Codeberg: `codeberg.org/web-of-trust/spec`

### WoT Core (das gemeinsame Fundament)

| # | Thema |
|---|-------|
| 001 | Identität und Schlüsselableitung (BIP39 → Ed25519 → did:key) |
| 002 | Signaturen und Verifikation (JWS, JCS, SHA-256) |
| 003 | Attestations (W3C Verifiable Credentials) |
| 004 | Verifikation (QR-Code, Challenge-Response) |

### WoT Sync (die Infrastruktur)

| # | Thema |
|---|-------|
| 005 | Verschlüsselung (AES-256-GCM, ECIES) |
| 006 | Sync-Protokoll (Append-only Logs) |
| 007 | Transport und Broker (DIDComm, Capabilities, Inbox pro Device) |
| 008 | Discovery (Broker-Discovery, Profil-Service) |
| 009 | Gruppen und Mitgliedschaft (Rollen, Einladungen, Key Rotation) |
| 010 | Personal Doc und Cross-Device-Sync |

### Extensions

| # | Thema | Status |
|---|-------|--------|
| R01 | Badges (Emoji, Farbe, Form) | Platzhalter |
| H01 | **Trust-Scores (dein quantitatives Modell)** | **Entwurf — bitte reviewen** |
| H02 | Transactions (Gutscheine, Double-Spend) | Platzhalter |
| H03 | Gossip-Propagation (Trust Lists über unsere Inbox) | Entwurf |

## Entscheidungen die wir getroffen haben

### JWS als einziges Signaturformat

Alle signierten Daten im Protokoll nutzen JWS Compact Serialization (RFC 7515). Attestations, Nachrichten, Log-Einträge — ein Format für alles. SD-JWT (was du für deine Listen nutzt) baut auf JWS auf und ist damit eine natürliche Erweiterung.

**Was das für dich heißt:** Dein SD-JWT-Format ist kompatibel. Du müsstest SHA3-256 → SHA-256 und Base58 → Base64URL umstellen.

### DIDComm v2 als Envelope-Format

Unser Nachrichtenformat folgt dem DIDComm v2 Plaintext Message Format (DIF) — auf Envelope-Ebene:

- **Plaintext Envelope** mit `id`, `typ`, `type`, `from`, `to`, `created_time`, `body`
- **Threading** via `thid` / `pthid` für Request/Response und verschachtelte Konversationen
- **ECIES** (X25519 + HKDF + AES-256-GCM) für 1:1-Verschlüsselung, Sender-Auth über innere JWS-Signatur
- **Feature-Discovery** über `protocols`-Feld im Profil (kein Laufzeit-Protokoll)

**Warum DIDComm — ehrliche Einordnung:** Das DIDComm-Ökosystem ist kleiner als oft angenommen. Die EU Digital Identity Wallet und eIDAS 2.0 haben sich für **OpenID4VC** (nicht DIDComm) als Exchange-Protokoll entschieden. Mainstream-Messaging (Matrix, Nostr, Signal) nutzt eigene Protokolle. DIDComm-Heimat ist das Aries/Hyperledger SSI-Ökosystem — real, aber eine Nische.

Was DIDComm uns konkret bringt:

- **Design-Disziplin** — klare Layer-Trennung, durchdachte Patterns
- **Library-Kompatibilität auf Envelope-Ebene** — `didcomm-node` (SICPA/didcomm-rust) und Veramo DIDComm koennen unsere Plaintext-Messages parsen
- **Formale Security-Analysen** verfügbar (ACM CCS 2024)
- **Envelope-Standard-Konformität** — billig zu bekommen, gibt uns Option-Value

Was DIDComm uns NICHT bringt: breite Interop zum EU-Wallet oder Mainstream-Messaging. Die breite Interop läuft über **Format-Standards**: DID:key, W3C VC 2.0, SD-JWT VC — nicht über das Exchange-Protokoll.

**Was das für dich heißt:** Dein Gossip-Protokoll (H03) nutzt unsere Inbox als Transport mit DIDComm-kompatiblem Envelope. Deine Trust-Lists werden in H01 als **SD-JWT VC** spezifiziert — das ist der strategisch wichtige Interop-Baustein, weil SD-JWT VC im EU-Wallet-Ökosystem Pflichtformat wird. Details zur ehrlichen Einordnung siehe [didcomm-migration.md](didcomm-migration.md).

### X25519 via separatem HKDF (nicht birationale Abbildung)

Der Verschlüsselungs-Key (X25519) wird über einen eigenen HKDF-Pfad abgeleitet (`"wot/encryption/x25519/v1"`), nicht über die birationale Abbildung aus dem Ed25519-Key.

**Warum:** Browser-Implementierungen (Web Crypto API) erzeugen Ed25519-Keys als `non-extractable` — der Private Key kann nicht für die Umrechnung ausgelesen werden. Der separate HKDF-Pfad funktioniert überall.

**Was das für dich heißt:** Du müsstest deinen X25519-Pfad umstellen — ein Change in deiner Krypto-Utils. Die Ed25519-Keys und DIDs bleiben gleich.

### Qualitative Attestations und Trust Lists koexistieren

Wir haben ausgearbeitet wie unsere qualitativen Attestations (Empfängerprinzip) und deine quantitativen Trust Lists (Senderprinzip) koexistieren:

| | Qualitative Attestation (Core) | Trust List (HMC Extension) |
|---|---|---|
| Inhalt | Freitext ("kann gut programmieren") | Trust-Level 0-3 |
| Eigentum | Empfänger besitzt | Sender verteilt |
| Veränderung | Neue Attestation ersetzt alte | Neue Listenversion ersetzt alte |
| Semantik | Geschenk | Weltsicht |

Beides auf demselben Identitäts-Layer (DID + Ed25519), verschiedene Verteilungswege für verschiedene Bedeutungen.

## Was wir von dir brauchen

### 1. Review von H01 — Trust-Scores als VC

Schau dir bitte `04-hmc-extensions/H01-trust-scores.md` an. Die zentrale Frage: deckt unser Vorschlag, dein quantitatives Modell als **W3C Verifiable Credential** zu verpacken, deine Anforderungen ab? Gibt es Aspekte deines Modells (Trust-Level-Semantik, Listen-Versionierung, Gewichtung), die im VC-Format nicht sauber abbildbar sind?

### 2. W3C VC als gemeinsames Attestation-Format

Funktioniert W3C VC als Verpackung für dein SD-JWT-Modell? Der Overhead ist ~100 Bytes pro Attestation (@context, type). Dafür bekommst du Interop mit dem gesamten VC-Ökosystem.

### 3. Key-Stretching

Du nutzt PBKDF2 mit 100k Runden zusätzlich zum BIP39-PBKDF2. Wir nicht. Wenn Stretching Teil des Standard-Pfades wird, ändern sich alle DIDs — eine Migration ist nötig. Lohnt sich das?

## Die Struktur

```
01-wot-core/         ← Das gemeinsame Fundament (001-004)
02-wot-sync/         ← Sync-Infrastruktur (005-010)
03-rls-extensions/   ← Unsere Extensions (Badges)
04-hmc-extensions/   ← Deine Extensions (Trust-Scores, Transactions, Gossip)
test-vectors/        ← Normative Interop-Testvektoren
research/            ← Forschung, Interop-Analyse, Outreach
```

## Was beide Systeme davon hätten

**Deine App** könnte unsere qualitativen Attestations anzeigen — "Bob kann gut programmieren", "Bob ist zuverlässig" neben deinem Trust-Level 85%.

**Unsere App** könnte deine Trust-Scores anzeigen — "Alice vertraut Bob zu 85%" neben unseren Pfad-Anzeigen.

**Beide Apps** hätten einen DIDComm-v2-kompatiblen Plaintext-Envelope — andere dezentrale Projekte könnten Messages zumindest erkennen, routen und über Adapter-Brücken weiterverarbeiten.

Beides auf demselben Vertrauensgraphen. Qualitativ und quantitativ als verschiedene Facetten derselben Beziehungen.
