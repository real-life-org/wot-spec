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

### Snapshots und Full-State-Nachrichten

`wot-sync@0.1` normiert den Append-only Log als Interop-Baseline. Implementierungen DÜRFEN zusaetzlich Snapshots, Full-State-Nachrichten oder Vault-Backups verwenden, um Restore und Multi-Device-Catch-Up zu beschleunigen. Solche Optimierungen ersetzen den Log nicht als Konformitaetsanforderung.

Wenn eine Implementierung einen Snapshot oder Full-State-Payload uebertraegt, gelten dieselben Sicherheitsregeln wie fuer Log-Payloads:

- Der Payload MUSS mit dem Space Content Key der angegebenen `keyGeneration` verschluesselt sein.
- Das verschluesselte Format MUSS `Nonce | Ciphertext | Auth Tag` oder eine aequivalente eindeutig parsebare Form transportieren.
- Die Autorenschaft oder Transportberechtigung MUSS separat authentifiziert sein (z.B. Envelope-JWS, authentifizierte Broker-Verbindung plus Capability, oder inneres JWS).
- Ein Empfaenger DARF einen Snapshot nur mergen, wenn er zur erwarteten `docId` und `keyGeneration` passt.
- Peers MUESSEN weiterhin Log-Eintraege mit `authorKid`, `seq`, `deviceId` und `keyGeneration` verifizieren koennen.

Snapshots sind damit eine optionale Performance-Schicht, nicht das normative Sync-Wire-Format. Ein Snapshot ist nicht autoritativ gegenueber bereits bekannten gueltigen CRDT-Operationen: Clients MUESSEN einen Snapshot ueber den jeweiligen CRDT mergen und DUERFEN ihn nicht verwenden, um lokal bekannte gueltige Log-Eintraege zurueckzurollen oder zu ersetzen. Wenn der CRDT-Import oder Merge eines Snapshots fehlschlaegt, MUSS der Client den Snapshot ignorieren und mit Log-/State-Sync fortfahren.

## Sync-Modi

