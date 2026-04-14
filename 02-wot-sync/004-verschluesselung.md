# WoT Sync 004: Verschlüsselung

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-13

## Zusammenfassung

Dieses Dokument spezifiziert wie Daten im Sync Layer verschlüsselt werden — für Peer-to-Peer-Kommunikation (Attestations, Einladungen) und für Gruppen-Verschlüsselung (Spaces).

## Referenzierte Standards

- **X25519** (RFC 7748) — Diffie-Hellman Key Exchange auf Curve25519
- **HKDF** (RFC 5869) — Schlüsselableitung aus Shared Secrets
- **AES-256-GCM** (NIST SP 800-38D) — Authentifizierte symmetrische Verschlüsselung

## Verschlüsselungs-Schlüssel

Aus dem Master-Seed (siehe [Core 001](../01-wot-core/001-identitaet-und-schluesselableitung.md)):

```
Master Seed
  → HKDF-SHA256(seed, info="wot/identity/ed25519/v1")    → Ed25519 Signatur-Schlüssel
  → HKDF-SHA256(seed, info="wot/encryption/x25519/v1")   → X25519 Verschlüsselungs-Schlüssel
```

Der Verschlüsselungs-Schlüssel wird auf einem separaten HKDF-Pfad vom Identitäts-Schlüssel abgeleitet. Beide sind deterministisch aus demselben Seed. Beide sind auf allen Geräten des Users verfügbar.

Alternativ DÜRFEN Implementierungen den X25519-Schlüssel direkt aus dem Ed25519-Schlüssel über die birationale Abbildung (Montgomery-Form) ableiten. Beide Ansätze erzeugen gültige X25519-Schlüssel.

## Symmetrische Verschlüsselung

**Algorithmus: AES-256-GCM** (AEAD)

- **Schlüssel:** 256 Bit
- **Nonce:** 96 Bit (12 Bytes), zufällig generiert pro Verschlüsselung
- **Auth Tag:** 128 Bit (implizit im Ciphertext)

### Verschlüsseltes Datenformat

```
[12-Byte Nonce | Ciphertext + Authentication Tag]
```

Die Nonce wird dem Ciphertext vorangestellt. AES-256-GCM ist nativ in der Web Crypto API aller Browser verfügbar und Hardware-beschleunigt (AES-NI).

## Peer-to-Peer-Verschlüsselung (ECIES)

Für direkte Nachrichten zwischen zwei Parteien (Attestations, Einladungen, Key-Austausch):

### Verschlüsselung (Sender → Empfänger)

1. Ephemeres X25519-Schlüsselpaar generieren
2. ECDH durchführen: `shared_secret = ephemeral_private × recipient_public`
3. Symmetrischen Schlüssel via HKDF-SHA256 ableiten:
   - Input: Shared Secret (32 Bytes)
   - Salt: leer
   - Info: `"wot/ecies/v1"`
   - Ausgabe: 256-Bit AES-Schlüssel
4. Klartext mit AES-256-GCM verschlüsseln
5. Ausgabe: `{ ephemeral_public_key, nonce, ciphertext }`

### Entschlüsselung (Empfänger)

1. ECDH durchführen: `shared_secret = recipient_private × ephemeral_public`
2. Denselben AES-Schlüssel via HKDF ableiten (gleiche Parameter)
3. Ciphertext entschlüsseln

Der ephemere Schlüssel wird nur einmal verwendet — jede Nachricht hat einen neuen.

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

CRDT-Änderungen werden vor der Synchronisierung verschlüsselt. Jeder Log-Eintrag (siehe [Sync 005](005-sync-protokoll.md)) enthält:

- Verschlüsselten Payload (AES-256-GCM mit dem Space-Schlüssel)
- Nonce
- Generation (welcher Schlüssel wurde verwendet)

Der Broker sieht niemals Klartext.

## Speicher-Verschlüsselung (At Rest)

Wie Seed und andere sensible Daten auf dem Gerät geschützt werden ist Sache der Implementierung (siehe [Core 001](../01-wot-core/001-identitaet-und-schluesselableitung.md), Abschnitt "Seed-Schutz auf dem Gerät").

## Zukünftige Erweiterungen

Für 1:1-Nachrichten mit Forward Secrecy könnte in Zukunft ein Double-Ratchet-Protokoll (wie bei Signal) evaluiert werden. Aktuell bietet ECIES mit ephemeren Schlüsseln ausreichenden Schutz für unsere Anwendungsfälle.

## Aktuelle Implementierungen

| | WoT Core | Human Money Core | Spec |
|---|---|---|---|
| **P2P-Verschlüsselung** | ECIES (X25519 + HKDF + AES-256-GCM) | SecureContainer (X25519 + HKDF + ChaCha20) | ✅ ECIES + AES-256-GCM |
| **Gruppen-Verschlüsselung** | Space Keys (zufällig, generationsbasiert) | Nicht eingebaut | ✅ Space Keys |
| **Symmetrischer Algorithmus** | AES-256-GCM (Web Crypto) | ChaCha20-Poly1305 | ✅ AES-256-GCM |
| **HKDF Info (P2P)** | `"wot-ecies-v1"` | `"secure-container-kek"` | **`"wot/ecies/v1"`** |
| **X25519-Ableitung** | Separater HKDF-Pfad | Birationale Abbildung | ✅ Beide erlaubt |
| **Nonce** | 12 Bytes zufällig | 12 Bytes zufällig | ✅ 12 Bytes zufällig |
| **Multi-Empfänger** | Nicht eingebaut | SecureContainer (Double-Key-Wrapping) | Nicht im Sync Layer (siehe Extensions) |
