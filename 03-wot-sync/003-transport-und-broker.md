# WoT Sync 003: Transport und Broker

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-13
- **Scope:** Broker, Transport, Capabilities, DIDComm-kompatible Plaintext Envelopes und P2P-Sync
- **Depends on:** Identity 002, Trust 002, Identity 003, Sync 001, Sync 002, Sync 005, Sync 006
- **Conformance profile:** `wot-sync@0.1`

## Zusammenfassung

Dieses Dokument spezifiziert wie Daten zwischen Peers transportiert werden und wie Broker als immer-online Peers funktionieren. Ein Broker ist kein spezieller Server — er ist ein Peer der zufällig immer online ist und Push-Notifications verschicken kann.

## Referenzierte Standards

- **WebSocket** (RFC 6455) — Primärer Transportkanal
- **DIDComm v2** (DIF) — kompatibler Plaintext Message Envelope am Transportrand (keine DIDComm-JWE/Authcrypt-Verschlüsselung)
- **Ed25519** (RFC 8032) — Signatur im Message Envelope
- **ECIES** (siehe [Sync 001](001-verschluesselung.md)) — 1:1-Verschlüsselung für Inbox-Nachrichten

## Broker

Ein Broker ist ein immer erreichbarer Peer für Store-and-Forward, Log-Sync, Device-Inboxen und Push-Signale. Broker speichern nur verschlüsselte Inhalte und Autorisierungs-Metadaten:

- verschlüsselte Log-Einträge für Dokumente (siehe [Sync 002](002-sync-protokoll.md))
- verschlüsselte Inbox-Nachrichten pro Device
- Capabilities für Dokumentzugriff
- Device-Registrierungen pro DID
- Push-Endpoints

