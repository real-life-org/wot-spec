# WoT Sync 009: Gruppen und Mitgliedschaft

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-16

## Zusammenfassung

Dieses Dokument spezifiziert wie Gruppen (Spaces) im Sync Layer funktionieren — Einladung, Mitgliedschaft, Rollen, Entfernung und die damit verbundenen kryptografischen Abläufe. Gruppen sind Teil der Sync-Infrastruktur, nicht anwendungsspezifisch — jede Local-First-App die verschlüsselte Zusammenarbeit braucht, kann diese Spezifikation nutzen.

## Referenzierte Dokumente

- [Sync 009: Verschlüsselung](005-verschluesselung.md) — Space-Schlüssel, ECIES, Schlüsselrotation
- [Sync 009: Transport und Broker](007-transport-und-broker.md) — Inbox, Message Envelope, Broker-Zuordnung

## Grundprinzip

Eine Gruppe (Space) ist ein verschlüsselter Raum für Zusammenarbeit. Alle Mitglieder teilen einen symmetrischen Schlüssel (Space Key, siehe [Sync 005](005-verschluesselung.md)) und können damit Daten lesen und schreiben.

```
Space = gemeinsamer Schlüssel + Mitgliederliste + Daten (CRDT)
```

Die Mitgliederliste ist Teil der Sync-Daten und wird wie alle anderen Änderungen über Append-only Logs synchronisiert (siehe [Sync 006](006-sync-protokoll.md)).

## Rollen

| Rolle | Einladen | Schreiben | Lesen | Entfernen |
|-------|----------|-----------|-------|-----------|
| **Admin** (`members[0]`) | Ja | Ja | Ja | Ja |
| **Member** | Ja | Ja | Ja | Nein |

Zwei Rollen, bewusst einfach:

- **Admin** — `members[0]` in der Mitgliederliste. Kann Mitglieder entfernen. Beim Erstellen eines Space ist der Ersteller automatisch Admin.
- **Member** — kann Daten lesen, schreiben und neue Mitglieder einladen. Kann niemanden entfernen.

Jeder darf einladen, nur der Admin darf entfernen. Das spiegelt eine Vertrauenskultur: wer eingeladen wurde, darf seinerseits einladen. Wer Missbrauch betreibt, wird vom Admin entfernt.

### Warum keine feineren Rollen

Feinere Rollen (Admin, Moderator, Read-Only) erzeugen Komplexität bei der Synchronisation — insbesondere bei konkurrierenden Aktionen (zwei Admins handeln gleichzeitig). Zwei Rollen decken den Großteil der Anwendungsfälle ab. Feinere Permissions können als Extension spezifiziert werden.

## Einladung

### Ablauf

```
Alice (Member oder Admin) lädt Bob ein:

1. Alice erstellt eine Einladungs-Nachricht:
   - Space-ID
   - Aktueller Space Key (Generation N)
   - Heim-Broker-URL(s) des Space
   - Alle bisherigen Space Keys (Generation 0..N-1) für Zugriff auf historische Daten
   
2. Alice verschlüsselt die Einladung via ECIES für Bobs Public Key
   (siehe Sync 005, Peer-to-Peer-Verschlüsselung)

3. Alice sendet die Einladung als Inbox-Nachricht an Bob
   (siehe Sync 007, Kanal 2: Inbox)

4. Bob empfängt, entschlüsselt und akzeptiert die Einladung

5. Bob verbindet sich mit dem Heim-Broker des Space

6. Bob synchronisiert die Daten (Catch-Up)
```

### Einladungs-Nachricht

