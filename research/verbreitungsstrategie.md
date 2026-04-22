# Verbreitungsstrategie — Web of Trust 2026-2031

*Stand: 19. April 2026*

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
- Sync-Stack nach aktueller Spec implementieren (JWE JSON Serialization, Threading, Trust Ping 2.0, Discover Features 2.0 — alle in Sync 007 spezifiziert) — DIDComm v2.1-konform
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

## DIDComm als bewusste Gegenwette

Der europäische SSI-Diskurs teilt sich 2026 in zwei Lager:

- **OpenID4VC** — als Teil von eIDAS 2.0 normativ gesetzt. OAuth-2.0-basiert, Issuer-Holder-Verifier mit bekannten Rollen, staatlich sanktionierte Trust-Anchors. Aktiv weiterentwickelt.
- **DIDComm v2.1** — DIF-ratifiziert, stabil, P2P-orientiert. Seit Mai 2024 eingefroren (keine inhaltlichen Commits mehr), aber nicht verwaist: Protokoll-Registry auf didcomm.org ist aktiv, das Aries-Ökosystem (Indicio, Procivis, Lissi) läuft weiter.

**Unsere Wette:** Wir positionieren uns bewusst auf der DIDComm-Seite. Nicht weil das Ökosystem größer wäre, sondern weil es der **einzige ernsthafte dezentrale Gegenpol** zum OpenID4VC-Monopol der EU-Wallet ist. Wenn die Debatte kommt, ob digitale Identität zentral oder dezentral sein soll, ist DIDComm die publizierte, durchdachte, spezifizierte Antwort.

### Warum eingefrorene Spec für uns eine Stärke ist

Das klingt paradox, aber: eine stabile, ratifizierte Spec ohne Moving-Target-Risiko ist **besser** für unsere Positionierung als ein aktiv entwickelter Standard, dessen Details sich ändern.

- Wir bauen gegen ein feststehendes Ziel — keine Breaking Changes aus v2.2, die uns zum Nachziehen zwingen
- Unsere Interop-Aussage ist überprüfbar und dauerhaft (Spec v2.1 liegt publiziert vor)
- Der Stabilitäts-Zustand signalisiert Reife — keine Beta-Disclaimer

Die Tatsache, dass die DIDComm-Libraries (`didcomm-rust` dormant, `didcomm-js` entfernt, `didcomm-rs` tot) nicht mehr aktiv gepflegt werden, ist für unseren Weg kein Problem: wir implementieren ohnehin eigenständig via Web Crypto API. Die Spec selbst — das Dokument — bleibt als Referenz belastbar.

### Was wir für das Ökosystem beitragen können

**Das, was DIDComm fehlt, sind nicht Spec-Details, sondern:**

- **Laufende Implementierungen mit echten Usern** — wir wären eine der ersten DIDComm-v2-Apps mit einer realen Community-Nutzer-Basis
- **Use Cases jenseits von Enterprise SSI** — Mitarbeiterausweise und Supply Chain bewegen niemanden; Vertrauensnetzwerke aus echten Begegnungen schon
- **Eine Gegenerzählung zu OpenID4VC/eIDAS** — momentan dominiert die EU-Perspektive die Diskussion. DIDComm hat keine vergleichbare narrative Position

### Konkrete Schritte

**Kurzfristig:**

- DIF beitreten (kostenlos unter 500 Personen) — weniger für "Einfluss auf die Spec" (die ist fertig), mehr als Teil der stabilen Community
- Interop-Tests publizieren — wir zeigen, dass unsere eigenständige Implementation die Spec erfüllt
- Aktive Beiträge im didcomm.org-Protokoll-Register (das lebt), wenn wir ein Protokoll haben das dort Sinn ergibt

**Mittelfristig:**

- Unseren Broker als DIDComm-Mediator veröffentlichen (Open Source)
- Talks auf DIF-Meetings, IIW, CCC, FOSDEM — über den Use Case, nicht über Technik
- Vergleichsdokument: eIDAS/OpenID4VC vs. DIDComm/WoT — sachlich, Feature für Feature

### Die eIDAS-Diskussion nutzen

