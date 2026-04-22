# WoT Sync 005: Verschlüsselung

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-13

## Zusammenfassung

Dieses Dokument spezifiziert wie Daten im Sync Layer verschlüsselt werden — für Peer-to-Peer-Kommunikation (Attestations, Einladungen) und für Gruppen-Verschlüsselung (Spaces).

## Referenzierte Standards

- **X25519** (RFC 7748) — Diffie-Hellman Key Exchange auf Curve25519
- **ECIES** — Elliptic Curve Integrated Encryption Scheme (X25519 + HKDF + AES-256-GCM)
- **HKDF** (RFC 5869) — Schlüsselableitung aus Shared Secrets
- **AES-256-GCM** (NIST SP 800-38D) — Authentifizierte symmetrische Verschlüsselung

## Implementierungsanforderungen

### Konstante Laufzeit (Constant-Time) — MUSS

Alle kryptographischen Operationen dieses Dokuments MÜSSEN in konstanter Zeit ausgeführt werden — die Ausführungsdauer DARF nicht von geheimen Eingaben (Schlüssel, Klartext, Zwischenwerte) abhängen.

Konkret:

- **AES-GCM Tag-Verifikation:** MUSS per bitweiser Gleichheits-Prüfung geschehen. Abbruch bei ungültigem Tag OHNE klartext-abhängige Zeitdifferenz.
- **X25519 Scalar Multiplication:** MUSS über eine konstant-zeit Implementierung laufen (Montgomery Ladder, keine secret-abhängigen Branches oder Table-Lookups).
- **HKDF / HMAC-Vergleich:** Byte-Vergleiche von MAC- oder Key-Material MÜSSEN über konstant-zeit Operationen erfolgen, NIEMALS über `===` auf Strings oder `==` auf Buffers. In Node.js: `crypto.timingSafeEqual(a, b)` (nicht `crypto.subtle`). Im Browser gibt es keine native Primitive — hier muss eine auditierte Bibliothek verwendet werden (z.B. `@noble/hashes/utils` `equalBytes`). Die Web Crypto API (`crypto.subtle.verify`) führt MAC-Vergleiche intern in konstanter Zeit durch — eigene HMAC-Vergleiche außerhalb davon sind zu vermeiden.

**Normative Implikation:** Implementierungen MÜSSEN die Web Crypto API (`crypto.subtle`) oder eine äquivalent auditierte native Bibliothek (z.B. `@noble/ed25519`, `@noble/hashes`) verwenden. Eigenbau von AES, X25519, HKDF oder HMAC in JavaScript/TypeScript ist NICHT erlaubt — JavaScript-Runtimes bieten keine Garantien für konstante Laufzeit bei bitweisen Operationen auf großen Integern.

