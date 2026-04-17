# DIDComm v2 Migration — Analyse und Roadmap

*Stand: 17. April 2026*

## Was ist DIDComm?

DIDComm v2 ist ein Messaging-Protokoll der Decentralized Identity Foundation (DIF) für sichere, private Kommunikation zwischen DIDs. Man kann es sich als TCP/IP für dezentrale Identität vorstellen — ein Transportlayer auf dem höhere Protokolle aufbauen.

Kernprinzipien:
- **Message-basiert, asynchron** — kein Request-Response, kein Server nötig
- **Transport-agnostisch** — WebSocket, HTTP, Bluetooth, QR-Code, USB-Stick
- **Message-Level Security** — Verschlüsselung ist in der Nachricht, nicht im Transport (anders als TLS)
- **Offline-fähig** — Nachrichten werden gespeichert und zugestellt wenn der Peer online kommt

## Warum DIDComm für unser WoT?

### Architektonische Übereinstimmung

DIDComm teilt unsere Werte: P2P, offline-fähig, dezentral, keine zentrale Autorität. Es ist das Gegenstück zu OpenID4VC (EU-Wallet, Client-Server, staatlich).

### Interoperabilität

Ohne DIDComm ist jedes dezentrale Projekt eine Insel. Mit DIDComm können verschiedene Apps denselben Vertrauensgraphen teilen:

- Eine Community-Währung (Circles) könnte WoT-Attestations als Sybil-Resistenz nutzen
- Ein dezentraler Messenger (Briar) könnte WoT-Verifikation für Kontakte nutzen
- Ein Nostr-Client könnte WoT-Trust-Scores als Spam-Filter nutzen

Alle über dasselbe Messaging-Protokoll, ohne bilaterale Integrationen.

### Zukunftssicherheit

DIDComm ist ein aktiv gepflegter Standard (v2.1, v2.2 in Arbeit) mit formaler Sicherheitsanalyse (ACM CCS 2024). Wenn das dezentrale Ökosystem wächst — besonders als Reaktion auf eIDAS — ist DIDComm der Standard der bereit steht.

## Aktueller Stand unserer Kompatibilität

### Was wir haben (~60%)

| Schicht | Status | Details |
|---|---|---|
| Plaintext Message Format | Kompatibel | `id`, `type` (URI), `from`, `to`, `body` |
| JWS Signaturen | Kompatibel | Identisch mit DIDComm Signed Messages |
| Krypto-Primitive | Kompatibel | X25519, AES-256-GCM, Ed25519 |
| Authcrypt-Verfahren | Spezifiziert | ECDH-1PU, Web Crypto API |
| Type-URIs | Kompatibel | `https://wot.example/protocols/.../1.0` |

### Was fehlt (~40%)

| Schicht | Aufwand | Beschreibung |
|---|---|---|
| JWE-Verpackung | Mittel | JSON-Struktur um Authcrypt-Ergebnis, ~300 Bytes Overhead |
| DID-Dokumente | Mittel | Service-Endpoints für Mediator-Routing |
| Message Threading | Niedrig | `thid` und `pthid` Felder ergänzen |
| Trust Ping | Niedrig | "Bist du da?" — einfaches Request-Response |
| Discover Features | Niedrig | "Welche Protokolle unterstützt du?" |
| Forward/Routing | Hoch | Doppelte Verschlüsselungsschicht für Mediator-Privacy |
| Mediator Coordination | Mittel | Formales Registrierungsprotokoll |

## Was jeder fehlende Teil konkret bedeutet

### JWE-Verpackung

Unsere Authcrypt-Berechnung (ECDH-1PU) ist spezifiziert. Was fehlt ist das Standard-Envelope:

```json
{
  "protected": "<Base64URL: { alg: 'ECDH-1PU+A256KW', enc: 'A256GCM', skid, apu, apv, epk }>",
  "recipients": [
    {
      "header": { "kid": "did:key:z6Mk...#key-x25519-1" },
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
    { "id": "#key-x25519-1", "type": "X25519KeyAgreementKey2020", "publicKeyMultibase": "z6LS..." }
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
  {"feature-type": "protocol", "id": "https://wot.example/protocols/space-invite/1.0"},
  {"feature-type": "protocol", "id": "https://wot.example/protocols/trust-list-delta/1.0"}
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

**Phase 1 (jetzt): Spec-Kompatibilität**
- Plaintext Message Format ✅
- Type-URIs ✅
- JWS Signaturen ✅
- Authcrypt (ECDH-1PU) ✅

**Phase 2 (nächster Schritt): Vollständige Interop**
- JWE-Verpackung spezifizieren
- DID-Dokumente mit Service-Endpoints
- Threading-Felder
- Trust Ping + Discover Features
- Interop-Test gegen SICPA-Library

**Phase 3 (Zukunft): Erweiterte Features**
- Forward/Routing (Mediator-Privacy)
- Mediator Coordination Protocol
- Out-of-Band Protocol (DIDComm-konformer QR-Code)

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
