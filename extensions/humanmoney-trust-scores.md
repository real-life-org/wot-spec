# Human Money Extension: Trust-Scores

- **Status:** Platzhalter
- **Autoren:** Sebastian Galek
- **Datum:** 2026-04-13

## Zusammenfassung

Erweitert WoT Attestations um quantitative Vertrauensstufen, Haftung und Trust-Propagation mit Hop-Limits. Ermöglicht die Berechnung eines numerischen Trust-Scores aus dem Attestation-Graphen.

## Felder

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `credentialSubject.trustLevel` | Integer (0-3) | Vertrauensstufe |
| `credentialSubject.liability` | String | Haftung in Arbeitsstunden (z.B. `"4.0h"`) |
| `credentialSubject.hopLimit` | Integer | Maximale Weitergabe-Tiefe |

## Trust-Levels (aus Sebastians ADR-00)

| Level | Bedeutung | Trust-Wert | Haftung |
|-------|-----------|------------|---------|
| 0 | Mensch-Existenz bestätigt | 0% | Keine |
| 1 | Bekannter | 30% | 0,5h |
| 2 | Guter Kontakt | 60% | 1,0h |
| 3 | Enger Vertrauter | 85% | 4,0h |

## Trust-Propagation (aus Sebastians ADR-01)

- **Einzelner Pfad:** `Trust = Kante₁ × Kante₂ × ... × Kanteₙ`
- **Multi-Path:** `Trust_Total = 1 - ((1-Trust_Pfad₁) × (1-Trust_Pfad₂) × ...)`
- **Lokale Berechnung:** Vollständig dezentral auf dem Client (Ego-Graph)

## SD-JWT Trust Lists (aus Sebastians ADR-04)

Gebündelte Trust Lists mit Selective Disclosure. Siehe [003 Attestations](../core/003-attestations.md), Abschnitt Human Money Extension.

## Reziprokes Routing (aus Sebastians ADR-05)

Tit-for-Tat Hop-Limit-Mirroring: Wer seine Liste stark limitiert, wird aus dem Netzwerk herausgefiltert.

## Context

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://wot.example/vocab/v1",
    "https://humanmoney.example/vocab/v1"
  ]
}
```

## Zu klären

- Detaillierte Spec der Trust-Berechnung (mit Sebastian)
- Sybil-Resistenz durch multiplikative Dämpfung
- Spieltheoretische Analyse der Hop-Limits
