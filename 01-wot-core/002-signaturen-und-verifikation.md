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

1. JWS-Header dekodieren und `alg`-Feld prüfen — siehe Algorithmus-Validierung unten
2. Ed25519 Public Key aus der DID extrahieren: `did:key:z...` → Multibase dekodieren → Multicodec-Präfix `0xed01` entfernen → 32 Bytes Public Key
3. Signing Input rekonstruieren: JWS Header + `.` + JWS Payload (kanonisiert mit JCS)
4. Ed25519-Signatur gegen Signing Input und Public Key verifizieren

Kein externer Key-Server oder Zertifikatskette nötig — die DID selbst enthält den Public Key.

### Algorithmus-Validierung (MUSS)

Verifier MÜSSEN das `alg`-Feld im JWS-Header prüfen **bevor** die Signatur verifiziert wird. Nur `"EdDSA"` ist akzeptiert. Jede andere Angabe MUSS zur sofortigen Ablehnung führen — insbesondere:

- `"none"` (keine Signatur) — ABLEHNEN
- `"HS256"`, `"HS384"`, `"HS512"` (HMAC) — ABLEHNEN
- `"RS256"`, `"RS384"`, `"RS512"` (RSA) — ABLEHNEN
- `"ES256"`, `"ES384"`, `"ES512"` (ECDSA) — ABLEHNEN
- Beliebige andere Werte — ABLEHNEN

**Warum diese Strenge:** Eine klassische JWS-Sicherheitslücke ist die Algorithmus-Konfusion. Wenn ein Verifier `alg=HS256` akzeptiert, könnte ein Angreifer den Public Key (der öffentlich aus der DID verfügbar ist) als HMAC-Secret nutzen und beliebige Nachrichten "signieren". Die Validierung gegen eine Whitelist ist die einzige Verteidigung.

```typescript
function verifyJws(jws: string, did: string): boolean {
  const [headerB64, ...] = jws.split('.')
  const header = JSON.parse(base64urlDecode(headerB64))

  // MUSS: Algorithmus-Whitelist
  if (header.alg !== 'EdDSA') {
    throw new Error(`Rejected algorithm: ${header.alg}`)
  }

  // ... weitere Verifikation
}
```

## Testvektor

Vollständige, verifizierbare Test-Vektoren mit konkreten Krypto-Werten finden sich in den [Test-Vektoren](../research/test-vektoren.md). Diese enthalten:

1. **Identität:** Mnemonic → BIP39 Seed → HKDF → Ed25519 Key → did:key (mit exakten Hex-Werten für jeden Schritt)
2. **JWS-Signatur:** Payload → JCS → Base64URL → Signing Input → Ed25519-Signatur → JWS Compact (mit verifizierbarer Signatur)
3. **AES-256-GCM:** Plaintext → Verschlüsselung → Ciphertext + Auth Tag → Blob-Format

Eine konforme Implementierung MUSS alle drei Test-Vektoren reproduzieren können.

**Wichtig:** Ed25519 signiert direkt die Bytes des Signing Input — kein SHA-256 Hash dazwischen. Ed25519 hasht intern mit SHA-512. SHA-256 wird nur für andere Zwecke im Protokoll verwendet (z.B. Content-Adressierung), nicht für die JWS-Signatur selbst.

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
