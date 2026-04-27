# WoT Identity Vergleich — Related Work

> **Nicht normativ:** Dieses Dokument ist Hintergrund, Analyse oder Planung. Normative Anforderungen stehen in den Spec-Dokumenten und in `CONFORMANCE.md`.

- **Status:** Research
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-27

## Zweck

Dieses Dokument ordnet ein, ob es fuer den Scope von **WoT Identity** bereits vergleichbare Projekte gibt und welche Bausteine wir uebernehmen sollten.

WoT Identity meint hier nicht den gesamten Web-of-Trust-Stack, sondern nur das kryptographische Identitaetsprofil:

- Seed-, Key- und DID-Ableitung
- DID-Dokumente und `resolve()`-Semantik
- JWS/JCS-Signaturen mit `kid`
- offline verifizierbare langlebige Signaturen
- geplanter Pfad zu Device-Key-Delegation und Key-History

Trust-Semantik, Attestations, Sync, Broker und Gruppen gehoeren zu anderen WoT-Profilen.

## Kurzfazit

Es gibt kein einzelnes Projekt, das WoT Identity direkt ersetzt. Die richtige Einordnung ist: **WoT Identity ist ein schmales Interop-Profil ueber existierenden Standards und erprobten Key-Management-Mustern.**

Der Kern sollte deshalb nicht sein, eine neue DID-Methode oder ein neues Identity-System zu erfinden. Der Kern sollte sein, sehr genau festzulegen:

- welche DID-Methoden wir wie verwenden
- wie aus einem Seed interoperables Key-Material entsteht
- wie Signaturen, `kid` und Resolver zusammenspielen
- wie Device Keys delegiert und offline verifiziert werden
- wann wir von self-contained Delegation zu temporal verifizierbarer Key-History wechseln

## Vergleich nach Naehe

| Kategorie | Projekte / Standards | Einordnung |
|---|---|---|
| Direktes Fundament | DID Core, DID Resolution, `did:key`, `did:webvh`, JWS, JCS, Ed25519 | Standards, die WoT Identity profilieren sollte |
| Starke Architektur-Referenz | KERI, `did:keri` | Besseres Sicherheitsmodell fuer Key-History, aber deutlich komplexer |
| Device-Key-Muster | OpenPGP Subkeys, Keybase Sigchain, Matrix Cross-Signing | Sehr relevante Vorbilder fuer Phase 2/3 |
| SSI-Stacks | DIDKit, Veramo, Credo/Aries, Web5 | Tooling und Interop, aber kein Ersatz fuer unser Profil |
| Local-First-/Wallet-Muster | NextGraph, CryptPad, Jazz, Keyhive | Wertvolle UX- und Multi-Device-Muster, anderer Identity-Scope |
| Angrenzende Identitaet | OpenID4VC, EUDIW, DIDComm | Wichtig fuer Interop/Transport, ersetzt WoT Identity nicht |
| Key-as-Identity-Netze | Nostr, SSB | Aehnliche Einfachheit, akzeptieren aber Shared-Key-Probleme eher |
| Proof of Personhood | BrightID, Worldcoin, Human Passport | Gleiche gesellschaftliche Frage, anderer kryptographischer Scope |

## Direkte Bausteine

### DID Core und DID Resolution

DID Core ist die passende Basissprache fuer dezentrale Identitaet: eine DID kontrolliert ein DID-Dokument, das Verification Methods, Authentication, Assertion und Key Agreement beschreibt.

WoT Identity sollte hier kein neues Modell einfuehren. Der wichtige WoT-spezifische Teil ist die Resolver-Semantik: `resolve()` ist eine lokale Abstraktion ueber DID-Methoden, Cache, QR-Bootstrap, Profil-Service und spaetere History-Methoden.

### `did:key`

`did:key` passt sehr gut zu Phase 1:

- keine Infrastruktur
- offline aus dem Public Key aufloesbar
- deterministisch aus BIP39/HKDF ableitbar
- ideal fuer portable Signaturverifikation