Broker sehen keinen Klartext, keine Inbox-Inhalte und keine Space-Mitgliederlisten. Ein einzelner Broker kann Nachrichten zurückhalten; Clients mit höheren Sicherheitsanforderungen SOLLTEN mehrere Broker parallel nutzen und Heads vergleichen (siehe [Sync 002](002-sync-protokoll.md#censorship--und-split-brain-detection)).

Das Sync-Protokoll selbst ist peer-agnostisch. Die Broker-Schicht ergänzt Authentisierung, Capability-Prüfung, Store-and-Forward und Push. Im direkten P2P-Modus fällt diese Broker-Schicht weg; P2P-Authentisierung ist in [Direkter P2P-Sync](#direkter-p2p-sync) spezifiziert.

## Authentisierung

Beim Verbindungsaufbau zum Broker authentifiziert sich der Client via **Challenge-Response**:

```
1. Client verbindet sich (WebSocket)
2. Client sendet: { type: "register", did: "did:key:z6Mk...", deviceId: "uuid" }
3. Broker generiert zufällige Nonce (32 Bytes)
4. Broker sendet: { type: "challenge", nonce: "<Base64URL>" }
5. Client signiert die Nonce mit Ed25519 Private Key
6. Client sendet: { type: "challenge-response", did, deviceId, nonce, signature }
7. Broker verifiziert:
   - DID auflösen → Public Key
   - Signatur über Nonce prüfen
   - OK → Verbindung authentifiziert
8. Broker sendet: { type: "registered", did, deviceId }
```

Nach dem Handshake ist die WebSocket-Verbindung authentifiziert. Alle weiteren Nachrichten auf dieser Verbindung gelten als von dieser DID + deviceId kommend.

Die Device-ID (`deviceId`) identifiziert das Gerät stabil — derselbe Wert wie im Sync-Protokoll ([Sync 002](002-sync-protokoll.md#device-identifikation)).

### Nonce-Handling (MUSS)

Die Challenge-Nonce in der Broker-Authentisierung MUSS denselben Replay-Schutz-Regeln folgen wie die Verifikations-Challenge in [Trust 002](../02-wot-trust/002-verifikation.md#nonce-history-muss):

- Broker MÜSSEN bereits verwendete Nonces für mindestens 24 Stunden speichern
- Eine Nonce DARF nur einmal akzeptiert werden
- Nonces MÜSSEN mindestens 32 Bytes aus einer kryptographisch sicheren Zufallsquelle haben
- Clients MÜSSEN die Nonce direkt nach Empfang signieren (keine späteren Signaturen auf wiederverwendeten Nonces)

## Device-Registrierung

Der Broker MUSS pro DID eine Liste der zugehörigen Device-IDs führen. Das ist notwendig für:

- **Sequenzierte Log-Einträge** — jeder Log-Eintrag ist identifiziert durch `(deviceId, docId, seq)` (siehe [Sync 002](002-sync-protokoll.md))
- **Nonce-Konstruktion** — die deterministische AES-GCM-Nonce basiert auf `(deviceId, seq)` (siehe [Sync 001](001-verschluesselung.md#nonce-konstruktion))
- **Store-and-Forward pro Device** — Inbox-Nachrichten müssen jedem Device zugestellt werden, auch wenn es vorübergehend offline ist

### Erstregistrierung

Wenn ein Client mit einer `(did, deviceId)`-Kombination verbindet, die der Broker noch nicht kennt:

1. Broker führt normale Challenge-Response durch (siehe oben)
2. Nach erfolgreicher Authentisierung: Broker prüft, ob `deviceId` bereits für eine **andere DID** registriert ist
   - Falls ja: **Ablehnen** mit `DEVICE_ID_CONFLICT` — Device-IDs MÜSSEN global eindeutig sein
3. Broker prüft, ob `deviceId` für diese DID in einer Revocation-Liste steht
   - Falls ja: **Ablehnen** mit `DEVICE_REVOKED`
4. Broker trägt `(did, deviceId)` dauerhaft in seine Device-Liste ein
5. Broker antwortet mit `{ type: "registered", did, deviceId, isNewDevice: true }`

### Erneute Verbindung eines bekannten Devices

Wenn derselbe `(did, deviceId)` wiederkommt:

1. Challenge-Response wie gewohnt
2. Broker erkennt die Kombination als bekannt
3. Broker antwortet mit `{ type: "registered", did, deviceId, isNewDevice: false }`
4. Broker liefert ausstehende Nachrichten aus der Device-Inbox aus

### Device-Deaktivierung

Device-Deaktivierung wird über eine **signierte Revocation-Nachricht** kommuniziert:

```json
{
  "type": "device-revoke",
  "did": "did:key:z6Mk...alice",
  "deviceId": "<UUID zu entfernen>",
  "revokedAt": "2026-04-22T10:00:00Z"
}
```

Signiert mit dem Identity Key der angegebenen DID. Der Broker MUSS prüfen:

1. JWS-Signatur gültig gegen den Ed25519-Key aus `did`
2. Der Broker markiert `(did, deviceId)` als `revoked`
3. Ausstehende Inbox-Nachrichten für dieses Device werden gelöscht
4. Zukünftige Verbindungsversuche mit dieser Kombination werden mit `DEVICE_REVOKED` abgelehnt

**Limitation im Shared-Seed-Modell:** Wer den Seed hat, kann eine neue `deviceId` generieren und sich als "neues Device" registrieren. Device-Deaktivierung schützt nicht gegen Seed-Kompromittierung — siehe [Identity 001](../01-wot-identity/001-identitaet-und-schluesselableitung.md#multi-device--shared-seed-modell). Für echten Schutz muss die Identität rotiert werden.

### Device-Liste im Broker

Der Broker speichert pro DID mindestens `deviceId`, `firstSeenAt`, `lastSeenAt`, `status` (`active` oder `revoked`) und optional `revokedAt`. Diese Liste ist Broker-Metadatum und liegt im Klartext vor.

### Race Conditions

Der Broker MUSS Revocations atomisch anwenden. Wenn Registrierung und Revocation für dieselbe `deviceId` konkurrieren, gewinnt die Revocation und die Registrierung wird mit `DEVICE_REVOKED` abgelehnt. Ist eine `deviceId` bereits für eine andere DID registriert, MUSS der Broker mit `DEVICE_ID_CONFLICT` ablehnen.

## Store-and-Forward pro Device

Inbox-Nachrichten werden **pro Device** zwischengespeichert, nicht pro DID. Das garantiert, dass jedes Device die für es bestimmten Nachrichten erhält, auch wenn es vorübergehend offline ist.

### Zustellungs-Regeln

1. Eine Inbox-Nachricht an DID X wird für **jedes aktive Device** dieser DID in die Inbox gelegt
2. Ein Device acknowledged die Nachricht mit `{ type: "ack", messageId: "..." }`
3. Die Nachricht wird aus der Inbox dieses Devices gelöscht — sie bleibt aber in den Inboxen anderer Devices, die noch nicht ACKt haben
4. Wenn **alle aktiven Devices** ACKt haben, ist die Nachricht vollständig zugestellt
5. Deaktivierte Devices werden bei der Zustellung ignoriert (und ihre Inbox-Einträge gelöscht)

Bei selbstadressierten Inbox-Nachrichten, deren `from` und `to` zur selben DID gehoeren, z.B. Cross-Device-Sync, MUSS der Broker die sendende `(did, deviceId)`-Verbindung von der Zustellung ausschliessen. Das sendende Device hat die lokale Aenderung bereits angewendet; ein ACK des sendenden Devices DARF niemals Inbox-Eintraege fuer andere Devices derselben DID loeschen.

ACKs sind pro Device scoped. Ein Broker MUSS ein ACK nur fuer die Inbox des authentifizierten `(did, deviceId)` anwenden. Ein ACK von Device A DARF keine Nachricht fuer Device B loeschen, auch wenn beide Devices dieselbe DID verwenden.

### Retention und Garbage Collection

- Nachrichten, die älter sind als ein definiertes TTL (z.B. 30 Tage) werden auch ohne ACK gelöscht — Implementierer dürfen das konfigurieren
- Wenn ein Device für längere Zeit (z.B. 90 Tage) nicht verbindet, DARF der Broker es als inaktiv behandeln und seine ausstehenden Nachrichten löschen
- Für kritische Nachrichten (Space-Einladungen, Key-Rotationen) SOLLTE der Sender einen Liefernachweis implementieren (z.B. erneutes Senden nach Timeout)

Der pro-Device-Zustellpfad stellt sicher, dass jedes aktive Device kritische Nachrichten wie Space-Einladungen und Key-Rotationen mindestens einmal erhält.

## Autorisierung (Capabilities)

Der Broker ist E2EE — er kann die Mitgliederliste eines Space nicht lesen (verschlüsselt mit dem Space Content Key). Deshalb braucht er einen externen Beweis, dass ein Client auf ein Dokument zugreifen darf.

### Space-Schlüssel am Broker

Der Broker kennt pro Space den `spaceCapabilityVerificationKey` für Capability-Prüfung und die `adminDid(s)` für Broker-Management-Nachrichten. Members signieren Capabilities mit dem geteilten `spaceCapabilitySigningKey`; Admins signieren Rotation und Admin-Wechsel mit ihrem abgeleiteten Admin Key (siehe [Sync 005](005-gruppen.md#admin-key-ableitung)).

### Capability-Format

Eine Capability ist ein JWS, signiert mit dem **Space Capability Signing Key**:

**JWS-Payload:**

```json
{
  "type": "capability",
  "spaceId": "7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b",
  "audience": "did:key:z6Mk...bob",
  "permissions": ["read", "write"],
  "generation": 3,
  "issuedAt": "2026-04-22T10:00:00Z",
  "validUntil": "2026-10-22T10:00:00Z"
}
```

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `spaceId` | UUID | Ja | Für welchen Space die Capability gilt |
| `audience` | DID | Ja | Für welchen User die Capability gilt |
| `permissions` | Array | Ja | Erlaubte Operationen (`read`, `write`) |
| `generation` | Integer | Ja | Space Capability Key Pair Generation zu der die Capability gehört |
| `issuedAt` | ISO 8601 | Ja | Erstellungszeitpunkt |
| `validUntil` | ISO 8601 | Ja | Ablaufzeitpunkt — nach diesem Moment ist die Capability ungültig |

Der JWS wird mit dem Space Capability Signing Key signiert. Der `kid` im JWS-Header MUSS den Space-Kontext und die Capability-Key-Generation referenzieren: `wot:space:<spaceId>#cap-<generation>`. Der Broker verifiziert mit dem aktuellen Space Capability Verification Key für genau diesen Space und diese Generation.

**Empfohlene Gültigkeitsdauer:**

- Normale Spaces: 6 Monate
- Hochsensitive Spaces: 1 Monat oder kürzer
- Persönliches Dokument (self-issued): 1 Jahr

### Capability-Verteilung

Capabilities werden zusammen mit den Space-Schlüsseln verteilt:

- **Bei Einladung:** Der Einladende signiert eine Capability mit dem `spaceCapabilitySigningKey` für den Eingeladenen. Die `space-invite` Inbox-Nachricht enthält Space Content Key, Capability Signing Key und Capability ([Sync 005](005-gruppen.md)).
- **Bei Key-Rotation (Member-Entfernung):** Der Admin generiert einen neuen Space Content Key und ein neues Capability Key Pair. Alle verbleibenden Members bekommen neuen Content Key + neuen Capability Signing Key + neue Capability.
- **Vor Ablauf:** Jedes Mitglied kann sich selbst (oder Peers) eine erneuerte Capability ausstellen, solange der aktuelle `spaceCapabilitySigningKey` gültig ist.

### Capability-Prüfung am Broker

Wenn ein Client ein Dokument syncen will:

1. Client sendet seine Capability
2. Broker prüft:
   - JWS-Signatur gültig gegen den aktuellen `spaceCapabilityVerificationKey`? (inklusive `alg=EdDSA`, siehe [Identity 002](../01-wot-identity/002-signaturen-und-verifikation.md#algorithmus-validierung-muss))
   - `audience` = authentifizierte DID?
   - `spaceId` = angefragter Space?
   - `generation` = aktuelle Capability-Key-Generation? (alte Capabilities werden damit implizit widerrufen)
   - `now < validUntil`? (nicht abgelaufen)
3. OK → Sync erlaubt

`validUntil` begrenzt Zugriffsrechte ohne explizite Rotation. Aktive Members bekommen rechtzeitig eine erneuerte Capability; inaktive Members verlieren den Broker-Zugriff automatisch.

### Capability-Widerruf über Rotation

Bei Member-Entfernung rotiert der Admin das **Space Capability Key Pair**. Der Broker akzeptiert ab dem Moment nur Capabilities die gegen den neuen `spaceCapabilityVerificationKey` verifizierbar sind — alle alten Capabilities werden automatisch ungültig.

Der Admin sendet dem Broker eine `space-rotate`-Nachricht:

```json
{
  "type": "space-rotate",
  "spaceId": "7f3a2b10-...",
  "newPublicKey": "<base64url>",
  "newGeneration": 4
}
```

Signiert mit dem **Admin Key** (space-spezifisch abgeleitet). Der Broker akzeptiert die Nachricht nur wenn der Admin Key zur registrierten Admin-Liste dieses Space gehört.

### Admin-Management

Admins können weitere Admins hinzufügen oder entfernen:

```json
{
  "type": "admin-add",
  "spaceId": "7f3a2b10-...",
  "newAdminDid": "did:key:z6Mk...derived-for-space"
}
```

```json
{
  "type": "admin-remove",
  "spaceId": "7f3a2b10-...",
  "removedAdminDid": "did:key:z6Mk...derived-for-space"
}
```

Beide Nachrichten müssen mit einem **bestehenden Admin Key** für diesen Space signiert sein.

### Persönliche Dokumente

Für das persönliche Dokument (Identität, Keys) stellt der User sich seine eigene Capability aus. Das persönliche Dokument hat kein Space Capability Key Pair — stattdessen signiert der User die Capability direkt mit seinem **Identity Key** (DID). Der Broker prüft: `issuer` = `audience` = authentifizierte DID.

**Unterschied zum Space-Capability-Modell:** Bei Spaces signiert der geteilte `spaceCapabilitySigningKey`, bei Personal Docs signiert der persönliche Identity Key (DID). Das ist eine bewusste Vereinfachung — ein Personal Doc hat genau einen Eigentümer, kein Gruppen-Key-Management nötig. Die Capability-Felder (`spaceId`, `generation`, `validUntil`) werden analog verwendet, aber `spaceId` wird durch die deterministische Personal-Doc-ID ersetzt (siehe [Sync 006](006-personal-doc.md)).

## Broker-Kanäle

Der Broker bietet zwei Kanäle:

- **Log-Sync:** Pull-basierter Austausch von Log-Einträgen für Dokumente. Der Broker kann verbundene Clients über neue Einträge informieren.
- **Inbox:** Store-and-Forward für direkte verschlüsselte Nachrichten. Inbox-Nachrichten werden pro aktivem Device vorgehalten und erst nach ACK des jeweiligen Devices gelöscht.

## WoT Message Envelope (DIDComm-kompatibel)

WoT-Peer-Nachrichten (über Broker oder direkt) verwenden einen eigenen **WoT Message Envelope**, dessen Plaintext-Form absichtlich mit dem DIDComm v2 Plaintext Message Format ([DIF DIDComm Messaging v2](https://identity.foundation/didcomm-messaging/spec/v2.0/)) kompatibel ist. Der Kompatibilitaetsanspruch ist bewusst eng: etablierte DIDComm-v2-Libraries sollen Plaintext-Envelopes parsen und routen koennen. WoT uebernimmt nicht den DIDComm-Crypto-Stack, keine DIDComm-JWE/Authcrypt-Verschluesselung und keine Mediator-Protokolle.

Persistente WoT-Objekte (Attestation-JWS, Capability-JWS, Log-Entry-JWS, verschlüsselte Dokument-Payloads) sind **keine DIDComm Messages**. Sie DÜRFEN im `body` eines WoT Plaintext Envelopes transportiert werden. Ihre Autorität und Integrität ergeben sich aus dem inneren JWS, der Capability, Broker-Authentisierung oder der dokumentenspezifischen Verschlüsselung — nicht aus `from`, `to` oder anderen Envelope-Feldern.

### Plaintext Message

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "typ": "application/didcomm-plain+json",
  "type": "https://web-of-trust.de/protocols/log-entry/1.0",
  "from": "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
  "to": ["did:key:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH"],
  "created_time": 1776514800,
  "thid": "550e8400-e29b-41d4-a716-446655440000",
  "pthid": "7a1c2f80-aabb-4cdd-9eef-112233445566",
  "body": {
    "docId": "7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b",
    "payload": "<Base64URL-kodierter verschlüsselter Inhalt>"
  }
}
```

### Felder

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `id` | UUID v4 | Ja | Eindeutige Nachrichten-ID |
| `typ` | String | Ja | Media Type. Für Plaintext Messages MUSS `application/didcomm-plain+json` gesetzt sein. |
| `type` | URI | Ja | Nachrichtentyp als URI (siehe Tabelle unten) |
| `from` | DID | Ja | Absender-DID |
| `to` | Array von DIDs | Bedingt | Empfänger-DID(s). Pflicht bei Inbox-Nachrichten. |
| `created_time` | Integer (Unix-Seconds) | Ja | Erstellungszeitpunkt (UTC Epoch Seconds), kompatibel mit DIDComm v2.1. |
| `thid` | UUID v4 | Optional | Thread-ID. Verknüpft Nachrichten die zu einer Konversation gehören (z.B. Request + Response). Die erste Nachricht eines Threads setzt `thid = id`; Folgenachrichten tragen denselben `thid`. |
| `pthid` | UUID v4 | Optional | Parent-Thread-ID. Verweist auf einen übergeordneten Thread — für verschachtelte Konversationen (z.B. ein Sub-Protokoll das innerhalb eines größeren Flows läuft). |
| `body` | Object | Ja | Nachrichteninhalt. Struktur abhängig vom `type`. |

### Autoritätsgrenze (MUSS)

Implementierungen MÜSSEN Envelope-Felder als Transport- und Routing-Metadaten behandeln. Insbesondere:

- `from` im Envelope DARF NICHT als Autor des enthaltenen Log-Eintrags oder der enthaltenen Attestation gewertet werden.
- Log-Einträge MÜSSEN über das innere Log-Entry-JWS und `authorKid` verifiziert werden.
- Attestations MÜSSEN über ihr VC-JWS und `issuer` / `iss` verifiziert werden.
- Capabilities MÜSSEN über ihr Capability-JWS und den passenden Verification Key verifiziert werden.
- Inbox-Nachrichten MÜSSEN nach ECIES-Entschlüsselung den inneren JWS prüfen.

### Threading

`thid` und `pthid` sind identisch zu den gleichnamigen DIDComm v2 Feldern. Sie erlauben:

- **Request/Response-Korrelation** — Eine Antwort trägt denselben `thid` wie die Anfrage.
- **Langlaufende Protokolle** — Mehrstufige Flows (z.B. Gruppen-Einladung mit Annahme/Ablehnung) werden durch einen stabilen `thid` zusammengehalten.
- **Verschachtelte Protokolle** — Ein Sub-Protokoll referenziert den Eltern-Flow über `pthid`.

Nachrichten ohne `thid` sind Einzelnachrichten ohne Konversationskontext. Nachrichten die eine andere Nachricht direkt beantworten (z.B. `ack`, `sync-response`) MÜSSEN den `thid` der Original-Nachricht tragen.

### Authentifizierung: drei Envelope-Varianten

Unser Message-Envelope kann in drei WoT-Formen vorliegen. Nur die Plaintext-Form beansprucht DIDComm-v2-Parser-Kompatibilitaet; Signatur und Verschluesselung sind WoT-spezifisch:

1. **Plaintext Message** — nackte JSON, keine Envelope-Signatur, keine Envelope-Verschlüsselung
2. **Signed Message** — Plaintext in JWS verpackt (Envelope-Signatur)
3. **Encrypted Message** — Body mit **ECIES** verschlüsselt (siehe [Sync 001](001-verschluesselung.md#peer-to-peer-verschlüsselung-ecies)). Der Sender wird nicht durch die Verschlüsselung selbst gebunden, sondern durch eine separate JWS-Signatur im Body oder im Envelope

### Wann wird welche Form verwendet (NORMATIV)

Der Envelope wird NUR dann als **Signed Message** verpackt, wenn der Body nicht bereits kryptographisch authentifiziert ist. Doppelte Authentifizierung (Envelope-JWS über Body mit innerer JWS) ist zu vermeiden — sie erhöht nur Größe und Verarbeitungsaufwand, bringt keinen Sicherheitsgewinn.

| Nachrichtentyp | Authentifizierung durch | Envelope |
|---|---|---|
| `log-entry` | Innerer Log-Entry-JWS im Body (persistentes WoT-Objekt) | Plaintext |
| `sync-request`, `sync-response` | Kontext der authentifizierten WebSocket-Verbindung | Plaintext |
| `inbox` (Attestation, etc.) | Innerer JWS im Klartext-Body (bindet Sender) + ECIES-Wrap | Encrypted (ECIES) |
| `space-invite`, `key-rotation`, `member-update` | Innerer JWS im Klartext-Body + ECIES-Wrap | Encrypted (ECIES) |
| `state-digest`, `state-digest-request` | Envelope-JWS (ephemer) | Signed |

### Signatur (WoT Envelope-JWS)

Wenn ein Envelope signiert wird, geschieht das als **JWS Compact Serialization** — identisch mit unseren Attestations ([Identity 002](../01-wot-identity/002-signaturen-und-verifikation.md)). Anders als beim Plaintext Envelope beanspruchen WoT Envelope-JWS keine DIDComm-Signed-Message-Kompatibilität; sie sind ein WoT-spezifisches Signaturprofil.

1. Plaintext Message mit JCS kanonisieren (RFC 8785)
2. JCS-Bytes als Base64URL kodieren
3. Signing Input: `BASE64URL(header) + "." + BASE64URL(jcs_payload)`
4. Ed25519-Signatur über die Signing-Input-Bytes
5. Ergebnis: JWS Compact String

### Verschlüsselung (ECIES)

Inbox-Nachrichten (1:1) werden mit **ECIES** verschlüsselt — X25519 + HKDF + AES-256-GCM. ECIES allein bindet den Sender nicht kryptographisch; die Sender-Authentifizierung wird durch einen **inneren JWS** hergestellt, der im Klartext-Body signiert ist und vom Empfänger nach der Entschlüsselung verifiziert wird.

Ablauf:

1. Sender erstellt den Klartext-Body (z.B. Attestation, Space-Invite)
2. Sender signiert den Body mit seinem Identity Key → innerer JWS
3. Sender verschlüsselt den JWS-String mit ECIES für den X25519-Key des Empfängers
4. Ausgabe: `{ epk, nonce, ciphertext }` (siehe [Sync 001](001-verschluesselung.md#verschlüsseltes-nachrichtenformat))
5. Transport als Body der WoT-Envelope-Nachricht (type = `inbox/1.0`, `space-invite/1.0`, etc.)

**Pflichtfelder im inneren JWS-Payload (MUSS):**

Der innere JWS MUSS mindestens enthalten: `from` (Sender-DID), `to` (Empfänger-DID), `type` (Nachrichtentyp), `id` (Message-ID), `created_time` (Unix-Seconds). Der Empfänger MUSS nach dem Entschlüsseln prüfen:

1. JWS-Signatur verifizieren (Sender's Key via resolve())
2. `to` MUSS die eigene DID sein — verhindert Misdirection (Nachricht an falschen Empfänger umgeleitet)
3. `from` MUSS mit dem JWS-Signierer übereinstimmen — verhindert Sender-Spoofing
4. `created_time` MUSS aktuell sein (nicht älter als konfigurierbar, z.B. 24h) — verhindert Replay
5. `id` DARF nicht bereits verarbeitet worden sein (Message-ID-History) — zweite Replay-Verteidigung

Siehe [Sync 001](001-verschluesselung.md#peer-to-peer-verschlüsselung-ecies) für Details.

Log-Einträge werden NICHT mit ECIES verschlüsselt — sie sind bereits mit dem Space Content Key (AES-256-GCM) verschlüsselt. ECIES ist nur für den Inbox-Kanal.

### Nachrichtentypen

#### WoT Sync (dieses Dokument)

| Type-URI | Kanal | Beschreibung |
|----------|-------|-------------|
| `.../log-entry/1.0` | Log-Sync | Neuer verschlüsselter Log-Eintrag |
| `.../sync-request/1.0` | Log-Sync | Anfrage: "Was hast du seit seq X für docId Y?" |
| `.../sync-response/1.0` | Log-Sync | Antwort: fehlende Log-Einträge |
| `.../inbox/1.0` | Inbox | Direkte verschlüsselte Nachricht (Attestation, etc.) |
| `.../ack/1.0` | Beide | Empfangsbestätigung (referenziert `id` der Original-Nachricht) |

#### Gruppen ([Sync 005](005-gruppen.md))

| Type-URI | Kanal | Beschreibung |
|----------|-------|-------------|
| `.../space-invite/1.0` | Inbox | Einladung in einen Space (Content Key + Capability Signing Key + Capability) |
| `.../key-rotation/1.0` | Inbox | Neuer Content Key + Capability Signing Key nach Member-Entfernung |
| `.../member-update/1.0` | Inbox | Mitgliedschafts-Änderung (hinzugefügt/entfernt) |

#### HMC Extension ([H03 Gossip](../05-hmc-extensions/H03-gossip.md))

| Type-URI | Kanal | Beschreibung |
|----------|-------|-------------|
| `.../trust-list-delta/1.0` | Inbox | Trust-List-Update (SD-JWT, selektiv offengelegt) |

Alle Type-URIs verwenden den Präfix `https://web-of-trust.de/protocols/`.

Die Body-Formate fuer `space-invite/1.0`, `key-rotation/1.0` und `member-update/1.0` sind in [Sync 005](005-gruppen.md) spezifiziert und werden durch die Schemas `space-invite`, `key-rotation` und `member-update` beschrieben. Alle drei Nachrichtentypen sind Inbox-Nachrichten und MUESSEN nach [Sync 001 ECIES](001-verschluesselung.md#peer-to-peer-verschlüsselung-ecies) fuer den jeweiligen Empfaenger verschluesselt werden.

### Wire-Formate der Sync-Nachrichten

#### `log-entry/1.0` — Neuer verschlüsselter Log-Eintrag

Ein Peer publiziert einen neuen Log-Eintrag an andere Peers. Der Log-Eintrag selbst ist ein persistentes WoT-Objekt und **JWS Compact String** (siehe [Sync 002](002-sync-protokoll.md#signatur-des-log-eintrags)). Er wird als opaker String im Body transportiert:

```json
{
  "entry": "<JWS Compact String des Log-Eintrags>"
}
```

Der JWS-Payload des Eintrags enthält die Felder `seq`, `deviceId`, `docId`, `authorKid`, `keyGeneration`, `data`, `timestamp` — JCS-kanonisiert, Ed25519-signiert. Vollständiges Schema in [Sync 002 Log-Eintrag](002-sync-protokoll.md#log-eintrag).

**Broker-Indexing:** Der Broker extrahiert `docId`, `deviceId`, `seq` aus dem JWS-Payload (Base64URL-dekodieren des mittleren Segments, JCS-kanonisiertes JSON parsen). Diese drei Felder braucht er für Indexing, Sync-Anfragen und Kollisionserkennung. Der Broker MUSS die JWS-Signatur NICHT verifizieren — Signatur-Verifikation ist Aufgabe der Peers, die die Einträge letztendlich konsumieren. Der Broker darf sie aber als zusätzliche Integritätsprüfung durchführen.

Kein ACK nötig — der Empfang wird implizit durch den nächsten `sync-request` bestätigt (fehlende seq-Werte werden nachgefordert).

**Broker-seitige Kollisionsabwehr (MUSS):**

Der Broker MUSS für jeden akzeptierten Log-Eintrag den **Content-Hash** (SHA-256 über den kanonisierten Payload) speichern, indiziert nach `(docId, deviceId, seq)`. Beim Empfang eines neuen Eintrags prüft der Broker:

1. Existiert bereits ein Eintrag mit derselben `(docId, deviceId, seq)`?
2. Falls ja: Stimmt der Content-Hash überein?
   - **Hash gleich:** Idempotente Retransmission — OK, der Broker ignoriert die Duplizierung still
   - **Hash unterschiedlich:** **Kollision** — der Broker MUSS den neuen Eintrag ablehnen und mit `SEQ_COLLISION_DETECTED` antworten
3. Falls nicht: Eintrag akzeptieren, Hash speichern

Diese Prüfung ist die letzte Verteidigungslinie gegen AES-GCM-Nonce-Reuse und MUSS auch dann erzwungen werden, wenn der Client seq-Konsistenz-Regeln aus [Sync 002](002-sync-protokoll.md#seq-konsistenz-muss) einhält (Defense in Depth).

**Reaktion des Clients bei `SEQ_COLLISION_DETECTED`:**

Der Client MUSS diese Response als Indikator für ein Restore/Clone-Szenario behandeln und die Restore-Detection-Regel aus [Sync 002](002-sync-protokoll.md#seq-konsistenz-muss) anwenden: neue `deviceId` generieren, alte deaktivieren, neu beginnen.

#### `sync-request/1.0` — Anfrage: "Was hast du seit X?"

Ein Peer fragt einen anderen nach fehlenden Log-Einträgen. Body:

```json
{
  "docId": "7f3a2b10-...",
  "heads": {
    "a1b2c3d4-...": 42,
    "e5f6g7h8-...": 17
  },
  "limit": 100
}
```

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `docId` | UUID | Ja | Für welches Dokument |
| `heads` | Object | Ja | Pro bekanntem `deviceId` die höchste seq, die ich bereits habe |
| `limit` | Integer | Nein | Maximale Anzahl Einträge in der Antwort (Default: 100) |

**Heads-Semantik:** Ein leerer oder fehlender Eintrag für eine `deviceId` bedeutet "ich habe nichts von diesem Device" — der Antwortende sendet dann alle verfügbaren Einträge ab `seq=0`. Ein bekannter Eintrag bedeutet "ich habe bis inklusive seq N" — gesendet werden Einträge ab `seq=N+1`.

#### `sync-response/1.0` — Antwort mit fehlenden Einträgen

Antwort auf `sync-request`. Body:

```json
{
  "docId": "7f3a2b10-...",
  "entries": [
    "<JWS Compact String #1>",
    "<JWS Compact String #2>"
  ],
  "heads": {
    "a1b2c3d4-...": 52,
    "e5f6g7h8-...": 17,
    "i9j0k1l2-...": 8
  },
  "truncated": false
}
```

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `docId` | UUID | Ja | Für welches Dokument |
| `entries` | Array of JWS-Strings | Ja | Die fehlenden Log-Einträge als JWS Compact Strings, sortiert nach `(deviceId, seq)`. Format gemäß [Sync 002 Log-Eintrag](002-sync-protokoll.md#log-eintrag). |
| `heads` | Object | Ja | Die aktuell höchsten bekannten seq pro deviceId beim Antwortenden |
| `truncated` | Boolean | Ja | `true` wenn durch `limit` abgeschnitten — der Fragende MUSS einen weiteren `sync-request` mit aktualisierten Heads senden |

**Threading:** Der `sync-response` MUSS denselben `thid` wie der zugehörige `sync-request` tragen.

**Heads-Diskrepanz-Detection:** Der Fragende kann die erhaltenen `heads` mit denen anderer Broker/Peers vergleichen, um Censorship oder Split-Brain zu erkennen (siehe [Sync 002](002-sync-protokoll.md#censorship--und-split-brain-detection)).

#### `ack/1.0` — Empfangsbestätigung

Wird nur für **Inbox-Nachrichten** verwendet (nicht für sync-request/response — dort ist die Bestätigung implizit). Body:

```json
{
  "messageId": "uuid-der-empfangenen-nachricht"
}
```

Der Empfänger schickt `ack` nach erfolgreichem Verarbeiten einer Inbox-Nachricht. Erfolgreich verarbeitet bedeutet:

1. ECIES-Entschlüsselung erfolgreich, falls die Nachricht verschlüsselt war.
2. Inneres JWS oder persistentes WoT-Objekt verifiziert.
3. Replay-Prüfung bestanden oder die Nachricht wurde als Duplikat sicher erkannt.
4. Resultierender lokaler State wurde angewendet oder die Nachricht wurde gemaess [Sync 002](002-sync-protokoll.md) durabel in der **Pending-Inbox** gepuffert. `Pending` bedeutet hier: crash-sichere persistente Speicherung (nicht nur volatil im RAM) zusammen mit den fuer die spaetere Aufloesung und Anwendung erforderlichen Metadaten, mindestens `messageId` sowie Abhaengigkeits-/Missing-Dependency-Metadaten.

Der Broker kann die Nachricht dann aus der Inbox **dieses authentifizierten Devices** entfernen. Er DARF sie nicht aus anderen Device-Inboxen derselben DID entfernen. Wenn der Client eine Nachricht wegen fehlender Abhaengigkeiten nur volatil im Speicher haelt, DARF er sie noch nicht ACKen.

Ein `ack/1.0` ist ausschliesslich eine Transport-/Persistenzbestaetigung fuer genau dieses Device. Es bestaetigt nicht, dass ein Inhaltsartefakt semantisch angenommen, vertraut, gelesen, angezeigt oder veroeffentlicht wurde. Insbesondere definiert `wot-trust@0.1` kein `attestation-ack`; ob ein Empfaenger eine Attestation spaeter oeffentlich zeigt, ergibt sich nur aus seiner bewussten Profil-Veroeffentlichung.

#### Fehler-Responses

Wenn eine Sync-Anfrage nicht erfüllt werden kann, antwortet der Broker mit einer Error-Nachricht:

```json
{
  "type": "https://web-of-trust.de/protocols/error/1.0",
  "thid": "<thid der Original-Anfrage>",
  "body": {
    "code": "DOC_NOT_FOUND",
    "message": "Unbekannte docId"
  }
}
```

Normative Error-Codes:

| Code | Wann |
|------|------|
| `DOC_NOT_FOUND` | Dokument existiert beim Broker nicht |
| `CAPABILITY_INVALID` | Capability-Signatur ungültig |
| `CAPABILITY_EXPIRED` | Capability abgelaufen |
| `CAPABILITY_GENERATION_STALE` | Capability für alte Space-Keypair-Generation (nach Rotation) |
| `DEVICE_NOT_REGISTERED` | Client-Device ist beim Broker nicht registriert |
| `DEVICE_REVOKED` | Device-ID ist als revoked markiert |
| `DEVICE_ID_CONFLICT` | Device-ID bereits für eine andere DID registriert |
| `SEQ_COLLISION_DETECTED` | Log-Eintrag mit `(docId, deviceId, seq)` existiert bereits mit anderem Content-Hash — Client MUSS neue `deviceId` generieren (Restore/Clone-Szenario) |
| `RATE_LIMITED` | Rate-Limit überschritten |
| `INTERNAL_ERROR` | Server-Fehler |

Clients SOLLEN bei `CAPABILITY_EXPIRED` eine neue Capability anfordern (via Peer-Kontakt, da der Broker die Signatur nicht erzeugen kann).

### Erweiterbarkeit

Neue Nachrichtentypen DÜRFEN von Extensions definiert werden. Ein Client der einen unbekannten Typ empfängt MUSS die Nachricht ignorieren (nicht verwerfen — der Broker speichert sie weiterhin für andere Clients die den Typ verstehen).

### Envelope-Kompatibilität

Das Plaintext-Envelope-Format ist **DIDComm-v2.1-kompatibel** auf Envelope-Ebene: `id`, `typ`, `type`, `from`, `to`, `created_time` (Unix-Seconds), `body`, `thid`/`pthid`. DIDComm-Bibliotheken können unsere Plaintext-Messages lesen und routen. Dieser Anspruch endet an der Envelope-Grenze: Verschlüsselung, Signaturen, persistente WoT-Objekte, Broker-Authentisierung und Sync-Semantik bleiben WoT-spezifisch.

Für die Hintergründe dieser Entscheidung siehe [Research: Interop und Zielgruppe](../research/interop-und-zielgruppe.md).

## Broker-Zuordnung und Multi-Broker

Persönliche Dokumente werden auf alle Broker repliziert, bei denen der User registriert ist. Space-Dokumente werden auf den Heim-Broker(n) des Space repliziert; die Broker-URL(s) sind Teil der Space-Metadata und werden in Space-Einladungen transportiert.

Broker kommunizieren NICHT untereinander. Clients synchronisieren mit allen relevanten Brokern und führen Konvergenz lokal über das Sync-Protokoll und den CRDT-Merge herbei. Ein Space DARF mehrere Heim-Broker haben; alle Members eines Space MÜSSEN bei mindestens einem gemeinsamen Heim-Broker registriert sein.

Ein Space-Admin DARF Heim-Broker in der Space-Metadata ändern. Clients migrieren beim nächsten Sync.

## Push-Notifications

Broker DÜRFEN Push-Signale senden, wenn für ein offline Device neue Inbox-Nachrichten oder Log-Einträge vorliegen. Push-Payloads DÜRFEN keinen Klartext und keine verschlüsselten WoT-Payloads enthalten; sie signalisieren nur, dass der Client den Broker erneut abfragen soll.

## Transport-Agnostik

Das Envelope-Format und die Body-Formate sind transportunabhängig. WebSocket ist der primäre Phase-1-Transport; andere Transports können dieselben Payloads mit transport-spezifischem Framing verwenden.

## Direkter P2P-Sync

Wenn zwei Peers direkt kommunizieren (Bluetooth, WiFi Direct, LAN ohne Broker), fällt die Broker-Schicht weg. Authentisierung, Autorisierung und Message-Routing laufen direkt zwischen den Peers.

### Mutual Challenge-Response

Im P2P-Modus gibt es keinen "Server" — beide Peers müssen sich gegenseitig authentifizieren:

```
1. Alice und Bob haben eine bidirektionale Verbindung (Bluetooth, WebSocket-LAN, etc.)

2. Alice sendet: { type: "p2p-hello", did_A, deviceId_A, nonce_A }
3. Bob sendet:   { type: "p2p-hello", did_B, deviceId_B, nonce_B }

4. Beide Seiten erstellen denselben kanonischen Transcript-String:
     transcript = JCS-Kanonisierung von {
       "protocol": "wot/p2p-auth/v1",
       "initiatorDid": did_A,
       "initiatorDeviceId": deviceId_A,
       "initiatorNonce": nonce_A,
       "responderDid": did_B,
       "responderDeviceId": deviceId_B,
       "responderNonce": nonce_B
     }

5. Alice signiert (transcript || "role:initiator") mit ihrem Identity Key:
   → { type: "p2p-auth", did: did_A, role: "initiator", signature: Sig_Alice }
6. Bob signiert (transcript || "role:responder") mit seinem Identity Key:
   → { type: "p2p-auth", did: did_B, role: "responder", signature: Sig_Bob }

7. Alice rekonstruiert denselben Transcript und verifiziert Sig_Bob gegen Bobs Public Key
8. Bob rekonstruiert denselben Transcript und verifiziert Sig_Alice gegen Alices Public Key

9. Beide authentifiziert → Sync kann beginnen
```

Die Initiator/Responder-Rolle MUSS vor der Signatur eindeutig festgelegt und in den signierten Input aufgenommen werden. Alle DIDs, Device-IDs und Nonces MÜSSEN Teil des Transcripts sein. Nach erfolgreicher Verifikation kennt jeder Peer die authentische DID und `deviceId` des Gegenübers.

### Nonce-Anforderungen

- Nonces MÜSSEN mindestens 32 Bytes aus einer kryptographisch sicheren Zufallsquelle sein
- Jede Seite MUSS eine Nonce-History (wie [Trust 002](../02-wot-trust/002-verifikation.md#nonce-history-muss)) führen um Replay-Angriffe zu verhindern
- Nonces MÜSSEN nach Verwendung verworfen werden
- Der Transcript MUSS mit JCS (RFC 8785) kanonisiert werden, damit beide Seiten bitgenau denselben Input signieren/verifizieren

### Autorisierung ohne Capabilities

Im P2P-Modus gibt es keinen Broker, der Capabilities prüft. Stattdessen prüft jeder Peer lokal:

**Für Space-Dokumente:**

1. Kennt der Peer das fragliche Dokument? (Space-ID in seiner Liste?)
2. Ist die DID des Gegenübers in der lokalen Mitgliederliste dieses Space?
3. Kann der Gegenüber aktuellen Space-Zugriff beweisen (durch erfolgreiches Entschlüsseln einer Test-Challenge mit dem Space Content Key oder durch eine vorzeigbare Capability)?

**Für persönliche Dokumente:**

Nur erlaubt zwischen Devices desselben Users (gleiche DID im Handshake).

### Entfernte Members im P2P-Modus

Im Offline-P2P-Modus gibt es keinen autoritativen Broker-Check für aktuelle Membership. Clients SOLLEN Peers als verdächtig markieren, wenn diese nur Log-Einträge mit alter `keyGeneration` liefern, und solche Daten nicht mergen, bis Membership über eine vertraute Quelle bestätigt wurde.

### Transport-Framing

Verschiedene Transports haben unterschiedliche Paket-Semantiken:

| Transport | Framing |
|---|---|
| WebSocket (LAN) | WebSocket-Messages sind bereits framed |
| Bluetooth L2CAP | Length-prefixed (4-Byte Big-Endian + Payload) |
| Sneakernet (QR, USB) | Einzelne JSON-Dokumente pro "Übertragungseinheit" |

Der normative Payload ist jeweils derselbe: eine DIDComm-kompatible Message mit `type`, `body`, etc. Nur die Transport-spezifische Einrahmung unterscheidet sich.

### Inbox im P2P-Modus

P2P-Verbindungen sind typischerweise kurz. Eine "Inbox" im Sinne von Store-and-Forward existiert nicht — Nachrichten werden direkt zugestellt oder gehen verloren. Für garantierte Zustellung SOLLEN Clients den Broker-Pfad nutzen, nicht P2P.

## Architektur-Grundlage

Siehe [Sync-Architektur](../research/sync-architektur.md) und [Sync-Alternativen](../research/sync-alternativen.md) für die vollständige Analyse.
