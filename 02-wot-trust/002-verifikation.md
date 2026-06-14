# WoT Trust 002: Verifikation

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-22
- **Scope:** In-person Verification, QR-Challenges, Nonce-History und Verification-Attestations
- **Depends on:** Identity 001, Identity 002, Trust 001, Identity 003
- **Conformance profile:** `wot-trust@0.1`

## Zusammenfassung

Dieses Dokument spezifiziert wie zwei Menschen einander ihre Identität beweisen — bei einem physischen Treffen oder über einen vertrauenswürdigen Kanal. Die Verifikation ist die Grundlage für das Web of Trust: erst nach gegenseitigem Identitätsbeweis können Attestations ausgestellt werden.

## Referenzierte Dokumente

- [Identity 001: Identität](../01-wot-identity/001-identitaet-und-schluesselableitung.md) — DID, Ed25519 Public Key
- [Identity 002: Signaturen](../01-wot-identity/002-signaturen-und-verifikation.md) — JWS, Ed25519
- [Trust 001: Attestations](001-attestations.md) — Verifiable Credentials
- [Sync 001: Verschlüsselung](../03-wot-sync/001-verschluesselung.md) — X25519 Encryption Key

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

Jeder User zeigt einen QR-Code, der als Challenge fungiert. Er enthält die Informationen, die der Gegenüber für sofortige lokale Verifikation und spätere verschlüsselte Zustellung braucht — insbesondere den Encryption Key und optional eine Broker-URL. DIDComm definiert ein ähnliches Konzept (Out-of-Band Invitation), das aber DID-Resolution voraussetzt und keine Challenge-Nonce enthält. Unser Format ist reicher und offline-tauglicher.

```json
{
  "did": "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
  "name": "Alice",
  "enc": "<Base64URL-kodierter X25519 Public Key, 32 Bytes>",
  "nonce": "<kanonische lowercase UUID v4>",
  "ts": "<ISO 8601>",
  "broker": "wss://broker.example.com"
}
```

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `did` | DID | Ja | Die DID des Users (enthält den Ed25519 Signing Key) |
| `name` | String | Ja | Anzeigename |
| `enc` | String | Ja | X25519 Encryption Public Key (Base64URL, 32 Bytes) |
| `nonce` | UUID v4 | Ja | Einmalige Nonce für diese Challenge |
| `ts` | ISO 8601 | Ja | Zeitstempel der Challenge-Erstellung |
| `broker` | URL | Nein | Broker-URL für die Zustellung von Nachrichten |

Der QR-Code enthält den JSON-String direkt (kein URL-Encoding, keine externe URL).

Das `nonce`-Feld einer QR-Challenge MUSS als kanonische lowercase UUID v4 serialisiert werden: 36 ASCII-Zeichen, Hex-Ziffern `0-9a-f`, Bindestriche in der `8-4-4-4-12`-Gruppierung, Versions-Nibble `4` und Variant-Nibble `8`, `9`, `a` oder `b`. Andere UUID-Versionen, uppercase Hex-Ziffern und nicht-kanonische UUID-Schreibweisen sind im QR-Challenge-Feld ungueltig. Diese Anforderung betrifft die QR-Challenge-Serialisierung; die Verification-Attestation-`jti`-Grammatik wird hier nicht geaendert.

**Warum kein separater Ed25519 Public Key?** Der Signing Key ist in der `did:key` kodiert — er muss nicht zusätzlich übertragen werden.

**Warum `enc`?** Der X25519 Encryption Key wird über einen separaten HKDF-Pfad abgeleitet (siehe [Sync 001](../03-wot-sync/001-verschluesselung.md)) und ist nicht aus der DID ableitbar. Damit hat der Gegenüber nach dem Scan sofort alles was er für verschlüsselte Kommunikation braucht.

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
   → Bob speichert lokal einen Pending-Counter-State fuer diese Attestation
   → Bob sendet die Attestation über den Broker an Alice

