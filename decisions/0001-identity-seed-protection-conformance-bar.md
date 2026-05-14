# ADR 0001: Three-Layer Conformance Bar for Identity 001 Seed Protection

## Status

Accepted — 2026-05-14, decided by Anton Tranelis.

## Context

[Identity 001](../01-wot-identity/001-identitaet-und-schluesselableitung.md) states that the BIP39 seed "MUSS auf dem Gerät angemessen geschützt werden und darf auf keinen Fall im Klartext extrahierbar sein". That phrasing is ambiguous for any environment that has to load seed bytes into process memory to derive Ed25519/X25519 material — most obviously JavaScript/TypeScript runtimes in browsers, where Web Crypto offers `Ed25519` key handles but BIP39/HKDF have to operate on raw seed bytes.

Concretely, the ambiguity has been blocking the TS runtime-port / seed-vault planning lane in the downstream `web-of-trust` repository (see `wot-identity-conformance.md` REQ-ID-011 and `runtime-port-contract-map.md` "Identity create, recover, unlock, delete"). Without a claimable conformance boundary, neither the existing `IdentitySeedVault` adapter nor any planned non-extractable-handle replacement can be evaluated against the spec.

`wot-identity@0.1` needs a conformance bar that is:

- deterministically checkable across implementations;
- realistic for browser/JS runtimes that cannot guarantee plaintext-free RAM;
- aligned with the existing shared-seed threat model, where hostile same-origin code is the primary attacker against a single device.

This decision resolves [wot-spec#45](https://github.com/real-life-org/wot-spec/issues/45).

## Decision

`wot-identity@0.1` seed protection conformance is structured as three layers:

1. **Persistence MUST** — Seed material at rest MUST be encrypted. Acceptable unlock factors include passphrase, biometric, or OS-keychain unlock. Storing the seed unencrypted (plain IndexedDB entry, plain file, plain localStorage, etc.) is non-conformant.

2. **API Surface MUST** — The application/port API exposed to application and workflow code MUST NOT contain any operation that returns raw seed bytes. There MUST be no `getSeed()`, no `export()`, no `loadSeed(): Uint8Array`, and no equivalent. Seed-using operations (sign, derive subkey, decrypt) are exposed instead, and the seed itself remains behind the port boundary.

3. **Runtime MAY + SHOULD** — Implementations MAY hold seed plaintext transiently in process memory during derivation or signing. They SHOULD minimize that lifetime (zero buffers as soon as derivation completes; do not keep long-lived seed copies in workflow state) and SHOULD use non-extractable key handles on platforms that support them (e.g. Web Crypto `Ed25519`/`X25519` `CryptoKey` with `extractable: false`, iOS Keychain / Secure Enclave, Android Keystore). The specific platform facility is non-normative; the SHOULD is on minimizing extractable plaintext lifetime, not on any single vendor mechanism.

## Rationale

- **API Surface MUST is the load-bearing rule.** It is the only layer that is deterministically checkable from outside the implementation: a reviewer can read the port interface and see whether `getSeed()` exists. Persistence-at-rest is also checkable, but the at-rest decision alone does not stop application code from accumulating plaintext seed copies once a vault returns `Uint8Array`.

- **Eliminating all plaintext from process RAM is unrealistic in browsers.** BIP39 seed-to-Ed25519 derivation has to happen on raw bytes; Web Crypto does not provide a "create Ed25519 key from a BIP39-derived seed without exposing the bytes" primitive. A strict "no plaintext seed in memory ever" rule would either rule out browser implementations entirely or force creative-but-fragile workarounds (e.g. WASM heaps that cannot actually defeat same-origin attackers).

- **The threat model is hostile same-origin code on a single device.** Under that model, API-surface MUST eliminates the largest realistic exfiltration class (workflow / UI / debug code accidentally or maliciously calling `getSeed()` and persisting the result). Transient plaintext during the derivation window is a narrower attack window that non-extractable handles further reduce on platforms that support them.

- **Pragmatism for existing implementations.** The bar is reachable for current JS/TS adapters via a focused migration (replace `loadSeed(): Uint8Array` with handle-/derive-style operations) without requiring a platform rewrite. Non-extractable-handle adoption can be claimed incrementally as a declared Runtime-SHOULD posture rather than a binary conformance gate.

## Consequences

- Existing JS/TS seed-vault adapters that return `Uint8Array` to workflows (e.g. `IdentitySeedVault.loadSeed` and `SeedStorageAdapter.loadSeed` in `web-of-trust/packages/wot-core`) are non-conformant under `wot-identity@0.1` and must migrate to handle-/derive-style APIs. The concrete TypeScript shape of that migration is a downstream `web-of-trust` task; this ADR does not prescribe it.

- Implementations declare their Runtime-SHOULD posture as part of their conformance claim (see `CONFORMANCE.md`). Typical values: non-extractable handles yes / no / partial, plus the platform facility used (Web Crypto, iOS Keychain, Android Keystore, Secure Enclave, OS keyring, etc.).

- Future runtime-specific ADRs (iOS Keychain, Android Keystore, Rust runtime, native desktop) should follow the same three-layer schema rather than reopening the bar.

- The bar deliberately does not commit `wot-identity@0.1` to any specific vendor facility. Web Crypto `CryptoKey extractable: false`, Secure Enclave, Android Keystore, iOS Keychain, and IndexedDB are non-normative examples; none of them are required as MUST.

- No new test vector is introduced. Conformance here is an API-surface check (no `getSeed()`-shaped operation crosses the application/port boundary) plus a declared Runtime-SHOULD posture, not a cross-implementation byte-for-byte vector.
