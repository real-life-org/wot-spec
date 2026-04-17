# Verbreitungsstrategie — Web of Trust 2026-2031

*Stand: 17. April 2026*

## Ausgangslage

Die EU rollt Ende 2026 die European Digital Identity Wallet (EUDIW) aus. Die Kritik ist bereits laut — Datenschutzorganisationen warnen, Sicherheitsforscher protestieren, viele Menschen werden sich von Anfang an verweigern. Gleichzeitig wird "Proof of Personhood" durch AI-Bots und Deepfakes zum drängenden Problem.

Unser Web of Trust ist die dezentrale Alternative: Identität und Vertrauen basierend auf echten Begegnungen, nicht auf staatlicher Autorität. Die Frage ist nicht ob es eine Alternative braucht, sondern ob unsere bereit ist wenn die Nachfrage kommt.

## Phase 1: Das Fundament (2026-2027)

### Was in der Welt passiert

- eIDAS-Wallets werden ausgerollt. Breiter Widerstand von Anfang an — viele Menschen verweigern sich, Datenschutz-Organisationen mobilisieren, der CCC und netzpolitik.org dokumentieren Probleme.
- Die Debatte "staatliche Kontrolle vs. Selbstbestimmung" beginnt sofort, nicht erst nach einem Skandal.
- AI-generierte Identitäten werden zum realen Problem. Deepfakes, Bot-Armeen, Fake-Accounts. "Wer ist echt?" wird eine Alltagsfrage.

### Was wir tun

- Spec finalisieren (mit Sebastian) — zwei Implementierungen die nachweislich interoperieren
- DIDComm Phase 2 implementieren (JWE, DID-Dokumente) — bereit für Interop
- Erste Communities nutzen WoT aktiv (Real Life Stack, Human Money)
- Material vorbereiten: "Was ist die Alternative zu eIDAS?" — technisch fundiert, verständlich erklärt, für Menschen die sich verweigern wollen

### Schlüsselpartner

- **Sebastian / Human Money** — erster Interop-Partner, bewährt das Protokoll
- **DIF (Decentralized Identity Foundation)** — beitreten, WoT-Protokolle als DIDComm-Protokolle einreichen
- **netzpolitik.org / CCC / epicenter.works** — als technische Referenz positionieren. Die kennen das Problem, wir haben eine Antwort.

## Phase 2: Die erste Welle (2027-2028)

### Was in der Welt passiert

- Der Widerstand gegen eIDAS formiert sich. Klagen, Proteste, Boykott-Aufrufe. Erste EU-Länder machen Zugeständnisse.
- Gleichzeitig: die Probleme die eIDAS lösen soll (Online-Betrug, Fake-Accounts) verschwinden nicht. Die Frage wird: "Wie lösen wir das ohne Überwachung?"
- Nostr wächst weiter, Circles v3, Community-Währungen expandieren. Die dezentrale Bewegung wird stärker — auch politisch.

### Was wir tun

- **Circles-Integration** — Circles hat ein öffentliches Trust-Graph-Problem (alles auf der Blockchain sichtbar). Unser E2EE WoT als Privacy-Layer für Circles' Sybil-Resistenz. Circles bekommt privaten Trust, wir bekommen Zugang zu einem Netzwerk mit hunderttausenden Usern.
- **Nostr-Bridge** — WoT-Verifikation als Nostr-Feature. "Verifiziert durch Web of Trust" neben dem Profil. Nostr-Clients integrieren WoT als Plugin oder NIP.
- **Öffentliche Präsenz** — CCC Congress, FOSDEM, re:publica. "Vertrauen ohne Staat — wie ein Web of Trust funktioniert." Workshops auf Community-Treffen, FoodCoop-Versammlungen, Kooperativen-Konferenzen.

### Schlüsselpartner

- **Circles / Gnosis** — Martin Köppelmann und Team. Technisch am nächsten, gleiche Werte, komplementäres Problem
- **Nostr-Community** — über NIP-Vorschläge und Hackathons
- **OpenWallet Foundation** — die Aries-Nachfolger, DIDComm-Expertise
- **Solidarische Landwirtschaft / FoodCoop-Netzwerke** — reale Communities die Vertrauensinfrastruktur brauchen

## Phase 3: Multi-App-Ökosystem (2028-2029)

### Was in der Welt passiert

