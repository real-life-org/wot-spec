# Human Money Extension: Payment

- **Status:** Platzhalter (nicht normativ — wird mit Sebastian ausgearbeitet. Custody-Konzept siehe [Sync 006](../03-wot-sync/006-personal-doc.md#extension-hinweis-device-spezifische-felder))
- **Autoren:** Sebastian Galek
- **Datum:** 2026-04-13
- **Scope:** HMC Transaktionen, Vouchers und Settlement-Bezug
- **Depends on:** Trust 001, H01, Sync 006
- **Conformance profile:** `wot-hmc@0.1` (geplant, aktuell Platzhalter)

## Zusammenfassung

Erweitert das WoT-Protokoll um dezentrales Payment mit Gutscheinen. Nutzt Detached Signatures, Device-Prefixes für Double-Spend-Prevention und ein Gossip-basiertes Fingerprint-Protokoll.

## Themen (aus Sebastians Implementierung)

- **Detached Signatures** — Multi-Signer-Format für Gutscheine mit mehreren Bürgen
- **SecureContainer** — Multi-Empfänger-Verschlüsselung (X25519 + ChaCha20-Poly1305)
- **Device-Prefixes / SAI** — Separierte Wallet-Instanzen pro Gerät. Ein Gutschein existiert physisch nur auf einem Gerät — das verhindert Double-Spend im Offline-Fall
- **TransactionFingerprints** — Erkennung von absichtlichem Betrug (wenn jemand trotzdem versucht doppelt auszugeben) via Gossip-Propagation
- **ProofOfDoubleSpend** — Kryptografischer Betrugs-Beweis der im Netzwerk propagiert wird

## Zu klären

- Detaillierte Spec (mit Sebastian)
- SecureContainer als eigenständiges Format oder als Extension des Verschlüsselungsmodells (Sync 001)
