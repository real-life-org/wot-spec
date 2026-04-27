# Device Keys — Multi-Device-Signaturen für Offline-Verifikation

> **Nicht normativ:** Dieses Dokument ist Hintergrund, Analyse oder Planung. Normative Anforderungen stehen in den Spec-Dokumenten und in `CONFORMANCE.md`.

- **Status:** Research
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-27

## Zusammenfassung

Dieses Dokument untersucht, wie mehrere Geräte für eine Identität Signaturen produzieren können, die **offline und langlebig** (Jahre später) verifizierbar sind — ohne Server zur Verifikationszeit. Es analysiert bestehende Systeme mit dem gleichen Problem und leitet drei Optionen ab, die für WoT Phase 2 in Frage kommen.

Phase 1 verwendet Shared Seed: alle Geräte leiten denselben Ed25519-Key deterministisch aus dem BIP39-Seed ab. Dieses Dokument beschreibt die Optionen für den Übergang zu Device-spezifischen Keys.

## Das fundamentale Problem

WoT-Attestations sind langlebige, portable, offline-verifizierbare Dokumente. Wenn Alice mit ihrem Tablet eine Attestation für Bob signiert, muss Carol diese Attestation drei Jahre später auf ihrem Handy verifizieren können — ohne Server, ohne Netzwerk, ohne Ledger.

Das unterscheidet WoT von Signal (ephemere Sessions), Matrix (Server-gestützte Cross-Signing-Chain) und allen Ledger-basierten Systemen. Die Signatur muss **self-contained** verifizierbar sein.

Gleichzeitig soll jedes Gerät eigenständig signieren können — Attestations, Verifikationen, Log-Einträge. Das erzeugt das Spannungsfeld:

| Anforderung | Implikation |
|---|---|
| Jedes Gerät signiert eigenständig | Jedes Gerät braucht einen Private Key |
| Signaturen sind offline verifizierbar | Der Verifier muss wissen, welche Keys autorisiert sind |
| Keine Server-Abhängigkeit | Die Autorisierung muss self-contained mitgeliefert werden |
| Key-Rotation möglich | Alte Signaturen bleiben gültig nach Rotation |

## Bestehende Systeme

### PGP Subkeys — 30 Jahre bewährt

PGP verwendet eine hierarchische Schlüsselstruktur: ein Master Key (Certification Key) signiert beliebig viele Subkeys (Signing, Encryption). Jedes Gerät bekommt eigene Subkeys; der Master Key bleibt offline.

**Verifikation:** Der exportierte Public Key Block enthält Master Key, alle Subkeys und die Binding Signatures. Vollständig self-contained — kein Server, kein Resolver. Die Binding Signature vom Master Key beweist die Zugehörigkeit des Subkeys.

**Schwäche:** Kein Konzept für temporale Verifikation — wenn ein Subkey revoked wird, sind auch alte Signaturen fragwürdig. Keine Rotation des Master Keys selbst.

### Keybase Sigchain — temporale Verifikation

Keybase hatte das eleganteste Design für dieses Problem. Jeder Account hat eine öffentliche **Sigchain** — eine geordnete Liste von Statements, jedes signiert, jedes mit Sequenznummer und Hash des vorherigen Links.

Neue Geräte werden provisioniert: ein autorisiertes Gerät signiert einen Sigchain-Link der den neuen Device Key als "sibkey" autorisiert. Der Verifier replayed die Chain und trackt dabei die gültigen Keys.

**Stärke:** Alte Signaturen bleiben gültig, auch wenn der signierende Key später revoked wird — weil die Verifikation temporal ist (gegen den Key-State zum Zeitpunkt der Signatur).

**Schwäche:** Die Sigchain war auf dem Keybase-Server gehostet. Keybase existiert de facto nicht mehr (Zoom-Akquisition 2020).

### KERI — Key Event Receipt Infrastructure

KERI ist das ambitionierteste System: ein append-only Key Event Log (KEL) mit Pre-Rotation (bei Inception werden Hashes der nächsten Rotation-Keys committed). Multi-Device über Multi-Sig AIDs oder Delegation.

**Stärke:** End-to-end verifizierbar, Pre-Rotation schützt gegen Key-Kompromittierung, KEL ist portabel und self-contained.

**Schwäche:** Extrem komplex — hunderte Seiten Spec, sehr wenige Implementierungen. Der KEL wächst mit jeder Rotation und muss mitgeliefert werden.

### did:webvh — KERI-lite

did:webvh fügt `did:web` ein versioniertes, kryptographisch verkettetes Log hinzu. Jede DID-Änderung wird in einem JSON Lines Log festgehalten. Pre-Rotation wird unterstützt. Einfacher als KERI, aber mit Web-Abhängigkeit für initiale Resolution.

### Nostr und SSB — Problem akzeptiert

Nostr teilt den Private Key (nsec) auf alle Geräte. NIP-26 (Delegated Signing) wurde als "unnecessary burden for little gain" deprecated. SSB hat eine Identität pro Gerät; "Fusion Identity" teilt ebenfalls einen Key. Beide Systeme haben das Problem akzeptiert statt es zu lösen.

