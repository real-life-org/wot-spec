# WoT Spec 006: Identity Migration (Key Rotation)

- **Status:** Draft
- **Authors:** Anton Tranelis
- **Date:** 2026-04-11

## Abstract

This document specifies how an existing WoT identity can be migrated to a new key pair without losing trust relationships. This is needed when the derivation path changes (e.g. to conform to [Spec 001](001-identity-and-key-derivation.md)), when a key is compromised, or when upgrading to a new algorithm.

## Migration Message

The holder of an old identity signs a statement with the old key:

```json
{
  "type": "identity-migration",
  "oldDid": "did:key:z6Mk...(old)",
  "newDid": "did:key:z6Mk...(new)",
  "timestamp": "2026-04-11T12:00:00.000Z",
  "proof": {
    "type": "Ed25519Signature2020",
    "verificationMethod": "did:key:z6Mk...(old)#key-1",
    "created": "2026-04-11T12:00:00.000Z",
    "proofPurpose": "authentication",
    "proofValue": "..."
  }
}
```

The old key signs the migration, proving ownership of both identities.

## Properties

- Existing attestations remain valid — verifiers follow the migration chain
- The migration message is propagated through the trust graph (relay, gossip)
- Only the holder of the old private key can initiate a migration
- A migration is permanent — once published, it cannot be undone

## Trust Continuity

When a verifier encounters an attestation pointing to an old DID:

1. Check if a migration message exists for that DID
2. If yes, follow the chain to the current DID
3. The attestation is considered valid for the current identity

## Use Cases

- **Spec conformance:** Changing the derivation path to match a new standard
- **Key compromise:** Rotating to a new key after the old one was exposed
- **Device loss:** Generating a new key from the same mnemonic with updated parameters
- **Algorithm upgrade:** Migrating from Ed25519 to a post-quantum algorithm (future)

## Open Questions

1. **Chain length:** Should there be a limit on how many times an identity can migrate? Long chains increase verification cost.
2. **Revocation:** Can a migration be revoked (e.g. if the new key is compromised before propagation)?
3. **Propagation:** How is the migration message distributed? Via relay, gossip, or profiles endpoint?
4. **Timestamp verification:** Should verifiers reject migrations with timestamps in the future?
