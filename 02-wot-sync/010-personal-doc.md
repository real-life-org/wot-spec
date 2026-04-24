# WoT Sync 010: Personal Doc und Cross-Device Sync

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-18

## Zusammenfassung

Das **Personal Doc** ist das persönliche Dokument eines Users — synchronisiert zwischen seinen eigenen Geräten, verschlüsselt mit einem aus dem Seed abgeleiteten Schlüssel, und enthält die Daten die zu seiner Identität gehören (Profil, Kontakte, Attestations, Space-Mitgliedschaften, Device-Registrierungen).

Technisch nutzt das Personal Doc dieselbe Sync-Infrastruktur wie Gruppen-Dokumente (Log-Protokoll, Broker, DIDComm-Transport). Der Unterschied liegt im **Key-Management**: Der Personal Doc Key wird deterministisch aus dem Seed abgeleitet statt zufällig generiert und geteilt.

## Referenzierte Dokumente

- [Core 001: Identität](../01-wot-core/001-identitaet-und-schluesselableitung.md) — Seed, HKDF-Ableitung
- [Sync 005: Verschlüsselung](005-verschluesselung.md) — AES-256-GCM, Nonce-Konstruktion
- [Sync 006: Sync-Protokoll](006-sync-protokoll.md) — Log-Struktur, seq-Konsistenz
- [Sync 007: Transport und Broker](007-transport-und-broker.md) — Multi-Broker-Replikation
- [Sync 009: Gruppen](009-gruppen.md) — Vergleichspunkt für das Key-Modell

## Abgrenzung: Personal Doc vs. Space-Dokumente

Beide nutzen dieselbe Log-Struktur, dasselbe Sync-Protokoll, dieselbe Verschlüsselung. Der fundamentale Unterschied ist das **Key-Management**:

| | Space-Dokument | Personal Doc |
|---|---|---|
| **Key-Erzeugung** | Zufällig vom Admin generiert | Deterministisch aus Seed abgeleitet |
| **Key-Verteilung** | Per ECIES an Members | Kein Transport nötig — jedes Device leitet selbst ab |
| **Member-Liste** | Explizit als Feld (`members[]`) | Implizit: alle Devices mit gleichem Seed |
| **Key-Rotation** | Bei Member-Entfernung | Nur bei Seed-Kompromittierung → Identity-Migration |
| **Authorisierung** | Admin stellt Capabilities aus | User ist sein eigener Admin |
| **Document-ID** | Zufällig beim Erstellen | Deterministisch aus Personal Doc Key |
| **Replikation** | Auf Heim-Brokern des Space | Auf allen Brokern des Users (Redundanz) |

Diese Unterschiede ergeben sich aus der Natur der Sache: ein Space ist ein soziales Artefakt zwischen mehreren Menschen, ein Personal Doc ist die digitale Repräsentation einer einzelnen Identität.

## Struktur des Personal Doc

