# WoT Spec 004: Verifikation

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-22
- **Scope:** In-person Verification, QR-Challenges, Nonce-History und Verification-Attestations
- **Depends on:** Core 001, Core 002, Core 003, Core 005
- **Conformance profile:** `wot-core@0.1`

## Zusammenfassung

Dieses Dokument spezifiziert wie zwei Menschen einander ihre Identität beweisen — bei einem physischen Treffen oder über einen vertrauenswürdigen Kanal. Die Verifikation ist die Grundlage für das Web of Trust: erst nach gegenseitigem Identitätsbeweis können Attestations ausgestellt werden.

## Referenzierte Dokumente

- [Core 001: Identität](001-identitaet-und-schluesselableitung.md) — DID, Ed25519 Public Key
- [Core 002: Signaturen](002-signaturen-und-verifikation.md) — JWS, Ed25519
- [Core 003: Attestations](003-attestations.md) — Verifiable Credentials
- [Sync 005: Verschlüsselung](../02-wot-sync/005-verschluesselung.md) — X25519 Encryption Key

## Grundprinzip

```
Alice zeigt ihren QR-Code
  → Bob scannt ihn und bestätigt
  → Bob sendet eine Verification-Attestation an Alice
  → Alice empfängt sie, erkennt die Nonce, bestätigt zurück
  → Gegenseitige Verifikation abgeschlossen
```

Im Normalfall reicht **ein einziger QR-Scan** für eine gegenseitige Verifikation. Die Nonce im QR-Code verbindet Bobs Attestation mit Alices physischer Anwesenheit.

## QR-Code-Format

Jeder User zeigt einen QR-Code, der als Challenge fungiert. Er enthält alle Informationen die der Gegenüber braucht — inklusive Encryption Key und Broker-URL, damit der Flow **komplett offline** funktioniert. DIDComm definiert ein ähnliches Konzept (Out-of-Band Invitation), das aber DID-Resolution voraussetzt und keine Challenge-Nonce enthält. Unser Format ist reicher und offline-tauglicher.

```json
{
  "did": "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
  "name": "Alice",
  "enc": "<Base64URL-kodierter X25519 Public Key, 32 Bytes>",
  "nonce": "<UUID>",
  "ts": "<ISO 8601>",
  "broker": "wss://broker.example.com"
}
```

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `did` | DID | Ja | Die DID des Users (enthält den Ed25519 Signing Key) |
| `name` | String | Ja | Anzeigename |
| `enc` | String | Ja | X25519 Encryption Public Key (Base64URL, 32 Bytes) |
| `nonce` | UUID | Ja | Einmalige Nonce für diese Challenge |
| `ts` | ISO 8601 | Ja | Zeitstempel der Challenge-Erstellung |
| `broker` | URL | Nein | Broker-URL für die Zustellung von Nachrichten |

Der QR-Code enthält den JSON-String direkt (kein URL-Encoding, keine externe URL).

**Warum kein separater Ed25519 Public Key?** Der Signing Key ist in der `did:key` kodiert — er muss nicht zusätzlich übertragen werden.

**Warum `enc`?** Der X25519 Encryption Key wird über einen separaten HKDF-Pfad abgeleitet (siehe [Sync 005](../02-wot-sync/005-verschluesselung.md)) und ist nicht aus der DID ableitbar. Damit hat der Gegenüber nach dem Scan sofort alles was er für verschlüsselte Kommunikation braucht.

### QR-Code-Regenerierung

Der QR-Code MUSS in folgenden Fällen mit neuer Nonce und neuem Timestamp regeneriert werden:

1. **Nach empfangener Verification:** Wenn eine Verification-Attestation eingeht, deren Nonce mit der aktiven Challenge-Nonce matcht, ist die Nonce verbraucht. Der QR-Code muss sofort regeneriert werden, damit die nächste Person eine frische Nonce scannt.
2. **Periodisch:** Der QR-Code SOLLTE auch ohne eingehende Verification regelmäßig regeneriert werden, um die Gültigkeitsdauer eines fotografierten QR-Codes zu begrenzen.

## Verifikations-Flow (Online)

Im Normalfall sind beide Parteien mit einem Broker verbunden. Ein einziger QR-Scan reicht für gegenseitige Verifikation:

### Ablauf

