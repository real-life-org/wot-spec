# Der dezentrale soziale Graph — Diskurs und Designprinzipien

Status: Entwurf (Research). Destillat eines Gesprächs Anton/Eli vom
05./06.07.2026, angestoßen durch ein Telefonat Antons mit Matthew Schutte
(RWOT, Ex-Holochain) am 05.07., der auch auf Sheldrake und die
Allen-Quellen verwies.
Zweck: die philosophische Einordnung und die daraus folgenden Designprinzipien
festhalten, bevor sie in normative Spec-Teile, Threat-Model-Szenarien oder
ADRs überführt werden. Ergänzt `positionierung.md`, ersetzt es nicht.

## 1. Kernproblem

Vertrauen zwischen Menschen skaliert nicht über die direkte Begegnung hinaus.
Jede historische Lösung dafür (Staat, Bank, Plattform) hat Vertrauen durch
Stellvertretung ersetzt: Ich vertraue nicht mehr dir, sondern der Instanz, die
für dich bürgt. Die Instanz wird dadurch zum Machtzentrum. Das Internet hat
dieses Muster radikalisiert (Plattformen besitzen den Vertrauensgraphen),
generative KI macht es akut (Kosten der Menschenfälschung gegen null).

Das WoT skaliert nicht Vertrauen selbst (das bleibt ein Akt zwischen
Menschen), sondern dessen Vorbedingung: soziales Wissen über Relationen.

> "We don't scale trust. Trust remains what it always was: making yourself
> vulnerable to another person. What we scale is the social knowledge that
> trust has always depended on: knowing where a stranger stands in relation
> to the people you already know. Villages had this for free."

## 2. Drei Philosophien von Identität

| Modell | Philosophie | Englische Begriffe | Bruchstelle |
|---|---|---|---|
| Staatlich | Identität als Rechtsstatus, Registereintrag; Legibility (Scott) | state-issued, granted or withheld | Was gewährt wird, kann entzogen werden; Register = Überwachungs- und Exklusionsinstrument |
| Self-Sovereign (SSI) | Identität als Eigentum; Locke, Cypherpunk; Deklaration per Key Pair | self-sovereign, self-asserted, claimed | Schlüssel ≠ Person (Sybil); atomistisches Selbst ist Fiktion |
| Relational (WoT) | Identität als Anerkennung; Hegel, Buber, Ubuntu; Attestation = formalisierte Anerkennung | relational identity, identity as recognition | Parochialismus: das Dorf kann auch Tyrannei sein |

WoT ist kein SSI. Das Key Pair ist nur der Anfang; Bedeutung entsteht
ausschließlich aus Beziehungen (deckt sich mit `research/positionierung.md`).

Finanzierungsdilemma als logische Folge: Staaten können nur die Identität
finanzieren, die ihrer eigenen Philosophie entspricht (gewährter Status).
Geförderte "dezentrale" Projekte driften deshalb systematisch zurück zum
Issuer-Modell. Konsequenz: Finanzierung muss aus den nutzenden Gemeinschaften
kommen, nicht von Identitäts-Souveränen.

## 3. Sheldrake: Bestätigung und zwei Herausforderungen

Philip Sheldrake (AKASHA Foundation, generative-identity.org) liefert die
zitierfähige akademische Fundierung der relationalen Linie:

- Identity ≠ identification ≠ ID (Donner). Der Digital-Identity-Diskurs
  redet fast nur über die letzten beiden.
