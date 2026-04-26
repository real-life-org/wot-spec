# WoT Sync 007: Transport und Broker

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-13
- **Scope:** Broker, Transport, Capabilities, DIDComm Plaintext Envelopes und P2P-Sync
- **Depends on:** Core 002, Core 004, Core 005, Sync 005, Sync 006, Sync 009, Sync 010
- **Conformance profile:** `wot-sync@0.1`

## Zusammenfassung

Dieses Dokument spezifiziert wie Daten zwischen Peers transportiert werden und wie Broker als immer-online Peers funktionieren. Ein Broker ist kein spezieller Server — er ist ein Peer der zufällig immer online ist und Push-Notifications verschicken kann.

## Referenzierte Standards

- **WebSocket** (RFC 6455) — Primärer Transportkanal
- **DIDComm v2** (DIF) — Plaintext Message Envelope (keine DIDComm-JWE/Authcrypt-Verschluesselung)
- **Ed25519** (RFC 8032) — Signatur im Message Envelope
- **ECIES** (siehe [Sync 005](005-verschluesselung.md)) — 1:1-Verschlüsselung für Inbox-Nachrichten

## Broker

### Was ein Broker ist

Ein Broker ist ein Peer mit Superkräften:

| Eigenschaft | Normaler Peer | Broker |
|-------------|--------------|--------|
| Online | Manchmal | Immer |
| Speichert Daten | Lokal für sich | Für alle berechtigten Peers |
| Push Notifications | Nein | Ja |
| Erreichbar | Nur im LAN / NAT Traversal | Öffentliche IP |
| Autorisierung | Client prüft Membership lokal | Capabilities vom Admin |
| Betrieben von | User | Community oder Anbieter |

### Was ein Broker speichert

- **Log-Einträge** — verschlüsselte Append-only Logs für alle Dokumente seiner User (siehe [Sync 006](006-sync-protokoll.md))
- **Inbox-Nachrichten** — verschlüsselte direkte Nachrichten (Attestations, Einladungen, Key-Rotation). Pro Device vorgehalten, gelöscht nach ACK aller Geräte.
- **Capabilities** — signierte Zugriffsberechtigung pro User pro Dokument (vom Admin ausgestellt)
- **Device-Registrierungen** — welche Device-IDs zu welcher DID gehören
- **Push-Endpoints** — UnifiedPush-Registrierungen für Offline-Notifications

### Was ein Broker NICHT sieht

- Klartext (alles ist E2EE verschlüsselt)
- Welcher CRDT-Typ verwendet wird
- Den Inhalt der Dokumente
- Den Inhalt der Inbox-Nachrichten
- Die Mitgliederliste eines Space (verschlüsselt)

### Broker-Deployment-Klassen — Sicherheitseinordnung

Das Protokoll unterstützt mehrere Broker-Konfigurationen mit unterschiedlichem Sicherheitsniveau:

| Modell | Zensur-Resistenz | Split-Brain-Detection | Typischer Einsatz |
|---|---|---|---|
| **Single Broker** | **Niedrig** | Nicht möglich | Private Gruppen mit vertrauenswürdigem Broker-Betreiber |
| **Multi-Broker (redundant)** | Mittel | Möglich via Head-Vergleich | Community-Spaces |
| **User-gewählter Broker-Mix** | Hoch | Möglich | Hochsensitive Gruppen |

**Single-Broker-Deployments sind eine explizit niedrigere Sicherheitsklasse:**

- Ein bösartiger oder gehackter Broker kann Nachrichten zurückhalten oder unterdrücken, ohne dass Clients das merken
- Es gibt keinen zweiten Sync-Pfad über den Inkonsistenzen erkannt werden könnten
- Der Broker-Betreiber muss als vertrauenswürdiger Akteur angenommen werden

