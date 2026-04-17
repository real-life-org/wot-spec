# WoT Sync 007: Transport und Broker

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-13

## Zusammenfassung

Dieses Dokument spezifiziert wie Daten zwischen Peers transportiert werden und wie Broker als immer-online Peers funktionieren. Ein Broker ist kein spezieller Server — er ist ein Peer der zufällig immer online ist und Push-Notifications verschicken kann.

## Referenzierte Standards

- **WebSocket** (RFC 6455) — Primärer Transportkanal
- **Ed25519** (RFC 8032) — Signatur im Message Envelope

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

Im **direkten P2P-Modus** (LAN, Bluetooth) fällt die Broker-Schicht weg. Der Client prüft selbst ob der Gegenüber Member ist (Mitgliederliste liegt lokal vor). Keine Capabilities nötig — das Vertrauen ist direkt.

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

## Autorisierung (Capabilities)

Der Broker ist E2EE — er kann die Mitgliederliste eines Space nicht lesen (verschlüsselt mit dem Space Key). Deshalb braucht er einen externen Beweis, dass ein Client auf ein Dokument zugreifen darf.

### Capability-Format

Eine Capability ist ein JWS, signiert vom Space-Admin:

**JWS-Payload:**

```json
{
  "type": "capability",
  "issuer": "did:key:z6Mk...admin",
  "audience": "did:key:z6Mk...bob",
  "docId": "7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b",
  "permissions": ["read", "write"],
  "generation": 3,
  "createdAt": "2026-04-16T10:00:00Z"
}
```

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `issuer` | DID | Der Admin der die Capability ausgestellt hat |
| `audience` | DID | Für welchen User die Capability gilt |
| `docId` | UUID | Für welches Dokument |
| `permissions` | Array | Erlaubte Operationen (`read`, `write`) |
| `generation` | Integer | Capability-Generation (steigt bei Entfernung) |
| `createdAt` | ISO 8601 | Erstellungszeitpunkt |

### Capability-Verteilung

Capabilities werden zusammen mit dem Space Key verteilt:

- **Bei Einladung:** Die `space-invite` Inbox-Nachricht enthält den Space Key und die Capability ([Sync 009](009-gruppen.md))
- **Bei Key-Rotation (Member-Entfernung):** Der Admin erstellt neue Capabilities mit erhöhter Generation für alle verbleibenden Members. Die `key-rotation` Nachricht enthält den neuen Key und die neue Capability.

### Capability-Prüfung am Broker

Wenn ein Client ein Dokument syncen will:

1. Client sendet seine Capability für dieses Dokument
2. Broker prüft:
   - JWS-Signatur gültig?
   - `audience` = authentifizierte DID?
   - `docId` = angefragtes Dokument?
   - `generation` = aktuelle Generation? (nicht widerrufen)
3. OK → Sync erlaubt

### Capability-Widerruf

Bei Member-Entfernung erhöht der Admin die Capability-Generation. Der Broker akzeptiert nur die neueste Generation. Alte Capabilities (niedrigere Generation) werden automatisch ungültig.

Der Admin teilt dem Broker die neue Generation mit — als signierte Nachricht:

```json
{
  "type": "capability-revocation",
  "docId": "7f3a2b10-...",
  "newGeneration": 4,
  "revokedDid": "did:key:z6Mk...bob"
}
```

Signiert vom Admin, verifizierbar über die DID.

### Persönliche Dokumente

Für das persönliche Dokument (Identität, Keys) stellt der User seine eigene Capability aus — er ist Admin seiner eigenen Daten. Der Broker prüft: `issuer` = `audience` = authentifizierte DID.

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

**Store-and-Forward pro Device:** Der Broker kennt die Device-IDs jedes Users (über die Authentisierung). Inbox-Nachrichten werden für **jedes registrierte Gerät** vorgehalten und erst gelöscht wenn **alle Geräte** ACK gesendet haben. Damit ist garantiert dass kein Gerät eine kritische Nachricht verpasst (Space Key, Capability, Key-Rotation).

## Message Envelope

Alle Nachrichten zwischen Peers (über Broker oder direkt) verwenden ein gemeinsames Envelope-Format. Das Envelope ist ein **JWS Compact Serialization** (RFC 7515) — dasselbe Signaturformat wie für Attestations (siehe [Core 002](../01-wot-core/002-signaturen-und-verifikation.md)).