4. Alice empfängt die Attestation über den Broker
   → Signatur verifizieren (Ed25519, Public Key aus Bobs DID)
   → Nonce in der Attestation-ID matcht Alices aktive Challenge-Nonce
   → Alice weiß: Bob hat meinen QR-Code physisch gescannt
   → Dialog: "Bob hat dich verifiziert. Bestätigst du Bob?"

5. Alice bestätigt
   → Alice erstellt eine Gegen-Verification-Attestation (from: Alice, to: Bob)
   → Die Gegen-Verification referenziert Bobs Attestation über `inResponseTo`
   → Alice speichert Bob als Kontakt
   → Alice sendet die Attestation über den Broker an Bob

6. Bob empfängt die Gegen-Verification
   → Signatur verifizieren
   → `inResponseTo` matcht Bobs lokalen Pending-Counter-State
   → Pending-Counter-State ist noch nicht abgelaufen
   → Gegenseitige Live-Verifikation abgeschlossen
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

1. Ist die JWS-Signatur gültig für den `issuer`? (inklusive `alg=EdDSA` Whitelist, siehe [Identity 002](../01-wot-identity/002-signaturen-und-verifikation.md#algorithmus-validierung-muss))
2. Bindet die Attestation-ID (`jti`) exakt die aktive Challenge-Nonce gemaess [Verification-Attestation](#verification-attestation)?
3. Ist der `ts` aus der Challenge aktuell (nicht älter als 5 Minuten)?

Die aktive Challenge (mindestens `nonce` und `ts`) MUSS nur bis zur Verifikation oder Regenerierung des QR-Codes lokal gehalten werden. Sie MUSS nicht dauerhaft persistiert werden. Bei App-Neustart ist der sichere Fallback, alte aktive Challenges zu verwerfen und einen neuen QR-Code zu erzeugen.

### Acceptance Gate fuer Online-Verifikation (MUSS)

Eine eingehende Verification-Attestation DARF im Online-Ein-QR-Scan-Flow nur dann als Live-Verifikation akzeptiert oder automatisch zur Gegen-Verifikation angeboten werden, wenn alle Bedingungen erfuellt sind:

1. Die Signatur der Attestation ist gueltig.
2. Die Attestation richtet sich an die lokale DID.
3. Die Attestation-ID (`jti`) bindet exakt eine lokal aktive, noch nicht verbrauchte Challenge-Nonce gemaess der unten definierten `jti`-Grammatik.
4. Die aktive Challenge ist zeitlich gueltig.
5. Die Nonce wurde noch nicht in der Nonce-History konsumiert.

Fehlt eine aktive Challenge-Nonce, MUSS die Attestation als ungebundene (nicht-live) Verifikation behandelt werden. Sie DARF gespeichert oder dem User als separate Anfrage angezeigt werden, aber sie DARF NICHT als Live-Verifikation gelten (keine frische Challenge-Response, also kein Beweis einer Live-Interaktion). Damit wird verhindert, dass beliebige signierte Verification-Attestations als Live-Verifikation in den Trust Graph gelangen.

Der Empfaenger MUSS die Nonce-Bindung ausschliesslich ueber einen Full-String-Match der `jti` pruefen. Unbeschraenkte Substring-Suche nach UUIDs ist ungueltig.

### Gegen-Verifikation und Pending-Counter-State (MUSS)

Der Online-Ein-QR-Scan-Flow benoetigt keinen zweiten QR-Scan. Der zweite QR-Scan wuerde nur erneut kopierbare QR-Daten uebertragen; die Sicherheitsbindung entsteht durch die frische Challenge-Nonce, die Signatur, den lokalen Pending-State und die bewusste Bestaetigung durch den User.

Damit zwei beliebige Verification-Attestations nicht automatisch eine gegenseitige Live-Verifikation ergeben, MUESSEN Implementierungen Gegen-Verifikationen an lokalen State binden:

1. Wenn Bob nach dem Scan von Alices QR-Code eine Verification-Attestation an Alice erstellt, MUSS Bob lokal einen `pendingCounterVerification`-Eintrag speichern.
2. Dieser Eintrag MUSS mindestens enthalten:
   - `counterpartyDid`: Alices DID
   - `originalVerificationId`: die `jti` von Bobs Verification-Attestation
   - `createdAt`: Erstellungszeitpunkt
   - `expiresAt`: Ablaufzeitpunkt des Pending-Counter-Fensters
3. Das Pending-Counter-Fenster DARF hoechstens 24 Stunden betragen. Nach Ablauf MUSS eine eingehende Gegen-Verification als ungebundene (nicht-live) Verifikation behandelt werden oder einen neuen QR-Flow erfordern.
4. Wenn Alice Bobs nonce-gebundene Verification-Attestation akzeptiert und Bob bestaetigt, MUSS Alices Gegen-Verification-Attestation ein Top-Level-Feld `inResponseTo` enthalten. Der Wert MUSS exakt der `jti` von Bobs urspruenglicher Verification-Attestation entsprechen.
5. Wenn Bob Alices Gegen-Verification empfaengt, DARF er sie nur dann als Abschluss einer gegenseitigen Live-Verifikation akzeptieren, wenn alle Bedingungen erfuellt sind:
   - Die Signatur der Gegen-Verification ist gueltig.
   - Die Gegen-Verification richtet sich an Bobs lokale DID.
   - `issuer`/`iss` der Gegen-Verification entspricht `counterpartyDid` im Pending-Counter-State.
   - `inResponseTo` entspricht `originalVerificationId`.
   - Der Pending-Counter-State ist noch nicht abgelaufen.
6. Fehlt `inResponseTo`, fehlt der passende Pending-Counter-State oder ist der Pending-Counter-State abgelaufen, DARF die Gegen-Verification NICHT als gegenseitige Live-Verifikation zaehlen. Sie DARF als ungebundene (nicht-live) Verifikation gespeichert oder angezeigt werden.

Eine Implementierung DARF den Pending-Counter-State kuerzer halten oder den User jederzeit einen neuen QR-Flow starten lassen. Sie DARF ihn jedoch NICHT unbegrenzt als Live-Beweis verwenden.

Hinweis zur Validierbarkeit: JSON-Schema kann nur die Feldform von `inResponseTo` validieren. Die Existenz und Integritaet des lokalen `pendingCounterVerification`-Eintrags, `inResponseTo`-Exact-Match, `issuer`/`iss`-Bindung an `counterpartyDid`, lokale DID-Bindung und `expiresAt`-Ablaufpruefung sind zustands- und zeitabhaengig. Sie MUESSEN durch Laufzeitlogik und Conformance-Tests mit kontrolliertem lokalen State und kontrollierter Uhr geprueft werden.

### Nonce-History (MUSS)

Empfänger MÜSSEN eine Liste bereits verwendeter Nonces führen um Replay-Angriffe zu verhindern. Ohne diese Prüfung könnte ein Angreifer eine aufgezeichnete gültige Attestation erneut vorlegen.

**Anforderungen:**

- Mindest-Retention: 24 Stunden
- Nonce-Storage kann volatil sein (In-Memory reicht)
- Bei Neustart: sicherer Fallback ist, alle Challenges der letzten 5 Minuten abzulehnen
- Eine Nonce wird konsumiert sobald eine passende Attestation empfangen wird — sie kann nicht erneut verwendet werden
- Die Nonce-History MUSS dieselbe normalisierte Nonce verwenden, die aus der `jti` extrahiert und mit der aktiven Challenge verglichen wurde.
- Wenn eine spaetere Attestation eine gueltige `jti`-Grammatik hat und ihre normalisierte Nonce bereits in der Nonce-History steht, MUSS sie als `nonce-consumed` abgelehnt werden, auch wenn gerade keine aktive Challenge mit dieser Nonce existiert.

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

Jede Partei erstellt eine Verification-Attestation für die andere — als JWS-signiertes W3C Verifiable Credential 2.0 (VC-JOSE-COSE Profil, siehe [Trust 001](001-attestations.md)):

**JWS-Payload:**

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    "https://web-of-trust.de/vocab/v1"
  ],
  "type": ["VerifiableCredential", "WotAttestation", "WotVerification"],
  "issuer": "did:key:z6Mk...bob",
  "credentialSubject": {
    "id": "did:key:z6Mk...alice",
    "claim": "in-person verifiziert"
  },
  "validFrom": "2026-04-22T10:00:00Z",

  "iss": "did:key:z6Mk...bob",
  "sub": "did:key:z6Mk...alice",
  "nbf": 1776852000,
  "jti": "urn:uuid:550e8400-e29b-41d4-a716-446655440000"
}
```

Eine **Live-Verifikation** ist eine nonce-gebundene Verifikation: ihre `jti` bindet eine frische Challenge-Nonce gemäß Acceptance Gate und beweist damit eine **frische Live-Interaktion zu einem Zeitpunkt** — nicht physische Präsenz. (Physische Anwesenheit ist die intendierte Nutzung der QR-Zeremonie, aber kein kryptographischer Beweis.)

Eine Live-Verifikation wird als `WotAttestation` mit dem zusätzlichen `type`-Eintrag `WotVerification` ausgestellt. Dieser `type`-Eintrag ist der **normative Diskriminator** einer Live-Verifikation. Alle Attestation-Regeln aus [Trust 001](001-attestations.md) gelten unverändert, da das `type`-Array weiterhin `WotAttestation` enthält. Der `credentialSubject.claim`-Text (z.B. `"in-person verifiziert"`) ist ein menschenlesbares, frei lokalisierbares Label und DARF NICHT als Diskriminator verwendet werden. Clients und Broker MÜSSEN Live-Verifikationen über den `WotVerification`-`type`-Eintrag erkennen, nicht über den `claim`-Wert.

Eine **ungebundene (nicht-live) Verifikation** — ohne frische Challenge-Nonce, z.B. eine Empfehlung ohne Live-Austausch (siehe [Verifikation ohne physisches Treffen](#verifikation-ohne-physisches-treffen)) — trägt `WotVerification` **NICHT** und ist eine gewöhnliche `WotAttestation`.

Die `jti` (Attestation-ID) einer online nonce-gebundenen Verification-Attestation MUSS die Nonce aus dem QR-Code exakt in dieser Form binden:

```abnf
verification-jti = %s"urn:uuid:" uuid
uuid = 8HEXDIG "-" 4HEXDIG "-" 4HEXDIG "-" 4HEXDIG "-" 12HEXDIG
```

Der Literal-Prefix `urn:uuid:` in `verification-jti` ist case-sensitiv und MUSS exakt lowercase geschrieben sein. Das ABNF verwendet deshalb den case-sensitiven Literal-Marker `%s`; Implementierungen DUERFEN nicht die standardmaessige case-insensitive ABNF-Literal-Semantik auf den Prefix anwenden. Der `uuid`-Teil MUSS genau die QR-Challenge-Nonce sein. Implementierungen MUESSEN die `jti` gegen den gesamten String matchen, die UUID-Gruppe extrahieren und fuer Vergleich sowie Nonce-History auf Kleinbuchstaben normalisieren. UUID-Buchstaben `A-F` in der `jti` sind deshalb gueltig, solange der normalisierte Wert exakt der lokal aktiven Challenge-Nonce entspricht.

Fuer das Acceptance Gate gilt:

| Eingehende `jti` | Ergebnis |
|---|---|
| `urn:uuid:<active-nonce>` mit beliebiger UUID-Gross-/Kleinschreibung | als nonce-gebundene Live-Verifikation akzeptierbar, wenn alle anderen Gates erfuellt sind |
| `urn:uuid:<consumed-nonce>` | als `nonce-consumed` ablehnen |
| `urn:uuid:<uuid>`, aber UUID ist weder aktive noch konsumierte Nonce | als ungebundene Remote-Verifikation behandeln |
| `URN:UUID:<uuid>` oder `Urn:Uuid:<uuid>` mit uppercase oder mixed-case Prefix | als ungebundene (nicht-live) Verifikation behandeln; nicht als Live-Verifikation akzeptieren und nicht als `nonce-consumed` ablehnen |
| `jti` mit mehreren UUID-foermigen Tokens | als ungebundene Remote-Verifikation behandeln |
| `jti` mit zusaetzlichem Prefix/Suffix, falschem URN-Namespace oder ungueltigen Trennzeichen | als ungebundene Remote-Verifikation behandeln |

Eine `jti` wie `urn:uuid:ver-<nonce>-<did-suffix>` ist fuer Trust 002 nonce-gebundene Verification-Attestations ungueltig, weil sie weder eine gueltige UUID-URN noch eine eindeutige Nonce-Bindung ist.

Bei einer Gegen-Verification enthält `jti` eine neue eindeutige ID der Gegen-Verification, z.B. `urn:uuid:123e4567-e89b-12d3-a456-426614174000`. Das optionale Feld `inResponseTo` MUSS gesetzt werden, wenn die Attestation als Gegen-Verification im Online-Ein-QR-Scan-Flow akzeptiert werden soll. `inResponseTo` referenziert die `jti` der urspruenglichen nonce-gebundenen Verification-Attestation, z.B. `urn:uuid:550e8400-e29b-41d4-a716-446655440000`.

Die Verification-Attestation sagt: **"Ich habe diese Person getroffen und ihre Identität verifiziert."** Sie wird wie jede andere Attestation behandelt — der Empfänger besitzt sie und entscheidet ob er sie akzeptiert und zeigt (Empfängerprinzip, siehe [Trust 001](001-attestations.md)).

### Zustellung

Die Verification-Attestation wird als DIDComm-Nachricht über den Broker zugestellt:

- **Online:** Sofortige Zustellung, Nonce-Match löst Gegen-Verifikation aus
- **Offline:** Lokal gespeichert, bei nächster Broker-Verbindung zugestellt
- **Outbox:** Implementierungen SOLLTEN eine Outbox für nicht-zugestellte Nachrichten führen

## Encryption Key Discovery

Der X25519 Encryption Public Key erreicht andere Teilnehmer auf zwei Wegen:

1. **QR-Code (In-Person):** Das `enc`-Feld im QR-Code — sofort verfügbar, auch offline
2. **Profil-Service (Online):** Über `didDocument.keyAgreement` — für Kontakte die nicht per QR-Code ausgetauscht wurden (z.B. Space-Einladungen über Dritte)

Siehe [Sync 001: Encryption Key Discovery](../03-wot-sync/001-verschluesselung.md#encryption-key-discovery) für Details.

## Verifikation ohne physisches Treffen

Für Fälle wo kein Treffen möglich ist (z.B. Empfehlung durch einen gemeinsamen Kontakt):

1. Carol kennt sowohl Alice als auch Bob (bereits verifiziert)
2. Carol teilt Bobs DID mit Alice (oder umgekehrt)
3. Alice ruft Bobs Profil ab (inkl. Encryption Key) und erstellt eine Verification-Attestation
4. Bob empfängt sie und kann gegenverifizieren (`counterVerify`)

Diese Verifikation ist schwächer — sie beweist nur die Empfehlung durch einen gemeinsamen Kontakt, weder physische Identität noch eine Live-Interaktion. Sie ist **ungebunden (nicht-live)**: ihre `jti` bindet keine frische Challenge-Nonce. Eine ungebundene Verifikation trägt deshalb **kein** `WotVerification` und ist eine gewöhnliche `WotAttestation` (Discovery: `/p/{did}/a`, nicht `/p/{did}/v` — siehe [Sync 004](../03-wot-sync/004-discovery.md)). Ob nonce-gebunden (live) oder ungebunden, entscheidet die `jti` gemäß Acceptance Gate, NICHT der `claim`-Text. Soll eine ungebundene Verifikation später maschinell als eigene Klasse unterscheidbar sein, erfordert das einen eigenen strukturierten `type`-Eintrag analog `WotVerification` — kein freier Claim-Text.
