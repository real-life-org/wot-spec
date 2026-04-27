# WoT Sync 006: Personal Doc und Cross-Device Sync

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-18
- **Scope:** Personal Doc, Cross-Device Sync, Device-Management und Self-Addressed Messages
- **Depends on:** Identity 001, Identity 002, Sync 001, Sync 002, Sync 003
- **Conformance profile:** `wot-sync@0.1`

## Zusammenfassung

Das **Personal Doc** ist das persönliche, verschlüsselte Dokument eines Users. Es wird zwischen den eigenen Geräten synchronisiert und enthält Profil, Kontakte, Attestations, Space-Mitgliedschaften, Space Content Keys und Device-Registrierungen.

Technisch nutzt das Personal Doc dieselbe Sync-Infrastruktur wie Space-Dokumente. Der Unterschied liegt im Key-Management: Der Personal Doc Key wird deterministisch aus dem Seed abgeleitet.

## Referenzierte Dokumente

- [Identity 001: Identität](../01-wot-identity/001-identitaet-und-schluesselableitung.md) — Seed, HKDF-Ableitung
- [Sync 001: Verschlüsselung](001-verschluesselung.md) — AES-256-GCM, Nonce-Konstruktion
- [Sync 002: Sync-Protokoll](002-sync-protokoll.md) — Log-Struktur, seq-Konsistenz
- [Sync 003: Transport und Broker](003-transport-und-broker.md) — Multi-Broker-Replikation
- [Sync 005: Gruppen](005-gruppen.md) — Vergleichspunkt für das Key-Modell

## Abgrenzung

Personal Doc und Space-Dokumente nutzen dieselbe Log-Struktur, dasselbe Sync-Protokoll und dieselbe Verschlüsselung. Sie unterscheiden sich im Key-Management:

| | Space-Dokument | Personal Doc |
|---|---|---|
| **Key-Erzeugung** | Zufällig vom Admin generiert | Deterministisch aus Seed abgeleitet |
| **Key-Verteilung** | Per ECIES an Members | Kein Transport nötig — jedes Device leitet selbst ab |
| **Mitglieder** | Explizite `members[]` | Implizit: eigene Devices mit gleichem Seed |
| **Key-Rotation** | Bei Member-Entfernung | Nur bei Seed-Kompromittierung → Identity-Migration |
| **Autorisierung** | Admin stellt Capabilities aus | User ist sein eigener Admin |
| **Document-ID** | Zufällig beim Erstellen | Deterministisch aus Personal Doc Key |
| **Replikation** | Auf Heim-Brokern des Space | Auf allen Brokern des Users (Redundanz) |

## Struktur des Personal Doc

