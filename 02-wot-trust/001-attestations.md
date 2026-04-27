# WoT Trust 001: Attestations

- **Status:** Entwurf
- **Autoren:** Anton Tranelis, Sebastian Galek
- **Datum:** 2026-04-21
- **Scope:** WoT Attestations als W3C VC 2.0 mit VC-JOSE-COSE/JWS
- **Depends on:** Identity 001, Identity 002, Identity 003, W3C VC 2.0, VC-JOSE-COSE
- **Conformance profile:** `wot-trust@0.1`

## Zusammenfassung

Attestations sind das Herzstück des Web of Trust. Eine Attestation ist eine signierte, kryptografisch verifizierbare Aussage einer Person über eine andere Person, ein Projekt, einen Ort oder ein Ereignis.

Attestations im Web of Trust sind **W3C Verifiable Credentials 2.0** — sie folgen dem offenen Standard und sind damit interoperabel mit anderen Systemen. Als Proof-Format verwenden wir das **VC-JOSE-COSE Profil** (W3C) — die Attestation wird als JWS Compact Serialization transportiert, konsistent mit [Identity 002](../01-wot-identity/002-signaturen-und-verifikation.md).

## Referenzierte Standards

- **W3C Verifiable Credentials Data Model 2.0** (W3C Recommendation, Mai 2025) — Datenmodell
- **W3C VC-JOSE-COSE** (W3C Recommendation) — Securing VCs mit JWS
- **JWS** (RFC 7515) — JSON Web Signature
- **DID Core** (W3C Recommendation) — Identifiers für Issuer und Subject
- **Ed25519** (RFC 8032) — Signaturalgorithmus
- **JCS** (RFC 8785) — Kanonisierung (siehe [Identity 002](../01-wot-identity/002-signaturen-und-verifikation.md))

## Grundprinzip

```
Jemand (Issuer)
  sagt etwas (Claim)
    über jemanden oder etwas (Subject)
      und signiert es (JWS)
```

Der Subject ist gleichzeitig der Holder — die Aussage gehört dem, über den sie gemacht wird. Der Holder entscheidet ob und wem er sie zeigt. Das ist das **Empfängerprinzip.**

## Format

Eine WoT Attestation ist ein W3C Verifiable Credential 2.0, gesichert als JWS (VC-JOSE-COSE Profil).

