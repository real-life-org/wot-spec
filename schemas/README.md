# Schemas

Dieser Ordner enthaelt JSON Schemas fuer normative Payloads der Web-of-Trust-Spezifikation.

Status: initialer Draft. Die Schemas decken die in den Spec-Dokumenten beschriebenen Kern-Payloads ab und werden mit den Formaten weiter geschaerft.

## Ziele

- Implementierungen koennen Payloads vor dem Signieren und nach dem Parsen validieren.
- Breaking Changes werden als Schema-Aenderungen sichtbar.
- Testvektoren koennen automatisch gegen die Schemas geprueft werden.

## Vorhandene Schemas

| Schema | Dokument | Zweck |
|---|---|---|
| `qr-challenge.schema.json` | Trust 002 | QR-Code Challenge fuer In-Person-Verifikation |
| `did-document-wot.schema.json` | Identity 003 | Minimales WoT-DID-Dokument-Profil |
| `device-key-binding.schema.json` | Identity 004 | DeviceKeyBinding Payload fuer Phase-2-Delegation |
| `delegated-attestation-bundle.schema.json` | Identity 004 | JSON-Container fuer delegierte Attestation + Binding-JWS |
| `attestation-vc-payload.schema.json` | Trust 001 | WotAttestation VC 2.0 Payload |
| `didcomm-plaintext-message.schema.json` | Sync 003 | WoT Plaintext Envelope mit DIDComm-kompatiblem Shape |
| `log-entry-payload.schema.json` | Sync 002 | JWS-Payload eines Log-Eintrags |
| `capability-payload.schema.json` | Sync 003 | Broker-Capability JWS-Payload |
| `profile-service-response.schema.json` | Sync 004 | Profil-Service Antwort mit DID-Dokument |
| `space-invite.schema.json` | Sync 005 | Space-Einladung ueber Inbox |
| `key-rotation.schema.json` | Sync 005 | Key-Rotation Nachricht |
| `trust-list-delta.schema.json` | H03 | HMC Trust-List-Gossip Nachricht |

## Regeln

- Schemas verwenden JSON Schema Draft 2020-12.
- Schemas validieren Payload-Struktur, nicht kryptographische Gueltigkeit.
- JWS-Signaturen, DID-Resolution und Disclosure-Hashes werden durch Conformance-Tests geprueft, nicht durch JSON Schema.
- Felder, die Extensions erlauben, muessen explizit mit `additionalProperties` oder `unevaluatedProperties` modelliert werden.

## Beispiele

- `examples/valid/` enthaelt je Schema mindestens ein gueltiges Beispiel.
- `examples/invalid/` enthaelt je Schema mindestens ein bewusst ungueltiges Beispiel.
- `scripts/validate_schemas.py` prueft, dass alle gueltigen Beispiele akzeptiert und alle ungueltigen Beispiele abgelehnt werden.

## Versionierung

Schema-Versionen folgen den Wire-Versionen der zugehoerigen Formate. Breaking Schema-Aenderungen muessen in `CHANGELOG.md` und `VERSIONING.md` beruecksichtigt werden.
