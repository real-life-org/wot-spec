# WoT Sync 002: Sync-Protokoll

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-13
- **Scope:** Append-only Logs, Sequenzen, Konflikterkennung und Sync-Ablauf
- **Depends on:** Identity 002, Sync 001
- **Conformance profile:** `wot-sync@0.1`

## Zusammenfassung

Dieses Dokument spezifiziert wie Daten zwischen Peers synchronisiert werden — verschlüsselt, CRDT-agnostisch, und über beliebige Transportwege. Das Protokoll ist für alle Peers identisch — ob Handy, Laptop oder Broker.

## Referenzierte Standards

- **Ed25519** (RFC 8032) — Signatur der Log-Einträge
- **AES-256-GCM** (NIST SP 800-38D) — Verschlüsselung der Payloads (siehe [Sync 001](001-verschluesselung.md))

## Grundprinzip

Das Sync-Protokoll ist für alle Peers identisch. Phase 1 spezifiziert nur den Append-only Log pro Device und Dokument. Kompression (z.B. Sedimentree) und effiziente Set-Reconciliation (z.B. RIBLT) sind zukünftige Erweiterungen und nicht Teil dieses Konformitätsprofils.

### Ausbauphasen des Sync-Protokolls

Das langfristige Sync-Design besteht aus drei aufeinander aufbauenden Phasen. Nur Phase 1 ist Teil von `wot-sync@0.1`; Phase 2 und Phase 3 sind bewusst dokumentierte, aber noch nicht normative Erweiterungen.

| Phase | Bestandteil | Zweck | Status |
|---|---|---|---|
| **1** | Append-only Log | Korrektes, einfaches Live-Sync und Catch-Up ueber Heads pro `(docId, deviceId)` | Normativ in `wot-sync@0.1` |
| **2** | Deterministische Kompression | Alte History zu reproduzierbaren Chunks verdichten, ohne Koordinator oder vertrauenswuerdigen Snapshot-Ersteller | Zukunft |
| **3** | Effiziente Set-Reconciliation | Stark divergierte Peers effizient abgleichen, proportional zur tatsaechlichen Differenz statt zur Log-Groesse | Zukunft |

Phase 2 kann sich an Sedimentree-orientiertem Chunking orientieren: Chunk-Grenzen werden deterministisch aus Hash-Eigenschaften berechnet, sodass verschiedene Peers unabhaengig dieselben komprimierten History-Segmente erzeugen koennen. Phase 3 kann RIBLT-basierte Reconciliation nutzen, um nach langer Offline-Zeit oder bei mehreren Quellen nur die fehlenden Eintraege bzw. Chunks zu identifizieren.

Diese Phasen sind wichtig fuer langfristige Skalierung, aber Implementierungen duerfen `wot-sync@0.1` beanspruchen, ohne Phase 2 oder Phase 3 zu implementieren. Details stehen im nicht-normativen Architekturentwurf [Sync-Architektur](../research/sync-architektur.md).

## Device-Identifikation

Jedes Gerät generiert beim ersten Start eine zufällige **Device-UUID** und speichert sie lokal:

```
deviceId = crypto.randomUUID()
```

Log-Einträge werden pro `deviceId` pro `docId` sequenziert. Die UUID ist kein kryptografischer Key, sondern nur der Sequenz- und Nonce-Namespace eines Devices.

## Log

Jeder Peer führt einen Append-only Log pro Dokument. Jeder Eintrag ist ein verschlüsselter Blob — das Protokoll weiß nicht was drin ist.

### Log-Eintrag

