# WoT Spec 003: Attestations

- **Status:** Entwurf
- **Autoren:** Anton Tranelis, Sebastian Galek
- **Datum:** 2026-04-13

## Zusammenfassung

Attestations sind das Herzstück des Web of Trust. Eine Attestation ist eine signierte, kryptografisch verifizierbare Aussage einer Person über eine andere Person, ein Projekt, einen Ort oder ein Ereignis.

Attestations im Web of Trust sind **W3C Verifiable Credentials** — sie folgen dem offenen Standard und sind damit interoperabel mit anderen Systemen.

## Referenzierte Standards

- **W3C Verifiable Credentials 2.0** (W3C Recommendation, Mai 2025) — Datenmodell
- **W3C Data Integrity 1.0** — Proof-Format (Ed25519Signature2020)
- **DID Core** (W3C Recommendation) — Identifiers für Issuer und Subject
- **Ed25519** (RFC 8032) — Signaturalgorithmus
- **JCS** (RFC 8785) — Kanonisierung (siehe [Spec 002](002-signaturen-und-verifikation.md))

## Grundprinzip

```
Jemand (Issuer)
  sagt etwas (Claim)
    über jemanden oder etwas (Subject)
      und signiert es (Proof)
```

Der Subject ist gleichzeitig der Holder — die Aussage gehört dem, über den sie gemacht wird. Der Holder entscheidet ob und wem er sie zeigt. Das ist das **Empfängerprinzip.**

## Format

Eine WoT Attestation ist ein W3C Verifiable Credential mit dem WoT-Profil:

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://wot.example/vocab/v1"
  ],
  "type": ["VerifiableCredential", "WotAttestation"],
  "issuer": "did:key:z6Mk...alice",
  "credentialSubject": {
    "id": "did:key:z6Mk...bob",
    "claim": "kann gut programmieren"
  },
  "issuanceDate": "2026-04-13T10:00:00Z",
  "proof": {
    "type": "Ed25519Signature2020",
    "verificationMethod": "did:key:z6Mk...alice",
    "created": "2026-04-13T10:00:00Z",
    "proofPurpose": "assertionMethod",
    "proofValue": "z3FX..."
  }
}
```

### Pflichtfelder

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `@context` | Array | W3C VC Context + WoT Vocabulary |
| `type` | Array | Immer `["VerifiableCredential", "WotAttestation"]` |
| `issuer` | DID | Wer macht die Aussage |
| `credentialSubject.id` | DID oder ID | Über wen/was die Aussage ist |
| `credentialSubject.claim` | String | Die Aussage (Freitext) |
| `issuanceDate` | ISO 8601 | Wann die Attestation erstellt wurde |
| `proof` | Object | Ed25519Signature2020 Beweis |

Das ist der vollständige WoT Core. Keine weiteren Pflichtfelder. Extensions fügen Felder über eigene Contexts hinzu (siehe Abschnitt "Drei Schichten").

## Drei Schichten: Core + Extensions

```
┌─────────────────────────────────────────────────────────────┐
│  W3C Verifiable Credentials 2.0                             │
│  @context, type, issuer, credentialSubject, proof            │
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

Jede Implementierung MUSS verstehen:

```json
{
  "@context": ["https://www.w3.org/2018/credentials/v1", "https://wot.example/vocab/v1"],
  "type": ["VerifiableCredential", "WotAttestation"],
  "issuer": "did:key:z6Mk...alice",
  "credentialSubject": {
    "id": "did:key:z6Mk...bob",
    "claim": "kann gut programmieren"
  },
  "issuanceDate": "2026-04-13T10:00:00Z",
  "proof": { ... }
}
```

Das ist alles. Issuer, Subject, Claim, Proof. Was man nicht kennt, ignoriert man.

### Real Life Extension

Erweitert den WoT Core um visuelle Darstellung und Event-Bezüge:

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://wot.example/vocab/v1",
    "https://reallife.example/vocab/v1"
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
  "issuanceDate": "2026-04-13T10:00:00Z",
  "proof": { ... }
}
```

Sebastians App sieht: WotAttestation mit Claim "hat am Community-Workshop teilgenommen". Die Felder `display`, `event`, `location` kennt sie nicht — ignoriert sie. Der Claim ist trotzdem verifizierbar.

### Human Money Extension

Erweitert den WoT Core um Vertrauensstufen und Haftung:

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://wot.example/vocab/v1",
    "https://humanmoney.example/vocab/v1"
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
  "issuanceDate": "2026-04-13T10:00:00Z",
  "proof": { ... }
}
```

Unsere App sieht: WotAttestation mit Claim "Vertrauensstufe 3". Die Felder `trustLevel`, `liability`, `hopLimit` kennen wir nicht — ignorieren wir. Der Claim ist trotzdem verifizierbar.

Für die effiziente Propagation gebündelter Trust Lists nutzt Human Money Core **SD-JWT** (Selective Disclosure JWT). Damit kann die gesamte Trust List signiert und selektiv weitergegeben werden — ohne die Signatur zu brechen. SD-JWT ist als IETF-Standard kompatibel mit dem kommenden W3C VC-SD Profil. SD-JWT ist nicht Teil des WoT Core — der WoT Core definiert einzelne Attestations als JWS-signierte VCs. SD-JWT ist eine Optimierung für den spezifischen Use Case gebündelter Trust Lists.

