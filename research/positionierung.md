# Positionierung — Web of Trust

> **Nicht normativ:** Dieses Dokument ist Hintergrund, Analyse oder Planung. Normative Anforderungen stehen in den Spec-Dokumenten und in `CONFORMANCE.md`.

*Stand: 20. April 2026*

## Elevator-Pitch

Web of Trust ist ein offenes Protokoll, das echte Begegnungen zur Grundlage digitaler Identität macht. Zwei Menschen treffen sich, verifizieren einander mit einem QR-Code — und haben damit die Basis für alle weiteren digitalen Beziehungen gelegt, ohne dass eine Plattform oder ein Staat dazwischensteht. Daraus wächst ein dezentraler Vertrauens-Graph, der Gemeinschaften auch dann trägt, wenn größere Infrastrukturen versagen.

## Was wir sind

Die [Real Life Organisation](https://github.com/real-life-org) baut Werkzeuge, das Real Life Network nutzt sie. Web of Trust ist das Werkzeug für **Identität und Vertrauen** in diesem Gefüge — das kryptographische Fundament, auf dem andere Werkzeuge (Real Life Stack, Human Money, später weitere) aufbauen.

Wir sind keine Plattform. Wir sind keine App. Wir sind keine Firma. Wir sind ein **Protokoll** — eine dokumentierte, offene Art, wie Computer über Identität und Vertrauen sprechen können. Das Protokoll gehört der Allmende, die Implementierungen sind MIT-lizenziert, jeder darf es nutzen, niemand kann es abschalten.

Der Kern ist radikal einfach: Eine Identität ist ein kryptographischer Schlüssel, den ein Mensch selbst erzeugt. Sie wird nicht vergeben. Sie wird nicht gewährt. Sie existiert, sobald der Mensch sie hervorbringt. Was dieser Identität anschließend an Bedeutung zuwächst, entsteht aus echten Begegnungen und gegenseitigen Bestätigungen anderer Menschen — nicht aus behördlichen Attesten und nicht aus algorithmischen Reputations-Scores.

## Die drei Koordinaten unserer Arbeit

### Ziele

Wir wollen Infrastruktur bereitstellen, auf der Gemeinschaften digital so zusammenarbeiten können, wie sie in der physischen Welt bereits funktionieren: auf Basis echter Bekanntschaft, mit fließender gegenseitiger Unterstützung, ohne Zwang zu Mitgliedschaft oder zentraler Buchführung. Konkret: Identitäts- und Vertrauens-Schicht für Nachbarschaftsinitiativen, Kooperativen, Ecovillages, Transition-Bewegungen, Festivals, Reparatur-Cafés, lokale Tauschnetze. Für alles, was Organisation vor Institutionalisierung ist.

### Werte

**Der Mensch ist das Subjekt.** Nicht der Staat, nicht die Plattform, nicht der Algorithmus. Aus Menschen entstehen Beziehungen, aus Beziehungen Gemeinschaften, aus Gemeinschaften größere Strukturen. Diese Richtung ist nicht umkehrbar. Identität fließt von unten nach oben.

**Echte Begegnung vor Online-Verbindung.** Wir halten es mit Ivan Illich: Konvivialität entsteht, wo Menschen einander unmittelbar begegnen. Digitale Werkzeuge sollen solche Begegnungen verstärken, nicht ersetzen.

**Datenhoheit beim Menschen.** Wer Daten über mich hält, hat Macht über mich. Deshalb gehören meine Daten auf meine Geräte — verschlüsselt, bevor sie irgendeinen Server berühren. Das Prinzip ist nicht Privacy aus Angst, sondern Selbstbestimmung aus Prinzip.

**Commons statt Produkt.** Was Infrastruktur ist, soll nicht Firmen gehören. Das gilt für Straßen, Trinkwasser und Strom. Und es gilt für Identität und Vertrauens-Netzwerke.

**Leichtigkeit.** Gute Technologie ist, die niemand bemerkt. Wer auf einem Marktplatz verifiziert wurde, soll es danach vergessen dürfen.

### Design-Entscheidungen

- **Dezentral:** kein zentraler Server, keine einzige Instanz, die man abschalten kann
- **Offline-first:** funktioniert ohne Internet, wenn Menschen nebeneinander stehen
- **End-to-End-verschlüsselt:** kein Server sieht, was Menschen einander sagen
- **CRDT-basiert:** Daten synchronisieren sich, ohne dass jemand den Schiedsrichter spielt
- **Standards-konform:** W3C Verifiable Credentials, W3C DID, JWS, DIDComm v2.1
- **Community-Broker:** die immer-online-Peers werden von Communities betrieben, nicht von einer Firma
- **Keine Blockchain:** Wir brauchen keinen globalen Konsens. Wir brauchen lokale Wahrheit.

## Die Landschaft, in der wir uns bewegen

Digitale Identität und dezentrale Infrastruktur werden gerade in mehreren parallelen Strömungen bearbeitet. Jede verfolgt eigene Ziele, steht für eigene Werte, trifft eigene Design-Entscheidungen. Keine davon ist verkehrt — aber keine davon kombiniert, was wir kombinieren.

### Überblick der Strömungen

| Strömung | Projekte (bekannte Beispiele) | Zentrale Ziele | Unser Verhältnis |
|---|---|---|---|
| **Staatlich organisierte digitale Identität** | eIDAS / EU-Wallet, Aadhaar (Indien) | Regulatorische Sicherheit, Gewährleistung durch Staat, Verbraucherschutz, offizielle Akzeptanz | Philosophische Abgrenzung (siehe unten). Technische Koexistenz möglich — unsere Identität ersetzt nicht den Personalausweis. |
| **Proof-of-Personhood-Protokolle** | Circles UBI, Worldcoin, BrightID, Idena, Humanode | Sybil-Resistenz beweisen (dass hinter einer Identität ein einzigartiger Mensch steht) | **Direkter Nachbar.** Wir sind auch ein Proof-of-Personhood-Protokoll. Unsere Antwort: Social-Graph über In-Person-Verifikation. Circles ist eine der großen Inspirationen — der Trust-Graph-Ansatz, nicht die Blockchain. |
| **Dezentrale Kommunikations-Netze** | Signal, Matrix, Nostr, Bluesky/ATProto, Briar | Kommunikation ohne Plattform-Zwang, Zensur-Resistenz, Datenhoheit | **Verwandtschaft im Ziel, Ergänzung in der Funktion.** Sie lösen Messaging und Publikation. Wir liefern die Vertrauens-Schicht, auf der solche Netze sich sinnvoll verhalten können (Spam-Filter, Reputation, Verifikation). |
| **Local-First und P2P-Infrastruktur** | Automerge, Jazz, Keyhive, Willow, Ink & Switch | Daten gehören den Menschen, offline-fähige Zusammenarbeit, CRDT-basierte Synchronisation | **Engste technische Verwandtschaft.** Unsere Design-Entscheidungen kommen aus diesem Lager. Wir bringen Identität und Sozialgraph als zusätzliche Schicht ein. |
| **Alternative Ökonomie-Plattformen** | Community-Währungen, Human Money, Chiemgauer, Sardex | Wirtschaftskreisläufe jenseits des etablierten Finanzsystems, Regionalität, Solidarität | **Anwendungsraum.** Wir liefern die Identitäts- und Trust-Schicht, auf der solche Ökonomie-Protokolle Sybil-sicher und privacy-tauglich laufen können. |
| **Gemeinwohl-Bewegungen (Anwender)** | Transition Towns, Ecovillage-Netzwerke, Platform Cooperatives, Real Life Network, Kooperativen | Gesellschaftliche Transformation, Lokalität, Resilienz, Kooperation | **Unsere Zielgruppe und unser Herkunftsraum.** Web of Trust ist das Werkzeug, das diese Bewegungen als digitale Infrastruktur fehlt. |

Unser Projekt liegt im Schnittpunkt mehrerer Strömungen: ein **Proof-of-Personhood** (Strömung 2) mit **Local-First-Architektur** (Strömung 4), konzipiert als **Infrastruktur-Layer unter Gemeinwohl-Anwendungen** (Strömung 6).

## Was nur wir in dieser Form kombinieren

Jede der genannten Strömungen hat ihre Stärken. Aber die spezifische Mischung, die Web of Trust ausmacht, findet sich nirgends sonst:

1. **In-Person-Verifikation als kryptographische Basis.** Nicht Biometrie, nicht Behavioral, nicht Live-Check — sondern ein QR-Code, gescannt zwischen zwei Menschen, die sich gegenüberstehen. Die stärkste Form von Sybil-Resistenz, die ohne Überwachung auskommt.

2. **Social-Graph ohne Blockchain.** Circles hat gezeigt, dass Vertrauens-Graphen funktionieren. Wir zeigen, dass sie ohne öffentlichen Ledger funktionieren — als private Beziehungen, verschlüsselt, sichtbar nur für Beteiligte.

3. **Offline-first und Krisen-resilient.** Unsere Architektur funktioniert auf einem Festivalgelände ohne Internet, in einer Nachbarschaft mit ausgefallenen Servern, in Regionen mit intermittierender Netzverbindung. Nicht als Notfall-Modus, sondern als Grundfall.

4. **Daten bei den Menschen, nicht auf einer Plattform, nicht auf einer Kette, nicht beim Staat.** Das Personal Document eines Nutzers liegt auf seinen Geräten. Synchronisation findet verschlüsselt statt. Broker, die dabei helfen, sehen nur Chiffrat — nicht wer mit wem, nicht warum.

5. **Commons-Governance von Anfang an.** Keine Venture-Capital-Spur, keine Token-Ökonomie, keine Exit-Strategie zu einem Corporate-Buyer. Finanzierung über öffentliche Förderung (NLnet) und Community-Beiträge.

6. **Integration physischer Begegnungen als Produktfeature.** Festivals, Kreise, Workshops, Nachbarschafts-Treffen sind nicht Marketing — sie sind der Ort, an dem das Netzwerk wächst. Die App ist das Werkzeug, die Community ist das Netzwerk.

## Unsere Position in der Debatte um digitale Identität

Die EU rollt bis Ende 2026 die European Digital Identity Wallet aus. Das wird eine Debatte entfachen, die gesellschaftlich weit reichen wird: Wer darf sagen, wer du bist? Wir haben dazu eine klare Haltung — und halten es gleichzeitig für falsch, diese Haltung als Opposition zu führen.

**Unsere Kritik ist philosophisch fundiert.** Eine Identität, die vom Staat gewährt wird, dreht das Verhältnis zwischen Mensch und Institution um. Staaten entstehen historisch aus Menschen, die sich organisieren — nicht umgekehrt. Wenn der Staat am Anfang der digitalen Identitätskette steht, wird der Mensch zum Derivat einer Verwaltungshandlung. Das ist eine strukturelle Verschiebung, deren Konsequenzen sich erst über Jahre zeigen werden — in autoritären Konstellationen früher als in stabilen Demokratien.

**Wir stehen auf einer anderen Grundlage.** Beim Web of Trust erzeugt der Mensch seine Identität selbst. Was sie bedeutet, fließt ausschließlich aus Beziehungen zu anderen Menschen. Der Staat hat in diesem Modell seinen Platz — aber nicht als Gewährer der Identität, sondern als eine Institution unter anderen, die Beziehungen bestätigen kann.

**Keine Opposition, sondern Pluralismus.** Wir lehnen die EU-Wallet nicht ab. Sie wird für bestimmte Kontexte sinnvoll sein: Behörden, regulierte Dienste, grenzüberschreitende Bürokratie. Aber sie darf nicht die einzige Form digitaler Identität sein. Eine Gesellschaft, die nur eine Art sich auszuweisen kennt, hat ein Problem, bevor das Problem eintritt. Wir bauen die andere Art — für alles, was außerhalb des formalen Verwaltungsraums stattfindet.

**Was das für uns strategisch heißt.** Wir nutzen die eIDAS-Debatte als Anlass, nicht als Feindbild. Wir erklären, was wir tun, und warum es wichtig ist, dass mehrere Antworten auf die Frage "Wer bist du digital?" nebeneinander existieren. Das Argument ist struktureller, nicht moralischer Natur — Pluralismus statt Monokultur.

## Community-Resilienz als strategischer Kern

In der Decentralized-Identity-Community gibt es seit Jahren eine Diskussion unter dem Arbeitstitel *"When the shit hits the fan"* — über Gemeinschaften als resiliente Keimzellen, die in Krisenzeiten Ressourcen teilen und einander tragen. Das Thema war damals durch Corona geprägt. Seitdem hat sich gezeigt, dass Pandemien nicht die letzte Form großflächiger Unterbrechung waren, die uns beschäftigt.

Digitale Infrastruktur kann in solchen Zeiten eines von zweierlei sein: fragile Abhängigkeit, oder tragende Struktur. Wenn Serverparks nicht erreichbar sind, wenn Datenschutzskandale zentrale Plattformen diskreditieren, wenn ein Regierungswechsel Behörden-Zugänge verändert — wovon hängt dann ab, dass Menschen digital zusammenarbeiten können?

Unsere Antwort ist: davon, dass ihre Identität nicht von einer einzelnen Instanz ausgestellt wurde. Dass ihre Daten auf ihren eigenen Geräten liegen. Dass zwei Menschen über Bluetooth einen Gutschein austauschen können, wenn das Internet ausgefallen ist. Dass ein Festival funktioniert, auch wenn Mobilfunk zusammenbricht.

Das ist kein Katastrophen-Marketing, sondern ein Designprinzip: **Eine Infrastruktur, die auch im Normalfall weniger wirkt, weil sie weniger Aufmerksamkeit fordert, trägt im Krisenfall umso stabiler.** Wir bauen für das, was Ivan Illich "konvivial" nannte — Werkzeuge, die ihre Nutzer stark machen, nicht schwach.

Community-Resilienz ist deshalb nicht ein zusätzliches Argument für Web of Trust. Es ist der Grund, warum es die Art hat, die es hat.

## Wo wir jetzt stehen

**Spezifikation:** Die WoT-Spec ist in aktiver Ausarbeitung. Core (Identität, Signaturen, Attestations, Verifikation) und Sync (Verschlüsselung, Sync-Protokoll, Transport, Discovery, Gruppen, Personal Doc) sind als v1 in Entwurf. Erste Extensions (Badges, Trust-Scores, Gossip, Transactions) sind skizziert.

**Implementierungen:** Zwei unabhängige Implementierungen informieren die Spec — TypeScript/Web Crypto (Real Life Organisation) und Rust/ed25519-dalek (Human Money Core, Sebastian Galek). Die Spec ist als Brückendokument konzipiert, nicht als einseitige Vorgabe.

**Nutzung:** Real Life Stack integriert WoT als erste Anwendung. Utopia Map (Vorgängerprojekt, ~860 registrierte Nutzer, ~50 Community-Instanzen) wird schrittweise auf die neue Architektur migriert. Human Money Core wird parallel entwickelt.

**Finanzierung:** Bewerbung bei NLnet NGI Zero Commons (36.000 €) eingereicht, Entscheidung im Frühsommer 2026 erwartet. Bisher: Ehrenamt, Eigenfinanzierung.

**Kooperationen in Planung:** DIF-Mitgliedschaft, Gespräche mit Willow-Entwicklern, KERI-Community.

## Weiterführende Dokumente

- [README der Spezifikation](../README.md) — technische Übersicht der Protokoll-Schichten
- [Verbreitungsstrategie 2026-2031](verbreitungsstrategie.md) — strategischer Plan und politische Einordnung
- [Interop und Zielgruppe](interop-und-zielgruppe.md) — detaillierte Analyse der Standards-Landschaft
- [Sync-Alternativen](sync-alternativen.md) — 13+ Sync-Protokolle als Inspirationsquellen
- [Identitäts-Alternativen](identitaet-alternativen.md) — Exploration zu Recovery, Unlock, Key-Rotation
- [Migration-Roadmap](migration-roadmap.md) — Phasenplan von Spec zu Implementation

Für öffentliche Darstellung und Zielgruppen-spezifische Narrative siehe die [Landing-Page](https://web-of-trust.de).
