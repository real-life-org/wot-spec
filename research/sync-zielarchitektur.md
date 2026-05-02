# WoT Sync-Zielarchitektur

> **Nicht normativ:** Dieses Dokument beschreibt ein gemeinsames mentales Modell fuer die Sync-Architektur. Normative Anforderungen stehen in `03-wot-sync/*` und `CONFORMANCE.md`.

- **Status:** Entwurf
- **Datum:** 2026-05-02
- **Bezug:** `wot-sync@0.1`

## Ziel

Dieses Dokument trennt die Protokollrollen von konkreten Implementierungen. Es sagt nicht, ob eine Implementierung Yjs, Automerge, Loro, IndexedDB, SQLite, WebSocket oder einen anderen Transport verwendet. Entscheidend ist, dass alle Implementierungen dieselben Sync-Abhaengigkeiten, ACK-Zeitpunkte und Recovery-Regeln einhalten.

## Architekturrollen

<!-- Uebersicht: 30-Sekunden-Bild. Details in den Diagrammen weiter unten. -->

```mermaid
flowchart TD
  SE(["🎯 Sync Engine\nStart · Reconnect · Writes"])

  subgraph net["🌐 Netzwerk"]
    direction LR
    Broker["Broker / Relay"]
    Peers["Peers · Snapshots"]
  end

  IP["📨 Inbox Path\nInvite · Keys · Members · Attestation"]
  LP["📋 Log Path\nHead-Vergleich · CRDT Catch-Up · Decrypt"]

  subgraph state["💾 Lokaler Durable State"]
    direction LR
    Docs["Dokumente · Keys · Metadata"]
    Pending["Pending Buffer"]
  end

  SE -.-> IP
  SE -.-> LP

  Broker -->|"Inbox"| IP
  Broker -->|"Entries"| LP
  Peers --> LP

  IP --> Docs
  IP --> Pending
  LP --> Docs
  LP --> Pending

  IP -->|"ACK"| Broker

  classDef netS fill:#fff7ed,stroke:#ea580c,stroke-width:2px
  classDef pathS fill:#dbeafe,stroke:#2563eb,stroke-width:2px
  classDef stateS fill:#ecfdf5,stroke:#059669,stroke-width:2px
  classDef orchS fill:#fef9c3,stroke:#ca8a04,stroke-width:2.5px

  class Broker,Peers netS
  class IP,LP pathS
  class Docs,Pending stateS
  class SE orchS
```

> **Nicht gezeigt:** Key Store, Log Store, Device State, Key Resolver, ACK Policy, CRDT Engine — diese Rollen sind in der Tabelle unten beschrieben und in den Detail-Diagrammen (Startup, Inbox-Flow, Key-Rotation) aufgeschluesselt.

## Verantwortung Der Rollen

| Rolle | Verantwortung | Normativer Bezug |
|---|---|---|
| Sync State Machine | Orchestriert App-Start, Reconnect, lokale Writes, Catch-Up und Pending-Replay | `03-wot-sync/002` |
| Inbox Processor | Verarbeitet direkte Inbox-Nachrichten wie Invite, Member Update, Key Rotation, Attestation, Verification | `03-wot-sync/002`, `003`, `005` |
| ACK Policy | Sendet ACK erst nach Anwendung oder durablem Pending-Speicher | `03-wot-sync/002`, `003` |
| Log Catch-Up | Vergleicht Heads und laedt fehlende Log-Eintraege | `03-wot-sync/002`, `003` |
| Key Dependency Resolver | Erkennt `blocked-by-key` und `future-rotation` und triggert Key-/Personal-Doc-Catch-Up | `03-wot-sync/002`, `005`, `006` |
| CRDT Document Engine | Wendet entschluesselte Updates an und exportiert Updates/Snapshots | CRDT-agnostisch, durch `03-wot-sync/002` nur als Payload betrachtet |
| Pending Inbox | Crash-sicherer lokaler Speicher fuer nicht anwendbare, aber gueltige Nachrichten/Eintraege | `03-wot-sync/002`, `003` |
| Broker / Relay | Authentisiert DID + Device, verwaltet per-device Inbox, liefert Nachrichten, beantwortet Sync-Requests | `03-wot-sync/003` |
| Snapshot / Full-State Source | Optimiert Restore/Catch-Up, ersetzt aber nie Log-Catch-Up als Norm | `03-wot-sync/002` |

## Start Und Reconnect

