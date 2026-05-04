# Spec Agent Flow

## Purpose

This document defines how local agents may help with `wot-spec` changes. The goal is to clarify normative protocol behavior, schemas, vectors, and conformance profiles without letting an implementation invent the specification.

## Default Flow

1. Identify the affected profile, spec document, schema, vector, and conformance manifest entries.
2. Classify the change as clarification, normative change, schema change, test-vector change, or research.
3. Write the smallest normative text change that resolves the ambiguity.
4. Update schemas and vectors when the behavior is machine-checkable.
5. Update `CONFORMANCE.md` or `conformance/manifest.json` when profile claims or validation surfaces change.
6. Run validation commands.
7. Open a draft PR and stop for human review.

## Scope Discipline

Spec PRs should be small:

- One protocol concept or ambiguity per PR.
- One schema family or vector section per PR when possible.
- No implementation repo changes in the same PR.
- No broad wording cleanup mixed with normative behavior changes.

## Review Focus

Reviewers should check:

- Is the normative rule unambiguous?
- Are examples, schemas, vectors, and conformance text consistent?
- Does the change create a breaking change?
- Does the PR state downstream implementation impact?
- Are human gates called out for crypto, authorization, membership, or key-management semantics?
- Are validation commands listed and run?

## Downstream Implementation Handoff

When a spec PR defines behavior that `web-of-trust` should implement, the PR should state:

- Affected conformance profile.
- Expected TypeScript implementation surface.
- Required test-vector or schema evidence.
- Whether existing TS behavior is expected to change or be removed.

After merge, create or update a corresponding implementation slice in `web-of-trust`.

## Agent Boundaries

Agents may draft spec text, schema changes, vectors, validation updates, and PR summaries under explicit scope. Agents must not:

- Merge PRs.
- Release versions.
- Force-push or bypass hooks.
- Modify implementation repositories as part of a spec PR.
- Resolve crypto/security/membership policy ambiguity without a human gate.
