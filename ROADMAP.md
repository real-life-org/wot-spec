# Roadmap

Diese Roadmap beschreibt die naechsten Arbeitsbloecke fuer die Web-of-Trust-Spezifikation. Sie ist operativ: Aus den Eintraegen sollen GitHub Issues, Releases und Implementierungsaufgaben entstehen.

## Zielbild

Die Web-of-Trust-Arbeit hat ein klares Ergebnisziel:

```txt
Spec + zwei unabhaengige Implementierungen + Demo-App
```

Die Spec soll als neutrales, versioniertes Interop-Profil dienen. Menschen und Communities sollen WoT-Identitaeten, Attestations und Sync unabhaengig von einer einzelnen App implementieren koennen. Der Interop-Beweis ist erst erbracht, wenn mindestens zwei unabhaengige Implementierungen dieselben Testvektoren bestehen. Die Demo-App beweist zusaetzlich, dass die Protokollentscheidungen fuer echte Menschen und echte Geraete benutzbar sind.

## Roadmap-Tracks

### 1. Spec Track

Die Spec ist die neutrale Protokollquelle. Sie definiert normative Dokumente, Schemas, Testvektoren, Conformance-Profile und Research-Abgrenzungen.

Erfolgskriterium:

- Eine externe Implementierung kann anhand von Spec, Schemas und Testvektoren interoperabel bauen, ohne implizites Wissen aus der TypeScript-App zu brauchen.

### 2. TypeScript Conformance Track

Die TypeScript-Implementierung (`web-of-trust`, `@web_of_trust/core/src/spec`) ist die erste Spec-nahe Referenzimplementierung. Sie beweist praktische Implementierbarkeit, darf aber nicht die Spec ersetzen.

Erfolgskriterium:

- Der Spec-Core besteht alle relevanten `wot-spec`-Vektoren mit vendored Fixtures und bleibt getrennt von Legacy-App-Services, Storage, Messaging, CRDT und UI.

### 3. Rust/HMC Conformance Track

Die Rust/HMC-Implementierung ist der zweite unabhaengige Interop-Beweis. Sie ist nicht nur Portierung, sondern Gegenprobe: Wenn Rust und TypeScript dieselben Vektoren bestehen, ist die Spec praezise genug.

Erfolgskriterium:

- Rust/HMC reproduziert dieselben Identity-, Trust-, Sync-Krypto- und Device-Delegation-Vektoren wie TypeScript. Abweichungen werden in Spec oder Testvektoren zurueckgefuehrt.

### 4. Demo-App Track

Die Web-of-Trust Demo App ist kein Conformance-Beweis und keine zweite Implementierung. Sie ist der UX-, Mobile-, Offline- und Systembeweis auf Basis der TypeScript-Implementierung.

Erfolgskriterium:

- Ein nicht-technischer Nutzer kann Identitaet erzeugen, wiederherstellen, eine Person per QR verifizieren, Attestations austauschen und verschluesselte Daten ueber Broker/Inbox/Sync auf mehreren Geraeten nutzen.

Kurzform:

```txt
Spec sagt, was korrekt ist.
TypeScript beweist, dass es implementierbar ist.
Rust beweist, dass es interoperabel ist.
Demo App beweist, dass es benutzbar ist.
```

## Milestones

### `v0.1.0-draft`

Erster oeffentlicher Draft-Snapshot.

Release-Kriterien:

- `LICENSE`, `CONTRIBUTING.md`, `VERSIONING.md`, `CHANGELOG.md`, `CONFORMANCE.md` vorhanden.
- Normative Testvektoren liegen unter `test-vectors/`.
- `schemas/` existiert mit Scope und Formatregeln.
- Offene Kernarbeiten sind als GitHub Issues erfasst.
- GitHub Release und Tag `v0.1.0-draft` erstellt.

### `v0.2.0-interop`

Erster Interop-Snapshot zwischen mindestens zwei unabhaengigen Implementierungen.

Release-Kriterien:

- TypeScript Spec-Core und Rust/HMC bestehen die Identity- und Trust-Testvektoren.
- TypeScript Spec-Core besteht die erweiterten Phase-1-Vektoren: DID-Resolution, ECIES, Log-Entry-JWS, Capability-JWS, Log-Payload-Encryption, Admin-Key, Personal-Doc und SD-JWT-VC Trust-List.
- WoT Plaintext Envelope bleibt externe Transport-Envelope-Validierung im Conformance-Kit, nicht TypeScript-Spec-Core.
- Rust/HMC reproduziert mindestens Identity, DID/key encoding, JCS/JWS, Attestation VC-JWS und die fuer HMC relevanten Trust-List-/SD-JWT-VC-Vektoren.
- JSON Schemas fuer Identity-, Trust- und Sync-Objekte sind verfuegbar.
- `wot-identity@0.1` und `wot-trust@0.1` sind praktisch implementierbar ohne offene normative Luecken.
- Abweichungen zwischen TypeScript, Rust/HMC und Spec sind dokumentiert oder behoben.

### `v0.3.0-sync`

