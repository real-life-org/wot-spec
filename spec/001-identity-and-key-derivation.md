# WoT Spec 001: Identity and Key Derivation

- **Status:** Draft
- **Authors:** Anton Tranelis, Sebastian Galek
- **Date:** 2026-04-11

## Abstract

This document specifies how a Web of Trust identity is derived from a BIP39 mnemonic seed. The goal is a deterministic path from mnemonic to DID, so that different implementations produce the same identity from the same seed.

## Layers

The derivation is structured in layers. Layers 0-3 are the mandatory core. Layer 4+ are optional extensions that implementations may use.

### L0: Entropy

- **Standard:** BIP39
- **Entropy:** 128 bit minimum (12 words)
- **Wordlist:** Implementation-defined. The wordlist does not affect the derived identity as long as it is a valid BIP39 wordlist. Implementations SHOULD support the English BIP39 wordlist for interoperability.

### L1: Seed

- **Standard:** BIP39 seed derivation (PBKDF2-HMAC-SHA512, 2048 rounds, as defined in BIP39)
- **Passphrase:** Optional. Default: empty string `""`
- **Output:** 64 bytes

> **Note:** The BIP39 passphrase is part of the seed derivation and changes the resulting identity. Implementations MUST document whether they use a passphrase.

### L2: Key Derivation

From the BIP39 seed, the identity signing key is derived.

- **Step 1 (optional): Key Stretching** — Implementations MAY apply additional key stretching (e.g. PBKDF2) for brute-force protection. If used, the parameters (algorithm, salt, rounds) MUST be specified.
- **Step 2: Application Key Derivation** — HKDF-SHA256 with:
  - **Input Key Material:** BIP39 seed (or stretched key if Step 1 is used)
  - **Salt:** empty (no salt)
  - **Info:** `"wot/identity/ed25519/v1"` (canonical, all implementations MUST use this string)
  - **Output:** 32 bytes (Ed25519 seed)

The info string is standardized so that the same mnemonic produces the same DID across all implementations. This enables a single identity and trust graph across multiple applications (e.g. WoT attestations and financial vouchers).

### L3: Identity

- **Signing Algorithm:** Ed25519
- **Input:** 32-byte seed from L2
- **DID Method:** `did:key` with Multicodec prefix `0xed01` (Ed25519 public key), Base58-BTC encoded

Example: `did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK`

### L4: Extensions (optional)

Extensions build on top of L0-L3 and are implementation-specific:

- **Device Prefixes** — Used by Human Money Core for double-spend prevention. A device-specific prefix is prepended to identifiers to distinguish transactions from different devices.
- **User-Readable IDs** — Format: `prefix-checksum@did:key:z...` with SHA3-256 checksum for human-readable identifiers.
- **Encryption Key Derivation** — X25519 key derived from Ed25519 for asymmetric encryption (ECDH + HKDF + AES-256-GCM).

## Current Implementations

| | WoT Core (TypeScript) | Human Money Core (Rust) |
|---|---|---|
| **L0: Wordlist** | German (custom) | English (BIP39 standard) |
| **L0: Entropy** | 128 bit (12 words) | Configurable (12-24 words) |
| **L1: Passphrase** | `""` (empty) | Optional, default `""` |
| **L1: Seed slice** | First 32 bytes | Full 64 bytes |
| **L2: Stretching** | None | PBKDF2-HMAC-SHA512, 100k rounds, salt `"human-money-core"` |
| **L2: HKDF info** | `"wot-identity-v1"` | `"human-money-core/ed25519"` |
| **L3: Ed25519** | `@noble/ed25519` | `ed25519_dalek` |
| **L3: DID** | `did:key:z` + `0xed01` + Base58 | `did:key:z` + `0xed01` + Base58 |

### Compatibility

With the current implementations, **the same mnemonic does NOT produce the same DID** due to differences in L1 (seed slice) and L2 (stretching, HKDF info string).

## Identity Migration (Key Rotation)

If the standard derivation path changes, existing identities must not be invalidated. The protocol defines a migration mechanism based on key rotation:

**Migration Message:**

The holder of an old identity signs a statement with the old key:

```
{
  type: "identity-migration",
  oldDid: "did:key:z6Mk...(old)",
  newDid: "did:key:z6Mk...(new)",
  timestamp: "ISO 8601",
  proof: {
    type: "Ed25519Signature2020",
    verificationMethod: "did:key:z6Mk...(old)#key-1",
    proofValue: "..."
  }
}
```

**Properties:**

- The old key signs the migration, proving ownership of both identities
- Existing attestations remain valid — verifiers follow the migration chain
- The migration message is propagated through the trust graph (relay, gossip)
- This is a general-purpose key rotation mechanism — migration is the first use case, but it also handles key compromise, device loss, and algorithm upgrades

**Trust Continuity:**

When a verifier encounters an attestation pointing to an old DID:
1. Check if a migration message exists for that DID
2. If yes, follow the chain to the current DID
3. The attestation is considered valid for the current identity

> **Note:** This mechanism is critical for the goal of one identity across multiple applications (WoT, Human Money Core, etc.). A standardized derivation path means users only need to migrate once.

## Open Questions

1. ~~**Standardized HKDF info string:**~~ **Decided:** `"wot/identity/ed25519/v1"` — all implementations MUST use this string.
2. **Seed slice:** Should the spec mandate using all 64 bytes or the first 32 bytes of the BIP39 seed?
3. **Key stretching:** Should additional stretching be part of the standard path, or an optional extension? Arguments for: brute-force protection for financial use cases. Arguments against: performance cost, not needed for non-financial identities.
4. **Migration chain length:** Should there be a limit on how many times an identity can migrate? Long chains increase verification cost.
5. **Migration revocation:** Can a migration be revoked (e.g., if the new key is compromised before propagation)?
6. **W3C alignment:** Should this spec reference existing W3C specs (DID Core, Verifiable Credentials) or remain independent?
