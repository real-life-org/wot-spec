# WoT Sync 006: Sync-Protokoll

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-13

## Zusammenfassung

Dieses Dokument spezifiziert wie Daten zwischen Peers synchronisiert werden — verschlüsselt, CRDT-agnostisch, und über beliebige Transportwege. Das Protokoll ist für alle Peers identisch — ob Handy, Laptop oder Broker.

## Referenzierte Standards

- **Ed25519** (RFC 8032) — Signatur der Log-Einträge
- **AES-256-GCM** (NIST SP 800-38D) — Verschlüsselung der Payloads (siehe [Sync 005](005-verschluesselung.md))

## Grundprinzip

**Ein Peer ist ein Peer ist ein Peer.** Das Sync-Protokoll ist immer dasselbe — egal ob zwei Handys direkt syncen, ein Handy mit einem Broker synced, oder zwei Broker untereinander. Ein Broker ist ein Peer der zufällig immer online ist.

## Drei Schichten

```
┌─────────────────────────────────────────────────┐
│  Schicht 3: Reconciliation                      │
│  Effiziente Differenz-Berechnung (RIBLT)        │
│  Für: Reconnect nach langer Offline-Zeit        │
├─────────────────────────────────────────────────┤
│  Schicht 2: Kompression                         │
│  Deterministische Chunk-Bildung (Sedimentree)   │
│  Für: Alte History komprimieren                  │
├─────────────────────────────────────────────────┤
│  Schicht 1: Log                                 │
│  Append-only Einträge pro Device pro Dokument   │
│  Für: Echtzeit-Sync, normale Nutzung            │
└─────────────────────────────────────────────────┘
```

Schicht 1 wird zuerst implementiert. Schichten 2 und 3 werden schrittweise hinzugefügt.

## Device-Identifikation

Jedes Gerät generiert beim ersten Start eine zufällige **Device-UUID** und speichert sie lokal:

```
deviceId = crypto.randomUUID()
```

Log-Einträge werden pro `deviceId` pro `docId` sequenziert. Die UUID hat keine kryptografische Bedeutung — sie ist nur ein Bezeichner um Einträge verschiedener Geräte desselben Users auseinanderzuhalten.

## Schicht 1: Log

Jeder Peer führt einen Append-only Log pro Dokument. Jeder Eintrag ist ein verschlüsselter Blob — das Protokoll weiß nicht was drin ist.

### Log-Eintrag

Ein Log-Eintrag ist ein **JWS Compact Serialization** (wie alle signierten Daten im Protokoll).

**JWS-Payload (nach Base64URL-Dekodierung):**

```json
{
  "seq": 42,
  "deviceId": "550e8400-e29b-41d4-a716-446655440000",
  "docId": "7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b",
  "authorDid": "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
  "keyGeneration": 3,
  "data": "<Base64URL-kodierter verschlüsselter Blob>",
  "timestamp": "2026-04-16T10:00:00Z"
}
```

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `seq` | Integer | Ja | Aufsteigend, pro deviceId pro docId. Beginnt bei 0. |
| `deviceId` | UUID v4 | Ja | Welches Gerät hat den Eintrag erzeugt |
| `docId` | UUID v4 | Ja | Zu welchem Dokument gehört der Eintrag |
| `authorDid` | DID | Ja | DID des Autors (für Signatur-Verifikation) |
| `keyGeneration` | Integer | Ja | Generation des Space Keys der zur Verschlüsselung verwendet wurde (siehe [Sync 005](005-verschluesselung.md)) |
| `data` | String | Ja | Base64URL-kodierter AES-256-GCM Ciphertext (Nonce + Ciphertext + Auth Tag, siehe [Sync 005](005-verschluesselung.md)) |
| `timestamp` | ISO 8601 | Ja | Erstellungszeitpunkt (UTC) |

### Signatur des Log-Eintrags