Ein Log-Eintrag ist ein **persistentes WoT-Objekt**: ein JWS-signierter Datensatz, der im Append-only Log gespeichert wird. Er ist selbst keine DIDComm Message. Er DARF als opaker JWS Compact String in einer `log-entry`-Nachricht oder `sync-response` transportiert werden (siehe [Sync 003](003-transport-und-broker.md#wire-formate-der-sync-nachrichten)).

**JWS-Payload:**

```json
{
  "seq": 42,
  "deviceId": "550e8400-e29b-41d4-a716-446655440000",
  "docId": "7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b",
  "authorKid": "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK#sig-0",
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
| `authorKid` | DID-URL | Ja | Verification Method ID des Signierenden (z.B. `did:key:z6Mk...#sig-0`). DID wird aus dem Teil vor `#` extrahiert. In Phase 1 ist das Fragment immer `#sig-0` (einziger Key). In Phase 2 identifiziert es einen spezifischen Device-Key. |
| `keyGeneration` | Integer | Ja | Generation des Space Content Keys der zur Verschlüsselung verwendet wurde (siehe [Sync 001](001-verschluesselung.md)) |
| `data` | String | Ja | Base64URL-kodierter AES-256-GCM Ciphertext (Nonce + Ciphertext + Auth Tag, siehe [Sync 001](001-verschluesselung.md)) |
| `timestamp` | ISO 8601 | Ja | Erstellungszeitpunkt (UTC) |

### seq-Konsistenz (MUSS)

Der `seq`-Wert ist sicherheitskritisch, weil er in die AES-256-GCM-Nonce-Konstruktion einfließt (siehe [Sync 001](001-verschluesselung.md#nonce-konstruktion)). Ein Wiederverwenden von `seq` durch dasselbe Device führt zu Nonce-Reuse.

**Anforderungen:**

- Vor jedem Schreibvorgang MUSS der Client den aktuellen höchsten `seq`-Wert für (`deviceId`, `docId`) kennen
- Dieser Wert MUSS aus dem persistierten Log gelesen werden, nicht aus volatilem Memory
- Der neue `seq` MUSS strikt größer sein als alle bisher geschriebenen
- Bei Divergenz zwischen lokalem Log und Broker-Log MUSS der höhere Wert zugrunde gelegt werden

**Crash-/Restore-/Clone-Regeln:**

- Der Client MUSS lokale Persistenz vor Übermittlung an den Broker durchführen.
- Beim App-Start oder Reconnect MUSS der Client für jede aktive `(deviceId, docId)`-Kombination `broker_seq` und lokalen persistierten `local_seq` vergleichen.
- Falls `broker_seq > local_seq`, MUSS der Client Restore/Clone annehmen, eine neue zufällige `deviceId` generieren, die alte `deviceId` per signierter `device-revoke`-Nachricht deaktivieren (siehe [Sync 003](003-transport-und-broker.md#device-deaktivierung)) und neue Einträge unter der neuen `deviceId` ab `seq=0` schreiben.
- Extensions MÜSSEN über den `deviceId`-Wechsel informiert werden, wenn sie device-spezifische Felder führen (siehe [Sync 006](006-personal-doc.md)).
- Bei parallelen Schreibvorgängen MUSS `seq`-Allocation atomar über `(deviceId, docId)` erfolgen. Browser-Implementierungen SOLLEN Cross-Tab-Koordination verwenden.

### Signatur des Log-Eintrags

Der Log-Eintrag wird als JWS Compact Serialization signiert, gemäß [Identity 002](../01-wot-identity/002-signaturen-und-verifikation.md): Payload mit JCS kanonisieren, Base64URL-kodieren, Ed25519-Signatur über den JWS Signing Input erzeugen.

Ein Empfänger verifiziert die Signatur indem er die DID aus `authorKid` extrahiert (Teil vor `#`), das DID-Dokument via `resolve()` auflöst ([Identity 003](../01-wot-identity/003-did-resolution.md)), die `verificationMethod` mit der passenden `id` findet und den Public Key daraus extrahiert.

### Transport-Framing

Ein einzelner Log-Eintrag KANN als `entry` im `body` einer DIDComm-Plaintext-Nachricht transportiert werden:

```json
{
  "id": "uuid",
  "typ": "application/didcomm-plain+json",
  "type": "https://web-of-trust.de/protocols/log-entry/1.0",
  "from": "did:key:z6Mk...alice",
  "to": ["did:key:z6Mk...broker"],
  "created_time": 1776420000,
  "body": {
    "entry": "<JWS Compact String des Log-Eintrags>"
  }
}
```

Der Log-Eintrag ist bereits mit dem Space Content Key verschlüsselt und JWS-signiert. Die DIDComm-Nachricht transportiert ihn nur; zusätzliche ECIES-Verschlüsselung ist nicht nötig.

Der DIDComm-Envelope ist **kein Autoritätsanker** für den Log-Eintrag. Empfänger MÜSSEN die Autorenschaft über `authorKid` im Log-Entry-JWS prüfen und DÜRFEN sich dafür nicht auf `from` im Envelope verlassen. Bei Bulk-Sync SOLLEN mehrere Log-Einträge als JWS-Strings in einer `sync-response` transportiert werden, statt jeden Eintrag einzeln zu wrappen.

### Verschlüsselter Payload (`data`)

Der `data`-Blob enthält ein mit AES-256-GCM verschlüsseltes CRDT-Update:

```
Klartext (CRDT-Update, z.B. Yjs-Binary)
  → AES-256-GCM verschlüsseln mit Space Content Key (Generation = keyGeneration)
  → Nonce (12 Bytes) + Ciphertext + Auth Tag (16 Bytes)
  → Base64URL kodieren
  → in `data`-Feld schreiben
```

### CRDT-Agnostik

Der entschlüsselte Payload ist opak. Der CRDT-Typ steht in der Space-Metadata, nicht im Log-Eintrag. Peers schreiben nur in den Log ihrer eigenen `deviceId`; empfangene Einträge bleiben unter der `deviceId` des Autors gespeichert.

## Sync-Modi

Das Log-Protokoll unterstützt Live-Sync und Catch-Up. Peers tauschen Heads pro `(docId, deviceId)` aus und senden fehlende Einträge. Push-Notifications sind nur ein Wecksignal; der Client holt fehlende Einträge danach über normalen Catch-Up (siehe [Sync 003](003-transport-und-broker.md#push-notifications)).

## Censorship- und Split-Brain-Detection

Das Sync-Protokoll konvergiert, solange Peers dieselben Log-Einträge sehen. Broker oder andere Zwischenakteure können jedoch Einträge selektiv unterdrücken oder verschiedenen Peers unterschiedliche Heads zeigen.

### Detection durch Multi-Source-Sync

Clients SOLLEN regelmäßig gegen mehrere verfügbare Quellen syncen: mehrere Broker desselben Space (siehe [Sync 003 Multi-Broker](003-transport-und-broker.md#broker-zuordnung-und-multi-broker)) oder direkte P2P-Peers.

Das existierende `sync-request` gibt Heads pro `deviceId` zurück — der Vergleich ist ein einfacher Abgleich der Heads-Vektoren zweier Quellen:

- Identische Heads → konsistente Sicht, kein Handlungsbedarf
- Unterschiedliche Heads trotz erfolgter Sync-Runde → Indikator für Divergenz (Sync-Lag oder Censorship)

### Umgang mit Divergenz

Clients SOLLEN persistente Divergenz für den User sichtbar machen und mindestens alternative Broker- oder P2P-Sync-Versuche anbieten. Divergenz DARF nicht still ignoriert werden.

### Grenzen

Dieses Verfahren erkennt Censorship nur wenn der Client alternative Quellen hat. Single-Broker-Communities ohne P2P-Option bleiben strukturell ungeschützt. Details: [Security Analysis S3/S5](../research/security-analysis.md#s3-split-brain-durch-broker-manipulation).

## Was gesynced wird

Zwei Dokumentarten verwenden dasselbe Sync-Protokoll:

| Dokument | Synced zwischen | Inhalt | Key-Herkunft | Spezifiziert in |
|---|---|---|---|---|
| **Personal Doc** | Eigene Geräte des Users | Profil, Devices, Kontakte, Verifikationen, empfangene Attestations, Space-Mitgliedschaften, Space Content Keys | Deterministisch aus dem Seed abgeleitet | [Sync 006](006-personal-doc.md) |
| **Space-Dokument (pro Space)** | Alle Members des Space | CRDT-Daten des Spaces, Mitgliederliste | Zufällig generiert, per ECIES verteilt | [Sync 005](005-gruppen.md) |

Jedes Dokument hat seinen eigenen Log mit eigener `docId`. Personal-Doc-Sync und Space-Sync sind unabhängig.

## Direkte Nachrichten (Inbox)

Direkte 1:1-Nachrichten wie Attestations, Space-Einladungen, Verifications und Key-Rotation laufen über die Inbox des Brokers (siehe [Sync 003](003-transport-und-broker.md)), nicht über den Log.

## Architektur-Grundlage

Siehe [Sync-Architektur](../research/sync-architektur.md) für den vollständigen Architektur-Entwurf.
