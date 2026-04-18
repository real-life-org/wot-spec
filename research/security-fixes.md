# Security Fixes — Aufwand und Trade-offs

*Stand: 2026-04-18*

Konkrete Analyse was es bedeuten würde jede identifizierte Schwachstelle zu beheben. Eingeteilt nach Aufwand: Quick Wins → Moderate Arbeit → Fundamentale Änderungen.

## Quick Wins (1-2 Tage Arbeit)

### Fix K4: JWS `alg` strict enforcement

**Spec-Änderung:** Ein Absatz in 002 Signaturen:

> Verifier MÜSSEN das `alg`-Feld im JWS-Header prüfen. Nur `"EdDSA"` ist akzeptiert. Jede andere Angabe (inklusive `"none"`, `"HS256"`, `"RS256"`) MUSS zur Ablehnung der Nachricht führen, noch bevor die Signatur verifiziert wird.

**Implementierung:**
```typescript
function verifyJws(jws: string) {
  const header = JSON.parse(base64urlDecode(jws.split('.')[0]))
  if (header.alg !== 'EdDSA') {
    throw new Error('Invalid algorithm')  // Reject before verify
  }
  // ... normal verification
}
```

**Trade-off:** Keiner. Reine Sicherheits-Verbesserung.

**Breaking Change:** Nein.

**Aufwand:** 30 Minuten + Tests.

---

### Fix S2: Nonce-History im Challenge-Response

**Spec-Änderung:** In 004 Verifikation:

> Empfänger MÜSSEN empfangene Challenge-Nonces für mindestens 24 Stunden speichern. Eine Challenge mit bereits gesehener Nonce MUSS abgelehnt werden.

**Implementierung:** Ein bounded Cache (LRU oder Time-based):
```typescript
const seenNonces = new TimedCache<string>(24 * 3600 * 1000)

function acceptChallenge(challenge) {
  if (seenNonces.has(challenge.nonce)) {
    throw new Error('Nonce replay detected')
  }
  seenNonces.add(challenge.nonce)
  // ... normal validation
}
```

**Trade-off:** Etwas Memory auf dem Gerät (bei 1000 Challenges/Tag à 32 Bytes = 32KB — vernachlässigbar).

**Breaking Change:** Nein.

**Aufwand:** 1-2 Stunden.

---

### Fix S4: Capability `validUntil`

**Spec-Änderung:** Das Capability-Schema ergänzen:

```json
{
  "type": "capability",
  "issuer": "did:key:z6Mk...",
  "audience": "did:key:z6Mk...",
  "docId": "...",
  "permissions": ["read", "write"],
  "generation": 3,
  "issuedAt": "2026-04-18T10:00:00Z",
  "validUntil": "2026-10-18T10:00:00Z"  // NEU
}
```

Broker prüft: `now < validUntil` vor jedem Zugriff.

**Trade-off:** Admin muss Capabilities regelmäßig erneuern. Erhöht Workload leicht. Aber: erzwingt sichere Praxis.

**Default-Empfehlung:** 6 Monate Gültigkeit. Bei kritischen Spaces kürzer.

**Breaking Change:** Teilweise — bestehende Capabilities ohne `validUntil` müssten als "legacy" akzeptiert werden oder migriert.

**Aufwand:** Halber Tag (Schema, Prüfung, Erneuerungs-Logik).

---

### Fix M5: JCS Test-Vektoren

**Spec-Änderung:** Erweiterung der Test-Vektoren um Edge-Cases:
- Unicode-Zeichen (€, 日本語, 🌍)
- Zahlen-Edge-Cases (0.1, 1e-1, -0, Infinity)
- Leere Strings vs null vs missing
- Verschachtelte Objekte mit unsortierten Keys

**Implementierung:** Test-Suite in der Spec, die alle konformen Implementierungen bestehen müssen.

**Trade-off:** Keiner. Nur Dokumentations-Arbeit.

**Aufwand:** Halber Tag.

---

## Moderate Arbeit (1-2 Wochen)

### Fix K2: AES-GCM Nonce-Reuse verhindern

**Option A: Deterministische Nonces**

Spec-Änderung in 005:

