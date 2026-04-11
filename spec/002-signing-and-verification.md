# WoT Spec 002: Signing and Verification

- **Status:** Draft
- **Authors:** Anton Tranelis, Sebastian Galek
- **Date:** 2026-04-11

## Abstract

This document specifies how data is signed and verified in the Web of Trust protocol. Signing is the foundation for attestations, messages, and all authenticated data exchange.

## Requirements

- All signed data MUST be verifiable using only the signer's DID (no external lookup required)
- The signature format MUST support deterministic verification (same input → same verification result)
- The canonicalization method MUST be unambiguous

## Signing Algorithm

- **Algorithm:** Ed25519 (RFC 8032)
- **Key:** Derived as specified in [Spec 001](001-identity-and-key-derivation.md)
- **Signature Size:** 64 bytes

## Signature Formats

The protocol defines two signature formats for different use cases.

### Format A: JWS Compact Serialization (RFC 7515)

Used for self-contained signed documents (attestations, capabilities).

```
BASE64URL(header).BASE64URL(payload).BASE64URL(signature)
```

**Header (fixed):**
```json
{ "alg": "EdDSA", "typ": "JWT" }
```

**Signing Input:**
```
BASE64URL(header) + "." + BASE64URL(JSON.stringify(payload))
```

**Advantages:** Standard format, widely supported, self-contained.

### Format B: Detached Signature

Used for data where the signature is stored separately from the content (e.g. voucher endorsements, transaction signatures).

**Process:**
1. Create canonical representation of the data to be signed
2. Hash the canonical form (see Canonicalization below)
3. Sign the hash with Ed25519
4. Store signature alongside (but separate from) the data

**Advantages:** Signature doesn't modify the original data, supports multiple signatures on the same document.

## Canonicalization

Deterministic serialization is critical — the same logical data must always produce the same bytes for signing.

### Option 1: Canonical JSON

Sort all object keys lexicographically, remove whitespace. Libraries: `serde_json_canonicalizer` (Rust), JSON Canonicalization Scheme (JCS, RFC 8785).

### Option 2: Pipe-Separated Fields

For fixed-structure messages with known fields:

```
field1|field2|field3|...|fieldN
```

Fields are concatenated in a defined order with `|` as separator.

**Advantages:** Simple, no JSON parsing needed, unambiguous.
**Disadvantages:** Only works for flat, known structures.

## Hashing

When signing a hash (Format B), the hash algorithm is:

- **Algorithm:** SHA-256 (for general use) or SHA3-256 (for ID generation)
- **Output:** 32 bytes

> **Open Question:** Should the protocol standardize on one hash algorithm, or allow both? SHA-256 is more widely supported (Web Crypto API). SHA3-256 provides domain separation.

## Encoding

| Data | Encoding |
|------|----------|
| Signatures in JWS | Base64URL (no padding) |
| Signatures in detached format | Implementation-defined (Base64URL recommended, Base58 acceptable) |
| Public keys in DIDs | Base58btc with multibase prefix `z` |
| Hashes for IDs | Implementation-defined (Base58 or hex) |

> **Open Question:** Should the spec mandate Base64URL everywhere for consistency, or allow Base58 for human-readable contexts?

## Verification

Verification requires:
1. The signed data (or its hash)
2. The signature
3. The signer's DID

**Process:**
1. Extract Ed25519 public key from DID (see [Spec 001](001-identity-and-key-derivation.md), L3)
2. Reconstruct the signing input using the same canonicalization method
3. Verify Ed25519 signature against the signing input and public key

No external key server or certificate chain is needed — the DID itself contains the public key.

## Message Envelope

For authenticated messages between peers, the protocol defines an envelope format:

```
{
  v: 1,                    // Protocol version
  id: string,              // Unique message ID
  type: string,            // Message category
  fromDid: string,         // Sender DID
  toDid: string,           // Recipient DID
  createdAt: string,       // ISO 8601
  payload: string,         // Encoded content
  signature: string        // Ed25519 signature
}
```

**Signing Input (pipe-separated):**
```
v|id|type|fromDid|toDid|createdAt|payload
```

The signature covers all fields except `signature` itself. The recipient verifies by extracting the sender's public key from `fromDid`.

## Current Implementations

| | WoT Core (TypeScript) | Human Money Core (Rust) |
|---|---|---|
| **Document signing** | JWS Compact (Format A) | Detached Signature (Format B) |
| **Message signing** | Pipe-separated envelope | N/A (no message protocol) |
| **Canonicalization** | JSON.stringify (JWS), pipe-separated (envelope) | Canonical JSON (JCS) → SHA3-256 hash |
| **Signature encoding** | Base64URL | Base58 |
| **Hash algorithm** | SHA-256 (Web Crypto) | SHA3-256 |
| **Crypto library** | Web Crypto API + @noble/ed25519 | ed25519_dalek |

## Open Questions

1. **One format or two?** Should the spec mandate JWS for everything, or allow detached signatures? JWS is standard but adds overhead. Detached signatures are lighter but non-standard.
2. **Canonical JSON standard:** Should we mandate JCS (RFC 8785) as the canonical JSON format?
3. **Hash algorithm:** SHA-256 vs SHA3-256 — standardize on one, or define which is used where?
4. **Base64URL vs Base58:** Standardize encoding or leave to implementations?
5. **Envelope format:** Should the message envelope be part of the core spec or an extension?