### Format

```
BASE64URL(header) . BASE64URL(payload) . BASE64URL(signature)
```

**Header:**

```json
{"alg":"EdDSA","typ":"JWT"}
```

**Payload (nach Base64URL-Dekodierung):**

```json
{
  "v": 1,
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "log-entry",
  "fromDid": "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
  "toDid": "did:key:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
  "docId": "7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b",
  "createdAt": "2026-04-16T10:00:00Z",
  "payload": "<Base64URL-kodierter verschlüsselter Inhalt>"
}
```

### Felder (im JWS-Payload)

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `v` | Integer | Ja | Protokoll-Version (aktuell: `1`) |
| `id` | UUID v4 | Ja | Eindeutige Nachrichten-ID |
| `type` | String | Ja | Nachrichtentyp (siehe Tabelle unten) |
| `fromDid` | DID | Ja | Absender-DID |
| `toDid` | DID | Bedingt | Empfänger-DID. Pflicht bei Inbox-Nachrichten. Bei Broadcast (z.B. `log-entry`) kann es die DID des Brokers oder leer sein. |
| `docId` | UUID v4 | Bedingt | Dokument-ID. Pflicht bei `log-entry`, `sync-request`, `sync-response`. |
| `createdAt` | ISO 8601 | Ja | Erstellungszeitpunkt (UTC) |
| `payload` | String | Bedingt | Base64URL-kodierter Inhalt. Verschlüsselt bei Daten, Klartext bei Steuerungsnachrichten (`sync-request`, `ack`). |

### Signatur

Signatur und Verifikation gemäß [Core 002](../01-wot-core/002-signaturen-und-verifikation.md):

1. Payload mit JCS kanonisieren (RFC 8785)
2. JCS-Bytes als Base64URL kodieren
3. Signing Input: `BASE64URL(header) + "." + BASE64URL(jcs_payload)`
4. Ed25519-Signatur über die Signing-Input-Bytes
5. Ergebnis: `header.payload.signature` als JWS Compact String

**Verifikation:**

1. JWS am `.` aufteilen → Header, Payload, Signatur
2. `fromDid` aus dem dekodierten Payload auslesen → Public Key extrahieren
3. Ed25519-Verify(public_key, signing_input_bytes, signature)

Ein Format für alles — Attestations, Envelopes, Log-Einträge. Kompatibel mit SD-JWT als Erweiterung für Trust Lists.

### Nachrichtentypen

#### WoT Sync (dieses Dokument)

| Type | Kanal | Beschreibung |
|------|-------|-------------|
| `log-entry` | Log-Sync | Neuer verschlüsselter Log-Eintrag |
| `sync-request` | Log-Sync | Anfrage: "Was hast du seit seq X für docId Y?" |
| `sync-response` | Log-Sync | Antwort: fehlende Log-Einträge |
| `inbox` | Inbox | Direkte verschlüsselte Nachricht (Attestation, etc.) |
| `ack` | Beide | Empfangsbestätigung (referenziert `id` der Original-Nachricht) |

#### Gruppen ([Sync 009](009-gruppen.md))

| Type | Kanal | Beschreibung |
|------|-------|-------------|
| `space-invite` | Inbox | Einladung in einen Space (Space Key + Broker-URLs) |
| `key-rotation` | Inbox | Neuer Space Key nach Member-Entfernung |
| `member-update` | Inbox | Mitgliedschafts-Änderung (hinzugefügt/entfernt) |

#### HMC Extension ([H03 Gossip](../04-hmc-extensions/H03-gossip.md))

| Type | Kanal | Beschreibung |
|------|-------|-------------|
| `trust-list-delta` | Inbox | Trust-List-Update (SD-JWT, selektiv offengelegt) |

### Erweiterbarkeit

Neue Nachrichtentypen DÜRFEN von Extensions definiert werden. Ein Client der einen unbekannten Typ empfängt MUSS die Nachricht ignorieren (nicht verwerfen — der Broker speichert sie weiterhin für andere Clients die den Typ verstehen).

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

Siehe [Sync-Architektur](../research/sync-architektur.md) und [Forschungsdokument](../research/sync-and-transport.md) für die vollständige Analyse.