**Warum:** Timing-Seitenkanäle erlauben einem Angreifer mit ausreichend vielen Messungen Rückschlüsse auf geheime Werte — besonders bei Decryption-Fehlerpfaden (Padding-Oracles, MAC-Vergleichen). In einem verteilten Protokoll mit vielen Nachrichten von potentiell bösartigen Peers ist dieses Angriffsmodell realistisch. Siehe [Security Analysis M1](../research/security-analysis.md#m1-timing-angriffe-bei-decryption).

## Verschlüsselungs-Schlüssel

Aus dem Master-Seed (siehe [Core 001](../01-wot-core/001-identitaet-und-schluesselableitung.md)):

```
Master Seed
  → HKDF-SHA256(seed, info="wot/identity/ed25519/v1")    → Ed25519 Signatur-Schlüssel
  → HKDF-SHA256(seed, info="wot/encryption/x25519/v1")   → X25519 Verschlüsselungs-Schlüssel
```

Der Verschlüsselungs-Schlüssel wird auf einem separaten HKDF-Pfad vom Identitäts-Schlüssel abgeleitet. Beide sind deterministisch aus demselben Seed. Beide sind auf allen Geräten des Users verfügbar.

Die birationale Abbildung (Ed25519 → Curve25519 → X25519) ist NICHT erlaubt — Browser-Implementierungen (Web Crypto API) erzeugen Ed25519-Keys als `non-extractable` und können den rohen Private Key nicht für die Umrechnung auslesen. Der separate HKDF-Pfad ist die einzige normative Methode. Siehe [Core 001](../01-wot-core/001-identitaet-und-schluesselableitung.md#weitere-schlüssel).

## Encryption Key Discovery

Der X25519 Encryption Public Key ist **nicht** aus der `did:key` ableitbar — die DID kodiert nur den Ed25519 Signing Key. Der Encryption Key wird über einen separaten HKDF-Pfad abgeleitet und muss explizit transportiert werden.

Zwei Transportwege:

1. **QR-Code (In-Person-Verifikation):** Das `enc`-Feld im QR-Code enthält den Base64URL-kodierten X25519 Public Key. Nach dem Scan ist der Key sofort lokal verfügbar — auch offline. Siehe [Core 004](../01-wot-core/004-verifikation.md).

2. **Profil-Service (Online-Discovery):** Der Key wird im Nutzerprofil unter `encryptionPublicKey` veröffentlicht. Clients die keinen QR-Code-Austausch hatten (z.B. bei Space-Einladungen über Dritte) rufen den Key über den Profil-Service ab. Siehe [Sync 008](008-discovery.md).

Clients MÜSSEN den Encryption Key nach dem ersten Empfang lokal cachen. In JWE-Headern (`kid`, `skid`) wird die DID ohne Fragment verwendet — die Auflösung zum X25519-Key geschieht protokollintern über den lokalen Cache, nicht über did:key-Fragment-Auflösung.

## Symmetrische Verschlüsselung

**Algorithmus: AES-256-GCM** (AEAD)

- **Schlüssel:** 256 Bit
- **Nonce:** 96 Bit (12 Bytes) — Konstruktion hängt vom Kontext ab (siehe unten)
- **Auth Tag:** 128 Bit (implizit im Ciphertext)

### Verschlüsseltes Datenformat

```
[12-Byte Nonce | Ciphertext + Authentication Tag]
```

Die Nonce wird dem Ciphertext vorangestellt. AES-256-GCM ist nativ in der Web Crypto API aller Browser verfügbar und Hardware-beschleunigt (AES-NI).

### Nonce-Konstruktion

AES-256-GCM ist **katastrophal unsicher** wenn dieselbe (Key, Nonce)-Kombination zweimal verwendet wird (Authentication-Key-Recovery, Klartext-Recovery). Die Spec definiert zwei verschiedene Nonce-Konstruktionen je nach Kontext:

**Für Gruppen-Verschlüsselung (Space Keys): deterministisch aus Log-Eintrag**

```
Nonce = SHA-256(deviceId || "|" || seq)[0:12]
```

Eindeutigkeit folgt aus den Protokoll-Garantien:

- `seq` ist monoton aufsteigend pro `deviceId` pro `docId` (siehe [Sync 006](006-sync-protokoll.md))
- `deviceId` ist per UUID v4 eindeutig pro Device
- Damit ist `(deviceId, seq)` eindeutig innerhalb eines Dokuments
- Der Space Key ist pro `docId` (und `keyGeneration`) eindeutig
- Folge: `(Space Key, Nonce)` kann nicht kollidieren

Voraussetzung: der Client MUSS vor jedem Schreibvorgang den aktuellen `seq`-Stand aus dem Sync-Protokoll abrufen, nicht nur auf lokalen State vertrauen. Bei einer Divergenz (z.B. nach Device-Restore) MUSS der höhere Wert verwendet werden. Siehe [Sync 006](006-sync-protokoll.md#seq-konsistenz-muss).

**Warum deterministisch statt zufällig:** Zufällige 96-Bit-Nonces kollidieren nach 2^48 Nachrichten mit 50% Wahrscheinlichkeit (Birthday-Paradox). Bei schwacher RNG sind Kollisionen früher möglich. Deterministische Konstruktion eliminiert das Problem komplett.

**Für P2P-Verschlüsselung (ECIES): zufällig**

Bei ECIES wird für jede Nachricht ein **ephemerer X25519-Key** generiert. Der AES-Schlüssel ist damit pro Nachricht neu — Nonce-Reuse über mehrere Nachrichten ist per Design unmöglich. Die Nonce kann zufällig gewählt werden (12 Bytes).

## Peer-to-Peer-Verschlüsselung (ECIES)

Für direkte Nachrichten zwischen zwei Parteien (Attestations, Einladungen, Key-Austausch). Das Verfahren ist **ECIES** (Elliptic Curve Integrated Encryption Scheme) mit X25519, HKDF und AES-256-GCM. Alle Operationen verwenden ausschließlich die Web Crypto API.

### Verschlüsselung (Sender → Empfänger)

1. Ephemeres X25519-Schlüsselpaar generieren
2. ECDH: `shared_secret = ephemeral_private × recipient_public`
3. HKDF-SHA256:
   - Input: `shared_secret`
   - Salt: leer (32 Null-Bytes)
   - Info: `"wot/ecies/v1"`
   - Ausgabe: 256-Bit AES-Schlüssel
4. Klartext mit AES-256-GCM verschlüsseln (zufällige 12-Byte Nonce)
5. Ausgabe: `{ ciphertext, nonce, ephemeralPublicKey }`

### Entschlüsselung (Empfänger)

1. Ephemeral Public Key aus der Nachricht lesen
2. ECDH: `shared_secret = recipient_private × ephemeral_public`
3. Denselben AES-Schlüssel via HKDF ableiten
4. Ciphertext entschlüsseln

### Sender-Authentifizierung

ECIES allein beweist nicht, von wem die Nachricht kommt — der Empfänger weiß nur, dass sie für ihn bestimmt war. Die Sender-Identität wird über eine **separate JWS-Signatur** sichergestellt: Jede 1:1-Nachricht wird vor der Verschlüsselung mit dem Ed25519-Key des Senders signiert (siehe [Core 002](../01-wot-core/002-signaturen-und-verifikation.md)). Der Empfänger entschlüsselt zuerst, dann verifiziert er die Signatur.

### Forward Secrecy — bewusste Limitation

Unser ECIES-Verfahren verwendet einen **ephemeren Sender-Key** aber einen **statischen Empfänger-Key** (der HKDF-abgeleitete X25519-Key des Empfängers, siehe [Core 001](../01-wot-core/001-identitaet-und-schluesselableitung.md)). Das bedeutet:

- Wenn der Empfänger-Private-Key zu einem späteren Zeitpunkt kompromittiert wird, kann ein Angreifer alle aufgezeichneten verschlüsselten Nachrichten rückwirkend entschlüsseln.
- Das Protokoll bietet **kein Perfect Forward Secrecy (PFS)** auf der Inbox-Ebene.

Gründe für diese Wahl:

- **Offline-Fähigkeit:** PFS-Protokolle (Signal, Double Ratchet) brauchen eine initiale Schlüsselaustausch-Phase zwischen zwei Parteien, die beide online sein müssen. WoT muss auch offline funktionieren (Festival, Krise).
- **Asynchrone Zustellung:** Nachrichten werden in die Inbox gelegt, auch wenn der Empfänger wochenlang offline ist. Ein Ratchet-Protokoll würde bei langer Offline-Zeit divergieren.
- **Key-Management-Komplexität:** PFS erfordert fortlaufende Key-Synchronisation zwischen allen Devices eines Users. Unsere Multi-Device-Architektur basiert auf einem gemeinsamen Seed.

**Mitigations:**

- Der Master-Seed MUSS auf dem Gerät stark geschützt werden (siehe [Core 001](../01-wot-core/001-identitaet-und-schluesselableitung.md#seed-schutz-auf-dem-gerät))
- Hochsensitive Nachrichten SOLLTEN eine kurze Lebensdauer in der Inbox haben (nach Zustellung löschen)
- Für zukünftige Hoch-Sensitivitäts-Kanäle kann ein ratcheted Modus als Extension spezifiziert werden

### Verschlüsseltes Nachrichtenformat

```json
{
  "epk": "<Base64URL-kodierter ephemerer X25519 Public Key, 32 Bytes>",
  "nonce": "<Base64URL-kodierte 12-Byte Nonce>",
  "ciphertext": "<Base64URL-kodierter Ciphertext + Auth Tag>"
}
```

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `epk` | String | Ephemerer X25519 Public Key (Base64URL, 32 Bytes) |
| `nonce` | String | AES-256-GCM Nonce (Base64URL, 12 Bytes) |
| `ciphertext` | String | Verschlüsselter Inhalt + AES-GCM Auth Tag (Base64URL) |

### Warum ECIES statt DIDComm Authcrypt

DIDComm v2 spezifiziert ECDH-1PU+A256KW (Authcrypt) — ein Verfahren das die Sender-Identität kryptographisch in die Verschlüsselung einbindet und Multi-Empfänger über CEK + Key Wrapping unterstützt. Wir verwenden stattdessen ECIES + JWS, weil:

- **Kein Multi-Empfänger nötig:** Unsere 1:1-Nachrichten sind tatsächlich 1:1. Wo mehrere Empfänger beteiligt sind (Spaces), nutzen wir symmetrische Gruppen-Keys.
- **Sender-Auth über JWS:** Wir signieren ohnehin jede Nachricht. Eine zweite kryptographische Sender-Bindung in der Verschlüsselungsschicht ist redundant.
- **Einfachheit:** ECIES braucht einen ECDH-Call, Authcrypt zwei. Kein CEK, kein Key Wrapping (AES-KW), weniger Code, weniger Angriffsfläche.
- **Web Crypto API nativ:** Alle ECIES-Operationen sind nativ verfügbar. AES-KW (für A256KW) erfordert zusätzlichen Code.

Interoperabilität mit DIDComm-Clients wird über die Envelope-Ebene hergestellt (siehe [Sync 007](007-transport-und-broker.md)), nicht über die Verschlüsselungsschicht.

### Web Crypto API

Alle Operationen sind nativ in der Web Crypto API verfügbar:
- `crypto.subtle.generateKey("X25519", ...)` — Ephemeres Keypair
- `crypto.subtle.deriveBits("X25519", ...)` — ECDH
- `crypto.subtle.deriveBits("HKDF", ...)` — Schlüsselableitung
- `crypto.subtle.encrypt("AES-GCM", ...)` — Verschlüsselung

Keine externe Krypto-Bibliothek nötig.

## Gruppen-Verschlüsselung (Spaces)

Für persistente Gruppen mit geteilten verschlüsselten Daten (CRDT-Dokumente) hat jeder Space drei Arten von Schlüsseln (siehe [Sync 009](009-gruppen.md)):

| Schlüssel | Typ | Zweck | Kurzname in Protokoll-Feldern |
|---|---|---|---|
| **Space Content Key** | Symmetrisch (AES-256) | Verschlüsselung von Space-Daten und Log-Einträgen | `spaceContentKey` |
| **Space Capability Key Pair** | Asymmetrisch (Ed25519) | Signiert und verifiziert Capabilities für Broker-Zugriff | Private: `spaceCapabilitySigningKey`, Public: `spaceCapabilityVerificationKey` |
| **Admin Key(s)** | Asymmetrisch (Ed25519, aus BIP39-Seed abgeleitet) | Autorisiert Space-Management am Broker (Rotation, Admin-Wechsel) | `adminKey` / `adminDid` |

**Wichtige Abgrenzung:** Der `spaceCapabilitySigningKey` ist **keine Autorenidentität**. Alle Members teilen ihn und können Capabilities damit signieren — eine Signatur mit diesem Key identifiziert also **keinen** bestimmten Member, sondern nur "irgendjemand aus dieser Gruppe". Autorenschaft von Log-Einträgen oder Inbox-Nachrichten wird ausschließlich über die persönliche Ed25519-Identität (DID) nachgewiesen.

### Space Content Key (symmetrisch)

- 32 Bytes, zufällig generiert bei Space-Erstellung
- Versioniert nach **Generation** (monoton aufsteigender Integer, beginnend bei 0)
- Alte Schlüssel werden aufbewahrt um historische Daten entschlüsseln zu können
- Neue Schlüssel werden bei Einladung via ECIES an Members verteilt
- In älteren Entwurfs-Texten auch als "Space Key" referenziert — der offizielle normative Name ist `spaceContentKey`

### Space Capability Key Pair (asymmetrisch)

- Ed25519 Keypair, zufällig generiert bei Space-Erstellung
- Der **Verification Key** (Public) wird beim Broker registriert (für Capability-Verifikation)
- Der **Signing Key** (Private) wird an alle Members verteilt (per ECIES, gemeinsam mit dem Content Key)
- Members signieren damit Capabilities für neue Members — **keine Admin-Signatur nötig**
- Wird bei Member-Entfernung zusammen mit dem Content Key rotiert

**MUSS-Regel:** Der `spaceCapabilitySigningKey` DARF **ausschließlich** zum Signieren von Broker-Capabilities verwendet werden. Er DARF **nicht** für Sender-Authentifizierung, Autoren-Identifikation oder allgemeine Nachrichten-Signaturen eingesetzt werden. Andernfalls würde die Member-Anonymität der Gruppe die Autoren-Identifikation kompromittieren.

### Admin Key (abgeleitet)

Admin Keys werden space-spezifisch aus dem BIP39-Seed des Users abgeleitet. Die Ableitung ist vollständig deterministisch — jeder Admin eines Spaces kann seinen Admin-Key jederzeit aus seinem Seed rekonstruieren.

**Normative Ableitung (MUSS):**

```
IKM  = 64-Byte BIP39-Seed (siehe Core 001 — volle 64 Bytes, nicht der HKDF-abgeleitete Ed25519-Identity-Seed)
salt = leer (32 Null-Bytes)
info = ASCII("wot/space-admin/") || canonical-lowercase-uuid(space-id) || ASCII("/v1")
OKM  = HKDF-SHA256(IKM, salt, info, 32 Bytes)
admin_key_pair = Ed25519 Keypair aus OKM (OKM als Ed25519-Seed)
admin_did = did:key-Enkodierung des admin_key_pair.public_key
```

**Präzisierungen:**

- `IKM` ist exakt der 64-Byte BIP39-Seed aus PBKDF2-HMAC-SHA512 (siehe [Core 001](../01-wot-core/001-identitaet-und-schluesselableitung.md#seed)). **Nicht** der HKDF-abgeleitete 32-Byte Ed25519-Identity-Seed. Damit sind Admin-Keys unabhängig von Identitäts-Schlüsseln — eine Kompromittierung des Ed25519-Identity-Seeds gefährdet nicht automatisch alle Admin-Rollen.
- `space-id` wird in **kanonischer Form** in den info-String kodiert: UUID v4 als 36-Zeichen ASCII-String, hex-Ziffern in lowercase, Bindestriche an Positionen 8-4-4-4-12 (wie RFC 9562). Beispiel: `"7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b"`.
- Der info-String ist die UTF-8/ASCII-Byte-Folge — keine JSON-Serialisierung, kein Trailing-Null.
- Ausgabe-Länge ist exakt 32 Bytes; diese Bytes werden direkt als Ed25519 Private Key Seed verwendet.

Eigenschaften:

- **Space-spezifisch:** Jeder Space hat einen eigenen Admin Key pro Admin
- **Nicht verknüpfbar:** Der abgeleitete Admin Key hat keine direkte Verbindung zur Haupt-DID des Admins — der Broker kann Admin-Rollen nicht cross-Space korrelieren
- **Reproduzierbar:** Der Admin kann seinen Admin Key jederzeit aus dem Identity-Seed + Space-ID neu ableiten (kein separates Key-Backup nötig)

Der Admin-Public-Key wird beim Broker registriert. Broker-Management-Nachrichten (Rotation, Admin-Wechsel) werden mit dem Admin-Private-Key signiert.

### Schlüsselrotation

Bei Entfernung eines Mitglieds werden **Space Key und Space Keypair gemeinsam rotiert**:

1. Neuer Space Key generieren (Generation + 1)
2. Neues Space Keypair generieren
3. Admin sendet `space-rotate`-Nachricht an Broker (signiert mit Admin Key) — neuer Space Public Key wird aktiv, alte Capabilities ungültig
4. Admin verteilt neuen Space Key + neuen Space Private Key + neue Capability an alle verbleibenden Mitglieder via ECIES
5. Neue Daten werden mit dem neuen Space Key verschlüsselt
6. Alte Daten bleiben mit dem alten Space Key lesbar (für Mitglieder die damals Zugriff hatten)
7. Das entfernte Mitglied hat weder neuen Space Key noch gültige Capability

### Encrypt-then-Sync

CRDT-Änderungen werden vor der Synchronisierung verschlüsselt. Jeder Log-Eintrag (siehe [Sync 006](006-sync-protokoll.md)) enthält:

- Verschlüsselten Payload (AES-256-GCM mit dem Space-Schlüssel)
- Nonce
- Generation (welcher Schlüssel wurde verwendet)

Der Broker sieht niemals Klartext.

## Speicher-Verschlüsselung (At Rest)

Wie Seed und andere sensible Daten auf dem Gerät geschützt werden ist Sache der Implementierung (siehe [Core 001](../01-wot-core/001-identitaet-und-schluesselableitung.md), Abschnitt "Seed-Schutz auf dem Gerät").

## Aktuelle Implementierungen

| | WoT Core | Human Money Core | Spec |
|---|---|---|---|
| **P2P-Verschlüsselung** | ECIES (X25519 + HKDF + AES-256-GCM) | SecureContainer (X25519 + HKDF + ChaCha20) | ✅ **ECIES** (X25519 + HKDF + AES-256-GCM) |
| **Gruppen-Verschlüsselung** | Space Keys (zufällig, generationsbasiert) | Nicht eingebaut | ✅ Space Keys |
| **Symmetrischer Algorithmus** | AES-256-GCM (Web Crypto) | ChaCha20-Poly1305 | ✅ AES-256-GCM |
| **HKDF Info (P2P)** | `"wot-ecies-v1"` | `"secure-container-kek"` | **`"wot/ecies/v1"`** |
| **X25519-Ableitung** | Separater HKDF-Pfad | Birationale Abbildung | ✅ **Separater HKDF-Pfad** (normativ) |
| **Nonce** | 12 Bytes zufällig | 12 Bytes zufällig | ✅ 12 Bytes zufällig |
| **DIDComm-kompatibel** | Nein (ECIES) | Nein (SecureContainer) | Envelope-Ebene (siehe Sync 007) |
