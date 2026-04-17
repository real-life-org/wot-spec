# WoT Spec 002: Signaturen und Verifikation

- **Status:** Entwurf
- **Autoren:** Anton Tranelis, Sebastian Galek
- **Datum:** 2026-04-13

## Zusammenfassung

Dieses Dokument spezifiziert wie Daten im Web of Trust signiert und verifiziert werden. Signaturen sind die Grundlage für Attestations, Nachrichten und jeden authentifizierten Datenaustausch.

## Referenzierte Standards

- **Ed25519** (RFC 8032) — Signaturalgorithmus
- **JWS** (RFC 7515) — JSON Web Signature
- **JCS** (RFC 8785) — JSON Canonicalization Scheme
- **SHA-256** (FIPS 180-4) — Hash-Algorithmus
- **Base64URL** (RFC 4648) — Encoding
- **DID Core** (W3C) — Decentralized Identifiers

## Anforderungen

- Alle signierten Daten MÜSSEN allein mit der DID des Signierers verifizierbar sein (kein externer Lookup nötig)
- Das Signaturformat MUSS deterministische Verifikation unterstützen (gleiche Eingabe → gleiches Ergebnis)
- Die Kanonisierungsmethode MUSS eindeutig sein

## Signaturalgorithmus

- **Algorithmus:** Ed25519 (RFC 8032)
- **Schlüssel:** Abgeleitet wie in [Spec 001](001-identitaet-und-schluesselableitung.md) spezifiziert
- **Signaturgröße:** 64 Bytes

## Signaturformat: JWS Compact Serialization (RFC 7515)

Das Core-Protokoll verwendet JWS (JSON Web Signature) als Signaturformat. JWS ist ein W3C-/IETF-Standard und wird auch von Verifiable Credentials verwendet.

```
BASE64URL(header) . BASE64URL(payload) . BASE64URL(signature)
```

**Header (fest):**

```json
{ "alg": "EdDSA", "typ": "JWT" }
```

**Signing Input:**

```
BASE64URL(header) + "." + BASE64URL(payload_bytes)
```

Der Payload wird als Byte-Folge behandelt — nicht neu serialisiert. Der Sender serialisiert den Payload einmal (mit JCS wenn JSON), kodiert ihn als Base64URL und signiert das Ergebnis. Der Empfänger verifiziert gegen exakt dieselben Base64URL-kodierten Bytes.

**Vorteile:**
- Standardformat (RFC 7515), weit verbreitet
- Selbstbeschreibend — Header enthält den Algorithmus
- W3C-kompatibel (Verifiable Credentials nutzen JWS)
- Empfänger braucht keine Vorab-Kenntnis über das Format
- SD-JWT (Selective Disclosure) baut auf JWS auf — Sebastians Trust Lists sind damit eine natürliche Erweiterung

JWS ist das **einzige Signaturformat** im WoT-Protokoll. Attestations, Message Envelopes und Log-Einträge verwenden alle JWS Compact Serialization. Ein Format, eine Toolchain.

## Kanonisierung

Deterministische Serialisierung ist kritisch — dieselben logischen Daten müssen immer dieselben Bytes erzeugen. Ohne Kanonisierung kann dieselbe JSON-Struktur je nach Implementierung verschiedene Byte-Folgen haben, was die Signaturverifikation brechen würde.

**Standard: JCS — JSON Canonicalization Scheme (RFC 8785)**

- Alle Objekt-Schlüssel lexikographisch sortiert
- Kein Whitespace
- Definierte Zahlenformatierung
- IETF-Standard, implementiert in allen relevanten Sprachen

Bibliotheken:
- **Rust:** `serde_json_canonicalizer`
- **TypeScript:** `canonicalize` (npm) oder eigene Implementierung nach RFC 8785
- **Go:** `github.com/nicktrav/jcs`

## Hashing

- **Algorithmus:** SHA-256 (FIPS 180-4)
- **Ausgabe:** 32 Bytes
- **Verwendung:** Hashing von Daten vor der Signatur (wo nötig), ID-Generierung

SHA-256 ist nativ in der Web Crypto API aller Browser verfügbar und der verbreitetste Hash-Algorithmus. SHA3-256 bietet theoretische Zukunftssicherheit (andere interne Konstruktion), ist aber nicht nativ im Browser verfügbar (frühestens 2027) und bringt keinen praktischen Sicherheitsgewinn gegenüber SHA-256.

## Encoding

**Base64URL (RFC 4648, ohne Padding)** für alles was das Protokoll selbst definiert:
- Signaturen
- Verschlüsselte Daten
- Hashes

**Base58btc** nur wo externe Standards es vorschreiben:
- Public Keys in DIDs (`did:key:z...`) — definiert durch W3C DID Core / Multibase