```
Nonce-Konstruktion:
  [4 Bytes: deviceId-Hash] || [8 Bytes: Counter pro Device]
  
Jedes Device führt einen monotonen Counter pro Space.
Counter wird zusammen mit dem Log-Eintrag persistiert.
```

**Vorteil:** Nie Kollisionen solange Devices ihre Counter nicht zurücksetzen.

**Nachteil:** Counter muss persistent sein (Browser: IndexedDB). Bei Backup-Restore muss Counter mit zurückgeholt werden, sonst Reuse-Gefahr.

**Option B: Automatische Key-Rotation**

Spec-Änderung: Jede 2^32 Nachrichten erzwungene Key-Rotation.

**Vorteil:** Einfacher, keine Counter-Persistenz.

**Nachteil:** Häufige Key-Rotation = mehr Overhead für alle Mitglieder.

**Option C: XChaCha20-Poly1305 (24-Byte Nonce)**

Spec-Änderung: AES-256-GCM ersetzen durch XChaCha20-Poly1305.

**Vorteil:** 192-Bit Nonce — kein Birthday-Problem realistisch möglich.

**Nachteil:**
- Web Crypto API unterstützt XChaCha20 **nicht nativ**
- Bräuchte externe Bibliothek (libsodium, @noble/ciphers)
- Inkonsistent mit DIDComm (nutzt AES-GCM)

**Empfehlung:** Option A (deterministische Nonces) — bleibt kompatibel mit Web Crypto und DIDComm, eliminiert das Problem sauber.

**Aufwand:** 1 Woche (Spec + Implementierung + Tests + Counter-Persistenz-Logik).

**Breaking Change:** Ja — alte Log-Einträge nach anderem Schema verschlüsselt. Migration nötig.

---

### Fix S3: Split-Brain-Detection

**Spec-Änderung:** Neuer Nachrichtentyp `state-digest` in 006:

```json
{
  "type": ".../state-digest/1.0",
  "docId": "...",
  "latestSeq": { "deviceId1": 42, "deviceId2": 17, ... },
  "rootHash": "<SHA-256 des gesamten sortierten Log-States>",
  "timestamp": "..."
}
```

Mitglieder tauschen regelmäßig `state-digest` Nachrichten aus (z.B. alle 10 Minuten). Bei Divergenz:
1. Detailliertere Sequenz-Level-Vergleiche
2. Wenn konsistente Divergenz → Alarm an User
3. User kann manuell mit anderen Mitgliedern syncen (P2P) um Broker-Manipulation zu umgehen

**Trade-off:** Etwas mehr Bandbreite (Digest-Nachrichten). Aber: Detection von Censorship.

**Aufwand:** 1 Woche (Protokoll + Hash-Logic + UI für Divergenz-Alarm).

**Breaking Change:** Nein (additive).

---

### Fix M6: Device-Revokation und TTL

**Spec-Änderung:** In 006 Sync-Protokoll:

```
Jedes Device hat:
  - registeredAt: ISO timestamp
  - lastActive: ISO timestamp (aktualisiert bei jeder Aktivität)
  - revokedAt: ISO timestamp (null wenn aktiv)

Deregistrierung:
  - Expliziter User-Action ("Gerät abmelden")
  - Oder automatisch wenn lastActive > 6 Monate

Nach revokedAt:
  - Keine neuen Log-Einträge von diesem Device akzeptiert
  - Historische Einträge bleiben gültig (waren ja zu ihrer Zeit gültig)
```

**Implementierung:** Device-Registry im persönlichen Dokument. Periodische Checks.

**Trade-off:** Kompliziert Multi-Device-Lifecycle. User müssen verstehen "wenn du dein Gerät 6 Monate nicht benutzt, wirst du abgemeldet."

**Aufwand:** 1-2 Wochen (Spec + UI + Device-Lifecycle).

**Breaking Change:** Ja — alte Devices ohne `registeredAt` brauchen Default-Werte.

---

### Fix M4: Attestation-Rate-Limiting

**Spec-Änderung:** In 007 Transport:

```
Broker MUSS Rate-Limits für Inbox-Nachrichten durchsetzen:
  - Max 100 Nachrichten pro Sender-DID pro Empfänger pro Tag
  - Max 1000 Nachrichten pro Sender-DID total pro Tag
  
Bei Überschreitung: Nachrichten werden vom Broker verworfen,
Sender bekommt Fehler zurück.
```

