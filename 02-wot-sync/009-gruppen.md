# WoT Sync 009: Gruppen und Mitgliedschaft

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-22

## Zusammenfassung

Dieses Dokument spezifiziert wie Gruppen (Spaces) im Sync Layer funktionieren — Einladung, Mitgliedschaft, Rollen, Entfernung und die damit verbundenen kryptografischen Abläufe. Gruppen sind Teil der Sync-Infrastruktur. Die Konzepte (symmetrische Content Keys, Capability-basierte Broker-Autorisierung, Key-Rotation bei Member-Entfernung) sind generisch — aber die konkrete Spezifikation setzt WoT-Identitäten (DID, Ed25519) und den WoT-Sync-Layer voraus.

## Referenzierte Dokumente

- [Core 001: Identität](../01-wot-core/001-identitaet-und-schluesselableitung.md) — Schlüsselableitung, HKDF-Pfade
- [Sync 005: Verschlüsselung](005-verschluesselung.md) — Space-Schlüssel, ECIES, Space-Keypair
- [Sync 007: Transport und Broker](007-transport-und-broker.md) — Inbox, Message Envelope, Capabilities

## Grundprinzip

Eine Gruppe (Space) ist ein verschlüsselter Raum für Zusammenarbeit. Alle Mitglieder teilen einen **symmetrischen Space Key** (für Datenverschlüsselung) und ein **Space-Keypair** (für Capability-Signaturen am Broker).

```
Space = Space Key (sym) + Space Keypair (asym) + Admin(s) + Mitgliederliste + Daten (CRDT)
```

Die Mitgliederliste ist Teil der Sync-Daten und wird wie alle anderen Änderungen über Append-only Logs synchronisiert (siehe [Sync 006](006-sync-protokoll.md)).

## Space-Schlüssel

