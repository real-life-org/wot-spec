# WoT Spec 001: Identität und Schlüsselableitung

- **Status:** Entwurf
- **Autoren:** Anton Tranelis, Sebastian Galek
- **Datum:** 2026-04-23
- **Scope:** Seed-, Key- und DID-Key-Ableitung fuer WoT Core
- **Depends on:** BIP39, HKDF, Ed25519, X25519
- **Conformance profile:** `wot-core@0.1`

## Zusammenfassung

Dieses Dokument spezifiziert wie Schlüsselmaterial aus einem BIP39-Mnemonic abgeleitet wird. Das Ziel ist ein deterministischer Pfad vom Mnemonic zu einem Ed25519-Schlüsselpaar und weiteren abgeleiteten Schlüsseln — so dass verschiedene Implementierungen aus demselben Seed dieselben Schlüssel erzeugen.

Wie aus dem Schlüsselmaterial eine auflösbare DID mit DID-Dokument wird, ist in [Core 005: DID-Dokument und Resolution](005-did-resolution.md) spezifiziert.

## Referenzierte Standards

- **BIP39** — Mnemonic-Generierung und Seed-Ableitung
- **HKDF** (RFC 5869) — Schlüsselableitung
- **Ed25519** (RFC 8032) — Signaturalgorithmus
- **X25519** (RFC 7748) — Key Agreement
- **DID Core** (W3C Recommendation) — Decentralized Identifiers

## Ableitungspfad

```
BIP39 Mnemonic (12+ Wörter)
  → BIP39 Seed (PBKDF2-HMAC-SHA512, 2048 Runden, Passphrase="") → 64 Bytes
  → HKDF-SHA256(seed, info="wot/identity/ed25519/v1") → 32 Bytes → Ed25519 Schlüsselpaar
  → HKDF-SHA256(seed, info="wot/encryption/x25519/v1") → 32 Bytes → X25519 Schlüsselpaar
  → resolve() → DID-Dokument (siehe Core 005)
```

Selbes Mnemonic → selbe Schlüssel → selbe Identität. Über alle Implementierungen, Sprachen und Anwendungen hinweg.

## Spezifikation

### Entropie (BIP39)

- **Standard:** BIP39
- **Entropie:** Mindestens 128 Bit (12 Wörter)
- **Wortliste:** Die Wortliste bestimmt welche Wörter vergeben werden — und damit den PBKDF2-Input und den Seed. Eine Identität die mit der deutschen Wortliste erstellt wurde, kann nur auf Geräten wiederhergestellt werden die die deutsche Wortliste kennen. Implementierungen SOLLTEN die englische BIP39-Wortliste als Standard verwenden und DÜRFEN weitere Wortlisten unterstützen.

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