**Trade-off:** Legitime Bulk-Operationen (Massen-Import) werden gebremst. Lösung: Explizite höhere Limits für verifizierte Organisationen (aber: wer verifiziert?).

**Aufwand:** 3-5 Tage (Broker-seitige Logik + Client-seitige Retry).

**Breaking Change:** Nein.

---

### Fix K3: Admin-only Felder für Space-Metadata

**Spec-Änderung:** Zurück zur Option B unserer früheren Diskussion — verschiedene Dokumente mit verschiedenen Keys:

```
Pro Space:
  - Doc-Content (Space Key, alle Members können schreiben)
  - Doc-Metadata (Admin Key, nur Admin kann schreiben)  NEU
  - Doc-Members (Admin Key, nur Admin kann schreiben)   NEU
```

Admin hält zwei Keys: Space Key (teilt er mit Members) + Admin Key (behält er).

Member können Space Key für Content nutzen, aber haben Admin Key nicht → können Metadata nicht ändern.

**Trade-off:** Zusätzliche Komplexität. Drei Keys pro Space. Aber: echte Admin-Protection.

**Aufwand:** 1-2 Wochen (Spec-Änderung, Crypto-Layer, UI).

**Breaking Change:** Ja — Space-Struktur ändert sich.

---

## Fundamentale Änderungen (Monate)

### Fix K1: Multi-Admin / Threshold Signatures

**Ansatz A: Einfaches Multi-Admin-Modell**

Spec-Änderung:

```
members[0..k] sind Admins (k konfigurierbar pro Space, Default: k=1)

Destruktive Aktionen (Remove Member, Key Rotation) brauchen:
  - k=1: Single-Admin signiert (wie jetzt)
  - k=2-3: Beide/alle Admins müssen signieren (innerhalb 24h)
  - k>3: Mehrheit (ceil(k/2)+1) muss signieren
```

Implementation: Sammlung von Signaturen, Quorum-Check.

**Vorteil:** Einfach, versteht jeder.

**Nachteil:** Bei Offline-Admin blockiert.

**Ansatz B: FROST Threshold Signatures**

Echtes kryptographisches Threshold-Schema:
- M-von-N Admins kombinieren Partial-Signatures
- Resultierende Signatur ist mathematisch wie Single-Signature
- Verifier sieht nur eine Signatur, nicht M

**Vorteil:** Elegant, verifier-side unverändert.

**Nachteil:** Komplexe Krypto. FROST ist noch nicht in Web Crypto API.

**Empfehlung:** Ansatz A für v1.0, Ansatz B als späteres Upgrade.

**Aufwand für Ansatz A:** 2-3 Wochen (Quorum-Logic, Partial-Sig-Collection, Spec-Änderungen).

**Breaking Change:** Ja.

---

### Fix S1: Forward Secrecy via Double-Ratchet

**Ansatz:** Signal-Protokoll-Style Double-Ratchet für Inbox.

**Spec-Änderung:** Komplett neuer Abschnitt in 005:

```
Double-Ratchet State pro (Alice, Bob) Paar:
  - Root Key
  - Sending Chain Key
  - Receiving Chain Key
  - Ephemeral DH Pair
  
Bei jeder Nachricht:
  - DH-Ratchet (wenn neuer Ephemeral Key empfangen)
  - Symmetric-Key-Ratchet (HKDF)
  - Neue Message Key
```

**Trade-off:**
- **Massive Komplexität** (Signal Protocol ist hunderte Seiten)
- State muss synchron gehalten werden zwischen Geräten
- Out-of-Order Delivery braucht Message-Key-Caching
- Multi-Device wird noch komplexer (Sesame Protocol)

**Vorteil:** Echte Forward Secrecy. Kompromittierte Keys = nur zukünftige Nachrichten gefährdet.

**Empfehlung:** Nur wenn Bedrohungsmodell es erfordert (Journalisten, Aktivisten). Nicht für normale Communities.

**Aufwand:** 2-3 Monate (wirklich).

**Breaking Change:** Fundamental. Eigenes Sub-Protokoll.

