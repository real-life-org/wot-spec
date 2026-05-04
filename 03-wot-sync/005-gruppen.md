# WoT Sync 005: Gruppen und Mitgliedschaft

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-22
- **Scope:** Spaces, Membership, Einladungen, Rollen und Key-Rotation
- **Depends on:** Identity 001, Sync 001, Sync 002, Sync 003
- **Conformance profile:** `wot-sync@0.1`

## Zusammenfassung

Dieses Dokument spezifiziert wie Gruppen (Spaces) im Sync Layer funktionieren — Einladung, Mitgliedschaft, Rollen, Entfernung und die damit verbundenen kryptografischen Abläufe. Gruppen sind Teil der Sync-Infrastruktur. Die Konzepte (symmetrische Content Keys, Capability-basierte Broker-Autorisierung, Key-Rotation bei Member-Entfernung) sind generisch — aber die konkrete Spezifikation setzt WoT-Identitäten (DID, Ed25519) und den WoT-Sync-Layer voraus.

## Referenzierte Dokumente

- [Identity 001: Identität](../01-wot-identity/001-identitaet-und-schluesselableitung.md) — Schlüsselableitung, HKDF-Pfade
- [Sync 001: Verschlüsselung](001-verschluesselung.md) — Space-Schlüssel, ECIES, Space Capability Key Pair
- [Sync 003: Transport und Broker](003-transport-und-broker.md) — Inbox, Message Envelope, Capabilities

## Grundprinzip