Kein zusätzliches Key-Stretching — BIP39-PBKDF2 ist ausreichend (siehe [Entschiedene Fragen](#entschiedene-fragen)).

### Schlüsselpaar

- **Signaturalgorithmus:** Ed25519
- **Eingabe:** 32-Byte Seed aus HKDF
- **Ausgabe:** Ed25519 Schlüsselpaar (Private Key + Public Key)

Wie aus dem Schlüsselpaar eine DID und ein DID-Dokument werden, ist in [Core 005](005-did-resolution.md) spezifiziert. Die DID-Methode ist austauschbar — das Protokoll arbeitet DID-Methoden-agnostisch über eine `resolve()`-Abstraktion.

### Weitere Schlüssel

Aus demselben Seed werden weitere Schlüssel abgeleitet. Jeder Schlüssel verwendet einen eigenen HKDF-Info-String:

| Schlüssel | HKDF Info | Zweck | Spezifiziert in |
|-----------|-----------|-------|----------------|
| Signatur (Master) | `"wot/identity/ed25519/v1"` | Identität, Attestations | Dieses Dokument |
| Verschlüsselung | `"wot/encryption/x25519/v1"` | Asymmetrische Verschlüsselung (X25519) | [Spec 005](../02-wot-sync/005-verschluesselung.md) |
| Personal Doc | `"wot/personal-doc/v1"` | Symmetrische Verschlüsselung des Personal Doc (AES-256) | [Spec 010](../02-wot-sync/010-personal-doc.md) |
| Space Admin (pro Space) | `"wot/space-admin/<canonical-lowercase-uuid>/v1"` | Space-spezifischer Admin Key (Ed25519). Nur für Admins eines Spaces. IKM ist der 64-Byte BIP39-Seed (nicht der Ed25519-Identity-Seed). | [Spec 005](../02-wot-sync/005-verschluesselung.md#admin-key-abgeleitet) |

Alle Schlüssel sind deterministisch aus demselben Seed ableitbar. Durch die verschiedenen Info-Strings sind sie kryptographisch unabhängig voneinander.

**Warum separater HKDF-Pfad statt birationale Abbildung:** Einige Implementierungen (z.B. Web Crypto API in Browsern) erzeugen Ed25519-Keys als `non-extractable` — der Private Key kann nur zum Signieren verwendet werden, ist aber als Byte-Folge nicht lesbar. Die birationale Abbildung (Ed25519 → Curve25519 → X25519) erfordert Zugriff auf den rohen Private Key und ist deshalb in Browser-Umgebungen nicht möglich. Der separate HKDF-Pfad funktioniert überall — Browser, Desktop, Mobile, Rust, JavaScript — und ist deshalb die normative Methode.

### Multi-Device — Shared-Seed-Modell

In der aktuellen Spec-Version verwenden **alle Geräte eines Users denselben Seed**. Geräte werden über zufällige Device-UUIDs unterschieden, nicht über eigene Schlüsselpaare. Jedes Gerät generiert beim ersten Start eine UUID und nutzt den Master-Schlüssel für alle Signaturen.

**Konsequenzen dieses Modells:**

- **Einfaches Onboarding:** Mnemonic eingeben, Seed wiederherstellen, Gerät ist vollwertig
- **Kein Master-Gerät nötig:** Alle Geräte sind kryptographisch gleichwertig
- **Cross-Device-Sync direkt möglich:** Alle Geräte können alles entschlüsseln und signieren
- **Device-Revocation ist kosmetisch:** Wer den Seed extrahiert, kann jede beliebige Device-UUID generieren — eine widerrufene UUID wird durch eine neue ersetzt
- **Seed-Diebstahl ist katastrophal:** Ein kompromittiertes Gerät bedeutet Kompromittierung aller Geräte

**Seed-Schutz ist die kritische Verteidigungslinie.** Das Modell funktioniert nur dann sicher, wenn der Seed auf jedem einzelnen Gerät stark geschützt ist (siehe unten).

### Zukünftiger Upgrade-Pfad: Per-Device Keys

Eine sauberere Architektur wären **Per-Device Keys** — jedes Gerät hat ein eigenes Schlüsselpaar, das von der Hauptidentität signiert wird. Damit würde:

- Der Seed nur noch auf einem primären Gerät liegen
- Device-Revocation kryptographisch bedeutungsvoll werden
- Gerätekompromittierung auf ein Gerät begrenzbar sein

**Warum wir das jetzt nicht einführen:** `did:key` kann per Design nur einen einzigen Schlüssel ausdrücken — die DID *ist* der Public Key. Ein Trust-Anchor-Dokument mit mehreren Device-Keys setzt eine andere DID-Methode voraus ([did:peer:4](https://identity.foundation/peer-did-method-spec/) oder [did:webvh](https://identity.foundation/didwebvh/)), die zu einem DID-Dokument mit mehreren `verificationMethod`-Einträgen aufgelöst wird.

Der Wechsel zu Per-Device Keys wird **gemeinsam mit der DID-Methoden-Migration** erfolgen — beide Themen gehören architektonisch zusammen. Siehe [Identitäts-Alternativen](../research/identitaet-alternativen.md) und [Identity Migration](../research/identity-migration.md) für den geplanten Pfad.

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
| **Stretching** | Keines | PBKDF2 100k Runden | **Keines** (BIP39-PBKDF2 reicht) |
| **HKDF Info** | `"wot-identity-v1"` | `"human-money-core/ed25519"` | **`"wot/identity/ed25519/v1"`** |
| **Ed25519** | @noble/ed25519 | ed25519_dalek | Beliebige konforme Impl. |
| **DID** | did:key + 0xed01 + Base58 | did:key + 0xed01 + Base58 | did:key + 0xed01 + Base58 |

## Entschiedene Fragen

### Key-Stretching — kein Extra-Stretching

Human Money Core verwendet PBKDF2 mit 100k Runden zusätzlich zum BIP39-PBKDF2. **Die Spec verzichtet darauf.** Begründung: Bei 128 Bit Entropie aus einem korrekten BIP39-Mnemonic sind 2^128 Kombinationen physikalisch nicht durchprobierbar — zusätzliches Stretching bringt keinen realen Sicherheitsgewinn. Die Kosten (~500ms Unlock-Verzögerung auf Mobilgeräten) überwiegen den Nutzen. Sebastian stimmt zu.

**Anpassungsbedarf HMC:** Sebastian entfernt das zusätzliche PBKDF2. Das ändert die abgeleiteten Keys — eine Migration bestehender HMC-Identitäten ist nötig.