Das Log-Protokoll unterstützt Live-Sync und Catch-Up. Peers tauschen Heads pro `(docId, deviceId)` aus und senden fehlende Einträge. Push-Notifications sind nur ein Wecksignal; der Client holt fehlende Einträge danach über normalen Catch-Up (siehe [Sync 003](003-transport-und-broker.md#push-notifications)).

## Normative Sync-Flows

Die folgenden Flows definieren die Reihenfolge der Operationen fuer `wot-sync@0.1`. Implementierungen duerfen einzelne Schritte parallelisieren, MUESSEN aber dieselben Abhaengigkeiten einhalten und MUESSEN jeden Flow idempotent implementieren. Mehrfach empfangene Nachrichten, mehrfach publizierte Log-Eintraege und wiederholte `sync-request`-Runden duerfen keinen anderen Endzustand erzeugen als eine einmalige Verarbeitung.

### Gemeinsame Regeln

- Dauerhafter Zustand MUSS aus Log-Eintraegen, Personal-Doc-Eintraegen, Space-Metadaten, Group Keys und durabel gepufferten Inbox-Nachrichten rekonstruierbar sein.
- Durabel gepufferte Pending-Zustaende, z.B. Pending-Inbox, `blocked-by-key` oder `future-rotation`, sind lokaler crash-sicherer State. Der konkrete Speicherort ist implementationsspezifisch, MUSS aber App-Neustarts ueberleben und MUSS alle Metadaten enthalten, die fuer erneute Pruefung und Anwendung noetig sind, mindestens Message-/Log-Entry-ID, betroffene `docId`, Abhaengigkeitsart und erwartete `keyGeneration`.
- Ein Client DARF eine Inbox-Nachricht erst ACKen, wenn er sie entweder erfolgreich angewendet hat oder sie inklusive aller Abhaengigkeits-Metadaten dauerhaft gepuffert hat. Nach einem ACK darf der Broker die Nachricht fuer genau dieses Device loeschen (siehe [Sync 003 ACK](003-transport-und-broker.md#ack10--empfangsbestätigung)).
- Ein Client DARF einen empfangenen Log-Eintrag nicht verwerfen, nur weil ihm der passende `keyGeneration`-Key fehlt. Er MUSS den Eintrag speichern oder erneut abrufbar lassen und den Eintrag als `blocked-by-key` behandeln.
- Push- und Inbox-Nachrichten sind Wecksignale oder Key-/Control-Messages. Sie ersetzen keinen Log-Catch-Up fuer das betroffene Dokument.
- Snapshots, Full-State-Nachrichten und Vault-Backups sind Optimierungen. Sie duerfen keinen bekannten gueltigen Log-Eintrag zurueckrollen und duerfen eine fehlende Log-Sync-Runde nicht ersetzen.

### App-Start und Reconnect

Bei App-Start und bei jedem Broker-Reconnect MUSS ein Client fuer das Personal Doc und danach fuer alle bekannten aktiven Space-Dokumente folgenden Ablauf ausfuehren:

1. Lokalen persistenten Zustand laden: Device-ID, bekannte Heads pro `(docId, deviceId)`, lokale Log-Eintraege, durabel gepufferte Inbox-Nachrichten, Personal Doc, Space-Metadaten und Group Keys.
2. Beim Broker authentisieren, inklusive `did` und `deviceId` (siehe [Sync 003 Authentisierung](003-transport-und-broker.md#authentisierung)).
3. Fuer das Personal Doc `broker_seq` und `local_seq` fuer die eigene `(deviceId, docId)`-Kombination vergleichen, bevor neue Personal-Doc-Eintraege an den Broker publiziert werden. Bei `broker_seq > local_seq` gilt die Restore-/Clone-Regel aus [seq-Konsistenz](#seq-konsistenz-muss).
4. Die eigene Device-Inbox drainen. Inbox-Nachrichten duerfen in beliebiger Reihenfolge empfangen werden, MUESSEN aber gemaess [Inbox-Verarbeitung](#inbox-verarbeitung-und-ack) verarbeitet, angewendet oder durabel gepuffert werden.
5. Das Personal Doc per `sync-request` synchronisieren, bevor Space-Dokumente verarbeitet werden, die neue Space-Mitgliedschaften oder Group Keys benoetigen koennen.
6. Nach abgeschlossenem Personal-Doc-Catch-Up die aktiven Space-Dokumente aus aktualisiertem Personal Doc, lokal persistenten Space-Metadaten und durabel gepufferten Abhaengigkeiten bestimmen.
7. Fuer jedes bekannte Space-Dokument `broker_seq` und `local_seq` fuer die eigene `(deviceId, docId)`-Kombination vergleichen, bevor neue Space-Eintraege publiziert werden, und danach einen `sync-request` mit den lokal bekannten Heads senden.
8. Empfangene `sync-response`-Eintraege verifizieren, lokal persistieren, nach `keyGeneration` entschluesseln und in den CRDT mergen. Eintraege mit fehlenden Keys werden als `blocked-by-key` gespeichert und spaeter erneut verarbeitet.
9. Erst nach Personal-Doc-Catch-Up, Inbox-Verarbeitung und Space-Catch-Up SOLL die UI den Sync-Zustand als aktuell anzeigen. Eine Implementierung DARF vorher lokale Daten anzeigen, MUSS diese aber als potentiell veraltet behandeln.

Wenn mehrere Broker oder P2P-Quellen verfuegbar sind, SOLLTE der Client diese Runden gegen mehrere Quellen ausfuehren und Heads vergleichen (siehe [Censorship- und Split-Brain-Detection](#censorship--und-split-brain-detection)).

### Lokaler Schreibvorgang

Bei jedem lokalen Schreibvorgang in ein Personal Doc oder Space-Dokument MUSS der Client:

1. Den naechsten `seq`-Wert atomar aus dem persistenten Log fuer `(deviceId, docId)` reservieren. Wenn der Broker erreichbar ist, MUSS vorher ein Broker-Head-Abgleich stattfinden; wenn der Client offline ist, MUSS spaetestens vor der ersten Publikation nach Reconnect der Broker-Head-Abgleich stattfinden.
2. Den CRDT-Update-Payload mit dem aktuell gueltigen Key und der aktuell gueltigen `keyGeneration` verschluesseln.
3. Einen Log-Entry-JWS mit `seq`, `deviceId`, `docId`, `authorKid`, `keyGeneration`, `data` und `timestamp` erzeugen und signieren.
4. Den Log-Eintrag lokal persistieren, bevor er an Broker oder Peers uebermittelt wird.
5. Den Log-Eintrag an alle relevanten Broker/Peers publizieren. Fehler bei der Uebermittlung MUESSEN als retrybarer Outbox-Zustand behandelt werden; eine erneute Publikation desselben Log-Eintrags MUSS idempotent sein.
6. Keine Inbox-ACK-Semantik fuer Log-Eintraege verwenden. Fehlende Log-Eintraege werden ueber Heads und `sync-request` erkannt.

### Inbox-Verarbeitung und ACK

Inbox-Nachrichten sind direkte Nachrichten wie Attestations, Verifications, Space-Einladungen, `member-update` und `key-rotation`. Fuer jede empfangene Inbox-Nachricht MUSS der Client:

1. ECIES entschluesseln, wenn die Nachricht verschluesselt ist.
2. Das innere JWS oder das normative persistente Objekt verifizieren. Envelope-Felder allein duerfen nicht als Autoritaetsanker verwendet werden (siehe [Sync 003 Autoritaetsgrenze](003-transport-und-broker.md#autoritätsgrenze-muss)).
3. Replay-Schutz ueber Message-ID-History anwenden.
4. Die resultierende lokale Aenderung anwenden oder die Nachricht durabel in einer Pending-Inbox speichern, wenn Abhaengigkeiten fehlen.
5. Falls die Nachricht ein Dokument betrifft, danach einen `sync-request` fuer dieses Dokument ausloesen oder vormerken. Ein `space-invite` fuehrt zu Space-Catch-Up; eine `key-rotation` fuehrt zu erneuter Verarbeitung blockierter Log-Eintraege fuer diese `keyGeneration`.
6. Erst dann ACKen, wenn Schritt 4 dauerhaft abgeschlossen ist. Bei einem Prozess-Crash nach ACK MUSS der Client ohne erneute Broker-Zustellung fortfahren koennen.

Wenn eine Inbox-Nachricht ungueltig ist (falsche Signatur, falscher Empfaenger, Replay, abgelaufen), MUSS der Client sie verwerfen und DARF sie ACKen, damit der Broker sie fuer dieses Device nicht erneut liefert. Der Client SOLLTE lokale Audit-/Debug-Informationen speichern, aber keinen autoritativen State aendern.

### Space-Invite-Annahme

Bei Annahme einer `space-invite` MUSS der Client:

1. Einladung entschluesseln und inneres JWS, Empfaenger-DID, Capability und `currentKeyGeneration` pruefen.
2. Space Content Keys, Space Capability Signing Key, Capability, Broker-URLs und Space-Metadaten im Personal Doc oder lokalem aequivalentem Zustand persistieren.
3. Danach den Invite ACKen.
4. Einen `sync-request` fuer das Space-Dokument mit leeren oder lokalen Heads senden.
5. Empfangene Log-Eintraege gemaess normalem Space-Catch-Up verarbeiten. Wenn die Einladung nicht alle historischen Keys enthaelt, MUSS der erste verarbeitbare Snapshot oder Log-Eintrag mit `currentKeyGeneration` erreichbar sein; sonst bleibt der Space `blocked-by-key`.

### Key-Rotation und Generation-Gaps

Key-Rotation ist eine Abhaengigkeit fuer alle spaeteren Space-Log-Eintraege. Clients MUESSEN folgende Regeln anwenden:

- Empfaengt ein Client eine `key-rotation` mit `generation = localGeneration + 1`, MUSS er den neuen Content Key und die neue Capability durabel speichern, blockierte Log-Eintraege dieser Generation erneut verarbeiten und einen `sync-request` fuer das Space-Dokument ausloesen.
- Empfaengt ein Client eine `key-rotation` mit `generation <= localGeneration`, MUSS er sie als doppelt oder veraltet behandeln. Er DARF sie ACKen, nachdem Replay- und Signaturpruefung abgeschlossen sind.
- Empfaengt ein Client eine `key-rotation` mit `generation > localGeneration + 1`, MUSS er sie als `future-rotation` durabel puffern. Er DARF sie nicht anwenden, bevor die Luecke geschlossen ist. Er MUSS fehlende Rotationen, Personal-Doc-Keys oder einen aktuellen Full-State/Log-Catch-Up anfordern.
- Empfaengt ein Client einen Log-Eintrag mit unbekannter `keyGeneration`, MUSS er den Eintrag als `blocked-by-key` speichern oder erneut abrufbar lassen und Key-/Personal-Doc-Catch-Up anfordern. Er DARF den Eintrag nicht als verarbeitet markieren.
- Sobald eine fehlende Generation verfuegbar wird, MUSS der Client alle gepufferten `future-rotation`-Nachrichten und `blocked-by-key`-Log-Eintraege in aufsteigender Generation erneut pruefen.

`Anfordern` von fehlenden Rotationen oder Keys bedeutet in `wot-sync@0.1`, dass ein Client die bestehenden Sync-Quellen erneut nutzt: eigene Device-Inbox drainen, Personal Doc per `sync-request` aufholen, fuer das betroffene Space-Dokument einen `sync-request` senden und, falls implementiert, einen autorisierten Snapshot oder Full-State abrufen. Ein separates generisches `key-request` Nachrichtenformat ist in `wot-sync@0.1` nicht normiert. Solange die fehlende Generation danach nicht verfuegbar ist, MUSS der Client die betroffenen `future-rotation`- und `blocked-by-key`-Eintraege durabel gepuffert lassen und bei App-Start, Reconnect oder neuem Wecksignal erneut aufloesen.

### Snapshot- und Full-State-Optimierungen

Snapshots und Full-State-Nachrichten duerfen verwendet werden, um lange Catch-Up-Runden zu beschleunigen. Sie MUESSEN aber wie folgt eingeordnet werden:

1. Ein Snapshot MUSS mindestens `docId`, `keyGeneration` und eine Abdeckung der enthaltenen Log-Heads (`heads` oder aequivalente Metadaten) besitzen, wenn er als Catch-Up-Optimierung verwendet wird.
2. Kann eine Implementierung die Abdeckung nicht bestimmen, DARF sie den Snapshot nur als CRDT-Merge-Hilfe verwenden und MUSS danach trotzdem eine normale `sync-request`-Runde ausfuehren.
3. Ein Snapshot mit unbekannter oder zukuenftiger `keyGeneration` wird wie ein blockierter Log-Eintrag behandelt: puffern oder erneut abrufen, fehlende Keys anfordern, nicht als verarbeitet markieren.
4. Ein Snapshot DARF keine lokal bekannten gueltigen Log-Eintraege loeschen oder ueberschreiben. Der CRDT-Merge bleibt autoritativ fuer Konvergenz.
5. Zeitbasierte Retry-Mechanismen duerfen als Implementierungsdetail existieren, sind aber nicht der normative Sync-Mechanismus. Normative Recovery basiert auf Heads, `sync-request`, per-Device-Inbox und Generation-Gap-Erkennung.

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