Minimaler Sync- und Demo-App-Snapshot.

Release-Kriterien:

- Minimaler Broker-Prototyp spricht Challenge-Response, Inbox und Log-Sync.
- Personal Doc funktioniert mit Append-only Log und AES-GCM.
- Restore/Clone- und `seq`-Kollisionsregeln sind getestet.
- Demo App zeigt den Kernflow: Onboarding, Recovery, QR-Verifikation, Attestation-Austausch, Personal-Doc-Sync und Offline-Outbox.
- Demo App nutzt die TypeScript-Implementierung als Produkt-/UX-Integration, definiert aber keine normativen Protokollregeln.

### `v0.4.0-device-delegation`

Erster Snapshot fuer Per-Device Keys mit self-contained Delegation Proofs.

Release-Kriterien:

- DeviceKeyBinding ist als signiertes Objekt spezifiziert: Identity DID, Device Key, Capabilities, Signaturberechtigungszeitraum und Binding-`iat`.
- Delegated-Attestation-Bundle als JSON-Container fuer Attestations und Verification-Attestations ist spezifiziert.
- Verifikationsregeln fuer `issuer`/`iss` = Identity DID und `kid` = Device Key sind normativ beschrieben.
- Capability-Scopes `sign-attestation`, `sign-verification`, `sign-log-entry`, `broker-auth` und `device-admin` sind definiert.
- Testvektoren fuer gueltige, abgelaufene Delegation und capability-falsche Device-Key-Signaturen liegen vor.
- TypeScript und Rust/HMC koennen DeviceKeyBinding und Delegated-Attestation-Bundle verifizieren.

### `v0.5.0-temporal-key-history`

Erster Snapshot fuer temporale Verifikation von Device-Key-Signaturen.

Release-Kriterien:

- Key-History-Modell ist spezifiziert: Add Device, Revoke Device, Rotate Identity Key.
- Verifikation gegen den Key-State zum Signaturzeitpunkt ist normativ beschrieben.
- `did:key` + WoT-Sigchain und `did:webvh` sind als moegliche History-Traeger abgegrenzt.
- Offline-Export enthaelt die noetigen Chain-Segmente oder eine aequivalente verifizierbare History.
- Testvektoren fuer alte gueltige Signaturen nach spaeterem Device-Revocation liegen vor.

### `v0.6.0-sync-compression`

Erster Snapshot fuer deterministische Log-Kompression.

Release-Kriterien:

- Kompressionsmodell fuer alte Log-History ist spezifiziert.
- Chunk-Grenzen sind deterministisch und koordinatorfrei berechenbar.
- Broker koennen verschluesselte Chunks speichern und nach Hash ausliefern, ohne Klartext zu sehen.
- Testvektoren fuer Chunk-Grenzen, Chunk-IDs und Rehydration liegen vor.

### `v0.7.0-sync-reconciliation`

Erster Snapshot fuer effiziente Set-Reconciliation.

Release-Kriterien:

- Reconciliation-Modell fuer stark divergierte Peers ist spezifiziert.
- RIBLT oder ein gleichwertiges Verfahren ist als Interop-Profil beschrieben.
- Peers koennen fehlende Eintraege oder Chunks proportional zur tatsaechlichen Differenz identifizieren.
- Testvektoren fuer kleine und grosse Divergenzfaelle liegen vor.

### `v1.0.0-identity-trust`

Stabiler Identity-/Trust-Snapshot.

Release-Kriterien:

- Identity- und Trust-Dokumente sind stabil genug fuer langfristige Implementierungen.
- Mindestens zwei unabhaengige Implementierungen interoperieren fuer Identity, JWS, Attestations und Verification.
- Breaking Changes an Identity oder Trust sind danach nur noch per Major Release erlaubt.

## Arbeitsbloecke

### A. Release-Vorbereitung

- Lizenzdatei und Beitragsregeln finalisieren.
- GitHub Issues aus dieser Roadmap anlegen.
- `v0.1.0-draft` Release vorbereiten.

### B. Normative Kanten schaerfen

- `keyAgreement`-Zustaende fuer `did:key` sauber formulieren: signaturfaehig vs. kommunikationsfaehig.
- AES-GCM Nonce-Domain klaeren: `docId` aufnehmen oder formalen Beweis dokumentieren.
- Nonce-only Challenge-Binding in Trust 002 beibehalten und explizit begruenden.
- Inner-JWS-Pflichtfelder fuer Inbox-Nachrichten normativ machen.
- `kid`, `authorKid`, `deviceKid` und Zweckbindung durch alle relevanten Dokumente konsistent halten.
- Capability `kid`/Issuer/Audience-Semantik praezisieren.
- Delegierte Device-Key-Signaturen von Identity-Key-Signaturen sauber abgrenzen.

### C. Testvektoren erweitern