- Identität liegt im Auge des Betrachters ("how we recognize, remember, and
  respond" — funktionale Definition der RWoT-Community selbst). "Control"
  über Identität ist logisch unmöglich, nicht nur schwer.
- Noun-like (Ausweis, Biometrie, unveränderlich) vs. verb-like Identität
  (narrativ, im Fluss). Gelebte Identität ist verb-like.
- Es gibt fast keine "personal data", nur "interpersonal data": Daten leben
  auf den Kanten, nicht auf den Knoten. "My data" ist ein Kategorienfehler.

Quellen: "Generative identity — beyond self-sovereignty" (2019),
"The interpersonal data at the heart of all human digital systems" (2019),
"Cooperating at Scale" 1+2 (2020), alle via web.archive.org / akasha.org.

Zwei Einwände von ihm treffen unser Design direkt und müssen beantwortet
bleiben (durch Architektur, nicht Rhetorik):

1. **Social-Credit-Emergenz.** Portabel vorzeigbare Fremd-Claims erzeugen
   über rationales Eigeninteresse (Reputation portieren) emergent ein
   Social-Credit-System von unten, bis Vorzeigen zur Erwartung wird.
2. **Friction als Systemeigenschaft.** Natürliches Verblassen und
   Nicht-Korrelierbarkeit von Kontexten schützen die "freedom of narrative".
   Kryptographische Artefakte vergessen nie; Vergessen muss Designprimitiv
   werden, nicht Bug.

Teilwiderspruch unsererseits: Sheldrakes These, Sybil-Resistenz sei nur in
einer Minderheit von Kontexten nötig, stammt von 2019, vor generativer KI.
Der Anteil der Kontexte, in denen Personhood zählt, ist seither dramatisch
gewachsen. Sein Punkt bleibt als Warnung vor dem Totalsystem gültig.

## 4. Warum der Graph Wert erzeugt

**Indirekte Reziprozität jenseits Dunbar.** Kooperation in Dorfgröße beruht
auf sozialem Wissen über Relationen (wer kennt wen, wer hat sich wie
verhalten). Genau dieses Wissen bricht bei ~150 Personen zusammen. Der
explizite egozentrische Graph ist eine Prothese für diese Fähigkeit: Er
stellt die Vorbedingung indirekter Reziprozität jenseits der Dorfgröße
wieder her ("dieser Mensch kennt Sabine", "war mit Bernhard auf Event XY").

**Ostroms erste Bedingung.** Funktionierende Commons brauchen "clearly
defined boundaries". Digitale Commons scheiterten bisher daran, dass die
Grenze entweder von Plattformen (gemietet) oder vom Staat (bürokratisiert)
gezogen wurde. Ein begegnungsbasierter Graph macht Zugehörigkeit erstmals
aus der Gemeinschaft heraus definierbar: als nachvollziehbarer Pfad echter
Beziehungen. Damit werden Eigenverantwortung, geteilte Verantwortung und
Commons-Governance dezentral adressierbar.

**Abgrenzung DAOs/POAP/SBT.** DAOs haben Ostroms Grenzproblem mit dem
falschen Material gelöst: Kapital (Token) statt Beziehung → kaufbar,
sybil-anfällig, plutokratisch. Die Nachbesserungen der Szene (POAP = Event-
Ko-Präsenz als NFT, Soulbound Tokens, Proof of Humanity, Worldcoin) hatten
die richtige Intuition auf dem falschen Substrat: globales, öffentliches,
permanentes Ledger = God's-eye view ohne Eigentümer. Unser Unterschied ist
nicht die Kante, sondern wo sie liegt: bei den Beteiligten,
adressatengebunden freigegeben.

## 5. Designprinzipien

Nummerierung P1–P7; Status bezieht sich auf den heutigen Spec-Stand.

**P1 Perspektivität (kein God's-eye view).** Der Graph existiert nirgends
als Ganzes, auch nicht aggregierbar. Es gibt nur egozentrische Sichten.
Status: normativ verankert (`web-of-trust/docs/architecture/graph-visibility.md`:
"The global graph exists — but nobody sees it"; Non-Goals: keine
Multi-Hop-Traversierung, keine transitiven Scores).

**P2 Pfad-Entdeckung = lokaler Join über getrennt autorisierte Freigaben.**
Was ich über Verbindungen weiß, entsteht ausschließlich durch Abgleich in
meinem Client über Daten, die mir ihre jeweiligen Besitzer einzeln
freigegeben haben (Sabines Freigabe an mich + Freigabe der neuen Person an
mich → Schnittmenge lokal). Keine Anfrage an ein Netz, kein Routing über
Dritte. Status: implizit vorhanden (Mutual Contacts in graph-visibility.md,
Empfängerprinzip in `02-wot-trust/001-attestations.md`); als explizites
Prinzip noch nicht formuliert.

**P3 Wissen ≠ Beweis (abgeleitete Kanten sind nicht portabel).** Aus
Freigaben darf ich lokal inferieren ("Sabine kennt diese Person vermutlich"),
wie es das Dorf auch tut. Zur Überwachung wird Inferenz erst, wenn sie
(a) Dritten gegenüber beweisbar oder (b) maschinell in Masse ausführbar
wird. Regel: Freigaben sind adressatengebunden und nicht weiterreichbar;
was mir gezeigt wurde, kann ich glauben, aber nicht vorzeigen. Status:
architektonisch angelegt (Empfängerprinzip, Selective Disclosure in H01),
als Invariante und als Threat-Szenario (Social-Credit-Emergenz) noch nicht
festgeschrieben.

Präzisierung (06.07.2026): Im heutigen Modell ist P3 nicht durchgesetzt —
wer eine Attestation sieht, hält den vollen JWS mit beweiskräftiger
Issuer-Signatur. Ziel ist nicht Verhinderung der Datenweitergabe
(unmöglich), sondern Entzug des Beweiswerts: Geleaktes = Hörensagen.
Enforcement-Stufen:
1. *Audience-Binding* (SD-JWT KB-JWT, aud+nonce): Replay wertlos, aber
   innere Issuer-Signatur bleibt beweiskräftig — halbe Lösung.
2. *Deniable Authentication*: Freigaben werden nicht als JWS ausgehändigt,
   sondern per paarweisem MAC aus statischem DH bewiesen (OTR/Signal-
   Muster). Live beweisend, für Dritte wertlos. X25519 ist in Spec v2
   bereits vorhanden — natürlicher Kandidat.
3. *ZK-Präsentationen* (BBS+): Basis-Signatur verlässt den Holder nie;
   erfordert BLS12-381 statt Ed25519 — größerer Schritt.
Unabhängig von der Stufe: **Verifizieren bei Aufnahme, Überzeugung
speichern statt Artefakt.** Der Client prüft live und legt einen eigenen,
nur lokal gültigen Eintrag ab ("verifiziert am …"); keine Archivkopie
fremder Artefakte. Das stützt zugleich P4: Archivkopien unterlaufen
Widerruf/Verfall, Live-Nachfragen respektieren sie.
Abgrenzung: bewusst Veröffentlichtes (`public=true` im Profil) ist
Publikation und darf portabel sein. Residuum: Leaks an Menschen, die dem
Leaker vertrauen, kann kein System verhindern; das System selbst prägt
nur keine portablen Beweise.

**P4 Friction und Vergessen als Primitive.** Verfall, Ablauf und
Kontext-Trennung sind Features, keine Bugs. Traversierung ist an das Tempo
echter Begegnungen gekoppelt, nicht an Bulk-Queries. Der Graph liefert
Gesprächsanfänge ("ihr wart beide auf Festival X"), keine Urteile (kein
Score). Status: fragmentarisch (180-Tage-Gossip-Gedächtnis in H01, Defaults
privat); kein formales Decay-Modell, offen laut ROADMAP.

**P5 Ko-Präsenz ist eine schwache, eigene Kantenart.** "Gleiches
Event/gleicher Space" ist keine Begegnungs-Attestation und darf nicht wie
eine aussehen. Offene Designentscheidung: eigene Kantenart vs. Kontexte nur
als gemeinsame Knoten. Status: ungelöst; Berührungspunkte R01-badges,
`03-wot-sync/005-gruppen.md`, RLN 8.5.

**P6 Handshake minimiert Offenlegung.** Beim Kennenlernen soll nur die
Schnittmenge sichtbar werden (gemeinsame Events, gemeinsame Kontakte), nicht
die Historien beider Seiten. Kandidat: Private Set Intersection als
kryptographisches Primitiv im Begegnungs-Flow. Status: nicht dokumentiert;
heutiger QR-Nonce-Handshake (`02-wot-trust/002-verifikation.md`) deckt
Live-Bindung ab, nicht Offenlegungsminimierung.

**P7 Anti-Koerzion: Mehr-Zeigen darf strukturell nicht belohnt werden.**
Nötigung braucht keinen Zwang: Was vorgezeigt werden kann, wird über
rationales Eigeninteresse zur Erwartung (Sheldrakes eBay→Airbnb-Dynamik,
Strukturation; Aadhaar als Extremfall "freiwillig, aber Opt-out =
Ausschluss vom Leben"). Selective Disclosure und private Defaults schützen
daher nur, wenn Nicht-Offenlegen folgenlos bleibt. Regeln:
- Kein Protokoll- oder Produktpfad darf denjenigen bevorteilen, der mehr
  Disclosures mitsendet; die Schnittmenge (P6) ist der normale
  Kennenlern-Modus, nicht die Profil-Vollansicht.
- Das Anfordern von mehr als der Schnittmenge ist ein Protokoll-Geruch;
  die UI macht Over-Asking sichtbar, statt es zu glätten.
- Der einfachste Weg in der UI entspricht der Souveränität der Person,
  nicht dem Interesse des Systems (2026-Entwurf revisitingssi.com:
  "Design is never neutral: it shapes behavior and distributes power").
- Einseitiges Austrittsrecht inkl. Wipe (Relational Autonomy); nicht-
  digitale Teilnahme bleibt möglich (Equity).
Status: konstruktiv teilweise erfüllt (private Defaults, Empfängerprinzip,
Teardown/Wipe-Strang, Offline-Box); als Invariante und Review-Lens noch
nicht festgeschrieben.

## 6. Diskurs-Formulierungen (englisch)

- Claimed vs. granted: "Identity you claim versus identity you're granted."
  / "State-issued identity can be granted, and it can just as easily be
  withheld."
- Gegen SSI-Einordnung: "We're not building self-sovereign identity, and
  we're not trying to make identity verifiable at all. Identity stays where
  it belongs: in the eye of the beholder, in flux. What we make verifiable
  is something much smaller: the fact of an encounter. And we deliberately
  keep it context-bound and frictional, because portable universal
  reputation is just social credit built bottom-up."
- Kernproblem: "Trust doesn't scale beyond direct encounter, and every
  institution we built to scale it ended up replacing trust with control.
  The choice isn't between decentralized and centralized identity. It's
  between trust as a commons and trust as a product."
- Finanzierung: "Asking a state to fund self-asserted identity is asking it
  to fund its own obsolescence as the source of who counts."

## 7. Offene Entscheidungen (nächste Schritte)

1. P3 normativ machen: Invariante "adressatengebundene Freigaben, keine
   Weiterreichbarkeit" + Threat-Szenario "emergentes Social-Credit" in
   `web-of-trust/docs/security/threat-model.md`; ggf. ADR in
   `wot-spec/decisions/`.
2. P5 entscheiden: Ko-Präsenz-Kantenart, im Zuge von R01-badges.
3. P4 ausarbeiten: Decay-/Expiry-Modell für Kanten und Attestations
   (ROADMAP-Item konkretisieren).
4. P6 erkunden: PSI-Handshake als Research-Spike.
5. P7 als Review-Lens etablieren: Bei jedem Feature prüfen, ob ein Pfad
   Mehr-Offenlegung strukturell belohnt oder Over-Asking glättet.

## Referenzen

- Sheldrake, Generative identity — beyond self-sovereignty, AKASHA 2019
- Sheldrake, The interpersonal data at the heart of all human digital
  systems, RadicalxChange/AKASHA 2019
- Sheldrake, Cooperating at Scale Teil 1+2, AKASHA 2020
- Allen, The Path to Self-Sovereign Identity, 2016
- Donner, The difference between digital identity, identification, and ID, 2018
- Scott, Seeing Like a State, 1998 · Arendt, Origins of Totalitarianism, 1951
- Ostrom, Governing the Commons, 1990 · Dunbar, Neocortex size…, 1992
- Weyl/Ohlhaver/Buterin, Decentralized Society: Finding Web3's Soul, 2022
- Allen et al., Revisiting the SSI Principles (2026-Entwurf),
  revisitingssi.com — sechs neue Prinzipien: Inalienability, Cognitive
  Liberty, Relational Autonomy, Stewardship, Equity, Anti-Coercive Design
