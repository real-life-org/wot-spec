# WoT Spec 003: Verschlüsselung

- **Status:** Entwurf
- **Autoren:** Anton Tranelis, Sebastian Galek
- **Datum:** 2026-04-13

## Zusammenfassung

Dieses Dokument spezifiziert wie Daten im Web of Trust verschlüsselt werden — sowohl für Peer-to-Peer-Kommunikation als auch für Gruppen-Verschlüsselung (Spaces).

## Referenzierte Standards

- **X25519** (RFC 7748) — Diffie-Hellman Key Exchange auf Curve25519
- **HKDF** (RFC 5869) — Schlüsselableitung aus Shared Secrets
- **AES-256-GCM** (NIST SP 800-38D) — Authentifizierte symmetrische Verschlüsselung
- **ChaCha20-Poly1305** (RFC 7539) — Alternative authentifizierte Verschlüsselung

## Verschlüsselungs-Schlüssel

Aus dem Master-Seed (siehe [Spec 001](001-identitaet-und-schluesselableitung.md)):

```
Master Seed
  → HKDF-SHA256(seed, info="wot/identity/ed25519/v1")    → Ed25519 Signatur-Schlüssel
  → HKDF-SHA256(seed, info="wot/encryption/x25519/v1")   → X25519 Verschlüsselungs-Schlüssel
```

Der Verschlüsselungs-Schlüssel wird auf einem separaten HKDF-Pfad vom Identitäts-Schlüssel abgeleitet. Beide sind deterministisch aus demselben Seed.

**Ed25519 → X25519 Konvertierung:**

Alternativ DÜRFEN Implementierungen den X25519-Schlüssel direkt aus dem Ed25519-Schlüssel über die birationale Abbildung (Montgomery-Form) ableiten. Beide Ansätze erzeugen gültige X25519-Schlüssel.

## Peer-to-Peer-Verschlüsselung (ECIES)

Für Nachrichten zwischen zwei Parteien verwendet das Protokoll ein ECIES-ähnliches Schema:

### Verschlüsselung (Sender → Empfänger)

1. Ephemeres X25519-Schlüsselpaar generieren
2. ECDH durchführen: `shared_secret = ephemeral_private × recipient_public`
3. Symmetrischen Schlüssel via HKDF-SHA256 ableiten:
   - Input: Shared Secret (32 Bytes)
   - Salt: leer (32 Null-Bytes)
   - Info: Kontext-String (siehe unten)
   - Ausgabe: 256-Bit symmetrischer Schlüssel
4. Klartext mit authentifizierter Verschlüsselung verschlüsseln (siehe Symmetrische Verschlüsselung unten)
5. Ausgabe: `{ ephemeral_public_key, nonce, ciphertext }`

### Entschlüsselung (Empfänger)

1. ECDH durchführen: `shared_secret = recipient_private × ephemeral_public`
2. Denselben symmetrischen Schlüssel via HKDF ableiten (gleiche Parameter)
3. Ciphertext entschlüsseln

## Multi-Empfänger-Verschlüsselung

Für Daten die von mehreren Empfängern lesbar sein müssen (z.B. Space-Einladungen):

### Ablauf

1. Zufälligen 32-Byte Payload-Schlüssel generieren
2. Die eigentlichen Daten mit dem Payload-Schlüssel verschlüsseln (symmetrisch)
3. Für jeden Empfänger:
   - ECDH: `shared_secret = ephemeral_private × recipient_public`
   - Key Encryption Key (KEK) via HKDF ableiten
   - Payload-Schlüssel mit dem KEK verschlüsseln (wrappen)
   - Speichern: `{ empfaenger_id_hash, wrapped_key }`
4. Für den Sender (Selbst-Zugriff):
   - ECDH: `shared_secret = sender_private × ephemeral_public`
   - KEK ableiten, Payload-Schlüssel wrappen
   - Als Sender-Eintrag speichern

### Ausgabe-Struktur

```
{
  ephemeral_public_key,
  wrapped_keys: [
    { matcher: hash(empfaenger_id), wrapped_key },
    { matcher: hash(empfaenger_id), wrapped_key },
    { sender: true, wrapped_key }
  ],
  encrypted_payload,
  signature
}
```

### Entschlüsselung

1. Eigenen Eintrag in `wrapped_keys` finden (über ID-Hash-Matching)
2. Shared Secret und KEK ableiten
3. Payload-Schlüssel unwrappen
4. Payload entschlüsseln

Die Matcher sind gehashte Empfänger-IDs — der Container verrät nicht im Klartext wer die Empfänger sind.

## Gruppen-Verschlüsselung (Spaces)

Für persistente Gruppen mit geteilten verschlüsselten Daten (CRDT-Dokumente):

### Space-Schlüssel-Verwaltung

- Jeder Space hat einen symmetrischen Schlüssel (32 Bytes, zufällig generiert)
- Schlüssel sind versioniert nach **Generation** (monoton aufsteigender Integer)
- Alte Schlüssel werden aufbewahrt um historische Daten entschlüsseln zu können
- Neue Schlüssel werden bei Einladung via Peer-to-Peer-Verschlüsselung (ECIES) verteilt

### Schlüsselrotation

