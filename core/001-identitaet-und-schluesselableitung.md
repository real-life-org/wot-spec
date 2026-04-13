# WoT Spec 001: Identität und Schlüsselableitung

- **Status:** Entwurf
- **Autoren:** Anton Tranelis, Sebastian Galek
- **Datum:** 2026-04-13

## Zusammenfassung

Dieses Dokument spezifiziert wie eine Web-of-Trust-Identität aus einem BIP39-Mnemonic abgeleitet wird. Das Ziel ist ein deterministischer Pfad vom Mnemonic zur DID — so dass verschiedene Implementierungen aus demselben Seed dieselbe Identität erzeugen.

## Referenzierte Standards

- **BIP39** — Mnemonic-Generierung und Seed-Ableitung
- **HKDF** (RFC 5869) — Schlüsselableitung
- **Ed25519** (RFC 8032) — Signaturalgorithmus
- **DID Core** (W3C Recommendation) — `did:key` als DID-Methode
- **Multicodec** — `0xed01` Präfix für Ed25519 Public Keys
- **Multibase** — `z` Präfix für Base58btc-Kodierung

## Ableitungspfad

```
BIP39 Mnemonic (12+ Wörter, beliebige gültige Wortliste)
  → BIP39 Seed (PBKDF2-HMAC-SHA512, 2048 Runden, Passphrase="") → 64 Bytes
  → HKDF-SHA256(seed, info="wot/identity/ed25519/v1") → 32 Bytes
  → Ed25519 Schlüsselpaar
  → did:key (Multicodec 0xed01 + Base58btc)
```

Selbes Mnemonic → selbe DID. Über alle Implementierungen, Sprachen und Anwendungen hinweg.

## Spezifikation

### Entropie (BIP39)

- **Standard:** BIP39
- **Entropie:** Mindestens 128 Bit (12 Wörter)
- **Wortliste:** Implementierungsdefiniert. Die Wortliste beeinflusst die abgeleitete Identität nicht, solange es eine gültige BIP39-Wortliste ist. Implementierungen SOLLTEN die englische BIP39-Wortliste für Interoperabilität unterstützen.

### Seed

- **Standard:** BIP39-Seed-Ableitung (PBKDF2-HMAC-SHA512, 2048 Runden, wie in BIP39 definiert)
- **Passphrase:** Immer leerer String `""`. Keine benutzerdefinierte Passphrase.
- **Ausgabe:** 64 Bytes (vollständig verwendet, kein Slicing)

Die Passphrase ist absichtlich fixiert. Eine benutzerdefinierte Passphrase würde die Determinismus-Garantie brechen: selbes Mnemonic + verschiedene Passphrase = verschiedene Identität. Im Web of Trust gilt: **ein Mnemonic = eine Identität, immer.**

### Schlüsselableitung

HKDF-SHA256 mit:
- **Input Key Material:** Volle 64 Bytes des BIP39-Seeds
- **Salt:** leer (kein Salt)
- **Info:** `"wot/identity/ed25519/v1"`
- **Ausgabe:** 32 Bytes (Ed25519-Seed)

Ob zusätzliches Key-Stretching vor der HKDF-Ableitung angewendet wird, ist eine offene Frage (siehe Offene Frage 2).

### Identität

- **Signaturalgorithmus:** Ed25519
- **Eingabe:** 32-Byte Seed aus HKDF
- **DID-Methode:** `did:key` mit Multicodec-Präfix `0xed01` (Ed25519 Public Key), Base58-BTC kodiert

Beispiel: `did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK`

### Weitere Schlüssel

Aus demselben Seed werden weitere Schlüssel abgeleitet. Jeder Schlüssel verwendet einen eigenen HKDF-Info-String:

| Schlüssel | HKDF Info | Zweck | Spezifiziert in |
|-----------|-----------|-------|----------------|
| Signatur (Master) | `"wot/identity/ed25519/v1"` | Identität, Attestations | Dieses Dokument |
| Verschlüsselung | `"wot/encryption/x25519/v1"` | Asymmetrische Verschlüsselung (X25519) | [Spec 004](../sync/004-verschluesselung.md) |

Alle Schlüssel sind deterministisch aus demselben Seed ableitbar. Durch die verschiedenen Info-Strings sind sie kryptographisch unabhängig voneinander.

### Multi-Device

Geräte werden über Device-UUIDs unterschieden, nicht über eigene Schlüsselpaare. Jedes Gerät generiert beim ersten Start eine zufällige UUID und nutzt den Master-Schlüssel für Signaturen. Siehe [Spec 005: Sync-Protokoll](../sync/005-sync-protokoll.md) für Details.

### Seed-Schutz auf dem Gerät

Der Seed MUSS auf dem Gerät angemessen geschützt werden und darf auf keinen Fall im Klartext extrahierbar sein. Wer den Seed hat, hat die vollständige Kontrolle über die Identität — einschließlich aller Schlüssel und aller Entschlüsselungsfähigkeiten.

Wie der Schutz konkret umgesetzt wird — Verschlüsselung at rest, Biometrie, Hardware-Keystore, Passwort — hängt vom jeweiligen Gerät und der Plattform ab und ist Sache der Implementierung.

## Migration (Schlüsselrotation)

Wenn eine Implementierung ihren Ableitungspfad ändern muss um dieser Spec zu entsprechen, werden bestehende Identitäten über Schlüsselrotation migriert. Siehe [Identity Migration](../research/identity-migration.md) (Entwurf).

## Aktuelle Implementierungen

Beide Implementierungen müssen Änderungen vornehmen um dieser Spec zu entsprechen:

| | WoT Core | Human Money Core | Spec |
|---|---|---|---|
| **Wortliste** | Deutsch (custom) | Englisch (Standard) | Beliebige gültige BIP39 |
| **Entropie** | 128 Bit | Konfigurierbar | Mindestens 128 Bit |
| **Seed-Bytes** | Erste 32 Bytes | Volle 64 Bytes | **Volle 64 Bytes** |
| **Passphrase** | `""` (leer) | `""` (leer) | `""` (immer leer) |
| **Stretching** | Keines | PBKDF2 100k Runden | ❓ Mit Sebastian klären |
| **HKDF Info** | `"wot-identity-v1"` | `"human-money-core/ed25519"` | **`"wot/identity/ed25519/v1"`** |
| **Ed25519** | @noble/ed25519 | ed25519_dalek | Beliebige konforme Impl. |
| **DID** | did:key + 0xed01 + Base58 | did:key + 0xed01 + Base58 | did:key + 0xed01 + Base58 |

## Offene Fragen

### 1. Key-Stretching bei der Ableitung

Human Money Core verwendet PBKDF2 mit 100k Runden zusätzlich zum BIP39-PBKDF2. WoT Core verwendet kein zusätzliches Stretching.

**Argumente dafür:** Bei Gutscheinen steht echtes Geld auf dem Spiel — zusätzlicher Brute-Force-Schutz ist sinnvoll. Schützt auch bei schwacher Entropie-Quelle.

**Argumente dagegen:** Bei 128 Bit Entropie aus einem korrekten Mnemonic ist Brute-Force bereits unlösbar. Stretching kostet Performance bei jedem Unlock auf Mobilgeräten.

Diese Entscheidung muss gemeinsam mit Sebastian getroffen werden. Wenn Stretching Teil des Standard-Pfades wird, ändert sich die DID — eine Migration ist nötig.
