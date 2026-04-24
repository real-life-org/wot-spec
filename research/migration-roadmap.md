# Migrations-Roadmap — von aktueller Implementation zu Spec v1.x

- **Status:** Planungsdokument
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-20

## Zweck

Dieses Dokument strukturiert, wie wir die beiden Implementierungen (**WoT Core** in TypeScript, **Human Money Core** in Rust) schrittweise auf die aktuelle Spec-Fassung überführen — ohne alles auf einmal machen zu müssen.

Die Spec ist in den letzten Wochen (vor allem seit dem 18./19.04.2026) substanziell erweitert worden. Parallel sind einige strukturelle Entscheidungen noch offen (siehe [identitaet-alternativen.md](identitaet-alternativen.md) für die strukturellen Fragen). Dieses Dokument nimmt den **aktuell spezifizierten Stand** als Ziel und plant die Migration.

**Koordinations-Prämisse:** Viele der Änderungen sind unabhängig voneinander. Wir können parallel migrieren und müssen nicht auf jede strukturelle Entscheidung warten, bevor wir anfangen.

## Status-Matrix

| Spec-Dokument | Spec-Stand | WoT Core Impl | HMC Impl | Gap-Größe |
|---|---|---|---|---|
| Core 001 Identität | v1.0 (HKDF `wot/identity/ed25519/v1`, volle 64 Bytes) | Abweichend (slice(0,32), `wot-identity-v1`) | Abweichend (info `human-money-core/ed25519`) | Klein (Info-String + Slicing) |
| Core 002 Signaturen | v1.0 (alg-strict, JCS-Test-Vektoren) | Teilweise konform | Zu prüfen | Klein |
| Core 003 Attestations | v1.0 (W3C VC 2.0) | Teilweise konform | Teilweise konform | Mittel |
| Core 004 Verifikation | v1.0 (QR-Challenge-Response) | Vorhanden | Zu prüfen | Klein |
| Sync 005 Verschlüsselung | v1.0+ (ECIES, Constant-Time, Det-Nonce aus seq) | Teilweise (ECIES vorhanden, Nonce/Key-Pfade pruefen) | Abweichend (SecureContainer, ChaCha20) | Mittel |
| Sync 006 Sync-Protokoll | v1.0+ (Multi-Source-Sync) | Append-Only-Logs da, Multi-Source fehlt | Eigenes Modell (Gutschein-Transfer) | Mittel |
| Sync 007 Transport | v1.0+ (DIDComm-Plaintext-Envelope mit `typ`, Threading, Envelope-Policy, Capability-TTL, Nonce-History) | Teilweise | Eigenes (L2-Server) | Mittel |
| Sync 008 Discovery | v1.0 (Profile-Service, Broker-Discovery) | Läuft (wot-profiles) | Zu prüfen | Klein |
| Sync 009 Gruppen | v1.0 (Einladungen, Key-Rotation) | Implementiert | Nicht direkt anwendbar | Mittel |
| Sync 010 Personal Doc | v1.0 (neu, 2026-04-19) | Fehlt | Fehlt | Groß |
| H01 Trust-Scores | Entwurf (SD-JWT VC, 2026-04-19) | Nicht implementiert | Teilweise (eigene Trust-Lists) | Groß |
| H02 Transactions | Platzhalter | Nicht implementiert | Implementiert (eigene Spec) | N/A |
| H03 Gossip | Entwurf | Nicht implementiert | Teilweise | Mittel |
| R01 Badges | Platzhalter | Teilweise | N/A | N/A |

**Noch nicht in Spec, aber diskutiert:**

- Primäre Key-Rotation (did:peer:4 vs. DID-Migration) — aktuelle Präferenz A
- Multi-Key-Konsequenzen (kid-Resolution, DID-Document-Distribution)
- Unlock-Mechanismen (Passwort + Argon2id, Passkey via PRF)
- Guardian-Vouching (reines Vouching, kein Shamir) aus NLnet WP2
- Wortlisten-Entscheidung
- v1.1-Security-Fixes (K1, K3, M4, M6)

## Abhängigkeits-Analyse

