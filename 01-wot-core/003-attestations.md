# WoT Spec 003: Attestations

- **Status:** Entwurf
- **Autoren:** Anton Tranelis, Sebastian Galek
- **Datum:** 2026-04-21

## Zusammenfassung

Attestations sind das Herzstück des Web of Trust. Eine Attestation ist eine signierte, kryptografisch verifizierbare Aussage einer Person über eine andere Person, ein Projekt, einen Ort oder ein Ereignis.

Attestations im Web of Trust sind **W3C Verifiable Credentials 2.0** — sie folgen dem offenen Standard und sind damit interoperabel mit anderen Systemen. Als Proof-Format verwenden wir das **VC-JOSE-COSE Profil** (W3C) — die Attestation wird als JWS Compact Serialization transportiert, konsistent mit [Spec 002](002-signaturen-und-verifikation.md).

## Referenzierte Standards

- **W3C Verifiable Credentials Data Model 2.0** (W3C Recommendation, Mai 2025) — Datenmodell
- **W3C VC-JOSE-COSE** (W3C Recommendation) — Securing VCs mit JWS
- **JWS** (RFC 7515) — JSON Web Signature
- **DID Core** (W3C Recommendation) — Identifiers für Issuer und Subject
- **Ed25519** (RFC 8032) — Signaturalgorithmus
- **JCS** (RFC 8785) — Kanonisierung (siehe [Spec 002](002-signaturen-und-verifikation.md))

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

- `alg`: MUSS `"EdDSA"` sein (siehe [Spec 002](002-signaturen-und-verifikation.md), Algorithmus-Validierung)
- `typ`: MUSS `"vc+jwt"` sein — W3C VC-JOSE-COSE Standard Media Type
- `kid`: Verification Method ID aus dem DID-Dokument des Issuers (siehe [Core 005](005-did-resolution.md)). Ermöglicht Key-Auflösung ohne den Payload zu parsen.

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
| `validFrom` | ISO 8601 | Ab wann die Attestation gültig ist |

### Optionale Felder

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `validUntil` | ISO 8601 | Ablaufdatum (wenn die Attestation zeitlich begrenzt ist) |
| `id` | URI | Eindeutige ID der Attestation (z.B. `urn:uuid:...`) |
| `credentialStatus` | Object | Widerrufs-Mechanismus (siehe Unveränderlichkeit) |

Das ist der vollständige WoT Core. Keine weiteren Pflichtfelder. Extensions fügen Felder über eigene Contexts hinzu (siehe Abschnitt "Drei Schichten").

## Drei Schichten: Core + Extensions

```
┌─────────────────────────────────────────────────────────────┐
│  W3C Verifiable Credentials 2.0 + VC-JOSE-COSE             │
│  @context, type, issuer, credentialSubject, validFrom       │
├─────────────────────────────────────────────────────────────┤
│  WoT Core (dieses Dokument)                                │
│  WotAttestation, claim                                      │
├──────────────────────────┬──────────────────────────────────┤
│  Real Life Extension     │  Human Money Extension           │
│  display (emoji, color,  │  trustLevel, liability,          │
│  shape), event, location │  hopLimit, SD-JWT                │
└──────────────────────────┴──────────────────────────────────┘
```

### WoT Core

Jede Implementierung MUSS den VC-Payload aus dem Abschnitt [Format](#format) verstehen: `@context`, `type`, `issuer`, `credentialSubject.claim`, `validFrom` + die JWT Claims (`iss`, `sub`, `nbf`). Was man darüber hinaus nicht kennt, ignoriert man.

### Real Life Extension

Erweitert den WoT Core um visuelle Darstellung und Event-Bezüge:

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    "https://web-of-trust.de/vocab/v1",
    "https://web-of-trust.de/vocab/rls/v1"
  ],
  "type": ["VerifiableCredential", "WotAttestation"],
  "issuer": "did:key:z6Mk...alice",
  "credentialSubject": {
    "id": "did:key:z6Mk...bob",
    "claim": "hat am Community-Workshop teilgenommen",
    "display": {
      "emoji": "🎓",
      "color": "#5bc0eb",
      "shape": "star"
    },
    "event": "event-uuid-123",
    "location": { "lat": 48.7758, "lng": 9.1829 }
  },
  "validFrom": "2026-04-21T10:00:00Z"
}
```

Sebastians App sieht: WotAttestation mit Claim "hat am Community-Workshop teilgenommen". Die Felder `display`, `event`, `location` kennt sie nicht — ignoriert sie. Der Claim ist trotzdem verifizierbar.

### Human Money Extension

Erweitert den WoT Core um Vertrauensstufen und Haftung:

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    "https://web-of-trust.de/vocab/v1",
    "https://web-of-trust.de/vocab/hmc/v1"
  ],
  "type": ["VerifiableCredential", "WotAttestation", "TrustRating"],
  "issuer": "did:key:z6Mk...alice",
  "credentialSubject": {
    "id": "did:key:z6Mk...bob",
    "claim": "Vertrauensstufe 3",
    "trustLevel": 3,
    "liability": "4.0h",
    "hopLimit": 2
  },
  "validFrom": "2026-04-21T10:00:00Z"
}
```