Neuer Inbox-Nachrichtentyp `space-invite`, als JWS Compact (siehe [Sync 009](007-transport-und-broker.md#message-envelope)):

**JWS-Payload:**

```json
{
  "v": 1,
  "id": "uuid",
  "type": "space-invite",
  "fromDid": "did:key:z6Mk...alice",
  "toDid": "did:key:z6Mk...bob",
  "createdAt": "2026-04-16T10:00:00Z",
  "payload": "<ECIES-verschlüsselt: { spaceId, brokerUrls, keys }>"
}
```

Die Payload enthält (nach Entschlüsselung):

```json
{
  "spaceId": "uuid",
  "brokerUrls": ["wss://broker.example.com"],
  "currentKeyGeneration": 3,
  "keys": [
    { "generation": 0, "key": "<base64url>" },
    { "generation": 1, "key": "<base64url>" },
    { "generation": 2, "key": "<base64url>" },
    { "generation": 3, "key": "<base64url>" }
  ]
}
```

Alle bisherigen Schlüssel werden mitgegeben, damit Bob auch historische Daten entschlüsseln kann. Der Schlüssel der höchsten Generation ist der aktuelle Schreibschlüssel.

### Annahme und Ablehnung

Bob kann die Einladung annehmen oder ablehnen. Bei Annahme:
- Bob speichert den Space Key lokal
- Bob verbindet sich mit dem Heim-Broker
- Bob erscheint als neues Mitglied

Bei Ablehnung passiert nichts — Bob verwirft die Nachricht. Alice erfährt nicht direkt ob Bob angenommen hat (sie sieht es daran, ob Bob im Space auftaucht).

## Mitgliederliste

Die Mitgliederliste wird als Teil der Sync-Daten gepflegt:

```json
{
  "members": {
    "did:key:z6Mk...alice": { "role": "creator", "joinedAt": "2026-04-10T..." },
    "did:key:z6Mk...bob":   { "role": "member",  "joinedAt": "2026-04-16T..." },
    "did:key:z6Mk...carol": { "role": "member",  "joinedAt": "2026-04-16T..." }
  }
}
```

Änderungen an der Mitgliederliste sind reguläre CRDT-Operationen und werden wie alle Daten über den Append-only Log synchronisiert.

## Entfernung

### Ablauf

```
Admin entfernt Bob:

1. Admin schreibt eine Entfernungs-Operation in den Log
   (Bobs Eintrag wird aus der Mitgliederliste entfernt)

2. Admin generiert einen neuen Space Key (Generation N+1)
   (siehe Sync 005, Schlüsselrotation)

3. Admin verteilt den neuen Key via ECIES an alle 
   verbleibenden Mitglieder (Inbox-Nachricht)

4. Neue Daten werden mit dem neuen Key verschlüsselt

5. Bob hat den neuen Key nicht → kann zukünftige Daten nicht lesen
```

### Key-Rotation Nachricht

Neuer Inbox-Nachrichtentyp `key-rotation`, als JWS Compact:

**JWS-Payload:**

```json
{
  "v": 1,
  "id": "uuid",
  "type": "key-rotation",
  "fromDid": "did:key:z6Mk...alice",
  "toDid": "did:key:z6Mk...carol",
  "createdAt": "2026-04-16T10:00:00Z",
  "payload": "<ECIES-verschlüsselt: { spaceId, generation, key }>"
}
```

Der Admin sendet eine `key-rotation` Nachricht an **jedes** verbleibende Mitglied einzeln — jede Nachricht individuell ECIES-verschlüsselt.

### Forward Secrecy

Alte Daten bleiben mit dem alten Schlüssel lesbar (für Mitglieder die damals Zugriff hatten). Neue Daten sind für entfernte Mitglieder unlesbar. Das ist **kein perfekter Forward Secrecy** — Bob könnte alte Daten, die er bereits heruntergeladen hat, weiterhin lokal lesen. Aber er kann keine zukünftigen Daten entschlüsseln und vom Broker werden ihm keine neuen Daten ausgeliefert.

## Concurrent-Verhalten

### Gleichzeitige Einladungen

Zwei Member laden gleichzeitig neue Leute ein → kein Konflikt. Beide Einladungen werden unabhängig verarbeitet, die Mitgliederliste konvergiert via CRDT-Merge.

### Einladung während Entfernung

Alice (Admin) entfernt Bob, während Carol (Member) Dave einlädt:
- Bobs Entfernung + Key-Rotation gewinnt
- Dave's Einladung enthält den alten Key (Generation N)
- Dave braucht den neuen Key (Generation N+1)
- Admin muss Dave den neuen Key nachliefern (erkennt beim nächsten Sync dass Dave mit einem alten Key arbeitet)

Das ist ein Edge Case der in der Implementierung behandelt werden muss: der Admin prüft nach einer Key-Rotation ob neue Members mit veralteten Keys existieren und sendet ihnen den aktuellen Key.

### Gleichzeitige Entfernungen

Nur der Admin kann entfernen. Da es nur einen Admin gibt und dieser ein einzelner User mit eventuell mehreren Geräten ist, koordinieren sich die Geräte über den persönlichen Log. In der Praxis tritt dieser Fall selten auf.

## Neue Nachrichtentypen

Diese Spezifikation definiert zwei neue Nachrichtentypen für das Message Envelope (siehe [Sync 007](007-transport-und-broker.md)):

| Type | Kanal | Beschreibung |
|------|-------|-------------|
| `space-invite` | Inbox | Einladung in einen Space (Space Key + Broker-URLs) |
| `key-rotation` | Inbox | Neuer Space Key nach Member-Entfernung |

## Zusammenspiel mit dem Broker

### Einladung und Broker-Zuordnung

Bei einer Einladung wird die Heim-Broker-URL des Space mitgeschickt. Der eingeladene User verbindet sich automatisch mit diesem Broker für diesen Space (siehe [Sync 009](007-transport-und-broker.md#space-broker-heim-broker)).

### Berechtigung am Broker

Der Broker liefert nur Daten an Peers die in der Mitgliederliste stehen. Nach einer Entfernung:
- Der Admin informiert den Broker über die Entfernung
- Der Broker verweigert dem entfernten Mitglied weitere Sync-Operationen
- Selbst wenn Bob den Broker direkt kontaktiert, bekommt er keine neuen Daten

### Offline-Entfernung

Wenn der Admin offline ist während er Bob entfernt:
- Die Entfernungs-Operation wird lokal im Log gespeichert
- Beim nächsten Reconnect synchronisiert der Log zum Broker
- Der Broker aktualisiert seine Berechtigungsliste
- Zwischen Entfernung und Sync könnte Bob theoretisch noch Daten empfangen — die sind aber noch mit dem alten Key verschlüsselt, also kein Sicherheitsrisiko

## Sicherheitsmodell

### Grundprinzip: Vertrauen innerhalb der Gruppe

Innerhalb einer Gruppe herrscht Vertrauen. Jedes Mitglied mit dem Space Key darf alles lesen und alles schreiben. Es gibt keine Feldebenen-Berechtigungen — der CRDT-Merge unterscheidet nicht nach Autor. Das ist eine bewusste Entscheidung: unsere Gruppen bestehen aus echten Beziehungen (Familie, Freundeskreis, Community-Projekte).

### Zwei Regeln

1. **Alle Members dürfen alles lesen und schreiben.** Ein Key, ein CRDT, keine Feldrechte. Wer den Space Key hat, ist vollwertiges Mitglied.
2. **Nur der Admin (`members[0]`) darf Members entfernen.** Entfernungs-Nachrichten werden empfängerseitig geprüft — nur Nachrichten von `members[0]` werden akzeptiert. Ein Member der versucht andere zu entfernen, wird von allen Clients abgelehnt.

### Admin-Austritt

Der Admin kann freiwillig austreten. In dem Fall rückt `members[1]` auf Position 0 und wird neuer Admin. Die Admin-Rolle ist implizit an die Position in der Mitgliederliste gebunden — kein separates Feld nötig.

### Was geschützt ist

- **Vertraulichkeit nach außen:** Alle Daten sind mit dem Space Key verschlüsselt (E2EE). Ohne Key kein Lesen, kein Schreiben.
- **Membership-Integrität:** Entfernungs-Nachrichten werden empfängerseitig geprüft — nur der Admin kann entfernen.

### Was bewusst NICHT eingeschränkt ist

- **CRDT-Schreibrechte:** Jedes Mitglied kann beliebige Daten schreiben. Das ist gewollt — innerhalb der Gruppe herrscht Vertrauen.
- **Einladungen:** Jedes Mitglied darf einladen. Wer eingeladen wurde, darf seinerseits einladen.

### Zukünftiger Upgrade-Pfad

Für feinere Permissions (Read-Only Members, Feld-Ebenen-Rechte, delegierbare Rollen) können in Zukunft **Capability-Chains** eingeführt werden (z.B. Keyhive/Beelay-Modell). Dabei signiert der Admin Capabilities die er an Members delegiert — jede CRDT-Operation muss dann eine gültige Signaturkette vorweisen. Das ist ein signifikanter Architektur-Schritt der erst sinnvoll wird wenn die zugrundeliegenden Frameworks (Keyhive, Beelay) produktionsreif sind.

## Zu klären

- **Mehrere Admins:** Brauchen wir mehr als einen Admin pro Space? Wenn ja: wie wird Key-Rotation bei gleichzeitigen Admin-Aktionen koordiniert?
