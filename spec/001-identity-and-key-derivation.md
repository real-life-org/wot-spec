# WoT Spec 001: Identity and Key Derivation

- **Status:** Draft
- **Authors:** Anton Tranelis, Sebastian Galek
- **Date:** 2026-04-11

## Abstract

This document specifies how a Web of Trust identity is derived from a BIP39 mnemonic seed. The goal is a deterministic path from mnemonic to DID, so that different implementations produce the same identity from the same seed.

## Derivation Path

```
BIP39 Mnemonic (12+ words, any valid wordlist)
  → BIP39 Seed (PBKDF2-HMAC-SHA512, 2048 rounds) → 64 bytes
  → HKDF-SHA256(seed, info="wot/identity/ed25519/v1") → 32 bytes
  → Ed25519 Key Pair
  → did:key (Multicodec 0xed01 + Base58btc)
```

Same mnemonic → same DID. Across all implementations, languages, and applications.

## Specification

### Entropy (BIP39)

- **Standard:** BIP39
- **Entropy:** 128 bit minimum (12 words)
- **Wordlist:** Implementation-defined. The wordlist does not affect the derived identity as long as it is a valid BIP39 wordlist. Implementations SHOULD support the English BIP39 wordlist for interoperability.

### Seed

- **Standard:** BIP39 seed derivation (PBKDF2-HMAC-SHA512, 2048 rounds, as defined in BIP39)
- **Passphrase:** Optional. Default: empty string `""`
- **Output:** 64 bytes (all bytes are used, no slicing)

> **Note:** The BIP39 passphrase is part of the seed derivation and changes the resulting identity. Implementations MUST document whether they use a passphrase.

### Key Derivation

HKDF-SHA256 with:
- **Input Key Material:** Full 64-byte BIP39 seed
- **Salt:** empty (no salt)
- **Info:** `"wot/identity/ed25519/v1"`
- **Output:** 32 bytes (Ed25519 seed)

No additional key stretching. BIP39 already applies PBKDF2 with 2048 rounds during seed generation, and 128 bit entropy from a proper mnemonic is not bruteforceable. Additional stretching adds performance cost without meaningful security gain.

Implementations that need additional protection for specific use cases (e.g. password-based unlock) SHOULD apply stretching at the storage/unlock layer, not at the identity derivation layer.

### Identity

- **Signing Algorithm:** Ed25519
- **Input:** 32-byte seed from HKDF
- **DID Method:** `did:key` with Multicodec prefix `0xed01` (Ed25519 public key), Base58-BTC encoded

Example: `did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK`

### Extensions (optional)

Extensions build on top of the core derivation and are implementation-specific:

- **Device Prefixes** — For double-spend prevention in financial applications.
- **User-Readable IDs** — Format: `prefix-checksum@did:key:z...` with checksum for human-readable identifiers.
- **Encryption Key Derivation** — X25519 key for asymmetric encryption (see [Spec 003](003-encryption.md)).

## Migration (Key Rotation)

If an implementation needs to change its derivation path to conform to this spec, existing identities are migrated via key rotation. See [Identity Migration](../drafts/004-identity-migration.md) (draft).

## Current Implementations

Both implementations need changes to conform to this spec:

| | WoT Core (TypeScript) | Human Money Core (Rust) | Spec |
|---|---|---|---|
| **Wordlist** | German (custom) | English (standard) | Any valid BIP39 |
| **Entropy** | 128 bit | Configurable | 128 bit minimum |
| **Seed** | First 32 bytes | Full 64 bytes | **Full 64 bytes** |
| **Stretching** | None | PBKDF2 100k rounds | **None** |
| **HKDF info** | `"wot-identity-v1"` | `"human-money-core/ed25519"` | **`"wot/identity/ed25519/v1"`** |
| **Ed25519** | @noble/ed25519 | ed25519_dalek | Any conformant implementation |
| **DID** | did:key + 0xed01 + Base58 | did:key + 0xed01 + Base58 | did:key + 0xed01 + Base58 |

## Open Questions

1. **Migration chain length:** Should there be a limit on how many times an identity can migrate?
2. **W3C alignment:** Should this spec reference existing W3C specs (DID Core, Verifiable Credentials) or remain independent?
