# WoT Identity 004: Device-Key-Delegation

- **Status:** Geplanter Entwurf fuer Phase 2
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-27
- **Scope:** DeviceKeyBinding, delegierte Device-Signaturen und portable Offline-Verifikation
- **Depends on:** Identity 001, Identity 002, Identity 003, Trust 001
- **Conformance profile:** `wot-device-delegation@0.1` (geplant; nicht Teil von `wot-identity@0.1`)

## Zusammenfassung

Phase 1 nutzt das Shared-Seed-Modell: alle Geraete einer Person leiten denselben Identity Key ab. Phase 2 fuehrt optionale Device Keys ein, ohne sofort eine neue DID-Methode vorauszusetzen.

Das Modell besteht aus:

- einer primaeren **Identity DID** der Person
- einer technischen **Device DID** pro Geraet
- einem **DeviceKeyBinding-JWS**, signiert vom Identity Key
- einem **Delegated-Attestation-Bundle**, das Attestation-JWS und Binding-JWS zusammen transportiert

Device DIDs sind keine sozialen Identitaeten. Sie sind technische Signing Keys, die durch die Identity DID fuer konkrete Capabilities delegiert werden.

## Identitaetsmodell

In Phase 2 nutzt jedes Geraet eine eigene `did:key`-DID:

```text
Identity DID: did:key:z6Mk...identity
Phone Key:    did:key:z6Mk...phone#sig-0
Tablet Key:   did:key:z6Mk...tablet#sig-0
```

Die soziale Aussage bleibt immer bei der Identity DID:

- `issuer` / `iss` in Attestations bleibt die Identity DID
- `kid` im JWS-Header zeigt bei delegierten Signaturen auf den Device Key
- `deviceKid` bezeichnet den konkreten Device-Signing-Key

Ein Verifier darf eine Device DID nicht als eigene Person im Trust Graph behandeln. Ohne gueltiges DeviceKeyBinding ist eine Device-DID fuer soziale Aussagen wertlos.

## `deviceKid`

`deviceKid` ist der kanonische Key Identifier des Device-Signing-Keys.

In Phase 2 ist `deviceKid` eine eigenstaendige `did:key`-DID-URL:

```text
deviceKid = did:key:<device-ed25519-public-key>#sig-0
```

Der Binding-Payload enthaelt zusaetzlich `devicePublicKeyMultibase`. Dieses Feld MUSS denselben Ed25519 Public Key bezeichnen wie `deviceKid`. Wenn `deviceKid` und `devicePublicKeyMultibase` nicht denselben Key bezeichnen, MUSS der Verifier das Binding ablehnen.

In spaeteren DID-Methoden kann `deviceKid` eine Verification Method der Identity DID sein, z.B. `did:webvh:example:alice#device-phone-1`.

## DeviceKeyBinding

Ein DeviceKeyBinding autorisiert einen Device Key, fuer eine Identity DID bestimmte Signaturen zu erzeugen.

### Payload

```json
{
  "type": "device-key-binding",
  "iss": "did:key:z6Mk...identity",
  "sub": "did:key:z6Mk...device#sig-0",
  "deviceKid": "did:key:z6Mk...device#sig-0",
  "devicePublicKeyMultibase": "z6Mk...device",
  "deviceName": "Alice's Phone",
  "capabilities": ["sign-attestation", "sign-verification", "sign-log-entry", "broker-auth"],
  "validFrom": "2026-04-27T10:00:00Z",
  "validUntil": "2027-04-27T10:00:00Z",
  "iat": 1777284000
}
```

| Feld | Pflicht | Bedeutung |
|---|---|---|
| `type` | Ja | MUSS `"device-key-binding"` sein |
| `iss` | Ja | Identity DID, die delegiert |
| `sub` | Ja | Subject der Delegation; MUSS `deviceKid` entsprechen |
| `deviceKid` | Ja | DID-URL des Device-Signing-Keys |
| `devicePublicKeyMultibase` | Ja | Ed25519 Public Key des Devices, redundant fuer Offline-Pruefung |
| `deviceName` | Nein | Lokaler Anzeigename; nicht sicherheitskritisch |
| `capabilities` | Ja | Zweckgebundene Signaturrechte |
| `validFrom` | Ja | Beginn der Device-Signaturberechtigung |
| `validUntil` | Ja | Ende der Device-Signaturberechtigung |
| `iat` | Ja | Ausstellungszeitpunkt des Bindings als Unix-Timestamp |

`validFrom` und `validUntil` begrenzen nur die Signaturberechtigung des Device Keys. Sie sind kein Gueltigkeitsfenster fuer Attestations, die waehrend des Delegationszeitraums ausgestellt wurden. `iat` im Binding ist der Ausstellungszeitpunkt des Bindings; `iat` in der Attestation ist der Ausstellungszeitpunkt der Attestation. Verifier MUESSEN Zeitvergleiche als Instant-Vergleich durchfuehren, also ISO-8601-Zeitpunkte und Unix-Timestamps vor dem Vergleich normalisieren.

### Capabilities

| Capability | Bedeutung |
|---|---|
| `sign-log-entry` | Device darf Sync-Log-Eintraege signieren |
| `sign-verification` | Device darf Verification-Attestations signieren |
| `sign-attestation` | Device darf normale Attestations signieren |
| `broker-auth` | Device darf Broker-Challenge-Response signieren |
| `device-admin` | Device darf weitere Device Keys delegieren oder widerrufen |