```
┌────────────────────────────────────────────────────────┐
│ Anwendungs-Extensions (H01 SD-JWT VC, H02, H03, R01)   │
│   ↑ hängt an Core 003 + Format-Entscheidungen          │
├────────────────────────────────────────────────────────┤
│ Unlock-Mechanismen (Passwort, Passkey)                 │
│   ↑ App-Layer — hängt an Core 001 (verschlüsselter     │
│     Container), aber nicht an Multi-Key-Frage          │
├────────────────────────────────────────────────────────┤
│ Core 003 Attestations + Core 004 Verifikation          │
│   ↑ hängt an Core 001-002 + ggf. Multi-Key-DID         │
├────────────────────────────────────────────────────────┤
│ Core 001 Identität + Core 002 Signaturen               │
│   ↑ hier entscheidet sich: did:key → did:peer:4        │
│     Format-Fixes aber unabhängig von DID-Methoden-     │
│     Wechsel                                             │
├────────────────────────────────────────────────────────┤
│ Sync 005-007, 010                                       │
│   ↑ nutzt DIDs nur als opake Strings                    │
│   ↑ UNABHÄNGIG von DID-Struktur                         │
├────────────────────────────────────────────────────────┤
│ Sync 008 Discovery                                      │
│   ↑ bindet DIDs an Profile, nicht an DID-Struktur       │
└────────────────────────────────────────────────────────┘
```

**Kernbeobachtung:** Sync-Layer behandelt DIDs als opake Identifier. Er muss nicht wissen, ob eine DID auf einen einzelnen Key oder ein Multi-Key-Document verweist. Deshalb kann Sync **jetzt** migrieren, ohne dass die DID-Methoden-Entscheidung getroffen ist.

## Phasen

### Phase 1 — Sync-Stack migrieren

**Was:** Alles, was in der Sync-Schicht neu spezifiziert wurde, in beide Implementierungen überführen.

**Spec-Dokumente:**

- Sync 005 (Verschlüsselung)
  - ECIES statt DIDComm-JWE/Authcrypt
  - Constant-Time-MUSS
  - Deterministische Nonce aus `(deviceId, seq)` für Gruppen-Verschlüsselung
- Sync 006 (Sync-Protokoll)
  - Multi-Source-Sync für Censorship-Detection
- Sync 007 (Transport)
  - DIDComm-v2-kompatibler Plaintext-Envelope mit `typ: "application/didcomm-plain+json"` und `thid`/`pthid` Threading
  - Broker-Presence statt Trust Ping 2.0
  - Profil-`protocols` statt Discover Features 2.0
  - Envelope-Signatur-Policy (wann Signed Message, wann nicht)
  - Capability `validUntil` Pflichtfeld
  - Nonce-History (24h) beim Broker
- Sync 010 (Personal Doc + Cross-Device-Sync)

**Abhängigkeiten:** Keine zu anderen Phasen. Kann sofort beginnen.

**Parallelisierbar:** Vollständig. Beide Impls können unabhängig voneinander migrieren.

**Aufwand:** Substanziell, aber gut eingegrenzt. Jede Teiländerung ist lokal in einem Modul.

**Impl-Aktionen WoT Core (TypeScript):**

- ECIES-Implementierung auf Spec-Vektoren pruefen
- Nonce-Generator anpassen (aus seq ableiten bei Gruppen-Verschlüsselung)
- DIDComm-Envelope mit Threading-Feldern ausstatten
- Broker-Presence und Profil-Discovery nachziehen
- Broker-Code: Capability-TTL-Check, Nonce-History
- Multi-Source-Sync-Logik im Client
- Personal-Doc-Modul neu

**Impl-Aktionen HMC Core (Rust):**

- Äquivalente Änderungen, in dem Maße wie Sebastian Sync-Primitive übernehmen will
- Koordination: welche Teile übernimmt er, welche bleiben sein Layer-1/Layer-2-Modell

### Phase 2 — Core-Format-Fixes

**Was:** Die formalen Inkonsistenzen in Core 001-002 beseitigen.

**Spec-Änderungen:**

- Core 001: HKDF-Info auf `wot/identity/ed25519/v1` vereinheitlichen, volle 64 Bytes
- Core 002: alg-strict-Enforcement, JCS-Test-Vektoren integrieren

**Abhängigkeiten:** Muss mit Phase 3 (Wortlisten) koordiniert werden, da beides Core 001 berührt.