- Zwei Lager haben sich formiert: staatliche digitale Identität vs. dezentrale Alternativen. Der Diskurs ist gesellschaftlich breit angekommen.
- AI-Deepfakes sind so gut dass Video-Verifikation nicht mehr reicht. In-Person-Verifikation (unser Kernfeature) wird wertvoller.
- Mehrere dezentrale Apps suchen Sybil-Resistenz ohne Staat.

### Was wir tun

- **"WoT-kompatibel"** wird ein Label das Apps tragen — wie "Signal-Protokoll" für Messenger:

```
Messaging:    Briar + WoT-Verifikation
Sozial:       Nostr + WoT-Trust-Scores
Währung:      Circles + WoT-Sybil-Resistenz
Community:    Real Life App + WoT-Attestations
Payment:      Human Money + WoT-Trust-Levels
Marktplatz:   ??? + WoT-Reputation
Governance:   ??? + WoT-Proof-of-Personhood
```

- Ein Mensch hat **ein** Vertrauensnetzwerk das über alle Apps funktioniert. Seine Attestations, Trust-Scores und Verifikationen sind portabel — dank DIDComm und gemeinsamer DIDs.

### Schlüsselpartner

- **Briar** — Messenger für Situationen wo der Staat der Angreifer ist. WoT-Verifikation als natürliche Erweiterung.
- **Matrix/Element** — größtes dezentrales Messaging-Ökosystem. DIDComm-Bridge als Multiplikator.
- **Kooperativen-Bewegung** — Platform Cooperativism, Commons-Bewegung, Transition Towns.
- **Polkadot / Web3 Foundation** — Gavin Wood's Proof of Personhood. Unser WoT als off-chain Verifikation für on-chain Governance.

## Phase 4: Anerkennung (2029-2031)

### Was passiert

- Zwei Identitätssysteme koexistieren:
  - **Staatlich (eIDAS)** — für Behörden, Banken, regulierte Dienste
  - **Dezentral (WoT)** — für Communities, Kooperativen, bürgerliche Freiheit
- Manche Menschen nutzen beides. Manche nur eins. Die Wahl zu haben ist der Punkt.
- WoT-Verifikation wird so normal wie ein Schlüsselaustausch bei Signal. Bei der ersten Begegnung: QR-Code scannen, verifiziert, fertig.
- Die DIF erkennt WoT als DIDComm-Protokollfamilie an. Akademische Forschung untermauert die Sybil-Resistenz formal.

### Schlüsselpartner

- **Akademische Forschung** — formale Analyse des Trust-Propagation-Modells
- **EU Digital Rights Organisationen** — als technische Referenz für "es geht auch anders"
- **Internationale Communities** — WoT jenseits der EU (Global South, Regionen ohne staatliche ID-Infrastruktur)

## Schlüssel-Insights

### Nicht eine App — ein Protokoll

Signal hat gewonnen weil das Signal-Protokoll in WhatsApp, Facebook Messenger und Google Messages eingebaut wurde — nicht weil alle Signal nutzen. Wir gewinnen wenn WoT-Verifikation in Nostr, Circles, Briar und Matrix eingebaut wird. Das Protokoll ist das Produkt, nicht die App.

### Die Brücke sind reale Communities

Technik allein reicht nicht. Menschen verifizieren sich bei echten Begegnungen. FoodCoops, Maker-Spaces, Community-Gärten, Nachbarschaftshilfe, Festivals — dort entstehen die Vertrauensnetzwerke. Die App ist nur das Werkzeug. Die Community ist das Netzwerk.

### DIDComm ist der Multiplier

Ohne Interop-Standard bleibt jede dezentrale App eine Insel. DIDComm verbindet die Inseln. Deshalb ist DIDComm-Kompatibilität strategisch wichtig — nicht als technisches Feature, sondern als Voraussetzung für ein Ökosystem.

### In-Person-Verifikation wird wertvoller, nicht weniger

In einer Welt voller AI-generierter Identitäten ist der Beweis "ich habe diesen Menschen persönlich getroffen und verifiziert" ein Wert der steigt. Jedes andere System (Biometrie, staatliche ID, Online-Verifikation) wird durch AI angreifbarer. Echte Begegnungen nicht.

### Die Alternative muss existieren bevor sie gebraucht wird

Man kann keine Infrastruktur bauen wenn die Krise da ist. Signal existierte bevor Snowden kam. Tor existierte bevor Wikileaks es brauchte. Unser WoT muss funktionieren, skalieren und interoperabel sein **bevor** der große Moment kommt. Deshalb bauen wir jetzt.
