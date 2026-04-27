# Device Keys — Multi-Device-Signaturen für Offline-Verifikation

> **Nicht normativ:** Dieses Dokument ist Hintergrund, Analyse oder Planung. Normative Anforderungen stehen in den Spec-Dokumenten und in `CONFORMANCE.md`.

- **Status:** Research
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-27

## Zusammenfassung

Dieses Dokument untersucht, wie mehrere Geräte für eine Identität Signaturen produzieren können, die **offline und langlebig** (Jahre später) verifizierbar sind — ohne Server zur Verifikationszeit. Es analysiert bestehende Systeme mit dem gleichen Problem und leitet mehrere Ausbaustufen nach Phase 1 ab.

Phase 1 verwendet Shared Seed: alle Geräte leiten denselben Ed25519-Key deterministisch aus dem BIP39-Seed ab. Dieses Dokument beschreibt die Optionen für den Übergang zu Device-spezifischen Keys.

Der aktuelle Draft fuer Phase 2 steht in [Identity 004: Device-Key-Delegation](../01-wot-identity/004-device-key-delegation.md).

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

## Drei Ausbaustufen nach Phase 1

Alle drei Ausbaustufen bauen aufeinander auf: Phase 2 ist in Phase 3 enthalten, Phase 3 ist in Phase 4 enthalten. Der Wechsel von einer Phase zur naechsten ist vorwaertskompatibel.

## Architekturentscheidung: Device Keys duerfen attestieren

Device Keys sollen in Phase 2 nicht nur fuer Broker-Login oder Log-Sync verwendet werden, sondern auch fuer langlebige Trust-Objekte wie Attestations und Verification-Attestations. Sonst waere der wichtigste Sicherheitsgewinn von Per-Device Keys nicht erreichbar: Der Identity Key muesste weiterhin auf jedem Geraet liegen, damit jedes Geraet attestieren kann.

Die Loesung ist ein **Delegation-Modell**:

```text
Identity Key = Root of Trust einer Person
Device Key   = delegierter Signatur-Key eines konkreten Geraets
Delegation   = vom Identity Key signierter Nachweis, was der Device Key darf
```

Ein Device Key ist also keine eigene soziale Identitaet. Er signiert im Namen der DID, aber nur innerhalb explizit delegierter Faehigkeiten.

### Capability-Scopes fuer Device Keys

Delegationen MUESSEN zweckgebunden sein. Phase 2 sollte mindestens diese Capabilities unterscheiden:

| Capability | Bedeutung |
|---|---|
| `sign-log-entry` | Device darf Sync-Log-Eintraege signieren |
| `sign-verification` | Device darf Verification-Attestations signieren |
| `sign-attestation` | Device darf normale Attestations signieren |
| `broker-auth` | Device darf Broker-Challenge-Response signieren |
| `device-admin` | Device darf weitere Device Keys delegieren oder widerrufen |

Nicht jedes Device muss alle Capabilities bekommen. Ein Alltags-Handy kann z.B. `sign-attestation`, `sign-verification`, `sign-log-entry` und `broker-auth` haben, aber kein `device-admin`.

### `deviceKid`-Semantik

`deviceKid` ist der kanonische Key Identifier des Device-Signing-Keys. In Phase 2 ist das eine eigenstaendige `did:key`-DID-URL des Device Keys:

```text
deviceKid = did:key:<device-ed25519-public-key>#sig-0
```

Der Device Key ist damit resolvierbar, aber keine soziale Identitaet. Die soziale Identitaet bleibt die Identity DID aus `iss`; das DeviceKeyBinding autorisiert `deviceKid`, in ihrem Namen bestimmte Signaturen zu erzeugen.

Der Binding-Payload enthaelt zusaetzlich `devicePublicKeyMultibase`. Dieses Feld ist der explizite Offline-Key im Bundle und MUSS zum Public Key passen, der aus `deviceKid` aufgeloest wird. Falls `deviceKid` und `devicePublicKeyMultibase` nicht denselben Ed25519-Key bezeichnen, MUSS der Verifier das Bundle ablehnen.

Praktisch hat ein User in Phase 2 also eine primaere Identity DID und zusaetzliche technische Device-DIDs:

```text
Identity DID: did:key:z6Mk...identity
Phone Key:    did:key:z6Mk...phone#sig-0
Tablet Key:   did:key:z6Mk...tablet#sig-0
```