**Parallelisierbar:** Zu Phase 1 ja. Zu Phase 4 ja, da Format-Fixes innerhalb did:key-Welt gemacht werden können.

**Konsequenz:** Bestehende DIDs werden bei diesem Schritt invalid. Alle User müssen einmalig neue DIDs erzeugen oder migrieren.

**Impl-Aktionen beide Impls:**

- Info-String anpassen
- Seed-Slicing entfernen
- Regression-Tests gegen neue Testvektoren

**Migrations-Strategie für bestehende User:**

- Option a): Big-Bang — alle existierenden DIDs werden neu generiert, keine Migration
- Option b): Parallel-Betrieb — App unterstützt alte und neue Ableitung, User wird zu Migration eingeladen
- Da beide Implementierungen noch nicht in großem Produktions-Einsatz sind, ist Option a) vermutlich akzeptabel

### Phase 3 — Wortlisten-Entscheidung treffen und implementieren

**Was:** Die offene Frage aus der Sebastian-Diskussion schließen.

**Entscheidung:** Drei Varianten (siehe aktueller Vorschlag an Sebastian):

- A) Englisch BIP39 als Pflicht, deutsche Positive-Liste als UI-Mapping
- B) Beide normativ unterstützt (Impl kennt englisch UND deutsch)
- C) Nur englisch BIP39

**Abhängigkeiten:** Muss mit Phase 2 koordiniert werden (beides Core 001). Gespräch mit Sebastian steht aus.

**Parallelisierbar:** Zu Phase 1 ja.

**Impl-Aktionen:** Abhängig von gewählter Variante. Bei A: englisch als interne Kanonisierung, deutsche Anzeige-Schicht. Bei B: beide Wortlisten im Impl, Auto-Detection bei Wiederherstellung.

### Phase 4 — Strukturelle Entscheidung: did:peer:4 + Guardian-Vouching spezifizieren

**Was:** Die substantielle Architektur-Entscheidung umsetzen.

**Spec-Dokumente:**

- Core 001 umschreiben: DID-Methoden-Wechsel auf did:peer:4, DID-Document-Struktur spezifizieren
- Core 002 erweitern: Multi-Key-Verifikation (kid-Resolution, Versions-Semantik, Historisch-gültig-Semantik, append-only Revocation)
- Core 003 erweitern: DID-Document-Snapshot-Option für Offline-Verifikation
- Core 004 erweitern: Long-Form-DID im QR-Code für In-Person-Verifikation
- **Neu: Core 005 (DID-Document-Updates)**
  - Update-Attestation-Format
  - Signatur-Regeln (Master signiert, Guardian-Quorum signiert, Device-Keys mit begrenzten Rechten)
  - Guardian-Vouching-Flow aus NLnet WP2
- **Neu: Core 006 (DID-Document-Distribution)**
  - Publishing via Profile-Service
  - Gossip-Propagation über DIDComm-Inbox
  - Cache-Strategie, Resolver-Semantik

**Abhängigkeiten:** Sollte NACH Phase 2 (Format-Fundament steht). Unabhängig von Phase 1 (Sync).

**Parallelisierbar:** Zu Phase 5 (Unlock-Mechanismen) ja. Zu Phase 7 (Extensions) teilweise.

**Aufwand:** Groß. Das ist der substantiellste Spec-Ausbau.

**Koordinations-Punkt mit Sebastian:** Muss von beiden Implementierungen adoptiert werden — oder wir akzeptieren, dass HMC bei did:key bleibt und WoT Core zu did:peer:4 wechselt. Dann wäre ein Adapter-Layer zwischen den beiden nötig.

**Impl-Aktionen:**

- DID-Document-Datenmodell implementieren
- DID-Document-Resolver-Logik
- Multi-Key-Signing (kid als JWS-Header-Feld)
- Multi-Key-Verifikation mit zeitlicher Semantik
- DID-Document-Publishing-Endpoint im Profile-Service
- Gossip-Propagation über bestehende Inbox
- Cache-Management auf Client-Seite

### Phase 5 — Unlock-Mechanismen

**Was:** CryptPad-Style Login-Block-Pattern implementieren, optional mit Passkey-Integration.

**Spec-Dokumente:**

