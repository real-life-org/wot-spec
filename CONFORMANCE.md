# Konformitaet

Dieses Dokument definiert, wann eine Implementierung als kompatibel mit der Web-of-Trust-Spezifikation gilt.

Die Anforderungen sind in Profile getrennt. Eine Implementierung kann ein Profil unterstuetzen, ohne alle anderen Profile zu implementieren.

## Allgemeine Anforderungen

Eine konforme Implementierung MUSS:

1. Alle fuer das beanspruchte Profil relevanten `MUSS`-Anforderungen erfuellen.
2. Alle relevanten Testvektoren in `test-vectors/` reproduzieren oder verifizieren.
3. Die Terminologie aus `GLOSSARY.md` konsistent interpretieren.
4. Unbekannte optionale Felder ignorieren, sofern das jeweilige Dokument nichts anderes verlangt.
5. Unbekannte Nachrichtentypen sicher ignorieren und nicht als gueltige bekannte Typen behandeln.
6. JWS `alg` strikt gegen die erlaubte Whitelist pruefen.
7. Signaturen ueber exakt die empfangenen JWS-Signing-Input-Bytes verifizieren.

## Profil-Abhaengigkeiten

`wot-identity@0.1` ist die kryptographische Basisschicht. `wot-trust@0.1` und `wot-sync@0.1` bauen darauf auf, sind aber voneinander unabhaengig nutzbar. Implementierungen SOLLTEN genau die Profile ausweisen, die sie tatsaechlich unterstuetzen.

## `wot-identity@0.1`

Eine Implementierung ist `wot-identity@0.1`-konform, wenn sie die folgenden Faehigkeiten besitzt.

### Identitaet und Key-Derivation

- BIP39-Seed mit leerer Passphrase ableiten.
- HKDF-SHA256 mit den spezifizierten Info-Strings verwenden.
- Ed25519-Signing-Key aus `wot/identity/ed25519/v1` ableiten.
- X25519-Encryption-Key aus `wot/encryption/x25519/v1` ableiten.
- `did:key` fuer Ed25519 Public Keys erzeugen und lesen.

### Signaturen

- JWS Compact Serialization mit `alg=EdDSA` erzeugen und verifizieren.
- JCS nach RFC 8785 fuer JSON-Payloads verwenden.
- `kid` im JWS-Header verpflichtend setzen und auswerten.
- Signatur-Keys ueber `resolve(did)` und DID-Dokumente aufloesen.

### DID-Resolution

- `resolve(did)` fuer `did:key` implementieren.
- Ed25519 `verificationMethod`, `authentication` und `assertionMethod` aus `did:key` ableiten.
- Fehlende `keyAgreement`-Informationen fuer `did:key` als nicht kommunikationsfaehigen Zustand behandeln, nicht als Signaturfehler.

## `wot-trust@0.1`

Eine Implementierung ist `wot-trust@0.1`-konform, wenn sie zusaetzlich `wot-identity@0.1` erfuellt und die folgenden Faehigkeiten besitzt.

### Attestations

- W3C VC 2.0 Payloads fuer `WotAttestation` erzeugen und parsen.
- VC-JOSE-COSE JWS (`typ: "vc+jwt"`) fuer Attestations verifizieren.
- `issuer`, `iss`, `credentialSubject.id`, `sub`, `validFrom` und `nbf` konsistent pruefen.
- Nicht verstandene Extension-Felder ignorieren.

### Verifikation

- QR-Challenge-Felder gemaess Trust 002 parsen.
- Verification-Attestations als VC-JWS erzeugen und verifizieren.
- Nonces gegen aktive Challenges und Nonce-History pruefen.
- Online-In-Person-Verifikationen nur bei aktiver, noch nicht verbrauchter Challenge-Nonce akzeptieren.

## `wot-sync@0.1`

Eine Implementierung ist `wot-sync@0.1`-konform, wenn sie zusaetzlich `wot-identity@0.1` erfuellt und die folgenden Faehigkeiten besitzt. `wot-trust@0.1` ist fuer Sync nicht erforderlich.

### Verschluesselung

- AES-256-GCM mit 96-Bit Nonces verwenden.
- ECIES mit X25519, HKDF-SHA256 und AES-256-GCM fuer Inbox-Nachrichten implementieren.
- Gruppen- und Personal-Doc-Payloads vor dem Sync verschluesseln.
- Die Nonce-Konstruktion des jeweiligen Dokuments einhalten.

### Log-Sync

- JWS-signierte Log-Eintraege erzeugen und verifizieren.
- `seq` pro `(deviceId, docId)` strikt monoton fuehren.
- Restore/Clone-Erkennung bei `broker_seq > local_seq` umsetzen.
- Kollisionen fuer `(docId, deviceId, seq)` erkennen und sicher behandeln.
- App-Start- und Reconnect-Flows gemaess Sync 002 ausfuehren: lokalen Zustand laden, Broker authentisieren, Personal Doc zuerst syncen, danach fuer Space-Dokumente ueber Heads/`sync-request` einen Catch-Up durchfuehren.
- Lokale Schreibvorgaenge zuerst persistent als Log-Eintrag speichern und erst danach an Broker/Peers publizieren.
- Log-Eintraege mit fehlender `keyGeneration` als `blocked-by-key` behandeln und nach Key-Catch-Up erneut verarbeiten.
- Snapshots und Full-State-Nachrichten nur als Optimierung mergen und niemals als Ersatz fuer Log-Catch-Up oder als Rollback bekannter gueltiger Eintraege verwenden.

### Transport und Broker

