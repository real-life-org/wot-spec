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

## Verwendung

Eine konforme Implementierung MUSS:

1. Aus dem Mnemonic "abandon...about" dieselbe DID erzeugen
2. Den JWS-Testvektor verifizieren können (Signatur über den Signing Input mit dem Public Key)
3. Den AES-256-GCM Ciphertext mit dem gegebenen Key und Nonce entschlüsseln können

Wenn alle drei Tests bestehen, ist die kryptographische Basis interoperabel.