Ein einheitliches Encoding vereinfacht die Implementierung und eliminiert Konvertierungsfehler.

## Verifikation

Für die Verifikation werden benötigt:

1. Die signierten Daten (oder deren JWS-Repräsentation)
2. Die DID des Signierers

**Ablauf:**

1. Ed25519 Public Key aus der DID extrahieren: `did:key:z...` → Multibase dekodieren → Multicodec-Präfix `0xed01` entfernen → 32 Bytes Public Key
2. Signing Input rekonstruieren: JWS Header + `.` + JWS Payload (kanonisiert mit JCS)
3. Ed25519-Signatur gegen Signing Input und Public Key verifizieren

Kein externer Key-Server oder Zertifikatskette nötig — die DID selbst enthält den Public Key.

## Testvektor

Schritt-für-Schritt-Beispiel mit konkreten Werten.

### Eingabe

**Payload (JSON):**

```json
{"claim":"kann gut programmieren","id":"did:key:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH"}
```

**Signierer-DID:**

```
did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK
```

### Schritt 1: JCS-Kanonisierung

Der Payload wird mit JCS (RFC 8785) kanonisiert. Bei diesem Beispiel sind die Keys bereits alphabetisch sortiert und es gibt kein Whitespace — die JCS-Ausgabe ist identisch mit der Eingabe:

```
{"claim":"kann gut programmieren","id":"did:key:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH"}
```

### Schritt 2: Base64URL-Kodierung

**Header:**

```json
{"alg":"EdDSA","typ":"JWT"}
```

→ Base64URL: `eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9`

**Payload (JCS-Bytes):**

→ Base64URL: `eyJjbGFpbSI6Imthbm4gZ3V0IHByb2dyYW1taWVyZW4iLCJpZCI6ImRpZDprZXk6ejZNa3BUSFI4Vk5zQnhZQUFXSHV0MkdlYWRkOWpTd3VCVjh4Um9BbndXc2R2a3RIIn0`

### Schritt 3: Signing Input

```
eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJjbGFpbSI6Imthbm4gZ3V0IHByb2dyYW1taWVyZW4iLCJpZCI6ImRpZDprZXk6ejZNa3BUSFI4Vk5zQnhZQUFXSHV0MkdlYWRkOWpTd3VCVjh4Um9BbndXc2R2a3RIIn0
```

Header + `.` + Payload, als UTF-8 Bytes.

### Schritt 4: Ed25519-Signatur

Die UTF-8 Bytes des Signing Input werden direkt mit dem Ed25519 Private Key signiert (kein zusätzliches Hashing — Ed25519 hasht intern mit SHA-512).

→ 64 Bytes Signatur → Base64URL kodieren

### Schritt 5: JWS Compact Serialization

```
<Header>.<Payload>.<Signatur>
```

Alle drei Teile Base64URL-kodiert, verbunden mit `.`.

### Verifikation

1. JWS in Header, Payload, Signatur aufteilen (am `.`)
2. `did:key:z6Mk...` → Multibase dekodieren → `0xed01` entfernen → 32 Bytes Ed25519 Public Key
3. Signing Input rekonstruieren: Header + `.` + Payload
4. Ed25519-Verify(public_key, signing_input_bytes, signature) → `true`

**Wichtig:** Ed25519 signiert direkt die Bytes — kein SHA-256 Hash dazwischen. SHA-256 wird nur für andere Zwecke im Protokoll verwendet (z.B. Content-Adressierung), nicht für die JWS-Signatur selbst.

## Aktuelle Implementierungen

| | WoT Core | Human Money Core | Spec |
|---|---|---|---|
| **Signaturformat** | JWS Compact | Detached Signature | ✅ JWS Compact (Detached als Extension) |
| **Kanonisierung** | JSON.stringify | JCS (RFC 8785) | ✅ JCS (RFC 8785) |
| **Hash** | SHA-256 | SHA3-256 | ✅ SHA-256 |
| **Signatur-Encoding** | Base64URL | Base58 | ✅ Base64URL |
| **Crypto-Bibliothek** | Web Crypto + @noble | ed25519_dalek | ✅ Beliebige konforme Impl. |

## Anpassungsbedarf

**WoT Core (TypeScript):**
- Kanonisierung von `JSON.stringify` auf JCS (RFC 8785) umstellen

**Human Money Core (Rust):**
- Hash von SHA3-256 auf SHA-256 umstellen
- Signatur-Encoding von Base58 auf Base64URL umstellen
- JWS als Core-Signaturformat implementieren (Detached bleibt für Payment-Extension)

Diese Änderungen betreffen die Signatur-Formate, nicht die Schlüsselableitung — bestehende DIDs bleiben gültig.

Das Message Envelope Format wird in [Sync 007](../02-wot-sync/007-transport-und-broker.md) spezifiziert.