Die Grenze ist ebenso klar: `did:key` kann per Design keine veraenderliche Key-History, keine echten Device-Keys im DID-Dokument und keine Identity-Key-Rotation ausdruecken. Phase 2 kann das mit self-contained DeviceKeyBinding ueberbruecken, aber nicht vollstaendig loesen.

### `did:webvh`

`did:webvh` ist ein natuerlicher Kandidat fuer Phase 3. Es bringt ein versioniertes, kryptographisch verkettetes DID-History-Log und kann Device Keys als Verification Methods im DID-Dokument ausdruecken.

Der Trade-off ist die Web-Abhaengigkeit bei Publikation und initialer Resolution. Fuer WoT ist das akzeptabel, wenn Offline-Verifier gecachte History-Segmente oder exportierte Proof-Bundles verwenden koennen.

### KERI und `did:keri`

KERI loest das gleiche Grundproblem am konsequentesten: langlebige Identifier, Key Event Logs, Pre-Rotation, Receipts und temporal verifizierbare Key-Rotation.

Fuer WoT ist KERI fachlich sehr relevant, aber fuer `wot-identity@0.1` zu schwer:

- grosser Spezifikationsumfang
- wenige breit genutzte Implementierungen
- hoeherer Implementierungsaufwand fuer kleine Apps
- mehr Daten, die mit exportierten Objekten oder Caches bewegt werden muessen

KERI ist deshalb eher Phase-4-Referenz oder spaeteres Kompatibilitaetsziel als Startpunkt.

### JWS, JCS und Ed25519

WoT Identity sollte bei Standard-Signaturbausteinen bleiben:

- Ed25519 fuer kompakte, deterministische Signaturen
- JWS Compact Serialization fuer transportierbare Signaturen
- JCS fuer kanonische JSON-Payloads vor Signatur
- `kid` als entscheidendes Bindeglied zwischen Signatur und Verification Method

Der WoT-spezifische Mehrwert liegt nicht im Signaturalgorithmus, sondern in den Pflichtregeln: `kid` muss vorhanden sein, Zweckbindung muss geprueft werden, und der Resolver muss den passenden Key liefern.

## Device-Key- und Key-History-Muster

### OpenPGP Subkeys

OpenPGP ist das naechste historische Vorbild fuer Phase 2. Ein Primary Key signiert Subkeys; die exportierte Public-Key-Struktur enthaelt Binding Signatures. Verifikation kann self-contained funktionieren.

Die WoT-Entsprechung ist:

| OpenPGP | WoT |
|---|---|
| Primary Key | Identity DID / Identity Key |
| Signing Subkey | Device Key |
| Binding Signature | DeviceKeyBinding-JWS |
| Public Key Block | Delegated-Attestation-Bundle oder Export-Bundle |

Die Grenze ist temporale Verifikation: OpenPGP-Revocation-Semantik ist fuer unsere langlebigen sozialen Attestations nicht praezise genug.

### Keybase Sigchain

Keybase ist das beste Vorbild fuer Phase 3. Die Sigchain bildet Account- und Device-Key-State als geordnete, hash-verkettete Liste ab. Verifier koennen den Key-State zum Signaturzeitpunkt rekonstruieren.

Die relevante Lektion fuer WoT:

- alte Signaturen bleiben gueltig, wenn der Key zum damaligen Zeitpunkt autorisiert war
- Device-Add und Device-Revoke sind auditierbare Key-Events
- eine Chain braucht Verteilung, Caching und Export-Semantik

Keybase selbst war serverzentriert. WoT sollte die Sigchain-Idee nur uebernehmen, wenn die History portabel, cachebar und offline pruefbar bleibt.

### Matrix Cross-Signing

Matrix loest Multi-Device-Vertrauen praktisch: User, Devices und Cross-Signing-Keys bilden eine Hierarchie, mit der Clients Geraete verifizieren.

Fuer WoT ist Matrix eine UX- und Device-Trust-Referenz, aber kein direktes Modell fuer portable Offline-Attestations. Matrix bleibt staerker server-/account-zentriert und ist auf sichere Kommunikation zwischen Clients optimiert, nicht auf jahrelang offline verifizierbare soziale Credentials.