Diese Device-DIDs duerfen nicht als eigene Personen im Trust Graph behandelt werden. Sie sind nur delegierte Signatur-Schluessel. In allen sozialen Aussagen bleibt `issuer` / `iss` die Identity DID; nur der JWS-Header `kid` zeigt auf das signierende Device.

In Phase 3 kann `deviceKid` auch eine Verification Method in einem versionierten Identity-DID-Dokument sein (z.B. `did:webvh:...#device-tablet`). Die Semantik bleibt gleich: `deviceKid` bezeichnet den konkreten Device-Signing-Key, `iss` bezeichnet die soziale Identity DID.

### Delegated-Attestation-Bundle

Eine mit Device Key signierte Attestation ist nur dann offline verifizierbar, wenn der Verifier auch den Delegation Proof hat. Phase 2 nutzt deshalb ein eigenes JSON-Containerformat. Es ist **keine** Verifiable Presentation und **kein** drittes JWS; die Integritaet kommt ausschliesslich aus den beiden enthaltenen JWS-Signaturen.

```json
{
  "type": "wot-delegated-attestation-bundle/v1",
  "attestationJws": "<VC-JWS signiert mit Device Key>",
  "deviceKeyBindingJws": "<DeviceKeyBinding-JWS signiert mit Identity Key>"
}
```

Bei Sigchain/did:webvh kann `deviceKeyBindingJws` spaeter durch eine Chain-Referenz plus gecachte/verifizierbare History ersetzt oder ergaenzt werden. Fuer Offline-Portabilitaet DARF ein Export weiterhin die noetigen Chain-Segmente beilegen.

### Verifikation einer delegierten Attestation

Ein Verifier prueft:

1. Bundle `type` ist `wot-delegated-attestation-bundle/v1`.
2. Attestation-JWS Header `kid` zeigt auf den Device Key (`deviceKid`).
3. Attestation-JWS Payload enthaelt `iat` als Ausstellungs-/Signaturzeitpunkt.
4. DeviceKeyBinding-JWS Header `kid` zeigt auf den Identity Key, und die Binding-Signatur ist mit diesem Key gueltig.
5. Binding `iss` ist die Identity DID aus dem Binding-Header `kid`.
6. Binding `sub` und `deviceKid` bezeichnen denselben Device Key wie der Attestation-JWS Header `kid`.
7. `devicePublicKeyMultibase` passt zum Public Key aus `deviceKid`.
8. Attestation-JWS Signatur ist mit diesem Device Key gueltig.
9. Binding enthaelt die benoetigte Capability (`sign-attestation` oder `sign-verification`).
10. `validFrom` / `validUntil` des Bindings umfassen `iat` der Attestation, nach Normalisierung auf denselben Zeittyp.
11. `issuer` / `iss` der Attestation bleibt die Identity DID aus dem Binding, nicht der Device Key.

Damit bleibt die soziale Aussage bei der Person, waehrend das konkrete Geraet kryptographisch und auditierbar signiert. Die zeitliche Begrenzung des Bindings begrenzt nur die Signaturberechtigung des Device Keys; sie laesst die Attestation selbst nicht ablaufen.

### Phase 2: Delegated Device Keys (PGP-Style)

Die einfachste Erweiterung. Der Identity Key (aus BIP39/HKDF) signiert Device-spezifische Keys. Jede Signatur trägt die Delegation als self-contained Beweis mit.

**Schlüssel-Hierarchie:**

```
BIP39 Seed
  → HKDF → Identity Key (Ed25519)
  → Identity Key signiert DeviceKeyBinding:
      {
        "type": "device-key-binding",
        "iss": "did:key:z6Mk...identity",
        "sub": "did:key:z6Mk...device#sig-0",
        "deviceKid": "did:key:z6Mk...device#sig-0",
        "devicePublicKeyMultibase": "z6Mk...device",
        "deviceName": "Alices Tablet",
        "validFrom": "2026-04-27T10:00:00Z",
        "validUntil": "2027-04-27T10:00:00Z",
        "capabilities": ["sign-attestation", "sign-log-entry"]
      }
```

`validFrom` / `validUntil` im Binding sind kein Ablaufdatum der Attestation. Sie sagen nur: dieses Device durfte in diesem Zeitraum im Namen der Identity DID signieren. Zeitvergleiche muessen als Instant-Vergleich erfolgen; ISO-8601-Werte und Unix-Timestamps werden vor dem Vergleich normalisiert.

**Signatur-Format:**