### Das Prinzip

Jede App versteht den WoT Core. Was sie nicht kennt, ignoriert sie. Die Signatur ist immer gültig — egal welche Extensions drinstecken. So bleiben alle Implementierungen interoperabel, ohne dass jeder alles verstehen muss.

## Empfängerprinzip

Die Attestation gehört dem Subject. Konkret:

- Der Issuer erstellt und signiert die Attestation
- Die Attestation wird verschlüsselt an den Subject/Holder übermittelt
- Der Holder speichert sie lokal
- Der Holder entscheidet ob er sie akzeptiert und wem er sie zeigt
- Der Issuer behält keine Kopie (kann aber natürlich eine behalten)

### Akzeptanz

Der Holder hat ein lokales `accepted`-Flag pro Attestation. Nicht akzeptierte Attestations sind unsichtbar für Dritte. Das Flag ist **nicht Teil des VC** und wird **nicht signiert** — es ist eine reine lokale Entscheidung.

## Unveränderlichkeit

Attestations sind **unveränderlich.** Einmal signiert, kann der Inhalt nicht geändert werden ohne die Signatur zu brechen.

Wenn sich die Meinung des Issuers ändert, erstellt er eine **neue Attestation:**

```
Januar:  Alice → Bob: "ist zuverlässig"
Juni:    Alice → Bob: "hat mich enttäuscht"
```

Beide Aussagen existieren. Beide sind signiert und wahr — zum jeweiligen Zeitpunkt. Die Trust-Propagation (siehe [Human Money Extension: Trust-Scores](../04-hmc-extensions/humanmoney-trust-scores.md)) berücksichtigt beides — neuere Aussagen wiegen schwerer.

Für formale Widerrufe DARF eine Implementierung den W3C VC `credentialStatus`-Mechanismus nutzen.

## Verifikation

Um eine Attestation zu verifizieren:

1. `@context` und `type` prüfen — enthält es `"WotAttestation"`?
2. `issuer` DID auflösen → Ed25519 Public Key extrahieren
3. `proof` verifizieren gemäß [Spec 002](002-signaturen-und-verifikation.md)
4. `issuanceDate` prüfen — liegt in der Vergangenheit?

Kein externer Service nötig. Alles lokal verifizierbar.

## Austausch-Szenarien

### Freitext-Attestation

Alice öffnet Bobs Profil, schreibt eine Attestation, wählt Emoji + Farbe + Form, signiert, schickt ab. Bob bekommt sie in seiner Inbox.

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

Der Template wird als QR-Code angezeigt. Teilnehmer scannen ihn, authentifizieren sich mit ihrer DID, und der Organisator stellt die Attestation automatisch aus — signiert mit seiner DID.

### Badges / Quests

Ein Quest-System definiert Attestation-Templates für Achievements. Wer ein Quest absolviert, bekommt automatisch die entsprechende Badge-Attestation — ausgestellt vom Quest-Ersteller.

## Subjects

Das `credentialSubject.id` kann verschiedene Dinge identifizieren:

- **Person:** `did:key:z6Mk...` — die häufigste Verwendung
- **Projekt, Ort, Veranstaltung:** ID-Format wird in zukünftigen Dokumenten spezifiziert

## Aktuelle Implementierungen

| | WoT Core | Utopia Map | Human Money Core | Spec |
|---|---|---|---|---|
| **Format** | Eigenes JSON | Directus API | SD-JWT Trust List | ✅ W3C VC |
| **Claim** | `claim: string` | `text: string` | Trust-Level 0-3 | ✅ `claim` Freitext |
| **Visuell** | Keine | emoji + color + shape | Keine | ✅ `display` Objekt |
| **Signatur** | Ed25519Signature2020 | Keine (Directus Auth) | Ed25519 in SD-JWT | ✅ Ed25519Signature2020 |
| **Speicherort** | Empfänger | Server (Directus) | Lokale Trust List | ✅ Empfänger (Holder) |

## Offene Fragen

### 1. WoT Vocabulary URI

`"https://wot.example/vocab/v1"` ist ein Platzhalter. Wir brauchen eine echte URI für unser JSON-LD Vocabulary.

### 2. Subjects jenseits von Personen

Wie identifizieren wir Projekte, Orte, Veranstaltungen als Subjects? Der W3C VC Standard erlaubt jede URI als `credentialSubject.id` — DIDs, UUIDs (`urn:uuid:...`), URLs. Die konkrete Entscheidung welches Format für welchen Subject-Typ verwendet wird steht noch aus.

### 3. Claim-Link Protokoll

Wie funktioniert der QR-Code-basierte Claim-Link technisch? Offene Design-Fragen:
- Enthält der QR-Code das Attestation-Template direkt oder eine URL?
- Wie authentifiziert sich der Scanner (DID-Austausch)?
- Wer signiert — das Handy des Organisators, sein Broker, oder ein delegiertes Device?
- Funktioniert es offline (Bluetooth/LAN) oder nur online?
