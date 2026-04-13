# WoT Spec 004: Device-Keys und Delegation

- **Status:** Platzhalter
- **Autoren:** Anton Tranelis, Sebastian Galek
- **Datum:** 2026-04-13

## Zusammenfassung

Spezifiziert wie Geräte eine eigene kryptografische Identität bekommen und wie der Master Key an Device-Keys delegiert.

## Zu klären

- Device-Key-Erzeugung (zufällig, nicht aus Seed)
- Delegations-Format (Master Key signiert Autorisierung für Device Key)
- Login-Flows: erstes Gerät, neues Gerät (QR-Code), neues Gerät (Seed), Recovery
- Recovery Device Key (deterministisch aus Seed: `"wot/device/recovery/v1"`)
- Wer signiert was: Master Key für Identity-Aktionen, Device Key für Sync-Aktionen
- Device-Widerruf: wie wird einem Gerät der Zugang entzogen?
- Gemeinsames Fundament mit Human Money Core (Double-Spend-Prevention)
- Identity Migration bei Schlüsselrotation (Verweis auf drafts/004)

## Architektur-Grundlage

Siehe `drafts/006-sync-architektur.md` Abschnitt 2 (Device-Keys) für die Architektur-Entscheidungen.