```
Attestation-JWS:
  Header: { "alg": "EdDSA", "kid": "did:key:z6Mk...device#sig-0" }
  Payload: { ... VC ..., "iat": 1776420000 }
  → signiert mit Device Key

+ DeviceKeyBinding-JWS:
  Header: { "alg": "EdDSA", "kid": "did:key:z6Mk...identity#sig-0" }
  Payload: { DeviceKeyBinding }
  → signiert mit Identity Key
```

Als portables Objekt wird die Attestation zusammen mit dem DeviceKeyBinding als Delegated-Attestation-Bundle transportiert. Das Attestation-VC selbst behaelt `issuer`/`iss` = Identity DID; nur der JWS-Header `kid` zeigt auf den Device Key. Phase 2 sollte fuer delegierte Signaturen `iat` verpflichtend machen, damit die Device-Key-Autorisierung gegen den Ausstellungszeitpunkt geprueft werden kann.

**Verifikation:**

1. Identity Key aus DID extrahieren (did:key → Public Key)
2. DeviceKeyBinding-JWS mit Identity Key verifizieren
3. Attestation-JWS mit Device Key verifizieren
4. Prüfen: `deviceKid` / `sub` im Binding = `kid` im Attestation-Header

**Revocation:** Identity Key signiert ein Revocation-Statement. Best-effort-Verteilung über Profil-Service und Inbox-Nachrichten. Offline-Verifier erfahren die Revocation erst beim nächsten Online-Kontakt.

**Vorteile:** Einfach, kein State nötig, vollständig self-contained.

**Nachteile:** Keine starke temporale Verifikation — ein kompromittierter Device Key koennte Signaturen zurueckdatieren, solange es keinen unabhaengig verifizierbaren Key-State zum Signaturzeitpunkt gibt. Revocation ist best-effort.

### Phase 3: Temporal Key History (Sigchain / did:webvh)

Eine geordnete, hash-verkettete Liste aller Key-Events. Der Verifier replayed die Chain und kennt den Key-State zu jedem Zeitpunkt.

**Sigchain-Struktur:**

```json
[
  {
    "seq": 1,
    "type": "inception",
    "identityPubKey": "z6Mk...",
    "prev": null,
    "sig": "..."
  },
  {
    "seq": 2,
    "type": "add-device",
    "devicePublicKeyMultibase": "z6Mk...",
    "deviceName": "Alices Handy",
    "prev": "sha256:abc...",
    "sig": "..."
  },
  {
    "seq": 3,
    "type": "add-device",
    "devicePublicKeyMultibase": "z6Mk...",
    "deviceName": "Alices Tablet",
    "prev": "sha256:def...",
    "sig": "..."
  },
  {
    "seq": 4,
    "type": "revoke-device",
    "devicePublicKeyMultibase": "z6Mk...",
    "reason": "lost",
    "prev": "sha256:ghi...",
    "sig": "..."
  }
]
```

Jeder Eintrag ist JWS-signiert (vom Identity Key oder einem dafuer autorisierten Device Key) und enthält den Hash des vorherigen Eintrags. Die Chain ist append-only und manipulationssicher.

**Verifikation:**

1. Chain replayen: von `seq: 1` bis zum Zeitpunkt der Signatur
2. Bei jedem Schritt den Key-State aktualisieren (add/revoke)
3. Prüfen: war der Device Key zum `iat` / Signaturzeitpunkt der Attestation autorisiert?

**Verteilung:** Die Sigchain wird über den Profil-Service bereitgestellt (`GET /p/{did}/keys`) und lokal gecacht. Bei Offline-Verifikation reicht der gecachte Stand.

**Vorteile:** Temporale Verifikation — alte Signaturen bleiben gültig nach Revocation. Vollständige Audit-History.

**Nachteile:** Chain muss mitgeliefert oder gecacht werden. Komplexer als Phase 2.

### Phase 4: Pre-Rotation / Mini-KERI

Wie Phase 3, aber mit einem zusätzlichen Sicherheitsmechanismus: bei der Inception werden die **Hashes der nächsten Rotation Keys** committed.

**Erweiterter Inception-Eintrag:**

```json
{
  "seq": 1,
  "type": "inception",
  "identityPubKey": "z6Mk...",
  "nextKeyHash": "sha256:xyz...",
  "prev": null,
  "sig": "..."
}
```

`nextKeyHash` ist der SHA-256-Hash des Public Keys, der für die nächste Identity-Key-Rotation verwendet wird. Dieser Key wird vorab generiert und sicher aufbewahrt (z.B. auf einem Offline-Medium).

**Rotation:**

