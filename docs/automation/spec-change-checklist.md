# Spec Change Checklist

Use this checklist for normative `wot-spec` PRs.

## Classification

- [ ] Clarification only, no behavior change.
- [ ] Normative behavior change.
- [ ] Schema change.
- [ ] Test-vector change.
- [ ] Conformance manifest/profile change.
- [ ] Research/non-normative change.

## Traceability

- [ ] Affected profile is named.
- [ ] Affected spec document section is named.
- [ ] Affected schema is named or explicitly not applicable.
- [ ] Affected vector section is named or explicitly not applicable.
- [ ] Downstream implementation impact is stated.

## Consistency

- [ ] Normative text uses `MUSS`, `SOLLTE`, and `DARF` consistently.
- [ ] Examples match schema shape.
- [ ] Schema required fields match normative text.
- [ ] Vectors cover the behavior when practical.
- [ ] `CONFORMANCE.md` is updated or explicitly unchanged.
- [ ] `conformance/manifest.json` is updated or explicitly unchanged.

## Human Gates

- [ ] Crypto/signature/DID/JWS/key-management impact reviewed.
- [ ] Authorization or membership-removal impact reviewed.
- [ ] Breaking change status reviewed.
- [ ] Ambiguous policy decisions escalated.

## Validation

- [ ] `npm run validate:conformance`
- [ ] `npm run validate:schemas`
- [ ] `npm run validate:vectors`
- [ ] `npm run validate:didcomm`
- [ ] `git diff --check`

## Handoff

- [ ] Draft PR remains human-controlled.
- [ ] PR summary lists validation results.
- [ ] PR summary states downstream TS implementation work, if any.
