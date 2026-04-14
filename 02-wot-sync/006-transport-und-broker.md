# WoT Sync 006: Transport und Broker

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
| Betrieben von | User | Community oder Anbieter |

### Was ein Broker speichert

- **Log-Einträge** — verschlüsselte Append-only Logs für alle Dokumente seiner User (siehe [Sync 005](005-sync-protokoll.md))
- **Inbox-Nachrichten** — verschlüsselte direkte Nachrichten (Attestations, Einladungen, Key-Rotation). Werden nach Zustellung gelöscht.
- **Push-Endpoints** — UnifiedPush-Registrierungen für Offline-Notifications

### Was ein Broker NICHT sieht

- Klartext (alles ist E2EE verschlüsselt)
- Welcher CRDT-Typ verwendet wird
- Den Inhalt der Dokumente
- Den Inhalt der Inbox-Nachrichten

### Community-betriebene Broker

Ein Broker ist ein einfacher Service:

- Nimmt verschlüsselte Blobs entgegen
- Speichert sie (SQLite, Filesystem, was auch immer)
- Liefert sie auf Anfrage aus
- Sendet Push-Notifications wenn User offline sind

Kein Domain-Name nötig (IP reicht). Kein Verständnis der Daten nötig. Kein CRDT-Code nötig.

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
Bob   → Broker: "Habe ich neue Nachrichten?"
Broker → Bob:   "Ja, hier ist eine von Alice"
Bob   → Broker: "Empfangen, kannst du löschen"
```

Store-and-Forward: der Broker speichert bis der Empfänger abholt und bestätigt.

## Message Envelope

Alle Nachrichten zwischen Peers (über Broker oder direkt) verwenden ein gemeinsames Envelope-Format:

```json
{
  "v": 1,
  "id": "uuid",
  "type": "log-entry | inbox | sync-request | ack",
  "fromDid": "did:key:z6Mk...",
  "toDid": "did:key:z6Mk...",
  "createdAt": "2026-04-13T10:00:00Z",
  "payload": "...",
  "sig": "Ed25519-Signatur"
}
```

Die Signatur wird gemäß [Core 002](../01-wot-core/002-signaturen-und-verifikation.md) erstellt — JCS-kanonisiert, SHA-256 gehasht, Ed25519 signiert. Sie deckt alle Felder außer `sig` selbst ab.

### Nachrichtentypen

| Type | Kanal | Beschreibung |
|------|-------|-------------|
| `log-entry` | Log-Sync | Neuer verschlüsselter Log-Eintrag |
| `sync-request` | Log-Sync | "Was hast du, was ich nicht habe?" |
| `sync-response` | Log-Sync | Fehlende Log-Einträge |
| `inbox` | Inbox | Direkte Nachricht (Attestation, Invite, etc.) |
| `ack` | Beide | Empfangsbestätigung |

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
  4. Mit Broker verbinden (WebSocket)
  5. Falls lokaler Speicher leer: Daten vom Broker holen

Phase 3: Sync
  6. Fehlende Log-Einträge austauschen (Catch-Up)
  7. Live-Sync aktivieren (neue Einträge sofort senden/empfangen)
  8. Inbox-Nachrichten abholen
```

Die App ist nach Phase 1 benutzbar. Phase 2 und 3 laufen im Hintergrund.

## Architektur-Grundlage

Siehe [Sync-Architektur](../research/sync-architektur.md) und [Forschungsdokument](../research/sync-and-transport.md) für die vollständige Analyse.
