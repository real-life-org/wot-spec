# DIDComm v2 Migration — Analyse und Roadmap

*Stand: 24. April 2026*

## Was ist DIDComm?

DIDComm v2 ist ein Messaging-Protokoll der Decentralized Identity Foundation (DIF) für sichere, private Kommunikation zwischen DIDs. Man kann es sich als TCP/IP für dezentrale Identität vorstellen — ein Transportlayer auf dem höhere Protokolle aufbauen.

Kernprinzipien:
- **Message-basiert, asynchron** — kein Request-Response, kein Server nötig
- **Transport-agnostisch** — WebSocket, HTTP, Bluetooth, QR-Code, USB-Stick
- **Message-Level Security** — Verschlüsselung ist in der Nachricht, nicht im Transport (anders als TLS)
- **Offline-fähig** — Nachrichten werden gespeichert und zugestellt wenn der Peer online kommt

## Warum DIDComm für unser WoT? — ehrliche Einordnung

### Was DIDComm wirklich bringt

**Design-Disziplin und konzeptionelle Klarheit:**
DIDComm ist ein durchdachter Stack mit klarer Layer-Trennung (Envelope / Protokoll / Anwendung), formaler Security-Analyse (ACM CCS 2024) und einem durchdachten Threading-Modell. Wer DIDComm-konform spezifiziert, vermeidet viele typische Fehler.

**Library-Kompatibilität für die SSI-Nische:**
`didcomm-rust`/`didcomm-node` (SICPA) und Veramo DIDComm existieren und werden gepflegt. Unser Anspruch ist aktuell enger: WoT-Plaintext-Envelopes sollen von diesen Bibliotheken geparst und geroutet werden koennen. Verschluesselung und signierte WoT-Envelopes beanspruchen derzeit keine volle DIDComm-Wire-Kompatibilitaet.

**Architektonische Übereinstimmung:**
DIDComm teilt unsere Werte: P2P, offline-fähig, dezentral, keine zentrale Autorität. Das macht DIDComm zu einem natürlichen Envelope-Standard für uns.

### Was DIDComm NICHT bringt — Mythen und Realität

**🚫 Kein EU-Wallet-Interop:**
Die eIDAS 2.0 Architecture Reference Framework hat sich gegen DIDComm entschieden. Die gewählten Protokolle sind **OpenID4VCI** (Ausstellung) und **OpenID4VP** (Präsentation) — beide OAuth-2.0-basiert, nicht DIDComm-basiert. Als Credential-Format ist **SD-JWT VC** (oder ISO mDL) vorgesehen.

Heißt: DIDComm-Compliance ist kein Ticket in den EU-Wallet-Stack. SD-JWT-VC-Compliance ist es.

**🚫 Kein Mainstream-Messaging-Interop:**
Matrix, Nostr, Signal, WhatsApp, ActivityPub nutzen alle eigene Protokolle. DIDComm hat dort keine Traktion.

**🚫 Kein Crypto/Web3-Interop:**
Ethereum-Ökosystem nutzt EIP-191/712, WalletConnect, custom Flows. DIDComm ist dort kein Thema.

**🚫 Kein Banking/Finance-Interop:**
ISO 20022 und Swift sind dort Standard. DIDComm taucht nicht auf.

### Wo Interop wirklich entsteht — auf Format-Ebene

Die echte Interop-Schicht sind **Datenformate und Identitäts-Primitive**, nicht Exchange-Protokolle:

| Baustein | Akzeptanz |
|---|---|
| DID:key + Ed25519 | SSI-Wallets, EU-Wallet, W3C-VC-Ökosystem, viele Crypto-Apps |
| W3C VC Data Model 2.0 | SSI-Wallets, EU-Wallet, OpenID4VC, Aries |
| SD-JWT VC | EU-Wallet (Pflicht), OpenID4VC, einige SSI-Wallets |
| JWS Compact | JOSE-Ökosystem, OpenID4VC, Aries |

Wenn wir auf diesen Ebenen die richtigen Wahlen treffen, sind wir auch dann interoperabel, wenn unser Exchange-Protokoll DIDComm ist und das Gegenüber OpenID4VC spricht. Die Daten lassen sich über Gateways/Bridges transformieren — die Identitäts- und Credential-Formate bleiben identisch.

### Was wir daraus konkret ableiten

- **Envelope-Ebene: DIDComm-Plaintext-kompatibel bleiben** — billig, gibt uns Aries-Nischen-Interop und Design-Disziplin
- **Format-Ebene: SD-JWT VC adoptieren** — für Trust-Lists (H01) und als Option für Attestations. Das ist der strategisch wichtige Interop-Baustein.
- **NICHT verfolgen: Forward Routing, Mediator Coordination, Pickup Protocol** — das sind Aries-spezifische Protokolle für Enterprise-Mediator-Szenarien, die uns Komplexität einbringen ohne klaren Gewinn für unser P2P-Modell.
- **NICHT verfolgen als Haupt-Pfad: Issue Credential 3.0, Present Proof 3.0 über DIDComm** — hier läuft der Mainstream über OpenID4VC. Wenn wir breitere Exchange-Interop wollen, wäre OpenID4VCI/VP strategisch wichtiger.

