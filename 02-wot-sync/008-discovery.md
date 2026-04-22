# WoT Sync 008: Discovery

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-22

## Zusammenfassung

Dieses Dokument spezifiziert wie Clients Broker und Daten im Netzwerk finden. Die Verifikation von Personen (QR-Code, Challenge-Response) ist in [Core 004](../01-wot-core/004-verifikation.md) spezifiziert.

## Broker-Discovery

Ein Client muss wissen welche Broker er nutzen kann.

### Standard-Broker

Die App wird mit einem Standard-Broker ausgeliefert der sofort funktioniert. Der User braucht keine Konfiguration.

### Community-Einladung

Beim Beitritt zu einer Community wird die Broker-URL mitgeliefert (siehe [Sync 007](007-transport-und-broker.md#community-einladung)). Der Community-Broker wird automatisch zum persönlichen Broker und zum Space-Broker.

### Manuell konfiguriert

Der User gibt eine Broker-URL in der App ein (z.B. `wss://broker.meine-community.org`).

### Im Profil hinterlegt

Jeder User kann seine Broker-URLs in seinem öffentlichen Profil angeben. Andere Clients lesen die Broker-URL von dort.

## Profil-Service

Für Fälle wo kein physisches Treffen möglich ist — z.B. jemand wird von einem gemeinsamen Freund empfohlen — gibt es einen öffentlichen **Profil-Service**. Clients laden dort ihr öffentliches Profil hoch und können das Profil anderer User abrufen.

Der Service ist optional — das Protokoll funktioniert auch ohne ihn. Ohne Profil-Service ist nur In-Person-Discovery (per QR-Code) möglich.

### Drei Ressourcen-Arten

Der Profil-Service verwaltet pro DID drei separate, aber zusammengehörige JWS-Dokumente:

| Ressource | Pfad | Inhalt |
|---|---|---|
| **Profil** | `/p/{did}` | Öffentliches Profil (Name, Bio, Avatar, Encryption Key, Broker-URLs, Protokolle) |
| **Verifikationen** | `/p/{did}/v` | Liste empfangener In-Person-Verifikationen (Beweis des Web-of-Trust-Graphen) |
| **Attestations** | `/p/{did}/a` | Liste akzeptierter Attestations (öffentliche Aussagen die der Holder zeigen möchte) |

Die Trennung ermöglicht unabhängige Updates: Eine neue Attestation ändert nicht das Profil, Profile-Updates triggern keinen Re-Upload aller Verifikationen.

### HTTP-API

**Medien-Typen:**

- Request-Body bei `PUT`: `application/jws` (JWS Compact Serialization als UTF-8-String)
- Response-Body bei `GET`: `application/jws` (exakt die gespeicherten Bytes)

**Endpunkte:**

```
GET  /p/{did}      → 200 + JWS-Profil               | 404
PUT  /p/{did}      → 200 OK | 400 invalid | 403 DID mismatch
GET  /p/{did}/v    → 200 + JWS-Verifications       | 404
PUT  /p/{did}/v    → 200 | 400 | 403
GET  /p/{did}/a    → 200 + JWS-Attestations        | 404
PUT  /p/{did}/a    → 200 | 400 | 403
GET  /s?dids=d1,d2 → 200 + Batch-Summaries (JSON)
GET  /health       → 200 + `{"status":"ok"}`
```

**DID im Pfad:** URL-encoded (`did:key:z6Mk...` → `did%3Akey%3Az6Mk...`).

**Batch-Abfrage:** `GET /s?dids=did1,did2,...` liefert Summaries (kleine Ausschnitte) für bis zu 100 DIDs gleichzeitig. Nützlich für Kontaktlisten. Das Summary-Format ist implementierungsdefiniert (z.B. Name + Avatar-URL pro DID) und dient nur der Performance-Optimierung bei Listen-UIs.

### JWS-Payload-Struktur

Jede der drei Ressourcen ist ein JWS (siehe [Core 002](../01-wot-core/002-signaturen-und-verifikation.md)). Der Payload ist ein JSON-Objekt:

**Profil (`/p/{did}`):**

```json
{
  "did": "did:key:z6Mk...",
  "name": "Alice",
  "bio": "Nachbarschaftsgarten",
  "avatar": "data:image/png;base64,...",
  "encryptionPublicKey": "<Base64URL X25519, 32 Bytes>",
  "brokers": ["wss://broker.example.com"],
  "protocols": ["https://web-of-trust.de/protocols/attestation/1.0"],
  "updatedAt": "2026-04-22T10:00:00Z"
}
```

**Verifikationen (`/p/{did}/v`):**

```json
{
  "did": "did:key:z6Mk...",
  "verifications": [ /* Verification-VCs (JWS-Strings) */ ],
  "updatedAt": "2026-04-22T10:00:00Z"
}
```

**Attestations (`/p/{did}/a`):**

```json
{
  "did": "did:key:z6Mk...",
  "attestations": [ /* Attestation-VCs (JWS-Strings), die der Holder als akzeptiert markiert hat */ ],
  "updatedAt": "2026-04-22T10:00:00Z"
}
```

### Pflichtfelder im Profil

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `did` | DID | Ja | Die DID des Users (MUSS mit dem URL-Pfad übereinstimmen) |
| `version` | Integer | Ja | Monoton aufsteigende Versionsnummer (beginnt bei 0, steigt bei jedem Update um mindestens 1). Schützt gegen Rollback-Attacken. |
| `name` | String | Ja | Anzeigename |
| `bio` | String | Nein | Kurzbeschreibung |
| `avatar` | String | Nein | Avatar-Bild (Data-URL oder HTTPS-URL) |
| `encryptionPublicKey` | String | Ja | X25519 Public Key (Base64URL, 32 Bytes). Siehe [Sync 005](005-verschluesselung.md#encryption-key-discovery). |
| `brokers` | Array | Nein | Broker-URLs (`["wss://..."]`) |
| `protocols` | Array | Nein | Unterstützte Protokoll-URIs. Ermöglicht Clients zu erkennen, welche Extensions der Peer unterstützt. |
| `updatedAt` | ISO 8601 | Ja | Zeitstempel der letzten Änderung (nur informativ, kein Konfliktkriterium) |

### Signatur-Prüfung beim PUT

Der Server MUSS beim PUT:

1. JWS-Signatur mit dem Ed25519-Key aus der DID verifizieren (inklusive `alg=EdDSA`-Whitelist, siehe [Core 002](../01-wot-core/002-signaturen-und-verifikation.md))
2. Den `did`-Wert im Payload extrahieren und mit der DID im URL-Pfad vergleichen — bei Mismatch: **403 Forbidden**
3. Bei ungültiger Signatur: **400 Bad Request**
4. **Versions-Monotonie prüfen:** `version` im neuen Payload MUSS strikt größer sein als der `version`-Wert des bereits gespeicherten Profils (falls vorhanden). Andernfalls: **409 Conflict** mit dem aktuellen `version`-Wert im Fehler-Body.

Damit kann nur der Besitzer der DID sein Profil ändern, und alte Versionen können nicht erneut hochgespielt werden.

### Versionierung und Rollback-Schutz

Das `version`-Feld im signierten Payload dient als **monotoner Versions-Zähler** gegen Rollback-Attacken durch bösartige oder veraltete Profil-Server:

**Server-Pflicht:**

- Beim PUT MUSS die neue `version` strikt größer sein als die aktuell gespeicherte
- Der Server DARF keine älteren signierten Versionen ausliefern, nachdem eine neuere akzeptiert wurde

**Client-Pflicht:**

- Clients MÜSSEN die letzte gesehene `version` pro DID lokal cachen
- Beim erneuten Abruf MUSS die zurückgelieferte `version` **≥** der zuletzt gesehenen sein
- Ist die gelieferte `version` **kleiner**, MUSS der Client das als Rollback-Indikator behandeln: den Broker/Server als nicht vertrauenswürdig markieren, eine alternative Quelle versuchen, oder die Operation abbrechen

Das gilt unabhängig von allen drei Ressourcen — `/p/{did}`, `/p/{did}/v`, `/p/{did}/a` haben jeweils ihr eigenes `version`-Feld und werden unabhängig überprüft.

**HTTP-Caching** (ETag, If-None-Match) ist OPTIONAL und orthogonal zum Rollback-Schutz. Clients SOLLTEN den zuletzt geholten JWS-String mit dem frisch geholten vergleichen, bevor sie ihn erneut verarbeiten.

### Rate Limiting

Server DÜRFEN Rate Limits setzen (z.B. max. 10 PUTs pro Minute pro DID). Empfohlene Antwort bei Überschreitung: **429 Too Many Requests** mit `Retry-After`-Header.

### Fehler-Responses

| Status | Bedeutung | Wann |
|---|---|---|
| 200 | OK | Erfolgreicher GET/PUT |
| 400 | Bad Request | Ungültiges JWS, fehlende Felder, kaputte Payload-Struktur |
| 403 | Forbidden | DID-Mismatch zwischen URL und Payload |
| 404 | Not Found | DID hat kein Profil hochgeladen |
| 409 | Conflict | `version` im neuen Payload ist nicht strikt größer als die gespeicherte (Rollback-Versuch oder Race-Condition) |
| 429 | Too Many Requests | Rate Limit überschritten |
| 500 | Internal Server Error | Server-Fehler |

Fehler-Bodies sollten `Content-Type: text/plain` sein mit einer lesbaren Fehlermeldung.

## Daten-Discovery

Ein neues Gerät muss wissen welche Spaces existieren und wo die Daten liegen.

### Über den Broker

```
Neues Gerät verbindet sich mit Broker
  → Broker kennt alle Dokumente dieses Users
  → Client fragt: "Welche Dokumente hast du für meine DID?"
  → Broker antwortet mit Dokument-IDs
  → Client synced die Dokumente
```

### Über Multi-Device-Sync

Wenn ein zweites Gerät online ist, können Identity- und Key-Dokumente direkt gesynced werden — inklusive der Liste aller Spaces.
