# Conformance Kit

Dieses Verzeichnis ist der maschinenlesbare Einstieg für Implementierer. Es beschreibt, welche Spec-Dokumente, JSON Schemas, Beispiele und Testvektoren zu welchem Konformitätsprofil gehören.

## Artefakte

- [`manifest.json`](manifest.json) ordnet Profile wie `wot-identity@0.1`, `wot-trust@0.1`, `wot-sync@0.1` und geplante Erweiterungsprofile ihren Pflichtartefakten zu.
- [`rust-hmc-checklist.md`](rust-hmc-checklist.md) beschreibt den ersten externen Rust/HMC-Conformance-Harness fuer `v0.2.0-interop`.
- `schemas/` enthält JSON Schemas plus gültige und ungültige Beispiele.
- `test-vectors/` enthält reproduzierbare Krypto- und Interop-Vektoren.

## Validierung

```sh
npm run conformance
```

Das führt die vorhandenen Repo-Checks aus:

- Manifest-Konsistenz: referenzierte Dokumente, Schemas, Beispiele und Testvektor-Sektionen existieren.
- Schema-Validierung: gültige Beispiele werden akzeptiert, ungültige Beispiele abgelehnt.
- Testvektor-Validierung: Krypto- und Interop-Werte werden reproduziert.
- DIDComm-Envelope-Validierung: Plaintext Envelope wird mit `didcomm-node` und `@veramo/did-comm` gelesen.

## Grenzen

Dieses Kit ist noch kein Black-Box-Runner gegen externe Implementierungen. Implementierer sollen die Werte aus `test-vectors/` in ihrer Sprache reproduzieren und die im Manifest gelisteten Schemas akzeptieren bzw. ablehnen.

Ein späterer Runner kann dieses Manifest verwenden, um externe Binaries oder Libraries profilweise zu testen.
