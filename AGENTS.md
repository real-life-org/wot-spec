# Agent Instructions for wot-spec

This repository is the normative protocol specification. Treat changes here differently from implementation work.

## Authority

- `wot-spec` is the source of truth for protocol behavior, schemas, test vectors, and conformance profiles.
- Implementation repositories such as `web-of-trust` may provide feedback, but they must not override this repository.
- Do not add implementation-only workarounds to normative documents.

## Required Context

Before editing normative content, read:

- `CONTRIBUTING.md`
- `CONFORMANCE.md`
- `VERSIONING.md`
- `docs/automation/spec-agent-flow.md`
- `docs/automation/spec-change-checklist.md`
- The affected spec document, schema, vector, and manifest entries.

## Normative Language

Use the existing German RFC-2119 terms consistently:

- `MUSS` / `MUESSEN` for required behavior.
- `SOLLTE` / `SOLLTEN` for recommended behavior.
- `DARF` / `DUERFEN` for permitted behavior.

Avoid vague normative language such as "usually", "probably", or "as needed" unless it is explicitly non-normative guidance.

## Spec Change Rules

- A normative behavior change must update or explicitly review affected schemas, test vectors, `CONFORMANCE.md`, and `conformance/manifest.json`.
- A clarification may be docs-only only when it does not change wire format, validation behavior, or conformance expectations.
- If a rule cannot be validated by a schema or vector, state why.
- Keep examples and schemas aligned.
- Prefer focused PRs that clarify one protocol surface at a time.

## Human Gates

Stop for human decision before merging when a change affects:

- Cryptography, signatures, DID/JWS, key derivation, key rotation, or storage confidentiality.
- Authorization, membership removal, or group key distribution semantics.
- Wire formats, schema required fields, or conformance profile claims.
- Breaking changes for existing implementations.
- Ambiguous or conflicting protocol requirements.

## Checks

Run relevant checks before handoff:

```sh
npm run validate:conformance
npm run validate:schemas
npm run validate:vectors
npm run validate:didcomm
git diff --check
```

Use `npm run validate` when a change touches multiple conformance surfaces.
