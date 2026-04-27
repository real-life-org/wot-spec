# Human Money Extension: Gossip-Propagation

- **Status:** Entwurf
- **Autoren:** Sebastian Galek, Anton Tranelis
- **Datum:** 2026-04-16
- **Scope:** HMC Gossip-Protokoll fuer Trust-Listen und Transaktionsdaten
- **Depends on:** H01, H02, Sync 002, Sync 003
- **Conformance profile:** `wot-hmc@0.1`

## Zusammenfassung

Spezifiziert wie Trust Lists über die bestehende WoT Sync Infrastruktur (Inbox, Broker) verteilt werden. Kein neues Protokoll — nur ein neuer Inbox-Nachrichtentyp und Client-seitige Forward-Logik.

## Grundprinzip

Die Gossip-Propagation nutzt den **Inbox-Kanal** (siehe [Sync 003](../03-wot-sync/003-transport-und-broker.md)), verschlüsselt mit ECIES (siehe [Sync 001](../03-wot-sync/001-verschluesselung.md)), als Transportweg. Der Broker braucht keine Änderungen — er sieht nur verschlüsselte Inbox-Nachrichten wie immer.

```
Alice aktualisiert ihre Trust List
  → verschlüsselt relevante Einträge pro Kontakt (SD-JWT)
  → sendet als Inbox-Nachricht an jeden Kontakt

Bob empfängt (online oder via Store-and-Forward)
  → prüft Hop-Limit: darf ich weiterleiten?
  → Ja → leitet an seine Kontakte weiter (Hop-Limit - 1)
  → Nein → speichert nur lokal

Broker sieht: verschlüsselte Inbox-Nachrichten
  → kein Gossip-Protokoll nötig
  → kein Wissen über Trust-Listen
  → nur Store-and-Forward wie immer
```

## Nachrichtentyp: `trust-list-delta`

Im Message Envelope (siehe [Sync 003](../03-wot-sync/003-transport-und-broker.md#message-envelope-didcomm-kompatibel)) wird ein neuer Typ definiert, verschlüsselt mit ECIES:

```json
{
  "id": "uuid",
  "typ": "application/didcomm-plain+json",
  "type": "https://web-of-trust.de/protocols/trust-list-delta/1.0",
  "from": "did:key:z6Mk...alice",
  "to": ["did:key:z6Mk...bob"],
  "created_time": 1776514800,
  "body": {
    "delta": "<SD-JWT-VC-Compact-String mit selektiv offengelegten Einträgen>"
  }
}
```

Die `body.delta` enthält die Trust List (oder ein Delta) als **SD-JWT VC** ([IETF Draft](https://datatracker.ietf.org/doc/draft-ietf-oauth-sd-jwt-vc/), normativ in [H01](H01-trust-scores.md)) — selektiv offengelegt für den jeweiligen Empfänger. Der Empfänger sieht nur die Einträge, deren Disclosures der Sender im konkatenierten SD-JWT-Compact-String mitsendet. Die Signatur im JWT-Header bleibt über alle Verteilungs-Hops gültig, weil die Disclosures nur die ohnehin im Payload enthaltenen Hashes ergänzen.

## Client-Logik

### Senden

Wenn Alice ihre Trust List aktualisiert:

1. **Delta berechnen** — was hat sich seit dem letzten Versand geändert?
2. **Empfänger bestimmen** — alle Kontakte mit Hop-Limit ≥ 1
3. **Selective Disclosure** — pro Empfänger: nur relevante Disclosures in den SD-JWT-VC-Compact-String aufnehmen
4. **Priorisierung** — nahe Kontakte (Hop-Limit = 1) zuerst
5. **Sent-Log aktualisieren** — merken was wann an wen gesendet wurde

### Empfangen

Wenn Bob ein `trust-list-delta` empfängt:

1. **Signatur prüfen** — ist die Nachricht authentisch?
2. **Trust List aktualisieren** — neue/geänderte Einträge in lokalen Ego-Graph einpflegen
3. **Hop-Limit prüfen** — ist Hop-Limit > 1?
   - **Ja:** Weiterleiten an eigene Kontakte mit Hop-Limit - 1
   - **Nein:** Nur lokal speichern, nicht weiterleiten
4. **ACK senden** — Empfangsbestätigung an Broker (Nachricht kann gelöscht werden)

### Sent-Log

Der Client führt einen lokalen Sent-Log:

| Empfänger | Letzte Version | Zeitpunkt | Nächstes Delta fällig |
|-----------|---------------|-----------|----------------------|
| Bob | v12 | 2026-04-16 | Bei Änderung |
| Carol | v11 | 2026-04-15 | v12 ausstehend |

- **Retention:** 180 Tage (aus Sebastians ADR-06)
- **Delta-Sync:** Nur Änderungen seit der letzten gesendeten Version
- **Kein erneutes Senden** wenn sich nichts geändert hat

## Piggybacking

Trust-List-Deltas DÜRFEN an andere Inbox-Nachrichten angehängt werden (z.B. Transaktionen). Das reduziert die Anzahl separater Nachrichten. Dazu wird ein `piggyback`-Feld im JWS-Payload ergänzt:

```json
{
  "type": "inbox",
  "payload": "<verschlüsselte Transaktion>",
  "piggyback": "<separater JWS mit trust-list-delta>"
}
```

Der Empfänger verarbeitet beide Payloads unabhängig.

## Warum Inbox und nicht Log-Sync

| | Inbox (gewählt) | Log-Sync |
|---|---|---|
| Selective Disclosure | Natürlich — pro Empfänger verschlüsselt | Schwierig — alle Members sehen denselben Log |
| Hop-Limit-Kontrolle | Client entscheidet pro Weiterleitung | Müsste in den Log eingebaut werden |
| Piggybacking | Einfach (Inbox-Nachricht anhängen) | Nicht möglich |
| Broker-Änderungen | Keine | Keine |

Trust Lists brauchen gezielte Zustellung (jeder Empfänger sieht andere Einträge). Log-Sync ist für Dokumente die alle Members gleich sehen. Deshalb ist die Inbox der richtige Kanal.

## Schichten-Trennung

```
┌──────────────────────────────────────────────┐
│  HMC Extension (H03)                         │
│  Trust-List-Deltas, Hop-Limits, Sent-Log,    │
│  Forward-Logik, SD-JWT Selective Disclosure  │
├──────────────────────────────────────────────┤
│  WoT Sync (007)                              │
│  Inbox, Broker, Store-and-Forward, E2EE,     │
│  Message Envelope, Push Notifications        │
├──────────────────────────────────────────────┤
│  WoT Trust (003-004)                         │
│  Attestations, Verifikation                  │
├──────────────────────────────────────────────┤
│  WoT Identity (001, 002, 005)                │
│  DID, Ed25519, Signaturen, Resolution        │
└──────────────────────────────────────────────┘
```

WoT Sync liefert die Rohre. HMC Extension definiert was durchfließt. Keine der Schichten muss die andere verstehen.

## Referenzen

- [Sync 003: Transport und Broker](../03-wot-sync/003-transport-und-broker.md) — Inbox-Kanal, Message Envelope
- [H01: Trust-Scores](H01-trust-scores.md) — Trust-Levels, Trust Lists, SD-JWT
- Sebastians ADR-06 — Gossip-Propagation (Originalentwurf)