Implementierungen MUESSEN die jeweils benoetigte Capability explizit pruefen. Unbekannte Capabilities duerfen nicht als bekannte Capabilities interpretiert werden.

### JWS-Header

DeviceKeyBinding wird als JWS Compact Serialization signiert.

```json
{
  "alg": "EdDSA",
  "typ": "wot-device-key-binding+jwt",
  "kid": "did:key:z6Mk...identity#sig-0"
}
```

- `alg` MUSS `"EdDSA"` sein.
- `kid` MUSS auf den Identity Key zeigen, der `iss` kontrolliert.
- `typ` SOLLTE `"wot-device-key-binding+jwt"` sein.

## Delegated-Attestation-Bundle

Eine delegierte Attestation wird als JSON-Container transportiert. Der Container selbst ist nicht signiert; die Integritaet kommt aus den beiden JWS-Signaturen.

```json
{
  "type": "wot-delegated-attestation-bundle/v1",
  "attestationJws": "<VC-JWS signiert mit Device Key>",
  "deviceKeyBindingJws": "<DeviceKeyBinding-JWS signiert mit Identity Key>"
}
```

Das Bundle ist keine Verifiable Presentation und kein weiteres JWS-Profil. Es ist ein portabler Offline-Container fuer genau die Nachweise, die ein Verifier braucht.

## Verifikation

Ein Verifier einer delegierten Attestation MUSS:

1. Bundle `type` gegen `wot-delegated-attestation-bundle/v1` pruefen.
2. DeviceKeyBinding-JWS Header `alg`, `typ` und `kid` pruefen.
3. Identity DID aus `iss` des Binding-Payloads gegen die DID im Binding-Header `kid` pruefen.
4. DeviceKeyBinding-JWS mit dem Identity Key verifizieren.
5. `sub`, `deviceKid` und Attestation-JWS Header `kid` auf denselben Device Key pruefen.
6. `devicePublicKeyMultibase` gegen den aus `deviceKid` aufgeloesten Public Key pruefen.
7. Attestation-JWS mit dem Device Key verifizieren.
8. `issuer` / `iss` der Attestation gegen `iss` des Bindings pruefen.
9. `iat` der Attestation pruefen und sicherstellen, dass `validFrom <= iat <= validUntil` als normalisierter Instant-Vergleich gilt.
10. Benoetigte Capability pruefen: `sign-attestation` oder `sign-verification`.
11. Die normalen Trust-001-Regeln fuer Attestation-Payload, `nbf`, optionales `exp` und optionales `credentialStatus` anwenden.

Delegierte Attestations MUESSEN einen `iat`-Claim enthalten. Ohne `iat` kann der Verifier nicht pruefen, ob das Device zum Signaturzeitpunkt autorisiert war.

### Pseudocode

```text
verifyDelegatedAttestationBundle(bundle, requiredCapability):
  require bundle.type == "wot-delegated-attestation-bundle/v1"

  attHeader, attPayload = decodeJws(bundle.attestationJws)
  bindingHeader, bindingPayload = decodeJws(bundle.deviceKeyBindingJws)

  require bindingHeader.alg == "EdDSA"
  require bindingHeader.typ == "wot-device-key-binding+jwt"
  require bindingPayload.type == "device-key-binding"

  identityDid = didFromKid(bindingHeader.kid)
  require bindingPayload.iss == identityDid
  verifyJws(bundle.deviceKeyBindingJws, resolve(identityDid, bindingHeader.kid))

  require bindingPayload.sub == bindingPayload.deviceKid
  require attHeader.kid == bindingPayload.deviceKid
  require bindingPayload.devicePublicKeyMultibase == publicKeyFromKid(bindingPayload.deviceKid)

  verifyJws(bundle.attestationJws, publicKeyFromKid(bindingPayload.deviceKid))

  require attPayload.iss == bindingPayload.iss
  require attPayload.issuer == bindingPayload.iss
  require requiredCapability in bindingPayload.capabilities
  require attPayload.iat exists

  attestationTime = instantFromUnix(attPayload.iat)
  require instantFromIso(bindingPayload.validFrom) <= attestationTime
  require attestationTime <= instantFromIso(bindingPayload.validUntil)

  apply Trust-001 verification rules to attPayload
  return ok
```

Fuer normale Attestations ist `requiredCapability = "sign-attestation"`; fuer Verification-Attestations ist `requiredCapability = "sign-verification"`.

## Revocation

Phase 2 hat keine starke temporale Revocation. Widerrufe von Device Keys koennen ueber Profil-Service, Inbox oder Personal Doc verteilt werden, aber Offline-Verifier erfahren sie erst beim naechsten Update.

Darum gilt:

- Phase 2 ist self-contained und einfach, aber Revocation ist best-effort.
- Alte Signaturen bleiben nur so belastbar wie der mitgelieferte Delegation Proof und der Kenntnisstand des Verifiers.
- Das `iat` der Attestation ist signiert, aber kein unabhaengig bezeugter Zeitstempel; ein kompromittierter Device Key kann ohne Phase-3-History zurueckdatierte Signaturen erzeugen.
- Starke temporale Verifikation ist Aufgabe von Phase 3 (Sigchain oder DID-Methode mit verifiable History, z.B. `did:webvh`).

## Nicht Teil von `wot-identity@0.1`

Dieses Dokument beschreibt ein geplantes Phase-2-Profil. Implementierungen duerfen `wot-identity@0.1` und `wot-trust@0.1` beanspruchen, ohne Device-Key-Delegation zu implementieren.