Die Kritiker der EU-Wallet (epicenter.works, Digitalcourage, CCC, EFF) haben ein Problem: sie können sagen was sie **nicht** wollen, aber nicht was sie **stattdessen** wollen. Wir können diese Lücke füllen:

- Kontakt zu Datenschutz-Organisationen: "Wir haben die technische Lösung für das Problem das ihr beschreibt."
- Material für Politiker und Journalisten: "So funktioniert dezentrale Identität — einfach erklärt."
- Live-Demo: zwei Apps (Real Life + Human Money) kommunizieren über DIDComm. "So sieht die Alternative aus."
- Workshops auf Festivals, Community-Treffen, Kooperativen-Tagungen. Nicht Kryptografie erklären sondern: "Scannt euch gegenseitig — jetzt habt ihr ein Vertrauensnetzwerk."

### Unser Beitrag

Nicht Code-Contributions zur DIDComm-Spec, sondern der Beweis dass es funktioniert und dass Menschen es wollen. Eine laufende Implementierung mit echten Communities ist wertvoller als jede theoretische Diskussion.

## Positionierung gegenüber der EU-Wallet

Die eIDAS-Debatte wird 2026-2028 an Fahrt aufnehmen. Wir brauchen eine klare Positionierung — nicht als Opposition, sondern als Alternative. Das Ziel ist nicht die EU-Wallet zu bekämpfen, sondern einen Raum zu öffnen für Menschen die eine andere Form digitaler Identität brauchen.

### Die Grundspannung

Wenn wir uns als "Anti-EU-Wallet" positionieren, verlieren wir die Mitte und werden als Verschwörungstheoretiker eingeordnet. Wenn wir zu neutral bleiben, haben wir keine Stimme wenn die Debatte kommt. Die richtige Balance:

**Nicht:** "EU-Wallet ist böse, nutzt stattdessen uns"
**Sondern:** "Es gibt zwei Arten von digitaler Identität — staatlich und community-basiert. Beide haben ihren Platz. Wir bauen die zweite."

Das ist **Pluralismus statt Opposition.** Keine Ablehnungs-Rhetorik. Einfach: eine Alternative existiert, funktioniert, ist verfügbar.

### Kern-Botschaft

> **"Staatliche Identität für den Staat. Community-Identität für die Community. Du wählst was zu welchem Kontext passt."**

Emotional aufgeladen:

> **"Dein Personalausweis beweist dem Staat wer du bist. Web of Trust beweist deinen Nachbarn dass du ein echter Mensch bist."**

### Drei Frames für verschiedene Zielgruppen

**Frame 1: Tech-Community (CCC, netzpolitik.org, Privacy-Aktivist:innen)**

Architektur-Kritik. Client-Server vs. Peer-to-Peer.

> "EU-Wallet ist eIDAS 2.0 — Client-Server, zentralisiert, **OpenID4VCI/OpenID4VP**-basiert, mit staatlichen Trust-Anchors. Wir bauen das Gegenteil: **DIDComm v2.1**, P2P, dezentral, Community-Trust-Anchors. Beide nutzen W3C Verifiable Credentials und Ed25519 — aber zwei fundamental unterschiedliche Exchange-Standards. Die Wahl ist nicht 'haben oder nicht haben', sondern welchem der beiden ratifizierten Standards man folgt."

Ankerpunkte: Mozilla's #SecurityRiskAhead, Artikel 45 Kritik, AI-Deepfake-Problem, DIDComm v2.1 als technisch ebenbürtige, dezentral orientierte Standards-Alternative zu OpenID4VC.

**Frame 2: Progressiv-kommunitaristisch (Commons, Kooperativen, Transition Towns)**

Community-Empowerment. Dein Netzwerk gehört dir.

> "Die EU-Wallet sagt: 'Der Staat bestätigt wer du bist.' Web of Trust sagt: 'Deine Gemeinschaft bestätigt wer du bist.' Kooperativen, Transition-Initiativen, Nachbarschaftsnetze, Mutual-Aid-Strukturen — alle brauchen Vertrauensinfrastruktur die nicht vom Staat abhängt. Nicht weil wir den Staat ablehnen, sondern weil Communities vor dem Staat existieren und ihn überdauern können."