### Zukunftssicherheit — vorsichtiger formuliert

DIDComm ist aktiv gepflegt (v2.1 Work in Progress), hat formale Sicherheitsanalyse und eine etablierte Nische im SSI-Sektor. Wenn das dezentrale Ökosystem außerhalb des staatlich geprägten eIDAS-Pfads wächst, **könnte** DIDComm weiter an Bedeutung gewinnen. Das ist keine Gewissheit, aber eine plausible Wette.

Gleichzeitig: selbst wenn DIDComm nicht zum breiten Standard wird, verlieren wir wenig — der Plaintext-Envelope ist klein, und unsere echte Interop hängt an den Format-Standards, nicht am Envelope.

## Aktueller Stand unserer Kompatibilität

Wir verfolgen **selektive DIDComm-Compliance** auf Envelope- und Utility-Ebene, nicht volle Compliance. Die folgenden Tabellen zeigen, was spezifiziert ist und was bewusst nicht verfolgt wird.

### Was spezifiziert ist

| Schicht | Status | Details |
|---|---|---|
| Plaintext Message Format | Library-validiert kompatibel | `id`, `typ`, `type` (URI), `from`, `to`, `created_time`, `body` ([Sync 007](../02-wot-sync/007-transport-und-broker.md#message-envelope-didcomm-kompatibel)); validiert mit `didcomm-node` und `@veramo/did-comm` |
| JWS Signaturen | WoT-Profil | JWS Compact fuer persistente WoT-Daten. Signierte WoT-Envelopes sind strukturell an DIDComm angelehnt, aber noch nicht als DIDComm Signed Messages library-validiert. |
| Krypto-Primitive | Kompatibel | X25519, AES-256-GCM, Ed25519 |
| Verschlüsselung | Eigenes Profil (ECIES) | ECIES statt DIDComm Authcrypt (ECDH-1PU). Begründung: siehe [Sync 005](../02-wot-sync/005-verschluesselung.md#warum-ecies-statt-didcomm-authcrypt) |
| Type-URIs | Kompatibel | `https://web-of-trust.de/protocols/.../1.0` |
| Message Threading | **Spezifiziert (2026-04-19)** | `thid` und `pthid` optional im Envelope ([Sync 007](../02-wot-sync/007-transport-und-broker.md#threading)) |
| Trust Ping | Entfernt (2026-04-22) | Presence-Abfrage über Broker, nicht per Peer-Ping |
| Discover Features | Entfernt (2026-04-22) | Feature-Discovery über `protocols`-Feld im Profil ([Sync 008](../02-wot-sync/008-discovery.md)) |

### Was wir bewusst NICHT verfolgen

| Baustein | Warum nicht |
|---|---|
| Forward/Routing (Onion) | Aries-Enterprise-Pattern für Mediator-Anonymität. Unsere Broker-Architektur ist P2P-orientiert, Forward-Routing würde Komplexität bringen ohne klaren Gewinn. |
| Mediator Coordination 2.0 | Formales Registrierungsprotokoll für Aries-Mediator-Setups. Unser Challenge-Response-Flow deckt das einfacher ab. |
| Pickup Protocol 2.0 | Inbox-Retrieval im Aries-Stil. Wir haben äquivalente Funktionalität mit anderer Semantik. |
| Issue Credential 3.0 | DIDComm-Flow für Credential-Ausstellung. Für breite VC-Interop wäre OpenID4VCI strategisch wichtiger. |
| Present Proof 3.0 | DIDComm-Flow für VP-Präsentation. Für breite VC-Interop wäre OpenID4VP strategisch wichtiger. |

### Offene Bausteine (optional, nicht blockierend)

| Baustein | Status |
|---|---|
| DID-Dokumente mit Service-Endpoints | Offen — relevant wenn wir externe DIDComm-Agenten erreichen wollen |
| Interop-Test gegen SICPA `didcomm-rust` | Offen — praktische Verifikation |
| Problem Report 2.0 | Offen — strukturierte Fehler, würde unsere Ad-hoc-Errors ersetzen |
| Out-of-Band 2.0 | Offen — standardisiertes QR-Code-Invitation-Format (potentiell relevant für Core 004) |

## Was jeder fehlende Teil konkret bedeutet

### JWE-Verpackung

Unsere Authcrypt-Berechnung (ECDH-1PU) ist spezifiziert. Was fehlt ist das Standard-Envelope:

```json
{
  "protected": "<Base64URL: { alg: 'ECDH-1PU+A256KW', enc: 'A256GCM', skid, apu, apv, epk }>",
  "recipients": [
    {
      "header": { "kid": "did:key:z6Mk..." },
      "encrypted_key": "<Base64URL: Wrapped Content Encryption Key>"
    }
  ],
  "iv": "<Base64URL: 12-Byte Nonce>",
  "ciphertext": "<Base64URL: Verschlüsselter Inhalt>",
  "tag": "<Base64URL: Auth Tag>"
}
```

**Overhead:** ~300-400 Bytes pro Nachricht. Nur Inbox-Kanal betroffen. Weniger als 1% des Gesamtdatenvolumens.

**Implementierung:** Kein neuer Krypto-Code — nur JSON-Konstruktion um das bestehende Authcrypt-Ergebnis. Web Crypto API reicht.

### DID-Dokumente mit Service-Endpoints

DIDComm braucht ein DID-Dokument das sagt wo der Mediator (Broker) erreichbar ist:

```json
{
  "id": "did:key:z6Mk...alice",
  "authentication": [
    { "id": "#key-1", "type": "Ed25519VerificationKey2020", "publicKeyMultibase": "z6Mk..." }
  ],
  "keyAgreement": [
    { "id": "#enc-1", "type": "X25519KeyAgreementKey2020", "publicKeyMultibase": "z6LS..." }
  ],
  "service": [{
    "id": "#didcomm-1",
    "type": "DIDCommMessaging",
    "serviceEndpoint": {
      "uri": "wss://broker.example.com",
      "routingKeys": []
    }
  }]
}
```

Bei `did:key` werden die Key-Sektionen synthetisch aus dem Key generiert. Der Service-Endpoint kommt aus:
- Dem Profil-Service (Sync 008)
- Der Space-Einladung (bei erstmaligem Kontakt)
- Dem QR-Code bei In-Person-Verifikation (Core 004)

### Message Threading

Zwei optionale Felder im Plaintext Message:

```json
{
  "id": "uuid",
  "type": "...",
  "thid": "uuid-des-ersten-messages-im-thread",
  "pthid": "uuid-des-parent-threads",
  "body": { ... }
}
```

Ermöglicht mehrstufige Konversationen (z.B. Einladung → Annahme → Bestätigung) als zusammenhängenden Thread.

### Trust Ping

```
Alice → Bob: { "type": ".../trust-ping/2.0", "body": { "response_requested": true } }
Bob → Alice: { "type": ".../trust-ping/2.0", "body": {} }
```

Verifiziert dass die Verschlüsselung funktioniert und der Peer erreichbar ist. ~100 Bytes Payload.

### Discover Features

```
Alice → Bob: { "type": ".../discover-features/2.0", "body": { "queries": [{"feature-type": "protocol"}] } }
Bob → Alice: { "type": ".../discover-features/2.0", "body": { "disclosures": [
  {"feature-type": "protocol", "id": "https://web-of-trust.de/protocols/space-invite/1.0"},
  {"feature-type": "protocol", "id": "https://web-of-trust.de/protocols/trust-list-delta/1.0"}
] } }
```

Ermöglicht einem Peer herauszufinden welche Protokolle der andere unterstützt. Wichtig für Interop — wenn eine externe App sich verbindet, kann sie fragen: "Sprichst du WoT?"

Privacy-Feature: Protokoll-Support wird nur auf Anfrage offengelegt, nicht öffentlich im DID-Dokument publiziert (verhindert Fingerprinting).

### Forward/Routing (Zukunft)

Doppelte Verschlüsselungsschicht: äußere für den Mediator (wohin liefern), innere für den Empfänger (Inhalt).

```
Ohne Forward (aktuell):
  Mediator sieht: from, to, type, created_time
  Mediator sieht nicht: body

Mit Forward:
  Mediator sieht: "deliver to did:key:bob"
  Mediator sieht nicht: from, type, created_time, body
```

Privacy-Gewinn: versteckt wer sendet und welchen Typ die Nachricht hat. Nicht blockierend für Interop innerhalb unseres Ökosystems (gleicher Broker). Relevant für Interop mit externen DIDComm-Mediators.

### Mediator Coordination (Zukunft)

Standardisiertes Protokoll für die Registrierung bei einem Mediator:
- **Mediate Request** → "Bitte sei mein Mediator"
- **Mediate Grant** → "OK"
- **Keylist Update** → "Meine aktuellen Keys"

Unser Challenge-Response + Capability-Flow ist funktional äquivalent. Migration wäre eine Übersetzung, keine Neuentwicklung.

## Sicherheitsanalyse (ACM CCS 2024)

Die erste formale Sicherheitsanalyse von DIDComm wurde 2024 publiziert (Badertscher, Banfi et al.). Zentrale Erkenntnisse:

**Positiv:**
- Die Kryptografie ist grundsätzlich solide
- Authcrypt bietet Authentizität und Vertraulichkeit

**Gefundene Schwächen:**
- DIDComm leakt die Empfänger-Identifiers (Recipients sind im JWE-Header sichtbar)
- Der kombinierte Modus (Anoncrypt+Authcrypt) garantiert nicht dass Ciphertexts an eine Nachricht gebunden sind

**Vorgeschlagene Verbesserung:**
- Ein optimierter Algorithmus der Anonymität und Authentizität gleichzeitig erreicht
- Bessere Performance als der aktuelle Vorschlag (fast Faktor 2 bei Ciphertext-Größe und Rechenzeit)
- Wurde in die Spec-Diskussion eingebracht

Für uns relevant: die Schwächen betreffen hauptsächlich den Forward/Routing-Fall (Anonymität des Senders). Für unseren aktuellen Use Case (bekannte Peers, eigener Broker) sind sie nicht kritisch.

## Implementierungsstrategie

### Bibliotheken vs. Eigenimplementierung

**Eigenimplementierung (empfohlen für TypeScript/Browser):**
- Alles mit Web Crypto API machbar
- Keine externen Abhängigkeiten
- Volle Kontrolle
- Testen gegen SICPA-Library für Interop-Verifikation

**SICPA `didcomm-rs` (empfohlen für Rust/Sebastian):**
- Ausgereifteste DIDComm-Implementierung
- Rust-native, gute Performance
- Aktiv gepflegt

### Roadmap

**Phase 1 (aktueller Stand): Plaintext-Envelope-Kompatibilitaet**
- Plaintext Message Format mit `typ: "application/didcomm-plain+json"` ✅
- Type-URIs ✅
- Threading-Felder (`thid`, `pthid`) ✅
- Interop-Test gegen SICPA `didcomm-node` und Veramo DIDComm ✅

**Nicht als DIDComm-Wire-Kompatibilitaet beansprucht:**
- JWE/Authcrypt — bewusst durch ECIES ersetzt
- DIDComm Signed Messages — WoT nutzt JWS Compact, aber erhebt erst nach eigenen Library-Tests einen Kompatibilitaetsanspruch
- Trust Ping / Discover Features — durch Broker-Presence und Profil-`protocols` ersetzt

**Phase 2 (optional, nicht blockierend):**
- Out-of-Band 2.0 als QR-Code-Format in Core 004 (Interop-Baustein, klein)
- Problem Report 2.0 (strukturierte Fehler)
- Library-validierte Signed-Envelope-Testvektoren, falls wir DIDComm-Signed-Kompatibilitaet beanspruchen wollen
- DID-Dokumente mit Service-Endpoints (falls externe DIDComm-Agenten adressiert werden sollen)

**Bewusst nicht auf der Roadmap:**
- Forward/Routing (Mediator-Privacy)
- Mediator Coordination Protocol
- Pickup Protocol 2.0
- Issue Credential 3.0 / Present Proof 3.0 (für VC-Interop ist OpenID4VC der strategische Pfad)

Siehe "Was wir bewusst NICHT verfolgen" oben für Begründung.

## Nicht betroffen von DIDComm

| Komponente | Warum nicht |
|---|---|
| Log-Sync (CRDT-Replikation) | DIDComm ist Messaging, nicht Datenreplikation |
| Space Keys (Gruppen-Encryption) | DIDComm hat kein Gruppen-Konzept |
| Capabilities | Anwendungsspezifisch, nicht Transport |
| BIP39 Seed / Key-Derivation | DIDComm ist Key-agnostisch |
| W3C VCs (Attestations) | Werden transportiert, nicht verändert |

DIDComm betrifft nur den **Inbox-Kanal** (1:1-Nachrichten). Das Gros unseres Protokolls (Sync, Gruppen, Verschlüsselung) bleibt unverändert.

## Quellen

- [DIDComm v2 Spec](https://identity.foundation/didcomm-messaging/spec/v2.0/)
- [DIDComm v2.1 Spec](https://identity.foundation/didcomm-messaging/spec/v2.1/)
- [DIDComm Book](https://didcomm.org/book/v2/)
- [Trust Ping 2.0](https://didcomm.org/trust-ping/2.0/)
- [Discover Features 2.0](https://didcomm.org/discover-features/2.0/)
- [SICPA DIDComm Rust](https://github.com/sicpa-dlab/didcomm-rust)
- [Sicherheitsanalyse ACM CCS 2024](https://dl.acm.org/doi/10.1145/3658644.3690300)
- [DIDComm gets formal (IOHK)](https://iohk.io/en/blog/posts/2024/10/16/didcomm-gets-formal/)
- [DIF DIDComm Working Group](https://identity.foundation/working-groups/did-comm.html)