- **Neu: Core 007 (Unlock-Mechanismen)**
  - Passwort + Argon2id (OWASP-2024-Parameter)
  - Login-Block-Architektur (Passwort entsperrt lokalen verschlüsselten Container)
  - zxcvbn-Score ≥ 3 als Mindestanforderung
  - Ancestor-Proof für Passwort-Rotation
- Optional: Passkey-Integration via WebAuthn PRF-Extension

**Abhängigkeiten:** Komplett orthogonal zu Phase 4. Kann parallel laufen.

**Parallelisierbar:** Zu allem außer Phase 2.

**Aufwand:** Mittel. Architektur ist klar (siehe CryptPad-Recherche), Integration in App-Layer.

**Impl-Aktionen:**

- Argon2id-Bibliothek einbinden
- Login-Block-Storage-Schema
- Block-URL-Schema mit Broker
- Ancestor-Proof-Signatur-Logik
- WebAuthn-PRF-Integration (wenn Browser-Support)

### Phase 6 — Guardian-Vouching Recovery-Implementation

**Was:** Den in Phase 4 spezifizierten Recovery-Flow aus NLnet WP2 tatsächlich bauen.

**Spec-Dokumente:** Bereits in Phase 4 (Core 005) spezifiziert, hier nur Implementation.

**Abhängigkeiten:** Phase 4 muss abgeschlossen sein (DID-Document-Update-Protokoll steht).

**Parallelisierbar:** Zu Phase 5 und Phase 7.

**Aufwand:** Mittel. Protokoll ist klar (signierte Vouching-Attestations, Threshold-Check, DID-Document-Update), UX ist die Herausforderung.

**Impl-Aktionen:**

- Guardian-Setup-UI
- Vouching-Attestation-Creation-Flow
- Guardian-Kontakt-Protokoll (User kontaktiert Guardians out-of-band, Guardians signieren)
- Threshold-Check-Logic
- Migration-Durchführung im Client

### Phase 7 — HMC- und RLS-Extensions

**Was:** H01 als SD-JWT VC, H02 Transactions, H03 Gossip-Integration, R01 Badges.

**Spec-Dokumente:**

- H01: SD-JWT VC-Format finalisieren (mit Sebastian)
- H02: Sebastians Voucher-Spec auf eine kompakte Extension in unserer Spec verdichten (mit Sebastian)
- H03: bereits Entwurf, nur kleinere Anpassungen
- R01: Badges-Spec vervollständigen

**Abhängigkeiten:** Kann laufen sobald Phase 2 (Core-Format) abgeschlossen ist.

**Parallelisierbar:** Zu allem nach Phase 2.

**Aufwand:** Variabel. H01 und H02 sind substantiell, R01 ist klein.

**Koordinations-Punkt mit Sebastian:** H01 und H02 sind seine Extensions. Wir unterstützen, aber er treibt die Ausarbeitung.

## Parallelisierungs-Matrix

```
                 P1     P2     P3     P4     P5     P6     P7
Sync-Stack       ████
Core-Fixes              ██
Wortlisten              ██ ██
did:peer:4                            ████████
Unlock           ▒▒▒▒   ▒▒     ▒▒     ▒▒▒▒▒▒▒▒
Guardian                                     ████
HMC-Extensions          ▒▒     ▒▒     ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒

████ = kritischer Pfad (muss in dieser Phase laufen)
▒▒▒▒ = parallel möglich (keine strikte Abhängigkeit)
```

## Kritischer Pfad

Der kritische Pfad, der nicht parallelisiert werden kann:

**Phase 2 → Phase 4 → Phase 6**

Das heißt konkret: Die Format-Fixes müssen vor der did:peer:4-Migration stehen. Die did:peer:4-Spec muss vor der Guardian-Recovery-Implementation stehen.

**Alles andere kann parallel laufen:**

- Phase 1 (Sync-Stack) — komplett unabhängig
- Phase 3 (Wortlisten) — parallel zu Phase 2
- Phase 5 (Unlock) — vollständig orthogonal
- Phase 7 (Extensions) — parallel sobald Phase 2 steht

## Migration-Strategie: Branch-basierter Neuaufbau, keine Daten-Migration