```json
{
  "seq": 5,
  "type": "rotate-identity-key",
  "newIdentityPubKey": "z6Mk...(neu)",
  "nextKeyHash": "sha256:uvw...",
  "prev": "sha256:jkl...",
  "sig": "..."
}
```

Signiert mit dem **alten** Identity Key. Der Verifier prüft: `sha256(newIdentityPubKey) == nextKeyHash` aus dem vorherigen Commitment. Ein Angreifer, der den aktuellen Identity Key kompromittiert, kann nicht rotieren — er kennt den pre-committed Key nicht.

**Vorteile:** Schutz gegen Identity-Key-Kompromittierung. Stärkstes Sicherheitsmodell.

**Nachteile:** Deutlich komplexer. Pre-Rotation-Keys müssen sicher aufbewahrt werden. Lohnt sich erst bei höheren Sicherheitsanforderungen.

## Vergleich

| | Phase 1: Shared Seed | Phase 2: Delegation | Phase 3: Temporal History | Phase 4: Pre-Rotation |
|---|---|---|---|---|
| Komplexität | Minimal | Niedrig | Mittel | Hoch |
| Offline-Verifikation | Trivial | Self-contained | Chain gecacht | Chain gecacht |
| Temporale Verifikation | N/A | Nein | Ja | Ja |
| Device-Revocation | Nein | Best-effort | Auditierbar | Auditierbar |
| Identity-Key-Schutz | Nein | Nein | Nein | Pre-Rotation |
| DID-Methode | did:key | did:key | did:key + WoT-Sigchain oder did:webvh | did:key + pre-rotating Sigchain, did:webvh oder KERI-artig |
| Signaturgröße | 1 JWS | 2 JWS im JSON-Bundle | 1 JWS + Chain-Referenz | 1 JWS + Chain-Referenz |

## Empfehlung

**Phase 1:** Shared Seed. Bewährt (Nostr, SSB), einfach, keine Delegation-Komplexität für Verifier.

**Phase 2:** Delegated Device Keys (DeviceKeyBinding + Delegated-Attestation-Bundle) als did:key-kompatibler Einstieg. Damit koennen Device Keys Attestations signieren, ohne sofort eine neue DID-Methode vorauszusetzen.

**Phase 3:** Temporal Key History via Sigchain oder did:webvh. did:webvh liefert das versionierte Log fuer autorisierte Device Keys direkt auf DID-Ebene — was eine separate Sigchain ersetzen kann. Reines `did:key` reicht ab hier nur noch mit zusaetzlicher WoT-Sigchain.

**Phase 4 (optional):** Pre-Rotation / Mini-KERI wenn die Sicherheitsanforderungen steigen.

Alle Phasen sind vorwärtskompatibel: Phase 2 → Phase 3 → Phase 4 ohne Breaking Change. Das `deviceKid`-Feld im Personal Doc ([Sync 006](../03-wot-sync/006-personal-doc.md)) ist bereits vorbereitet.

## Zusammenhang mit DID-Methoden

| DID-Methode | Device-Key-Ansatz | Temporale Verifikation |
|---|---|---|
| **did:key** | Phase 2 Delegation oder Phase 3 mit separater WoT-Sigchain — DID = Identity Key, Device Keys sind autorisierte Signateure | Nur mit expliziter Sigchain |
| **did:webvh** | Device Keys als verificationMethods im DID-Dokument, autorisiert durch Log-Einträge | Eingebaut (Verifiable History Log) |
| **did:keri** | Multi-Sig AID oder Delegation — KEL liefert die Chain | Eingebaut (Key Event Log) |

did:webvh ist der natürliche Partner für Phase 3: das DID-Dokument listet alle autorisierten Device Keys, und das Verifiable History Log ermöglicht temporale Verifikation. Phase 2 kann mit `did:key` und self-contained Delegation Proofs starten; Phase 3 sollte Device-Key-Autorisierung und DID-History zusammenführen.

## Offene Fragen

1. **Chain-Größe:** Wie groß wird eine Sigchain nach 5 Jahren mit vielen Geräten? Brauchen wir Checkpointing?
2. **Delegation-Tiefe:** Soll ein Device Key weitere Keys delegieren können (z.B. für Sub-Devices), oder bleibt `device-admin` auf explizit autorisierte Geraete beschraenkt?
3. **Revocation-Semantik in Phase 2:** Wie markieren wir alte Signaturen als weiterhin gueltig, wenn der Device Key nachtraeglich widerrufen wurde?
4. **Interaktion mit Guardian-Vouching:** Wie funktioniert Social Recovery wenn Device Keys im Spiel sind?
