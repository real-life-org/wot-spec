# Interoperabilität, Zielgruppe und Standards

> **Nicht normativ:** Dieses Dokument ist Hintergrund, Analyse oder Planung. Normative Anforderungen stehen in den Spec-Dokumenten und in `CONFORMANCE.md`.

*Stand: 17. April 2026*

## Was ist unser Protokoll?

Ein Protokoll für dezentrale Vertrauensnetzwerke basierend auf echten Begegnungen. Zwei Menschen treffen sich, verifizieren ihre Identität, und stellen sich gegenseitig signierte Aussagen aus — kryptographisch verifizierbar, offline-fähig, ohne zentrale Instanz.

Sybil-Resistenz kommt aus dem Netzwerk, nicht vom Staat.

## Zwei Welten der digitalen Identität

### Staatliche Identität (Top-Down)

Die EU rollt bis Ende 2026 die European Digital Identity Wallet (EUDIW) aus. Jeder Mitgliedsstaat muss mindestens eine zertifizierte Wallet bereitstellen. Die technische Basis:

- **OpenID4VP** — Verifiable Presentations vorzeigen
- **OpenID4VCI** — Credentials ausstellen
- **SD-JWT + mdoc** — Credential-Formate
- **Client-Server-Architektur** — Verifier fragt, Wallet antwortet

Sybil-Resistenz kommt vom Staat: deine eID beweist dass du existierst, weil der Staat das sagt.

**Kritik (Stand April 2026):**
- Digitale Rechtsgruppen warnen in einem offenen Brief vor geschwächtem Datenschutz
- Zentraler persistenter Identifier ermöglicht Tracking über alle Interaktionen
- Artikel 45/45a: Browser müssen staatliche Zertifikate akzeptieren, auch bei Sicherheitsproblemen
- Der Staat kann deine digitale Identität widerrufen — sie wird abschaltbar
- epicenter.works: "unprecedented risk for privacy"

### Dezentrale Identität (Bottom-Up)

Vertrauen entsteht zwischen Menschen, nicht durch Institutionen. Keine zentrale Autorität stellt Credentials aus — Menschen attestieren einander. DID + Verifiable Credentials + P2P Sync.

Sybil-Resistenz kommt aus dem Netzwerk: echte Begegnungen, transitive Vertrauenspfade, multiplikative Dämpfung.

**Stärken:** Nicht abschaltbar, zensurresistent, offline-fähig, keine Überwachungsinfrastruktur.

**Schwächen:** Schwächere Sybil-Garantie als staatliche ID, langsamer Netzwerkaufbau, keine regulatorische Anerkennung.

## Messaging-Standards

### DIDComm v2 (DIF)

P2P-Messaging zwischen DIDs. Transport-agnostisch, offline-fähig, E2EE.

- **Spec-Status:** DIF Ratified Specification (v2.1)
- **Adoption:** Gering. Hyperledger Aries migriert noch von v1 auf v2. Keine große App nutzt v2 produktiv. Die EU hat sich für OpenID4VC entschieden, nicht DIDComm.
- **Implementierungen:** Rust (didcomm-rs), JavaScript, Kotlin/Swift (DIDComm-gRPC)
- **Stärke:** Echtes P2P, offline, zensurresistent, automatisierte Flows möglich
- **Schwäche:** Komplexe Spec, kleines Ökosystem, keine EU-Adoption

### OpenID4VC (OpenID Foundation)

Drei Protokolle auf Basis von OpenID Connect: OpenID4VCI (Credentials ausstellen), OpenID4VP (Credentials vorzeigen), SIOPv2 (Self-Issued Identity).

- **Spec-Status:** Final (v1.0), Selbstzertifizierung seit Februar 2026
- **Adoption:** Massiv. EU-Regulierung treibt Adoption. 500 Millionen EU-Bürger bis Ende 2026.
- **Stärke:** Riesiges Ökosystem, Web-kompatibel, regulatorische Rückendeckung
- **Schwäche:** Client-Server (nicht P2P), User muss in der Schleife sein, nicht offline-fähig, ermöglicht Überwachung

