# WoT Sync 007: Discovery

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-13

## Zusammenfassung

Dieses Dokument spezifiziert wie sich Peers, Broker und Inhalte im Web of Trust finden.

## Drei Discovery-Ebenen

### 1. Menschen finden: Kontakt-Austausch

Zwei Menschen treffen sich und wollen sich im Web of Trust verbinden.

**QR-Code-Scan (primärer Weg):**

```
Alice zeigt ihren QR-Code (enthält DID + Public Key + Profil-Name)
  → Bob scannt
  → Bob zeigt seinen QR-Code
  → Alice scannt
  → Beide haben die DID des anderen
  → Challenge-Response für gegenseitige Verification (siehe Core 003)
```

Funktioniert offline. Kein Broker nötig. Die Verification-Attestation wird lokal erstellt und bei Reconnect zugestellt.

**Profil-Service (öffentliche Profile):**

Für Fälle wo kein physisches Treffen möglich ist — z.B. jemand wird von einem gemeinsamen Freund empfohlen:

- Öffentliche Profile werden auf einem Profil-Service hinterlegt (HTTPS, JWS-signiert)
- Profil enthält: DID, Name, Bio, öffentliche Attestations
- Jeder kann ein Profil über die DID abrufen

### 2. Broker finden

Ein Client muss wissen welche Broker er nutzen kann.

**Möglichkeiten:**

- **Im Profil hinterlegt:** Jeder User kann seine Broker-URLs in seinem öffentlichen Profil angeben. Andere Clients lesen die Broker-URL von dort.
- **Manuell konfiguriert:** Der User gibt die Broker-URL in der App ein (z.B. `wss://broker.meine-community.org`).
- **Standard-Broker:** Die App wird mit einem Standard-Broker ausgeliefert der sofort funktioniert.
- **Von einem Kontakt empfohlen:** "Nutze unseren Community-Broker" — URL wird beim Kontakt-Austausch mitgegeben.

### 3. Daten finden: Spaces und Dokumente

Ein neues Gerät muss wissen welche Spaces existieren und wo die Daten liegen.

**Über den Broker:**

```
Neues Gerät verbindet sich mit Broker
  → Broker kennt alle Dokumente dieses Users
  → Client fragt: "Welche Dokumente hast du für meine DID?"
  → Broker antwortet mit Dokument-IDs
  → Client synced die Dokumente
```

**Über Multi-Device-Sync:**

Wenn ein zweites Gerät online ist, können Identity- und Key-Dokumente direkt gesynced werden — inklusive der Liste aller Spaces.

## Zukunft: Lokale Peer-Discovery

Für direktes P2P-Sync ohne Broker (z.B. im selben WLAN):

- **mDNS** — Geräte im lokalen Netzwerk finden sich automatisch
- **Bluetooth Low Energy** — für Nahbereich-Discovery
- **WiFi Direct** — direkte Verbindung ohne Router

Wird implementiert wenn das P2P-Layer (via Iroh oder ähnlich) hinzugefügt wird.

## Zukunft: Private Interest Overlap

Aus der Willow-Forschung: Peers entdecken gemeinsame Interessen (z.B. gemeinsame Spaces) ohne preiszugeben welche anderen Interessen sie haben. Relevant für Privacy-bewusste Space-Discovery.

## Architektur-Grundlage

Siehe [Sync-Architektur](../research/sync-architektur.md) und [Forschungsdokument](../research/sync-and-transport.md) für Details zu Discovery-Ansätzen verschiedener Protokolle.
