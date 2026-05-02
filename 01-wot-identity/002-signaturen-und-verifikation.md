# WoT Identity 002: Signaturen und Verifikation

- **Status:** Entwurf
- **Autoren:** Anton Tranelis, Sebastian Galek
- **Datum:** 2026-04-13
- **Scope:** Signaturformate, JWS/JCS-Verifikation und Algorithmus-Validierung
- **Depends on:** Identity 001, Identity 003, JWS, JCS, Ed25519
- **Conformance profile:** `wot-identity@0.1`

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

- DID-gebundene Signaturen MUESSEN ueber `kid`, `resolve(did)` und das DID-Dokument verifizierbar sein; nicht-DID-gebundene Signaturen MUESSEN ihren kontextspezifischen Key-Resolver normativ angeben.
- Das Signaturformat MUSS deterministische Verifikation unterstützen (gleiche Eingabe → gleiches Ergebnis)
- Die Kanonisierungsmethode MUSS eindeutig sein

## Signaturalgorithmus

- **Algorithmus:** Ed25519 (RFC 8032)
- **Schlüssel:** Abgeleitet wie in [Identity 001](001-identitaet-und-schluesselableitung.md) spezifiziert
- **Signaturgröße:** 64 Bytes

## Signaturformat: JWS Compact Serialization (RFC 7515)

WoT Identity verwendet JWS (JSON Web Signature) als Signaturformat. JWS ist ein W3C-/IETF-Standard und wird auch von Verifiable Credentials verwendet.

```
BASE64URL(header) . BASE64URL(payload) . BASE64URL(signature)
```

**Header:**

```json
{ "alg": "EdDSA", "typ": "<kontextspezifisch>", "kid": "<Key-Identifier>" }
```

`kid` (Key Identifier) ist **PFLICHT** in jedem WoT-JWS. Es identifiziert welcher konkrete Key die Signatur erzeugt hat. Für DID-gebundene Signaturen ist `kid` eine DID-URL mit Fragment (z.B. `did:key:z6Mk...#sig-0`). Der Verifier nutzt `kid` um über `resolve()` ([Identity 003](003-did-resolution.md)) den richtigen Public Key zu finden. In Phase 1 ist das Fragment immer `#sig-0` (einziger Key). In Phase 2 (Per-Device-Keys) zeigt es auf den spezifischen Device-Key.

Für nicht-DID-gebundene Signaturen DARF `kid` ein kontextspezifischer Key-Identifier sein. Beispiel: Space-Capabilities werden mit dem `spaceCapabilitySigningKey` signiert; ihr `kid` ist `wot:space:<spaceId>#cap-<generation>` und wird gegen den beim Broker registrierten Space Capability Verification Key geprüft, nicht über DID-Resolution.

Das `typ`-Feld identifiziert den Inhalt des JWS. Kontextspezifische Werte:

| JWS-Verwendung | `typ` | Begründung |
|---|---|---|
| Attestation (VC 2.0) | `"vc+jwt"` | W3C VC-JOSE-COSE Standard. Payload enthält JWT Claims (`iss`, `sub`, `nbf`) neben VC-Feldern. |
| SD-JWT VC (Trust-Lists) | `"vc+sd-jwt"` | IETF SD-JWT VC Draft |
| DeviceKeyBinding | `"wot-device-key-binding+jwt"` | Geplante Phase-2-Delegation eines Device Keys durch den Identity Key |
| Capability | `"wot-capability+jwt"` | WoT-spezifisch |
| WoT Envelope-JWS | `"wot-envelope+jwt"` | WoT-spezifischer signierter Envelope, strukturell an DIDComm angelehnt |
| Log-Eintrag, interne Nachricht | `typ` kann weggelassen werden | Protokoll-intern |

**Attestations verwenden `vc+jwt`** und enthalten sowohl W3C VC 2.0 Felder als auch JWT Registered Claims (siehe [Trust 001](../02-wot-trust/001-attestations.md)). Die JWT Claims sind redundant zu den VC-Feldern, stellen aber sicher dass Standard-JWT-Bibliotheken und externe VC-Verifier die Attestations korrekt parsen können.

Empfänger prüfen das `typ`-Feld optional für Plausibilität. Die Sicherheit hängt nicht vom `typ` ab — die Algorithmus-Whitelist (siehe unten) ist die normative Verteidigung.

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
- SD-JWT (Selective Disclosure) baut auf JWS auf und bleibt damit als Extension anschlussfähig

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
2. Das `kid` aus dem JWS-Header
3. Den zum `typ` passenden Key-Resolver (DID-Resolution für DID-gebundene Signaturen, Space-Key-Registry für Space-Capabilities)

**Ablauf:**

1. JWS in drei Segmente splitten: `headerB64.payloadB64.signatureB64`
2. Header dekodieren und `alg`-Feld prüfen — siehe Algorithmus-Validierung unten
3. Public Key über `kid` auflösen: DID-URL → `resolve(did)` → `verificationMethod`; Space-Capability → registrierter Space Capability Verification Key
4. Signing Input: **exakt die empfangenen Bytes** `headerB64 + "." + payloadB64` — keine Re-Serialisierung, keine Re-Kanonisierung
5. Signatur aus Base64URL dekodieren
6. Ed25519-Signatur gegen Signing Input und Public Key verifizieren

