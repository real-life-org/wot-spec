# WoT Identity 003: DID-Dokument und Resolution

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-23
- **Scope:** DID-Dokumente, Resolution-Interface und DID-Methoden-Profile für WoT
- **Depends on:** Identity 001, DID Core, did:key
- **Conformance profile:** `wot-identity@0.1`

## Zusammenfassung

Das WoT-Protokoll arbeitet **DID-Methoden-agnostisch**. Alle Protokoll-Operationen (Signaturen, Verschlüsselung, Verifikation, Broker-Authentisierung) basieren auf **DID-Dokumenten**, nicht auf einer spezifischen DID-Methode. Eine `resolve()`-Funktion liefert das DID-Dokument — egal ob die DID `did:key`, `did:webvh` oder eine andere Methode verwendet.

Dieses Dokument definiert:
- Die normative DID-Dokument-Struktur (Pflichtfelder, optionale Felder)
- Das `resolve()`-Interface
- Method-Bindings für unterstützte DID-Methoden
- Quellen und Caching von DID-Dokumenten

## Referenzierte Standards

- **W3C DID Core** (W3C Recommendation) — DID-Syntax und DID-Dokument-Modell
- **W3C DID Resolution** (W3C Note) — Resolution-Interface und Metadaten
- **did:key** (W3C CCG) — Selbstbeschreibende DIDs aus Public Keys
- **did:webvh** (DIF) — Web-basierte DIDs mit verifiable History

## Grundprinzip

```
Seed → Keys (Identity 001)
  ↓
Keys → DID-Dokument (dieses Dokument)
  ↓
DID-Dokument → resolve() Interface
  ↓
Alle Protokoll-Operationen nutzen resolve()
```

**Identity 001** erzeugt Schlüsselmaterial (Ed25519, X25519) aus dem BIP39-Seed. **Dieses Dokument** definiert, wie aus dem Schlüsselmaterial eine auflösbare Identität mit DID-Dokument wird. Identity-, Trust- und Sync-Dokumente arbeiten über `resolve()` mit DID-Dokumenten.

## DID-Dokument-Struktur

### Kommunikationsfähiges WoT-DID-Dokument

Ein kommunikationsfähiges DID-Dokument enthält neben dem Signing Key auch den X25519-Key für ECIES und optional Service-Endpoints. Ein rein signaturfähiges Dokument (z.B. ein frisch aus `did:key` abgeleitetes Dokument ohne Erstkontakt) MUSS das Feld `keyAgreement` ebenfalls enthalten, DARF es aber als leeres Array setzen.

```json
{
  "id": "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
  "verificationMethod": [
    {
      "id": "#sig-0",
      "type": "Ed25519VerificationKey2020",
      "controller": "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
      "publicKeyMultibase": "z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
    }
  ],
  "authentication": ["#sig-0"],
  "assertionMethod": ["#sig-0"],
  "keyAgreement": [
    {
      "id": "#enc-0",
      "type": "X25519KeyAgreementKey2020",
      "controller": "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
      "publicKeyMultibase": "z6LSxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
  ]
}
```

### Pflichtfelder

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `id` | DID | Die DID selbst |
| `verificationMethod` | Array | Mindestens ein Ed25519 Signing Key |
| `authentication` | Array | Verweis auf verificationMethod — für Broker-Login, Challenge-Response |
| `assertionMethod` | Array | Verweis auf verificationMethod — für Attestation-Signaturen, Capabilities |
| `keyAgreement` | Array | X25519 Encryption Keys für ECIES-Verschlüsselung. Das Feld MUSS vorhanden sein, DARF bei rein signaturfähigen Dokumenten aber leer sein. |

### Optionale Felder

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `service` | Array | Service-Endpoints (z.B. Inbox-Broker) |
| `capabilityDelegation` | Array | Verweis auf verificationMethod — für Capability-Signatur (Zukunft: Per-Device Keys) |

### Service-Endpoint (Inbox-Broker)

```json
{
  "service": [
    {
      "id": "#inbox",
      "type": "WoTInbox",
      "serviceEndpoint": "wss://broker.example.com"
    }
  ]
}
```

Der Service-Endpoint identifiziert den **Inbox-Broker** — den Ort, an dem 1:1-Nachrichten (Attestations, Verifikationen, Space-Einladungen) zugestellt werden. Er ist vergleichbar mit einer E-Mail-Adresse.

**Privacy-Abgrenzung:** Nur der Inbox-Broker steht im DID-Dokument. **Space-Broker** (wo Spaces synchronisiert werden) stehen NICHT im DID-Dokument — sie werden in Space-Einladungen transportiert und sind nur für Space-Members sichtbar. Siehe [Sync 005](../03-wot-sync/005-gruppen.md).

## resolve() — Das Interface

### Signatur

