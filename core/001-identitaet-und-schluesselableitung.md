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
  → (optional: zusätzliches Key-Stretching — siehe Offene Frage 3)
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
- **Ausgabe:** 64 Bytes

Die Passphrase ist absichtlich fixiert. Eine benutzerdefinierte Passphrase würde die Determinismus-Garantie brechen: selbes Mnemonic + verschiedene Passphrase = verschiedene Identität. Im Web of Trust gilt: **ein Mnemonic = eine Identität, immer.**

### Schlüsselableitung

Optional: Zusätzliches Key-Stretching vor der Ableitung (siehe Offene Frage 3).

HKDF-SHA256 mit:
- **Input Key Material:** BIP39-Seed (siehe Offene Frage 1: 32 vs. 64 Bytes)
- **Salt:** leer (kein Salt)
- **Info:** `"wot/identity/ed25519/v1"` (siehe Offene Frage 2)
- **Ausgabe:** 32 Bytes (Ed25519-Seed)

### Identität

- **Signaturalgorithmus:** Ed25519
- **Eingabe:** 32-Byte Seed aus HKDF
- **DID-Methode:** `did:key` mit Multicodec-Präfix `0xed01` (Ed25519 Public Key), Base58-BTC kodiert

Beispiel: `did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK`

### Weitere Schlüssel

Aus demselben Seed werden weitere Schlüssel abgeleitet. Jeder Schlüssel verwendet einen eigenen HKDF-Info-String:

| Schlüssel | HKDF Info | Zweck | Spezifiziert in |
|-----------|-----------|-------|----------------|
| Signatur (Master) | `"wot/identity/ed25519/v1"` | Identität, Attestations, Delegationen | Dieses Dokument |
| Verschlüsselung | `"wot/encryption/x25519/v1"` | Asymmetrische Verschlüsselung (X25519) | Spec 003 |
| Recovery Device | `"wot/device/recovery/v1"` | Geräte-Recovery wenn alle Geräte verloren | Spec 004 |

Alle Schlüssel sind deterministisch aus demselben Seed ableitbar. Durch die verschiedenen Info-Strings sind sie kryptographisch unabhängig voneinander.

Device-Keys für den regulären Betrieb werden NICHT aus dem Seed abgeleitet, sondern zufällig generiert. Siehe [Spec 004](004-device-keys-und-delegation.md).

### Seed-Schutz auf dem Gerät

Der Seed MUSS auf dem Gerät angemessen geschützt werden und darf auf keinen Fall im Klartext extrahierbar sein. Wer den Seed hat, hat die vollständige Kontrolle über die Identität — einschließlich aller Schlüssel, aller Geräte-Delegationen und aller Entschlüsselungsfähigkeiten.

Wie der Schutz konkret umgesetzt wird — Verschlüsselung at rest, Biometrie, Hardware-Keystore, Passwort — hängt vom jeweiligen Gerät und der Plattform ab und ist Sache der Implementierung.

## Migration (Schlüsselrotation)

Wenn eine Implementierung ihren Ableitungspfad ändern muss um dieser Spec zu entsprechen, werden bestehende Identitäten über Schlüsselrotation migriert. Siehe [Identity Migration](../drafts/004-identity-migration.md) (Entwurf).

## Aktuelle Implementierungen

| | WoT Core | Human Money Core | Spec |
|---|---|---|---|
| **Wortliste** | Deutsch (custom) | Englisch (Standard) | ✅ Beliebige gültige BIP39 |
| **Entropie** | 128 Bit | Konfigurierbar | ✅ Mindestens 128 Bit |
| **Seed-Bytes** | Erste 32 Bytes | Volle 64 Bytes | ❓ Mit Sebastian klären |
| **Passphrase** | `""` (leer) | `""` (leer) | ✅ `""` (immer leer) |
| **Stretching** | Keines | PBKDF2 100k Runden | ❓ Mit Sebastian klären |
| **HKDF Info** | `"wot-identity-v1"` | `"human-money-core/ed25519"` | ❓ `"wot/identity/ed25519/v1"` (Migration!) |
| **Ed25519** | @noble/ed25519 | ed25519_dalek | ✅ Beliebige konforme Impl. |
| **DID** | did:key + 0xed01 + Base58 | did:key + 0xed01 + Base58 | ✅ did:key + 0xed01 + Base58 |

## Offene Fragen

Die Fragen 1-3 hängen zusammen: jede Änderung an der Ableitungskette erzeugt eine neue DID und erfordert eine Migration aller DIDs im Web of Trust — inklusive aller bestehenden Kontakte, Verifikationen, Attestations und Space-Mitgliedschaften. Es sollte sorgfältig abgewogen werden ob den Migrationskosten ein tatsächlicher Gewinn gegenübersteht. Wenn Änderungen gemacht werden, sollten alle offenen Fragen gemeinsam entschieden werden, damit höchstens eine Migration nötig ist.

### 1. Seed-Länge als HKDF-Input: 32 vs. 64 Bytes

WoT Core verwendet die ersten 32 Bytes des BIP39-Seeds, Human Money Core die vollen 64 Bytes. 64 Bytes ist intuitiver (der volle Seed wird verwendet). 32 Bytes reicht kryptographisch aus (HKDF-SHA256 extrahiert ohnehin maximal 256 Bit). Ein Wechsel würde alle bestehenden DIDs der betroffenen Implementierung invalidieren — ohne echten Sicherheitsgewinn.

### 2. HKDF-Info-String

WoT Core verwendet `"wot-identity-v1"`, Human Money Core verwendet `"human-money-core/ed25519"`. Der vorgeschlagene Standard `"wot/identity/ed25519/v1"` erfordert eine Migration auf beiden Seiten — inklusive neuer DIDs.

### 3. Key-Stretching bei der Ableitung

Human Money Core verwendet PBKDF2 mit 100k Runden zusätzlich zum BIP39-PBKDF2. WoT Core verwendet kein zusätzliches Stretching.

Stretching verlangsamt Brute-Force-Angriffe auf das Mnemonic. Bei einem korrekt generierten Mnemonic mit 128 Bit Entropie ist ein Brute-Force-Angriff bereits unlösbar (2^128 Möglichkeiten) — Stretching bringt keinen zusätzlichen Schutz. Bei einer schwachen Entropie-Quelle (z.B. fehlerhafte Zufallszahlen-Generierung) würde Stretching den Angriff um den Faktor 100.000 verlangsamen — ein realer Schutz.

Die Kosten: spürbare Verzögerung bei jedem Geräte-Entsperren und höherer Energieverbrauch auf mobilen Geräten.

Die Frage ist im Kern: **Vertrauen wir unseren Entropie-Quellen?** Sebastian hat sich bei Human Money Core möglicherweise bewusst für den zusätzlichen Schutz entschieden — bei Gutscheinen steht echtes Geld auf dem Spiel.