### Vergleich für unseren Kontext

| | DIDComm v2 | OpenID4VC | Unser Protokoll |
|---|---|---|---|
| Architektur | P2P | Client-Server | P2P |
| Offline-fähig | Ja | Nein | Ja |
| Zensurresistent | Ja | Nein (Server nötig) | Ja |
| EU-Wallet kompatibel | Nein | Ja | Nein |
| Gruppen-Encryption | Nein | Nein | Ja |
| Komplexität | Hoch | Mittel | Niedrig |
| Adoption | Nische (SSI) | Mainstream (EU) | Nur wir |

DIDComm teilt unsere Werte (P2P, offline, dezentral). OpenID4VC ist für die Welt die wir als Alternative bauen.

## Überlappung: Unser Protokoll und DIDComm

Wir haben im Kern ein eigenes DIDComm gebaut:

| Unser Konzept | DIDComm-Äquivalent |
|---|---|
| Message Envelope (JWS) | DIDComm Plaintext + Signed Message |
| ECIES-Verschlüsselung | DIDComm Authcrypt (ECDH-1PU) |
| Broker (Store-and-Forward) | DIDComm Mediator |
| Inbox-Nachrichten | DIDComm Messages |
| Challenge-Response | DIDComm Protocol |

DIDComm könnte unseren **Inbox-Kanal** ersetzen (1:1-Nachrichten: Attestations, Einladungen, Verifikation). Der **Log-Sync** (CRDT-Replikation) hat kein DIDComm-Äquivalent — das bleibt unser eigenes Protokoll.

## Projekte die ein WoT brauchen

### Ring 1: Gemeinschafts-Ökonomie (Kern-Zielgruppe)

**Circles UBI (Gnosis)** — Community-Währung mit WoT-basierter Sybil-Resistenz. V2 seit Mai 2025 live. Problem: sozialer Graph ist öffentlich auf der Blockchain. Arbeiten am "Entropy Project" für private Graphen. Unser Ansatz (E2EE) löst genau dieses Problem.

**Human Money Core (Sebastian)** — Gutschein-basiertes Payment mit quantitativen Trust-Scores. Nutzt bereits did:key + Ed25519. Teilt unsere Spec.

**Community-Währungen allgemein** (Minuto, Chiemgauer, etc.) — Brauchen Sybil-Resistenz für faire Verteilung. Aktuell meist papierbasiert oder zentralisiert.

**Solidarische Landwirtschaft / FoodCoops** — Vertrauensnetzwerke für Mitgliederverwaltung ohne zentrale Plattform.

### Ring 2: Dezentrale Soziale Netzwerke

**Nostr** — Wachsendes WoT-Ökosystem: NIP-101 (Trust System), trust.nostr.band (PageRank), WoT-a-thon Hackathon (April 2026). Follow-basiert (nicht begegnungsbasiert), aber gleiche Richtung: Spam-Resistenz ohne zentrale Autorität.

**Scuttlebutt / Manyverse** — Architektonisch fast identisch (Offline-first, P2P, Append-only Logs, Gossip). Kleines Ökosystem, Entwicklung verlangsamt.

**Briar** — Offline-Messenger für Aktivisten. In-Person-Verifikation vorhanden, aber kein transitives Vertrauen.

**Matrix/Element** — Dezentrales Messaging mit Schlüssel-Verifikation, aber kein WoT darüber.

### Ring 3: Die eIDAS-Alternative (Langfristig)

Menschen die bewusst eine dezentrale Alternative zur staatlichen digitalen Identität wollen. Wachsende Nische — besonders wenn eIDAS die erwarteten Probleme erzeugt (Datenlecks, autoritärer Missbrauch, Zensur).

Vergleichbar mit Signal als Alternative zu WhatsApp nach Snowden: klein, aber prinzipientreu und wachsend.

## Das Proof-of-Personhood-Feld

Unser WoT ist eine Antwort auf dieselbe Frage die alle Proof-of-Personhood-Projekte stellen: "Wie beweist du dass du ein echter Mensch bist?"

