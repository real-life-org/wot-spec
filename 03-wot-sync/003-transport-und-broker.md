# WoT Sync 003: Transport und Broker

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-13
- **Scope:** Broker, Transport, Capabilities, WoT Transport Envelopes (DIDComm-v2-kompatibel), Broker Control-Frames und P2P-Sync
- **Depends on:** Identity 002, Trust 002, Identity 003, Sync 001, Sync 002, Sync 005, Sync 006
- **Conformance profile:** `wot-sync@0.1`

## Zusammenfassung

Dieses Dokument spezifiziert wie Daten zwischen Peers transportiert werden und wie Broker als immer-online Peers funktionieren. Ein Broker ist kein spezieller Server — er ist ein Peer der zufällig immer online ist und Push-Notifications verschicken kann.

## Referenzierte Standards

- **WebSocket** (RFC 6455) — Primärer Transportkanal
- **DIDComm v2** (DIF) — Format-Kompatibilität auf der Envelope-Schicht für peer-to-peer Messages (keine DIDComm-JWE/Authcrypt-Verschlüsselung, keine Mediator-Protokolle)
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
5. Client signiert den Broker-Auth-Transcript mit Ed25519 Private Key
6. Client sendet: { type: "challenge-response", did, deviceId, nonce, signature }
7. Broker verifiziert:
   - DID auflösen → Public Key
   - Signatur über den Broker-Auth-Transcript prüfen
   - OK → Verbindung authentifiziert
8. Broker sendet: { type: "registered", did, deviceId }
```

Nach dem Handshake ist die WebSocket-Verbindung authentifiziert. Alle weiteren Nachrichten auf dieser Verbindung gelten als von dieser DID + deviceId kommend.

Die Device-ID (`deviceId`) identifiziert das Gerät stabil — derselbe Wert wie im Sync-Protokoll ([Sync 002](002-sync-protokoll.md#device-identifikation)).

`register.deviceId`, `challenge-response.deviceId`, `device-revoke.deviceId` und ACK-/Inbox-Scoping über `deviceId` MÜSSEN die kanonische lowercase UUID-v4-Form verwenden. Broker MÜSSEN malformed oder nicht-v4 Device-IDs vor einer Registrierung mit `MALFORMED_MESSAGE` ablehnen.

### Nonce-Handling (MUSS)

Die Challenge-Nonce in der Broker-Authentisierung MUSS denselben Replay-Schutz-Regeln folgen wie die Verifikations-Challenge in [Trust 002](../02-wot-trust/002-verifikation.md#nonce-history-muss):

- Broker MÜSSEN bereits verwendete Nonces für mindestens 24 Stunden speichern
- Eine Nonce DARF nur einmal akzeptiert werden
- Nonces MÜSSEN mindestens 32 Bytes aus einer kryptographisch sicheren Zufallsquelle haben
- Clients MÜSSEN die Nonce direkt nach Empfang signieren (keine späteren Signaturen auf wiederverwendeten Nonces)

### Broker-Auth-Transcript (MUSS)

Die Signatur in `challenge-response` wird nicht über die rohen Nonce-Bytes und nicht über den Base64URL-String allein erzeugt. Sie MUSS über die JCS-kanonisierten Bytes des folgenden Transcripts erzeugt und verifiziert werden:

```json
{
  "protocol": "wot/broker-auth/v1",
  "type": "challenge-response",
  "did": "did:key:z6Mk...",
  "deviceId": "550e8400-e29b-41d4-a716-446655440000",
  "nonce": "<kanonische unpadded Base64URL-Nonce>"
}
```

Die `nonce` im Transcript ist die kanonische unpadded Base64URL-Darstellung der 32 zufälligen Nonce-Bytes. Base64URL-Padding (`=`) ist in Broker-Challenges und Challenge-Responses ungültig.

Der Broker MUSS ausgegebene, noch nicht akzeptierte Nonces an die konkrete WebSocket-Verbindung und an die zuvor empfangenen `register.did` / `register.deviceId` Werte binden. `challenge-response.did`, `challenge-response.deviceId` und `challenge-response.nonce` MÜSSEN exakt zu dieser ausstehenden Challenge passen, bevor die Signatur als gültig akzeptiert wird. Nach erfolgreicher Akzeptanz MUSS die Nonce als verbraucht gespeichert werden; ein erneuter Versuch mit derselben Nonce wird mit `NONCE_REPLAY` abgelehnt.

> Diese Bindung ist nicht durch JSON-Schema oder ein statisches Vektor-Fixture validierbar — sie ist Protokollzustand pro Verbindung. Implementierungen MÜSSEN sie zur Laufzeit durchsetzen (Nonce-zu-Verbindungs-Map + Verbrauchsliste, Abgleich von `did`/`deviceId`/`nonce` vor jeder Signaturverifikation).

### Wire-Encoding der `signature` (MUSS)

Das `signature`-Feld im `challenge-response`-Control-Frame MUSS die **kanonische unpadded Base64URL**-Encodierung der 64-Byte Ed25519-Signatur über die JCS-kanonisierten Bytes des Broker-Auth-Transcripts enthalten (RFC 4648 §5 ohne Padding). Daraus folgt:

- Die encodierte Form hat exakt 86 Base64URL-Zeichen.
- Base64URL-Padding (`=`) ist ungültig.
- Standard-Base64 (Zeichensatz `+`/`/`) ist ungültig.
- Hex, Multibase oder andere Encodings sind ungültig.

Fehlerbehandlung:

- **`MALFORMED_MESSAGE`** — Signature-Feld fehlt, hat nicht 86 Zeichen, enthält Padding oder nicht-Base64URL-Zeichen, oder dekodiert nicht zu genau 64 Bytes.
- **`AUTH_INVALID`** — Signature ist well-formed, dekodiert zu 64 Bytes, aber Ed25519-Verifikation gegen den Public Key der DID schlägt fehl.

Challenge-Response ist bewusst **kein** WoT-JWS. Der Transcript ist explizit im Control-Frame-Body, Algorithmus-Agility ist auf Sync-003-Ebene nicht spezifiziert (Ed25519 fest), und die Authentisierung ist transient — nur für den Verbindungsaufbau, nicht für persistente Claims.

## Device-Registrierung

Der Broker MUSS pro DID eine Liste der zugehörigen Device-IDs führen. Das ist notwendig für:

- **Sequenzierte Log-Einträge** — jeder Log-Eintrag ist identifiziert durch `(deviceId, docId, seq)` (siehe [Sync 002](002-sync-protokoll.md))
- **Nonce-Konstruktion** — die deterministische AES-GCM-Nonce basiert auf `(deviceId, seq)` (siehe [Sync 001](001-verschluesselung.md#nonce-konstruktion))
- **Store-and-Forward pro Device** — Inbox-Nachrichten müssen jedem Device zugestellt werden, auch wenn es vorübergehend offline ist

### Erstregistrierung

Wenn ein Client mit einer `(did, deviceId)`-Kombination verbindet, die der Broker noch nicht kennt:

1. Broker führt normale Challenge-Response durch (siehe oben)
2. Nach erfolgreicher Authentisierung: Broker prüft, ob `deviceId` bereits für eine **andere DID** registriert ist, egal ob dort `active` oder `revoked` (siehe [Device-Liste](#device-liste-im-broker))
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

Device-Deaktivierung wird über einen **Broker Control-Frame** mit einem inneren signierten Revocation-Claim kommuniziert. Die exakte äußere Wire-Form ist:

```json
{
  "type": "device-revoke",
  "revocationJws": "<JWS Compact Serialization>"
}
```

Der `device-revoke`-Control-Frame MUSS genau die Top-Level-Felder `type` und `revocationJws` tragen. Er DARF kein `thid`, kein `body` und keine unbekannten Top-Level-Felder tragen. Broker MÜSSEN abweichende äußere Formen mit `MALFORMED_MESSAGE` ablehnen.

`revocationJws` MUSS eine JWS Compact Serialization sein. Der dekodierte JWS-Payload MUSS exakt das Device-Deaktivierungsobjekt mit den Feldern `type`, `did`, `deviceId` und `revokedAt` sein:

```json
{
  "type": "device-revoke",
  "did": "did:key:z6Mk...alice",
  "deviceId": "<UUID zu entfernen>",
  "revokedAt": "2026-04-22T10:00:00Z"
}
```

Der innere JWS-Payload DARF keine weiteren Felder tragen. Er MUSS mit dem Identity Key der angegebenen DID signiert sein. Der Broker MUSS prüfen:

1. JWS-Signatur gültig gegen den Ed25519-Key aus `did`
2. `type` im JWS-Payload ist exakt `device-revoke`
3. `deviceId` ist eine kanonische lowercase UUID v4 und `revokedAt` ist ein RFC3339-Date-Time mit expliziter Zeitzone
4. Der Broker markiert `(did, deviceId)` als `revoked`
5. Ausstehende Inbox-Nachrichten für dieses Device werden gelöscht
6. Zukünftige Verbindungsversuche mit dieser Kombination werden mit `DEVICE_REVOKED` abgelehnt

Die Effekte aus 4-6 sind Runtime-/Protokollzustands-Prüfungen. Das Markieren von `(did, deviceId)`, die Inbox-Löschung und die Ablehnung mit `DEVICE_REVOKED` können nicht vollständig durch statische Schema- oder Vektor-Fixtures bewiesen werden; ihr Nachweis erfordert beobachtetes Broker-Laufzeitverhalten oder Protokoll-Logs.

Jede gültig mit dem Identity Key der DID signierte `device-revoke` Nachricht DARF jedes Device derselben DID deaktivieren. Im Shared-Seed-Modell ist keine zusätzliche Signatur eines device-spezifischen Keys erforderlich.

Eine gültige Revocation für ein unbekanntes `(did, deviceId)` MUSS der Broker als revoked Tombstone speichern und idempotent akzeptieren. Eine gültige Revocation für ein bereits revoked Device MUSS ebenfalls idempotent akzeptiert werden; die zuerst gespeicherten Revocation-Metadaten bleiben autoritativ und werden durch spätere Duplikate nicht überschrieben. Für Duplikate MUSS der Broker keine Inbox-Nachrichten erneut löschen, DARF aber dieselbe Cleanup-Operation idempotent ausführen.

Malformed `device-revoke` Nachrichten werden mit `MALFORMED_MESSAGE` abgelehnt. Ungültige Signaturen, Signaturen eines anderen DID-Schlüssels oder ein `did`/Signer-Mismatch werden mit `AUTH_INVALID` abgelehnt.

**Limitation im Shared-Seed-Modell:** Wer den Seed hat, kann eine neue `deviceId` generieren und sich als "neues Device" registrieren. Device-Deaktivierung schützt nicht gegen Seed-Kompromittierung — siehe [Identity 001](../01-wot-identity/001-identitaet-und-schluesselableitung.md#multi-device--shared-seed-modell). Für echten Schutz muss die Identität rotiert werden.

### Device-Liste im Broker

Der Broker speichert pro DID mindestens `deviceId`, `firstSeenAt`, `lastSeenAt`, `status` (`active` oder `revoked`) und optional `revokedAt`. Diese Liste ist Broker-Metadatum und liegt im Klartext vor.

`active` und `revoked` sind die einzigen normativen Device-Statuswerte in `wot-sync@0.1`. Ein `revoked` Record ist ein Tombstone: solange der Broker ihn speichert, gilt die `deviceId` weiter als registriert und reserviert für Konfliktprüfungen. Eine für eine andere DID retained revoked `deviceId` führt daher weiterhin zu `DEVICE_ID_CONFLICT`.

### Race Conditions

Der Broker MUSS Revocations atomisch anwenden. Wenn Registrierung und Revocation für dieselbe `deviceId` konkurrieren, gewinnt die Revocation und die Registrierung wird mit `DEVICE_REVOKED` abgelehnt. Ist eine `deviceId` bereits für eine andere DID registriert, MUSS der Broker mit `DEVICE_ID_CONFLICT` ablehnen.

### Log-Eintrag-Autor-Bindung (MUSS)

Beim Ingest eines `log-entry/1.0` MUSS der Broker prüfen, dass die aus `authorKid` extrahierte DID (Teil vor `#`, siehe [Sync 002](002-sync-protokoll.md#signatur-des-log-eintrags)) exakt die DID ist, die `deviceId` in der Broker-Device-Liste besitzt. Andernfalls Ablehnung mit `AUTHOR_MISMATCH`; der Eintrag wird **weder gespeichert noch relayed**. Diese Bindung verankert die `(docId, deviceId, seq)`-Autorität an der registrierten `(did, deviceId)`-Kombination (`deviceId` global eindeutig, siehe [Device-Liste](#device-liste-im-broker)) und verhindert, dass ein gültig signierender Autor unter einer fremden `deviceId` schreibt. Sie ist der autoritative Anker und ersetzt brokerlokale First-Writer-Wins-Heuristiken auf `(docId, deviceId)`.