```
1. Alice zeigt ihren QR-Code (Challenge: did, name, enc, nonce, ts, broker)

2. Bob scannt den QR-Code
   → Sieht Alices Name und DID
   → Bestätigt: "Ja, das ist Alice"

3. Bob erstellt eine Verification-Attestation (from: Bob, to: Alice)
   → Die Nonce aus Alices QR-Code fließt in die Attestation-ID ein
   → Bob speichert Alice als Kontakt (DID + enc + Name)
   → Bob sendet die Attestation über den Broker an Alice

4. Alice empfängt die Attestation über den Broker
   → Signatur verifizieren (Ed25519, Public Key aus Bobs DID)
   → Nonce in der Attestation-ID matcht Alices aktive Challenge-Nonce
   → Alice weiß: Bob hat meinen QR-Code physisch gescannt
   → Dialog: "Bob hat dich verifiziert. Bestätigst du Bob?"

5. Alice bestätigt
   → Alice erstellt eine Gegen-Verification-Attestation (from: Alice, to: Bob)
   → Alice speichert Bob als Kontakt
   → Alice sendet die Attestation über den Broker an Bob

6. Gegenseitige Verifikation abgeschlossen
```

### Warum die Nonce entscheidend ist

Die Nonce verbindet die digitale Attestation mit der physischen Begegnung. Alice zeigt einen QR-Code mit einer Nonce. Bob scannt ihn und baut die Nonce in seine Attestation-ID ein. Wenn Alice eine Attestation empfängt, deren ID ihre aktive Nonce enthält, weiß sie: diese Attestation kommt von jemandem, der gerade physisch ihren QR-Code gescannt hat.

Ohne die Nonce könnte ein Angreifer zu einem beliebigen Zeitpunkt eine Verification-Attestation an Alice senden — ohne physisch anwesend gewesen zu sein.

### Warum kein Challenge-Hash?

Die Verification-Attestation bindet die QR-Challenge **nur über die Nonce**. Ein zusätzlicher Hash über den gesamten QR-Code (`did`, `name`, `enc`, `nonce`, `ts`, `broker`) ist nicht Teil der Phase-1-Spec.

Grund: Ein solcher Hash wäre nur prüfbar, solange der Empfänger die exakte aktive Challenge noch lokal hält — inklusive exakt serialisiertem Timestamp. Nach Verbrauch der Nonce wird diese Challenge nicht persistiert und soll auch nicht dauerhaft Teil der öffentlichen Attestation werden. Für spätere Dritte hätte der Hash keinen verifizierbaren Wert, weil ihnen die ursprüngliche Challenge nicht vorliegt.

Die Sicherheitsgarantie der Online-Verifikation ist deshalb bewusst enger definiert: Die Nonce beweist gegenüber dem Challenge-Ersteller, dass der Attestation-Issuer die aktuell angezeigte Challenge gesehen hat. Sie ist kein dauerhaft extern verifizierbarer Beweis über den gesamten QR-Code-Inhalt.

### Prüfungen beim Empfang

Der Empfänger einer Verification-Attestation prüft:

1. Ist die JWS-Signatur gültig für den `issuer`? (inklusive `alg=EdDSA` Whitelist, siehe [Core 002](002-signaturen-und-verifikation.md#algorithmus-validierung-muss))
2. Enthält die Attestation-ID die aktive Challenge-Nonce?
3. Ist der `ts` aus der Challenge aktuell (nicht älter als 5 Minuten)?

Die aktive Challenge (mindestens `nonce` und `ts`) MUSS nur bis zur Verifikation oder Regenerierung des QR-Codes lokal gehalten werden. Sie MUSS nicht dauerhaft persistiert werden. Bei App-Neustart ist der sichere Fallback, alte aktive Challenges zu verwerfen und einen neuen QR-Code zu erzeugen.

### Nonce-History (MUSS)

Empfänger MÜSSEN eine Liste bereits verwendeter Nonces führen um Replay-Angriffe zu verhindern. Ohne diese Prüfung könnte ein Angreifer eine aufgezeichnete gültige Attestation erneut vorlegen.

**Anforderungen:**

- Mindest-Retention: 24 Stunden
- Nonce-Storage kann volatil sein (In-Memory reicht)
- Bei Neustart: sicherer Fallback ist, alle Challenges der letzten 5 Minuten abzulehnen
- Eine Nonce wird konsumiert sobald eine passende Attestation empfangen wird — sie kann nicht erneut verwendet werden

## Offline-Verifikation (Bidirektionaler QR-Scan)

Wenn kein Broker erreichbar ist (kein Internet, Festivalgelände, Krisenfall), funktioniert die Verifikation über bidirektionalen QR-Scan:

### Ablauf

```
1. Alice zeigt ihren QR-Code
   → Bob scannt, sieht Alices Name und DID
   → Bob bestätigt: "Ja, das ist Alice"
   → Bob speichert Alice als Kontakt (DID + enc + Name)
   → Bob erstellt eine Verification-Attestation für Alice (lokal gespeichert)

2. Bob zeigt seinen QR-Code
   → Alice scannt, sieht Bobs Name und DID
   → Alice bestätigt: "Ja, das ist Bob"
   → Alice speichert Bob als Kontakt (DID + enc + Name)
   → Alice erstellt eine Verification-Attestation für Bob (lokal gespeichert)

3. Sobald beide wieder online sind:
   → Attestations werden über den Broker zugestellt
```

### Unterschiede zum Online-Flow

| | Online (ein QR-Scan) | Offline (zwei QR-Scans) |
|---|---|---|
| QR-Scans nötig | 1 | 2 |
| Nonce-Verifikation | Ja (Nonce-Match beweist physische Anwesenheit) | Nein (menschliche Bestätigung statt Nonce-Match) |
| Zustellung | Sofort über Broker | Verzögert — bei nächster Broker-Verbindung |
| Voraussetzung | Broker erreichbar für mindestens eine Partei | Keine |

Die Offline-Verifikation ist etwas schwächer — sie hat keinen kryptographischen Beweis über die Nonce, dass der Gegenüber den QR-Code tatsächlich gescannt hat. Die Sicherheit liegt allein in der physischen Begegnung. Für den typischen Anwendungsfall (Festival, Workshop, Nachbarschaft) ist das ausreichend.

## Verification-Attestation

Jede Partei erstellt eine Verification-Attestation für die andere — als JWS-signiertes W3C Verifiable Credential 2.0 (VC-JOSE-COSE Profil, siehe [Core 003](003-attestations.md)):

**JWS-Payload:**

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    "https://web-of-trust.de/vocab/v1"
  ],
  "type": ["VerifiableCredential", "WotAttestation"],
  "issuer": "did:key:z6Mk...bob",
  "credentialSubject": {
    "id": "did:key:z6Mk...alice",
    "claim": "in-person verifiziert"
  },
  "validFrom": "2026-04-22T10:00:00Z",

  "iss": "did:key:z6Mk...bob",
  "sub": "did:key:z6Mk...alice",
  "nbf": 1745280000,
  "jti": "urn:uuid:ver-<nonce>-<did-suffix>"
}
```

Die `jti` (Attestation-ID) enthält die Nonce aus dem QR-Code, damit der Empfänger sie seiner aktiven Challenge zuordnen kann.

Die Verification-Attestation sagt: **"Ich habe diese Person getroffen und ihre Identität verifiziert."** Sie wird wie jede andere Attestation behandelt — der Empfänger besitzt sie und entscheidet ob er sie akzeptiert und zeigt (Empfängerprinzip, siehe [Core 003](003-attestations.md)).

### Zustellung

Die Verification-Attestation wird als DIDComm-Nachricht über den Broker zugestellt:

- **Online:** Sofortige Zustellung, Nonce-Match löst Gegen-Verifikation aus
- **Offline:** Lokal gespeichert, bei nächster Broker-Verbindung zugestellt
- **Outbox:** Implementierungen SOLLTEN eine Outbox für nicht-zugestellte Nachrichten führen

## Encryption Key Discovery

Der X25519 Encryption Public Key erreicht andere Teilnehmer auf zwei Wegen:

1. **QR-Code (In-Person):** Das `enc`-Feld im QR-Code — sofort verfügbar, auch offline
2. **Profil-Service (Online):** Veröffentlicht im Nutzerprofil unter `encryptionPublicKey` — für Kontakte die nicht per QR-Code ausgetauscht wurden (z.B. Space-Einladungen über Dritte)

Siehe [Sync 005: Encryption Key Discovery](../02-wot-sync/005-verschluesselung.md#encryption-key-discovery) für Details.

## Verifikation ohne physisches Treffen

Für Fälle wo kein Treffen möglich ist (z.B. Empfehlung durch einen gemeinsamen Kontakt):

1. Carol kennt sowohl Alice als auch Bob (bereits verifiziert)
2. Carol teilt Bobs DID mit Alice (oder umgekehrt)
3. Alice ruft Bobs Profil ab (inkl. Encryption Key) und erstellt eine Verification-Attestation
4. Bob empfängt sie und kann gegenverifizieren (`counterVerify`)

Die Verifikation ist schwächer als bei einem physischen Treffen — sie beweist nur die Empfehlung durch einen gemeinsamen Kontakt, nicht die physische Identität. Implementierungen DÜRFEN zwischen In-Person- und Remote-Verifikation unterscheiden (z.B. durch verschiedene Claim-Texte).