## Analyse: Warum Shared Seed für Phase 1 richtig ist

Shared Seed (alle Geräte leiten denselben Ed25519-Key aus BIP39 ab) hat einen entscheidenden Vorteil: **jede Signatur ist identisch verifizierbar, egal von welchem Gerät sie kommt.** Kein Verifier muss Delegation-Chains verstehen, keine Chain muss mitgeliefert werden, keine temporale Resolution nötig.

Die Trade-offs sind bekannt und akzeptabel für Phase 1:

| Trade-off | Bewertung |
|---|---|
| Seed-Kompromittierung = alle Geräte betroffen | Akzeptabel — gilt für jedes Single-Root-System |
| Kein selektives Device-Revocation | Akzeptabel — bei Kompromittierung wird der Seed gewechselt (Identity Migration) |
| Seed muss auf jedes Gerät übertragen werden | Akzeptabel — 12 Wörter, einmaliger Vorgang |

Nostr und SSB haben gezeigt, dass dieser Ansatz in der Praxis funktioniert. Die Einschränkungen werden erst relevant wenn die Nutzerbasis wächst und die Sicherheitsanforderungen steigen.

## Drei Optionen für Phase 2

Alle drei Optionen bauen aufeinander auf: A ist in B enthalten, B ist in C enthalten. Der Wechsel von A nach B oder C ist vorwärtskompatibel.

### Option A: Device Key Delegation (PGP-Style)

Die einfachste Erweiterung. Der Root Key (aus BIP39/HKDF) signiert Device-spezifische Keys. Jede Signatur trägt die Delegation als self-contained Beweis mit.

**Schlüssel-Hierarchie:**

```
BIP39 Seed
  → HKDF → Root Key (Ed25519) = Identity Key
  → Root Key signiert DeviceKeyBinding:
      {
        "type": "device-key-binding",
        "devicePubKey": "z6Mk...",
        "deviceName": "Alices Tablet",
        "validFrom": "2026-04-27T10:00:00Z",
        "capabilities": ["sign-attestation", "sign-log-entry"]
      }
```

**Signatur-Format:**

```
Attestation-JWS:
  Header: { "alg": "EdDSA", "kid": "did:key:z6Mk...#device-tablet" }
  Payload: { ... VC ... }
  → signiert mit Device Key

+ DeviceKeyBinding-JWS:
  Header: { "alg": "EdDSA", "kid": "did:key:z6Mk...#root" }
  Payload: { DeviceKeyBinding }
  → signiert mit Root Key
```

**Verifikation:**

1. Root Key aus DID extrahieren (did:key → Public Key)
2. DeviceKeyBinding-JWS mit Root Key verifizieren
3. Attestation-JWS mit Device Key verifizieren
4. Prüfen: Device Key in Binding = Device Key in Attestation-Header

**Revocation:** Root Key signiert ein Revocation-Statement. Best-effort-Verteilung über Profil-Service und Inbox-Nachrichten. Offline-Verifier erfahren die Revocation erst beim nächsten Online-Kontakt.

**Vorteile:** Einfach, kein State nötig, vollständig self-contained.

**Nachteile:** Keine temporale Verifikation — nach Revocation sind auch alte Signaturen fragwürdig. Revocation ist best-effort.

### Option B: Sigchain (Keybase-Style)

Eine geordnete, hash-verkettete Liste aller Key-Events. Der Verifier replayed die Chain und kennt den Key-State zu jedem Zeitpunkt.

**Sigchain-Struktur:**

```json
[
  {
    "seq": 1,
    "type": "inception",
    "rootPubKey": "z6Mk...",
    "prev": null,
    "sig": "..."
  },
  {
    "seq": 2,
    "type": "add-device",
    "devicePubKey": "z6Mk...",
    "deviceName": "Alices Handy",
    "prev": "sha256:abc...",
    "sig": "..."
  },
  {
    "seq": 3,
    "type": "add-device",
    "devicePubKey": "z6Mk...",
    "deviceName": "Alices Tablet",
    "prev": "sha256:def...",
    "sig": "..."
  },
  {
    "seq": 4,
    "type": "revoke-device",
    "devicePubKey": "z6Mk...",
    "reason": "lost",
    "prev": "sha256:ghi...",
    "sig": "..."
  }
]
```

Jeder Eintrag ist JWS-signiert (vom Root Key) und enthält den Hash des vorherigen Eintrags. Die Chain ist append-only und manipulationssicher.

**Verifikation:**

1. Chain replaysn: von `seq: 1` bis zum Zeitpunkt der Signatur
2. Bei jedem Schritt den Key-State aktualisieren (add/revoke)
3. Prüfen: war der Device Key zum Zeitpunkt `created_time` der Attestation autorisiert?