**Entscheidung (20.04.2026):** Wir bauen die neue Implementation auf einem separaten Git-Branch auf. **Keine Daten-Migration** für bestehende User. Frischer Start ist akzeptabel, weil weder Implementation noch Produktionsnutzung ausreichend weit fortgeschritten sind, um Migrations-Aufwand zu rechtfertigen.

### Branch-Strategie

**Branch:** `next/sync-v1` im `web-of-trust`-Repo — angelegt 20.04.2026.

- **Main bleibt unverändert** — alte Implementation läuft weiter für existierende Entwicklungs-/Pilot-Nutzung
- **Der Branch `next/sync-v1` bekommt alle Phase-1-Änderungen** — Sync 005/006/007/010 nach neuer Spec
- **Merge nach Main erst wenn**:
  - Alle Tests grün
  - End-to-End-Flow funktioniert (zwei Devices, Space erstellen, syncen, Attestation ausstellen)
  - Performance akzeptabel
  - Team (Tillmann, Sebastian Stein) hat die Implementation gesehen
- **Vergleichsmöglichkeiten während der Branch-Arbeit**:
  - `git diff main next/sync-v1` für Code-Vergleiche
  - Parallele Test-Instanzen möglich
  - Rollback trivial (auf Main zurück)

**Für HMC (Sebastian) analog:** eigener Branch im `human-money-core`-Repo, koordiniert.

### Was "frischer Start" konkret bedeutet

**Keine Migration erforderlich für:**

- Personal Doc (User legt bei erstem Start neues an)
- Space-Mitgliedschaften (Spaces werden neu erstellt)
- Capabilities (neue Spaces = neue Capabilities direkt mit `validUntil`)
- Attestations (gehen verloren)
- Trust-Graph (baut sich neu auf)

**Das heißt für User:**

- Nach App-Update mit neuem Branch: neue Identität anlegen (neue DID)
- Kontakte müssen sich neu verifizieren (In-Person-Verifikation wiederholen)
- Spaces werden neu erstellt und Einladungen neu verschickt

**Das ist für die aktuelle Nutzungsintensität vertretbar.** Die Anzahl wirklich aktiver WoT-Nutzer ist begrenzt, Datenverlust ist für sie kommunizierbar als "Beta-Phase".

### Implikationen für Phase 2 und spätere Phasen

Dadurch, dass Phase 1 auf `next/sync-v1` komplett neu gebaut wird, können wir Phase 2 (Core-Format-Fixes) direkt auf demselben Branch fortführen — ohne Migrations-Code für die Core-001-Änderungen (HKDF-Info, volle 64 Bytes). Der Branch wird erst zu Main-kompatibel, wenn er als Ganzes stimmt.

**Implizite Kaskade**: Phase 4 (did:peer:4) kann im selben Branch passieren. Der Branch wird zum "neues Web of Trust v1"-Branch, der alle spec-konformen Änderungen akkumuliert, bevor er breit gemerged wird.

**Für spätere User-facing Migrations-Bedarfe (wenn wir mal Produktions-Nutzer haben):** Das Equivalence-Proof-Pattern aus NLnet WP2 steht als Konzept bereit, ist aber aktuell nicht zu implementieren.

## Koordinations-Punkte mit Sebastian

Die Migration ist nicht nur unser Projekt — sie betrifft HMC Core genauso. Folgende Punkte brauchen Abstimmung:

**Phase 2:**

- HKDF-Info-String auf `wot/identity/ed25519/v1` — er muss ebenfalls migrieren
- Wortlisten-Variante (A, B, C) — gemeinsame Entscheidung nötig

**Phase 4:**

- Folgt HMC dem Wechsel zu did:peer:4, oder bleibt HMC bei did:key?
- Wenn Divergenz: Adapter-Layer zwischen den Systemen nötig
- Alternativ: HMC adoptiert did:peer:4, was für ihn größerer Umbau ist

**Phase 5:**

- Nutzt HMC unser Unlock-Pattern? Sein System ist möglicherweise anders strukturiert
- Seine "Wallet"-Logik überschneidet sich konzeptionell — Abstimmung sinnvoll

**Phase 7:**

- H01 SD-JWT VC: gemeinsam mit Sebastian ausarbeiten
- H02 Transactions: Sebastian treibt, wir integrieren

**Generell:** Regelmäßiger Sync-Rhythmus zwischen beiden Teams hilft. Eventuell zweiwöchentliche Spec-Syncs.

