# Test-Vektoren

Kanonische Test-Vektoren für die Verifikation von Implementierungen. Jede Implementierung MUSS diese Werte reproduzieren können.

**WARNUNG:** Die hier verwendeten Schlüssel sind öffentlich bekannt und dürfen NIEMALS in Produktion verwendet werden.

## 1. Identität (Core 001)

### Eingabe

```
Mnemonic: abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about
BIP39 Passphrase: "" (leer)
```

### BIP39 Seed

```
5eb00bbddcf069084889a8ab9155568165f5c453ccb85e70811aaed6f6da5fc1
9a5ac40b389cd370d086206dec8aa6c43daea6690f20ad3d8d48b2d2ce9e38e4
```

(64 Bytes, PBKDF2-HMAC-SHA512, 2048 Runden, wie in BIP39 definiert)

### Ed25519 Schlüssel

```
HKDF-SHA256(seed, salt="", info="wot/identity/ed25519/v1") → 32 Bytes:

Ed25519 Seed:       f5dfa334475ac58513d0be39daaa1ad4677e65a5a2dc42e695b7fc22881af96c
Ed25519 Public Key: 7fa6ae99f7fc28a61096ad3d62f91a76b5c2b39bab0decfaa16c1611e8944f17
```

### DID

```
Multicodec:  0xed01 + Public Key
Base58btc:   z + base58btc(0xed01 || public_key)
DID:         did:key:z6Mko3ZEjKJWQAM5nDXKoZ9jErvvxbWbYgS8KJXYpC5Hbu8a
```

### X25519 Verschlüsselungsschlüssel

```
HKDF-SHA256(seed, salt="", info="wot/encryption/x25519/v1") → 32 Bytes:

X25519 Seed: 955ae6771ff7a40465800baded885780c88527b2eabcd9ef4683dac041ab1e82
```

## 2. JWS Signatur (Core 002)

### Eingabe

```
Signierer: did:key:z6Mko3ZEjKJWQAM5nDXKoZ9jErvvxbWbYgS8KJXYpC5Hbu8a
           (aus Test-Vektor 1)

Payload (JSON, bereits JCS-konform):
{"claim":"kann gut programmieren","id":"did:key:z6Mko3ZEjKJWQAM5nDXKoZ9jErvvxbWbYgS8KJXYpC5Hbu8a"}
```

### Schritt 1: Base64URL-Kodierung

```
Header:  {"alg":"EdDSA","typ":"JWT"}
         → eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9

Payload: {"claim":"kann gut programmieren","id":"did:key:z6Mko3ZEjKJWQAM5nDXKoZ9jErvvxbWbYgS8KJXYpC5Hbu8a"}
         → eyJjbGFpbSI6Imthbm4gZ3V0IHByb2dyYW1taWVyZW4iLCJpZCI6ImRpZDprZXk6ejZNa28zWkVqS0pXUUFNNW5EWEtvWjlqRXJ2dnhiV2JZZ1M4S0pYWXBDNUhidThhIn0
```

### Schritt 2: Signing Input

```
eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJjbGFpbSI6Imthbm4gZ3V0IHByb2dyYW1taWVyZW4iLCJpZCI6ImRpZDprZXk6ejZNa28zWkVqS0pXUUFNNW5EWEtvWjlqRXJ2dnhiV2JZZ1M4S0pYWXBDNUhidThhIn0
```

### Schritt 3: Ed25519 Signatur

```
Signature (Base64URL):
KIXws6t8QYMlYL1NsRjeEg0FA25v5xMbRbAR9bR0cURPHfO_Mr5ay5nyou6bIasqgc7OR1vJi0HX4s_1jQaUAA
```

### Schritt 4: JWS Compact

```
eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJjbGFpbSI6Imthbm4gZ3V0IHByb2dyYW1taWVyZW4iLCJpZCI6ImRpZDprZXk6ejZNa28zWkVqS0pXUUFNNW5EWEtvWjlqRXJ2dnhiV2JZZ1M4S0pYWXBDNUhidThhIn0.KIXws6t8QYMlYL1NsRjeEg0FA25v5xMbRbAR9bR0cURPHfO_Mr5ay5nyou6bIasqgc7OR1vJi0HX4s_1jQaUAA
```

### Verifikation

```
Public Key: 7fa6ae99f7fc28a61096ad3d62f91a76b5c2b39bab0decfaa16c1611e8944f17
Signing Input: Header.Payload (UTF-8 Bytes)
Ed25519-Verify(public_key, signing_input, signature) → true
```

## 3. AES-256-GCM Verschlüsselung (Sync 005)

### Eingabe

```
Space Key (32 Bytes, hex): 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
Nonce (12 Bytes, hex):     000102030405060708090a0b
Plaintext:                 Hello WoT!
```

### Verschlüsselung

```
Ciphertext + Auth Tag (hex): c961f67169c77567ceea5041fd4405f852bc87940a0b52eeee41
```

### Vollständiger Blob (wie im Log-Eintrag)

```
Format: [12-Byte Nonce | Ciphertext | 16-Byte Auth Tag]

Full Blob (Base64URL): AAECAwQFBgcICQoLyWH2cWnHdWfO6lBB_UQF-FK8h5QKC1Lu7kE
```

