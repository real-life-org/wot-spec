# WoT Sync 008: Discovery

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-16

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

Für Fälle wo kein physisches Treffen möglich ist — z.B. jemand wird von einem gemeinsamen Freund empfohlen:

- Öffentliche Profile werden auf einem Profil-Service hinterlegt (HTTPS, JWS-signiert)
- Profil enthält: DID, Name, Bio, Broker-URLs, öffentliche Attestations
- Jeder kann ein Profil über die DID abrufen

Der Profil-Service ist ein einfacher HTTP-Server:

```
GET /p/{did} → JWS-signiertes Profil-JSON
PUT /p/{did} → Profil aktualisieren (JWS-authentifiziert)
```

Der Service verifiziert die JWS-Signatur beim PUT — nur der Besitzer der DID kann sein Profil ändern. Der Service ist optional — das Protokoll funktioniert auch ohne ihn.

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