```mermaid
sequenceDiagram
  participant Peer
  participant Local as Local Durable State
  participant Broker
  participant Personal as Personal Doc
  participant Pending as Pending Inbox
  participant Keys as Key Store
  participant Log as Space Log Catch-Up
  participant Doc as CRDT Engine

  Peer->>Local: load deviceId, heads, logs, pending, metadata, keys
  Peer->>Broker: authenticate did + deviceId
  Peer->>Broker: compare broker_seq/local_seq for Personal Doc
  Broker-->>Peer: queued Inbox messages
  Peer->>Pending: apply or durable-buffer before ACK
  Peer->>Broker: ACK only after apply/buffer
  Peer->>Personal: sync-request Personal Doc
  Personal->>Keys: import space keys and memberships
  Peer->>Log: determine active spaces after Personal Doc catch-up
  loop each active Space
    Peer->>Broker: compare broker_seq/local_seq
    Peer->>Broker: sync-request with local heads
    Broker-->>Peer: missing log entries
    Peer->>Keys: resolve keyGeneration
    alt key available
      Peer->>Doc: decrypt and apply CRDT update
      Peer->>Local: persist log and document state
    else key missing
      Peer->>Pending: durable blocked-by-key
    end
  end
  Peer->>Pending: replay after key catch-up
```

Kernaussagen:

- Personal Doc kommt vor Space-Dokumenten, weil Space-Mitgliedschaften und Group Keys dort liegen koennen.
- Inbox-Nachrichten duerfen als Wecksignal dienen, ersetzen aber keinen Log-Catch-Up.
- Ein ACK ist nur erlaubt, wenn der Client nach Crash ohne erneute Broker-Zustellung fortfahren kann.
- Ein unbekannter Key ist kein Fehler zum Verwerfen, sondern ein Abhaengigkeitszustand.

## Lokaler Schreibvorgang

```mermaid
sequenceDiagram
  participant User
  participant Peer
  participant Broker
  participant LogStore
  participant Keys
  participant Doc as CRDT Engine
  participant Snapshot as Snapshot Source

  User->>Peer: local change
  Peer->>Broker: if online, head check for own device/doc
  Peer->>LogStore: reserve next seq atomically
  Peer->>Doc: create CRDT update
  Peer->>Keys: current content key + keyGeneration
  Peer->>Peer: encrypt update + sign Log Entry JWS
  Peer->>LogStore: persist log entry before publish
  Peer->>Broker: publish log entry / wake peers
  Peer->>Snapshot: optional snapshot/full-state optimization
```

Kernaussagen:

- Lokaler State entsteht zuerst lokal und durable.
- Publikation an Broker/Peers ist retrybar und idempotent.
- Log-Eintraege verwenden keine Inbox-ACK-Semantik.
- Snapshots duerfen beschleunigen, aber keine gueltigen Log-Eintraege ersetzen oder zurueckrollen.

## Inbox, Pending Und ACK

```mermaid
flowchart TD
  Receive["Inbox message received"] --> Decrypt["decrypt if encrypted"]
  Decrypt --> Verify["verify inner JWS / object"]
  Verify --> Replay["replay check"]
  Replay --> Dependencies{"dependencies available?"}

  Dependencies -->|yes| Apply["apply state change"]
  Apply --> DurableApplied["persist resulting state"]
  DurableApplied --> Ack["ACK this device inbox"]

  Dependencies -->|no| Classify["classify dependency"]
  Classify --> Blocked["blocked-by-key"]
  Classify --> Future["future-rotation"]
  Classify --> Unknown["unknown-space"]
  Blocked --> PersistPending["durably persist pending + metadata"]
  Future --> PersistPending
  Unknown --> PersistPending
  PersistPending --> Ack

  Verify -->|invalid| Drop["drop invalid message"]
  Drop --> AckInvalid["ACK allowed to stop redelivery"]
```

Pending-Metadaten muessen mindestens enthalten:

- Message- oder Log-Entry-ID
- betroffene `docId` oder Space-ID
- Abhaengigkeitsart
- erwartete `keyGeneration`, falls vorhanden
- ausreichend Daten, um die Nachricht spaeter erneut zu pruefen und anzuwenden

Der Speicherort ist implementationsspezifisch. Er muss aber crash-sicher sein und App-Neustarts ueberleben.

## Key-Rotation Und Generation-Gaps