Ankerpunkte: Platform Cooperativism, Commons-Bewegung (Elinor Ostrom), Transition Towns, Real Life Network als konkretes Beispiel.

**Frame 3: Liberal/libertär (Bürgerrechte, Privacy, "alte Werte")**

Freiheit und Wahlmöglichkeit.

> "Wir haben einen Personalausweis — aber wir können auch Bargeld nutzen ohne uns auszuweisen. Wir haben öffentliche Telefondienste — aber wir können auch private Gespräche führen. Die EU-Wallet ist das Äquivalent zu einem verpflichtenden Klarnamen-Ausweis im Netz. Web of Trust ist das Äquivalent zu einem Vertrauensvorschuss unter Nachbarn. Beides muss möglich sein — das ist Freiheit."

Ankerpunkte: Pluralismus statt Monopolismus staatlicher Identität, Bürgerrechtsgeschichte, nicht anti-Staat sondern pro-Vielfalt.

### Zeitliche Staffelung der Kommunikation

**Phase A (jetzt bis Ende 2026): Vorbereitung**

Die Debatte ist noch klein. Wir bauen still:
- Technische Grundlagen (Spec, Implementation)
- Netzwerk (DWeb Camp, Sebastian, Community-Partner)
- Story-Reservoir (Analysen, Positions-Papiere in research/)

Kommunikation zurückhaltend. Nicht aggressiv publizieren. Bereit sein wenn gefragt wird.

Ziel: Sobald die Debatte kommt, haben wir Antworten, Code, und Partner — nicht nur Meinungen.

**Phase B (2027 bis Mitte 2028): Erste Welle**

Die ersten EU-Wallets rollen aus. Datenschutz-Bedenken werden öffentlich. Medien schreiben erste kritische Artikel.

Kommunikation:
- Meinungsbeiträge in netzpolitik.org, Heise, taz
- CCC-Congress-Talk (Vorschlag bis September 2027 einreichen)
- DWeb Camp Präsenz
- Technische Demos die funktionieren
- Gezielte Kontakte zu Datenschutz-Organisationen

Botschaft: "Es gibt eine Alternative. Sie existiert. Hier ist sie."

**Phase C (ab Q4 2027): Der Kipppunkt**

Private Akteure müssen EU-Wallet akzeptieren. Breite öffentliche Wahrnehmung. Erste Missbrauchs-Fälle, Datenlecks, vielleicht ein autoritärer Regierungswechsel in einem EU-Staat der zeigt was zentrale digitale ID bedeuten kann.

**Das ist der Signal-Moment** — wie Snowden für Signal.

Kommunikation:
- Offensive Präsenz in Medien
- Partnerschaften mit bekannten Aktivist:innen
- Sichtbare Implementation die Menschen sofort nutzen können
- Integration mit bekannten Apps (Nostr, Bluesky, Matrix)

Botschaft: "Ihr habt gefragt: gibt es eine Alternative? Hier ist sie. Schon seit Jahren. Bereit."

### Vorbereitete Antworten (Talking Points)

**"Ist das nicht zu kompliziert für normale Menschen?"**
> "Signal war auch 'zu kompliziert'. Bis es nicht mehr kompliziert war. Die Technologie ist komplex, die Nutzung ist einfach: QR-Code scannen, verifiziert."

**"Lehnt ihr die EU-Wallet ab?"**
> "Nein. Wir bauen etwas anderes. Für Menschen die staatliche Identität nicht nutzen wollen oder können. Beide Systeme können parallel existieren."

**"Was ist mit Kriminellen die das missbrauchen?"**
> "Web of Trust verifiziert dass jemand ein echter Mensch ist — nicht dass er ein guter Mensch ist. Für gesetzliche Durchsetzung gibt es den Staat mit seinen Instrumenten. Wir ersetzen das nicht."

**"Warum brauchen wir überhaupt eine Alternative?"**
> "Stell dir vor: eine zukünftige Regierung wird autoritär. Sie kontrolliert die EU-Wallet. Sie kann deinen digitalen Zugang zur Gesellschaft abschalten. Web of Trust ist nicht abschaltbar, weil niemand allein darüber verfügt."

