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