Ein Space ist ein verschlüsseltes CRDT-Dokument mit Mitgliederliste, Space Content Key, Space Capability Key Pair und optional mehreren Admins. Die Schlüssel sind normativ in [Sync 001](001-verschluesselung.md#gruppen-verschlüsselung-spaces) definiert; Broker-Capabilities sind in [Sync 003](003-transport-und-broker.md#autorisierung-capabilities) definiert.

Die Mitgliederliste ist Teil der Sync-Daten und wird wie alle anderen Änderungen über Append-only Logs synchronisiert (siehe [Sync 002](002-sync-protokoll.md)). Bei Member-Entfernung werden Space Content Key und Space Capability Key Pair gemeinsam rotiert. Admin Keys bleiben stabil, außer bei Admin-Wechsel.

### Admin Key Ableitung

Admin Keys werden pro Space aus dem 64-Byte BIP39-Seed abgeleitet; die normative Ableitung steht in [Sync 001](001-verschluesselung.md#admin-key-abgeleitet). Der Broker kennt nur die abgeleitete `adminDid`, nicht die Haupt-DID des Admins.

## Rollen

| Rolle | Einladen | Schreiben | Lesen | Rotieren / Entfernen |
|-------|----------|-----------|-------|---------------------|
| **Admin** | Ja | Ja | Ja | Ja |
| **Member** | Ja | Ja | Ja | Nein |

- **Admin** — kann den Space Content Key rotieren und damit Members ausschließen. Beim Erstellen eines Space wird der Ersteller automatisch erster Admin. Mehrere Admins sind möglich.
- **Member** — kann Daten lesen, schreiben und neue Mitglieder einladen. Kann niemanden entfernen.

Jeder Member darf einladen; nur Admins dürfen rotieren und damit Members entfernen.

Jeder Space DARF mehrere Admins haben. Die abgeleiteten Admin-DIDs werden beim Broker registriert; jeder registrierte Admin DARF Rotationen auslösen. Feinere Permissions sind nicht Teil von Phase 1.

## Space-Erstellung

Beim Erstellen eines Spaces erzeugt der Client einen Space Content Key, ein Space Capability Key Pair und die initiale Mitgliederliste. Der Ersteller leitet seinen Admin Key ab und registriert beim Broker `spaceId`, `spaceCapabilityVerificationKey` und seine abgeleitete `adminDid`.

## Einladung

### Invitee-Key-Discovery (MUSS)

Vor dem Erstellen einer Space-Einladung MUSS der Einladende den X25519 Encryption Public Key des Eingeladenen kennen. Erlaubte Quellen sind:

1. ein zuvor gescannter QR-Code (`enc`, siehe [Trust 002](../02-wot-trust/002-verifikation.md)),
2. ein lokal gecachter Contact-Key aus einer frueheren Begegnung,
3. das DID-Dokument des Eingeladenen (`keyAgreement`, siehe [Identity 003](../01-wot-identity/003-did-resolution.md) und [Sync 004](004-discovery.md)).

Wenn kein Encryption Key aufloesbar ist, MUSS die Einladung abbrechen. Ein Client DARF in diesem Fall keine Space Content Keys unverschluesselt oder an eine falsche DID senden.

### Ablauf

Einladungen werden als ECIES-verschlüsselte Inbox-Nachrichten transportiert. Jeder Member DARF eine Capability mit dem `spaceCapabilitySigningKey` für den Eingeladenen signieren; eine Admin-Signatur ist für Einladungen nicht erforderlich.

Eine Einladung MUSS Space-ID, Broker-URL(s), aktuelle und historische Space Content Keys, den Space Capability Signing Key, Admin-DIDs und eine Capability für den Eingeladenen enthalten.

### Einladungs-Nachricht

Inbox-Nachrichtentyp `space-invite`, verschlüsselt mit ECIES:

```json
{
  "id": "uuid",
  "typ": "application/didcomm-plain+json",
  "type": "https://web-of-trust.de/protocols/space-invite/1.0",
  "from": "did:key:z6Mk...alice",
  "to": ["did:key:z6Mk...bob"],
  "created_time": 1776945600,
  "body": {
    "spaceId": "uuid",
    "brokerUrls": ["wss://broker.example.com"],
    "currentKeyGeneration": 3,
    "spaceContentKeys": [
      { "generation": 0, "key": "<base64url>" },
      { "generation": 1, "key": "<base64url>" },
      { "generation": 2, "key": "<base64url>" },
      { "generation": 3, "key": "<base64url>" }
    ],
    "spaceCapabilitySigningKey": "<base64url>",
    "adminDids": ["did:key:z6Mk...admin-alice-derived"],
    "capability": "<JWS — Capability signiert mit spaceCapabilitySigningKey>"
  }
}
```

### Einladungs-Invarianten (MUSS)

- `currentKeyGeneration` MUSS der hoechsten Generation in `spaceContentKeys` entsprechen.
- Die `capability.generation` MUSS `currentKeyGeneration` entsprechen.
- Die `capability.audience` MUSS der DID des Eingeladenen entsprechen.
- `spaceContentKeys` MUSS alle Generationen enthalten, die der Eingeladene zum Entschluesseln der aktuell verfuegbaren Space-History benoetigt. Implementierungen duerfen alte Generationen weglassen, wenn sie dem Eingeladenen nur Zugriff ab einem spaeteren Snapshot geben; dann MUSS dieser Snapshot mit `currentKeyGeneration` entschluesselbar sein.
- Der `spaceCapabilitySigningKey` DARF nur zur Ausstellung weiterer Broker-Capabilities verwendet werden, nicht zur Autoren-Authentifizierung.

### Annahme und Ablehnung

Bei Annahme speichert der Empfänger Space Content Key, Space Capability Signing Key und Capability lokal, verbindet sich mit dem Heim-Broker und synchronisiert das Space-Dokument. Bei Ablehnung verwirft er die Nachricht.

## Mitgliederliste

Die Mitgliederliste wird als Teil der Sync-Daten gepflegt:

```json
{
  "members": [
    "did:key:z6Mk...alice",
    "did:key:z6Mk...bob",
    "did:key:z6Mk...carol"
  ],
  "admins": [
    "did:key:z6Mk...alice"
  ]
}
```

- `members` enthält die Haupt-DIDs aller Mitglieder
- `admins` enthält die Haupt-DIDs der Admins (Teilmenge von `members`)
- Die Admin-DIDs hier sind die **Haupt-DIDs** (für Members sichtbar), nicht die abgeleiteten Admin-Keys (die nur beim Broker bekannt sind)

Änderungen an der Mitgliederliste sind reguläre CRDT-Operationen.

## Member-Update Nachricht

`member-update/1.0` informiert bestehende oder entfernte Members ueber eine Mitgliedschaftsaenderung. Die authoritative Mitgliederliste bleibt das verschluesselte Space-Dokument; `member-update` ist ein Zustell- und UX-Signal, damit Clients sofort reagieren koennen.

Inbox-Nachrichtentyp `member-update`, verschluesselt mit ECIES und mit innerem JWS signiert:

```json
{
  "id": "uuid",
  "typ": "application/didcomm-plain+json",
  "type": "https://web-of-trust.de/protocols/member-update/1.0",
  "from": "did:key:z6Mk...alice",
  "to": ["did:key:z6Mk...bob"],
  "created_time": 1776945600,
  "body": {
    "spaceId": "uuid",
    "action": "added",
    "memberDid": "did:key:z6Mk...bob",
    "effectiveKeyGeneration": 3
  }
}
```

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `spaceId` | UUID | Ja | Betroffener Space |
| `action` | `added` \| `removed` | Ja | Art der Aenderung |
| `memberDid` | DID | Ja | Betroffener Member |
| `effectiveKeyGeneration` | Integer | Ja | Key-Generation, ab der diese Aenderung wirksam ist |
| `reason` | String | Nein | Optionale menschenlesbare Begruendung |

Empfaenger MUESSEN `member-update` gegen den naechsten Space-Sync verifizieren. Die kanonische Mitgliederliste bleibt das signierte und synchronisierte Space-Dokument. `member-update` allein DARF keine dauerhafte Membership-State-Aenderung erzwingen.

### Member-Update Verarbeitung (MUSS)

`member-update` ist zugleich ein Zustellsignal und ein lokales Pending-Signal. Es ist keine Autoritaet fuer den kanonischen Membership-State. Ein Client MUSS die Nachricht nach erfolgreicher Entschluesselung, JWS-Pruefung, Replay-Pruefung und durablem Pending-Speicher ACKen; die ACK bestaetigt nur die lokale Annahme des Signals, nicht die kanonische Membership-Aenderung.

Ein Client MUSS `member-update` anhand von `(spaceId, action, memberDid, effectiveKeyGeneration)` idempotent verarbeiten. Exakte Duplikate MUESSEN ohne zusaetzliche UI-, Sync- oder State-Transitions ignoriert werden, nachdem die erste Nachricht durable verarbeitet wurde.

Vor der Bestaetigung durch den naechsten Space-Sync gelten diese Regeln:

- Bei `action="added"` fuer die lokale DID DARF der Client den Space als "Beitritt ausstehend" oder vergleichbar anzeigen, lokale Keys und Capabilities aus einer passenden `space-invite` verwenden und MUSS einen Space-Catch-Up per `sync-request` ausloesen. Er DARF Schreibzugriff erst als bestaetigte Mitgliedschaft behandeln, wenn die kanonische Mitgliederliste die lokale DID enthaelt.
- Bei `action="added"` fuer eine andere DID DARF der Client UIs und lokale Caches als ausstehende Hinzufuegung aktualisieren, MUSS die kanonische Mitgliederliste aber unveraendert lassen.
- Bei `action="removed"` fuer die lokale DID SOLLTE der Client den Space als "Entfernung ausstehend" oder vergleichbar markieren und DARF lokale Schreibaktionen sofort sperren oder den Space lokal ausblenden. Er DARF lokalen State erst nach kanonischer Bestaetigung oder bestaetigter Broker-Rotation dauerhaft als ausgetreten behandeln.
- Bei `action="removed"` fuer eine andere DID DARF der Client UIs und lokale Caches als ausstehende Entfernung aktualisieren, MUSS die kanonische Mitgliederliste aber unveraendert lassen.

Nach dem naechsten Space-Sync MUSS der Client Pending-Updates gegen die kanonische Mitgliederliste aufloesen:

- Wenn `action="added"` und die kanonische Mitgliederliste `memberDid` enthaelt, MUSS der Client die Hinzufuegung als bestaetigt behandeln.
- Wenn `action="removed"` und die kanonische Mitgliederliste `memberDid` nicht enthaelt, MUSS der Client die Entfernung als bestaetigt behandeln.
- Wenn die kanonische Mitgliederliste dem Pending-Update widerspricht, MUSS der Client das Pending-Update verwerfen und den kanonischen Membership-State beibehalten.

`effectiveKeyGeneration` bindet das Pending-Signal an die Space-Key-Generation, ab der die Aenderung erwartet wird:

- Wenn fuer `spaceId` noch keine lokal bekannte Space-Key-Generation existiert, MUSS der Client die hoechste durable Generation aus einer passenden akzeptierten `space-invite` als lokale Vergleichsgeneration verwenden. Ohne lokale Space-Keys DARF der Client das Update nur als unverifiziertes Pending-Signal speichern und MUSS zuerst Einladung oder Key-Material nachladen.
- Wenn `effectiveKeyGeneration` kleiner als die lokal bekannte Space-Key-Generation ist, MUSS der Client das Update als veraltet behandeln und DARF daraus keine neue Pending-State-Aenderung ableiten. Ein bereits bestaetigter kanonischer State bleibt unveraendert.
- Wenn `effectiveKeyGeneration` gleich der lokal bekannten Space-Key-Generation oder exakt `local+1` ist, DARF der Client das Pending-Update nach den obigen Regeln verarbeiten und MUSS einen Space-Catch-Up ausloesen.
- Wenn `effectiveKeyGeneration` groesser als `local+1` ist, MUSS der Client das Update als zukuenftiges Pending-Update durabel puffern, fehlende Rotationen oder Keys gemaess [Sync 002 Key-Rotation und Generation-Gaps](002-sync-protokoll.md#key-rotation-und-generation-gaps) nachladen und DARF das Update nicht als bestaetigt behandeln, bevor die Generation-Luecke geschlossen und der Space-Sync erfolgt ist.

Ein `member-update` kann konkurrierende oder widerspruechliche Signale transportieren. Solche Konflikte werden nicht durch Inbox-Reihenfolge entschieden; die kanonische Mitgliederliste nach Log-Catch-Up MUSS entscheiden.

## Neue Admins hinzufügen

Ein Admin DARF einen bestehenden Member zum Admin befördern. Dafür wird die Admin-Liste im CRDT um die Haupt-DID des neuen Admins erweitert und dessen abgeleitete Admin-DID per `admin-add` beim Broker registriert. `admin-add` MUSS mit einem bestehenden Admin Key signiert sein.

## Key-Rotation (Member-Entfernung)

Bei Member-Entfernung werden Space Content Key **und** Space Capability Key Pair gemeinsam rotiert — damit werden auch alte Capabilities ungültig.

### Ablauf

Bei Entfernung eines Members MUSS ein Admin:

1. die Mitgliederliste per CRDT-Operation aktualisieren,
2. einen neuen Space Content Key und ein neues Space Capability Key Pair erzeugen,
3. den neuen `spaceCapabilityVerificationKey` per signierter `space-rotate`-Nachricht beim Broker registrieren,
4. neuen Space Content Key, neuen Space Capability Signing Key und neue Capability via ECIES an alle verbleibenden Members verteilen.

Neue Daten werden mit der neuen Generation verschlüsselt. Der entfernte Member besitzt weder neuen Content Key noch gültige Capability.

Der Admin MUSS zusaetzlich `member-update` Nachrichten senden:

- an den entfernten Member mit `action="removed"` und `effectiveKeyGeneration` der neuen Generation, damit der Client den Space lokal als Entfernung ausstehend markieren oder sperren kann;
- an die verbleibenden Members mit `action="removed"`, damit UIs und lokale Caches die Entfernung sofort anzeigen koennen.

Verbleibende Members MUESSEN ausserdem eine `key-rotation` Nachricht mit dem neuen Content Key und der neuen Capability erhalten. Der entfernte Member DARF diese `key-rotation` Nachricht nicht erhalten.

### Operationelle Reihenfolge (MUSS)

Damit offline Devices deterministisch aufholen koennen, MUSS eine Member-Entfernung als geordneter Sync-Flow behandelt werden:

1. Der Admin erzeugt die Remove-CRDT-Operation und den neuen Key-Material-Satz lokal und persistiert beides gemaess [Sync 002 Lokaler Schreibvorgang](002-sync-protokoll.md#lokaler-schreibvorgang).
2. Der Admin registriert die neue Capability-Key-Generation beim Broker (`space-rotate`) oder legt die Operation in eine retrybare Outbox, falls der Broker offline ist.
3. Der Admin sendet `key-rotation` Inbox-Nachrichten an alle verbleibenden Members und `member-update` Nachrichten an verbleibende sowie entfernte Members. Diese Nachrichten MUESSEN pro Device zugestellt und ACKt werden (siehe [Sync 003 Store-and-Forward pro Device](003-transport-und-broker.md#store-and-forward-pro-device)).
4. Verbleibende Members speichern die neue Generation durabel, bevor sie `key-rotation` ACKen. Danach MUESSEN sie einen Space-`sync-request` ausloesen und blockierte Log-Eintraege dieser Generation erneut verarbeiten.
5. Entfernte Members duerfen `member-update(action="removed")` erst als dauerhaften lokalen Austritt behandeln, wenn der naechste Space-Sync die kanonische Mitgliederliste ohne diese DID bestaetigt oder die Broker-Rotation fuer `effectiveKeyGeneration` die bisherige Capability mit `CAPABILITY_GENERATION_STALE` ablehnt. Bis dahin SOLLTE die UI den Space als "Entfernung ausstehend" oder vergleichbar markieren. Es gibt keinen normativen Timeout, weil Offline-Zeit keine neue Protokoll-Autoritaet erzeugt; bei App-Start oder Reconnect MUSS der Client den Bestaetigungs-Sync erneut versuchen. Implementierungen DUERFEN den Space lokal ausblenden oder Schreibaktionen sperren, DUERFEN lokalen State aber nicht ohne diese Bestaetigung als kanonisch geloescht behandeln.

Zeitbasierte Snapshot- oder Vault-Retries duerfen diesen Ablauf beschleunigen, sind aber nicht normativ. Normative Konvergenz entsteht durch Inbox-Zustellung, Key-/Generation-Gap-Regeln und Log-Catch-Up gemaess [Sync 002 Key-Rotation und Generation-Gaps](002-sync-protokoll.md#key-rotation-und-generation-gaps).

### Key-Rotation Nachricht

Inbox-Nachrichtentyp `key-rotation`, verschlüsselt mit ECIES:

```json
{
  "id": "uuid",
  "typ": "application/didcomm-plain+json",
  "type": "https://web-of-trust.de/protocols/key-rotation/1.0",
  "from": "did:key:z6Mk...alice",
  "to": ["did:key:z6Mk...carol"],
  "created_time": 1776945600,
  "body": {
    "spaceId": "uuid",
    "generation": 4,
    "spaceContentKey": "<base64url>",
    "spaceCapabilitySigningKey": "<base64url>",
    "capability": "<JWS — neue Capability signiert mit neuem spaceCapabilitySigningKey>"
  }
}
```

Der Admin sendet eine `key-rotation` Nachricht an **jedes** verbleibende Mitglied einzeln.

Alte Daten bleiben mit alten Space Content Keys lesbar. Rotation schuetzt nur zukuenftige Daten und zukuenftigen Broker-Zugriff.

### Key-Rotation Invarianten (MUSS)

- `generation` MUSS exakt die vorherige Space-Key-Generation plus eins sein.
- Die enthaltene `capability.generation` MUSS `generation` entsprechen.
- Der Broker MUSS nach erfolgreicher `space-rotate` Verarbeitung alte Capabilities ablehnen (`CAPABILITY_GENERATION_STALE`).
- Clients MUESSEN neue Log-Eintraege nach Rotation mit der neuen `keyGeneration` schreiben.
- Clients MUESSEN alte Log-Eintraege weiter mit der jeweils im Log-Eintrag angegebenen historischen `keyGeneration` entschluesseln.

Clients MUESSEN Key-Rotations anhand ihrer lokal bekannten Space-Key-Generation anwenden:

- Wenn `generation` der lokal bekannten Generation plus eins entspricht, DARF die Rotation angewendet werden.
- Wenn `generation` kleiner oder gleich der lokal bekannten Generation ist, MUSS die Rotation als doppelt oder veraltet ignoriert werden.
- Wenn `generation` groesser als die lokal bekannte Generation plus eins ist, MUSS der Client die Rotation als zukuenftige Rotation behandeln. Er DARF sie puffern, MUSS die in [Sync 002](002-sync-protokoll.md#key-rotation-und-generation-gaps) definierten Catch-Up-Quellen fuer fehlende Rotationen oder Keys nutzen und DARF die zukuenftige Rotation nicht anwenden, bevor die Luecke geschlossen ist.

Die detaillierte Verarbeitung von `blocked-by-key` Log-Eintraegen, durabel gepufferten `future-rotation` Nachrichten und ACK-Zeitpunkten ist in [Sync 002 Normative Sync-Flows](002-sync-protokoll.md#normative-sync-flows) definiert.

## Concurrent-Verhalten

Gleichzeitige Einladungen sind unabhängige CRDT-Operationen. Wenn Einladung und Entfernung konkurrieren, gewinnt die höhere Key-Generation: Members mit veralteten Keys müssen eine neue Capability und die aktuellen Space-Schlüssel erhalten. Bei gleichzeitigen Rotationen akzeptiert der Broker nur die erste gültige `space-rotate`-Nachricht für die neue Generation; spätere Nachrichten mit veralteter Generation werden abgelehnt.

## Neue Nachrichtentypen

| Type | Kanal | Beschreibung |
|------|-------|-------------|
| `space-invite` | Inbox | Einladung in einen Space (Content Key + Capability Signing Key + Capability) |
| `key-rotation` | Inbox | Neuer Content Key + Capability Signing Key nach Member-Entfernung |
| `admin-add` | Broker | Neue Admin-DID beim Broker registrieren (signiert von bestehendem Admin) |
| `admin-remove` | Broker | Admin-DID entfernen (signiert von anderem Admin) |
| `space-rotate` | Broker | Rotation des Space Capability Verification Keys (signiert von einem Admin) |

## Broker-Interaktion

### Initiale Space-Registrierung

Wenn ein User einen Space erstellt, registriert er ihn beim Broker:

```json
{
  "type": "space-register",
  "spaceId": "uuid",
  "spaceCapabilityVerificationKey": "<base64url>",
  "adminDids": ["did:key:z6Mk...admin-derived"]
}
```

Signiert mit dem (noch einzigen) Admin Key. Der Broker akzeptiert die Registrierung, speichert Space-ID, Space Capability Verification Key und Admin-DIDs. Später können Admins hinzugefügt, entfernt oder das Capability Key Pair rotiert werden (jeweils signiert von einem eingetragenen Admin).

### Capability-Prüfung

Capability-Prüfung ist in [Sync 003](003-transport-und-broker.md#autorisierung-capabilities) spezifiziert.

### Offline-Entfernung

Wenn ein Admin offline entfernt, werden Remove-Operation und Rotation lokal vorbereitet und beim nächsten Broker-Reconnect synchronisiert. Erst nach erfolgreicher `space-rotate`-Verarbeitung sind alte Capabilities beim Broker ungültig.

## Sicherheitsmodell

1. **Alle Members dürfen alles lesen und schreiben.** Ein Space Content Key, ein CRDT, keine Feldrechte.
2. **Alle Members dürfen Capabilities für neue Members signieren** (mit dem Space Capability Signing Key). Einladungen sind nicht auf Admins beschränkt.
3. **Nur Admins dürfen rotieren (= Members ausschließen).** Rotation-Nachrichten werden am Broker geprüft — nur Nachrichten signiert mit einem registrierten Admin Key werden akzeptiert.

### Admin-Austritt

Ein Admin DARF aus dem Space austreten oder nur die Admin-Rolle abgeben. Das geschieht durch eine `admin-remove`-Nachricht, signiert mit einem bestehenden Admin Key. Falls der ausscheidende Admin der einzige war, SOLLTE vorher ein neuer Admin ernannt werden.

### Space ohne Admin

Falls alle Admins weg sind (z.B. alle haben ausgetreten oder verloren ihre Keys), ist der Space in seiner aktuellen Zusammensetzung eingefroren:
- Members können weiter lesen/schreiben
- Keine Rotation mehr möglich → keine Member-Entfernung mehr möglich
- Neue Einladungen sind weiter möglich (Member-Privileg)

Dies ist ein akzeptierter Degraded Mode.

### Privacy gegenüber dem Broker

Durch abgeleitete Admin-Keys erfährt der Broker **nicht**:
- Die Haupt-Identitäten der Admins
- Welche User über mehrere Spaces Admins sind
- Die Mitgliederliste (im verschlüsselten CRDT)

Der Broker sieht nur:
- Space-ID
- Space Capability Verification Key
- Abgeleitete Admin-DIDs (pro Space eindeutig, nicht verknüpfbar)
- Capability-Signaturen (bestätigen Zugriff, offenbaren aber nicht wer signiert hat)

### Was bewusst NICHT eingeschränkt ist

- **CRDT-Schreibrechte:** Jedes Mitglied kann beliebige Daten schreiben.
- **Einladungen:** Jedes Mitglied darf einladen.

Feinere Permissions und Capability-Chains sind nicht Teil von Phase 1.
