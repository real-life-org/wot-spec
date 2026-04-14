# Briefing für Sebastian

*Stand: 13. April 2026*

Lieber Sebastian,

wir haben in den letzten Tagen intensiv an der WoT-Spezifikation gearbeitet. Hier ist eine Zusammenfassung — als Grundlage für unser nächstes Gespräch.

## Was wir gemacht haben

Wir haben das Web of Trust Protokoll in klare Schichten aufgeteilt und spezifiziert. Die Spec liegt auf Codeberg: `codeberg.org/web-of-trust/spec`

### WoT Core (3 Dokumente — das gemeinsame Fundament)

| # | Thema | Status |
|---|-------|--------|
| 001 | Identität und Schlüsselableitung (BIP39 → Ed25519 → did:key) | Entwurf, offene Fragen für dich |
| 002 | Signaturen und Verifikation (JWS, JCS, SHA-256) | Entwurf |
| 003 | Attestations (W3C Verifiable Credentials) | Entwurf |

### WoT Sync Layer (4 Dokumente — unsere Infrastruktur)

Verschlüsselung, Sync-Protokoll, Transport/Broker, Discovery. Das ist unser Sync-System — du brauchst das nicht zu übernehmen, aber du könntest es nutzen.

### Extensions

Deine ADRs sind als Extensions abgebildet:
- **H01 Trust-Scores** — dein quantitatives Vertrauensmodell (30/60/85%, Hop-Limits, Propagation)
- **H02 Transactions** — Gutscheine, Double-Spend, SecureContainer

## Der Kern-Vorschlag: W3C Verifiable Credentials als gemeinsames Format

Wir schlagen vor, Attestations als **W3C Verifiable Credentials** zu formatieren. Das hätte für beide Seiten Vorteile:

**Deine Trust List als VC:**

```json
{
  "@context": ["https://www.w3.org/2018/credentials/v1", "https://wot.example/vocab/v1"],
  "type": ["VerifiableCredential", "WotAttestation"],
  "issuer": "did:key:z6Mk...alice",
  "credentialSubject": {
    "id": "did:key:z6Mk...bob",
    "claim": "Vertrauensstufe 3",
    "trustLevel": 3,
    "liability": "4.0h"
  },
  "proof": { "type": "Ed25519Signature2020", ... }
}
```

**Unsere Attestation als VC:**

```json
{
  "@context": ["https://www.w3.org/2018/credentials/v1", "https://wot.example/vocab/v1"],
  "type": ["VerifiableCredential", "WotAttestation"],
  "issuer": "did:key:z6Mk...alice",
  "credentialSubject": {
    "id": "did:key:z6Mk...bob",
    "claim": "kann gut programmieren"
  },
  "proof": { "type": "Ed25519Signature2020", ... }
}
```

Selbes Format, verschiedene Claim-Typen. Deine Trust-Levels über deinen eigenen Context (`humanmoney.example/vocab/v1`), unsere Attestations über unseren. Was man nicht kennt, ignoriert man — die Signatur bleibt trotzdem verifizierbar.

SD-JWT (was du für deine Listen nutzt) wird als W3C VC-SD standardisiert — du könntest dein SD-JWT-Format als VC-kompatibel verpacken ohne es grundlegend zu ändern.

## Was beide Systeme davon hätten

**Deine App** könnte unsere qualitativen Attestations anzeigen — "Bob kann gut programmieren", "Bob ist zuverlässig" neben deinem Trust-Level 85%. Das gibt Profilen Tiefe.

**Unsere App** könnte deine Trust-Scores anzeigen — "Alice vertraut Bob zu 85%" neben unseren Pfad-Anzeigen. Das gibt uns quantitative Signale.

Beides auf demselben Vertrauensgraphen. Qualitativ und quantitativ als verschiedene Facetten derselben Beziehungen.

## Wo wir übereinstimmen

- **did:key + Ed25519** — identisch
- **Offline-First** — gleiche Philosophie
- **Asymmetrisches Vertrauen** — gleiche Richtung
- **Nur positive Aussagen** — kein Downvote bei beiden
- **Lokale Berechnung** — kein globaler Konsens

## Offene Fragen für unser Gespräch

### 1. HKDF Info-Strings und Seed-Länge

Wir nutzen verschiedene HKDF Info-Strings (`"wot-identity-v1"` vs. `"human-money-core/ed25519"`) und verschiedene Seed-Längen (32 vs. 64 Bytes). Jede Änderung bedeutet Migration aller DIDs. Frage: lohnt sich die Harmonisierung? Wenn ja, einmal alle Fragen zusammen entscheiden und einmal migrieren.

### 2. Signaturen

Wir schlagen vor: JWS + JCS (RFC 8785) + SHA-256 + Base64URL. Du nutzt: Detached + JCS + SHA3-256 + Base58. JCS haben wir von dir übernommen — das ist der richtige Standard. Bei Hash und Encoding sehen wir SHA-256 und Base64URL als pragmatischer (Web Crypto API nativ). Detached Signatures können als Extension für Multi-Signer Use Cases (Gutscheine) leben.

### 3. VCs als gemeinsames Attestation-Format

Funktioniert das für dich? Dein SD-JWT-Modell bleibt erhalten — es wird nur VC-kompatibel verpackt. Die Frage ist ob der Overhead (~100 Bytes pro Attestation für @context und type) akzeptabel ist.

### 4. Verteilung: Empfänger- vs. Senderprinzip

Unsere Attestations gehören dem Empfänger (Holder = Subject). Deine Trust Lists verteilt der Sender via Gossip. Beides kann koexistieren — verschiedene Verteilungswege für verschiedene Claim-Typen. Geschenke gehen an den Empfänger, Bewertungen verteilt der Sender.

### 5. Deine Device-Prefixes

Wie bilden wir die in der gemeinsamen Spec ab? Wir nutzen Device-UUIDs für unseren Sync. Du nutzt Device-Prefixes für Wallet-Isolation und Double-Spend-Prevention. Beides funktioniert — aber sollen wir einen gemeinsamen Mechanismus definieren?

## Die Struktur der Spec

```
01-wot-core/         ← Das gemeinsame Fundament (001-003)
02-wot-sync/         ← Unsere Sync-Infrastruktur (004-007)
03-rls-extensions/   ← Unsere Extensions (Datenmodell, Gruppen, Badges)
04-hmc-extensions/   ← Deine Extensions (Trust-Scores, Transactions)
research/            ← Forschungsmaterial
```

Dein quantitatives Vertrauensmodell mit Trust-Levels, Hop-Limits, Gossip und Pfadberechnung ist als Extension (H01/H02) abgebildet — nicht weil es weniger wichtig ist, sondern weil es spezifisch für den Human Money Use Case ist. Der Core bleibt schlank: Identität, Signaturen, Attestations.

## Was ich mir wünsche

Dass wir einen gemeinsamen Standard finden für das Fundament (did:key, Ed25519, Attestation-Format) und dass jeder darauf aufbaut was er braucht. Dein quantitatives Modell und unser qualitatives Modell schließen sich nicht aus — sie ergänzen sich. Und wenn beides auf VCs aufbaut, können beide Systeme voneinander profitieren ohne sich gegenseitig einzuschränken.

Wann hast du Zeit für einen Call?
