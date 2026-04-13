# WoT Spec 011: Discovery

- **Status:** Platzhalter
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-13

## Zusammenfassung

Spezifiziert wie Peers, Broker und Inhalte im Web of Trust gefunden werden.

## Zu klären

- Profil-Discovery: wot-profiles Service (öffentliche Profile, JWS-signiert)
- Broker-Discovery: wie findet ein Client seine Broker? (Profil, DNS, manuell)
- Peer-Discovery: wie finden sich zwei Peers im selben Netzwerk? (mDNS, Bluetooth)
- Private Interest Overlap (Willow PIO): Peers entdecken gemeinsame Interessen ohne Nicht-Geteiltes zu leaken
- Space-Discovery: wie erfährt ein neues Gerät von existierenden Spaces? (PersonalDoc / Identity Store)
- Öffentliche Items: Discovery über Profiles-Service oder separaten Endpunkt (RFC-0005)
- Kontakt-Austausch: QR-Code-Scan für gegenseitige Verifikation + Profil-Austausch
