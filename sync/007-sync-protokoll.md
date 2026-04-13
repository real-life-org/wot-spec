# WoT Spec 006: Sync-Protokoll

- **Status:** Platzhalter
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-13

## Zusammenfassung

Spezifiziert wie Daten zwischen Peers synchronisiert werden — verschlüsselt, CRDT-agnostisch, und über beliebige Transportwege.

## Zu klären

- Drei-Schichten-Modell: Log → Kompression → Reconciliation
- Schicht 1 (Log): Append-only Logs mit Sequenznummern pro Device pro Dokument
- Schicht 2 (Kompression): Sedimentree-Prinzip — deterministische Chunk-Bildung
- Schicht 3 (Reconciliation): RIBLT für effiziente Differenz-Berechnung
- Log-Eintrags-Format: seq, deviceKey, docId, data (verschlüsselt), timestamp, sig
- Sync-Ablauf: Live-Sync vs. Catch-Up vs. Push-Notification
- CRDT-Agnostik: Log-Einträge sind verschlüsselte Blobs, Protokoll kennt keinen CRDT-Typ

## Architektur-Grundlage

Siehe `drafts/006-sync-architektur.md` für die vollständige Architektur.
