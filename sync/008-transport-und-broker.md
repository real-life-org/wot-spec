# WoT Spec 005: Transport und Broker

- **Status:** Platzhalter
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-13

## Zusammenfassung

Spezifiziert wie Daten zwischen Peers transportiert werden und wie Broker als immer-online Peers funktionieren.

## Zu klären

- Message Envelope Format (aus Spec 002 hierher verschoben): v, id, type, fromDid, toDid, payload, signature
- Grundprinzip: ein Peer ist ein Peer (Broker = Peer der immer online ist)
- Was ein Broker speichert: Log-Einträge + Inbox-Nachrichten
- Was ein Broker NICHT sieht: Klartext, CRDT-State, Dokumentinhalte
- Broker-API: WebSocket-Protokoll für Sync + Inbox
- Multi-Broker: Client repliziert zu mehreren Brokern, kein Federation-Protokoll
- Push-Notifications: UnifiedPush/ntfy als Wecker (RFC-0004)
- Transport-Agnostik: WebSocket, QUIC, Bluetooth, Sneakernet
- Community-betriebene Broker: einfaches Setup, keine Domain nötig

## Architektur-Grundlage

Siehe `drafts/006-sync-architektur.md` Abschnitt 5 (Broker) und Abschnitt 6 (Transport).
Siehe `drafts/005-sync-and-transport.md` für die vollständige Forschungsgrundlage.