Das Personal Doc ist ein CRDT-Dokument (siehe [Sync 002: CRDT-Agnostik](002-sync-protokoll.md#crdt-agnostik)) mit folgenden Kern-Feldern:

```
PersonalDoc
├── profile          — Öffentliches Profil (Name, Bio, Avatar)
├── devices          — Registrierte Geräte des Users
├── contacts         — Verifizierte Kontakte (DID → ContactInfo)
├── verifications    — Verifikations-Records (In-Person-Begegnungen)
├── attestations     — Empfangene/erstellte Attestations
├── spaces           — Mitgliedschaften in Spaces
└── groupKeys        — Space Content Keys pro (spaceId, generation)
```

### `profile`

Öffentliche Profil-Daten des Users. Dieses Profil wird vom [Profil-Service](004-discovery.md#profil-service) als JWS-signierte Kopie veröffentlicht; im Personal Doc liegt es als CRDT-Feld.

```json
{
  "did": "did:key:z6Mk...",
  "name": "Alice",
  "bio": "...",
  "avatar": "<URL oder Base64>",
  "brokerUrls": ["wss://broker.example.com"],
  "createdAt": "2026-01-15T...",
  "updatedAt": "2026-04-18T..."
}
```

### `devices`

Liste der registrierten Geräte des Users:

```json
{
  "<deviceId>": {
    "deviceId": "550e8400-e29b-41d4-a716-446655440000",
    "deviceKid": null,
    "name": "Alice's Handy",
    "status": "active",
    "registeredAt": "2026-01-15T10:00:00Z",
    "lastActive": "2026-04-18T10:00:00Z",
    "revokedAt": null
  }
}
```

**Begriffliche Trennung:**

- **`deviceId`** (UUID) — lokaler Sequenz-/Nonce-Namespace. Identifiziert das Gerät im Sync-Protokoll. Existiert immer.
- **`deviceKid`** (DID-URL, optional) — kryptographischer Device-Key als Verification Method ID (z.B. `did:peer:4z...#device-phone-1`). In Phase 1 ist `deviceKid` immer `null` (Shared-Seed-Modell, kein eigener Device-Key). In Phase 2 (Per-Device-Keys) wird hier die DID-URL des Device-Keys eingetragen.

Jedes Gerät trägt sich beim ersten Start selbst ein. Der User kann Geräte deaktivieren (siehe [Device-Verlust](#device-verlust)).

### `contacts`

Verifizierte und gespeicherte Kontakte, indexiert nach DID:

```json
{
  "did:key:z6Mk...bob": {
    "did": "did:key:z6Mk...bob",
    "name": "Bob",
    "verifiedAt": "2026-02-10T...",
    "trustLevel": null,
    "notes": "Treffen bei FoodCoop"
  }
}
```

Das `trustLevel`-Feld ist optional und nur relevant wenn die HMC-Extension (Trust Lists, [H01](../05-hmc-extensions/H01-trust-scores.md)) verwendet wird.

### `verifications`

Aufzeichnungen der In-Person-Verifikationen (siehe [Trust 002](../02-wot-trust/002-verifikation.md)):

```json
{
  "<verification-id>": {
    "id": "uuid",
    "counterpartyDid": "did:key:z6Mk...bob",
    "method": "in-person-qr",
    "timestamp": "2026-02-10T15:30:00Z",
    "location": { "lat": 50.55, "lng": 9.67 },
    "proof": "<JWS Challenge-Response>"
  }
}
```

### `attestations`

Empfangene und erstellte Attestations (siehe [Trust 001](../02-wot-trust/001-attestations.md)):

```json
{
  "<attestation-id>": {
    "id": "uuid",
    "direction": "received | issued",
    "jws": "<JWS Compact String — das autoritative, signierte VC>",
    "receivedAt": "2026-02-10T15:30:00Z",
    "public": false
  }
}
```

### `spaces`

Mitgliedschaften des Users in Spaces:

```json
{
  "<spaceId>": {
    "spaceId": "uuid",
    "joinedAt": "2026-03-01T...",
    "role": "admin | member",
    "brokerUrls": ["wss://broker.community.org"],
    "currentKeyGeneration": 3
  }
}
```

### `groupKeys`

Die Space Content Keys aller Generationen die der User erhalten hat:

```json
{
  "<spaceId>:<generation>": {
    "spaceId": "uuid",
    "generation": 3,
    "key": "<Base64URL 32 Bytes>"
  }
}
```

Diese werden benötigt um historische Space-Daten zu entschlüsseln (siehe [Sync 001: Schlüsselrotation](001-verschluesselung.md#schlüsselrotation)).

### Implementierungsspezifische Felder

Eine Implementierung DARF zusätzliche Felder verwalten die für den Betrieb nötig sind aber nicht zum Sync-Protokoll gehören — z.B. eine Outbox für unzugestellte Nachrichten, Metadaten zu Delivery-Status, Caches. Diese Felder sind nicht Teil der Spec und MÜSSEN nicht zwischen Implementierungen interoperabel sein.

## Schlüsselableitung

Der Personal Doc Key wird deterministisch aus dem BIP39-Seed abgeleitet (siehe [Identity 001](../01-wot-identity/001-identitaet-und-schluesselableitung.md)):

```
BIP39 Seed
  → HKDF-SHA256(seed, info="wot/personal-doc/v1") → 32 Bytes
  → Personal Doc Key (AES-256)
```

Damit hat jedes Gerät des Users denselben Personal Doc Key. Es muss nichts verteilt werden.

### Deterministische Document-ID

Die Dokument-ID des Personal Doc wird aus dem Personal Doc Key abgeleitet:

```
docId = first_16_bytes(Personal Doc Key)  → formatiert als UUID
```

Damit hat jedes Gerät des Users dieselbe Document-ID. Der Broker speichert Log-Einträge unter dieser ID, ohne wissen zu müssen, dass es ein Personal Doc ist.

## Device-Management

### Device-Lifecycle

Ein Device durchläuft die Zustände `new`, `active`, `restored/cloned` und `revoked`. Broker-Registrierung und Revocation sind in [Sync 003](003-transport-und-broker.md#device-registrierung) spezifiziert; `seq`-/Restore-Regeln in [Sync 002](002-sync-protokoll.md#seq-konsistenz-muss).

### Device-Registrierung

Wenn ein Gerät mit einem bestehenden Seed initialisiert wird, generiert es eine zufällige Device-UUID, leitet Personal Doc Key und Document-ID ab, verbindet sich mit dem Broker und trägt sich selbst in `devices` ein. Die Kenntnis des Seed ist die Zugangsberechtigung.

### Device-Deaktivierung

Der User kann ein Device als deaktiviert markieren. Das setzt `revokedAt` auf den aktuellen Zeitstempel:

```json
{
  "<deviceId>": {
    "deviceId": "...",
    "revokedAt": "2026-04-18T10:00:00Z",
    "revokedBy": "<other-deviceId>"
  }
}
```

Nach Deaktivierung lehnt der Broker Authentisierung mit dieser `deviceId` ab (siehe [Sync 003](003-transport-und-broker.md#device-deaktivierung)); eigene Geräte sehen die Deaktivierung über das Personal Doc. Andere Space-Members werden nicht direkt benachrichtigt, weil sie DID-Signaturen und nicht Device-IDs prüfen.

### Limitationen der Device-Deaktivierung (MUSS dokumentiert)

Im aktuellen **Shared-Seed-Modell** (siehe [Identity 001](../01-wot-identity/001-identitaet-und-schluesselableitung.md#multi-device--shared-seed-modell)) ist Device-Deaktivierung keine kryptographische Maßnahme. Die `deviceId` ist eine UUID, kein Schlüssel; wer den Seed extrahiert, kann eine neue `deviceId` erzeugen und sich erneut registrieren.

Bei Seed-Kompromittierung schützt nur Key-Rotation aller Spaces und gegebenenfalls Identitäts-Rotation (siehe [Identity Migration](../research/identity-migration.md)). Per-Device Keys sind ein zukünftiger Upgrade-Pfad.

### Restore/Clone-Detection: erzwungener deviceId-Wechsel

Bei Device-Restore oder Storage-Clone können zwei physische Geräte dieselbe `deviceId` beanspruchen. Sobald ein Client beim Reconnect feststellt, dass der Broker für seine `(deviceId, docId)` einen höheren `seq` hat als er selbst, MUSS er dieses als Restore/Clone-Ereignis behandeln (siehe [Sync 002](002-sync-protokoll.md#seq-konsistenz-muss)):

1. **Neue `deviceId` generieren** (zufällige UUID v4)
2. **Alte `deviceId` deaktivieren** via signierter `device-revoke`-Nachricht an den Broker
3. **Personal Doc aktualisieren:** Neue `deviceId` in `devices` eintragen, alte als `revokedAt` markieren
4. **Extensions benachrichtigen** über den `deviceId`-Wechsel (siehe [Extension-Hinweis](#extension-hinweis-device-spezifische-felder))
5. **Neu beginnen** unter der neuen `deviceId` ab `seq=0`

`SEQ_COLLISION_DETECTED` am Broker ist nur die letzte Verteidigungslinie; der Client SOLL Restore/Clone lokal erkennen, bevor eine Kollision entsteht.

### Extension-Hinweis: Device-spezifische Felder

Extensions des WoT-Protokolls (z.B. HMC, RLS) dürfen eigene Datenstrukturen im Personal Doc verwenden. Falls eine Extension device-spezifische Felder führt, gilt:

- Bei einem **deviceId-Wechsel** MUSS die Extension ihre device-spezifischen Felder konsistent aktualisieren
- Extensions, die solche Felder verwenden, MÜSSEN dokumentieren, wie sie auf deviceId-Wechsel reagieren
- WoT Sync stellt nur die CRDT-Infrastruktur und das Device-Rotation-Event bereit — die Semantik der device-spezifischen Felder liegt bei der Extension

### Device-Verlust

- Gerät verloren, Seed sicher: Device als `revoked` markieren; Space-Key-Rotation SOLLTE geprüft werden.
- Gerät verloren, Seed kompromittiert: Identity-Migration ist nötig (siehe [Identity Migration](../research/identity-migration.md)).
- Seed verloren: Recovery ist nur über Mnemonic-Backup möglich; ohne Backup ist eine neue Identität nötig.

## Sync-Mechanismus

Das Personal Doc nutzt dieselbe Log-, Signatur-, Nonce- und DIDComm-Infrastruktur wie Space-Dokumente (siehe [Sync 002](002-sync-protokoll.md)).

### Self-Addressed Messages

Personal-Doc-Nachrichten werden an die eigene DID adressiert. Der Broker routet sie an die anderen verbundenen Geräte derselben DID.

### Replikation auf mehreren Brokern

Das Personal Doc wird auf allen Brokern repliziert, bei denen der User registriert ist (siehe [Sync 003: Broker-Zuordnung und Multi-Broker](003-transport-und-broker.md#broker-zuordnung-und-multi-broker)). Die Devices übernehmen Multi-Broker-Synchronisierung; Broker kommunizieren nicht untereinander.

### `seq`-Konsistenz

Die in [Sync 002: seq-Konsistenz](002-sync-protokoll.md#seq-konsistenz-muss) definierte MUSS-Anforderung gilt auch hier.

## Verschlüsselung

Der Personal Doc wird mit dem Personal Doc Key und AES-256-GCM verschlüsselt. Die Nonce-Konstruktion ist dieselbe wie bei Space-Dokumenten (siehe [Sync 001: Nonce-Konstruktion](001-verschluesselung.md#nonce-konstruktion)):

```
Nonce = SHA-256(deviceId || "|" || seq)[0:12]
```

Es gibt keine Personal-Doc-Key-Rotation im normalen Betrieb; der Key ändert sich nur bei Identity-Migration.

## Capability-Modell

Der User ist sein eigener Admin für das Personal Doc. Broker prüfen self-issued Capabilities (siehe [Sync 003](003-transport-und-broker.md#autorisierung-capabilities)):

```
Personal Doc Capability:
  issuer   = did:key:z6Mk...alice (der User selbst)
  audience = did:key:z6Mk...alice (derselbe User)
  docId    = <deterministische Personal Doc ID>
  permissions = ["read", "write"]
```

Die Capability ist self-issued, vom User selbst signiert und kann jederzeit neu ausgestellt werden.

## Recovery

Wenn alle Geräte verloren gehen, aber der BIP39-Seed gesichert ist, kann ein neues Device Personal Doc Key und Document-ID ableiten, sich mit einem bekannten Broker verbinden, den verschlüsselten Personal-Doc-State laden und sich neu in `devices` registrieren. Falls kein Broker erreichbar ist, braucht der User ein lokales Backup.
