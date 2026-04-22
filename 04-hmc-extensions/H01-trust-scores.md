# Human Money Extension: Trust-Scores

- **Status:** Entwurf
- **Autoren:** Sebastian Galek, Anton Tranelis
- **Datum:** 2026-04-19

## Zusammenfassung

Erweitert WoT Attestations um quantitative Vertrauensstufen, Haftung und Trust-Propagation mit Hop-Limits. Ermöglicht die Berechnung eines numerischen Trust-Scores aus dem Attestation-Graphen.

Trust-Lists werden als **SD-JWT VC** (IETF Draft) kodiert — das Selective-Disclosure-Profile von W3C Verifiable Credentials. Damit liegen unsere Trust-Lists direkt auf dem Interop-Pfad zum EU-Digital-Identity-Wallet-Ökosystem (eIDAS 2.0 schreibt SD-JWT VC als Pflichtformat vor).

## Trust-Levels (aus Sebastians ADR-00)

| Level | Bedeutung | Trust-Wert | Haftung |
|-------|-----------|------------|---------|
| 0 | Mensch-Existenz bestätigt | 0% | Keine |
| 1 | Bekannter | 30% | 0,5h |
| 2 | Guter Kontakt | 60% | 1,0h |
| 3 | Enger Vertrauter | 85% | 4,0h |

## Zwei Formate

### Einzelne Trust-Attestation (W3C VC)

Kompatibel mit dem WoT Core — eine Aussage pro Kontakt, als W3C Verifiable Credential:

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    "https://web-of-trust.de/vocab/v1",
    "https://web-of-trust.de/vocab/hmc/v1"
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
  "validFrom": "2026-04-13T10:00:00Z"
}
```

### Gebündelte Trust List (SD-JWT VC) — Sebastians primäres Format

Alices gesamte Vertrauensliste als ein signiertes Dokument mit mehreren Einträgen, kodiert als **SD-JWT VC** ([IETF Draft: SD-JWT-based Verifiable Credentials](https://datatracker.ietf.org/doc/draft-ietf-oauth-sd-jwt-vc/)). Das ist Sebastians Kernmodell — eine Liste pro Nutzer, selektiv offenlegbar beim Weitergeben.

**Grund für SD-JWT VC als normatives Format:**

- **EU-Wallet-Interop** — eIDAS 2.0 ARF schreibt SD-JWT VC als Pflichtformat für Credentials vor. Trust-Lists in diesem Format sind im EU-Digital-Identity-Ökosystem direkt lesbar.
- **JWT-native** — keine separate JSON-LD-Normalisierung, kein LD-Signatures-Aufwand. Passt zu unserer JWS-basierten Core-Signatur-Infrastruktur.
- **EdDSA-kompatibel** — unsere Ed25519-Identität wird direkt für die Signatur genutzt.
- **Holder-Redaktion** — der Besitzer der Liste kann beim Weitergeben einzelne Einträge verbergen, ohne die Signatur zu brechen. Exakt das Modell, das Sebastian braucht.
- **Salted-Hash-Mechanik** — jedes verschwärzbare Feld wird mit einem zufälligen Salt zu einem Hash gerechnet; der Hash landet im signierten JWT-Payload, der Klartext samt Salt als "Disclosure" separat. Offenlegen = Disclosure mitsenden. Schwärzen = Disclosure weglassen.

#### Struktur einer Trust-List als SD-JWT VC

**Issuer-signed JWT Payload** (was Alice signiert):

```json
{
  "iss": "did:key:z6Mk...alice",
  "iat": 1742428800,
  "exp": 1774048800,
  "vct": "https://humanmoney.example/credentials/TrustList/v1",
  "_sd_alg": "sha-256",
  "version": 12,
  "entries": [
    { "...": "<digest-1>" },
    { "...": "<digest-2>" },
    { "...": "<digest-3>" }
  ],
  "cnf": {
    "jwk": { "kty": "OKP", "crv": "Ed25519", "x": "..." }
  }
}
```

**Disclosures** (getrennt transportiert, pro Eintrag ein Disclosure):

```text
WyJfcWIyX0hOMTYybFJhVG5PIiwgImVudHJ5IiwgeyJpZCI6ImRpZDprZXk6ejZNay4uLmJvYiIsInRydXN0TGV2ZWwiOjMsImxpYWJpbGl0eSI6IjQuMGgiLCJob3BMaW1pdCI6Mn1d
```

Dekodiert (Base64URL):

```json
["_qb2_HN162lRaTnO", "entry", {
  "id": "did:key:z6Mk...bob",
  "trustLevel": 3,
  "liability": "4.0h",
  "hopLimit": 2
}]
```

**SD-JWT-Compact-Serialization:** Das signierte JWT und die Disclosures werden durch `~` getrennt konkateniert:

```text
<JWT>~<disclosure-1>~<disclosure-2>~<disclosure-3>~
```

Der Sender wählt pro Empfänger aus, welche Disclosures er mitsendet. Weggelassene Disclosures sind für den Empfänger unsichtbar — die Signatur bleibt gültig, weil der Hash im JWT-Payload steht.

**Verteilung:** Im Gegensatz zu qualitativen Attestations (Empfängerprinzip) verteilt der **Sender** seine Trust List aktiv via Gossip an sein Netzwerk. Jeder Knoten leitet die Liste unter Beachtung der Hop-Limits weiter. Konkrete Gossip-Mechanik siehe [H03](H03-gossip.md).

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

## Referenzen

- [IETF SD-JWT-based Verifiable Credentials](https://datatracker.ietf.org/doc/draft-ietf-oauth-sd-jwt-vc/) — Normatives Format für gebündelte Trust-Lists
- [IETF SD-JWT](https://datatracker.ietf.org/doc/draft-ietf-oauth-selective-disclosure-jwt/) — Selective-Disclosure-Mechanik (Basis für SD-JWT VC)
- [W3C VC Data Model 2.0](https://www.w3.org/TR/vc-data-model-2.0/) — Normatives Format für einzelne Trust-Attestations
- [H03 Gossip-Propagation](H03-gossip.md) — Wie Trust-Lists via Inbox verteilt werden
- Sebastians ADRs im [humoco-web-of-trust](https://github.com/minutogit/humoco-web-of-trust) — Detailanalysen zu Propagation, Reziprokem Routing, Spieltheorie

## Zu klären

- Detaillierte Spec der Trust-Berechnung (mit Sebastian)
- Spieltheoretische Analyse der Hop-Limits (Sebastian hat Material in docs/research)
- Integration von `cnf` (Key-Binding): soll der Holder einen eigenen Key haben, oder ist Key-Binding für unseren Use Case überflüssig?
- ~~Passt das VC-Format für seine SD-JWT-Listen?~~ → Ja, wir nutzen SD-JWT VC (2026-04-19)
- ~~Gossip-Protokoll: könnte es über unseren Broker/Sync laufen statt nur P2P?~~ → Ja, siehe [H03 Gossip-Propagation](H03-gossip.md)