## 4. JCS Kanonisierung (Core 002)

Test-Vektoren für das JSON Canonicalization Scheme (RFC 8785). Verschiedene Implementierungen MÜSSEN für dieselben Eingaben **bytengenau dieselbe** Ausgabe erzeugen.

### Alphabetische Schlüssel-Sortierung

```
Input:  {"b":1,"a":2,"c":3}
JCS:    {"a":2,"b":1,"c":3}
SHA256: e145110e712e3ed0a6b233551b27a90aa39b4c93ed67e111ba2002d16e5ed1fa
```

### Verschachtelte Objekte

```
Input:  {"z":{"y":1,"x":2},"a":[3,2,1]}
JCS:    {"a":[3,2,1],"z":{"x":2,"y":1}}
SHA256: 00284ff64ddee4ecd1b3c76fde9524200571a90c53d8c79e5e36e08d8d1d7d1c
```

### Zahlen-Formate

Verschiedene Notationen derselben Zahl MÜSSEN gleich kanonisiert werden:

```
Input 1: {"v":0.1}
Input 2: {"v":1e-1}
JCS:     {"v":0.1}
SHA256:  8ec9c466832e74cab1700269790aa649b06fb67989ecf3ac8e6e3c2e5cde2b3a
```

### Negative Null

```
Input:  {"v":-0}
JCS:    {"v":0}
SHA256: ec4f95abcb4e2e3dbe856c3eb2f81995eacb3823d40aa2e78ed4c5e1798f664d
```

### Unicode-Zeichen

**Euro-Zeichen:**
```
Input:  {"name":"€"}
JCS:    {"name":"€"}
SHA256: 080466493ecc711eb2010d0339912c06fcc8d7921c380aecbfb4f0b86ed18b69
```

**Japanische Zeichen:**
```
Input:  {"name":"日本語"}
JCS:    {"name":"日本語"}
SHA256: 31f61054724d90cfd30b479851489719b1daf462c1c02f28a8b50e43953f4b84
```

**Emoji (4-Byte UTF-8):**
```
Input:  {"name":"🌍"}
JCS:    {"name":"🌍"}
SHA256: 892d583d6c33ee9a5ad78d08d94ae6eb1fe891e5a1c52a42ef767eccdd49fc73
```

### Leere Strings und Null

Wichtig: `""` und `null` sind **nicht** dasselbe:

```
Input:  {"a":"","b":null}
JCS:    {"a":"","b":null}
SHA256: 36a91cfc7b71bc03983cb4471d47a93867526932f442aeb9adb2bdf30aaa16d9
```

### Escape-Zeichen

```
Input:  {"text":"Line1\nLine2\t\"quoted\""}
JCS:    {"text":"Line1\nLine2\t\"quoted\""}
SHA256: bd5313afb08357ff10941a4211a3e204932ff716c052473b5caa4a87abddb2b0
```

### Leere Container

```
Input:  {}
JCS:    {}
SHA256: 44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a
```

```
Input:  []
JCS:    []
SHA256: 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945
```

### Gemischtes Array

```
Input:  [1,"two",null,true,false]
JCS:    [1,"two",null,true,false]
SHA256: 5681027102942962c899dacb19ef598c03ae25d8a2094ce98ed0d61d22c5b547
```

### Warum diese Tests nötig sind

JCS-Implementierungen können subtil divergieren — besonders bei Unicode-Normalisierung, Zahlen-Formaten und Escape-Zeichen. Ein einziger Byte-Unterschied in der Kanonisierung führt zu ungültigen Signaturen zwischen verschiedenen Implementierungen.

Eine konforme Implementierung MUSS alle obigen SHA-256 Hashes reproduzieren. Wenn auch nur einer abweicht, sind Signaturen nicht interoperabel.

## Verwendung

Eine konforme Implementierung MUSS:

1. Aus dem Mnemonic "abandon...about" dieselbe DID erzeugen
2. Den JWS-Testvektor verifizieren können (Signatur über den Signing Input mit dem Public Key)
3. Den AES-256-GCM Ciphertext mit dem gegebenen Key und Nonce entschlüsseln können
4. Für alle JCS-Test-Vektoren dieselben SHA-256 Hashes erzeugen

Wenn alle vier Tests bestehen, ist die kryptographische Basis interoperabel.

## Noch fehlende Test-Vektoren

Folgende Vektoren werden ergänzt sobald die Implementierung auf dem neuen Sync-Stack steht:

- **ECIES** — X25519 ECDH + HKDF + AES-256-GCM (Peer-to-Peer-Verschlüsselung)
- **Space Content Key** — Deterministische Nonce aus (deviceId, seq), Verschlüsselung/Entschlüsselung
- **Space Capability** — JWS-Signatur mit spaceCapabilitySigningKey, Broker-Verifikation
- **DID-Dokument** — resolve() für did:key → DID-Dokument-Generierung
- **Admin Key Ableitung** — HKDF mit Space-ID im Info-String
- **SD-JWT VC** (HMC) — Trust-List-Signatur, Disclosure-Hashes, Selective Disclosure