```mermaid
flowchart TD
  Rotation["key-rotation received"] --> Compare{"generation compared to local"}
  Compare -->|generation = local + 1| ApplyRotation["store key + capability"]
  ApplyRotation --> ReplayBlocked["replay blocked entries for generation"]
  ReplayBlocked --> SpaceCatchUp["trigger Space sync-request"]

  Compare -->|generation <= local| Stale["stale or duplicate"]
  Stale --> AckStale["ACK after verification"]

  Compare -->|generation > local + 1| Future["future-rotation"]
  Future --> PersistFuture["durably buffer"]
  PersistFuture --> RequestMissing["drain Inbox + Personal Doc catch-up + Space sync-request + optional snapshot/full-state"]
  RequestMissing --> Wait["retry on start, reconnect, wake signal"]
```

`wot-sync@0.1` definiert kein generisches `key-request` Nachrichtenformat. Fehlende Rotationen oder Keys werden ueber bestehende Quellen gesucht:

- eigene Device-Inbox
- Personal Doc Catch-Up
- Space `sync-request`
- optionale Snapshot-/Full-State-Quelle

## CRDT-Agnostik

```mermaid
flowchart LR
  LogEntry["Encrypted Log Entry\nkeyGeneration + ciphertext"] --> Decrypt["decrypt"]
  Decrypt --> Payload["opaque CRDT update"]
  Payload --> Engine["CRDT Engine\nYjs / Automerge / Loro / other"]
  Engine --> State["document state"]
  Engine --> Export["export update / snapshot"]
  Export --> Encrypt["encrypt + sign"]
  Encrypt --> LogEntryOut["new Log Entry"]
```

Das Sync-Protokoll behandelt CRDT-Daten als verschluesselten Payload. Es normiert Signatur, Log, Keys, Catch-Up und ACK-Regeln, aber nicht die interne CRDT-Datenstruktur.

## Snapshot Und Full-State

```mermaid
flowchart TD
  NeedCatchUp["Client needs catch-up"] --> LogFirst["normal log sync via heads"]
  NeedCatchUp --> Snapshot["optional snapshot/full-state"]

  Snapshot --> HasCoverage{"has docId, keyGeneration, coverage metadata?"}
  HasCoverage -->|yes| Merge["merge as optimization"]
  HasCoverage -->|no| MergeOnly["merge as CRDT help only"]
  MergeOnly --> LogFirst
  Merge --> LogFirst
  LogFirst --> Converged["known valid log entries preserved"]
```

Snapshots und Full-State-Nachrichten sind Optimierungen. Sie duerfen keinen bekannten gueltigen Log-Eintrag loeschen, ueberschreiben oder als normative Recovery ersetzen.

## Spec-Bezuege

| Normative Quelle | Inhalt | Architekturrolle |
|---|---|---|
| `03-wot-sync/002-sync-protokoll.md` | Normative Sync-Flows, App-Start, Reconnect, lokale Writes, Pending, blocked-by-key, future-rotation, Snapshots | Sync State Machine, Pending Inbox, Log Catch-Up, Key Resolver |
| `03-wot-sync/003-transport-und-broker.md` | Broker Auth, per-device Inbox, ACK, sync-request/response, self-addressed delivery | Broker/Relay, ACK Policy, Transport |
| `03-wot-sync/005-gruppen.md` | Space Invite, Member Update, Key Rotation, Generation-Gaps | Key Resolver, Group/Membership Workflow |
| `03-wot-sync/006-personal-doc.md` | Personal Doc, Self-addressed Messages, Personal Doc vor Space Sync | Startup/Reconnect Flow, Key Store, Space Metadata |
| `CONFORMANCE.md` | pruefbare Anforderungen fuer `wot-sync@0.1` | Conformance Tests und Implementierungs-Checkliste |

## Implementierungsleitlinien

- Implementierungen duerfen Technologien frei waehlen, solange die Rollen und Abhaengigkeiten eingehalten werden.
- Broker duerfen Inhalte nicht als Autoritaetsanker interpretieren; autoritative Pruefung liegt beim Client.
- Transport kann WebSocket, QUIC, Bluetooth, Sneakernet oder P2P sein; Sync-Semantik bleibt gleich.
- Pending darf nicht volatil sein, wenn danach ACK gesendet wird.
- CRDT-Engine ist austauschbar und darf nicht ueber ACK, Key-Gaps oder Broker-Catch-Up entscheiden.
- Snapshot-/Vault-/Full-State-Mechanismen bleiben Optimierungen und muessen mit Log-Catch-Up kombiniert werden.