### Nostr und SSB

Nostr und Secure Scuttlebutt zeigen, wie weit man mit `Key = Identity` kommt. Das ist wertvoll fuer Phase 1, weil es die Einfachheit von Shared-Key-Identitaeten bestaetigt.

Sie loesen das Device-Key-Problem aber nicht sauber:

- Nostr teilt den Private Key typischerweise ueber Clients oder akzeptiert Remote-Signer-Muster
- NIP-26 Delegated Signing wurde deprecated und ist kein starkes Device-Key-Modell
- SSB behandelt Identitaeten stark device-nah oder akzeptiert Shared-Key/Fusion-Identity-Muster

Diese Systeme sind Praxisbelege fuer Phase-1-Einfachheit, nicht Zielarchitektur fuer Phase 2/3.

## SSI- und DID-Toolchains

### DIDKit, Veramo, Credo und Aries

Diese Projekte liefern wichtige Implementierungsbausteine:

- DID-Resolution
- VC/JWT/JOSE-Verarbeitung
- DIDComm und Agent-Flows
- Wallet-/Holder-/Issuer-Patterns

Sie definieren aber nicht das konkrete WoT-Identity-Profil. Ein Veramo- oder Credo-Agent kann WoT-kompatibel werden, wenn er unsere Profilregeln implementiert: BIP39/HKDF, `kid`-Semantik, JCS/JWS-Regeln, Resolver-Verhalten und DeviceKeyBinding.

### Web5 / DWN / did:dht

Web5 und verwandte TBD-Technologien adressieren dezentrale Identitaet, persoenliche Datenspeicher und agentische Dateninfrastruktur. Das ist nah am groesseren WoT-Stack, aber breiter und staerker als Produkt-/Plattform-Stack gedacht.

Fuer WoT Identity sind sie eher Interop- und Architektur-Referenz als Ersatz. Besonders interessant ist die Trennung von Identifier, Datenspeicher, Agent und Protokoll-Flows.

## Angrenzende Standards

### OpenID4VC und EUDIW

OpenID4VC ist fuer Credential-Austausch und EU-Wallet-Interop wichtig, aber es loest nicht unser P2P/offline Identity-Key-Modell.

Der Scope ist anders:

| OpenID4VC | WoT Identity |
|---|---|
| Online Presentation / Issuance Flows | Offline verifizierbare Signaturen |
| Wallet-Verifier-Protokolle | Lokales DID-/Key-Profil |
| Staatlich/regulatorisch anschlussfaehig | Bottom-up, community-faehig |
| User-in-the-loop HTTP/OIDC | Portable Objekte und P2P-Kontext |

OpenID4VC kann spaeter ein Bridge-Profil werden, aber kein Ersatz fuer WoT Identity.

### DIDComm

DIDComm ist Messaging und Envelope-Semantik, nicht Identity. Fuer WoT ist DIDComm nur dort relevant, wo DIDs als Sender/Empfaenger in Transport-Flows auftauchen.

Die Identitaetsfrage bleibt trotzdem bei WoT Identity: Welche DID kontrolliert welche Keys, wie wird `kid` aufgeloest, und welche Signatur ist fuer welchen Zweck autorisiert?

## Local-First- und Wallet-Systeme

### NextGraph

NextGraph ist relevant fuer Wallet-UX, lokales Key-Material, Device-Transfer und Backup. Das Pazzle-/Wallet-Modell kann helfen, den BIP39-Seed aus der Default-UX herauszunehmen.

Es ersetzt WoT Identity nicht, weil die formale Interop-Spezifikation fuer unsere DID/JWS/offline-Attestation-Regeln ein anderer Scope ist.

### CryptPad

CryptPad liefert besonders wertvolle Muster fuer lokale und servergestuetzte Secrets:

- Login-Block-Indirektion
- Entkopplung von Passwort und langlebiger Identitaet
- rotierbare Authentisierung bei stabilen Daten-Keys

Das ist fuer Seed-Schutz und Recovery relevant, aber kein DID-/VC-Identity-Profil.

### Jazz und Passkeys

