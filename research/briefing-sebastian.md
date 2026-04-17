# Briefing für Sebastian

*Stand: 17. April 2026*

Lieber Sebastian,

wir haben in den letzten Tagen intensiv an der WoT-Spezifikation gearbeitet. Hier ist der aktuelle Stand — als Grundlage für unser nächstes Gespräch.

## Was ist WoT?

Ein Protokoll für dezentrale Vertrauensnetzwerke basierend auf echten Begegnungen. Zwei Menschen treffen sich, verifizieren ihre Identität, und stellen sich gegenseitig signierte Aussagen aus — kryptographisch verifizierbar, offline-fähig, ohne zentrale Instanz.

WoT definiert keine neuen Standards — es kombiniert bestehende (DID, W3C VC, DIDComm, Ed25519, JWS, AES-256-GCM) zu einem interoperablen Profil.

## Die Spec

Die Spec liegt auf Codeberg: `codeberg.org/web-of-trust/spec`

### WoT Core (4 Dokumente — das gemeinsame Fundament)

| # | Thema | Status |
|---|-------|--------|
| 001 | Identität und Schlüsselableitung (BIP39 → Ed25519 → did:key) | Entwurf |
| 002 | Signaturen und Verifikation (JWS, JCS, SHA-256) | Entwurf |
| 003 | Attestations (W3C Verifiable Credentials) | Entwurf |
| 004 | Verifikation (QR-Code, Challenge-Response) | Entwurf |

### WoT Sync (5 Dokumente — die Infrastruktur)

| # | Thema | Status |
|---|-------|--------|
| 005 | Verschlüsselung (AES-256-GCM, Authcrypt/ECDH-1PU) | Entwurf |
| 006 | Sync-Protokoll (Append-only Logs, Sedimentree, RIBLT) | Entwurf |
| 007 | Transport und Broker (DIDComm, Capabilities, Inbox pro Device) | Entwurf |
| 008 | Discovery (Broker-Discovery, Profil-Service) | Entwurf |
| 009 | Gruppen und Mitgliedschaft (Rollen, Einladungen, Key Rotation) | Entwurf |

### Extensions

| # | Thema | Status |
|---|-------|--------|
| R01 | Badges (Emoji, Farbe, Form) | Platzhalter |
| H01 | Trust-Scores (dein quantitatives Modell) | Entwurf |
| H02 | Transactions (Gutscheine, Double-Spend) | Platzhalter |
| H03 | Gossip-Propagation (Trust Lists über unsere Inbox) | Entwurf |

## Entscheidungen die wir getroffen haben

### JWS als einziges Signaturformat

Alle signierten Daten im Protokoll nutzen JWS Compact Serialization (RFC 7515). Attestations, Nachrichten, Log-Einträge — ein Format für alles. SD-JWT (was du für deine Listen nutzt) baut auf JWS auf und ist damit eine natürliche Erweiterung.

**Was das für dich heißt:** Dein SD-JWT-Format ist kompatibel. Du müsstest SHA3-256 → SHA-256 und Base58 → Base64URL umstellen.

### DIDComm v2 als Nachrichtenformat

Unser Nachrichtenformat folgt dem DIDComm v2 Plaintext Message Format (DIF). Die Verschlüsselung für 1:1-Nachrichten nutzt Authcrypt (ECDH-1PU) — der DIDComm-Standard.

**Warum:** Interoperabilität mit dem dezentralen Ökosystem (Circles, Nostr, Briar und andere Projekte die dezentrale Identität brauchen). DIDComm teilt unsere Werte: P2P, offline-fähig, zensurresistent.

**Was das für dich heißt:** Dein Gossip-Protokoll (H03) nutzt unsere Inbox als Transport — die jetzt DIDComm-kompatibel ist. Deine Trust-List-Deltas sind DIDComm-Nachrichten mit SD-JWT im Body.

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

## Was noch offen ist (für unser Gespräch)

### 1. Key-Stretching

Du nutzt PBKDF2 mit 100k Runden zusätzlich zum BIP39-PBKDF2. Wir nicht. Wenn Stretching Teil des Standard-Pfades wird, ändern sich alle DIDs — eine Migration ist nötig. Lohnt sich das?

### 2. VCs als gemeinsames Attestation-Format

Funktioniert W3C VC als Verpackung für dein SD-JWT-Modell? Der Overhead ist ~100 Bytes pro Attestation (@context, type). Dafür bekommst du Interop mit dem gesamten VC-Ökosystem.

## Die Struktur

```
01-wot-core/         ← Das gemeinsame Fundament (001-004)
02-wot-sync/         ← Sync-Infrastruktur (005-009)
03-rls-extensions/   ← Unsere Extensions (Badges)
04-hmc-extensions/   ← Deine Extensions (Trust-Scores, Transactions, Gossip)
research/            ← Forschung, Test-Vektoren, Interop-Analyse
```

## Was beide Systeme davon hätten

**Deine App** könnte unsere qualitativen Attestations anzeigen — "Bob kann gut programmieren", "Bob ist zuverlässig" neben deinem Trust-Level 85%.

**Unsere App** könnte deine Trust-Scores anzeigen — "Alice vertraut Bob zu 85%" neben unseren Pfad-Anzeigen.

**Beide Apps** wären DIDComm-kompatibel — andere dezentrale Projekte könnten mit uns interagieren ohne unser internes Protokoll zu kennen.

Beides auf demselben Vertrauensgraphen. Qualitativ und quantitativ als verschiedene Facetten derselben Beziehungen.