---

### Fix: Capability-Chains (Keyhive-Style)

**Ansatz:** Vertrauen kryptographisch statt sozial.

Jede CRDT-Operation trägt eine Capability-Chain:
```
Alice (Admin, Root Capability)
  → signiert Capability für Bob: "write content"
    → Bob erstellt Sub-Capability für Bob's Mobile: "write content"
      → Mobile schreibt Operation mit voller Chain

Empfänger verifiziert:
  1. Alice ist Admin ✓
  2. Alices Cap für Bob gültig ✓
  3. Bobs Delegation an Mobile gültig ✓
  4. Operation in Mobile's Scope ✓
  → Accept
```

**Vorteil:** Kryptographisch durchgesetzte Permissions. Keine "malicious member" Probleme mehr.

**Nachteil:**
- Jede Operation trägt Capability-Chain mit (mehr Daten)
- CRDT-Merge muss Chains verifizieren
- Revocation wird komplex (Capability-Revocation-Propagation)
- **Massive Komplexität**

**Empfehlung:** Auf Keyhive/Beelay warten. Nicht selbst bauen.

**Aufwand:** 3-6 Monate selbst gebaut. Oder warten bis Keyhive produktionsreif ist.

---

## Priorisierungs-Matrix

| Fix | Aufwand | Impact | Priorität |
|-----|---------|--------|-----------|
| K4: alg-Strict | 30 min | Hoch | **Sofort** |
| S2: Nonce-History | 2h | Mittel | **Sofort** |
| S4: Capability TTL | 4h | Mittel | **Sofort** |
| M5: JCS Test-Vektoren | 4h | Niedrig | **Sofort** |
| K2: Deterministische Nonces | 1 Woche | Hoch | **v1.1** |
| M4: Rate-Limiting | 3-5 Tage | Mittel | **v1.1** |
| M6: Device-TTL | 1-2 Wochen | Hoch | **v1.1** |
| S3: Split-Brain Detection | 1 Woche | Hoch | **v1.1** |
| K3: Admin-only Metadata | 1-2 Wochen | Mittel | **v1.2** |
| K1: Multi-Admin | 2-3 Wochen | Hoch | **v1.2** |
| S1: Forward Secrecy | 2-3 Monate | Hoch | **v2.0** |
| Capability-Chains | 3-6 Monate | Hoch | **v2.0+** |

## Gesamt-Aufwand für Production-Ready

**Minimum für v1.0 Production:**
- Alle Quick Wins (~3 Tage)
- K2 (Nonce-Reuse Fix, ~1 Woche)
- **Total: ~2 Wochen**

**Für "nicht-trivial-secure" (gegen casual attackers):**
- Alles aus v1.0
- + M6 (Device-TTL), S3 (Split-Brain), M4 (Rate-Limiting), K3 (Admin Metadata), K1 (Multi-Admin)
- **Total: ~6-8 Wochen**

**Für "adversarial-hard" (gegen state-level attackers):**
- Alles aus v1.1
- + S1 (Double-Ratchet), Capability-Chains
- **Total: 6-12 Monate**

## Strategische Empfehlung

**Phase 1 (jetzt, 2 Wochen):** Quick Wins + Nonce-Fix. Damit sind wir auf "Community-Tool sicher" Niveau.

**Phase 2 (nächste 2 Monate):** Multi-Admin, Device-TTL, Split-Brain-Detection. Damit sind wir auf "für ernste Projekte sicher" Niveau — vergleichbar mit Matrix, Signal (ohne deren Forward Secrecy).

**Phase 3 (2027):** Forward Secrecy via Double-Ratchet ODER warten auf Keyhive für kryptographische Permissions. Dann sind wir auf "ernste Sicherheit gegen Staat" Niveau.

Die kritische Einsicht: **Phase 1 ist schnell und günstig zu haben.** Es gibt keinen guten Grund das nicht sofort zu machen. Die Spec wird dadurch ernster genommen und die Sicherheit messbar besser.

Phase 2 ist mittelfristige Arbeit die die Implementierung erfordert.

Phase 3 ist entweder ein eigenes großes Projekt oder Warten auf Ökosystem-Entwicklung (Keyhive/Beelay).