Bei Entfernung eines Mitglieds:
1. Neuen Space-Schlüssel generieren (Generation + 1)
2. Neuen Schlüssel an alle verbleibenden Mitglieder via ECIES verteilen
3. Neue Daten werden mit dem neuen Schlüssel verschlüsselt
4. Alte Daten bleiben mit dem alten Schlüssel lesbar (für Mitglieder die damals Zugriff hatten)

### Encrypt-then-Sync

CRDT-Änderungen werden vor der Synchronisierung verschlüsselt:

```
{
  ciphertext,
  nonce,
  space_id,
  generation,     // Welche Schlüssel-Version wurde verwendet
  from_did        // Autor
}
```

Das ermöglicht Ende-zu-Ende-verschlüsselte Zusammenarbeit — der Relay/Broker sieht niemals Klartext.

## Symmetrische Verschlüsselung

Authentifizierte Verschlüsselung (AEAD) mit:

- **Schlüssel:** 256 Bit
- **Nonce:** 96 Bit (12 Bytes), zufällig generiert pro Verschlüsselung
- **Auth Tag:** 128 Bit (implizit im Ciphertext)

### Verschlüsseltes Datenformat

```
[12-Byte Nonce | Ciphertext | Authentication Tag]
```

Die Nonce wird dem Ciphertext vorangestellt. Der Authentication Tag wird angehängt (oder ist im Ciphertext enthalten, abhängig von der Bibliothek).

## Speicher-Verschlüsselung (At Rest)

Wie der Seed und andere sensible Daten auf dem Gerät geschützt werden ist Sache der Implementierung (siehe [Spec 001](001-identitaet-und-schluesselableitung.md), Abschnitt "Seed-Schutz auf dem Gerät").

## Aktuelle Implementierungen

| | WoT Core | Human Money Core | Spec |
|---|---|---|---|
| **P2P-Verschlüsselung** | ECIES (X25519 + HKDF + AES-256-GCM) | SecureContainer (X25519 + HKDF + ChaCha20-Poly1305) | ❓ |
| **Multi-Empfänger** | Nicht eingebaut | Double-Key-Wrapping (Sender + N Empfänger) | ❓ |
| **Gruppen-Verschlüsselung** | Space Keys (zufällig, generationsbasiert) | Nicht eingebaut | ❓ |
| **HKDF Info (P2P)** | `"wot-ecies-v1"` | `"secure-container-kek"` | ❓ |
| **Symmetrischer Algorithmus** | AES-256-GCM (Web Crypto) | ChaCha20-Poly1305 | ✅ AES-256-GCM (Core), ChaCha20 in Extensions |
| **Ed25519 → X25519** | Separater HKDF-Pfad | Birationale Abbildung (Montgomery) | ❓ |
| **Nonce** | 12 Bytes zufällig | 12 Bytes zufällig | ✅ 12 Bytes zufällig |

## Offene Fragen

### 1. HKDF Info-String für P2P-Verschlüsselung

WoT Core verwendet `"wot-ecies-v1"`, Human Money Core verwendet `"secure-container-kek"`. Für Interoperabilität muss ein gemeinsamer String gewählt werden. Der konsistente Name wäre `"wot/ecies/v1"` — erfordert aber Migration auf beiden Seiten. Verknüpft mit der gleichen Frage in [Spec 001](001-identitaet-und-schluesselableitung.md) (HKDF Info für Identity). Wenn migriert wird, dann alles gleichzeitig. Entscheidung: jetzt (wenige User, geringe Kosten) oder nie (bestehende Strings als Standard akzeptieren).

### 2. Symmetrischer Algorithmus: AES-256-GCM oder ChaCha20-Poly1305?

✅ **Entschieden: AES-256-GCM im Core-Protokoll** (Sync, Spaces, P2P-Verschlüsselung). Nativ in der Web Crypto API aller Browser, Hardware-beschleunigt (AES-NI).

Human Money Core nutzt ChaCha20-Poly1305 intern (SecureContainer, File Storage) — das betrifft die Interoperabilität nicht, weil Sebastians Verschlüsselung in seiner Anwendungsschicht lebt, nicht in der Sync-Schicht. Extensions DÜRFEN ChaCha20-Poly1305 verwenden.

### 3. Multi-Empfänger-Format

Soll Sebastians SecureContainer-Pattern (Double-Key-Wrapping mit anonymen Matchern) Teil des Core werden? Oder ist es eine Extension? WoT Core hat aktuell keine Multi-Empfänger-Verschlüsselung.

### 4. X25519-Ableitung

Separater HKDF-Pfad (kryptographisch unabhängige Schlüssel) oder Ed25519 → X25519 Konvertierung (einfacher, ein Schlüsselpaar)? Die HKDF-Variante ist sauberer, die Konvertierung ist verbreiteter.

### 5. Gruppen-Schlüssel-Verteilung

Gehört die Space-Key-Verwaltung (Generationen, Rotation, Verteilung) in den Core oder in eine Extension (z.B. zusammen mit Spec 008 Mitgliedschaft)?

### 6. Zwei-Schema-Ansatz

Aus der Forschung (p2panda, secsync): Symmetrische Verschlüsselung für geteilte Daten (Spaces) und Double Ratchet für 1:1-Nachrichten (Forward Secrecy). Soll die Spec diesen Zwei-Schema-Ansatz übernehmen? Double Ratchet wäre eine signifikante Erweiterung.