```
resolve(did: string) → DIDDocument | null
```

Ein konformer WoT-Client MUSS eine `resolve()`-Funktion implementieren, die für jede unterstützte DID-Methode ein DID-Dokument liefert. Der Resolver ist eine **lokale Funktion**, kein Service — er greift auf lokale Caches, QR-Code-Daten, den Profil-Service oder den Sync-Layer zu.

### Anforderungen

- `resolve()` MUSS für alle unterstützten DID-Methoden ein DID-Dokument liefern
- `resolve()` DARF Netzwerk-Calls machen (Profil-Service, Broker), aber MUSS auch offline funktionieren wenn das DID-Dokument lokal gecacht ist
- Bei unbekannter DID-Methode: `null` zurückgeben
- Bei bekannter DID-Methode aber fehlendem Dokument: `null` zurückgeben

**Zwei DID-Dokument-Zustände:**

Ein DID-Dokument kann in zwei Zuständen vorliegen:

| Zustand | Felder | Wann | Was geht |
|---|---|---|---|
| **Signaturfähig** | `verificationMethod`, `authentication`, `assertionMethod` | Immer — für did:key aus der DID ableitbar | Signatur-Verifikation, Broker-Auth |
| **Kommunikationsfähig** | Zusätzlich: `keyAgreement`, `service` | Erst nach Erstkontakt (QR-Scan oder Profil-Service) | Verschlüsselung, Inbox-Zustellung |

Für did:key ohne vorherigen Kontakt liefert `resolve()` ein **signaturfähiges** Dokument — `keyAgreement` ist leer weil der X25519-Key nicht aus der DID ableitbar ist (separater HKDF-Pfad). Das reicht um Attestations zu **verifizieren**, aber nicht um Nachrichten zu **verschlüsseln**.

### Wer ruft resolve() auf?

| Caller | Zweck | Felder die er braucht |
|--------|-------|----------------------|
| Identity 002 (Signatur-Verifikation) | Public Key des Signierers | `verificationMethod` via `assertionMethod` |
| Trust 001 (Attestation-Verifikation) | Issuer-Key | `verificationMethod` via `assertionMethod` |
| Trust 002 (Verifikation) | Peer-Key für Challenge-Response | `verificationMethod` via `authentication` |
| Sync 001 (Verschlüsselung) | Encryption Key des Empfängers | `keyAgreement` |
| Sync 003 (Broker-Auth) | DID-Verifikation beim Login | `verificationMethod` via `authentication` |
| Sync 003 (Inbox-Zustellung) | Broker-URL des Empfängers | `service` |
| Sync 001 (Einladung) | Encryption Key für ECIES | `keyAgreement` |

### Zweck-Bindung (MUSS)

Ein Verifier MUSS prüfen dass der verwendete Key für den jeweiligen Zweck autorisiert ist:

- **Attestations und Trust-Lists** MÜSSEN an die Identität gebunden sein. In `wot-identity@0.1` bedeutet das: sie werden mit einem Key signiert der in `assertionMethod` gelistet ist. Eine geplante Phase-2-Erweiterung erlaubt Device-Key-Signaturen nur mit einem vom Identity Key signierten Delegation Proof fuer die Capability `sign-attestation` bzw. `sign-verification`.
- **Broker-Login und Sync** DÜRFEN mit einem Key aus `authentication` signiert werden — das sind Session-bezogene Aktionen
- **Device-Enrollment und Admin-Delegation** SOLLEN mit einem Key aus `capabilityDelegation` signiert werden (Phase 2)

In Phase 1 verweisen `authentication`, `assertionMethod` und `capabilityDelegation` alle auf denselben Key (`#sig-0`). Die Trennung hat aktuell keine praktische Auswirkung, bereitet aber den Wechsel zu Per-Device-Keys vor: Device Keys stehen dann typischerweise in `authentication` und koennen ueber Delegation Proofs zusaetzliche, capability-gebundene Signaturrechte erhalten. Das Delegation-Modell ist noch nicht Teil von `wot-identity@0.1`; siehe [Identity 004](004-device-key-delegation.md).

## DID-Dokument-Quellen

Das DID-Dokument einer Person erreicht andere Teilnehmer auf verschiedenen Wegen. Es gibt keine Priorisierungs-Hierarchie, sondern **verschiedene Quellen für verschiedene Situationen**:

### Erstbefüllung — woher kommt das Dokument beim ersten Kontakt?

**Szenario: In-Person (offline, QR-Scan)**

Der QR-Code (siehe [Trust 002](../02-wot-trust/002-verifikation.md)) enthält Hilfsfelder (`enc`, `broker`), aus denen der Resolver ein Bootstrap-DID-Dokument konstruiert:

```
QR-Code { did, enc, broker, name, nonce, ts }
  → resolve() konstruiert:
    - verificationMethod aus der DID (bei did:key: aus dem Key ableitbar)
    - keyAgreement aus dem enc-Feld
    - service aus dem broker-Feld
```

Das Bootstrap-Dokument ist ein **Provisorium** — es enthält die minimalen Daten für sofortige Kommunikation. Sobald Internet verfügbar ist, holt der Client das vollständige Profil (inkl. DID-Dokument) vom Profil-Service und ersetzt das Provisorium.

**Szenario: Online (Empfehlung durch Freund, Profilsuche)**

Der Client ruft den Profil-Service auf und bekommt das vollständige DID-Dokument als Teil der Profil-Antwort. Kein Bootstrap nötig.

### Lokaler Cache — der Normalfall

Nach dem ersten Kontakt wird das DID-Dokument **lokal gecacht**. Alle folgenden `resolve()`-Aufrufe für diese DID nutzen den Cache — kein Netzwerk-Call. Das garantiert Offline-Fähigkeit: ein Client kann mit allen bekannten Kontakten kommunizieren, auch ohne Internet.

### Aktualisierung — wie erfährt der Client von Änderungen?

In Phase 1 (did:key) ändert sich das DID-Dokument nie — die DID ist der Key, der Key ändert sich nicht. Aktualisierungen betreffen nur Profil-Felder (Name, Bio, Avatar).

In Phase 2 (did:webvh) kann sich das DID-Dokument ändern (Key-Rotation, Broker-Wechsel). Updates werden über zwei Wege propagiert:

- **Push:** Inbox-Nachricht (`did-document-update/1.0`) an alle Kontakte — sofortige Benachrichtigung
- **Pull:** Periodischer Refresh vom Profil-Service — Fallback für Kontakte die die Inbox-Nachricht verpasst haben

### Profil-Service als DID-Dokument-Quelle

Der Profil-Service ([Sync 004](../03-wot-sync/004-discovery.md)) liefert das DID-Dokument **als Teil der Profil-Antwort** — ein Call, ein Response:

```
GET /p/{did} → JWS-signiertes Profil mit eingebettetem DID-Dokument
```

```json
{
  "did": "did:key:z6Mk...",
  "version": 42,
  "didDocument": {
    "id": "did:key:z6Mk...",
    "verificationMethod": [...],
    "authentication": [...],
    "assertionMethod": [...],
    "keyAgreement": [...]
  },
  "profile": {
    "name": "Alice",
    "bio": "...",
    "avatar": "...",
    "protocols": [...]
  },
  "updatedAt": "2026-04-23T10:00:00Z"
}
```

**Warum ein Call statt zwei:**

- Ein Netzwerk-Call statt zwei — bei Mobilgeräten mit schlechtem Netz zählt jeder Call
- Atomare Konsistenz — DID-Dokument und Profil sind im selben JWS signiert, können nicht auseinanderlaufen
- Einfacherer Cache — ein Objekt pro DID

**Phase-2-Erweiterung:** Für did:webvh-konforme externe Resolution kann ein zusätzlicher Endpoint `GET /p/{did}/log` das JSONL-Log liefern. Für WoT-Clients bleibt der primäre Pfad über `/p/{did}`.