Clients, die in Umgebungen mit hohen Sicherheitsanforderungen arbeiten (kritische Infrastruktur, Aktivismus, Krisenkommunikation), SOLLTEN mehrere Broker parallel nutzen und die Multi-Source-Sync-Logik aus [Sync 006](006-sync-protokoll.md#censorship--und-split-brain-detection) aktivieren.

### Community-betriebene Broker

Ein Broker ist ein einfacher Service:

- Nimmt verschlüsselte Blobs entgegen
- Speichert sie (SQLite, Filesystem, was auch immer)
- Liefert sie auf Anfrage aus
- Sendet Push-Notifications wenn User offline sind

Kein Domain-Name nötig (IP reicht). Kein Verständnis der Daten nötig. Kein CRDT-Code nötig.

## Zwei Schichten

Das Sync-Protokoll ([Sync 006](006-sync-protokoll.md)) ist **peer-agnostisch** — es funktioniert identisch zwischen zwei Handys, zwischen Handy und Broker, oder zwischen zwei Brokern. Jeder Peer spricht dasselbe Protokoll.

Der Broker fügt eine **Schicht darüber** hinzu:

```
┌──────────────────────────────────────────────────┐
│  Broker-Schicht (nur Broker)                     │
│  Authentisierung, Autorisierung (Capabilities),  │
│  Inbox (Store-and-Forward, pro Device), Push     │
├──────────────────────────────────────────────────┤
│  Sync-Protokoll (alle Peers gleich)              │
│  Log-Einträge austauschen, JWS verifizieren      │
└──────────────────────────────────────────────────┘
```

Im **direkten P2P-Modus** (LAN, Bluetooth) fällt die Broker-Schicht weg. Der Client prüft selbst ob der Gegenüber Member ist (Mitgliederliste liegt lokal vor). Keine Capabilities nötig — das Vertrauen ist direkt. Die P2P-Authentisierung ist in [Direkter P2P-Sync](#direkter-p2p-sync) spezifiziert.

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

Die Device-ID (`deviceId`) identifiziert das Gerät stabil — derselbe Wert wie im Sync-Protokoll ([Sync 006](006-sync-protokoll.md#device-identifikation)).

### Nonce-Handling (MUSS)

Die Challenge-Nonce in der Broker-Authentisierung MUSS denselben Replay-Schutz-Regeln folgen wie die Verifikations-Challenge in [Core 004](../01-wot-core/004-verifikation.md#nonce-history-muss):

- Broker MÜSSEN bereits verwendete Nonces für mindestens 24 Stunden speichern
- Eine Nonce DARF nur einmal akzeptiert werden
- Nonces MÜSSEN mindestens 32 Bytes aus einer kryptographisch sicheren Zufallsquelle haben
- Clients MÜSSEN die Nonce direkt nach Empfang signieren (keine späteren Signaturen auf wiederverwendeten Nonces)

## Device-Registrierung

Der Broker MUSS pro DID eine Liste der zugehörigen Device-IDs führen. Das ist notwendig für:

- **Sequenzierte Log-Einträge** — jeder Log-Eintrag ist identifiziert durch `(deviceId, docId, seq)` (siehe [Sync 006](006-sync-protokoll.md))
- **Nonce-Konstruktion** — die deterministische AES-GCM-Nonce basiert auf `(deviceId, seq)` (siehe [Sync 005](005-verschluesselung.md#nonce-konstruktion))
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

**Limitation im Shared-Seed-Modell:** Wer den Seed hat, kann eine neue `deviceId` generieren und sich als "neues Device" registrieren. Device-Deaktivierung schützt nicht gegen Seed-Kompromittierung — siehe [Core 001](../01-wot-core/001-identitaet-und-schluesselableitung.md#multi-device--shared-seed-modell). Für echten Schutz muss die Identität rotiert werden.

### Device-Liste im Broker

Der Broker speichert pro DID:

| Feld | Beschreibung |
|------|-------------|
| `deviceId` | UUID v4 |
| `firstSeenAt` | Zeitstempel der Erstregistrierung |
| `lastSeenAt` | Zeitstempel der letzten Verbindung |
| `status` | `active`, `revoked` |
| `revokedAt` | Zeitstempel der Revocation (falls vorhanden) |

Diese Liste ist nicht Teil des E2EE-Modells — der Broker kennt sie im Klartext. Sie enthält keine sensiblen Inhalte, nur Identifikations-Metadaten.

### Race Conditions

**Gleichzeitige Registrierung zweier Devices mit demselben Seed:** Kein Problem. UUIDs sind per Definition (v4) eindeutig — zwei parallele Registrierungen produzieren unterschiedliche Device-IDs. Beide werden akzeptiert.

**Registrierung eines Devices während eine Revocation verarbeitet wird:** Der Broker MUSS Revocations atomisch anwenden. Falls eine Registrierung in dem Moment ankommt, in dem eine Revocation für dieselbe `deviceId` verarbeitet wird, wird die Revocation zuerst angewendet — die Registrierung schlägt dann mit `DEVICE_REVOKED` fehl.

**Conflict bei UUID-Kollision:** Bei v4-UUIDs ist das astronomisch unwahrscheinlich (~2^122 Zustände). Falls es doch passiert (defekte RNG, Restore aus Backup): Broker lehnt mit `DEVICE_ID_CONFLICT` ab, Client muss eine neue UUID generieren.

## Store-and-Forward pro Device

Inbox-Nachrichten werden **pro Device** zwischengespeichert, nicht pro DID. Das garantiert, dass jedes Device die für es bestimmten Nachrichten erhält, auch wenn es vorübergehend offline ist.

### Zustellungs-Regeln

1. Eine Inbox-Nachricht an DID X wird für **jedes aktive Device** dieser DID in die Inbox gelegt
2. Ein Device acknowledged die Nachricht mit `{ type: "ack", messageId: "..." }`
3. Die Nachricht wird aus der Inbox dieses Devices gelöscht — sie bleibt aber in den Inboxen anderer Devices, die noch nicht ACKt haben
4. Wenn **alle aktiven Devices** ACKt haben, ist die Nachricht vollständig zugestellt
5. Deaktivierte Devices werden bei der Zustellung ignoriert (und ihre Inbox-Einträge gelöscht)

### Retention und Garbage Collection

- Nachrichten, die älter sind als ein definiertes TTL (z.B. 30 Tage) werden auch ohne ACK gelöscht — Implementierer dürfen das konfigurieren
- Wenn ein Device für längere Zeit (z.B. 90 Tage) nicht verbindet, DARF der Broker es als inaktiv behandeln und seine ausstehenden Nachrichten löschen
- Für kritische Nachrichten (Space-Einladungen, Key-Rotationen) SOLLTE der Sender einen Liefernachweis implementieren (z.B. erneutes Senden nach Timeout)

### Warum pro Device und nicht pro DID

Das Protokoll garantiert damit, dass jedes Device alle für es relevanten Nachrichten mindestens einmal sieht — insbesondere Space-Einladungen und Key-Rotationen. Das ist ein Fallback für den Fall, dass Personal-Doc-Sync zwischen den Devices des Users zeitweise nicht funktioniert (Offline, Broker-Ausfall, etc.).

## Autorisierung (Capabilities)

Der Broker ist E2EE — er kann die Mitgliederliste eines Space nicht lesen (verschlüsselt mit dem Space Content Key). Deshalb braucht er einen externen Beweis, dass ein Client auf ein Dokument zugreifen darf.

### Zwei-Schlüssel-Modell für Spaces

Der Broker kennt pro Space zwei Arten von Schlüsseln:

- **Space Capability Verification Key (Ed25519)** — verifiziert **Capabilities** die an einzelne Members ausgestellt werden. Alle Members besitzen den Space Capability Signing Key und können Capabilities signieren. Bei Key-Rotation (Member-Entfernung) wird das Keypair erneuert — alte Capabilities werden damit ungültig.
- **Admin-DID(s)** — abgeleitete, space-spezifische Ed25519-Keys (siehe [Sync 009](009-gruppen.md#admin-key-ableitung)). Nur Admins können **Broker-Management-Nachrichten** signieren (Rotation des Space Capability Key Pairs, Admin hinzufügen/entfernen).

Das löst das Delegations-Problem: jeder Member kann einladen (= Capabilities signieren), weil alle den `spaceCapabilitySigningKey` haben. Nur Admins können rotieren.

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
| `generation` | Integer | Ja | Space-Keypair-Generation zu der die Capability gehört |
| `issuedAt` | ISO 8601 | Ja | Erstellungszeitpunkt |
| `validUntil` | ISO 8601 | Ja | Ablaufzeitpunkt — nach diesem Moment ist die Capability ungültig |

Der JWS wird mit dem Space Capability Signing Key signiert. Der `kid` im JWS-Header MUSS den Space-Kontext und die Capability-Key-Generation referenzieren: `wot:space:<spaceId>#cap-<generation>`. Der Broker verifiziert mit dem aktuellen Space Capability Verification Key fuer genau diesen Space und diese Generation.

**Empfohlene Gültigkeitsdauer:**

- Normale Spaces: 6 Monate
- Hochsensitive Spaces: 1 Monat oder kürzer
- Persönliches Dokument (self-issued): 1 Jahr

### Capability-Verteilung

Capabilities werden zusammen mit dem Space Key verteilt:

- **Bei Einladung:** Der Einladende signiert eine Capability mit dem `spaceCapabilitySigningKey` für den Eingeladenen. Die `space-invite` Inbox-Nachricht enthält Space Content Key, Capability Signing Key und Capability ([Sync 009](009-gruppen.md)).
- **Bei Key-Rotation (Member-Entfernung):** Der Admin generiert einen neuen Space Content Key und ein neues Capability Key Pair. Alle verbleibenden Members bekommen neuen Content Key + neuen Capability Signing Key + neue Capability.
- **Vor Ablauf:** Jedes Mitglied kann sich selbst (oder Peers) eine erneuerte Capability ausstellen, solange der aktuelle `spaceCapabilitySigningKey` gültig ist.

### Capability-Prüfung am Broker

Wenn ein Client ein Dokument syncen will:

1. Client sendet seine Capability
2. Broker prüft:
   - JWS-Signatur gültig gegen den aktuellen `spaceCapabilityVerificationKey`? (inklusive `alg=EdDSA`, siehe [Core 002](../01-wot-core/002-signaturen-und-verifikation.md#algorithmus-validierung-muss))
   - `audience` = authentifizierte DID?
   - `spaceId` = angefragter Space?
   - `generation` = aktuelle Capability-Key-Generation? (alte Capabilities werden damit implizit widerrufen)
   - `now < validUntil`? (nicht abgelaufen)
3. OK → Sync erlaubt

### Warum Capability-Ablauf nötig ist

Ohne `validUntil` sind Capabilities unbegrenzt gültig — bis zur nächsten Key-Rotation. Das erzeugt das "Left but never removed"-Problem: ein Member der den Space freiwillig verlässt behält theoretisch Zugriff bis ein Admin eine Rotation auslöst (was vielleicht nie passiert, weil kein offensichtlicher Anlass besteht).

Mit `validUntil` läuft die Berechtigung automatisch ab. Aktive Members bekommen rechtzeitig eine erneuerte Capability. Inaktive Members verlieren den Zugriff ohne dass jemand aktiv handeln muss.

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

**Unterschied zum Space-Capability-Modell:** Bei Spaces signiert der geteilte `spaceCapabilitySigningKey`, bei Personal Docs signiert der persönliche Identity Key (DID). Das ist eine bewusste Vereinfachung — ein Personal Doc hat genau einen Eigentümer, kein Gruppen-Key-Management nötig. Die Capability-Felder (`spaceId`, `generation`, `validUntil`) werden analog verwendet, aber `spaceId` wird durch die deterministische Personal-Doc-ID ersetzt (siehe [Sync 010](010-personal-doc.md)).

## Zwei Kanäle

Der Broker bietet zwei Kommunikationskanäle:

### Kanal 1: Log-Sync

Für die Synchronisation von Dokumenten (Spaces, Identity, Keys):

```
Client → Broker: "Hier ist ein neuer Log-Eintrag für Dokument X"
Broker → Client: "Dokument X hat neue Einträge seit deinem letzten Stand"
```

Pull-basiert: der Client fragt aktiv nach fehlenden Einträgen. Der Broker notifiziert verbundene Clients wenn neue Einträge eingehen.

### Kanal 2: Inbox

Für direkte Nachrichten die nicht über den Log laufen:

```
Alice → Broker: "Speichere diese verschlüsselte Nachricht für Bob"
Bob (Handy)  → Broker: "Habe ich neue Nachrichten?"
Broker → Bob (Handy):  "Ja, hier ist eine von Alice"
Bob (Handy)  → Broker: "Empfangen" (ACK)
Bob (Laptop) → Broker: "Habe ich neue Nachrichten?"
Broker → Bob (Laptop): "Ja, hier ist eine von Alice"
Bob (Laptop) → Broker: "Empfangen" (ACK)
Broker: Alle Geräte haben bestätigt → Nachricht löschen
```

**Store-and-Forward pro Device:** Der Broker kennt die Device-IDs jedes Users (über die Authentisierung). Inbox-Nachrichten werden für **jedes registrierte Gerät** vorgehalten und erst gelöscht wenn **alle Geräte** ACK gesendet haben. Damit ist garantiert dass kein Gerät eine kritische Nachricht verpasst (Space Content Key, Capability, Key-Rotation).

## Message Envelope (DIDComm-kompatibel)

Alle Nachrichten zwischen Peers (über Broker oder direkt) verwenden das **DIDComm v2 Plaintext Message Format** ([DIF DIDComm Messaging v2](https://identity.foundation/didcomm-messaging/spec/v2.0/)). Das stellt Interoperabilität auf der Envelope-Ebene sicher: etablierte DIDComm-v2-Libraries können WoT-Plaintext-Messages parsen und routen. Die Verschlüsselung bleibt WoT-spezifisch (ECIES statt DIDComm-JWE/Authcrypt).

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
| `created_time` | Integer (Unix-Seconds) | Ja | Erstellungszeitpunkt (UTC Epoch Seconds). DIDComm v2.1 konform. |
| `thid` | UUID v4 | Optional | Thread-ID. Verknüpft Nachrichten die zu einer Konversation gehören (z.B. Request + Response). Die erste Nachricht eines Threads setzt `thid = id`; Folgenachrichten tragen denselben `thid`. |
| `pthid` | UUID v4 | Optional | Parent-Thread-ID. Verweist auf einen übergeordneten Thread — für verschachtelte Konversationen (z.B. ein Sub-Protokoll das innerhalb eines größeren Flows läuft). |
| `body` | Object | Ja | Nachrichteninhalt. Struktur abhängig vom `type`. |

### Threading

`thid` und `pthid` sind identisch zu den gleichnamigen DIDComm v2 Feldern. Sie erlauben:

- **Request/Response-Korrelation** — Eine Antwort trägt denselben `thid` wie die Anfrage.
- **Langlaufende Protokolle** — Mehrstufige Flows (z.B. Gruppen-Einladung mit Annahme/Ablehnung) werden durch einen stabilen `thid` zusammengehalten.
- **Verschachtelte Protokolle** — Ein Sub-Protokoll referenziert den Eltern-Flow über `pthid`.

Nachrichten ohne `thid` sind Einzelnachrichten ohne Konversationskontext. Nachrichten die eine andere Nachricht direkt beantworten (z.B. `ack`, `sync-response`) MÜSSEN den `thid` der Original-Nachricht tragen.

### Authentifizierung: drei Envelope-Varianten

Unser Message-Envelope kann in drei Formen vorliegen (analog zu DIDComm v2, aber mit unserer eigenen Verschlüsselung):

1. **Plaintext Message** — nackte JSON, keine Envelope-Signatur, keine Envelope-Verschlüsselung
2. **Signed Message** — Plaintext in JWS verpackt (Envelope-Signatur)
3. **Encrypted Message** — Body mit **ECIES** verschlüsselt (siehe [Sync 005](005-verschluesselung.md#peer-to-peer-verschlüsselung-ecies)). Der Sender wird nicht durch die Verschlüsselung selbst gebunden, sondern durch eine separate JWS-Signatur im Body oder im Envelope

### Wann wird welche Form verwendet (NORMATIV)

Der Envelope wird NUR dann als **Signed Message** verpackt, wenn der Body nicht bereits kryptographisch authentifiziert ist. Doppelte Authentifizierung (Envelope-JWS über Body mit innerer JWS) ist zu vermeiden — sie erhöht nur Größe und Verarbeitungsaufwand, bringt keinen Sicherheitsgewinn.

| Nachrichtentyp | Authentifizierung durch | Envelope |
|---|---|---|
| `log-entry` | Innerer JWS im Body (persistent, dauerhaft verifizierbar) | Plaintext |
| `sync-request`, `sync-response` | Kontext der authentifizierten WebSocket-Verbindung | Plaintext |
| `inbox` (Attestation, etc.) | Innerer JWS im Klartext-Body (bindet Sender) + ECIES-Wrap | Encrypted (ECIES) |
| `space-invite`, `key-rotation`, `member-update` | Innerer JWS im Klartext-Body + ECIES-Wrap | Encrypted (ECIES) |
| `state-digest`, `state-digest-request` | Envelope-JWS (ephemer) | Signed |

### Signatur (WoT Envelope-JWS)

Wenn ein Envelope signiert wird, geschieht das als **JWS Compact Serialization** — identisch mit unseren Attestations ([Core 002](../01-wot-core/002-signaturen-und-verifikation.md)) und strukturell an DIDComm Signed Messages angelehnt. Anders als beim Plaintext Envelope beanspruchen WoT Envelope-JWS derzeit keine Library-validierte DIDComm-Signed-Message-Kompatibilitaet; dieser Anspruch wird erst mit eigenen Signed-Envelope-Testvektoren erhoben.

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
4. Ausgabe: `{ epk, nonce, ciphertext }` (siehe [Sync 005](005-verschluesselung.md#verschlüsseltes-nachrichtenformat))
5. Transport als Body der DIDComm-Envelope-Nachricht (type = `inbox/1.0`, `space-invite/1.0`, etc.)

**Pflichtfelder im inneren JWS-Payload (MUSS):**

Der innere JWS MUSS mindestens enthalten: `from` (Sender-DID), `to` (Empfänger-DID), `type` (Nachrichtentyp), `id` (Message-ID), `created_time` (Unix-Seconds). Der Empfänger MUSS nach dem Entschlüsseln prüfen:

1. JWS-Signatur verifizieren (Sender's Key via resolve())
2. `to` MUSS die eigene DID sein — verhindert Misdirection (Nachricht an falschen Empfänger umgeleitet)
3. `from` MUSS mit dem JWS-Signierer übereinstimmen — verhindert Sender-Spoofing
4. `created_time` MUSS aktuell sein (nicht älter als konfigurierbar, z.B. 24h) — verhindert Replay
5. `id` DARF nicht bereits verarbeitet worden sein (Message-ID-History) — zweite Replay-Verteidigung

Siehe [Sync 005](005-verschluesselung.md#peer-to-peer-verschlüsselung-ecies) für Details.

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

#### Gruppen ([Sync 009](009-gruppen.md))

| Type-URI | Kanal | Beschreibung |
|----------|-------|-------------|
| `.../space-invite/1.0` | Inbox | Einladung in einen Space (Content Key + Capability Signing Key + Capability) |
| `.../key-rotation/1.0` | Inbox | Neuer Content Key + Capability Signing Key nach Member-Entfernung |
| `.../member-update/1.0` | Inbox | Mitgliedschafts-Änderung (hinzugefügt/entfernt) |

#### HMC Extension ([H03 Gossip](../04-hmc-extensions/H03-gossip.md))

| Type-URI | Kanal | Beschreibung |
|----------|-------|-------------|
| `.../trust-list-delta/1.0` | Inbox | Trust-List-Update (SD-JWT, selektiv offengelegt) |

Alle Type-URIs verwenden den Präfix `https://web-of-trust.de/protocols/`.

### Wire-Formate der Sync-Nachrichten

#### `log-entry/1.0` — Neuer verschlüsselter Log-Eintrag

Ein Peer publiziert einen neuen Log-Eintrag an andere Peers. Der Log-Eintrag selbst ist ein **JWS Compact String** (siehe [Sync 006](006-sync-protokoll.md#signatur-des-log-eintrags)). Er wird als opaker String im Body transportiert:

```json
{
  "entry": "<JWS Compact String des Log-Eintrags>"
}
```

Der JWS-Payload des Eintrags enthält die Felder `seq`, `deviceId`, `docId`, `authorKid`, `keyGeneration`, `data`, `timestamp` — JCS-kanonisiert, Ed25519-signiert. Vollständiges Schema in [Sync 006 Log-Eintrag](006-sync-protokoll.md#log-eintrag).

**Broker-Indexing:** Der Broker extrahiert `docId`, `deviceId`, `seq` aus dem JWS-Payload (Base64URL-dekodieren des mittleren Segments, JCS-kanonisiertes JSON parsen). Diese drei Felder braucht er für Indexing, Sync-Anfragen und Kollisionserkennung. Der Broker MUSS die JWS-Signatur NICHT verifizieren — Signatur-Verifikation ist Aufgabe der Peers, die die Einträge letztendlich konsumieren. Der Broker darf sie aber als zusätzliche Integritätsprüfung durchführen.

Kein ACK nötig — der Empfang wird implizit durch den nächsten `sync-request` bestätigt (fehlende seq-Werte werden nachgefordert).

**Broker-seitige Kollisionsabwehr (MUSS):**

Der Broker MUSS für jeden akzeptierten Log-Eintrag den **Content-Hash** (SHA-256 über den kanonisierten Payload) speichern, indiziert nach `(docId, deviceId, seq)`. Beim Empfang eines neuen Eintrags prüft der Broker:

1. Existiert bereits ein Eintrag mit derselben `(docId, deviceId, seq)`?
2. Falls ja: Stimmt der Content-Hash überein?
   - **Hash gleich:** Idempotente Retransmission — OK, der Broker ignoriert die Duplizierung still
   - **Hash unterschiedlich:** **Kollision** — der Broker MUSS den neuen Eintrag ablehnen und mit `SEQ_COLLISION_DETECTED` antworten
3. Falls nicht: Eintrag akzeptieren, Hash speichern

Diese Prüfung ist die letzte Verteidigungslinie gegen AES-GCM-Nonce-Reuse und MUSS auch dann erzwungen werden, wenn der Client seq-Konsistenz-Regeln aus [Sync 006](006-sync-protokoll.md#seq-konsistenz-muss) einhält (Defense in Depth).

**Reaktion des Clients bei `SEQ_COLLISION_DETECTED`:**

Der Client MUSS diese Response als Indikator für ein Restore/Clone-Szenario behandeln und die Restore-Detection-Regel aus [Sync 006](006-sync-protokoll.md#seq-konsistenz-muss) anwenden: neue `deviceId` generieren, alte deaktivieren, neu beginnen.

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
| `entries` | Array of JWS-Strings | Ja | Die fehlenden Log-Einträge als JWS Compact Strings, sortiert nach `(deviceId, seq)`. Format gemäß [Sync 006 Log-Eintrag](006-sync-protokoll.md#log-eintrag). |
| `heads` | Object | Ja | Die aktuell höchsten bekannten seq pro deviceId beim Antwortenden |
| `truncated` | Boolean | Ja | `true` wenn durch `limit` abgeschnitten — der Fragende MUSS einen weiteren `sync-request` mit aktualisierten Heads senden |

**Threading:** Der `sync-response` MUSS denselben `thid` wie der zugehörige `sync-request` tragen.

**Heads-Diskrepanz-Detection:** Der Fragende kann die erhaltenen `heads` mit denen anderer Broker/Peers vergleichen, um Censorship oder Split-Brain zu erkennen (siehe [Sync 006](006-sync-protokoll.md#censorship--und-split-brain-detection)).

#### `ack/1.0` — Empfangsbestätigung

Wird nur für **Inbox-Nachrichten** verwendet (nicht für sync-request/response — dort ist die Bestätigung implizit). Body:

```json
{
  "messageId": "uuid-der-empfangenen-nachricht"
}
```

Der Empfänger schickt `ack` nach erfolgreichem Verarbeiten (Entschlüsseln, Signatur-Verifizieren) einer Inbox-Nachricht. Der Broker kann die Nachricht dann aus der Device-Inbox entfernen.

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

### DIDComm-Kompatibilität

Das Nachrichtenformat ist **DIDComm v2.1 konform** auf Envelope-Ebene: `id`, `typ`, `type`, `from`, `to`, `created_time` (Unix-Seconds), `body`, `thid`/`pthid`. DIDComm-Bibliotheken können unsere Plaintext-Messages lesen und routen. Die Verschlüsselung (ECIES statt DIDComm Authcrypt) ist eine bewusste Abweichung auf Crypto-Ebene — sie betrifft nicht die Envelope-Struktur.

Für die Hintergründe dieser Entscheidung siehe [Research: Interop und Zielgruppe](../research/interop-und-zielgruppe.md).

## Broker-Zuordnung

### Persönlicher Broker

Jeder User hat einen persönlichen Broker für seine privaten Dokumente (Identität, Keys, Kontakte). Das ist typischerweise der Broker der Community über die er eingeladen wurde.

Das persönliche Dokument wird automatisch auf **allen Brokern** repliziert bei denen der User registriert ist — für Redundanz. Wenn ein Broker ausfällt, haben die anderen noch alles.

### Space-Broker (Heim-Broker)

Jeder Space hat einen oder mehrere **Heim-Broker**. Beim Erstellen eines Space wird der Broker des Erstellers zum Heim-Broker. Die Broker-URL ist Teil der Space-Metadata.

Beim Einladen in einen Space wird die Broker-URL mitgeschickt. Der eingeladene User verbindet sich automatisch mit diesem Broker für diesen Space.

Ein Space DARF mehrere Heim-Broker haben — für Redundanz. Clients syncen mit allen verfügbaren Brokern. Log-Einträge konvergieren automatisch (selbes Sync-Protokoll, CRDT-Merge).

### Community-Einladung

Wenn ein User über eine Community eingeladen wird, enthält die Einladung:

```
Community-Einladung:
  Space-ID + Group Key (verschlüsselt)
  Broker-URL der Community
  Profil des Einladenden
```

Der Community-Broker wird automatisch zum persönlichen Broker und zum Space-Broker. Der neue User ist sofort vernetzt — ein Schritt.

### Standard-Broker

Die App wird mit einem Standard-Broker ausgeliefert als Fallback für User die ohne Einladung starten. Sobald der User einer Community beitritt, kann er zu deren Broker wechseln.

### Broker-Verbindungen eines Users

```
Alice's App verbindet sich mit:
  → Broker A (persönlicher Broker + Space 1 + Space 2)
  → Broker B (Space 3 Heim-Broker)
  
Persönliches Dokument: repliziert auf BEIDEN Brokern
Space 1 + 2: nur auf Broker A
Space 3: nur auf Broker B
```

## Multi-Broker

Broker kommunizieren NICHT untereinander. Es gibt kein Federation-Protokoll. Stattdessen:

- **Persönliche Dokumente** werden auf alle Broker repliziert (automatisch, für Redundanz)
- **Space-Dokumente** werden auf die Heim-Broker des Space repliziert
- Alle Members eines Space müssen bei mindestens einem gemeinsamen Heim-Broker registriert sein
- Der Client löst alles — die Broker sind nur Speicher

### Broker-Wechsel

Ein Space-Admin kann den Heim-Broker ändern (z.B. wenn der alte Broker eingestellt wird). Die neue Broker-URL wird in der Space-Metadata aktualisiert. Members migrieren automatisch beim nächsten Sync.

### Broker-Ausfall

Wenn ein Broker offline geht:
- Lokale Daten bleiben verfügbar (CompactStore)
- Persönliche Dokumente sind auf anderen Brokern repliziert
- Spaces die nur diesen Broker haben können nicht syncen bis er wieder da ist oder ein neuer Heim-Broker gesetzt wird

## Push-Notifications

Wenn ein Peer offline ist und eine neue Nachricht oder ein neuer Log-Eintrag für ihn eingeht:

```
Broker prüft: ist der Empfänger online?
  → Ja: direkt zustellen via WebSocket
  → Nein: Push-Notification senden (UnifiedPush/ntfy)
    → Peer wacht auf
    → Peer verbindet sich mit Broker
    → Peer holt fehlende Daten
```

Push enthält keinen Inhalt — nur ein Signal: "Es gibt was Neues." Der Peer holt die Daten selbst.

Siehe auch RFC-0004 (Push Notifications mit UnifiedPush) für Implementierungsdetails.

## Transport-Agnostik

Das Sync-Protokoll funktioniert über verschiedene Transportwege:

| Transport | Wann | Status |
|-----------|------|--------|
| **WebSocket** | Primär, Browser-kompatibel | Implementiert |
| **QUIC** (via Iroh) | Effizienter, NAT Traversal | Zukunft |
| **Bluetooth / WiFi Direct** | Lokales Mesh ohne Internet | Zukunft |
| **Sneakernet** | USB-Stick, QR-Code, E-Mail | Zukunft |

Das Envelope-Format und das Sync-Protokoll (007) sind transportunabhängig. Nur der Verbindungsaufbau unterscheidet sich.

## Direkter P2P-Sync

Wenn zwei Peers direkt kommunizieren (Bluetooth, WiFi Direct, LAN ohne Broker), fällt die Broker-Schicht weg. Authentisierung, Autorisierung und Message-Routing laufen direkt zwischen den Peers.

### Anwendungsszenarien

- Zwei Smartphones auf einem Festival ohne Internet
- Zwei Devices desselben Users im lokalen WLAN (schneller als via Broker)
- Cross-Device-Sync ohne Broker-Abhängigkeit

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

**Wichtige Eigenschaften:**

- **Initiator/Responder-Rolle** wird am Anfang der Verbindung eindeutig festgelegt (z.B. wer zuerst `p2p-hello` sendet ist Initiator). Die Rolle wird in die Signatur mit einbezogen, damit ein Angreifer die Signatur des einen nicht als die des anderen ausgeben kann.
- **Alle Handshake-Parameter** (DIDs, Device-IDs, beide Nonces) sind Teil des signierten Transcripts. Ein Angreifer, der nur Nonces spiegelt oder DIDs manipuliert, kann keine gültige Signatur produzieren, ohne den tatsächlichen Identity Key zu besitzen.
- **Reflection-Schutz:** Weil die Signatur rollen-spezifisch ist (`"role:initiator"` vs `"role:responder"`) und die DIDs explizit im Transcript stehen, kann ein Angreifer nicht seine eigene Signatur aus einer anderen Session als die einer anderen Partei ausgeben.

Nach dem Handshake kennt jeder Peer die **DID + deviceId** des anderen (authentisch verifiziert) und kann damit den normalen Sync-Protokoll-Flow (`sync-request`, `sync-response`) anstoßen.

### Nonce-Anforderungen

- Nonces MÜSSEN mindestens 32 Bytes aus einer kryptographisch sicheren Zufallsquelle sein
- Jede Seite MUSS eine Nonce-History (wie [Core 004](../01-wot-core/004-verifikation.md#nonce-history-muss)) führen um Replay-Angriffe zu verhindern
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

### Bewusste Limitation: Entfernte Members im P2P-Modus

Nach einer Space-Key-Rotation haben entfernte Members den alten Space Content Key und den alten Space Capability Signing Key noch. Am **Broker** scheitern sie sofort — der alte Capability Verification Key ist ungültig. Im **P2P-Modus** (offline, ohne Broker) gibt es keinen autoritativen Membership-Check. Das ist eine **inhärente Limitation des Offline-Betriebs**, nicht ein Protokoll-Fehler.

**Bestmögliche Heuristik:** Verbleibende Members schreiben Einträge mit der aktuellen (höchsten) `keyGeneration`. Ein Peer der nur Einträge mit einer älteren `keyGeneration` produzieren kann, ist wahrscheinlich entfernt worden. Clients SOLLEN solche Peers als **verdächtig** markieren und empfangene Daten nicht in den lokalen CRDT-State mergen, bis der Membership-Status über eine vertrauenswürdige Quelle (Broker, anderer Member) bestätigt wurde.

**Was das bedeutet:** Im reinen Offline-P2P-Modus kann ein entfernter Member kurzfristig Daten empfangen die er nicht mehr sehen sollte (mit dem alten Key verschlüsselt). Er kann keine neuen Daten produzieren die von aktiven Members als aktuell akzeptiert werden (falsche keyGeneration). Sobald ein Broker erreichbar ist, wird der Zustand korrigiert.

### Sync-Ablauf nach Handshake

Nach erfolgreicher gegenseitiger Authentisierung läuft das normale Sync-Protokoll:

```
1. Alice: { type: "sync-request", docId, heads }
2. Bob:   { type: "sync-response", docId, entries, heads }
3. Alice verifiziert jeden empfangenen Log-Eintrag (JWS-Signatur, Space-Key-Entschlüsselung)
4. Alice: weitere sync-requests für andere gemeinsame Dokumente
```

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

## App-Start-Reihenfolge

Beim Starten der App:

```
Phase 1: Lokal (offline-fähig)
  1. Lokalen Speicher öffnen (CompactStore / IndexedDB)
  2. Dokumente aus lokalem Speicher laden
  3. App ist offline benutzbar

Phase 2: Netzwerk
  4. Mit Broker verbinden (WebSocket + Challenge-Response)
  5. Capabilities für eigene Dokumente vorlegen
  6. Falls lokaler Speicher leer: Daten vom Broker holen

Phase 3: Sync
  7. Fehlende Log-Einträge austauschen (Catch-Up)
  8. Live-Sync aktivieren (neue Einträge sofort senden/empfangen)
  9. Inbox-Nachrichten abholen (pro Device)
```

Die App ist nach Phase 1 benutzbar. Phase 2 und 3 laufen im Hintergrund.

## Architektur-Grundlage

Siehe [Sync-Architektur](../research/sync-architektur.md) und [Sync-Alternativen](../research/sync-alternativen.md) für die vollständige Analyse.