### VC-Payload (der signierte Inhalt)

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    "https://web-of-trust.de/vocab/v1"
  ],
  "type": ["VerifiableCredential", "WotAttestation"],
  "issuer": "did:key:z6Mk...alice",
  "credentialSubject": {
    "id": "did:key:z6Mk...bob",
    "claim": "kann gut programmieren"
  },
  "validFrom": "2026-04-21T10:00:00Z",

  "iss": "did:key:z6Mk...alice",
  "sub": "did:key:z6Mk...bob",
  "nbf": 1745222400,
  "jti": "urn:uuid:attestation-id"
}
```

Die letzten vier Felder sind **JWT Registered Claims** (RFC 7519) — redundant zu den VC-Feldern darüber, aber nötig für Kompatibilität mit Standard-JWT-Bibliotheken und externen VC-Verifiern:

| JWT Claim | VC-Feld | Wert |
|---|---|---|
| `iss` | `issuer` | DID des Issuers |
| `sub` | `credentialSubject.id` | DID des Subjects |
| `nbf` | `validFrom` | Unix-Timestamp (Sekunden seit Epoch) |
| `jti` | `id` (optional) | Eindeutige ID der Attestation |
| `exp` | `validUntil` (optional) | Unix-Timestamp (nur wenn zeitlich begrenzt) |

### Transport: JWS Compact Serialization (VC-JOSE-COSE Profil)

Die Attestation wird als JWS transportiert und gespeichert — konform mit dem **W3C VC-JOSE-COSE** Profil:

```
eyJhbGciOiJFZERTQSIsInR5cCI6InZjK2p3dCJ9.eyJAY29udGV4dCI6WyJodHRwcz...fQ.signatur
```

**JWS Header:**

```json
{ "alg": "EdDSA", "typ": "vc+jwt", "kid": "did:key:z6Mk...alice#sig-0" }
```

- `alg`: MUSS `"EdDSA"` sein (siehe [Identity 002](../01-wot-identity/002-signaturen-und-verifikation.md), Algorithmus-Validierung)
- `typ`: MUSS `"vc+jwt"` sein — W3C VC-JOSE-COSE Standard Media Type
- `kid`: Verification Method ID aus dem DID-Dokument des Issuers (siehe [Identity 003](../01-wot-identity/003-did-resolution.md)). Ermöglicht Key-Auflösung ohne den Payload zu parsen.

**JWS Payload:** Der VC-Payload (oben, inkl. JWT Claims), kanonisiert mit JCS (RFC 8785), dann Base64URL-kodiert.

**JWS Signature:** Ed25519-Signatur über `BASE64URL(header) + "." + BASE64URL(payload)`.

Es gibt kein eingebettetes `proof`-Objekt. Die Signatur ist der JWS selbst. Ein Format, eine Toolchain — konsistent mit dem gesamten Protokoll.

### Pflichtfelder

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `@context` | Array | `["https://www.w3.org/ns/credentials/v2", "https://web-of-trust.de/vocab/v1"]` |
| `type` | Array | Immer `["VerifiableCredential", "WotAttestation"]` |
| `issuer` | DID | Wer macht die Aussage |
| `credentialSubject.id` | DID oder URI | Über wen/was die Aussage ist |
| `credentialSubject.claim` | String | Die Aussage (Freitext) |
| `validFrom` | ISO 8601 | Ausstellungs- bzw. Gueltigkeitsbeginn der Attestation |

### Optionale Felder

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `validUntil` | ISO 8601 | Nur fuer explizit zeitlich begrenzte Aussagen; fehlt bei unbefristeten Attestations |
| `id` | URI | Eindeutige ID der Attestation (z.B. `urn:uuid:...`) |
| `credentialStatus` | Object | Widerrufs-Mechanismus (siehe Unveränderlichkeit) |

Attestations sind standardmaessig unbefristet. Aussagen ueber historische Ereignisse oder Erfahrungen (z.B. "Person A hat X getan") laufen nicht ab; sie koennen nur durch spaetere, zusaetzliche Attestations ergaenzt, relativiert oder widersprochen werden. `validUntil` bzw. `exp` wird nur fuer Aussagen verwendet, die fachlich selbst zeitlich begrenzt sind.

Das ist der vollständige WoT-Trust-Kern. Keine weiteren Pflichtfelder. Extensions fügen Felder über eigene Contexts hinzu (siehe [Erweiterbarkeit](#erweiterbarkeit)).

## Erweiterbarkeit

Jede Implementierung MUSS den VC-Payload aus dem Abschnitt [Format](#format) verstehen: `@context`, `type`, `issuer`, `credentialSubject.claim`, `validFrom` + die JWT Claims (`iss`, `sub`, `nbf`). Extensions DÜRFEN eigene Context-URIs, `type`-Werte und Felder ergänzen.

Unbekannte Extension-Felder MÜSSEN ignoriert werden, solange JWS-Signatur und Trust-Pflichtfelder gültig sind. Die JWS-Signatur ist über den gesamten Payload verifizierbar, unabhängig davon ob eine Implementierung alle Extension-Felder semantisch versteht.

SD-JWT VC, Trust-Listen, visuelle Darstellung oder Event-Bezüge sind Extensions und nicht Teil von WoT Trust. Für Phase 1 funktioniert `https://web-of-trust.de/vocab/v1` als Type-Identifier; ein auflösbares JSON-LD-Context-Dokument kann später ergänzt werden.

## Empfängerprinzip

Die Attestation gehört dem Subject. Konkret:

- Der Issuer erstellt und signiert die Attestation (als JWS)
- Die Attestation wird verschlüsselt an den Subject/Holder übermittelt
- Der Holder speichert den JWS lokal
- Der Holder entscheidet ob er sie veröffentlicht
- Der Issuer behält keine Kopie (kann aber natürlich eine behalten)

### Akzeptanz

Der Holder hat ein lokales `public`-Flag pro Attestation. Nicht veröffentlichte Attestations sind unsichtbar für Dritte (nicht im Profil-Service). Das Flag ist **nicht Teil des VC** und wird **nicht signiert** — es ist eine reine lokale Entscheidung, gespeichert als Metadaten neben dem JWS im Personal Doc.

## Unveränderlichkeit

Attestations sind **unveränderlich.** Einmal signiert, kann der Inhalt nicht geändert werden ohne die JWS-Signatur zu brechen.

Wenn sich die Meinung des Issuers ändert, erstellt er eine **neue Attestation:**

```
Januar:  Alice → Bob: "ist zuverlässig"
Juni:    Alice → Bob: "hat mich enttäuscht"
```