Das Personal Doc ist ein CRDT-Dokument (siehe [Sync 006: CRDT-Agnostik](006-sync-protokoll.md#crdt-agnostik)) mit folgenden Kern-Feldern:

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

Öffentliche Profil-Daten des Users:

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

Dieses Profil wird vom [Profil-Service](008-discovery.md#profil-service) abrufbar gemacht — dort als JWS-signierte Kopie, hier als CRDT-Feld das ohne Signatur gepflegt wird (die Signatur entsteht erst beim Publish).

### `devices`

Liste der registrierten Geräte des Users:

```json
{
  "<deviceId>": {
    "deviceId": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Alice's Handy",
    "registeredAt": "2026-01-15T10:00:00Z",
    "lastActive": "2026-04-18T10:00:00Z",
    "revokedAt": null
  }
}
```

Jedes Gerät trägt sich beim ersten Start selbst ein. Der User kann in der App Geräte aktiv deaktivieren (siehe [Device-Verlust](#device-verlust)).

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

Das `trustLevel`-Feld ist optional und nur relevant wenn die HMC-Extension (Trust Lists, [H01](../04-hmc-extensions/H01-trust-scores.md)) verwendet wird.

### `verifications`

Aufzeichnungen der In-Person-Verifikationen (siehe [Core 004](../01-wot-core/004-verifikation.md)):

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

Empfangene und erstellte Attestations (siehe [Core 003](../01-wot-core/003-attestations.md)):

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

Diese werden benötigt um historische Space-Daten zu entschlüsseln (siehe [Sync 005: Schlüsselrotation](005-verschluesselung.md#schlüsselrotation)).

### Implementierungsspezifische Felder

Eine Implementierung DARF zusätzliche Felder verwalten die für den Betrieb nötig sind aber nicht zum Core-Protokoll gehören — z.B. eine Outbox für unzugestellte Nachrichten, Metadaten zu Delivery-Status, Caches. Diese Felder sind nicht Teil der Spec und MÜSSEN nicht zwischen Implementierungen interoperabel sein.

## Schlüsselableitung

Der Personal Doc Key wird deterministisch aus dem Seed abgeleitet (siehe [Core 001](../01-wot-core/001-identitaet-und-schluesselableitung.md)):

```
Master Seed
  → HKDF-SHA256(seed, info="wot/personal-doc/v1") → 32 Bytes
  → Personal Doc Key (AES-256)
```

Damit hat jedes Gerät des Users den gleichen Personal Doc Key. Es muss nichts verteilt werden.

### Deterministische Document-ID

Die Dokument-ID des Personal Doc wird aus dem Personal Doc Key abgeleitet:

```
docId = first_16_bytes(Personal Doc Key)  → formatiert als UUID
```

Damit hat jedes Gerät des Users die gleiche Document-ID für das Personal Doc. Der Broker kann Log-Einträge unter dieser ID speichern und ausliefern ohne zu wissen dass es ein Personal Doc ist.

## Device-Management

### Device-Lifecycle-Übersicht

Ein Device durchläuft folgende Zustände:

```
new → active → (restored/cloned) → revoked
```

| Zustand | Auslöser | Personal Doc | Broker | Sync 006 |
|---|---|---|---|---|
| **new** | Erster App-Start | Device-UUID generiert, in `devices` eingetragen | — | — |
| **active** | Broker-Verbindung | — | Challenge-Response, Device registriert ([Sync 007](007-transport-und-broker.md#device-registrierung)) | Schreibt Log-Einträge unter eigener deviceId |
| **restored/cloned** | `broker_seq > local_seq` erkannt | Neue deviceId generiert, alte als `revokedAt` markiert | Alte deviceId revoked, neue registriert | Neu beginnen bei seq=0 unter neuer deviceId ([Sync 006](006-sync-protokoll.md#seq-konsistenz-muss)) |
| **revoked** | User deaktiviert oder Restore-Detection | `revokedAt` gesetzt | Authentisierung abgelehnt ([Sync 007](007-transport-und-broker.md#device-deaktivierung)) | Einträge mit dieser deviceId werden von Peers abgelehnt |

Details zu jedem Zustand in den folgenden Abschnitten. Die Regeln sind über drei Spec-Dokumente verteilt — die normative Quelle für jeden Aspekt ist in der Tabelle verlinkt.

### Device-Registrierung

Wenn ein Gerät mit einem bestehenden Seed initialisiert wird:

```
1. Device generiert lokale Device-UUID (zufällig, v4)
2. Device leitet Personal Doc Key und Document-ID aus Seed ab
3. Device verbindet sich mit Broker (Challenge-Response, siehe Sync 007)
4. Device holt aktuellen Personal Doc State vom Broker
5. Device trägt sich selbst in das devices-Feld ein (neuer Log-Eintrag)
6. Log-Eintrag wird an andere Devices des Users verteilt
```

Kein explizites Enrollment-Ticket oder Pairing nötig — die Kenntnis des Seed ist die einzige Zugangsberechtigung.

### Device-Deaktivierung

Der User kann in der App ein Device als deaktiviert markieren. Das setzt `revokedAt` auf den aktuellen Zeitstempel:

```json
{
  "<deviceId>": {
    "deviceId": "...",
    "revokedAt": "2026-04-18T10:00:00Z",
    "revokedBy": "<other-deviceId>"
  }
}
```

Nach Deaktivierung:

- **Broker:** Lehnt Authentisierung mit dieser `deviceId` ab (via `device-revoke` Nachricht, siehe [Sync 007](007-transport-und-broker.md#device-deaktivierung))
- **Eigene Geräte:** Sehen die Deaktivierung im Personal Doc (CRDT-Sync zwischen eigenen Devices)
- **Andere Peers (Space-Members):** Werden **nicht direkt benachrichtigt** — sie prüfen DID-Signaturen, nicht Device-IDs. Im Shared-Seed-Modell hat die Device-ID für andere Peers keine sicherheitsrelevante Bedeutung.
- Der User SOLLTE alle Space Content Keys rotieren (siehe unten)

### Limitationen der Device-Deaktivierung (MUSS dokumentiert)

Im aktuellen **Shared-Seed-Modell** (siehe [Core 001](../01-wot-core/001-identitaet-und-schluesselableitung.md#multi-device--shared-seed-modell)) ist Device-Deaktivierung **keine kryptographische Maßnahme**, sondern eine **UUID-basierte Konvention**:

- Die `deviceId` ist eine zufällige UUID, kein Schlüssel
- Wer den Seed extrahiert, kann **eine neue Device-UUID generieren** und sich als neues Device registrieren
- Die Deaktivierung wirkt nur gegen "ehrliche" Geräte, die sich an die Konvention halten

**Bei Seed-Kompromittierung schützt Device-Deaktivierung nicht.** Der einzige wirksame Schutz ist:

1. Sofortige Key-Rotation aller Spaces (wird neue Space Content Keys und neue Capabilities erzeugen)
2. Bei hochsensitiven Daten: Identitäts-Rotation (neue DID, siehe [Identity Migration](../research/identity-migration.md))

**Zukünftiger Upgrade:** Mit Per-Device Keys (gemeinsam mit DID-Methoden-Migration, siehe [Core 001](../01-wot-core/001-identitaet-und-schluesselableitung.md#zukünftiger-upgrade-pfad-per-device-keys)) wird Device-Deaktivierung kryptographisch bedeutungsvoll — der widerrufene Device-Key kann nicht einfach regeneriert werden.

### Restore/Clone-Detection: erzwungener deviceId-Wechsel

Bei einem Device-Restore aus Backup oder einem Storage-Clone kann die Situation entstehen, dass zwei physische Geräte dieselbe `deviceId` beanspruchen. Das würde zu katastrophalem AES-GCM-Nonce-Reuse führen (siehe [Sync 005](005-verschluesselung.md#nonce-konstruktion), [Sync 006](006-sync-protokoll.md#seq-konsistenz-muss)).

**Harte Regel:** Sobald ein Client beim Reconnect feststellt, dass der Broker für seine `(deviceId, docId)` einen höheren `seq` hat als er selbst, MUSS er dieses als Restore/Clone-Ereignis behandeln:

1. **Neue `deviceId` generieren** (zufällige UUID v4)
2. **Alte `deviceId` deaktivieren** via signierter `device-revoke`-Nachricht an den Broker
3. **Personal Doc aktualisieren:** Neue `deviceId` in `devices` eintragen, alte als `revokedAt` markieren
4. **Extensions benachrichtigen** über den `deviceId`-Wechsel (siehe [Extension-Hinweis](#extension-hinweis-device-spezifische-felder))
5. **Neu beginnen** unter der neuen `deviceId` ab `seq=0`

Die Broker-seitige Erkennung eines Konflikts (`SEQ_COLLISION_DETECTED`, siehe [Sync 007](007-transport-und-broker.md#wire-formate-der-sync-nachrichten)) ist die letzte Verteidigungslinie — der Client SOLL das Szenario bereits lokal erkennen und verhindern, bevor es zur Kollision kommt.

### Extension-Hinweis: Device-spezifische Felder

Extensions des WoT-Protokolls (z.B. HMC, RLS) dürfen eigene Datenstrukturen im Personal Doc verwenden. Falls eine Extension in einzelnen Items ein device-spezifisches Feld führt (z.B. HMC-Vouchers mit einer `custodyDeviceId` zur Lokalisierung der aktiven Verwahrung), gilt:

- Bei einem **deviceId-Wechsel** (siehe Restore/Clone-Detection oben) MUSS die Extension ihre device-spezifischen Felder konsistent aktualisieren — z.B. durch Master-Key-signierte CRDT-Operationen, die die alte `deviceId` durch die neue ersetzen
- Extensions, die solche Felder verwenden, MÜSSEN dokumentieren, wie sie auf deviceId-Wechsel reagieren
- Der Core stellt nur die CRDT-Infrastruktur und das Device-Rotation-Event bereit — die Semantik der device-spezifischen Felder liegt bei der Extension

Details zu HMC-spezifischen Feldern siehe [H02 Transactions](../04-hmc-extensions/H02-transactions.md) (in Arbeit mit Sebastian Galek).

### Device-Verlust

Drei Szenarien:

**1. Gerät ist weg, Seed ist sicher (verloren, defekt)**

- Der User markiert das Device in der App auf einem anderen Gerät als `revoked`
- Key-Rotation aller Spaces in denen der User Admin ist (vorsichtshalber)
- Für Spaces wo der User nur Member ist: er informiert die Admins, die rotieren

**2. Gerät ist weg, Seed ist kompromittiert**

- Das Device-Feld zu aktualisieren reicht nicht — der Angreifer könnte ein neues Device registrieren
- Identity-Migration nötig: neuer Seed, neue DID (siehe [research/identity-migration.md](../research/identity-migration.md))
- Kontakte müssen über die Migration informiert werden
- Attestations müssen neu ausgestellt werden oder als migriert markiert werden

**3. Seed-Verlust (z.B. einziges Gerät weg, kein Backup)**

- Kein Zugriff mehr auf Personal Doc, Space Content Keys, Attestations
- Recovery nur über Mnemonic-Backup (siehe [Core 001](../01-wot-core/001-identitaet-und-schluesselableitung.md))
- Ohne Backup: vollständiger Identity-Verlust, neue Identität nötig

## Sync-Mechanismus

Das Personal Doc nutzt **dieselbe Infrastruktur wie Space-Dokumente** (siehe [Sync 006](006-sync-protokoll.md)):

- Append-only Log pro `deviceId`
- Einträge mit `seq`, `deviceId`, `docId`, `authorDid`, `keyGeneration`, `data`
- Signierung und Nonce-Konstruktion identisch
- Transport über DIDComm-Nachrichten

### Self-Addressed Messages

Der Unterschied: Messages werden **an die eigene DID adressiert**. Der Broker routet sie an alle verbundenen Geräte mit dieser DID (außer dem Sender selbst):

```
Alice (Handy) schreibt neuen Log-Eintrag für Personal Doc
  → verschlüsselt mit Personal Doc Key
  → sendet DIDComm-Message mit from=alice, to=[alice]
  → Broker routet an Alices andere Geräte (Laptop, Tablet)
  → Diese Geräte entschlüsseln, merged CRDT
```

### Replikation auf mehreren Brokern

Weil der User mehrere Broker nutzen kann (für Redundanz), wird das Personal Doc **auf allen Brokern des Users repliziert** — siehe [Sync 007: Broker-Zuordnung](007-transport-und-broker.md#broker-zuordnung).

Die Devices kümmern sich selbst um die Multi-Broker-Synchronisierung. Der Broker muss nichts wissen über andere Broker.

### `seq`-Konsistenz

Die in [Sync 006: seq-Konsistenz](006-sync-protokoll.md#seq-konsistenz-muss) definierte MUSS-Anforderung gilt auch hier. Insbesondere nach Device-Restore: bevor das Gerät neue Einträge schreibt, MUSS es den aktuellen State vom Broker abgerufen haben, um den korrekten `seq` zu verwenden.

## Verschlüsselung

Der Personal Doc wird mit dem Personal Doc Key und AES-256-GCM verschlüsselt. Die Nonce-Konstruktion ist dieselbe wie bei Space-Dokumenten (siehe [Sync 005: Nonce-Konstruktion](005-verschluesselung.md#nonce-konstruktion)):

```
Nonce = SHA-256(deviceId || "|" || seq)[0:12]
```

Weil der Personal Doc Key deterministisch aus dem Seed abgeleitet wird, haben alle Geräte des Users automatisch den gleichen Key. Es gibt keine Key-Rotation im normalen Betrieb — der Key ändert sich nur bei Identity-Migration.

## Capability-Modell

Der User ist sein eigener Admin für das Personal Doc. Broker prüfen (siehe [Sync 007](007-transport-und-broker.md#autorisierung-capabilities)):

```
Personal Doc Capability:
  issuer   = did:key:z6Mk...alice (der User selbst)
  audience = did:key:z6Mk...alice (derselbe User)
  docId    = <deterministische Personal Doc ID>
  permissions = ["read", "write"]
```

Die Capability ist self-issued und vom User selbst signiert. Sie wird bei der ersten Verbindung zum Broker präsentiert und kann vom User für sich selbst jederzeit neu ausgestellt werden.

## Recovery

Wenn alle Geräte verloren gehen aber der Seed gesichert ist (BIP39-Mnemonic):

```
1. Neuer Device mit Seed initialisieren
2. Personal Doc Key und Document-ID aus Seed ableiten
3. Mit einem bekannten Broker verbinden (Standard-Broker oder aus Backup)
4. Personal Doc State vom Broker laden
5. State entschlüsseln mit Personal Doc Key
6. Neues Device im devices-Feld registrieren
```

Der Broker speichert das verschlüsselte Personal Doc solange der User bei ihm registriert ist. Es dient damit implizit als **dezentrales Backup** — jeder Broker auf dem das Personal Doc repliziert ist, kann nach Verlust die Wiederherstellung ermöglichen.

Für den Fall dass auch der Broker nicht mehr erreichbar ist, sollte ein zusätzliches lokales Backup (z.B. Vault) genutzt werden.

## Zukunft (nicht Phase 1)

- **Identity-Rotation:** Personal Doc bei DID-Wechsel — siehe [identity-migration.md](../research/identity-migration.md).
- **Mehrere Identitäten pro Gerät:** Aktuell nicht spezifiziert. Entscheidung bei Bedarf.
- **Verschlüsselung sensibler Felder:** `groupKeys` sind hochsensitiv — zusätzliche Verschlüsselung (Hardware-Keystore) als Implementierungsentscheidung.
- **Profil-Publish-Workflow:** Automatisches vs. manuelles Publizieren — Implementierungsentscheidung.