| Projekt | Methode | Dezentral? | Privacy? |
|---|---|---|---|
| **World (Worldcoin)** | Iris-Scan mit Orb-Hardware | Nein (proprietäre Hardware) | Problematisch (Biometrie-Daten) |
| **Human Passport (Gitcoin)** | Multi-Faktor (Social, Biometrie, Staat) | Teilweise | Mittel |
| **BrightID** | Soziale Graphen | Ja | Nein (öffentlicher Graph) |
| **Polkadot PoP** | Zero-Knowledge Proofs | Ja | Ja |
| **Idena** | Puzzle-Zeremonien | Ja | Ja |
| **Unser WoT** | Echte Begegnungen + Trust-Graph | Ja | Ja (E2EE) |

Unser Differenzierungsmerkmal: **E2EE + Offline-First + echte Begegnungen**. Kein anderes Projekt kombiniert alle drei.

## Der gesellschaftliche Kontext

Die EU-Wallet kommt Ende 2026. Der Diskurs wird sich verschärfen:

**Phase 1 (2026-2027): Einführung** — Pflicht zur Akzeptanz durch Dienste. Erste Datenschutz-Beschwerden. Technische Probleme.

**Phase 2 (2027-2028): Normalisierung** — "Zeig deinen Ausweis" wird digital. Gewöhnung. Aber auch: erste Fälle von Missbrauch, Tracking, Diskriminierung.

**Phase 3 (2028+): Gegenreaktion** — "Gibt es eine Alternative?" Parallelen zu den Crypto-Wars, zu Signal nach Snowden, zu Tor nach Wikileaks. Hier wird unser WoT relevant — als technisch fundierte, dezentrale Alternative.

Wir müssen nicht die Massen überzeugen. Wir müssen bereit sein wenn die Massen fragen.

## Offene Fragen

- **DIDComm-Timing:** Wann lohnt sich die Integration? Wenn ein konkretes Projekt (Circles, Nostr, Briar) mit uns interoperieren will? Oder proaktiv?
- **Credential-Format-Brücke:** Können wir unsere W3C VCs so formatieren dass sie auch in einer EU-Wallet anzeigbar wären? (Nicht als Ersatz, sondern als Ergänzung)
- **Nostr-Brücke:** Nostr's WoT (follow-basiert) und unser WoT (begegnungsbasiert) — können sie sich gegenseitig stärken?
- **Circles-Brücke:** Können wir Circles' öffentlichen Trust-Graph durch unser E2EE-Modell ersetzen?

## Quellen

- [DIDComm v2 Spec](https://identity.foundation/didcomm-messaging/spec/v2.0/)
- [DIDComm v2 Approved Status](https://blog.identity.foundation/didcomm-v2/)
- [OpenID4VC](https://openid.net/sg/openid4vc/)
- [EUDIW Resource Hub](https://openid.net/openid-foundation-launches-eudiw-resource-hub/)
- [eIDAS Privacy Concerns (epicenter.works)](https://epicenter.works/en/content/european-electronic-id-without-privacy-safeguards)
- [eIDAS Privacy Concerns (offener Brief)](https://cadeproject.org/updates/digital-rights-groups-warn-eu-over-privacy-risks-in-new-eidas-rules/)
- [Circles UBI Whitepaper](https://handbook.joincircles.net/docs/developers/whitepaper/)
- [Circles v2 Launch](https://www.theblock.co/post/355133/circles-v2-launches-martin-koppelmann-gnosis-dao)
- [Nostr WoT](https://nostr-wot.com/)
- [NIP-101 Decentralized Trust](https://github.com/papiche/NIP-101)
- [BrightID / Proof of Personhood Alternativen](https://analyticsindiamag.com/ai-trends/6-worldcoin-alternatives-you-should-know/)
- [Vitalik: Biometric Proof of Personhood](https://vitalik.eth.limo/general/2023/07/24/biometric.html)
- [Proof of Personhood 2026](https://academy.exmon.pro/proof-of-personhood-2026-crypto-vs-deepfakes-ai-agents)