**"Ist das nicht was für Verschwörungstheoretiker?"**
> "Nein. Es ist für Menschen die aus Erfahrung wissen dass Systeme versagen. Signal existiert nicht weil alle paranoid sind, sondern weil Privatsphäre ein Menschenrecht ist. Web of Trust existiert aus demselben Grund."

**"Ist das nicht illegal nach eIDAS?"**
> "Nein. eIDAS regelt was als offizielle EU-Wallet akzeptiert werden muss. Alternative Systeme für Community-Nutzung sind nicht reguliert. Wir sind nicht die EU-Wallet — wir sind etwas anderes."

**"Warum DIDComm statt OpenID4VC?"**
> "OpenID4VC ist Client-Server — es setzt bekannte Issuer, Holder und Verifier voraus, die über Web-Endpoints kommunizieren. Das passt zur EU-Wallet-Topologie (Bürger, Bundesdruckerei, Verwaltung), aber nicht zu P2P-Communities. DIDComm v2.1 ist für den Peer-to-Peer-Fall gebaut — zwei Menschen tauschen Nachrichten aus, ohne dass einer vorher den anderen 'kennt' oder eine dritte Instanz involviert ist. Beide Standards nutzen W3C VCs und JWS — sie sind also auf Daten-Ebene interoperabel über Gateways. Wir haben uns für DIDComm entschieden, weil es zum Community-Modell passt."

**"Ist DIDComm nicht ein totes Projekt?"**
> "Die Spec ist seit v2.1 stabil — keine inhaltlichen Commits seit Mai 2024. Aber 'stabil' ist nicht 'tot': TLS 1.3 hatte auch lange keine Updates, und das Protokoll wird überall genutzt. Die aktive Arbeit passiert auf der Protokoll-Ebene (didcomm.org), nicht an der Envelope-Spec. Für uns ist eine eingefrorene Spec eine Stärke: wir bauen gegen ein feststehendes Ziel, ohne Moving-Target-Risiko."

### Zu produzierende Materialien

**Kurzformate (Blog, Social Media):**
- "EU-Wallet vs. Web of Trust — was ist der Unterschied?" (Erklär-Artikel)
- "5 Fragen zur digitalen Identität — die du stellen solltest"
- "Warum Signal vor Snowden existieren musste"

**Mittelformate (Publikationen, Interviews):**
- Positions-Papier: "Pluralismus digitaler Identität" — technisch fundiert, politisch neutral
- Vergleichs-Tabelle EU-Wallet vs. WoT
- Interview-Pool mit vorbereiteten Antworten

**Langformate (Talks, Videos):**
- 20-Minuten-Talk: "Die andere digitale Identität"
- 5-Minuten-Demo-Video
- Akademisches Paper zur Sybil-Resistenz ohne staatliche Autorität

### Wer sollte wann sprechen

- **Anton** — Vision, Community, Realitäts-Nähe
- **Sebastian** — Technische Tiefe, Currency/Economic-Perspektive
- **Joachim Lohkamp** (wenn er mitmacht) — SSI-Erfahrung, "wir haben das schon erlebt"
- **Partner aus DWeb** — internationale Perspektive
- **Aktivist:innen** (epicenter.works, Digitalcourage) — politische Einordnung
- **Projektteam nicht zu sichtbar machen** — wir sind das Werkzeug, nicht die Bewegung

### Die Meta-Strategie

**Wir positionieren uns als Infrastruktur.** Wie Signal, wie Matrix, wie Tor. Nicht als politische Bewegung, nicht als Firma, nicht als Produkt. Einfach: Infrastruktur die es gibt, die funktioniert, die du nutzen kannst wenn du willst.

Das macht uns **unangreifbar** auf der politischen Ebene:

- Nicht "die gegen die EU"
- Nicht "die Verschwörungstheoretiker"
- Nicht "die Crypto-Bros"
- Sondern: "die haben eine technische Alternative gebaut — sauber, open source, dezentral. Nutze es wenn du willst."

Genau diese nüchterne Positionierung ist was Signal so stark gemacht hat — gegen anfänglichen Widerstand und heute als De-facto-Standard akzeptiert.