Beide Aussagen existieren. Beide sind signiert und wahr — zum jeweiligen Zeitpunkt. Die Trust-Propagation (siehe [Human Money Extension: Trust-Scores](../05-hmc-extensions/H01-trust-scores.md)) berücksichtigt beides — neuere Aussagen wiegen schwerer.

### Widerruf (Credential Status)

In WoT Trust werden Attestations nicht formal widerrufen — stattdessen überschreibt eine neuere Attestation die ältere (siehe oben). Für Extensions die formalen Widerruf brauchen (z.B. HMC Trust-Scores, Transaktionen) DARF der W3C **StatusList2021** Mechanismus über das optionale `credentialStatus`-Feld genutzt werden. Details werden in den jeweiligen Extensions spezifiziert (siehe [H01](../05-hmc-extensions/H01-trust-scores.md), [H02](../05-hmc-extensions/H02-transactions.md)).

### Zukünftige Erweiterung: Verifiable Presentations (VP)

Innerhalb des WoT-Ökosystems werden Attestations direkt als JWS-Strings geteilt — über den Sync-Layer, die Inbox oder den Profil-Service. Der Holder kontrolliert durch bewusste Veröffentlichung, wer seine Attestations sieht.

Für **externe Interop** (z.B. wenn ein externer Verifier WoT-Attestations prüfen will) definiert W3C VC 2.0 das Konzept der **Verifiable Presentation (VP)** — ein JWS-Wrapper signiert vom Holder, der beweist dass er die Credentials **gerade, bewusst und an einen bestimmten Empfänger** präsentiert (`typ: "vp+jwt"`, mit `aud` und `nonce`). VP-Support ist als Extension geplant wenn externer Interop-Bedarf entsteht. Das VC-JOSE-COSE-Format unserer Attestations ist dafür vorbereitet — eine VP ist nur ein weiterer JWS-Wrapper um bestehende VC-JWS-Strings.

## Verifikation

Um eine Attestation zu verifizieren:

1. JWS-Header dekodieren und `alg` prüfen — MUSS `"EdDSA"` sein (siehe [Identity 002](../01-wot-identity/002-signaturen-und-verifikation.md))
2. `kid` aus dem Header extrahieren → DID-Dokument via `resolve()` auflösen ([Identity 003](../01-wot-identity/003-did-resolution.md)) → Ed25519 Public Key aus `verificationMethod` / `assertionMethod`
3. JWS-Signatur verifizieren gegen die exakt empfangenen Bytes `BASE64URL(header) + "." + BASE64URL(payload)` (keine Re-Kanonisierung)
4. Payload dekodieren und parsen
5. `@context` und `type` prüfen — enthält es `"WotAttestation"`?
6. Fuer `wot-trust@0.1`: `iss` im Payload MUSS zur DID im `kid`-Header passen
7. `nbf` prüfen — liegt in der Vergangenheit?
8. Falls `exp` vorhanden — ist die explizit zeitlich begrenzte Aussage noch gueltig?
9. Falls `credentialStatus` vorhanden — StatusList prüfen (nicht widerrufen?)

Kein externer Service nötig für die Signatur-Verifikation. Alles lokal verifizierbar (DID-Dokument aus Cache). Nur die StatusList-Prüfung (Schritt 9) kann einen optionalen Online-Abruf erfordern.

**Geplante Phase-2-Erweiterung:** Attestations koennen spaeter auch mit einem delegierten Device Key signiert werden. Dann bleibt `iss` die Identity DID, der JWS-Header `kid` zeigt auf den Device Key, und der Verifier prueft zusaetzlich einen vom Identity Key signierten Delegation Proof. Der Proof begrenzt die Signaturberechtigung des Device Keys, nicht die Gueltigkeit der Attestation selbst. Er bindet Device Key, Identity DID, Ausstellungszeitpunkt und die Capability `sign-attestation` bzw. `sign-verification`. Das geplante Bundle ist ein JSON-Container mit Attestation-JWS und DeviceKeyBinding-JWS; es ist nicht Teil von `wot-trust@0.1`. Siehe [Device Keys](../research/device-keys.md).

## Subjects

Das `credentialSubject.id` kann verschiedene Dinge identifizieren:

- **Person:** `did:key:z6Mk...` — die häufigste Verwendung
- **Projekt, Ort, Veranstaltung:** ID-Format wird in zukünftigen Dokumenten spezifiziert
