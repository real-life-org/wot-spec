# Rust/HMC Conformance Checklist

This checklist defines the first external implementation target for `v0.2.0-interop`: a Rust/HMC harness that reads the same `wot-spec` test vectors as the TypeScript spec-core.

The goal is not to port the TypeScript implementation. The goal is an independent Rust implementation that reproduces the vectors from the specification.

## Target Repository

Expected Rust crate:

```txt
human_money_core
```

In the local workspace this currently exists as:

```txt
../decentral-voucher-system-core
```

## Runner Contract

The Rust conformance harness SHOULD read vectors directly from `wot-spec`.

Recommended command:

```bash
WOT_SPEC_DIR=/path/to/wot-spec cargo test --test wot_conformance -- --ignored
```

If `WOT_SPEC_DIR` is not set, a local harness MAY fall back to a sibling checkout:

```txt
../wot-spec
```

The test MUST fail if required vector files are missing. Silent success without vectors is not conformance.

## Stage 0: Identity And JCS

Vector file:

```txt
test-vectors/phase-1-interop.json
```

Sections:

- `identity`
- `did_resolution`

Assertions:

- BIP39 mnemonic with empty passphrase derives `identity.bip39_seed_hex`.
- HKDF-SHA256 with `wot/identity/ed25519/v1` derives `identity.ed25519_seed_hex`.
- Ed25519 public key from that seed equals `identity.ed25519_public_hex`.
- Ed25519 public key encodes to `identity.did` and `identity.kid` using did:key/multicodec/base58btc.
- HKDF-SHA256 with `wot/encryption/x25519/v1` derives `identity.x25519_seed_hex`.
- X25519 public key equals `identity.x25519_public_hex`, `identity.x25519_public_b64`, and `identity.x25519_public_multibase`.
- DID document JCS SHA-256 equals `did_resolution.jcs_sha256`.

## Stage 1: Trust/JWS

Vector file:

```txt
test-vectors/phase-1-interop.json
```

Sections:

- `attestation_vc_jws`

Assertions:

- Header and payload decode exactly to the vector JSON.
- JCS SHA-256 of payload equals `payload_jcs_sha256`.
- Signing input equals `signing_input`.
- Signature Base64URL equals `signature_b64`.
- JWS verifies with the Ed25519 public key from `header.kid`.
- `issuer`, `iss`, `credentialSubject.id`, and `sub` are consistent.

## Stage 2: HMC Trust List Vector

Vector file:

```txt
test-vectors/phase-1-interop.json
```

Sections:

- `sd_jwt_vc_trust_list`

Assertions:

- Disclosure JCS encoding matches the disclosure embedded in `sd_jwt_compact`.
- SHA-256 disclosure digest equals `disclosure_digest`.
- Issuer-signed JWT verifies with the Ed25519 public key from its `kid`.
- `_sd_alg` is `sha-256`.
- `iss` is a DID that resolves to the verification key.
- The compact form reconstructs as `<issuer_signed_jwt>~<disclosure>~`.

This is vector-level SD-JWT VC coverage, not a full SD-JWT VC implementation.

## Stage 3: Sync Crypto For Interop

Vector file:

```txt
test-vectors/phase-1-interop.json
```

Sections:

- `ecies`
- `log_payload_encryption`
- `log_entry_jws`
- `space_capability_jws`
- `admin_key_derivation`
- `personal_doc`

Assertions:

- ECIES X25519 shared secret and HKDF AES key match the vector.
- AES-GCM ciphertext/tag and blob encoding match the vector.
- Log-entry JWS verifies and its payload matches exactly.
- Space-capability JWS verifies with `verification_key_multibase` and rejects mismatched audience/space/generation/expiry.
- Space admin key derivation matches HKDF info, Ed25519 seed/public key, and DID.
- Personal Doc key and deterministic document ID match the vector.

Stage 3 can be implemented after Stage 0-2. HMC does not need to implement a broker or CRDT to pass these cryptographic vectors.

## Stage 4: Device Delegation

Vector file:

```txt
test-vectors/device-delegation.json
```

Sections:

- `device_key_binding_jws`
- `delegated_attestation_bundle`
- `invalid_cases`

Assertions:

- DeviceKeyBinding-JWS verifies with the identity key.
- Binding payload JCS SHA-256 equals `payload_jcs_sha256`.
- Delegated attestation bundle verifies offline with only the included JWS objects and did:key public keys.
- `issuer` / `iss` stay bound to the identity DID.
- JWS header `kid` for the attestation is the device key.
- Binding `deviceKid`, `sub`, and `devicePublicKeyMultibase` all refer to the same device key.
- Required capability is present.
- Binding validity window covers the attestation `iat`.
- All `invalid_cases` are rejected.

## External Boundary

`didcomm_plaintext_envelope` remains a transport-envelope compatibility check in `wot-spec` using DIDComm libraries. It is not required inside the Rust/HMC core crate.

## Pass Criteria For `v0.2.0-interop`

Minimum Rust/HMC pass set:

- Stage 0
- Stage 1
- Stage 2

Recommended pass set:

- Stage 0
- Stage 1
- Stage 2
- the JWS-only parts of Stage 3

`v0.4.0-device-delegation` requires Stage 4 in both TypeScript and Rust/HMC.

## Local Proof Status

As of 2026-04-27, the local workspace crate `../decentral-voucher-system-core` contains an ignored integration test:

```txt
tests/wot_conformance.rs
```

The explicit command passes against this checkout:

```bash
WOT_SPEC_DIR=/home/fritz/workspace/workspace/wot-spec cargo test --test wot_conformance -- --ignored
```

Covered by that harness:

- Stage 0: Identity and DID resolution
- Stage 1: Attestation VC-JWS
- Stage 2: HMC SD-JWT VC trust-list vector
- Stage 3: ECIES, log payload encryption, log-entry JWS, space capability JWS, admin key, personal doc
- Stage 4: DeviceKeyBinding, delegated attestation bundle, invalid cases

The test is intentionally ignored by default so the HMC crate does not require a sibling `wot-spec` checkout during normal CI. It MUST be run explicitly for conformance checks.
