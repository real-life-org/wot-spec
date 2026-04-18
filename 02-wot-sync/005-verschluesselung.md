# WoT Sync 005: Verschlüsselung

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-13

## Zusammenfassung

Dieses Dokument spezifiziert wie Daten im Sync Layer verschlüsselt werden — für Peer-to-Peer-Kommunikation (Attestations, Einladungen) und für Gruppen-Verschlüsselung (Spaces).

## Referenzierte Standards

- **X25519** (RFC 7748) — Diffie-Hellman Key Exchange auf Curve25519
- **ECDH-1PU** (IETF Draft) — Authentifiziertes Key Agreement (Authcrypt)
- **JWE** (RFC 7516) — JSON Web Encryption
- **HKDF** (RFC 5869) — Schlüsselableitung aus Shared Secrets
- **AES-256-GCM** (NIST SP 800-38D) — Authentifizierte symmetrische Verschlüsselung
- **DIDComm v2** (DIF) — Messaging-Standard für Verschlüsselung zwischen DIDs

## Verschlüsselungs-Schlüssel

Aus dem Master-Seed (siehe [Core 001](../01-wot-core/001-identitaet-und-schluesselableitung.md)):

```
Master Seed
  → HKDF-SHA256(seed, info="wot/identity/ed25519/v1")    → Ed25519 Signatur-Schlüssel
  → HKDF-SHA256(seed, info="wot/encryption/x25519/v1")   → X25519 Verschlüsselungs-Schlüssel
```

Der Verschlüsselungs-Schlüssel wird auf einem separaten HKDF-Pfad vom Identitäts-Schlüssel abgeleitet. Beide sind deterministisch aus demselben Seed. Beide sind auf allen Geräten des Users verfügbar.

Die birationale Abbildung (Ed25519 → Curve25519 → X25519) ist NICHT erlaubt — Browser-Implementierungen (Web Crypto API) erzeugen Ed25519-Keys als `non-extractable` und können den rohen Private Key nicht für die Umrechnung auslesen. Der separate HKDF-Pfad ist die einzige normative Methode. Siehe [Core 001](../01-wot-core/001-identitaet-und-schluesselableitung.md#weitere-schlüssel).

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

**Für P2P-Verschlüsselung (Authcrypt): zufällig**

Bei Authcrypt wird für jede Nachricht ein **ephemerer X25519-Key** generiert. Der Content Encryption Key (CEK) ist damit pro Nachricht neu — Nonce-Reuse über mehrere Nachrichten ist per Design unmöglich. Die Nonce kann zufällig gewählt werden (12 Bytes).

## Peer-to-Peer-Verschlüsselung (Authcrypt)

Für direkte Nachrichten zwischen zwei Parteien (Attestations, Einladungen, Key-Austausch). Das Verfahren folgt dem **DIDComm Authcrypt** Standard (ECDH-1PU, [RFC Draft](https://datatracker.ietf.org/doc/html/draft-madden-jose-ecdh-1pu)) und verwendet ausschließlich Web Crypto API Operationen.

### Verschlüsselung (Sender → Empfänger)

1. Ephemeres X25519-Schlüsselpaar generieren
2. Zwei ECDH-Operationen durchführen:
   - `shared_secret_static = sender_static_private × recipient_public`
   - `shared_secret_ephemeral = ephemeral_private × recipient_public`
3. Beide Secrets kombinieren und symmetrischen Schlüssel via HKDF-SHA256 ableiten:
   - Input: `shared_secret_ephemeral || shared_secret_static`
   - Salt: leer
   - Info: `"wot/authcrypt/v1"`
   - Ausgabe: 256-Bit AES-Schlüssel
4. Klartext mit AES-256-GCM verschlüsseln
5. Verpacken als JWE (JSON Web Encryption, RFC 7516)

### Entschlüsselung (Empfänger)

1. Ephemeral Public Key und Sender-DID aus dem JWE-Header lesen
2. Zwei ECDH-Operationen durchführen:
   - `shared_secret_static = recipient_private × sender_static_public`
   - `shared_secret_ephemeral = recipient_private × ephemeral_public`
3. Beide Secrets kombinieren, denselben AES-Schlüssel via HKDF ableiten
4. Ciphertext entschlüsseln

### Warum Authcrypt statt ECIES

Authcrypt bindet die Sender-Identität kryptographisch in die Verschlüsselung ein — der Empfänger weiß nicht nur dass die Nachricht für ihn ist, sondern auch **von wem** sie kommt, ohne auf eine separate Signatur angewiesen zu sein. Zusätzlich ist Authcrypt das DIDComm-Standardverfahren, was Interoperabilität mit dem DIDComm-Ökosystem sicherstellt.

### Web Crypto API

Alle Operationen sind nativ in der Web Crypto API verfügbar:
- `crypto.subtle.deriveBits("X25519", ...)` — beide ECDH-Operationen
- `crypto.subtle.deriveBits("HKDF", ...)` — Schlüsselableitung
- `crypto.subtle.encrypt("AES-GCM", ...)` — Verschlüsselung

Keine externe Krypto-Bibliothek nötig.

## Gruppen-Verschlüsselung (Spaces)

Für persistente Gruppen mit geteilten verschlüsselten Daten (CRDT-Dokumente):

### Space-Schlüssel

- Jeder Space hat einen symmetrischen Schlüssel (32 Bytes, zufällig generiert)
- Schlüssel sind versioniert nach **Generation** (monoton aufsteigender Integer, beginnend bei 0)
- Alte Schlüssel werden aufbewahrt um historische Daten entschlüsseln zu können
- Neue Schlüssel werden bei Einladung via ECIES an den neuen Member verteilt

### Schlüsselrotation

Bei Entfernung eines Mitglieds:

1. Neuen Space-Schlüssel generieren (Generation + 1)
2. Neuen Schlüssel an alle verbleibenden Mitglieder via ECIES verteilen
3. Neue Daten werden mit dem neuen Schlüssel verschlüsselt
4. Alte Daten bleiben mit dem alten Schlüssel lesbar (für Mitglieder die damals Zugriff hatten)
5. Das entfernte Mitglied hat den neuen Schlüssel nicht und kann zukünftige Daten nicht lesen

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
| **P2P-Verschlüsselung** | ECIES (X25519 + HKDF + AES-256-GCM) | SecureContainer (X25519 + HKDF + ChaCha20) | ✅ **Authcrypt** (ECDH-1PU + AES-256-GCM) |
| **Gruppen-Verschlüsselung** | Space Keys (zufällig, generationsbasiert) | Nicht eingebaut | ✅ Space Keys |
| **Symmetrischer Algorithmus** | AES-256-GCM (Web Crypto) | ChaCha20-Poly1305 | ✅ AES-256-GCM |
| **HKDF Info (P2P)** | `"wot-ecies-v1"` | `"secure-container-kek"` | **`"wot/authcrypt/v1"`** |
| **X25519-Ableitung** | Separater HKDF-Pfad | Birationale Abbildung | ✅ **Separater HKDF-Pfad** (normativ) |
| **Nonce** | 12 Bytes zufällig | 12 Bytes zufällig | ✅ 12 Bytes zufällig |
| **DIDComm-kompatibel** | Nein (ECIES) | Nein (SecureContainer) | ✅ Ja (Authcrypt + JWE) |