Unsere App sieht: WotAttestation mit Claim "Vertrauensstufe 3". Die Felder `trustLevel`, `liability`, `hopLimit` kennen wir nicht — ignorieren wir. Der Claim ist trotzdem verifizierbar.

Für die effiziente Propagation gebündelter Trust Lists nutzt Human Money Core **SD-JWT VC** (Selective Disclosure JWT). Damit kann die gesamte Trust List signiert und selektiv weitergegeben werden — ohne die Signatur zu brechen. SD-JWT VC ist als IETF-Standard kompatibel mit dem W3C VC-JOSE-COSE Profil. SD-JWT ist nicht Teil des WoT Core — der WoT Core definiert einzelne Attestations als JWS-signierte VCs. SD-JWT ist eine Optimierung für den spezifischen Use Case gebündelter Trust Lists.

### Das Prinzip

Jede App versteht den WoT Core. Was sie nicht kennt, ignoriert sie. Die JWS-Signatur ist immer verifizierbar — egal welche Extensions im Payload stecken. So bleiben alle Implementierungen interoperabel, ohne dass jeder alles verstehen muss.

## Empfängerprinzip

Die Attestation gehört dem Subject. Konkret:

- Der Issuer erstellt und signiert die Attestation (als JWS)
- Die Attestation wird verschlüsselt an den Subject/Holder übermittelt
- Der Holder speichert den JWS lokal
- Der Holder entscheidet ob er sie akzeptiert und wem er sie zeigt
- Der Issuer behält keine Kopie (kann aber natürlich eine behalten)

### Akzeptanz

Der Holder hat ein lokales `accepted`-Flag pro Attestation. Nicht akzeptierte Attestations sind unsichtbar für Dritte. Das Flag ist **nicht Teil des VC** und wird **nicht signiert** — es ist eine reine lokale Entscheidung.

## Unveränderlichkeit

Attestations sind **unveränderlich.** Einmal signiert, kann der Inhalt nicht geändert werden ohne die JWS-Signatur zu brechen.

Wenn sich die Meinung des Issuers ändert, erstellt er eine **neue Attestation:**

```
Januar:  Alice → Bob: "ist zuverlässig"
Juni:    Alice → Bob: "hat mich enttäuscht"
```

Beide Aussagen existieren. Beide sind signiert und wahr — zum jeweiligen Zeitpunkt. Die Trust-Propagation (siehe [Human Money Extension: Trust-Scores](../04-hmc-extensions/H01-trust-scores.md)) berücksichtigt beides — neuere Aussagen wiegen schwerer.

### Widerruf (Credential Status)

Im WoT-Core werden Attestations nicht formal widerrufen — stattdessen überschreibt eine neuere Attestation die ältere (siehe oben). Für Extensions die formalen Widerruf brauchen (z.B. HMC Trust-Scores, Transaktionen) DARF der W3C **StatusList2021** Mechanismus über das optionale `credentialStatus`-Feld genutzt werden. Details werden in den jeweiligen Extensions spezifiziert (siehe [H01](../04-hmc-extensions/H01-trust-scores.md), [H02](../04-hmc-extensions/H02-transactions.md)).

### Zukünftige Erweiterung: Verifiable Presentations (VP)

Innerhalb des WoT-Ökosystems werden Attestations direkt als JWS-Strings geteilt — über den Sync-Layer, die Inbox oder den Profil-Service. Der Holder kontrolliert durch bewusste Veröffentlichung, wer seine Attestations sieht.

Für **externe Interop** (z.B. wenn ein externer Verifier WoT-Attestations prüfen will) definiert W3C VC 2.0 das Konzept der **Verifiable Presentation (VP)** — ein JWS-Wrapper signiert vom Holder, der beweist dass er die Credentials **gerade, bewusst und an einen bestimmten Empfänger** präsentiert (`typ: "vp+jwt"`, mit `aud` und `nonce`). VP-Support ist als Extension geplant wenn externer Interop-Bedarf entsteht. Das VC-JOSE-COSE-Format unserer Attestations ist dafür vorbereitet — eine VP ist nur ein weiterer JWS-Wrapper um bestehende VC-JWS-Strings.

## Verifikation

Um eine Attestation zu verifizieren:

1. JWS-Header dekodieren und `alg` prüfen — MUSS `"EdDSA"` sein (siehe [Spec 002](002-signaturen-und-verifikation.md))
2. `kid` aus dem Header extrahieren → DID-Dokument via `resolve()` auflösen ([Core 005](005-did-resolution.md)) → Ed25519 Public Key aus `verificationMethod` / `assertionMethod`
3. JWS-Signatur verifizieren gegen die exakt empfangenen Bytes `BASE64URL(header) + "." + BASE64URL(payload)` (keine Re-Kanonisierung)
4. Payload dekodieren und parsen
5. `@context` und `type` prüfen — enthält es `"WotAttestation"`?
6. `iss` im Payload MUSS zur DID im `kid`-Header passen
7. `nbf` prüfen — liegt in der Vergangenheit?
8. Falls `exp` vorhanden — noch nicht abgelaufen?
9. Falls `credentialStatus` vorhanden — StatusList prüfen (nicht widerrufen?)

Kein externer Service nötig für die Signatur-Verifikation. Alles lokal verifizierbar (DID-Dokument aus Cache). Nur die StatusList-Prüfung (Schritt 9) kann einen optionalen Online-Abruf erfordern.

## Austausch-Szenarien

### Freitext-Attestation

Alice öffnet Bobs Profil, schreibt eine Attestation, wählt Emoji + Farbe + Form, signiert, schickt ab. Bob bekommt den JWS in seiner Inbox.

### Gegenseitige Verifikation (In-Person)

Alice und Bob treffen sich. Beide scannen den QR-Code des anderen (Challenge-Response mit Nonce). Jeder erstellt eine Verification-Attestation für den anderen. Bei Reconnect werden sie zugestellt.

### Claim-Link (QR-Code für Events)

Ein Event-Organisator erstellt ein Attestation-Template vorab:

```json
{
  "claim": "hat am Community-Workshop 2026 teilgenommen",
  "display": { "emoji": "🎓", "color": "#5bc0eb", "shape": "star" }
}
```

Der Template wird als QR-Code angezeigt. Teilnehmer scannen ihn, authentifizieren sich mit ihrer DID, und der Organisator stellt die Attestation automatisch aus — signiert mit seiner DID, transportiert als JWS.

### Badges / Quests

Ein Quest-System definiert Attestation-Templates für Achievements. Wer ein Quest absolviert, bekommt automatisch die entsprechende Badge-Attestation — ausgestellt vom Quest-Ersteller.

## Subjects

Das `credentialSubject.id` kann verschiedene Dinge identifizieren:

- **Person:** `did:key:z6Mk...` — die häufigste Verwendung
- **Projekt, Ort, Veranstaltung:** ID-Format wird in zukünftigen Dokumenten spezifiziert

## Aktuelle Implementierungen

| | WoT Core | Utopia Map | Human Money Core | Spec |
|---|---|---|---|---|
| **VC-Version** | 1.1 | — | — | ✅ VC 2.0 |
| **Format** | Eigenes JSON | Directus API | SD-JWT Trust List | ✅ W3C VC 2.0 |
| **Proof** | Ed25519Signature2020 | Keine (Directus Auth) | Ed25519 in SD-JWT | ✅ JWS (VC-JOSE-COSE) |
| **Claim** | `claim: string` | `text: string` | Trust-Level 0-3 | ✅ `claim` Freitext |
| **Visuell** | Keine | emoji + color + shape | Keine | ✅ `display` Objekt |
| **Speicherort** | Empfänger | Server (Directus) | Lokale Trust List | ✅ Empfänger (Holder) |

## Anpassungsbedarf

**WoT Core (TypeScript):**
- VC Context von `2018/credentials/v1` auf `ns/credentials/v2` umstellen
- `issuanceDate` → `validFrom`
- `proof`-Objekt entfernen — Attestation als JWS Compact transportieren
- `typ: "vc+jws"` und `kid` im JWS-Header setzen

**Human Money Core (Rust):**
- SD-JWT VC ist bereits JWS-basiert — kein grundlegender Formatwechsel nötig
- VC Context auf v2 prüfen

## Offene Fragen

### 1. WoT Vocabulary URI

`"https://web-of-trust.de/vocab/v1"` — die Domain steht fest, aber das Vocabulary-Dokument unter dieser URI muss noch erstellt werden.

### 2. Subjects jenseits von Personen

Wie identifizieren wir Projekte, Orte, Veranstaltungen als Subjects? Der W3C VC Standard erlaubt jede URI als `credentialSubject.id` — DIDs, UUIDs (`urn:uuid:...`), URLs. Die konkrete Entscheidung welches Format für welchen Subject-Typ verwendet wird steht noch aus.

### 3. Claim-Link Protokoll

Wie funktioniert der QR-Code-basierte Claim-Link technisch? Offene Design-Fragen:
- Enthält der QR-Code das Attestation-Template direkt oder eine URL?
- Wie authentifiziert sich der Scanner (DID-Austausch)?
- Wer signiert — das Handy des Organisators, sein Broker, oder ein delegiertes Device?
- Funktioniert es offline (Bluetooth/LAN) oder nur online?
