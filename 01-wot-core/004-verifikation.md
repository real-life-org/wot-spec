# WoT Spec 004: Verifikation

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-16

## Zusammenfassung

Dieses Dokument spezifiziert wie zwei Menschen einander ihre Identität beweisen — bei einem physischen Treffen oder über einen vertrauenswürdigen Kanal. Die Verifikation ist die Grundlage für das Web of Trust: erst nach gegenseitigem Identitätsbeweis können Attestations ausgestellt werden.

## Referenzierte Dokumente

- [Core 001: Identität](001-identitaet-und-schluesselableitung.md) — DID, Ed25519 Public Key
- [Core 002: Signaturen](002-signaturen-und-verifikation.md) — JWS, Ed25519
- [Core 003: Attestations](003-attestations.md) — Verifiable Credentials

## Grundprinzip

```
Alice und Bob treffen sich
  → tauschen ihre DIDs aus (QR-Code)
  → beweisen dass sie den Private Key besitzen (Challenge-Response)
  → erstellen gegenseitige Verification-Attestations
```

Die Verifikation beweist: **"Diese Person kontrolliert diesen Private Key."** Nicht mehr, nicht weniger. Was danach passiert (Attestations, Einladungen, Trust-Bewertungen) baut darauf auf.

## QR-Code-Format

Der QR-Code enthält die Informationen die der Gegenüber braucht um eine Verbindung herzustellen:

```json
{
  "did": "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
  "name": "Alice",
  "brokerUrl": "wss://broker.example.com"
}
```

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `did` | DID | Ja | Die DID des Users (enthält den Public Key) |
| `name` | String | Ja | Anzeigename |
| `brokerUrl` | URL | Nein | Broker-URL für die Zustellung von Nachrichten |

Der QR-Code enthält den JSON-String direkt (kein URL-Encoding, keine externe URL). Damit funktioniert der Austausch offline — ohne Internet, ohne Broker, ohne Server.

**Warum kein separater Public Key?** Der Public Key ist in der `did:key` kodiert — er muss nicht zusätzlich übertragen werden.

## Challenge-Response-Verifikation

Nach dem QR-Code-Scan beweisen beide Parteien dass sie den Private Key zu ihrer DID besitzen.

### Ablauf

```
1. Alice scannt Bobs QR-Code → kennt Bobs DID
2. Bob scannt Alices QR-Code → kennt Alices DID

3. Alice generiert eine Nonce (32 Bytes, zufällig)
4. Alice signiert die Nonce mit ihrem Private Key (JWS)
5. Alice sendet an Bob: { nonce, signedNonce (JWS) }

6. Bob verifiziert: 
   - Signatur gültig? (Public Key aus Alices DID)
   - Ja → Alice kontrolliert den Private Key zu ihrer DID

7. Bob macht dasselbe in die andere Richtung
```

### Challenge-Nachricht

Die Challenge wird als JWS signiert (wie alle signierten Daten im Protokoll):

**JWS-Payload:**

```json
{
  "type": "verification-challenge",
  "fromDid": "did:key:z6Mk...alice",
  "toDid": "did:key:z6Mk...bob",
  "nonce": "<32 Bytes, Base64URL-kodiert>",
  "timestamp": "2026-04-16T10:00:00Z"
}
```

Der Empfänger prüft:

1. Ist die JWS-Signatur gültig für `fromDid`? (inklusive `alg=EdDSA` Whitelist, siehe [Core 002](002-signaturen-und-verifikation.md#algorithmus-validierung-muss))
2. Ist der `timestamp` aktuell (nicht älter als 5 Minuten)?
3. Ist `toDid` meine eigene DID?
4. Wurde diese `nonce` noch nicht verwendet? (Nonce-History, siehe unten)

Wenn alle vier Prüfungen bestehen, ist die Identität des Gegenübers verifiziert.

### Nonce-History (MUSS)

Empfänger MÜSSEN eine Liste bereits gesehener Nonces führen um Replay-Angriffe zu verhindern. Ohne diese Prüfung könnte ein Angreifer eine aufgezeichnete gültige Challenge erneut vorlegen.

**Anforderungen:**

- Mindest-Retention: 24 Stunden (länger als das Challenge-Zeitfenster von 5 Minuten mit großer Sicherheitsmarge)
- Nonce-Storage kann volatil sein (In-Memory reicht) wenn das Device keine lang-laufenden Sessions unterstützt
- Bei Neustart: sicherer Fallback ist, alle Challenges der letzten 5 Minuten abzulehnen

**Warum das nötig ist:** Die 32-Byte Zufalls-Nonce macht Kollisionen kryptographisch unwahrscheinlich. Aber bei schwacher RNG (ältere Geräte, eingebettete Systeme) sind Kollisionen möglich. Die Nonce-History ist eine zweite Verteidigungslinie die unabhängig von der RNG-Qualität funktioniert.

```typescript
const seenNonces = new TimedCache<string>(24 * 3600 * 1000)  // 24h TTL

function verifyChallenge(challenge) {
  // ... alg-Check, Signatur-Check, Timestamp-Check, toDid-Check

  if (seenNonces.has(challenge.nonce)) {
    throw new Error('Nonce replay detected')
  }
  seenNonces.add(challenge.nonce)

  return true
}
```

### Transportweg

Die Challenge-Response kann über verschiedene Wege laufen:

- **Lokal (Bluetooth/LAN):** Direkt zwischen den Geräten, kein Internet nötig
- **Über den Broker:** Als Inbox-Nachricht, wenn beide nicht direkt verbunden sind
- **Manuell:** Als kopierbarer Text (z.B. in einem Messenger)

Der Transportweg ist nicht Teil dieser Spezifikation — die Challenge ist selbst-verifizierbar unabhängig vom Übertragungsweg.

## Verification-Attestation

Nach erfolgreicher gegenseitiger Verifikation erstellt jede Partei eine **Verification-Attestation** für die andere:

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
    "claim": "in-person verifiziert"
  },
  "issuanceDate": "2026-04-16T10:00:00Z",
  "proof": { ... }
}
```

Die Verification-Attestation sagt: **"Ich habe diese Person getroffen und ihre Identität verifiziert."** Sie wird wie jede andere Attestation behandelt — der Empfänger (Bob) besitzt sie und entscheidet ob er sie akzeptiert und zeigt (Empfängerprinzip, siehe [Core 003](003-attestations.md)).

## Verifikation ohne physisches Treffen

Für Fälle wo kein Treffen möglich ist (z.B. Empfehlung durch einen gemeinsamen Kontakt):

1. Carol kennt sowohl Alice als auch Bob (bereits verifiziert)
2. Carol teilt Bobs DID mit Alice (oder umgekehrt)
3. Alice und Bob führen die Challenge-Response über den Broker durch
4. Beide erstellen Verification-Attestations

Die Verifikation ist schwächer als bei einem physischen Treffen — sie beweist nur Key-Kontrolle, nicht die physische Identität. Implementierungen DÜRFEN zwischen In-Person- und Remote-Verifikation unterscheiden (z.B. durch verschiedene Claim-Texte).

## Zu klären

- **Claim-Link-Protokoll:** QR-Codes für automatische Badge-Vergabe bei Events (Organisator stellt Attestation-Template bereit, Teilnehmer scannen). Das ist ein verwandtes aber separates Thema — siehe [Core 003, Abschnitt Claim-Link](003-attestations.md#claim-link-qr-code-für-events).
