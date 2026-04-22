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

Ein Log-Eintrag ist ein **JWS-signierter Datensatz**. Er wird über das DIDComm-Envelope als `body` einer `log-entry`-Nachricht transportiert (siehe [Sync 007](007-transport-und-broker.md#message-envelope-didcomm-kompatibel)), ist aber selbst kein DIDComm-Message — er ist ein Datensatz der im Append-only Log persistiert wird.

**JWS-Payload:**

```json
{
  "seq": 42,
  "deviceId": "550e8400-e29b-41d4-a716-446655440000",
  "docId": "7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b",
  "authorDid": "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
  "keyGeneration": 3,
  "data": "<Base64URL-kodierter verschlüsselter Blob>",
  "timestamp": "2026-04-17T10:00:00Z"
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

### seq-Konsistenz (MUSS)

Der `seq`-Wert ist mehr als nur eine Reihenfolge-Nummer — er ist ein **Sicherheits-kritisches Feld**, weil er in die Nonce-Konstruktion für die AES-256-GCM-Verschlüsselung einfließt (siehe [Sync 005](005-verschluesselung.md#nonce-konstruktion)). Ein Wiederverwenden von `seq` durch dasselbe Device führt zu Nonce-Reuse und damit zu einem kompletten Sicherheits-Zusammenbruch.

**Anforderungen:**

- Vor jedem Schreibvorgang MUSS der Client den aktuellen höchsten `seq`-Wert kennen für (`deviceId`, `docId`, `keyGeneration`)
- Dieser Wert MUSS aus dem persistierten Log gelesen werden, nicht aus volatilem Memory
- Der neue `seq` MUSS strikt größer sein als alle bisher geschriebenen
- Bei Divergenz zwischen lokalem Log und Broker-Log MUSS der höhere Wert zugrunde gelegt werden

**Kritische Edge Cases:**

1. **Device-Crash nach Broker-Übermittlung, vor lokaler Persistenz**
   - Problem: Broker kennt `seq=42` mit Inhalt A, lokales Log kennt nur bis `seq=41`
   - Nach Restart: Client würde `seq=42` neu vergeben wollen mit Inhalt B
   - Resultat: gleicher Nonce mit gleichem Key für zwei verschiedene Klartexte → katastrophal
   - **Lösung:** Client MUSS lokale Persistenz VOR Übermittlung an den Broker durchführen

2. **Device-Restore / Clone / Multi-Tab (Restore-Detection-Regel — MUSS)**
   - Problem: Backup enthält `seq=1000`, zwischenzeitlich wurde `seq=1050` geschrieben; oder zwei parallele Instanzen der App mit gleicher `deviceId`
   - Naive "Full-Sync vor Schreiben" reicht nicht — zwischen Sync und Schreiben kann eine parallele Instanz dieselbe `(deviceId, seq)` nutzen
   - **Regel:** Beim App-Start / Reconnect MUSS der Client für jede aktive `(deviceId, docId)`-Kombination prüfen:
     1. Broker-`seq` für diese `(deviceId, docId)` abfragen
     2. Lokaler persistierter `seq` laden
     3. Falls `broker_seq > local_seq` (egal wie klein die Diskrepanz): **Restore/Clone erkannt**
   - Bei Restore/Clone-Erkennung MUSS der Client:
     1. Eine **neue zufällige `deviceId`** generieren
     2. Die alte `deviceId` beim Broker per signierter `device-revoke`-Nachricht deaktivieren (siehe [Sync 007](007-transport-und-broker.md#device-deaktivierung))
     3. Extensions über den `deviceId`-Wechsel informieren, damit device-spezifische Felder in Personal-Doc-Items aktualisiert werden können (siehe [Sync 010](010-personal-doc.md))
     4. Alle neuen Einträge unter der neuen `deviceId` schreiben (beginnend bei `seq=0`)
   - Damit gibt es keinen `(deviceId, seq)`-Konflikt mehr — die neue `deviceId` hat einen frischen `seq`-Raum

3. **Multi-Device mit gleichem Seed aber verschiedenen Devices**
   - Kein Problem: jedes Device hat eigene `deviceId`, eigenen `seq`-Raum
   - Die Nonces kollidieren nicht zwischen Devices

4. **Atomares Schreiben innerhalb eines Clients**
   - Bei gleichzeitigen Schreibvorgängen (z.B. zwei Browser-Tabs, parallele Async-Operationen) MUSS der Client `seq`-Allocation atomar mit dem Schreibvorgang durchführen
   - Konkret: Lock über `(deviceId, docId, keyGeneration)` — der Lesevorgang von `current_seq`, die Berechnung `next_seq = current_seq + 1`, das Persistieren des Eintrags und das Aktualisieren von `current_seq` MÜSSEN ununterbrechbar sein
   - Browser-Implementierungen SOLLEN `BroadcastChannel` oder `WebLocks API` für Cross-Tab-Koordination nutzen

### Signatur des Log-Eintrags

Der Log-Eintrag wird als JWS signiert — gemäß [Core 002](../01-wot-core/002-signaturen-und-verifikation.md):

1. Payload mit JCS kanonisieren (RFC 8785)
2. JCS-Bytes als Base64URL kodieren
3. Signing Input: `BASE64URL(header) + "." + BASE64URL(jcs_payload)`
4. Ed25519-Signatur über die Signing-Input-Bytes
5. Ergebnis: JWS Compact String

Ein Empfänger verifiziert die Signatur indem er `authorDid` aus dem Payload auflöst und den Public Key extrahiert.

### Transport über DIDComm

Ein Log-Eintrag wird als `body` einer DIDComm-Nachricht transportiert:

```json
{
  "id": "uuid",
  "type": "https://web-of-trust.de/protocols/log-entry/1.0",
  "from": "did:key:z6Mk...alice",
  "to": ["did:key:z6Mk...broker"],
  "created_time": "2026-04-17T10:00:00Z",
  "body": {
    "entry": "<JWS Compact String des Log-Eintrags>"
  }
}
```

Der Log-Eintrag ist bereits mit dem Space Key verschlüsselt (AES-256-GCM) und JWS-signiert. Die DIDComm-Nachricht transportiert ihn nur — keine zusätzliche ECIES-Verschlüsselung nötig.

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

## Censorship- und Split-Brain-Detection

Das Sync-Protokoll konvergiert korrekt solange Peers tatsächlich dieselben Log-Einträge sehen. Ein Zwischenakteur (Broker oder Admin mit Sonderrolle) kann jedoch Einträge selektiv unterdrücken oder gegenüber verschiedenen Peers unterschiedliche Antworten geben — ohne dass die Peers es von sich aus merken.

### Detection durch Multi-Source-Sync

Clients SOLLEN regelmäßig gegen mehrere verfügbare Quellen syncen — mehrere Broker desselben Space (siehe [Sync 007 Multi-Broker](007-transport-und-broker.md#multi-broker)) oder direkte P2P-Peers wenn ein alternativer Transport verfügbar ist (LAN, Bluetooth, QR-Code).

Das existierende `sync-request` gibt Heads pro `deviceId` zurück — der Vergleich ist ein einfacher Abgleich der Heads-Vektoren zweier Quellen:

- Identische Heads → konsistente Sicht, kein Handlungsbedarf
- Unterschiedliche Heads trotz erfolgter Sync-Runde → Indikator für Divergenz (Sync-Lag oder Censorship)

### Umgang mit Divergenz

Clients SOLLEN persistente Divergenz für den User sichtbar machen — als Status-Indikator im betroffenen Space, nicht als disruptiver Alarm. Der User SOLL Handlungsoptionen bekommen:

- Sync gegen alternativen Broker erzwingen
- Direkt-P2P-Sync mit einem anderen Mitglied versuchen
- Den Hinweis ignorieren (z.B. bei bekannter Sync-Latenz)

Konkrete UX-Formulierung liegt bei der Implementation. Die Spec fordert nur, dass Divergenz nicht still bleibt.

### Grenzen

Dieses Verfahren erkennt Censorship nur wenn der Client tatsächlich alternative Quellen hat. Communities mit einem einzigen Broker und ohne P2P-Kapazität sind strukturell ungeschützt — unabhängig von der Protokoll-Ausgestaltung. Details zur Bedrohungsmodellierung siehe [Security Analysis S3/S5](../research/security-analysis.md#s3-split-brain-durch-broker-manipulation).

## Was gesynced wird

Es gibt zwei Arten von Dokumenten, die sich in **Key-Management und Zielgruppe** unterscheiden, aber dasselbe Sync-Protokoll verwenden:

| Dokument | Synced zwischen | Inhalt | Key-Herkunft | Spezifiziert in |
|---|---|---|---|---|
| **Personal Doc** | Eigene Geräte des Users | Profil, Devices, Kontakte, Verifikationen, empfangene Attestations, Space-Mitgliedschaften, Space Keys | Deterministisch aus dem Seed abgeleitet | [Sync 010](010-personal-doc.md) |
| **Space-Dokument (pro Space)** | Alle Members des Space | CRDT-Daten des Spaces, Mitgliederliste | Zufällig generiert, per ECIES verteilt | [Sync 009](009-gruppen.md) |

Jedes Dokument hat seinen eigenen Log mit eigener `docId`. Kein Cross-Triggering — Personal-Doc-Sync und Space-Sync sind unabhängig.

**Konsolidierung statt mehrerer persönlicher Dokumente:** Frühere Entwürfe trennten ein "Identity-Dokument" (Profil, Kontakte) von einem "Key-Dokument" (Group Keys). Diese Trennung wurde aufgegeben — alles was zu einer Identität gehört liegt im Personal Doc. Das vereinfacht Cross-Device-Sync (ein Sync-Pfad statt mehrerer) und spiegelt die aktuelle Implementierung wider. Siehe [Sync 010](010-personal-doc.md) für die Struktur des Personal Doc.

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