Signatur und Verifikation gemäß [Core 002](../01-wot-core/002-signaturen-und-verifikation.md) — identisch mit dem Message Envelope (siehe [Sync 007](007-transport-und-broker.md#signatur)):

1. Payload mit JCS kanonisieren (RFC 8785)
2. JCS-Bytes als Base64URL kodieren
3. Signing Input: `BASE64URL(header) + "." + BASE64URL(jcs_payload)`
4. Ed25519-Signatur über die Signing-Input-Bytes
5. Ergebnis: JWS Compact String (`header.payload.signature`)

Ein Empfänger verifiziert die Signatur indem er `authorDid` aus dem Payload auflöst und den Public Key extrahiert.

### Verschlüsselter Payload (`data`)

Der `data`-Blob enthält ein mit AES-256-GCM verschlüsseltes CRDT-Update:

```
Klartext (CRDT-Update, z.B. Yjs-Binary)
  → AES-256-GCM verschlüsseln mit Space Key (Generation = keyGeneration)
  → Nonce (12 Bytes) + Ciphertext + Auth Tag (16 Bytes)
  → Base64URL kodieren
  → in `data`-Feld schreiben
```

### CRDT-Agnostik

Der entschlüsselte Payload ist opak. Das Sync-Protokoll weiß nicht ob da ein Yjs-Update, ein Automerge-Change oder etwas anderes drin steckt. Der CRDT-Adapter auf dem Client entschlüsselt den Blob und wendet ihn an.

Welcher CRDT-Typ verwendet wird, ist im Space-Metadata festgelegt (nicht im Log-Eintrag). Alle Members eines Space verwenden denselben CRDT-Typ.

### Warum das den Loop löst

Jeder Peer schreibt nur in seinen eigenen Log (seine eigene deviceId). Empfangene Einträge werden unter der deviceId des Absenders gespeichert. Es gibt physisch keine Möglichkeit empfangene Daten als eigene weiterzusenden.

### Sync zwischen zwei Peers

```
Alice: "Für Dokument X habe ich von deinem Device 'abc' Einträge bis seq 47.
        Und von deinem Device 'def' bis seq 12. Was kommt danach?"

Bob:   "Hier sind abc:48, abc:49, abc:50 und def:13."

Alice: "Und hier sind meine neuen Einträge die du noch nicht hast."
```

Kein Full State Exchange. Kein Broadcast an N Members. Nur: was hast du, was ich nicht habe?

## Schicht 2: Kompression (Zukunft)

Log-Einträge akkumulieren über Zeit. Ein Dokument mit tausenden Änderungen über Monate erzeugt einen großen Log. Ein neuer Peer müsste alle einzelnen Einträge herunterladen — langsam.

### Sedimentree-Prinzip

Alte Log-Einträge werden zu größeren Chunks zusammengefasst. Alle Peers berechnen unabhängig dieselben Chunks — kein Koordinator nötig, kein byzantinisches Problem.

- Chunk-Grenzen werden durch Hash-Eigenschaften bestimmt (z.B. führende Null-Bytes im Hash eines Eintrags)
- Ältere History → größere Chunks → weniger Metadaten
- Jeder Peer komprimiert lokal und unabhängig

Details werden spezifiziert wenn Schicht 2 implementiert wird.

## Schicht 3: Reconciliation (Zukunft)

Wenn zwei Peers stark divergiert sind (z.B. nach Wochen offline), wäre es ineffizient alle fehlenden Einträge einzeln aufzuzählen.

### RIBLT

Rateless Invertible Bloom Lookup Tables ermöglichen effiziente Set-Reconciliation:

- Datenmenge proportional zur tatsächlichen Differenz (1,35x Overhead)
- Parameterlos — kein Tuning nötig
- 1 Milliarde Items, 5 Unterschiede → ca. 240 Bytes

Details werden spezifiziert wenn Schicht 3 implementiert wird.

## Sync-Modi

### Live-Sync (beide Peers online)

```
Peer A erzeugt neuen Log-Eintrag
  → signiert + verschlüsselt
  → sendet an verbundene Peers
  → Peers speichern den Eintrag und wenden ihn an
```

### Catch-Up (nach Offline-Phase)

```
Peer A verbindet sich mit Peer B
  → tauschen Sequenznummern pro deviceId pro docId aus
  → senden fehlende Einträge
```

### Push-Notification (Peer ist offline)

```
Broker empfängt neuen Eintrag
  → Peer ist nicht verbunden
  → Push via UnifiedPush/ntfy (siehe Sync 007)
  → Peer wacht auf, verbindet sich, holt fehlende Einträge
```

## Was gesynced wird

Verschiedene Daten syncen in verschiedenen Dokumenten:

| Dokument | Synced zwischen | Inhalt |
|----------|----------------|--------|
| Identity-Dokument | Eigene Geräte | Profil, Kontakte |
| Key-Dokument | Eigene Geräte | Group Keys |
| Space-Dokument (pro Space) | Alle Space-Members | CRDT-Daten des Spaces |

Jedes Dokument hat seinen eigenen Log. Kein Cross-Triggering — Identity-Sync und Space-Sync sind unabhängig.

## Direkte Nachrichten (Inbox)

Nicht alles läuft über den Log. Einige Nachrichten werden direkt zugestellt:

- **Attestations** — 1:1 verschlüsselt, an den Empfänger
- **Space-Einladungen** — Snapshot + Group Key, an das neue Mitglied
- **Verifications** — Challenge-Response bei Begegnung
- **Key-Rotation** — Neuer Space Key nach Member-Entfernung

Diese Nachrichten gehen über die Inbox des Brokers (siehe [Sync 007](007-transport-und-broker.md)), nicht über den Log.

## Herkunft der Ideen

| Idee | Quelle |
|------|--------|
| Append-only Logs | Jazz, p2panda |
| Sedimentree (Kompression) | Ink & Switch (Beelay) |
| RIBLT (Reconciliation) | ORP (Nik Graf), ACM SIGCOMM 2024 |
| Peer = Peer | p2panda (Shared Nodes), Iroh |
| Drei-Schichten-Modell | Niks Erfahrung (secsync → ORP) |

## Architektur-Grundlage

Siehe [Sync-Architektur](../research/sync-architektur.md) für den vollständigen Architektur-Entwurf.