- ECIES: X25519 ECDH + HKDF + AES-256-GCM.
- WoT Plaintext Envelope gegen etablierte DIDComm-v2-Libraries validieren.
- Deterministische Nonce fuer Space/Personal-Doc Payloads.
- `resolve(did:key)` zu DID-Dokument.
- Log-Entry JWS.
- DeviceKeyBinding JWS.
- Delegated-Attestation-Bundle.
- Space Capability JWS.
- Admin-Key-Ableitung aus BIP39 Seed + Space-ID.
- SD-JWT VC Trust List mit Disclosures.

### D. Schemas einfuehren

- QR Challenge.
- DID Document Profil.
- Attestation VC Payload.
- WoT Plaintext Envelope.
- Log Entry Payload.
- Capability Payload.
- Profile-Service Response.
- Space Invite und Key Rotation.
- Trust List Delta.
- DeviceKeyBinding / Delegation Proof.

### E. Device-Key-Delegation spezifizieren

- DeviceKeyBinding-Payload festlegen: `iss`, `sub`, `deviceKid`, `devicePublicKeyMultibase`, `capabilities`, `validFrom`, `validUntil`, `iat`.
- Delegated-Attestation-Bundle als portables Offline-Verifikationsformat definieren.
- Revocation-Semantik fuer Phase 2 klaeren: Best-effort-Revocation vs. Gueltigkeit zum Signaturzeitpunkt.
- Admin-Delegation begrenzen: Welche Geraete duerfen weitere Device Keys delegieren oder widerrufen?
- Migrationspfad zu Phase 3 Temporal Key History festlegen.

### F. Temporal Key History spezifizieren

- Key-History-Events festlegen: Inception, Add Device, Revoke Device, Rotate Identity Key.
- Replay-Regeln definieren: Welcher Device Key war zu welchem Signaturzeitpunkt autorisiert?
- `did:key` + WoT-Sigchain gegen `did:webvh` als History-Traeger abgrenzen.
- Offline-Bundle fuer Chain-Segmente oder DID-History definieren.
- Phase-4-Pfad zu Pre-Rotation / Mini-KERI dokumentieren.

### G. HMC-Extension konkretisieren

- Trust-Score-Algorithmus formal spezifizieren.
- Multipath mit Zyklen und Pfadabhaengigkeiten klaeren.
- Versionierung und Ueberschreiben neuerer Trust-Aussagen definieren.
- Hop-Limit-Propagation normativ machen.
- SD-JWT `cnf` / Key-Binding entscheiden.
- Widerruf / StatusList2021 fuer Trust Lists klaeren.

### H. TypeScript Conformance pflegen

- TypeScript Spec-Core auf neue Testvektoren bringen.
- Spec-Core strikt von Legacy-App-Services, Storage, Messaging, CRDT und UI getrennt halten.
- Vendored Fixtures bytegenau gegen `wot-spec/test-vectors/` abgleichen.
- Attestations, Verification-Flow und Device-Key-Delegation nur dann in App-/Legacy-Services integrieren, wenn die Spec-Core-Abdeckung existiert.

### I. Rust/HMC Conformance aufbauen

- Rust/HMC-Conformance-Harness gegen `wot-spec/test-vectors/*.json` anlegen.
- Identity-Derivation, did:key, JCS/JWS und Attestation VC-JWS zuerst reproduzieren.
- Danach ECIES, Log-Entry-JWS, Capability-JWS, Admin-Key, Personal-Doc und SD-JWT-VC Trust-List-Vektor abdecken.
- Abweichungen nicht lokal wegpatchen, sondern als Spec-/Vektor-/Implementierungsfrage dokumentieren.

### J. Demo App als Systembeweis

- Demo App auf die Spec-nahe TypeScript-Implementierung zurueckfuehren, ohne App-Logik zur Norm zu machen.
- Onboarding, Recovery, QR-Verifikation, Attestation-Austausch, Personal-Doc-Sync und Offline-Outbox als Kernflows stabilisieren.
- Mobile/Web-Realitaet testen: Kamera, IndexedDB, Biometrie/Unlock, Offline, Relay-Ausfall, Wiederherstellung auf neuem Geraet.
- Erkenntnisse aus UX und Betrieb zurueck in Spec, Schemas oder Testvektoren fuehren, wenn sie Protokollrelevanz haben.

### K. Minimalen Broker/Personal-Doc-Sync implementieren

- Broker-Challenge-Response, Inbox, ACKs und Log-Sync minimal lauffaehig machen.
- Personal Doc ueber Append-only Log und AES-GCM synchronisieren.
- Restore/Clone-Erkennung und `seq`-Kollisionen testen.
- Capability-Pruefung und Personal-Doc-Self-Capability im Broker-Pfad verifizieren.

## Nicht Phase 1

- Per-Device Keys und Device-Key-Delegation als vollstaendiges Modell.
- DID-Migration zu `did:webvh`.
- Forward-Secrecy / Double Ratchet fuer Inbox.
- Deterministische Log-Kompression (z.B. Sedimentree) — vorgesehen fuer Sync Phase 2.
- Effiziente Set-Reconciliation (z.B. RIBLT) — vorgesehen fuer Sync Phase 3.
- Feld-Level-Permissions im CRDT.
- Tor/Cover-Traffic/Onion-Routing fuer Metadaten-Schutz.