- WoT Plaintext Envelopes erzeugen und parsen, deren JSON-Shape DIDComm-v2-Plaintext-kompatibel ist und `typ: "application/didcomm-plain+json"` setzt.
- Envelope-Testvektoren mit mindestens einer etablierten DIDComm-v2-Library validieren. Diese Validierung prueft nur die Envelope-Kompatibilitaet, nicht DIDComm-JWE/Authcrypt oder DIDComm-Mediator-Protokolle.
- WoT Envelopes nur als ephemeres Transport-Framing behandeln; persistente WoT-Objekte bleiben JWS-/Payload-Objekte im Body.
- Broker-Challenge-Response mit DID-Signaturen umsetzen.
- Capabilities als JWS verifizieren.
- Inbox-Nachrichten pro Device zustellen und ACKs verarbeiten.
- Selbstadressierte Inbox-Nachrichten an andere Devices derselben DID zustellen, ohne das sendende Device als erfolgreich zugestellten Empfaenger zu behandeln.
- Inbox-ACKs nur pro authentifiziertem Device anwenden und erst nach Entschluesselung, Verifikation, Replay-Pruefung und dauerhafter Anwendung oder durablem Pending-Speicher senden.

### Personal Doc und Gruppen

- Personal Doc Key aus `wot/personal-doc/v1` ableiten.
- Personal Doc mit derselben Log-Infrastruktur wie Spaces synchronisieren.
- Space Content Keys und Capability Keys gemaess Sync 001/005 verwalten.
- Invitee Encryption Keys ueber QR-Cache oder DID-Dokument `keyAgreement` aufloesen und fehlende Keys als Invite-Fehler behandeln.
- `space-invite`, `member-update` und `key-rotation` Inbox-Nachrichten erzeugen, parsen und gegen die Space-Membership-Regeln pruefen.
- `member-update` als Zustell- und Pending-UX-Signal behandeln, gegen den naechsten Space-Sync verifizieren, idempotent verarbeiten und stale/future `effectiveKeyGeneration` gemaess Sync 005 anwenden.
- Key-Rotation bei Member-Entfernung verarbeiten.
- Key-Rotation-Generationen exakt nach Sync 005 anwenden: `local+1` anwenden, `<=local` ignorieren, `>local+1` durabel puffern und fehlende Rotationen/Keys ueber Device-Inbox, Personal-Doc-Catch-Up, Space-`sync-request` und optionale Snapshot-/Full-State-Quellen nachladen.
- Nach `space-invite` und `key-rotation` einen Space-Catch-Up per `sync-request` ausloesen.

## `wot-device-delegation@0.1` (geplant)

`wot-device-delegation@0.1` ist ein geplantes Phase-2-Erweiterungsprofil in der Identity-Dokumentfamilie, aber nicht Teil von `wot-identity@0.1`. Eine Implementierung ist konform, wenn sie zusaetzlich `wot-identity@0.1` und `wot-trust@0.1` erfuellt und die folgenden Faehigkeiten besitzt.

- DeviceKeyBinding-JWS mit `typ: "wot-device-key-binding+jwt"` erzeugen und verifizieren.
- `deviceKid`, `sub` und `devicePublicKeyMultibase` konsistent pruefen.
- Capability-Scopes fuer Device Keys strikt pruefen.
- Delegated-Attestation-Bundles als JSON-Container parsen.
- Delegierte Attestations gegen Device Key, Identity-Key-Binding, Attestation-`iat` und normalisierten Delegationszeitraum verifizieren.
- Device-DIDs nicht als eigene soziale Identitaeten im Trust Graph behandeln.

## `wot-rls@0.1`

Eine Implementierung ist `wot-rls@0.1`-konform, wenn sie `wot-trust@0.1` erfuellt und RLS-spezifische Attestation-Felder gemaess `04-rls-extensions/` erzeugt oder sicher ignoriert.

## `wot-hmc@0.1`

Eine Implementierung ist `wot-hmc@0.1`-konform, wenn sie `wot-trust@0.1` und `wot-sync@0.1` erfuellt und HMC-spezifische Trust-Listen, Trust-Scores und Gossip-Nachrichten gemaess `05-hmc-extensions/` erzeugt oder sicher ignoriert.

Fuer vollstaendige HMC-Konformitaet MUESSEN SD-JWT VC Trust-Lists validiert werden:

- JWT-Signatur gegen `iss` pruefen.
- `vct`, `exp`, `iat` und `_sd_alg` pruefen.
- Disclosure-Hashes verifizieren.
- Hop-Limits bei Trust-Propagation einhalten.

## Testvektoren

Die Testvektoren in `test-vectors/` sind Teil der Konformitaet. Eine Implementierung darf ein Profil erst beanspruchen, wenn alle fuer dieses Profil vorhandenen Testvektoren bestanden werden.

Noch fehlende Testvektoren blockieren keine Draft-Konformitaet, MUESSEN aber vor einem stabilen `v1.0.0-identity`, `v1.0.0-trust` oder `v1.0.0-sync` Release ergaenzt werden.

## Conformance Kit

Das Verzeichnis [`conformance/`](conformance/) enthält ein maschinenlesbares Manifest, das Profile auf Spec-Dokumente, Schemas und Testvektor-Sektionen abbildet.

```sh
npm run conformance
```

Dieser Befehl validiert Manifest, Schemas, Testvektoren und den DIDComm-Plaintext-Envelope. Er prüft die Artefakte dieses Repositories; externe Implementierungen müssen die gelisteten Vektoren in ihrer eigenen Sprache reproduzieren.