Der Client prüft die JWS-Signatur und die `version`-Monotonie (siehe [Sync 004 Rollback-Schutz](../03-wot-sync/004-discovery.md#versionierung-und-rollback-schutz)).

### Zusammenfassung der Quellen pro Situation

| Situation | Quelle | Was der Client bekommt |
|---|---|---|
| Erstkontakt offline (QR-Scan) | QR-Code-Felder | Bootstrap-Dokument (Provisorium) |
| Erstkontakt online (Empfehlung) | Profil-Service | Vollständiges Profil + DID-Dokument |
| Bekannter Kontakt | Lokaler Cache | Gecachtes DID-Dokument |
| Profil-Änderung (Name, Bio) | Profil-Service (Pull) oder Inbox (Push) | Aktualisiertes Profil |
| Key-Rotation (Phase 2) | Inbox (Push) + Profil-Service (Pull) | Neues DID-Dokument |

## Method-Bindings

### did:key (Phase 1 — normativ)

Bei `did:key` ist der Ed25519 Public Key direkt in der DID kodiert. `resolve()` generiert das DID-Dokument **deterministisch** aus dem Key — kein Netzwerk-Call, keine Speicherung.

```
resolve("did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK")

1. Multibase-Decode: 'z' entfernen → Base58btc-Decode
2. Multicodec-Prefix 0xed01 entfernen → 32 Bytes Ed25519 Public Key
3. DID-Dokument generieren:
   {
     id: did,
     verificationMethod: [{ id: "#sig-0", type: "Ed25519VerificationKey2020", publicKeyMultibase: ... }],
     authentication: ["#sig-0"],
     assertionMethod: ["#sig-0"],
     keyAgreement: []   ← LEER — X25519-Key ist nicht aus did:key ableitbar
   }
```

#### Das keyAgreement-Problem bei did:key

Der X25519 Encryption Key wird über einen separaten HKDF-Pfad abgeleitet (siehe [Identity 001](001-identitaet-und-schluesselableitung.md)) und ist **nicht aus der `did:key` ableitbar**. Deshalb ist `keyAgreement` im generierten Dokument zunächst leer.

Der Resolver befüllt `keyAgreement` aus externen Quellen:

- **QR-Code:** Das `enc`-Feld (siehe [Trust 002](../02-wot-trust/002-verifikation.md)) wird in `keyAgreement` eingetragen
- **Profil-Service:** Das eingebettete DID-Dokument (siehe [Sync 004](../03-wot-sync/004-discovery.md)) liefert `keyAgreement`

Dies ist ein **bekannter Workaround** für die Phase-1-Architektur. In Phase 2 (did:webvh) steht der Encryption Key direkt im DID-Dokument.

### did:webvh (Phase 2 — informativ, nicht normativ)

`did:webvh` speichert ein JSONL-Log (JSON Lines) mit hash-verketteten, signierten DID-Dokument-Versionen. Das Log ist ein **selbst-verifizierendes Artefakt** — wer das Log hat, kann die gesamte History kryptographisch prüfen, unabhängig davon wie er es bekommen hat.

```
resolve("did:webvh:example.com:user:alice")

1. Lokales Log suchen (Cache)
2. Falls nicht vorhanden: Log vom Profil-Service holen (GET /p/{did}/log)
3. Log verifizieren: Hash-Kette + Signaturen prüfen
4. Neuesten Eintrag extrahieren → aktuelles DID-Dokument
```

**Distribution des Logs:**

| Kanal | Wann | Spec-konform? |
|---|---|---|
| HTTPS (Profil-Service) | Standard-Resolution | Ja (did:webvh-Spec) |
| Sync-Layer (bilateral) | Offline-Sync zwischen Peers | WoT-Extension |
| Inbox-Nachricht | Key-Rotation-Benachrichtigung | WoT-Extension |
| QR-Code | Genesis-Dokument beim Erstkontakt | WoT-Extension |

Solange das Log **auch** über HTTPS auf dem Profil-Service verfügbar ist, bleibt die Nutzung did:webvh-spec-konform. Die zusätzlichen Kanäle (Sync, Inbox, QR) sind WoT-spezifische Erweiterungen für Offline-Szenarien.

**Vorteile gegenüber did:key:**

- **Key-Rotation bei stabiler DID** — neuer Log-Eintrag, DID ändert sich nicht
- **keyAgreement nativ im Dokument** — kein enc-Feld-Hack nötig
- **service nativ im Dokument** — kein broker-Feld-Hack nötig
- **Per-Device Keys** — mehrere verificationMethod-Einträge möglich
- **Verifiable History** — die gesamte Schlüsselhistorie ist nachvollziehbar

**Die Migration von did:key zu did:webvh ist KEIN Breaking Change** auf Protokoll-Ebene — nur ein neuer Resolver hinter demselben Interface.

## DID-Methoden-Koexistenz

Ein WoT-Netzwerk KANN gemischte DID-Methoden enthalten. Alice nutzt `did:key`, Bob nutzt `did:webvh` — beide können miteinander kommunizieren, solange beide Clients Resolver für beide Methoden haben.

**Anforderung:** Jeder konforme WoT-Client MUSS `did:key` unterstützen. Weitere Methoden sind optional.

**Für den Übergang (Phase 1 → Phase 2):**

- Neue Clients starten mit did:key (einfach, keine Infrastruktur nötig)
- Clients können optional auf did:webvh upgraden
- Alte DIDs (did:key) bleiben verifizierbar — Attestations die mit einer did:key-DID signiert wurden, bleiben gültig
- Die DID-Methoden-Migration ([identity-migration.md](../research/identity-migration.md)) definiert wie alte DIDs auf neue verweisen

## Admin-Keys

Space-Admin-Keys (siehe [Sync 001](../03-wot-sync/001-verschluesselung.md#admin-key-abgeleitet), [Sync 005](../03-wot-sync/005-gruppen.md)) sind **immer did:key** — unabhängig von der DID-Methode des Users. Sie sind:

- Space-spezifisch (per HKDF abgeleitet)
- Kurzlebig (nur für Broker-Management)
- Nicht verknüpfbar mit der Haupt-DID (Privacy)

Für Admin-Keys gibt es keinen Grund für DID-Dokumente oder Key-Rotation — sie werden bei Space-Rotation einfach neu abgeleitet.
