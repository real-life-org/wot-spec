# Human Money Extension: Trust-Scores

- **Status:** Platzhalter
- **Autoren:** Sebastian Galek
- **Datum:** 2026-04-13

## Zusammenfassung

Erweitert WoT Attestations um quantitative Vertrauensstufen, Haftung und Trust-Propagation mit Hop-Limits. Ermöglicht die Berechnung eines numerischen Trust-Scores aus dem Attestation-Graphen.

## Trust-Levels (aus Sebastians ADR-00)

| Level | Bedeutung | Trust-Wert | Haftung |
|-------|-----------|------------|---------|
| 0 | Mensch-Existenz bestätigt | 0% | Keine |
| 1 | Bekannter | 30% | 0,5h |
| 2 | Guter Kontakt | 60% | 1,0h |
| 3 | Enger Vertrauter | 85% | 4,0h |

## Zwei Formate

### Einzelne Trust-Attestation

Kompatibel mit dem WoT Core — eine Aussage pro Kontakt:

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://wot.example/vocab/v1",
    "https://humanmoney.example/vocab/v1"
  ],
  "type": ["VerifiableCredential", "WotAttestation", "TrustRating"],
  "issuer": "did:key:z6Mk...alice",
  "credentialSubject": {
    "id": "did:key:z6Mk...bob",
    "claim": "Vertrauensstufe 3",
    "trustLevel": 3,
    "liability": "4.0h",
    "hopLimit": 2
  },
  "issuanceDate": "2026-04-13T10:00:00Z",
  "proof": { ... }
}
```

### Gebündelte Trust List (Sebastians primäres Format)

Alices gesamte Vertrauensliste als ein signiertes Dokument mit mehreren Subjects. Das ist Sebastians Kernmodell — eine Liste pro Nutzer, selektiv schwärzbar via SD-JWT:

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://wot.example/vocab/v1",
    "https://humanmoney.example/vocab/v1"
  ],
  "type": ["VerifiableCredential", "WotAttestation", "TrustList"],
  "issuer": "did:key:z6Mk...alice",
  "credentialSubject": [
    {
      "id": "did:key:z6Mk...bob",
      "trustLevel": 3,
      "liability": "4.0h",
      "hopLimit": 2
    },
    {
      "id": "did:key:z6Mk...carol",
      "trustLevel": 2,
      "liability": "1.0h",
      "hopLimit": 1
    },
    {
      "id": "did:key:z6Mk...dave",
      "trustLevel": 1,
      "liability": "0.5h",
      "hopLimit": 1
    }
  ],
  "issuanceDate": "2026-04-13T10:00:00Z",
  "proof": { ... }
}
```

**Selective Disclosure (SD-JWT):** Beim Weiterleiten der Liste können einzelne Einträge geschwärzt werden — die Signatur bleibt gültig. Alice kann Carol nur den Eintrag für Bob zeigen, ohne Dave und Carol's eigenen Eintrag preiszugeben.

**Verteilung:** Im Gegensatz zu qualitativen Attestations (Empfängerprinzip) verteilt der **Sender** seine Trust List aktiv via Gossip an sein Netzwerk. Jeder Knoten leitet die Liste unter Beachtung der Hop-Limits weiter.

### Verhältnis zu WoT Core Attestations

Trust Lists und qualitative Attestations sind verschiedene Dinge die koexistieren:

| | Qualitative Attestation (WoT Core) | Trust List (HMC Extension) |
|---|---|---|
| **Inhalt** | Freitext-Aussage ("kann gut programmieren") | Numerische Bewertung (Trust-Level 0-3) |
| **Granularität** | Eine Aussage pro VC | Alle Kontakte in einem Dokument |
| **Eigentum** | Empfänger besitzt (Empfängerprinzip) | Sender besitzt und verteilt (Senderprinzip) |
| **Verteilung** | Empfänger zeigt selektiv | Sender verteilt via Gossip |
| **Veränderung** | Unveränderlich — neue Attestation ersetzt alte | Neue Version der Liste ersetzt alte |
| **Semantik** | Geschenk — "das sage ich über dich" | Weltsicht — "so sehe ich mein Netzwerk" |

Beide Formate sind signiert und versioniert — das signierte Dokument selbst ist in beiden Fällen unveränderlich. Bei Trust Lists wird eine neue Version erstellt und neu signiert wenn sich Bewertungen ändern.

## Trust-Propagation (aus Sebastians ADR-01)

- **Einzelner Pfad:** `Trust = Kante₁ × Kante₂ × ... × Kanteₙ`
- **Multi-Path:** `Trust_Total = 1 - ((1-Trust_Pfad₁) × (1-Trust_Pfad₂) × ...)`
- **Lokale Berechnung:** Vollständig dezentral auf dem Client (Ego-Graph)
- **Sybil-Resistenz:** Multiplikative Dämpfung bestraft lange Ketten — Fake-Accounts kommen nie über relevante Trust-Werte

## Reziprokes Routing (aus Sebastians ADR-05)

Tit-for-Tat Hop-Limit-Mirroring: Wenn Alice Carol nur Hop-Limit 1 gibt, spiegelt Carol das zurück. Wer seine Liste stark limitiert, verliert Netzwerk-Reichweite. Spieltheoretisch stabile Balance zwischen Privatsphäre und Netzwerknutzen.

## Gossip-Propagation (aus Sebastians ADR-06)

Vertrauenslisten werden via Gossip verteilt:
- **Sent-Log:** Sender merkt sich 180 Tage lang welche Listen er wem geschickt hat
- **Delta-Sync:** Nur neue oder geänderte Einträge werden gesendet
- **Hop-Priorisierung:** Nahe Kontakte (Hop=1) werden zuerst gesendet
- **Piggybacking:** Trust-Deltas werden an reguläre Transaktionen angehängt

## Zu klären

- Detaillierte Spec der Trust-Berechnung (mit Sebastian)
- Passt das VC-Format für seine SD-JWT-Listen? (W3C VC-SD wird standardisiert)
- Spieltheoretische Analyse der Hop-Limits
- ~~Gossip-Protokoll: könnte es über unseren Broker/Sync laufen statt nur P2P?~~ → Ja, siehe [H03 Gossip-Propagation](H03-gossip.md)
