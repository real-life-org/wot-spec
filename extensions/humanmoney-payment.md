# Human Money Extension: Payment

- **Status:** Platzhalter
- **Autoren:** Sebastian Galek
- **Datum:** 2026-04-13

## Zusammenfassung

Erweitert das WoT-Protokoll um dezentrales Payment mit Gutscheinen. Nutzt Detached Signatures, Device-Prefixes für Double-Spend-Prevention und ein Gossip-basiertes Fingerprint-Protokoll.

## Themen (aus Sebastians Implementierung)

- **Detached Signatures** — Multi-Signer-Format für Gutscheine mit mehreren Bürgen
- **SecureContainer** — Multi-Empfänger-Verschlüsselung (X25519 + ChaCha20-Poly1305)
- **Device-Prefixes / SAI** — Separierte Wallet-Instanzen pro Gerät
- **TransactionFingerprints** — Double-Spend-Detection via Gossip
- **ProofOfDoubleSpend** — Kryptografischer Betrugs-Beweis

## Zu klären

- Detaillierte Spec (mit Sebastian)
- Abgrenzung zu WoT Core Device-Keys (Sync 006) vs. Payment Device-Prefixes
- SecureContainer als eigenständiges Format oder als Extension des WoT Core Verschlüsselungsmodells (Sync 005)
