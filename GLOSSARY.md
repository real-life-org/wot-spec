# Glossar

Dieses Glossar definiert die zentralen Begriffe der Web-of-Trust-Spezifikation. Normative Dokumente SOLLTEN diese Begriffe konsistent verwenden.

## Normative Sprache

Die Spezifikation verwendet die folgenden Begriffe im Sinne von RFC 2119/RFC 8174, aber deutschsprachig:

| Begriff | Bedeutung |
|---|---|
| **MUSS** | Zwingende Anforderung. Eine Implementierung ist nicht konform, wenn sie diese Anforderung verletzt. |
| **DARF NICHT** | Zwingendes Verbot. |
| **SOLLTE** | Starke Empfehlung. Abweichungen brauchen einen dokumentierten Grund. |
| **DARF** | Erlaubnis oder optionale Fähigkeit. |

Nicht-normative Abschnitte (z.B. `research/`) koennen bewusst freier formulieren. Normative Anforderungen stehen in `01-wot-core/`, `02-wot-sync/`, `03-rls-extensions/`, `04-hmc-extensions/`, `CONFORMANCE.md`, `schemas/` und `test-vectors/`.

## Identitaet und Keys

| Begriff | Definition |
|---|---|
| **DID** | Decentralized Identifier einer Person, eines Admin-Keys oder eines anderen kryptographischen Subjekts. Phase 1 nutzt primaer `did:key`. |
| **DID-Dokument** | Aufgeloestes Dokument zu einer DID. Enthaelt Verification Methods, Key-Zwecke und optional Service-Endpoints. |
| **Verification Method** | Ein konkreter Public Key im DID-Dokument, referenziert durch eine DID-URL wie `did:key:z6Mk...#sig-0`. |
| **`kid`** | Key Identifier im JWS-Header. Fuer DID-gebundene Signaturen ist `kid` eine DID-URL. Fuer Space-Capabilities ist `kid` ein Space-Kontext wie `wot:space:<spaceId>#cap-<generation>`. |
| **`authorKid`** | Verification Method ID des Autors eines Log-Eintrags. Ersetzt alte `authorDid`-Formulierungen. |
| **`deviceId`** | Zufaellige UUID eines lokalen Devices. Dient als Sequenz- und Nonce-Namespace, ist aber kein kryptographischer Key. |
| **`deviceKid`** | Zukuenftige DID-URL eines Per-Device-Keys. In Phase 1 optional/vorbereitet, aber noch nicht sicherheitskritisch. |
| **Identity Key** | Ed25519-Key der Hauptidentitaet. Aus `wot/identity/ed25519/v1` abgeleitet. Normative Texte SOLLTEN nicht mehr pauschal von "Master Key" sprechen. |
| **Encryption Key** | X25519-Key fuer ECIES-Inbox-Nachrichten. Aus `wot/encryption/x25519/v1` abgeleitet und nicht aus der `did:key` ableitbar. |

## Attestations und Credentials

| Begriff | Definition |
|---|---|
| **Attestation** | Signierte Aussage ueber eine Person, typischerweise als W3C VC 2.0 Payload mit JWS (`typ: "vc+jwt"`). |
| **Verification-Attestation** | Spezielle Attestation, die eine reale Begegnung und eine Challenge-Response-Verifikation bestaetigt. |
| **Trust List** | HMC-spezifisches gebuendeltes Vertrauensdokument, kodiert als SD-JWT VC. |
| **SD-JWT VC** | Selective-Disclosure JWT Verifiable Credential. Wird fuer HMC Trust Lists verwendet. |

## Sync und Transport

| Begriff | Definition |
|---|---|
| **Broker** | Immer-online Peer fuer Store-and-Forward, Inbox, Log-Sync und Push-Notifications. Kein vertrauenswuerdiger Klartext-Server. |
| **Inbox-Broker** | Broker fuer direkte 1:1-Nachrichten an eine DID. Kann im DID-Dokument oder Profil-Service veroeffentlicht werden. |
| **Space-Broker** | Broker fuer ein bestimmtes Space-Dokument. Wird in Space-Einladungen transportiert und nicht oeffentlich im DID-Dokument veroeffentlicht. |
| **DIDComm Plaintext Envelope** | DIDComm-v2-kompatible Plaintext Message mit `typ: "application/didcomm-plain+json"`. Der Anspruch gilt auf Envelope-Ebene, nicht fuer DIDComm-JWE/Authcrypt. |
| **WoT Envelope-JWS** | WoT-spezifisch signierter Envelope. Strukturell an DIDComm Signed Messages angelehnt, aber nicht als library-validierte DIDComm Signed Message beansprucht. |
| **ECIES** | WoT-Verschluesselung fuer 1:1-Inbox-Nachrichten: X25519 + HKDF-SHA256 + AES-256-GCM. |
| **Log-Eintrag** | JWS-signierter Datensatz im Append-only Log eines Dokuments. Enthaelt u.a. `seq`, `deviceId`, `docId`, `authorKid`, `keyGeneration`, `data`. |
| **`seq`** | Monoton steigende Sequenznummer pro `(deviceId, docId, keyGeneration)`. Sicherheitskritisch fuer deterministische Nonces. |
| **`docId`** | Dokument-ID fuer Space- oder Personal-Doc-Logs. |

## Spaces und Gruppen

| Begriff | Definition |
|---|---|
| **Space** | Gemeinsames verschluesseltes Dokument einer Gruppe. |
| **Space Content Key** | Symmetrischer AES-256-Key fuer Space-Daten und Log-Payloads. Pro Generation versioniert. Kurzname: `spaceContentKey`. |
| **Space Capability Key Pair** | Ed25519-Keypair fuer Broker-Capabilities eines Spaces. Private/Signing Key: `spaceCapabilitySigningKey`; Public/Verification Key: `spaceCapabilityVerificationKey`. |
| **Space Capability Signing Key** | Geteilter privater Ed25519-Key, den Members ausschliesslich zum Signieren von Broker-Capabilities verwenden duerfen. Er ist keine Autorenidentitaet. |
| **Space Capability Verification Key** | Public Key, den Broker zur Verifikation von Space-Capabilities verwenden. |
| **Capability** | JWS, das Broker-Zugriff auf ein Dokument fuer eine DID autorisiert. Space-Capabilities werden mit dem `spaceCapabilitySigningKey` signiert. |
| **Admin Key** | Space-spezifischer, aus dem BIP39-Seed abgeleiteter Ed25519-Key fuer Broker-Management-Nachrichten. Als DID kodiert (`adminDid`), aber nicht mit der Haupt-DID verknuepfbar. |
| **Key Generation** | Monoton steigende Generation eines Space Content Keys und des zugehoerigen Space Capability Key Pairs. |

## Personal Doc

| Begriff | Definition |
|---|---|
| **Personal Doc** | Persoenliches, verschluesseltes Dokument eines Users fuer Profil, Devices, Kontakte und lokale Zustandsdaten. |
| **Personal Doc Key** | Deterministisch aus `wot/personal-doc/v1` abgeleiteter AES-256-Key. |
| **Self-Addressed Message** | Sync-Nachricht von einer DID an dieselbe DID, damit andere eigene Devices den Personal-Doc-State erhalten. |