**Verteilung:** Die Sigchain wird über den Profil-Service bereitgestellt (`GET /p/{did}/keys`) und lokal gecacht. Bei Offline-Verifikation reicht der gecachte Stand.

**Vorteile:** Temporale Verifikation — alte Signaturen bleiben gültig nach Revocation. Vollständige Audit-History.

**Nachteile:** Chain muss mitgeliefert oder gecacht werden. Komplexer als Option A.

### Option C: Mini-KERI (Pre-Rotation)

Wie Option B, aber mit einem zusätzlichen Sicherheitsmechanismus: bei der Inception werden die **Hashes der nächsten Rotation Keys** committed.

**Erweiterter Inception-Eintrag:**

```json
{
  "seq": 1,
  "type": "inception",
  "rootPubKey": "z6Mk...",
  "nextKeyHash": "sha256:xyz...",
  "prev": null,
  "sig": "..."
}
```

`nextKeyHash` ist der SHA-256-Hash des Public Keys, der für die nächste Root-Key-Rotation verwendet wird. Dieser Key wird vorab generiert und sicher aufbewahrt (z.B. auf einem Offline-Medium).

**Rotation:**

```json
{
  "seq": 5,
  "type": "rotate-root",
  "newRootPubKey": "z6Mk...(neu)",
  "nextKeyHash": "sha256:uvw...",
  "prev": "sha256:jkl...",
  "sig": "..."
}
```

Signiert mit dem **alten** Root Key. Der Verifier prüft: `sha256(newRootPubKey) == nextKeyHash` aus dem vorherigen Commitment. Ein Angreifer, der den aktuellen Root Key kompromittiert, kann nicht rotieren — er kennt den pre-committed Key nicht.

**Vorteile:** Schutz gegen Root-Key-Kompromittierung. Stärkstes Sicherheitsmodell.

**Nachteile:** Deutlich komplexer. Pre-Rotation-Keys müssen sicher aufbewahrt werden. Lohnt sich erst bei höheren Sicherheitsanforderungen.

## Vergleich

| | Shared Seed (Phase 1) | A: Delegation | B: Sigchain | C: Mini-KERI |
|---|---|---|---|---|
| Komplexität | Minimal | Niedrig | Mittel | Hoch |
| Offline-Verifikation | Trivial | Self-contained | Chain gecacht | Chain gecacht |
| Temporale Verifikation | N/A | Nein | Ja | Ja |
| Device-Revocation | Nein | Best-effort | Auditierbar | Auditierbar |
| Root-Key-Schutz | Nein | Nein | Nein | Pre-Rotation |
| DID-Methode | did:key | did:key | did:key oder did:webvh | did:key oder did:webvh |
| Signaturgröße | 1 JWS | 2 JWS | 1 JWS + Chain-Referenz | 1 JWS + Chain-Referenz |

## Empfehlung

**Phase 1:** Shared Seed. Bewährt (Nostr, SSB), einfach, keine Delegation-Komplexität für Verifier.

**Phase 2:** Option A (Delegation) als Einstieg, natürlich verbunden mit dem did:webvh-Wechsel. did:webvh liefert das versionierte Log für temporale Verifikation gleich mit — was Option B auf DID-Ebene löst.

**Phase 3 (optional):** Pre-Rotation (Option C) wenn die Sicherheitsanforderungen steigen.

Alle drei Optionen sind vorwärtskompatibel: A → B → C ohne Breaking Change. Das `deviceKid`-Feld im Personal Doc ([Sync 006](../03-wot-sync/006-personal-doc.md)) ist bereits vorbereitet.

## Zusammenhang mit DID-Methoden

| DID-Methode | Device-Key-Ansatz | Temporale Verifikation |
|---|---|---|
| **did:key** | Delegation (Option A) oder Sigchain (Option B) — DID = Root Key, Device Keys sind autorisierte Signateure | Nur mit expliziter Sigchain |
| **did:webvh** | Device Keys als verificationMethods im DID-Dokument, autorisiert durch Log-Einträge | Eingebaut (Verifiable History Log) |
| **did:keri** | Multi-Sig AID oder Delegation — KEL liefert die Chain | Eingebaut (Key Event Log) |

did:webvh ist der natürliche Partner für Device Keys: das DID-Dokument listet alle autorisierten Device Keys, und das Verifiable History Log ermöglicht temporale Verifikation. Der Wechsel zu Device Keys und der Wechsel zu did:webvh sollten zusammen erfolgen.

## Offene Fragen

1. **Capability-Scoping:** Sollen Device Keys unterschiedliche Berechtigungen haben (z.B. "darf Attestations signieren, aber nicht rotieren")?
2. **Chain-Größe:** Wie groß wird eine Sigchain nach 5 Jahren mit vielen Geräten? Brauchen wir Checkpointing?
3. **Delegation-Tiefe:** Soll ein Device Key weitere Keys delegieren können (z.B. für Sub-Devices)?
4. **Interaktion mit Guardian-Vouching:** Wie funktioniert Social Recovery wenn Device Keys im Spiel sind?