Jazz zeigt eine pragmatische Auth-UX mit Passkeys und Mnemonic-Fallback. Fuer WoT koennen Passkeys ein Unlock- oder Device-Auth-Mechanismus sein.

Sie sollten aber nicht die WoT-Root-Identity ersetzen, solange Recovery und Sync an Apple/Google/Platform-Accounts haengen.

### Keyhive

Keyhive ist technisch nah bei Local-First, Multi-Device und Delegationsketten. Es ist besonders interessant fuer Gruppen, Capabilities und Peer-to-Peer-Zusammenarbeit.

Der Scope ist aber eher Daten-/Gruppen-Autorisierung als globales, langlebiges DID-/Attestation-Profil fuer soziale Identitaet.

## Proof-of-Personhood-Systeme

BrightID, Worldcoin, Human Passport, Idena und aehnliche Systeme beantworten die gesellschaftliche Frage: Wie entsteht Sybil-Resistenz?

WoT Identity beantwortet eine schmalere technische Frage: Wie sieht die kryptographische Identitaet aus, mit der solche Aussagen offline signiert und verifiziert werden?

Darum sind Proof-of-Personhood-Systeme eher Nachbarn von **WoT Trust** als Ersatz fuer **WoT Identity**.

## Was WoT Identity daraus ableiten sollte

WoT Identity sollte bewusst ein Profil bleiben:

| Profilteil | Empfehlung |
|---|---|
| Seed und Key-Derivation | BIP39 + HKDF deterministisch profilieren |
| DID-Methode Phase 1 | `did:key` als minimale, offline aufloesbare Identity DID |
| DID-Methode Phase 3 | `did:webvh` oder KERI-kompatible History pruefen |
| Signaturen | Ed25519 + JWS Compact + JCS + verpflichtendes `kid` |
| Resolver | Lokale `resolve()`-Abstraktion ueber DID-Methode, Cache und Profil-Service |
| Device Keys Phase 2 | OpenPGP-artige DeviceKeyBinding-JWS-Bundles |
| Device Keys Phase 3 | Keybase-/did:webvh-artige temporale Key-History |
| High-Security Phase 4 | KERI-artige Pre-Rotation optional evaluieren |

## Was WoT Identity nicht tun sollte

- Keine eigene DID-Methode erfinden, solange `did:key` plus `did:webvh` oder KERI-kompatible History reichen.
- Keine Ledger- oder Blockchain-Abhaengigkeit einfuehren, nur um Key-History global zu verankern.
- Kein vollstaendiges KERI-Subset in `wot-identity@0.1` aufnehmen.
- Kein OpenID4VC-Flow als Voraussetzung fuer lokale WoT-Verifikation definieren.
- Kein Device als eigene soziale Person behandeln.

## Empfohlener Pfad

1. `wot-identity@0.1` bleibt minimal: BIP39/HKDF, `did:key`, DID-Dokument, `resolve()`, JWS/JCS/`kid`.
2. `wot-device-delegation@0.1` uebernimmt das OpenPGP-Subkey-Muster: Identity Key signiert DeviceKeyBinding, delegierte Signaturen liefern den Binding-Proof mit.
3. Phase 3 prueft `did:webvh` als bevorzugten Einstieg in temporal verifizierbare Key-History.
4. KERI bleibt Referenz fuer ein staerkeres spaeteres Sicherheitsmodell, nicht Startpunkt.
5. SSI-Toolchains werden als Implementierungsoptionen behandelt, nicht als normative Abhaengigkeit.

## Offene Fragen

1. Soll Phase 3 zuerst `did:webvh` profilieren oder eine eigene WoT-Sigchain definieren?
2. Brauchen exportierte Attestation-Bundles spaeter eingebettete History-Segmente, damit sie auch ohne Cache offline pruefbar bleiben?
3. Welche minimale Revocation-Semantik aus OpenPGP oder KERI ist fuer Phase 2 sinnvoll, ohne Phase 2 zu verkomplizieren?
4. Soll WoT Identity ein optionales OpenID4VC-Bridge-Profil bekommen, oder bleibt das strikt ausserhalb des Identity-Profils?
