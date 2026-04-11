# WoT Spec 003: Encryption

- **Status:** Draft
- **Authors:** Anton Tranelis, Sebastian Galek
- **Date:** 2026-04-11

## Abstract

This document specifies how data is encrypted in the Web of Trust protocol — both for peer-to-peer communication and for group (Space) encryption.

## Encryption Key Derivation

From the master seed (see [Spec 001](001-identity-and-key-derivation.md)):

```
Master Seed
  → HKDF-SHA256(seed, info="wot-identity-v1")    → Ed25519 signing key
  → HKDF-SHA256(seed, info="wot-encryption-v1")   → X25519 encryption key
```

The encryption key is derived on a separate HKDF path from the identity key. Both are deterministic from the same seed.

**Ed25519 → X25519 Conversion:**

Alternatively, implementations MAY derive the X25519 key directly from the Ed25519 key using the standard birational map (Montgomery form). Both approaches produce valid X25519 keys.

## Peer-to-Peer Encryption (ECIES)

For messages between two parties, the protocol uses an ECIES-like scheme:

### Process

**Encryption (sender → recipient):**

1. Generate ephemeral X25519 key pair
2. Perform ECDH: `shared_secret = ephemeral_private × recipient_public`
3. Derive symmetric key via HKDF-SHA256:
   - Input: shared secret (32 bytes)
   - Salt: empty (32 zero bytes)
   - Info: context string (see below)
   - Output: 256-bit symmetric key
4. Encrypt plaintext with authenticated encryption (see Symmetric Encryption below)
5. Output: `{ ephemeral_public_key, nonce, ciphertext }`

**Decryption (recipient):**

1. Perform ECDH: `shared_secret = recipient_private × ephemeral_public`
2. Derive same symmetric key via HKDF (same parameters)
3. Decrypt ciphertext

### HKDF Info String

> **Open Question:** Should this be standardized? Current implementations use different strings (`"wot-ecies-v1"` vs `"secure-container-kek"`).

## Multi-Recipient Encryption

For data that must be readable by multiple recipients (e.g., Space invites, shared vouchers):

### Process

1. Generate a random 32-byte payload key
2. Encrypt the actual data with the payload key (symmetric encryption)
3. For each recipient:
   a. Perform ECDH: `shared_secret = ephemeral_private × recipient_public`
   b. Derive a Key Encryption Key (KEK) via HKDF
   c. Wrap (encrypt) the payload key with the KEK
   d. Store: `{ recipient_id_hash, wrapped_key }`
4. For the sender (self-access):
   a. Perform ECDH: `shared_secret = sender_private × ephemeral_public`
   b. Derive KEK, wrap payload key
   c. Store as sender entry

**Output structure:**
```
{
  ephemeral_public_key,
  wrapped_keys: [
    { matcher: hash(recipient_id), wrapped_key },
    { matcher: hash(recipient_id), wrapped_key },
    { sender: true, wrapped_key }
  ],
  encrypted_payload,
  signature
}
```

**Decryption:**
1. Find own entry in `wrapped_keys` (by matching ID hash)
2. Derive shared secret and KEK
3. Unwrap payload key
4. Decrypt payload

## Group Encryption (Spaces)

For persistent groups with shared encrypted data (CRDT documents):

### Space Key Management

- Each Space has a symmetric key (32 bytes, randomly generated)
- Keys are versioned by **generation** (monotonically increasing integer)
- Old keys are retained for decrypting historical data
- New keys are distributed via peer-to-peer encryption (ECIES) when members are invited

### Key Rotation

When a member is removed:
1. Generate new Space key (generation + 1)
2. Distribute new key to all remaining members via ECIES
3. New data is encrypted with the new key
4. Old data remains readable with old key (by members who had access at that time)

### Encrypt-then-Sync

CRDT changes are encrypted before synchronization:

```
{
  ciphertext,
  nonce,
  space_id,
  generation,     // Which key version was used
  from_did        // Author
}
```

This enables end-to-end encrypted collaboration — the relay server never sees plaintext.

## Symmetric Encryption

The protocol supports two AEAD ciphers:

### AES-256-GCM

- **Key:** 256 bits
- **Nonce:** 96 bits (12 bytes), randomly generated per encryption
- **Tag:** 128 bits (implicit in ciphertext)
- **Available in:** Web Crypto API (browser-native)

### ChaCha20-Poly1305 (RFC 7539)

- **Key:** 256 bits
- **Nonce:** 96 bits (12 bytes), randomly generated per encryption
- **Tag:** 128 bits (implicit in ciphertext)
- **Available in:** Most native crypto libraries (Rust, Go, etc.)

Both provide authenticated encryption. Both are equally secure for this use case.

> **Open Question:** Should the spec mandate one cipher, or allow both with a negotiation mechanism? AES-256-GCM has hardware acceleration in browsers. ChaCha20-Poly1305 is faster in software without AES-NI.

## Encrypted Data Format

```
[12-byte nonce | ciphertext | authentication tag]
```

The nonce is prepended to the ciphertext. The authentication tag is appended (or included in ciphertext, depending on library).

## Storage Encryption (At Rest)

For encrypting local data (seed, keys, wallet):

### Seed Storage

```
passphrase → PBKDF2(passphrase, random_salt, iterations=100000, SHA-256) → AES-GCM key
AES-GCM key → encrypt(seed) → { ciphertext, salt, nonce }
```

### Wallet Storage

Implementations MAY use additional key derivation:

```
passphrase → Argon2id(passphrase, salt) → storage_key
storage_key → encrypt(data) → encrypted_file
```

Argon2id is preferred over PBKDF2 for password-based encryption due to memory-hardness.

## Current Implementations

| | WoT Core (TypeScript) | Human Money Core (Rust) |
|---|---|---|
| **P2P Encryption** | ECIES (X25519 + HKDF + AES-256-GCM) | SecureContainer (X25519 + HKDF + ChaCha20-Poly1305) |
| **Multi-Recipient** | Not built-in | Double-Key-Wrapping (sender + N recipients) |
| **Group Encryption** | Space keys (random, generational) | Not built-in |
| **HKDF info (P2P)** | `"wot-ecies-v1"` | `"secure-container-kek"` |
| **Symmetric cipher** | AES-256-GCM (Web Crypto) | ChaCha20-Poly1305 |
| **Seed encryption** | PBKDF2 + AES-GCM | Argon2id + ChaCha20-Poly1305 |
| **Ed25519 → X25519** | Separate HKDF path (`"wot-encryption-v1"`) | Birational map (Montgomery conversion) |
| **Nonce** | 12 bytes random | 12 bytes random |

## Open Questions

1. **ECIES HKDF info string:** Standardize to one string, or allow per-implementation?
2. **AES-GCM vs ChaCha20-Poly1305:** Mandate one, or define both as acceptable with a preference?
3. **Multi-recipient format:** Should the SecureContainer pattern become part of the spec?
4. **X25519 derivation:** Separate HKDF path or Ed25519 → X25519 conversion? The HKDF path is cleaner (independent keys), the conversion is simpler (one key pair).
5. **Cipher negotiation:** If both ciphers are allowed, how do peers agree on which to use?
6. **Group key distribution:** Should Space key management be part of the core spec or an extension?