## Offene Fragen

1. **Big-Bang vs. sanfte Migration für bestehende User?** Bei Phase 2 und Phase 4 werden DIDs neu erzeugt. Brauchen wir einen Auto-Migration-Flow oder ist Neu-Onboarding akzeptabel?

2. **Wann fangen wir mit Phase 1 an?** Nach Abstimmung mit Sebastian oder proaktiv? Argumente für proaktiv: geringe Interop-Risiken, großer Spec-Fortschritt wird Code. Argumente für Abstimmung: Sync-Stack ist einer der Bereiche, wo HMC und WoT Core auseinandergehen könnten.

3. **Folgt HMC uns zu did:peer:4?** Antwort ist substanziell für Phase 4. Wenn nein: Adapter oder Divergenz akzeptieren.

4. **Welche v1.1-Security-Fixes in welche Phase?** M4 (Rate-Limiting) passt zu Phase 1. M6 (Device-TTL) zu Phase 4 (Multi-Key). K1 (Multi-Admin) und K3 (Admin-only-Metadata) zu Phase 4 oder später.

5. **Wie dokumentieren wir die Migration für Nutzer?** User-facing Changelog, In-App-Benachrichtigung, Migration-Assistent?

6. **Welche Phase hat Priorität für das NLnet-Projekt?** Die Bewerbung listet WP2 (Recovery + Key Rotation) als konkretes Deliverable — das ist Phase 4 + Phase 6. WP1 (Authorization & Access Control) überschneidet sich mit Sync 007-Capabilities. WP3 (Developer Experience) wird durch alle Phasen informiert.

## Notizen aus Web5-Recherche (20.04.2026)

**Für WP1 Authorization (Capabilities):** Das DWN Protocol-Definitions-Modell von Web5 ist ein guter Referenz-Entwurf für unsere Authorization-Spec. Nicht übernehmen, aber lesen vor Spec-Ausarbeitung:

- **`who × can`-Grammar**: `who: [anyone, author, recipient]` × `can: [create, read, update, delete, co-update, co-delete, query, subscribe]` — minimal aber expressiv. Besser als ABAC/RBAC selbst zu erfinden.
- **Deklarative Protocol-Definitions**: App-Entwickler definieren statisch Record-Typen und Action-Rules, kein imperativer Policy-Code.
- **JWS-Authorization mit `descriptorCid` + `permissionsGrantCid`**: saubere Signatur-Struktur, passt zu unserem SignedClaim-Ansatz.
- Quelle: [DWN Spec](https://identity.foundation/decentralized-web-node/spec/), §Protocols, §Message Authorization

**Warnung:** DWN-Permissions/Subscribe/Hooks/Sync sind im Spec-Draft noch **TODO** — Web5 hat das nie fertig spezifiziert. Wer DWN übernimmt, erbt Baustellen. Wir sollten konzeptuell lernen, aber nicht 1:1 übernehmen.

**Für Phase 4 (Multi-Key-DID):** Web5's `@web5/dids` und `@web5/agent` enthalten fertigen MIT-Code für:
- HD Identity Vault mit Login-Block-Pattern (siehe identitaet-alternativen.md §F)
- did:dht-Resolver
- Generisches BearerDid-Modell mit `kid`-basierten Signaturen
- JWE Compact Serialization für verschlüsselte Container

Wenn wir Ansatz A (did:peer:4) verfolgen, können wir das BearerDid-Modell als Referenz nehmen. Wenn wir Ansatz C (did:dht) verfolgen, können wir direkt `@web5/dids` einbinden.

## Referenzen

- [identitaet-alternativen.md](identitaet-alternativen.md) — Die strukturellen Entscheidungen, die hinter Phase 4-6 stehen
- [security-analysis.md](security-analysis.md) — Die Security-Fixes, die nach v1.0 kommen
- [security-fixes.md](security-fixes.md) — Aufwand und Trade-offs der v1.1-Fixes
- [didcomm-migration.md](didcomm-migration.md) — DIDComm-Kompatibilitäts-Stand
- [briefing-sebastian.md](briefing-sebastian.md) — Kommunikation mit Sebastian zur aktuellen Spec
- NLnet-Bewerbung WP1-WP4 — Förderungs-Kontext für Implementation