Jeder Space hat drei Arten von Schlüsseln (normativ definiert in [Sync 005](005-verschluesselung.md#gruppen-verschlüsselung-spaces)):

| Schlüssel | Kurzname | Typ | Zweck | Wer hat ihn |
|---|---|---|---|---|
| **Space Content Key** | `spaceContentKey` | Symmetrisch (AES-256) | Verschlüsselung von Space-Daten und Log-Einträgen | Alle Members |
| **Space Capability Signing Key** | `spaceCapabilitySigningKey` | Asymmetrisch (Ed25519) | Signiert Capabilities für Broker-Zugriff | Alle Members |
| **Admin Key(s)** | `adminKey` | Asymmetrisch (Ed25519, abgeleitet) | Autorisiert Rotation beim Broker | Admin(s) |

Der Broker kennt nur die Public Keys: `spaceCapabilityVerificationKey` und `adminDid(s)`.

Bei Key-Rotation (Member-Entfernung) werden **Space Content Key und Space Capability Key Pair gemeinsam rotiert**. Admin Keys bleiben stabil (nur bei Admin-Wechsel werden sie aktualisiert).

### Admin Key Ableitung

Admin Keys werden pro Space aus dem 64-Byte BIP39-Seed des Users abgeleitet. Die normative Ableitung ist in [Sync 005](005-verschluesselung.md#admin-key-abgeleitet) spezifiziert:

```
HKDF-SHA256(BIP39-Seed, salt=leer, info="wot/space-admin/<canonical-lowercase-uuid>/v1", 32 Bytes)
  → Ed25519 Keypair
  → did:key-Enkodierung des Public Keys
```

Die `<canonical-lowercase-uuid>` ist die Space-ID in kanonischer Form (36-Zeichen lowercase-hex mit Bindestrichen).

Der Admin Key ist eine **space-spezifische Identität** — er hat keine direkte Verbindung zur Haupt-DID des Admins. Das bewahrt Privacy gegenüber dem Broker: der Broker sieht nur die Admin-DID für diesen Space, kann sie aber nicht mit der Haupt-Identität verknüpfen oder Admin-Rollen über mehrere Spaces korrelieren.

Members kennen die Haupt-DID des Admins aus der Mitgliederliste (im verschlüsselten CRDT), die für den Broker nicht sichtbar ist.

## Rollen

| Rolle | Einladen | Schreiben | Lesen | Rotieren / Entfernen |
|-------|----------|-----------|-------|---------------------|
| **Admin** | Ja | Ja | Ja | Ja |
| **Member** | Ja | Ja | Ja | Nein |

Zwei Rollen, bewusst einfach:

- **Admin** — kann den Space Content Key rotieren und damit Members ausschließen. Beim Erstellen eines Space wird der Ersteller automatisch erster Admin. Mehrere Admins sind möglich.
- **Member** — kann Daten lesen, schreiben und neue Mitglieder einladen. Kann niemanden entfernen.

**Jeder darf einladen, nur Admins dürfen rotieren/entfernen.** Das spiegelt eine Vertrauenskultur: wer eingeladen wurde, darf seinerseits einladen. Wer Missbrauch betreibt, wird von einem Admin entfernt.

### Mehrere Admins

Jeder Space kann mehrere Admins haben. Ein Admin kann weitere Admins hinzufügen. Das ist wichtig für Gruppen mit geteilter Verantwortung (Festival-Orga, Kooperativen, Vereine):

- Bei Ausfall eines Admins können die anderen weiter handeln
- Keine Single-Point-of-Failure-Situation
- Gemeinsame Moderation möglich

Die Admin-DIDs (abgeleitete Keys pro Space) werden beim Broker registriert. Jeder einzelne Admin kann Rotationen auslösen.

### Warum keine feineren Rollen

Feinere Rollen (Moderator, Read-Only) erzeugen Komplexität bei der Synchronisation — insbesondere bei konkurrierenden Aktionen. Zwei Rollen decken den Großteil der Anwendungsfälle ab. Feinere Permissions können als Extension spezifiziert werden.

## Space-Erstellung

```
1. Alice erstellt einen Space:
   → Generiert Space Content Key (symmetrisch, 32 Bytes zufällig)
   → Generiert Space Capability Key Pair (Ed25519)
   → Leitet ihren Admin Key ab (siehe [Sync 005](005-verschluesselung.md#admin-key-abgeleitet))

2. Alice registriert den Space beim Broker:
   → Space-ID
   → Space Public Key (für Capability-Verifikation)
   → Admin-DIDs (aktuell: Alice's abgeleitete Admin-DID)
   → Registrierung signiert mit Admin Key

3. Alice hält lokal:
   → Space Content Key, Space Capability Signing Key
   → Ihren Admin Key
   → Mitgliederliste im CRDT: [Alice's Haupt-DID]
```

## Einladung

### Ablauf

```
Alice (Member oder Admin) lädt Bob ein:

1. Alice signiert eine Capability für Bob mit dem Space Private Key

2. Alice erstellt eine Einladungs-Nachricht:
   - Space-ID
   - Aktueller Space Key (Generation N)
   - Alle bisherigen Space Keys (Generation 0..N-1) für historische Daten
   - Space Private Key (Ed25519)
   - Admin-DIDs (aus dem CRDT, für UI-Anzeige)
   - Heim-Broker-URL(s) des Space
   - Capability (signiert vom Absender mit Space Private Key)

3. Alice verschlüsselt die Einladung via ECIES für Bobs X25519 Public Key
   (siehe Sync 005)

4. Alice sendet die Einladung als Inbox-Nachricht an Bob

5. Bob empfängt, entschlüsselt und akzeptiert die Einladung

6. Bob verbindet sich mit dem Heim-Broker, zeigt seine Capability vor
   → Broker verifiziert Signatur mit Space Public Key → OK

7. Bob synchronisiert die Daten (Catch-Up)
```

Jeder Member kann Capabilities signieren, weil jeder den Space Capability Signing Key hat. **Kein Delegations-Problem** — keine Admin-Signatur nötig für Einladungen.

### Einladungs-Nachricht

Inbox-Nachrichtentyp `space-invite`, verschlüsselt mit ECIES:

```json
{
  "id": "uuid",
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

Bob kann die Einladung annehmen oder ablehnen. Bei Annahme:
- Bob speichert Space Content Key, Space Capability Signing Key und Capability lokal
- Bob verbindet sich mit dem Heim-Broker
- Bob erscheint als neues Mitglied im CRDT-Log

Bei Ablehnung passiert nichts — Bob verwirft die Nachricht.

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

Ein Admin kann einen bestehenden Member zum Admin befördern:

```
Admin Alice befördert Bob zum Admin:

1. Alice erweitert die Admins-Liste im CRDT um Bobs Haupt-DID

2. Bob leitet seinen Admin Key ab (siehe [Sync 005](005-verschluesselung.md#admin-key-abgeleitet))

3. Alice registriert Bobs abgeleitete Admin-DID beim Broker:
   → Nachricht "admin-add" mit Bobs abgeleiteter Admin-DID
   → Signiert mit Alice's Admin Key (bestehender Admin)
   → Broker akzeptiert und fügt Bob zur Admin-Liste für diesen Space hinzu

4. Ab jetzt kann Bob ebenfalls Rotationen auslösen
```

## Key-Rotation (Member-Entfernung)

Bei Member-Entfernung wird der Space Key **und** das Space Keypair gemeinsam rotiert — damit werden auch alte Capabilities ungültig.

### Ablauf

```
Admin Alice entfernt Bob:

1. Alice schreibt eine Remove-Operation in den Log
   (Bob's Eintrag wird aus der Mitgliederliste entfernt)

2. Alice generiert:
   - Neuen Space Content Key (Generation N+1)
   - Neues Space Capability Key Pair

3. Alice sendet dem Broker eine Rotation-Nachricht:
   → Neuer spaceCapabilityVerificationKey, neue Generation
   → Signiert mit ihrem Admin Key
   → Broker verifiziert: gehört Admin-DID zur registrierten Admin-Liste?
   → Ja: neuer Verification Key wird aktiv, alte Capabilities ungültig

4. Alice verteilt an alle verbleibenden Mitglieder via ECIES:
   - Neuen Space Content Key
   - Neuen Space Capability Signing Key
   - Neue Capability (signiert mit neuem Signing Key)

5. Neue Daten werden mit dem neuen Space Content Key verschlüsselt

6. Bob hat weder neuen Content Key noch gültige Capability
   → kann keine neuen Daten entschlüsseln
   → wird vom Broker abgelehnt
```

### Key-Rotation Nachricht

Inbox-Nachrichtentyp `key-rotation`, verschlüsselt mit ECIES:

```json
{
  "id": "uuid",
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

### Forward Secrecy

Alte Daten bleiben mit dem alten Space Content Key lesbar (für Mitglieder die damals Zugriff hatten). Neue Daten sind für entfernte Mitglieder unlesbar. Das ist **kein perfekter Forward Secrecy** — Bob könnte alte Daten, die er bereits heruntergeladen hat, weiterhin lokal lesen. Aber er kann keine zukünftigen Daten entschlüsseln, und vom Broker werden ihm keine neuen Daten ausgeliefert.

## Concurrent-Verhalten

### Gleichzeitige Einladungen

Zwei Member laden gleichzeitig neue Leute ein → kein Konflikt. Beide Einladungen werden unabhängig verarbeitet, die Mitgliederliste konvergiert via CRDT-Merge.

### Einladung während Entfernung

Alice (Admin) entfernt Bob, während Carol (Member) Dave einlädt:
- Bobs Entfernung + Rotation gewinnt
- Dave's Einladung enthält den alten Space Key und alte Capability
- Dave braucht den neuen Space Key und die neue Capability
- Admin muss Dave die neuen Keys nachliefern (erkennt beim nächsten Sync, dass ein neuer Member mit veralteten Keys existiert)

### Gleichzeitige Rotationen durch verschiedene Admins

Zwei Admins rotieren gleichzeitig → der Broker akzeptiert die Rotation die zuerst ankommt. Die zweite Rotation wird abgelehnt (Generation veraltet). Der zweite Admin bekommt einen Fehler und muss neu rotieren, falls die Entfernung noch nicht abgedeckt ist.

In der Praxis sollten Admins sich informell absprechen bevor sie rotieren — das Protokoll verhindert aber auch ohne Absprache kein kaputtes Ergebnis, nur unnötige Nachsynchronisation.

## Neue Nachrichtentypen

| Type | Kanal | Beschreibung |
|------|-------|-------------|
| `space-invite` | Inbox | Einladung in einen Space (Content Key + Capability Signing Key + Capability) |
| `key-rotation` | Inbox | Neuer Content Key + Capability Signing Key nach Member-Entfernung |
| `admin-add` | Broker | Neue Admin-DID beim Broker registrieren (signiert von bestehendem Admin) |
| `admin-remove` | Broker | Admin-DID entfernen (signiert von anderem Admin) |
| `space-rotate` | Broker | Rotation des Space Public Keys (signiert von einem Admin) |

## Zusammenspiel mit dem Broker

### Initiale Space-Registrierung

Wenn ein User einen Space erstellt, registriert er ihn beim Broker:

```json
{
  "type": "space-register",
  "spaceId": "uuid",
  "spacePublicKey": "<base64url>",
  "adminDids": ["did:key:z6Mk...admin-derived"]
}
```

Signiert mit dem (noch einzigen) Admin Key. Der Broker akzeptiert die Registrierung, speichert Space-ID, Space Public Key und Admin-DIDs. Später können Admins hinzugefügt, entfernt oder das Keypair rotiert werden (jeweils signiert von einem eingetragenen Admin).

### Capability-Prüfung

Wenn ein Client Daten für einen Space syncen will:
1. Client sendet seine Capability
2. Broker prüft JWS-Signatur mit dem aktuellen Space Public Key
3. OK → Sync erlaubt

Details siehe [Sync 007](007-transport-und-broker.md#autorisierung-capabilities).

### Offline-Entfernung

Wenn ein Admin offline ist während er einen Member entfernt:
- Die Remove-Operation wird lokal im Log gespeichert
- Rotation-Nachricht an Broker wird lokal vorbereitet
- Beim nächsten Reconnect werden Log und Rotation synchronisiert
- Der Broker aktualisiert Space Public Key und invalidiert alte Capabilities

## Sicherheitsmodell

### Grundprinzip: Vertrauen innerhalb der Gruppe

Innerhalb einer Gruppe herrscht Vertrauen. Jedes Mitglied mit dem Space Key darf alles lesen und alles schreiben. Es gibt keine Feldebenen-Berechtigungen — der CRDT-Merge unterscheidet nicht nach Autor.

### Drei Regeln

1. **Alle Members dürfen alles lesen und schreiben.** Ein Space Key, ein CRDT, keine Feldrechte.
2. **Alle Members dürfen Capabilities für neue Members signieren** (mit dem Space Private Key). Einladungen sind nicht auf Admins beschränkt.
3. **Nur Admins dürfen rotieren (= Members ausschließen).** Rotation-Nachrichten werden am Broker geprüft — nur Nachrichten signiert mit einem registrierten Admin Key werden akzeptiert.

### Admin-Austritt

Ein Admin kann:
- **Aus dem Space austreten** — bleibt damit auch nicht länger Admin
- **Die Admin-Rolle abgeben** ohne den Space zu verlassen — wird zum normalen Member

Das geschieht durch eine `admin-remove`-Nachricht signiert mit dem eigenen Admin Key. Falls der ausscheidende Admin der einzige war, SOLLTE er vorher einen neuen Admin ernennen — sonst bleibt der Space ohne Admin und kann nicht mehr rotiert werden.

### Space ohne Admin

Falls alle Admins weg sind (z.B. alle haben ausgetreten oder verloren ihre Keys), ist der Space in seiner aktuellen Zusammensetzung eingefroren:
- Members können weiter lesen/schreiben
- Keine Rotation mehr möglich → keine Member-Entfernung mehr möglich
- Neue Einladungen sind weiter möglich (Member-Privileg)

Dies ist ein akzeptabler Degraded-Mode für kleine vertrauensvolle Gruppen.

### Privacy gegenüber dem Broker

Durch abgeleitete Admin-Keys erfährt der Broker **nicht**:
- Die Haupt-Identitäten der Admins
- Welche User über mehrere Spaces Admins sind
- Die Mitgliederliste (im verschlüsselten CRDT)

Der Broker sieht nur:
- Space-ID
- Space Public Key
- Abgeleitete Admin-DIDs (pro Space eindeutig, nicht verknüpfbar)
- Capability-Signaturen (bestätigen Zugriff, offenbaren aber nicht wer signiert hat)

### Was bewusst NICHT eingeschränkt ist

- **CRDT-Schreibrechte:** Jedes Mitglied kann beliebige Daten schreiben.
- **Einladungen:** Jedes Mitglied darf einladen.

### Zukünftiger Upgrade-Pfad

Für feinere Permissions (Read-Only Members, Feld-Ebenen-Rechte, delegierbare Rollen) können in Zukunft **Capability-Chains** eingeführt werden (z.B. Keyhive/Beelay-Modell). Das ist ein signifikanter Architektur-Schritt der erst sinnvoll wird wenn die zugrundeliegenden Frameworks produktionsreif sind.

## Zu klären

- **Admin-Transfer-Protokoll:** Details für "Admin überträgt seine Rolle an jemanden der noch nicht Admin ist" — Reihenfolge der Operationen (erst `admin-add`, dann `admin-remove`).
- **Capability-Caching:** Wie lange sollen Broker Capabilities cachen? Bei jeder Rotation müssen alle alten Capabilities verworfen werden.
