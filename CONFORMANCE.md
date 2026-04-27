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

## `wot-core@0.1`

Eine Implementierung ist `wot-core@0.1`-konform, wenn sie die folgenden Faehigkeiten besitzt.

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

### Attestations

- W3C VC 2.0 Payloads fuer `WotAttestation` erzeugen und parsen.
- VC-JOSE-COSE JWS (`typ: "vc+jwt"`) fuer Attestations verifizieren.
- `issuer`, `iss`, `credentialSubject.id`, `sub`, `validFrom` und `nbf` konsistent pruefen.
- Nicht verstandene Extension-Felder ignorieren.

### Verifikation

- QR-Challenge-Felder gemaess Core 004 parsen.
- Verification-Attestations als VC-JWS erzeugen und verifizieren.
- Nonces gegen aktive Challenges und Nonce-History pruefen.

### DID-Resolution

- `resolve(did)` fuer `did:key` implementieren.
- Ed25519 `verificationMethod`, `authentication` und `assertionMethod` aus `did:key` ableiten.
- Fehlende `keyAgreement`-Informationen fuer `did:key` als nicht kommunikationsfaehigen Zustand behandeln, nicht als Signaturfehler.

## `wot-sync@0.1`

Eine Implementierung ist `wot-sync@0.1`-konform, wenn sie zusaetzlich `wot-core@0.1` erfuellt und die folgenden Faehigkeiten besitzt.

### Verschluesselung

- AES-256-GCM mit 96-Bit Nonces verwenden.
- ECIES mit X25519, HKDF-SHA256 und AES-256-GCM fuer Inbox-Nachrichten implementieren.
- Gruppen- und Personal-Doc-Payloads vor dem Sync verschluesseln.
- Die Nonce-Konstruktion des jeweiligen Dokuments einhalten.

### Log-Sync

- JWS-signierte Log-Eintraege erzeugen und verifizieren.
- `seq` pro `(deviceId, docId, keyGeneration)` strikt monoton fuehren.
- Restore/Clone-Erkennung bei `broker_seq > local_seq` umsetzen.
- Kollisionen fuer `(docId, deviceId, seq)` erkennen und sicher behandeln.

### Transport und Broker

- DIDComm-v2-kompatible Plaintext Messages mit `typ: "application/didcomm-plain+json"` erzeugen und parsen.
- Envelope-Testvektoren mit mindestens einer etablierten DIDComm-v2-Library validieren.
- Broker-Challenge-Response mit DID-Signaturen umsetzen.
- Capabilities als JWS verifizieren.
- Inbox-Nachrichten pro Device zustellen und ACKs verarbeiten.

### Personal Doc und Gruppen

- Personal Doc Key aus `wot/personal-doc/v1` ableiten.
- Personal Doc mit derselben Log-Infrastruktur wie Spaces synchronisieren.
- Space Content Keys und Capability Keys gemaess Sync 005/009 verwalten.
- Key-Rotation bei Member-Entfernung verarbeiten.

## `wot-rls@0.1`

Eine Implementierung ist `wot-rls@0.1`-konform, wenn sie `wot-core@0.1` erfuellt und RLS-spezifische Attestation-Felder gemaess `03-rls-extensions/` erzeugt oder sicher ignoriert.

## `wot-hmc@0.1`

Eine Implementierung ist `wot-hmc@0.1`-konform, wenn sie `wot-core@0.1` erfuellt und HMC-spezifische Trust-Listen, Trust-Scores und Gossip-Nachrichten gemaess `04-hmc-extensions/` erzeugt oder sicher ignoriert.

Fuer vollstaendige HMC-Konformitaet MUESSEN SD-JWT VC Trust-Lists validiert werden:

- JWT-Signatur gegen `iss` pruefen.
- `vct`, `exp`, `iat` und `_sd_alg` pruefen.
- Disclosure-Hashes verifizieren.
- Hop-Limits bei Trust-Propagation einhalten.

## Testvektoren

Die Testvektoren in `test-vectors/` sind Teil der Konformitaet. Eine Implementierung darf ein Profil erst beanspruchen, wenn alle fuer dieses Profil vorhandenen Testvektoren bestanden werden.

Noch fehlende Testvektoren blockieren keine Draft-Konformitaet, MUESSEN aber vor einem stabilen `v1.0.0-core` oder `v1.0.0-sync` Release ergaenzt werden.

## Conformance Kit

Das Verzeichnis [`conformance/`](conformance/) enthält ein maschinenlesbares Manifest, das Profile auf Spec-Dokumente, Schemas und Testvektor-Sektionen abbildet.

```sh
npm run conformance
```

Dieser Befehl validiert Manifest, Schemas, Testvektoren und den DIDComm-Plaintext-Envelope. Er prüft die Artefakte dieses Repositories; externe Implementierungen müssen die gelisteten Vektoren in ihrer eigenen Sprache reproduzieren.
