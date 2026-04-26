# Real Life Extension: Display

- **Status:** Platzhalter (nicht normativ — wird ausgearbeitet wenn die Implementierung die Felder nutzt)
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-13
- **Scope:** Real-Life-Display-Felder fuer Attestations
- **Depends on:** Core 003
- **Conformance profile:** `wot-rls@0.1` (geplant, aktuell Platzhalter)

## Zusammenfassung

Erweitert WoT Attestations um visuelle Darstellung (Badges) und Event-/Ortsbezüge.

## Felder

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `credentialSubject.display.emoji` | String | Visuelles Symbol (z.B. 🌱, 🏆, ⭐) |
| `credentialSubject.display.color` | String | Farbe als Hex-Wert (z.B. `"#9bc53d"`) |
| `credentialSubject.display.shape` | String | Form (z.B. `"circle"`, `"star"`, `"hexagon"`) |
| `credentialSubject.event` | ID | Bezug zu einer Veranstaltung |
| `credentialSubject.location` | Object | Ort (`{ lat, lng }`) |

## Context

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    "https://web-of-trust.de/vocab/v1",
    "https://web-of-trust.de/vocab/rls/v1"
  ]
}
```

## Zu klären

- Claim-Link Protokoll (QR-Code für automatische Badge-Vergabe)
- Badge-Vorlagen / Templates
- Shapes: welche Formen definieren wir?