**Grenze (Shared-Seed):** Im Shared-Seed-Modell teilen alle Geräte eines Users dieselbe DID; die Bindung filtert dann fremde DIDs, nicht Geräte derselben DID. Geräte-granulare Autorität erfordert per-device Keys (Identity 004 / Phase 2).

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
- Wenn ein Device für längere Zeit (z.B. 90 Tage) nicht verbindet, DARF der Broker es nach lokaler Retention-Policy als inaktiv behandeln und seine ausstehenden Nachrichten löschen. `inactive` ist kein normativer Statuswert; der Broker modelliert solche GCs lokal, ohne die `active`/`revoked`-Statusmenge zu erweitern.
- Für kritische Nachrichten (Space-Einladungen, Key-Rotationen) SOLLTE der Sender einen Liefernachweis implementieren (z.B. erneutes Senden nach Timeout)

Der pro-Device-Zustellpfad stellt sicher, dass jedes aktive Device kritische Nachrichten wie Space-Einladungen und Key-Rotationen mindestens einmal erhält.

### Relay-Whitelist (MUSS)

Der Broker relayt und queued **ausschließlich** Nachrichten **definierter** Typen: WoT Transport Envelopes, deren `type` in der [Nachrichtentypen-Tabelle](#nachrichtentypen) steht, sowie die definierten [Control-Frames](#broker-control-frames-normativ). Jede andere Nachricht — unbekannter `type` oder eine nicht-konforme Legacy-Envelope (insbesondere der **deprecated pipe-`content`-Kanal** vor seiner vollständigen Entfernung in einem späteren Slice) — MUSS mit `MALFORMED_MESSAGE` abgelehnt und **weder relayed noch gequeued** werden.

Begründung (sicherheitskritisch): Ohne diese Whitelist könnte ein entfernter Member nach der Rotation alt-verschlüsselten Inhalt in einen Envelope mit beliebigem, nicht-definiertem `type` packen und über den generischen Routing-Pfad **live an verbliebene Member zustellen** — der `log-entry`-Ingest-Gate (inkl. Generations-Gate) greift dort nicht. Die Whitelist schließt diesen un-gegateten Restkanal: legitime Clients senden Content ausschließlich als `log-entry/1.0` (gegated), Membership-/Key-Nachrichten ausschließlich über die definierten Inbox-Typen.

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

Das Feld `type` ist immer `"capability"`. Der JWS wird mit dem Space Capability Signing Key signiert. Der `kid` im JWS-Header MUSS den Space-Kontext und die Capability-Key-Generation referenzieren: `wot:space:<spaceId>#cap-<generation>`. Der Broker verifiziert mit dem aktuellen Space Capability Verification Key für genau diesen Space und diese Generation.

Für **persönliche Dokumente** wird dasselbe Payload-Schema mit festen Bindungen und einem abweichenden `kid` (Identity-Key statt Space-Key) verwendet — siehe [Persönliche Dokumente](#persönliche-dokumente).

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

**Präsentation (session-scoped, MUSS).** Eine Capability wird **einmal pro Session** präsentiert, nicht pro Nachricht. Nach dem Handshake sendet der Client für jedes Dokument, das er nutzen will, einen `present-capability`-Control-Frame (siehe [Control-Frame-Vokabular](#broker-control-frames-normativ)). Der Broker verifiziert die Capability und **cached den erlaubten Scope pro `(WebSocket, docId)`**. Folgende `log-entry`- und `sync-request`-Nachrichten werden gegen diesen Cache geprüft — ohne erneute Capability. Das folgt der Authentizität-pro-Message-Typ-Regel ([§Authentizität](#authentizität-pro-message-typ-normativ)): Autorität über den authentifizierten Kanal, keine doppelte Auth.

**Verifikation bei `present-capability` (MUSS).** Der Broker bestimmt zuerst den Pfad anhand der `docId`:

- **Space-Dokument** (für `docId` existiert eine `space-register`-Eintragung): Capability-JWS gültig gegen den aktuellen `spaceCapabilityVerificationKey` dieses Space (inklusive `alg=EdDSA`, siehe [Identity 002](../01-wot-identity/002-signaturen-und-verifikation.md#algorithmus-validierung-muss)); `audience` = authentifizierte DID; `spaceId` = `docId` (für Space-Dokumente gilt `docId == spaceId`, siehe [Sync 002](002-sync-protokoll.md#docid-und-spaceid)); `generation` = aktuelle Capability-Key-Generation; `now < validUntil`.
- **Persönliches Dokument** (für `docId` existiert **keine** `space-register`-Eintragung): self-issued Capability — siehe [Persönliche Dokumente](#persönliche-dokumente).

Der gecachte Scope MUSS die `permissions` (`read`/`write`) **und** die `generation` der Capability mitführen.

**Gate (MUSS).** Der Capability-Gate gilt **ausschließlich für den Log-Sync-Kanal**:

- `log-entry/1.0`-Ingest erfordert einen gecachten **`write`**-Scope für `docId`. Fehlt er → `CAPABILITY_REQUIRED`.
- `sync-request` erfordert einen gecachten **`read`**-Scope für `docId`. Fehlt er → `CAPABILITY_REQUIRED`.

Der **Inbox-Kanal** (`inbox/1.0`, `space-invite/1.0`, `member-update/1.0`, `key-rotation/1.0`, `ack/1.0`) ist **NICHT** capability-gated — sonst könnte ein frischer Client nie die erste Capability erhalten (Cold-Start). Inbox-Nachrichten sind ECIES-verschlüsselt und tragen ihre Autorität im inneren JWS.

`validUntil` begrenzt Zugriffsrechte ohne explizite Rotation. Aktive Members bekommen rechtzeitig eine erneuerte Capability; inaktive Members verlieren den Broker-Zugriff automatisch.

### Capability-Widerruf über Rotation

Bei Member-Entfernung rotiert der Admin das **Space Capability Key Pair**. Der Broker akzeptiert ab dem Moment nur Capabilities die gegen den neuen `spaceCapabilityVerificationKey` verifizierbar sind — alle alten Capabilities werden automatisch ungültig.

Der Admin sendet dem Broker einen `space-rotate`-Control-Frame. Wie alle Broker-Management-Frames trägt er seinen Claim als **Inner-JWS** (analog `device-revoke`), signiert mit dem space-spezifisch abgeleiteten **Admin Key**:

```json
{
  "type": "space-rotate",
  "rotationJws": "<JWS Compact Serialization>"
}
```

Der dekodierte JWS-Payload MUSS exakt `{ "type": "space-rotate", "spaceId": "<uuid>", "newSpaceCapabilityVerificationKey": "<base64url>", "newGeneration": <int> }` sein; der JWS-`kid` referenziert die signierende `adminDid`. `newSpaceCapabilityVerificationKey` ist der kanonische Feldname (parallel zu `spaceCapabilityVerificationKey` bei `space-register`, mit `new`-Präfix wie `newGeneration`) — derselbe Wire-Contract, ein Feldname. Der Broker akzeptiert die Nachricht nur, wenn die `adminDid` zur registrierten Admin-Liste dieses Space gehört (sonst `AUTH_INVALID`). Eine NEUE Rotation installiert er ausschließlich für `newGeneration` exakt gleich der aktuellen Generation plus eins; `newGeneration` größer als die aktuelle Generation plus eins wird mit `GENERATION_GAP` abgelehnt; das Error-Frame MUSS die aktuell installierte Broker-Generation als strukturiertes Detail `currentGeneration` tragen — erst dadurch ist die Reparatur wire-seitig entscheidbar. Client-Verhalten (MUSS): Ist die eigene lokale Generation kleiner-gleich `currentGeneration`, holt der Client per Catch-Up auf und staged frisch auf `currentGeneration + 1`. Ist die eigene lokale Generation bereits GRÖSSER als `currentGeneration` (Split-Brain bzw. Broker-State-Verlust), ist der Gap NICHT automatisch reparierbar: der Client DARF nicht blind restagen und MUSS den Zustand als Fehler surfacen (das Staging bleibt durabel erhalten). Für `newGeneration` kleiner-gleich der aktuellen Generation gilt die materialgebundene Idempotenz-Regel unten (idempotenter Erfolg bzw. `GENERATION_TAKEN`).

**Materialgebundene Idempotenz und `GENERATION_TAKEN` (MUSS).** Konkurrierende Rotationen und verlorene Erfolgsbestätigungen sind für den Client nur unterscheidbar, wenn die Broker-Antwort an das Key-Material bindet:

- Ist `newGeneration` exakt die **aktuell installierte** Generation UND `newSpaceCapabilityVerificationKey` **byte-identisch** mit dem aktuell installierten Key, MUSS der Broker mit **Erfolg** antworten (idempotente Wiederholung — die ursprüngliche Bestätigung ging verloren; der Absender hat gewonnen). Idempotenter Erfolg gilt AUSSCHLIESSLICH für diesen aktuellen Zustand — nie für historische Generationen.
- In jedem anderen Fall mit `newGeneration <= aktuelle Generation` (abweichender Key für die aktuelle Generation ODER jede historische Generation, auch mit seinerzeit identischem Key) MUSS der Broker mit dem dedizierten Fehlercode **`GENERATION_TAKEN`** ablehnen: Der Space ist weiterrotiert, das Material des Absenders ist nicht (mehr) das installierte — er MUSS konvergieren statt committen. `AUTH_INVALID` ist für diesen Fall verboten — es bleibt echten Autorisierungs-/Signaturfehlern vorbehalten.

Damit gilt clientseitig: identischer Retry → Erfolg ⇒ das eigene Material ist installiert (committen und verteilen); `GENERATION_TAKEN` ⇒ ein anderer Admin hat gewonnen (eigenes Material verwerfen, auf die eintreffende `key-rotation` konvergieren, niemals das eigene Material committen).

**Cache-Invalidierung bei Rotation (MUSS, sicherheitskritisch).** Nach erfolgreicher `space-rotate`-Verarbeitung MUSS der Broker **sofort alle gecachten Capability-Scopes für diese `spaceId` mit `generation < newGeneration` über ALLE offenen WebSockets ALLER betroffenen DIDs invalidieren** — nicht erst beim nächsten Reconnect und nicht erst bei `validUntil`. Andernfalls könnte ein gerade entfernter Member über seinen noch offenen Socket weiter in den durablen Log schreiben; Member-Entfernung ist der einzige Zweck der Rotation und liefe sonst ins Leere. Ein Schreib-/Leseversuch mit einer Capability alter Generation wird mit `CAPABILITY_GENERATION_STALE` abgelehnt; der Client muss eine erneuerte Capability beschaffen und neu `present-capability`-en.

### Space-Registrierung (`space-register`)

Beim Erstellen eines Space registriert der Ersteller ihn beim Broker (Detail-Shape siehe [Sync 005](005-gruppen.md#initiale-space-registrierung)). Wie alle Broker-Management-Frames trägt `space-register` seinen Claim als **Inner-JWS**, signiert mit dem (noch einzigen) **Admin Key**:

```json
{
  "type": "space-register",
  "registrationJws": "<JWS Compact Serialization>"
}
```

Der JWS-Payload MUSS `{ "type": "space-register", "spaceId": "<uuid>", "spaceCapabilityVerificationKey": "<base64url>", "adminDids": ["did:key:..."] }` sein.

**Trust-on-first-use + Konfliktregel (MUSS).** Beim Erst-Register existiert noch keine Admin-Liste, gegen die der Broker prüfen könnte. Der Broker verifiziert daher nur, dass der JWS gegen eine der im Payload genannten `adminDids` signiert ist (self-asserting), und bindet dann `(spaceId → spaceCapabilityVerificationKey, adminDids)` **first-writer-wins**:

- Ein späterer `space-register` für dieselbe `spaceId` mit **identischem** Inhalt → idempotent akzeptieren.
- Ein späterer `space-register` mit **abweichendem** `spaceCapabilityVerificationKey` oder Admin-Set → **ablehnen** mit `SPACE_ALREADY_REGISTERED`. Änderungen laufen ausschließlich über die signierten Frames `space-rotate`/`admin-add`/`admin-remove`.
- Ein `space-register` für eine `docId`, die bereits ein **Personal-Doc-Owner-Binding** (TOFU) trägt → **ablehnen** mit `PERSONAL_DOC_OWNER_MISMATCH`, es sei denn der Inner-JWS ist **vom gebundenen Owner signiert** (legitimer, owner-signierter Personal→Space-Upgrade; löscht das Owner-Binding atomar mit der Space-Eintragung). Die bloße Nennung der Owner-DID in `adminDids` genügt **nicht** — siehe [Persönliche Dokumente](#persönliche-dokumente).

`spaceId` ist eine nicht-ratbare zufällige UUID v4; Pre-Squatting setzt Kenntnis der `spaceId` voraus (Insider). Bei vollständigem Verlust des Broker-State DARF ein aktueller Admin den Space identisch re-registrieren (idempotenter Recovery-Pfad).

**Scope-Invalidierung bei Erst-Register (MUSS).** Vor der ersten `space-register`-Verarbeitung gilt eine `docId` als Personal-Doc (kein Registereintrag), sodass Sockets self-issued Personal-Scopes dafür cachen könnten. Nach erfolgreichem initialem `space-register` für eine `docId` MUSS der Broker daher alle zuvor für diese `docId` gecachten **Personal-Doc-Scopes** über ALLE offenen WebSockets verwerfen (analog zur [Cache-Invalidierung bei Rotation](#capability-widerruf-über-rotation)). Folgezugriffe MÜSSEN über den Space-Pfad neu `present-capability`-en. Andernfalls könnte ein Socket mit einem vor dem Register gecachten Personal-Scope den Space-Pfad-Zwang („Existiert eine `space-register`-Eintragung → nur Space-Pfad") auf einer offenen Verbindung umgehen.

### Admin-Management

Admins können weitere Admins hinzufügen oder entfernen. Beide Frames tragen ihren Claim als **Inner-JWS**, signiert mit einem **bestehenden Admin Key** für diesen Space (sonst `AUTH_INVALID`):

```json
{ "type": "admin-add", "adminChangeJws": "<JWS Compact Serialization>" }
```

```json
{ "type": "admin-remove", "adminChangeJws": "<JWS Compact Serialization>" }
```

Der JWS-Payload MUSS exakt `{ "type": "admin-add", "spaceId": "<uuid>", "newAdminDid": "did:key:..." }` bzw. `{ "type": "admin-remove", "spaceId": "<uuid>", "removedAdminDid": "did:key:..." }` sein; der JWS-`kid` referenziert die signierende `adminDid`.

**Idempotenter Self-`admin-remove` (MUSS).** Referenziert der `kid` eine DID, die NICHT (mehr) in der Admin-Liste steht, gilt vor dem `AUTH_INVALID`-Reject eine Ausnahme: Ist der Signer identisch mit `removedAdminDid` und diese DID bereits nicht (mehr) in der Admin-Liste, MUSS der Broker mit **Erfolg** antworten (idempotente Wiederholung eines bereits durchgesetzten Self-Remove — die Erfolgsbestätigung ging verloren). Das ist sicher: Der Claim „entferne mich selbst" der bereits entfernten Partei ist ein No-op und verleiht keinerlei Autorität. Für alle anderen Signer-Konstellationen bleibt `AUTH_INVALID` unverändert.

### Persönliche Dokumente

Für das persönliche Dokument (Identität, Keys) stellt der User sich seine eigene Capability aus. Das persönliche Dokument hat kein Space Capability Key Pair — stattdessen signiert der User die Capability direkt mit seinem **Identity Key** (DID).

**Wire-Form (MUSS).** Die Personal-Doc-Capability nutzt **dasselbe Payload-Schema** wie die Space-Capability ([Capability-Format](#capability-format)) mit folgenden festen Bindungen — kein separater Payload-Typ, kein zusätzliches `issuer`-Feld:

| Feld | Wert bei Personal-Doc |
|------|----------------------|
| `type` | `"capability"` |
| `spaceId` | die deterministische **Personal-Doc-ID** (= `docId`, siehe [Sync 006](006-personal-doc.md#deterministische-document-id)) |
| `audience` | die Owner-DID |
| `permissions` | `["read", "write"]` |
| `generation` | `0` — Personal-Docs werden in `wot-sync@0.1` **nicht** rotiert; der Scope-Cache speichert Generation `0` |
| `issuedAt` / `validUntil` | wie bei Space-Capabilities |

Der `kid` im JWS-Header MUSS die **Verification-Method-ID des Identity Keys** des Owners sein (`<did>#<vm>`, **nicht** `wot:space:…`); signiert wird mit dem Identity Key. Ein separates `issuer`-Feld entfällt — der „Issuer" ist implizit die `kid`-DID, und die self-issued-Bedingung ist `kid`-DID = `audience` = authentifizierte DID.

**Broker-Erkennung (MUSS).** Der Broker unterscheidet den Pfad anhand der `space-register`-Eintragung für die `docId`:

- Existiert **keine** `space-register`-Eintragung für `docId` → Personal-Doc-Pfad: Der Broker resolved die authentifizierte DID zu ihrem Ed25519 Identity Key, verifiziert das Capability-JWS damit und prüft `kid`-DID = `audience` = authentifizierte DID sowie `spaceId` = `docId` (Wire-Form oben). Der Broker kann **nicht** kryptographisch beweisen, dass `docId` die deterministische Personal-Doc-ID *dieser* DID ist (sie ist seed-abgeleitet, broker-blind). Für die **Inhalts-Vertraulichkeit** ist das unkritisch (Personal-Doc-Inhalt liegt unter einem nur dem Eigentümer bekannten Schlüssel). Die Selbst-Autorisierung (`kid`-DID = `audience` = auth-DID) beweist jedoch nur **Selbst-Autorisierung, nicht Besitz** der `docId`: ein Fremder, der die `docId` lernt, könnte sich eine self-issued Capability mit eigener DID ausstellen und so in den durablen Log schreiben (Integrität) oder Sync-Metadaten lesen. Dagegen greift das **Owner-Binding (TOFU)** unten.
- Existiert **eine** `space-register`-Eintragung für `docId` → greift **nur** der Space-Pfad; ein self-issued-Versuch auf eine registrierte `docId` wird abgelehnt. Damit kann der Personal-Pfad keine Space-`docId` umgehen.

**Owner-Binding (TOFU, MUSS).** Beim **ersten erfolgreichen `present-capability`** für eine Personal-`docId` (keine `space-register`-Eintragung) bindet der Broker `(docId → authentifizierte DID)` **durabel**, first-writer-wins. Danach gilt für diese owner-gebundene `docId`:

- Ein **`present-capability`** von einer **anderen** authentifizierten DID MUSS mit **`PERSONAL_DOC_OWNER_MISMATCH`** abgelehnt werden und **DARF keinen Capability-Scope cachen** — der Reject greift schon auf dem **Control-Pfad**, nicht erst bei Write/Read.
- Jede `log-entry`- oder `sync-request`-Nachricht von einer **anderen** DID wird ebenfalls mit **`PERSONAL_DOC_OWNER_MISMATCH`** abgelehnt — geprüft **vor** dem Capability-Scope-Cache: Schreiben wird weder gespeichert noch relayed, Lesen liefert **keine** `sync-response` (kein Metadaten-Leak).
- Geräte **derselben** DID (geteilter Seed) re-präsentieren und re-claimen **idempotent** (Multi-Device).

> **Vertrauensgrenze (akzeptiert).** Die `docId` ist seed-abgeleitet und broker-blind, also ein Bearer-Secret. Ein Fremder, der die `docId` **vor** dem ersten `present-capability` des Eigentümers lernt, kann das Binding pre-squatten (TOFU-pre-squat) — außerhalb des Schutzziels.

**Anti-Escalation gegen `space-register` (MUSS).** Ein `space-register` auf eine `docId`, die bereits ein Owner-Binding (TOFU) trägt, wird mit **`PERSONAL_DOC_OWNER_MISMATCH`** abgelehnt, **es sei denn der `space-register`-Inner-JWS ist vom gebundenen Owner signiert** (`kid`-DID = Owner-DID). Beim legitimen, owner-signierten Upgrade löscht der Broker das Owner-Binding **atomar** mit der Space-Eintragung (eine `docId` ist nie gleichzeitig space-registriert und owner-gebunden). Die bloße Nennung der Owner-DID in `adminDids` genügt **nicht**: `adminDids` ist self-asserted und der Inner-JWS beweist nur, dass der Signer *irgendein* Admin ist — ein Fremder könnte sonst den Owner als Decoy-Co-Admin listen, selbst signieren und über den Space-Pfad (der das Owner-Gate via `isSpaceRegistered` abschaltet) den Owner aussperren/poisonen.

**Unterschied zum Space-Capability-Modell:** Bei Spaces signiert der geteilte `spaceCapabilitySigningKey`, bei Personal Docs signiert der persönliche Identity Key (DID). Das ist eine bewusste Vereinfachung — ein Personal Doc hat genau einen Eigentümer, kein Gruppen-Key-Management nötig. Die Capability-Felder (`spaceId`, `generation`, `validUntil`) werden analog verwendet, aber `spaceId` wird durch die deterministische Personal-Doc-ID ersetzt (siehe [Sync 006](006-personal-doc.md)).

## Broker-Kanäle

Der Broker bietet zwei Kanäle:

- **Log-Sync:** Pull-basierter Austausch von Log-Einträgen für Dokumente. Der Broker kann verbundene Clients über neue Einträge informieren.
- **Inbox:** Store-and-Forward für direkte verschlüsselte Nachrichten. Inbox-Nachrichten werden pro aktivem Device vorgehalten und erst nach ACK des jeweiligen Devices gelöscht.

## Zwei Message-Familien (NORMATIV)

Sync 003 definiert **zwei distinkte Message-Familien** mit unterschiedlichen Envelopes, Schemata und Authentisierungsmodellen:

| Familie | Zweck | Envelope | Authentisierung | Beispiele |
|---|---|---|---|---|
| **WoT Transport Envelope** | Peer-zu-Peer-Nachrichten (über Broker oder direkt P2P), inklusive persistierter Inhalte und replayable Transporte | DIDComm-v2-kompatible Hülle mit `id`, `typ`, `type`, `from`, `to?`, `created_time`, `body`, `thid?`, `pthid?` | Inner-Crypto im `body` (JWS, ECIES) **oder** authentifizierter Transportkanal — siehe [Authentizität pro Message-Typ](#authentizität-pro-message-typ-normativ) | `log-entry/1.0`, `space-invite/1.0`, `member-update/1.0`, `key-rotation/1.0`, `sync-request/1.0`, `sync-response/1.0`, `ack/1.0`, `inbox/1.0` |
| **Broker Control-Frame** | Transiente Client↔Broker-Steuernachrichten für Auth-Handshake und Fehlerrückmeldung. Nicht persistiert, nicht replayable, nicht DIDComm-kompatibel | Schlanke Form `{ type, thid?, body? }` plus typspezifische Felder; `device-revoke` verwendet stattdessen die geschlossene Form `{ type, revocationJws }` | Vor dem Handshake: explizite Felder (z. B. `signature` in `challenge-response`). Nach dem Handshake: authentifizierter WebSocket-Kontext | `register`, `challenge`, `challenge-response`, `registered`, `device-revoke`, `error/1.0` |

Daraus folgt normativ:

- Eine **WoT Transport Envelope MUSS** dem in [WoT Transport Envelope](#wot-transport-envelope-didcomm-v2-kompatibel) definierten Format genügen und in der dortigen Typtabelle erscheinen.
- Ein **Broker Control-Frame DARF NICHT** WoT Transport Envelope-Felder (`id`, `typ`, `from`, `to`, `created_time`) tragen. Er erscheint nur in der [Control-Frame-Typtabelle](#broker-control-frames-normativ).
- DIDComm-v2-Bibliotheken werden **nur** Transport Envelopes parsen können, **nicht** Control-Frames. Das ist beabsichtigt: Control-Frames sind Broker-Protokoll-Interna ohne Anspruch auf Interop.

## WoT Transport Envelope (DIDComm-v2-kompatibel)

WoT-Peer-Nachrichten (über Broker oder direkt) verwenden einen einheitlichen **WoT Transport Envelope**, dessen Format absichtlich mit dem DIDComm v2 Plaintext Message Format ([DIF DIDComm Messaging v2](https://identity.foundation/didcomm-messaging/spec/v2.0/)) kompatibel ist. Der Kompatibilitätsanspruch ist bewusst eng: etablierte DIDComm-v2-Libraries sollen Transport Envelopes parsen und routen können. WoT übernimmt nicht den DIDComm-Crypto-Stack, keine DIDComm-JWE/Authcrypt-Verschlüsselung und keine Mediator-Protokolle.

> **Naming hint:** In DIDComm-v2-Terminologie heißt dieses Format "Plaintext Message". Wir verwenden in WoT-Spec und Implementierungen den Begriff **"Transport Envelope"**, um klarzustellen, dass die *Envelope-Schicht* keine Crypto trägt, der *Inhalt im `body`* aber praktisch immer kryptographisch geschützt ist (JWS, ECIES, oder über den authentifizierten Transportkanal). Siehe [Authentizität pro Message-Typ](#authentizität-pro-message-typ-normativ).

Persistente WoT-Objekte (Attestation-JWS, Capability-JWS, Log-Entry-JWS, verschlüsselte Dokument-Payloads) sind **keine DIDComm Messages**. Sie DÜRFEN im `body` eines WoT Transport Envelopes transportiert werden. Ihre Autorität und Integrität ergeben sich aus dem inneren JWS, der Capability, Broker-Authentisierung oder der dokumentenspezifischen Verschlüsselung — nicht aus `from`, `to` oder anderen Envelope-Feldern.

### Transport Envelope (Beispiel)

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
| `typ` | String | Ja | Media Type. Für WoT Transport Envelopes MUSS `application/didcomm-plain+json` gesetzt sein. |
| `type` | URI | Ja | Nachrichtentyp als URI (siehe Tabelle unten) |
| `from` | DID | Ja | Absender-DID |
| `to` | Array von DIDs | Bedingt | Empfänger-DID(s). Pflicht bei Inbox-Nachrichten. |
| `created_time` | Integer (Unix-Seconds) | Ja | Erstellungszeitpunkt (UTC Epoch Seconds), kompatibel mit DIDComm v2.1. |
| `thid` | UUID v4 | Optional | Thread-ID. Verknüpft Nachrichten die zu einer Konversation gehören (z.B. Request + Response). Die erste Nachricht eines Threads setzt `thid = id`; Folgenachrichten tragen denselben `thid`. |
| `pthid` | UUID v4 | Optional | Parent-Thread-ID. Verweist auf einen übergeordneten Thread — für verschachtelte Konversationen (z.B. ein Sub-Protokoll das innerhalb eines größeren Flows läuft). |
| `body` | Object | Ja | Nachrichteninhalt. Struktur abhängig vom `type`. |

Das generische Transport-Envelope-Format DARF `to` weglassen, wenn der konkrete Nachrichtentyp seine Empfänger aus dem authentifizierten Transportkontext oder aus dem Body ableitet, z.B. bei Broker-gebundenen `sync-request`/`sync-response` Nachrichten. Konkrete Nachrichtentypen DÜRFEN strengere Regeln definieren. Inbox- und direkt adressierte Nachrichten MÜSSEN `to` setzen.

`thid` und `pthid` MÜSSEN — wenn gesetzt — kanonische lowercase UUID v4 sein, identisch zur `id`-Form. Das stimmt das generische Schema mit den message-typ-spezifischen Schemas überein (`space-invite`, `member-update`, `key-rotation`, etc.), die diese Striktheit bereits durchsetzen.

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

### Authentizität pro Message-Typ (NORMATIV)

Der **Envelope selbst trägt keine Crypto** — das ist Absicht. Authentizität und Integrität liegen entweder im `body` (Inner-JWS oder ECIES-Wrap) oder werden durch den authentifizierten Transportkanal hergestellt (post-handshake WebSocket nach Broker-Challenge-Response, oder authentifizierter P2P-Kanal). Doppelte Authentifizierung (Envelope-JWS über Body mit innerer JWS) ist zu vermeiden — sie erhöht nur Größe und Verarbeitungsaufwand ohne Sicherheitsgewinn.

Drei Envelope-Formen sind definiert:

1. **Plaintext** — JSON-Envelope ohne Envelope-Signatur, ohne Envelope-Verschlüsselung. Der Inhalt im `body` ist entweder selbst-authentifizierend (Inner-JWS) oder wird über den Transportkanal authentifiziert. **Standard für die meisten Sync-Messages.**
2. **Encrypted** — Body mit **ECIES** verschlüsselt (siehe [Sync 001](001-verschluesselung.md#peer-to-peer-verschlüsselung-ecies)). Der Inner-JWS innerhalb des verschlüsselten Bodys bindet den Sender; ECIES allein bindet ihn nicht. Standard für Inbox- und Membership-Messages.
3. **Signed** — Envelope-JWS. Mechanismus für zukünftige ephemere Nachrichten ohne sinnvollen Inhalts-Body. Aktuell verwendet kein in dieser Spec definierter Message-Typ diese Form; zukünftige Slices, die sie nutzen, MÜSSEN ihren Message-Typ in der unten stehenden Authentizitätsmatrix sowie in einer dedizierten Wire-Format-Sektion ergänzen.

Die folgende Tabelle ist normativ. Eine Implementation MUSS diese Authentisierung für jeden Message-Typ durchsetzen:

| Familie | Nachrichtentyp | Authentizität durch | Envelope-Form |
|---|---|---|---|
| Transport | `log-entry/1.0` | Inner Log-Entry-JWS im Body (persistentes WoT-Objekt, bindet `authorKid`) | Plaintext |
| Transport | `sync-request/1.0`, `sync-response/1.0` | Authentifizierter WebSocket-Kontext (Sender-Identität aus Challenge-Response) | Plaintext |
| Transport | `ack/1.0` | Authentifizierter WebSocket-Kontext | Plaintext |
| Transport | `inbox/1.0` | Inner JWS im Klartext-Body (bindet Sender) + ECIES-Wrap | Encrypted (ECIES) |
| Transport | `space-invite/1.0`, `member-update/1.0`, `key-rotation/1.0` | Inner JWS im Klartext-Body + ECIES-Wrap | Encrypted (ECIES) |
| Control-Frame | `register` | Kein Crypto im Frame — Identität wird erst durch nachfolgenden `challenge-response` gebunden | (kein Envelope) |
| Control-Frame | `challenge` | Broker→Client, vor Handshake; vertrauenswürdig durch Transport (HTTPS/WSS) | (kein Envelope) |
| Control-Frame | `challenge-response` | Explizites `signature`-Feld im Frame: unpadded Base64URL einer Ed25519-Signatur über den JCS-kanonisierten Broker-Auth-Transcript (siehe [Wire-Encoding der signature](#wire-encoding-der-signature-muss)) | (kein Envelope) |
| Control-Frame | `registered` | Authentifizierter WebSocket-Kontext (post-handshake) | (kein Envelope) |
| Control-Frame | `device-revoke` | Inner JWS gegen den Identity Key der `did` (persistenter Revocation-Claim) | (kein Envelope) |
| Control-Frame | `present-capability` | Inner Capability-JWS im Frame; Broker verifiziert gegen `spaceCapabilityVerificationKey` (Space) bzw. Identity Key der DID (Personal-Doc) | (kein Envelope) |
| Control-Frame | `space-register` | Inner JWS gegen einen der genannten `adminDids` (TOFU, first-writer-wins) | (kein Envelope) |
| Control-Frame | `space-rotate`, `admin-add`, `admin-remove` | Inner JWS gegen einen **registrierten Admin Key** des Space | (kein Envelope) |
| Control-Frame | `error/1.0` | Authentifizierter WebSocket-Kontext, Broker→Client (Broker spricht in seinem eigenen Namen) | (kein Envelope) |

**Konsequenz für Control-Frames:** `challenge-response`, `device-revoke`, `present-capability`, `space-register`, `space-rotate`, `admin-add` und `admin-remove` tragen eigene Signaturen, weil sie kryptographische Claims machen, die vor oder über den Kanal hinaus gelten. Alle übrigen Control-Frames (`register`, `challenge`, `registered`, `error/1.0`) sind reine Transport-Steuerung und brauchen keine zusätzliche Signatur. Capability-JWS und Admin-Claim-JWS sind persistente WoT-Objekte, die hier — wie der Revocation-Claim bei `device-revoke` — als opaker String in einem transienten Control-Frame transportiert werden; das verletzt die Control-Frame-Definition nicht (der Frame trägt keine Transport-Envelope-Felder).

### Signatur (WoT Envelope-JWS)

Wenn ein Envelope signiert wird (Form 3 oben), geschieht das als **JWS Compact Serialization** — identisch mit unseren Attestations ([Identity 002](../01-wot-identity/002-signaturen-und-verifikation.md)). Anders als beim Transport Envelope beanspruchen WoT Envelope-JWS keine DIDComm-Signed-Message-Kompatibilität; sie sind ein WoT-spezifisches Signaturprofil.

1. Transport Envelope mit JCS kanonisieren (RFC 8785)
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
| `.../ack/1.0` | Inbox | Per-Device Empfangs-/Persistenzbestätigung für Inbox-Nachrichten (referenziert `id` der Original-Nachricht). Log-Sync DARF `ack/1.0` NICHT verwenden; siehe [Log-Sync vs. Inbox-ACK](#log-sync-vs-inbox-ack-normativ). |

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

**Broker-Ingest-Verifikation (MUSS).** Für den durablen Log (nicht mehr transiente Queue) MUSS der Broker den Log-Entry-JWS **vollständig verifizieren, bevor** er Autor-Bindung, Content-Hash/Kollisionsprüfung und Store/Relay durchführt:

1. `alg = EdDSA` (Algorithmus-Validierung, siehe [Identity 002](../01-wot-identity/002-signaturen-und-verifikation.md#algorithmus-validierung-muss));
2. DID aus `authorKid` extrahieren (Teil vor `#`), via `resolve()` den Public Key der passenden `verificationMethod` bestimmen;
3. JWS-Signatur gegen diesen Public Key gültig;
4. `kid == authorKid` (Header-`kid` identisch zum Payload-`authorKid`);
5. Payload-Schema vollständig (`seq`, `deviceId`, `docId`, `authorKid`, `keyGeneration`, `data`, `timestamp`).

Schlägt eine dieser Prüfungen fehl → `AUTH_INVALID`; der Eintrag wird **weder gespeichert noch relayed**. Erst nach erfolgreicher Verifikation extrahiert der Broker die jetzt **authentifizierten** Felder `docId`, `deviceId`, `seq` für Indexing, [Autor-Bindung](#log-eintrag-autor-bindung-muss), Kollisionserkennung und Sync-Anfragen.

Ohne diese Pflicht-Verifikation würde die Autor-Bindung ins Leere laufen: ein Angreifer könnte einen JWS mit fremder `deviceId` und passend gesetztem `authorKid`-Payload, aber **eigener** Signatur einschleusen — der Broker würde den `(docId, deviceId, seq)`-Slot im durablen Log dauerhaft vergiften, obwohl der Angreifer die fremde DID nicht kontrolliert. (In der früheren transienten Queue war Signaturprüfung optional, weil der Log nicht persistierte; das gilt nicht mehr.)

**Broker-Ingest-Generations-Gate (MUSS, sicherheitskritisch).** Für eine registrierte Space-`docId` (es existiert ein `space-register`-Eintrag mit einer `generation`) MUSS der Broker — nach JWS-Verifikation und [Autor-Bindung](#log-eintrag-autor-bindung-muss), vor Store/Relay — einen `log-entry` ablehnen, dessen `keyGeneration` **strikt kleiner** als die aktuelle `space.generation` dieses Space ist → `KEY_GENERATION_STALE`; der Eintrag wird **weder gespeichert noch relayed**. Der Vergleich liest die **durable** `space.generation` (aus `space-register`/`space-rotate`), nicht den Capability-Scope-Cache — er ist damit race-sicher gegenüber einer nebenläufigen Rotation.

Wirkung: Ein entfernter Member besitzt nur den **alten** Content-Key → schreibt `keyGeneration = alt` → nach der Rotation `< space.generation` → abgelehnt, **unabhängig vom Scope-Cache-Zustand**. Das ist die durable Safety-Grenze, die das Schreibfenster nach einer Member-Entfernung schließt (zusammen mit der sofortigen [Cache-Invalidierung bei Rotation](#capability-widerruf-über-rotation)).

`keyGeneration` **gleich oder größer** als `space.generation` MUSS der Broker **akzeptieren** — auch eine ihm noch unbekannte zukünftige Generation: ein legitimer Member, der die `key-rotation` bereits erhielt, kann an einen Broker schreiben, dessen `space-rotate` noch unterwegs ist; den Eintrag zu verwerfen würde ihn dauerhaft verlieren, falls dieser Broker verlassen wird. Ein entfernter Member kann keinen gültigen `≥`-Eintrag erzeugen, da ihm der neue Content-Key fehlt. **Nicht puffern** (broker-blinder State). Für Spaces mit `generation = 0` (nie rotiert, z.B. single-member private Spaces) ist `0 < 0` falsch → akzeptiert.

Ein hinterherhinkender legitimer Member, dessen Alt-Gen-Eintrag mit `KEY_GENERATION_STALE` abgelehnt wurde, re-emittiert nach Erhalt der `key-rotation` unter einer **neuen `seq`** und der neuen `keyGeneration` (siehe [Sync 002 Lokaler Schreibvorgang](002-sync-protokoll.md#lokaler-schreibvorgang)) — **nicht** unter derselben `seq` (das würde bei einem Broker, der den Alt-Gen-Eintrag bereits speicherte, `SEQ_COLLISION_DETECTED` auslösen).

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

Der Client MUSS `SEQ_COLLISION_DETECTED` als **harten Fehler** behandeln, **nicht** als Restore/Clone-Signal: die Ablehnung trifft den Schreibpfad, nachdem der Client bereits einen kollidierenden Eintrag erzeugt hat — die proaktive `broker_seq > local_seq`-Erkennung aus [Sync 002 seq-Konsistenz](002-sync-protokoll.md#seq-konsistenz-muss) war also wirkungslos und es liegt echter `seq`-/Nonce-Reuse vor (z.B. ein Wipe, der die `deviceId` überleben ließ, oder verletzte Cross-Tab-Atomarität). Der Client MUSS den Fehler **surfacen** und DARF **nicht** still eine neue `deviceId` minten — das würde genau den AES-256-GCM-Nonce-Reuse maskieren, den die obige Kollisionsprüfung als letzte Verteidigungslinie erkennt. Der **legitime** Restore/Clone-Pfad (neue `deviceId` generieren, alte per `device-revoke` deaktivieren, ab `seq=0` neu beginnen) wird ausschließlich **proaktiv** über `broker_seq > local_seq` ausgelöst, bevor ein kollidierender Eintrag entsteht.

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
| `heads` | Object | Ja | Pro bekanntem `deviceId` die höchste **lückenlose** seq, die ich habe (kontiger Vollständigkeits-Cursor, siehe [Sync 002](002-sync-protokoll.md#vollstaendigkeits-cursor-luecken-und-pagination)) |
| `limit` | Integer | Nein | Maximale Anzahl Einträge in der Antwort (Default: 100) |

**Heads-Semantik:** Ein leerer oder fehlender Eintrag für eine `deviceId` bedeutet "ich habe nichts von diesem Device" — der Antwortende sendet dann alle verfügbaren Einträge ab `seq=0`. Ein bekannter Eintrag bedeutet "ich habe bis inklusive seq N" — gesendet werden Einträge ab `seq=N+1`. Der `heads`-Wert pro `deviceId` ist die höchste **lückenlose** `seq` (kontiger Vollständigkeits-Cursor), nicht die höchste bekannte; oberhalb einer Lücke empfangene Einträge rücken ihn nicht vor (siehe [Sync 002 Vollständigkeits-Cursor](002-sync-protokoll.md#vollstaendigkeits-cursor-luecken-und-pagination)).

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
| `heads` | Object | Ja | Die aktuell höchsten **bekannten** seq pro deviceId beim Antwortenden (Maximum, für Heads-Diskrepanz-Diagnostik) — **nicht** der kontige Vollständigkeits-Cursor, anders als bei `sync-request.heads` |
| `truncated` | Boolean | Ja | `true` wenn durch `limit` abgeschnitten — der Fragende MUSS einen weiteren `sync-request` mit aktualisierten Heads senden (Terminierung und Lücken-Behandlung siehe [Sync 002](002-sync-protokoll.md#vollstaendigkeits-cursor-luecken-und-pagination)) |

**Threading:** Der `sync-response` MUSS denselben `thid` wie der zugehörige `sync-request` tragen.

**Heads-Diskrepanz-Detection:** Der Fragende kann die erhaltenen `heads` mit denen anderer Broker/Peers vergleichen, um Censorship oder Split-Brain zu erkennen (siehe [Sync 002](002-sync-protokoll.md#censorship--und-split-brain-detection)).

**`sync-response.heads` sind NICHT der nächste Request-Cursor (MUSS).** Sie sind das Maximum des Antwortenden (Diagnostik), nicht der kontige Vollständigkeits-Cursor des Fragenden. Der nächste `sync-request.heads` MUSS aus dem **lokalen kontigen Cursor** nach Verarbeitung der verifizierten Einträge berechnet werden (siehe [Sync 002 Vollständigkeits-Cursor](002-sync-protokoll.md#vollstaendigkeits-cursor-luecken-und-pagination)) — niemals durch Übernahme von `sync-response.heads`, sonst werden lokale Lücken übersprungen.

#### `ack/1.0` — Empfangsbestätigung (NORMATIV)

`ack/1.0` ist **ausschließlich für den Inbox-Kanal** definiert (per-Device Store-and-Forward). Log-Sync DARF `ack/1.0` NICHT verwenden — dort ist die Bestätigung implizit durch den nächsten `sync-request` (siehe [Log-Sync vs. Inbox-ACK](#log-sync-vs-inbox-ack-normativ)).

##### Envelope und Body

Ein Inbox-ACK ist ein WoT Transport Envelope mit:

- `type`: `https://web-of-trust.de/protocols/ack/1.0`
- `thid`: MUSS gesetzt sein und MUSS die `id` der ursprünglichen Inbox-Nachricht tragen (lowercase UUID v4 nach generischem [Plaintext-thid-Pattern](#felder)).
- `to`: OPTIONAL. Inbox-ACKs werden ausschließlich über den authentifizierten WebSocket-Kontext an den Broker zugestellt; die effektive Routing-Information steht in `body.messageId`. Implementierungen DÜRFEN `to` weglassen.
- `body`:

```json
{
  "messageId": "550e8400-e29b-41d4-a716-446655440000"
}
```

- `body.messageId`: MUSS die kanonische lowercase UUID v4 der ursprünglichen Inbox-Nachricht (`id`) sein. MUSS mit `thid` übereinstimmen, wenn `thid` gesetzt ist. Weitere Body-Felder sind NICHT definiert; Empfänger MÜSSEN unbekannte Body-Felder ignorieren (forward-compat).

> Diese Bindungen sind nicht durch JSON-Schema oder ein statisches Vektor-Fixture validierbar — sie sind Protokollzustand pro Verbindung und Inbox. Implementierungen MÜSSEN zur Laufzeit prüfen, dass (a) `thid` und `body.messageId` einer real existierenden, nicht bereits acknowledgten Inbox-Nachricht in der Inbox dieses authentifizierten Devices entsprechen, (b) `body.messageId` und `thid` (falls beide gesetzt) übereinstimmen, und (c) der `type` der referenzierten Nachricht ein Inbox-Type ist (siehe [Log-Sync vs. Inbox-ACK](#log-sync-vs-inbox-ack-normativ)). Diese Checks ersetzen NICHT die Schema-Validierung der Envelope-Form; sie ergänzen sie.

##### ACK-Vorbedingungen

Der Empfänger schickt `ack` nach erfolgreichem Verarbeiten einer Inbox-Nachricht. Erfolgreich verarbeitet bedeutet:

1. ECIES-Entschlüsselung erfolgreich, falls die Nachricht verschlüsselt war.
2. Inneres JWS oder persistentes WoT-Objekt verifiziert.
3. Replay-Prüfung bestanden oder die Nachricht wurde als Duplikat sicher erkannt.
4. Resultierender lokaler State wurde angewendet oder die Nachricht wurde gemaess [Sync 002](002-sync-protokoll.md) durabel in der **Pending-Inbox** gepuffert. `Pending` bedeutet hier: crash-sichere persistente Speicherung (nicht nur volatil im RAM) zusammen mit den fuer die spaetere Aufloesung und Anwendung erforderlichen Metadaten, mindestens `messageId` sowie Abhaengigkeits-/Missing-Dependency-Metadaten.

Der Broker kann die Nachricht dann aus der Inbox **dieses authentifizierten Devices** entfernen. Er DARF sie nicht aus anderen Device-Inboxen derselben DID entfernen. Wenn der Client eine Nachricht wegen fehlender Abhaengigkeiten nur volatil im Speicher haelt, DARF er sie noch nicht ACKen.

Ein `ack/1.0` ist ausschliesslich eine Transport-/Persistenzbestaetigung fuer genau dieses Device. Es bestaetigt nicht, dass ein Inhaltsartefakt semantisch angenommen, vertraut, gelesen, angezeigt oder veroeffentlicht wurde. Insbesondere definiert `wot-trust@0.1` kein `attestation-ack`; ob ein Empfaenger eine Attestation spaeter oeffentlich zeigt, ergibt sich nur aus seiner bewussten Profil-Veroeffentlichung.

##### Log-Sync vs. Inbox-ACK (NORMATIV)

WoT-Sync hat zwei strukturell verschiedene Bestätigungsmechanismen, die NICHT gegenseitig austauschbar sind:

| Aspekt | Inbox-ACK (`ack/1.0`) | Log-Sync (implicit) |
|---|---|---|
| Geltungsbereich | 1:1-Inbox-Nachrichten (Attestation, Space-Invite, Member-Update, Key-Rotation) | Log-Sync (`log-entry/1.0`, `sync-request/1.0`, `sync-response/1.0`) |
| Form | Explizite Transport-Envelope-Nachricht | Implizit via `since-seq` im nächsten `sync-request` |
| Pro Device? | Ja — jede Device-Inbox separat | Pro `(deviceId, docId, seq)`-Tupel, geräteübergreifend |
| Was wird bestätigt? | Per-Device durable Persistenz oder Anwendung der Inbox-Nachricht | Dass der Client alle Log-Einträge bis zu einer bestimmten `seq` empfangen hat |
| Konsequenz beim Broker | Inbox-Slot für `(device, messageId)` darf gelöscht werden | Keine — Log-Einträge bleiben für andere Clients erhalten |

Implementierungen MÜSSEN `ack/1.0` ausschließlich für Inbox-Nachrichten erzeugen und akzeptieren. Ein `ack/1.0`, das auf einen `log-entry/1.0`, `sync-request/1.0` oder `sync-response/1.0` referenziert, ist normativ ungültig; Broker MÜSSEN ihn mit `MALFORMED_MESSAGE` ablehnen.

## Broker Control-Frames (NORMATIV)

Control-Frames sind die zweite Message-Familie neben dem WoT Transport Envelope (siehe [Zwei Message-Familien](#zwei-message-familien-normativ)). Sie fließen ausschließlich zwischen Client und Broker, sind transient und nicht persistiert, und folgen einem schlanken Format ohne DIDComm-Kompatibilitätsanspruch.

### Allgemeines Format

Ein Control-Frame ist ein JSON-Objekt mit mindestens dem Feld `type`, das den Frame-Typ als kurzen Bezeichner trägt (KEIN URI wie bei Transport Envelopes):

```json
{
  "type": "<frame-type>",
  "thid": "<optional, korreliert zu einer vorherigen Frame oder einem Transport Envelope>",
  ...typspezifische Felder
}
```

Control-Frame-`type` MUSS aus folgendem geschlossenem Vokabular kommen:

| Frame-Type | Richtung | Zweck | Body / typspezifische Felder |
|---|---|---|---|
| `register` | Client→Broker | Verbindungsaufbau, vor Challenge-Response | `did`, `deviceId` |
| `challenge` | Broker→Client | Broker schickt Auth-Nonce | `nonce` (Base64URL) |
| `challenge-response` | Client→Broker | Client beweist DID-Besitz | `did`, `deviceId`, `nonce`, `signature` (siehe [Wire-Encoding der signature](#wire-encoding-der-signature-muss)) |
| `registered` | Broker→Client | Broker bestätigt erfolgreiche Auth | `did`, `deviceId`, `isNewDevice` |
| `device-revoke` | Client→Broker | Signierter Revocation-Claim für eine Device-ID dieser DID | `revocationJws`; keine weiteren Top-Level-Felder (siehe [Device-Deaktivierung](#device-deaktivierung)) |
| `present-capability` | Client→Broker | Session-scoped Capability-Präsentation für eine `docId` | `capabilityJws`; keine weiteren Top-Level-Felder (siehe [Capability-Prüfung](#capability-prüfung-am-broker)) |
| `space-register` | Client→Broker | Erst-Registrierung eines Space (TOFU, first-writer-wins) | `registrationJws`; keine weiteren Top-Level-Felder |
| `space-rotate` | Client→Broker | Rotation des Space Capability Verification Key (Admin-signiert) | `rotationJws`; keine weiteren Top-Level-Felder |
| `admin-add` / `admin-remove` | Client→Broker | Admin-Liste eines Space ändern (Admin-signiert) | `adminChangeJws`; keine weiteren Top-Level-Felder |
| `error/1.0` | Broker→Client | Fehlerrückmeldung auf eine vorherige Nachricht | `thid` (Referenz auf ursprüngliche Anfrage), `body.code`, `body.message` |

Implementierungen MÜSSEN unbekannte Frame-Types als `MALFORMED_MESSAGE` ablehnen — Control-Frames sind **nicht erweiterbar** durch Drittparteien.

### Error-Response (`error/1.0`)

Wenn eine Sync-Anfrage nicht erfüllt werden kann oder ein Frame zurückgewiesen wird, antwortet der Broker mit einem `error/1.0`-Control-Frame:

```json
{
  "type": "error/1.0",
  "thid": "<thid der Original-Anfrage, oder null wenn nicht zuordenbar>",
  "body": {
    "code": "DOC_NOT_FOUND",
    "message": "Unbekannte docId"
  }
}
```

`error/1.0` ist ein **Control-Frame**, kein WoT Transport Envelope. Es trägt keine `id`, kein `typ`-Media-Type-Feld, kein `from`, kein `to`, kein `created_time`. Der Broker spricht in seinem eigenen Namen über den authentifizierten WebSocket — eine zusätzliche Envelope-Signatur ist nicht erforderlich und wäre konzeptionell falsch (der Broker hat keine DID-Authority über den Sync-Inhalt).

`body` enthält:

- `code` — String aus der unten stehenden Tabelle.
- `message` — frei wählbarer menschenlesbarer Hinweis, NICHT normativ.

Implementierungen DÜRFEN zusätzliche Felder in `body` setzen (z.B. `details` für strukturierte Diagnose-Daten). Empfänger MÜSSEN unbekannte Felder ignorieren (forward-compatible Erweiterung).

Normative Error-Codes:

| Code | Wann |
|------|------|
| `DOC_NOT_FOUND` | Dokument existiert beim Broker nicht |
| `CAPABILITY_REQUIRED` | Für `log-entry`-Ingest (`write`) oder `sync-request` (`read`) wurde keine gültige Capability dieser Session präsentiert (kein gecachter Scope für `docId`) |
| `CAPABILITY_INVALID` | Capability-Signatur ungültig |
| `CAPABILITY_EXPIRED` | Capability abgelaufen |
| `CAPABILITY_GENERATION_STALE` | Capability für alte Space-Keypair-Generation (nach Rotation) |
| `SPACE_ALREADY_REGISTERED` | `space-register` für eine bereits mit abweichendem Verification Key / Admin-Set registrierte `spaceId` (first-writer-wins) |
| `AUTHOR_MISMATCH` | Log-Eintrag-`authorKid`-DID ist nicht die für `deviceId` registrierte DID (Device-Registrierungs-Bindung) |
| `PERSONAL_DOC_OWNER_MISMATCH` | Personal-Doc-Owner-Binding (TOFU) liegt für eine **andere** DID vor — betrifft fremde `present-capability`, `log-entry`, `sync-request` und `space-register` auf eine owner-gebundene `docId`; **keine** Speicherung, **kein** Relay, **keine** `sync-response`, **kein** Scope-Cache. Der owner-signierte Personal→Space-Upgrade ist die Ausnahme (siehe [Persönliche Dokumente](#persönliche-dokumente)) |
| `DEVICE_NOT_REGISTERED` | Client-Device ist beim Broker nicht registriert |
| `DEVICE_REVOKED` | Device-ID ist als revoked markiert |
| `DEVICE_ID_CONFLICT` | Device-ID bereits für eine andere DID registriert |
| `SEQ_COLLISION_DETECTED` | Log-Eintrag mit `(docId, deviceId, seq)` existiert bereits mit anderem Content-Hash — **harter Fehler** (`seq`-/Nonce-Reuse auf dem Schreibpfad); Client MUSS surfacen, **nicht** still eine neue `deviceId` minten. Der legitime Restore/Clone läuft proaktiv über `broker_seq > local_seq` (siehe [Sync 002](002-sync-protokoll.md#seq-konsistenz-muss)) |
| `GENERATION_GAP` | `space-rotate` mit `newGeneration > aktuelle Generation + 1`; das Error-Frame traegt die installierte Broker-Generation als `currentGeneration`-Detail. Lokale Generation <= `currentGeneration`: Catch-Up + frisches Staging auf `currentGeneration + 1`. Lokale Generation > `currentGeneration`: Split-Brain — nicht automatisch reparierbar, surfacen, Staging behalten |
| `GENERATION_TAKEN` | `space-rotate` mit `newGeneration <= aktuelle Generation`, deren Material NICHT byte-identisch der aktuell installierte `(generation, verificationKey)`-Zustand ist — der Absender hat die Rotation nicht (mehr) gewonnen und MUSS auf das installierte Material konvergieren; die byte-identische Wiederholung des aktuellen Zustands wird stattdessen idempotent bestätigt (siehe [Capability-Widerruf über Rotation](#capability-widerruf-über-rotation)) |
| `KEY_GENERATION_STALE` | `log-entry` mit `keyGeneration` strikt kleiner als die aktuelle `space.generation` (Schreibversuch unter rotiertem-out Content-Key, z.B. ein entfernter Member nach Rotation) — weder gespeichert noch relayed; legitimer hinterherhinkender Member re-emittiert unter neuer `seq` + neuer `keyGeneration` |
| `MALFORMED_MESSAGE` | Nachricht oder Pflichtfeld ist syntaktisch ungültig, inklusive JSON-Parse-Fehler, malformed DID, malformed UUID v4 `deviceId`, malformed Base64URL-Nonce, malformed `signature`-Encoding, fehlender Pflichtfelder oder unbekannter Frame-Type |
| `AUTH_INVALID` | Challenge-Response-Signatur, Envelope-JWS oder Device-Revocation-Signatur ist well-formed aber kryptographisch ungültig — passt nicht zu DID, Device oder ausstehender Challenge |
| `NONCE_REPLAY` | Broker-Challenge-Nonce wurde bereits akzeptiert oder ist nicht mehr als ausstehende Challenge gültig |
| `RATE_LIMITED` | Rate-Limit überschritten |
| `INTERNAL_ERROR` | Server-Fehler |

Clients SOLLEN bei `CAPABILITY_EXPIRED` eine neue Capability anfordern (via Peer-Kontakt, da der Broker die Signatur nicht erzeugen kann).

### Erweiterbarkeit von Transport-Nachrichtentypen

Neue **WoT Transport Envelope**-Nachrichtentypen DÜRFEN von Extensions definiert werden — der `type`-URI ist auf der **Definitionsebene** offen erweiterbar. Für **Relaying/Queuing** gilt jedoch die [Relay-Whitelist](#relay-whitelist-muss): Ein Broker relayt/queued einen Transport-`type` **nur**, wenn er in der [Nachrichtentypen-Tabelle](#nachrichtentypen) steht **oder** durch eine explizite Broker-Policy bzw. registrierte Extension freigegeben ist; jeden anderen (unbekannten oder deprecated) `type` MUSS er mit `MALFORMED_MESSAGE` ablehnen und **nicht** speichern/weiterleiten. Ein Client, der einen ihm unbekannten — aber vom Broker durchgelassenen — Transport-`type` empfängt, MUSS die Nachricht ignorieren (nicht verwerfen; Forward-Compat client-seitig). Die frühere Regel „der Broker speichert Unbekanntes blind für andere Clients" entfällt: ein typ-agnostischer Relay wäre ein un-gegateter Kanal, über den ein entfernter Member nach Rotation alt-verschlüsselten Inhalt zustellen könnte.

Für **Broker Control-Frames** gilt das nicht: das Frame-Type-Vokabular ist geschlossen (siehe [Broker Control-Frames](#broker-control-frames-normativ)). Unbekannte Control-Frame-`type`-Werte MÜSSEN mit `MALFORMED_MESSAGE` abgelehnt werden, da Control-Frames Broker-Protokoll-Interna sind und keine Drittpartei-Erweiterung kennen.

### Envelope-Kompatibilität

Das WoT Transport Envelope ist **DIDComm-v2.1-kompatibel** auf Envelope-Ebene: `id`, `typ`, `type`, `from`, optional `to`, `created_time` (Unix-Seconds), `body`, `thid`/`pthid`. DIDComm-Bibliotheken können WoT Transport Envelopes lesen und routen. Dieser Anspruch endet an der Envelope-Grenze: Verschlüsselung, Signaturen, persistente WoT-Objekte, Broker-Authentisierung und Sync-Semantik bleiben WoT-spezifisch. Control-Frames (siehe [Broker Control-Frames](#broker-control-frames-normativ)) sind ausdrücklich **nicht** DIDComm-kompatibel und werden von DIDComm-Bibliotheken nicht erkannt — sie sind broker-protokoll-intern.

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