**Wichtig:** Der Verifier darf den Payload NICHT neu kanonisieren oder neu serialisieren. Kanonisierung (JCS) findet ausschließlich auf Sender-Seite statt, **bevor** Base64URL-Kodierung. Auf Empfängerseite werden die empfangenen Bytes 1:1 verifiziert. Re-Kanonisierung bei der Verifikation würde abweichende Bytes erzeugen und gültige Signaturen fälschlich ablehnen.

Kein vertrauenswuerdiger externer Key-Server oder eine Zertifikatskette ist noetig. DID-gebundene Signaturen werden ueber DID-Dokumente verifiziert; kontextspezifische Signaturen wie Space-Capabilities werden ueber den im jeweiligen Protokolldokument definierten Kontext-Resolver verifiziert.

### kid-Konsistenz (MUSS)

Der Verifier MUSS prüfen, dass `kid` mit dem Signierer- oder Kontext-Identifier im Payload konsistent ist. Konkret:

- Bei direkten Attestation-Signaturen in `wot-trust@0.1`: Die DID im `kid` MUSS zur DID in `iss` / `issuer` passen. Delegierte Device-Key-Signaturen folgen den Regeln aus [Identity 004](004-device-key-delegation.md).
- Bei Log-Einträgen: `kid` MUSS dem `authorKid` entsprechen.
- Bei Space-Capabilities: `kid` MUSS `spaceId` und `generation` referenzieren (Format: `wot:space:<spaceId>#cap-<generation>`)

"Passen" bedeutet bei direkten DID-gebundenen Signaturen: die DID im `kid` (ohne Fragment) MUSS identisch sein mit der DID im Payload. Bei Space-Capabilities MUSS der Space-Kontext im `kid` mit dem Payload uebereinstimmen. Bei delegierten Signaturen MUSS der Delegation Proof die Beziehung zwischen Device Key und Identity DID herstellen. Andernfalls MUSS der Verifier den JWS ablehnen — ein Mismatch deutet auf Manipulation hin.

### Algorithmus-Validierung (MUSS)

Verifier MÜSSEN das `alg`-Feld im JWS-Header prüfen **bevor** die Signatur verifiziert wird. Nur `"EdDSA"` ist akzeptiert. Jede andere Angabe MUSS zur sofortigen Ablehnung führen — insbesondere:

- `"none"` (keine Signatur) — ABLEHNEN
- `"HS256"`, `"HS384"`, `"HS512"` (HMAC) — ABLEHNEN
- `"RS256"`, `"RS384"`, `"RS512"` (RSA) — ABLEHNEN
- `"ES256"`, `"ES384"`, `"ES512"` (ECDSA) — ABLEHNEN
- Beliebige andere Werte — ABLEHNEN

**Warum diese Strenge:** Eine klassische JWS-Sicherheitslücke ist die Algorithmus-Konfusion. Wenn ein Verifier `alg=HS256` akzeptiert, könnte ein Angreifer den Public Key (der öffentlich aus der DID verfügbar ist) als HMAC-Secret nutzen und beliebige Nachrichten "signieren". Die Validierung gegen eine Whitelist ist die einzige Verteidigung.

**Erweiterbarkeit:** Zukünftige Signaturtypen (z.B. BBS für Zero-Knowledge-Beweise) werden als Extension spezifiziert und erweitern die Algorithmus-Whitelist. Die Architektur ist darauf vorbereitet — das DID-Dokument ([Identity 003](003-did-resolution.md)) kann mehrere `verificationMethod`-Einträge mit verschiedenen Key-Typen enthalten. Der Verifier prüft dann: ist der `alg` im JWS-Header in meiner Whitelist, und hat die aufgelöste DID einen passenden Key? Die Whitelist wird pro Implementierung konfiguriert — eine App die nur Ed25519 unterstützt, akzeptiert nur `"EdDSA"`. Eine App die BBS+ unterstützt, akzeptiert auch `"BBS"`.

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

Vollständige, verifizierbare Test-Vektoren mit konkreten Krypto-Werten finden sich in den [Test-Vektoren](../test-vectors/). Diese enthalten:

1. **Identität:** Mnemonic → BIP39 Seed → HKDF → Ed25519 Key → did:key (mit exakten Hex-Werten für jeden Schritt)
2. **JWS-Signatur:** Payload → JCS → Base64URL → Signing Input → Ed25519-Signatur → JWS Compact (mit verifizierbarer Signatur)
3. **AES-256-GCM:** Plaintext → Verschlüsselung → Ciphertext + Auth Tag → Blob-Format

Eine konforme Implementierung MUSS alle drei Test-Vektoren reproduzieren können.

**Wichtig:** Ed25519 signiert direkt die Bytes des Signing Input — kein SHA-256 Hash dazwischen. Ed25519 hasht intern mit SHA-512. SHA-256 wird nur für andere Zwecke im Protokoll verwendet (z.B. Content-Adressierung), nicht für die JWS-Signatur selbst.

Das Message Envelope Format wird in [Sync 003](../03-wot-sync/003-transport-und-broker.md) spezifiziert.
