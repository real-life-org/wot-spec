# WoT Sync-Architektur

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-12
- **Grundlage:** Forschungsdokument 005-sync-and-transport.md

## Zusammenfassung

Dieses Dokument beschreibt die Sync-Architektur des Web of Trust Protokolls. Es definiert wie Daten zwischen Peers synchronisiert werden — verschlüsselt, CRDT-agnostisch, und ohne zentralen Server.

---

## 1. Grundprinzip

**Ein Peer ist ein Peer ist ein Peer.**

Es gibt keinen Unterschied zwischen einem Handy, einem Laptop, einem Community-Broker oder einem anderen User. Das Sync-Protokoll ist immer dasselbe. Ein Broker ist ein Peer der zufällig immer online ist und Push-Notifications verschicken kann.

Daraus folgt:
- Zwei Handys im selben WLAN können direkt syncen
- Ein Handy und ein Broker syncen über das Internet
- Wenn der Broker down ist, syncen die Handys trotzdem — nur wenn beide online sind
- Das Protokoll muss auf allen Transportwegen funktionieren: WebSocket, QUIC, Bluetooth, Sneakernet

---

## 2. Device-Keys

### Warum Device-Keys?

Jedes Gerät braucht eine eigene kryptografische Identität. Zwei Gründe:

1. **Sync:** Log-Einträge müssen eindeutig einem Gerät zugeordnet werden. Sonst können zwei Geräte desselben Users Sequenznummern-Konflikte erzeugen.

2. **Double-Spend-Prevention:** In Sebastians Human Money Core müssen Gutscheine auf genau einem Gerät leben. Ein Gutschein gehört nicht "Alice", sondern "Alice-auf-ihrem-Handy". Transfer nur durch explizite Übergabe zwischen Device-Keys.

### Hierarchie

```
BIP39 Seed (12 Wörter)
  → HKDF("wot/identity/ed25519/v1") → Master Key (= DID)
      → Delegation an Device Key A (Handy)
      → Delegation an Device Key B (Laptop)
      → Delegation an Device Key C (...)
```

Der Master Key ist der Root of Trust. Er delegiert an Device-Keys. Device-Keys signieren die Log-Einträge. Jeder kann verifizieren: "Dieser Eintrag kommt von Alices Handy, autorisiert durch Alices Identität."

### Device-Key-Erzeugung

Device-Keys sind **zufällig** — nicht aus dem Seed ableitbar. Das garantiert Einzigartigkeit und verhindert versehentlichen Double Spend.

### Login-Flows

**Erstes Gerät (Onboarding):**

```
1. Seed eingeben (oder generieren)
2. Master Key ableiten
3. Zufälligen Device Key generieren
4. Master Key signiert Delegation an Device Key
5. Fertig — Gerät ist autorisiert
```

**Neues Gerät hinzufügen (bestehendes Gerät verfügbar):**

```
1. Neues Gerät: App öffnen → "QR-Code scannen"
2. Neues Gerät: Generiert zufälligen Device Key, zeigt QR-Code
3. Bestehendes Gerät: Scannt QR → "Laptop möchte Zugang" → bestätigen
4. Bestehendes Gerät: Signiert Delegation mit Master Key
5. Bestehendes Gerät: Sendet Delegation + Daten an neues Gerät
6. Neues Gerät: Hat Device Key + Delegation + Daten
```

Vorteil: Der Seed wird nicht auf dem neuen Gerät eingegeben. Sicherer.

**Neues Gerät hinzufügen (bestehendes Gerät NICHT verfügbar):**

```
1. Neues Gerät: Seed eingeben
2. Master Key ableiten → neuen zufälligen Device Key generieren
3. Master Key signiert Delegation
4. Verbindung zum Broker → Daten holen
5. Fertig — funktioniert auch wenn das alte Gerät aus ist
```

Weniger sicher (Seed muss eingegeben werden), aber funktioniert immer.

**Recovery (alle Geräte verloren):**

```
1. Neues Gerät: Seed eingeben
2. Master Key ableiten → Recovery Device Key generieren
   (deterministisch: HKDF(seed, "wot/device/recovery/v1"))
3. Master Key signiert Delegation an Recovery Key
4. Broker liefert verschlüsselte Daten aus
5. Sofort: Zufälligen Device Key generieren für Normalbetrieb
6. Recovery Key wird nicht weiterbenutzt
```

### Delegation

Eine Delegation ist ein signiertes Dokument:

```
{
  type:       "device-delegation"
  masterDid:  "did:key:z6Mk..."        (die Identität)
  deviceKey:  "z6Mk..."                (Public Key des Geräts)
  capability: "full"                    (was das Gerät darf)
  issuedAt:   "2026-04-12T..."
  sig:        Ed25519-Signatur des Master Key
}
```

Jeder kann verifizieren: DID → Public Key extrahieren → Signatur prüfen → ja, dieses Gerät ist autorisiert.

### Für WoT und Human Money Core

Dasselbe Device-Key-Modell, unterschiedliche Nutzung:

| | WoT (Sync) | Human Money Core (Payment) |
|--|-----------|---------------------------|
| **Device Key signiert** | Log-Einträge | Transaktionen |
| **Daten-Replikation** | Alle Geräte haben alles | Gutschein lebt auf einem Gerät |
| **Double Spend** | Kein Problem (CRDT merged) | Muss verhindert werden |
| **Transfer** | Automatisch (Sync) | Explizit (Device A → Device B) |

Das gemeinsame Fundament: **Kryptografisch verifizierbare Geräte-Identität, delegiert von der Master-Identität.**

---

## 3. Drei Schichten

```
┌─────────────────────────────────────────────────┐
│  Schicht 3: Reconciliation                      │
│  Effiziente Differenz-Berechnung (RIBLT)        │
│  Für: Reconnect nach langer Offline-Zeit        │
├─────────────────────────────────────────────────┤
│  Schicht 2: Kompression                         │
│  Deterministische Chunk-Bildung (Sedimentree)   │
│  Für: Alte History komprimieren                  │
├─────────────────────────────────────────────────┤
│  Schicht 1: Log                                 │
│  Append-only Einträge pro Peer pro Dokument     │
│  Für: Echtzeit-Sync, normale Nutzung            │
└─────────────────────────────────────────────────┘
```

### Schicht 1: Log

Jeder Peer führt einen Append-only Log pro Dokument. Jeder Eintrag ist ein verschlüsselter Blob — das Protokoll weiß nicht was drin ist (Yjs-Update, Automerge-Change, oder etwas anderes).

**Struktur eines Log-Eintrags:**

```
{
  seq:       Sequenznummer (aufsteigend, pro Device pro Dokument)
  deviceKey: Public Key des Geräts das den Eintrag erzeugt hat
  docId:     Zu welchem Dokument gehört er
  data:      Verschlüsselter Blob (der CRDT-Update)
  timestamp: Wann erzeugt
  sig:       Ed25519-Signatur des Device Keys
}
```

Der `deviceKey` identifiziert das Gerät eindeutig. Die Signatur beweist dass der Eintrag wirklich von diesem Gerät kommt. Über die Delegation kann jeder prüfen: Device Key → Master Key → DID.

**Sync zwischen zwei Peers:**

```
Alice: "Für Dokument X habe ich von dir Einträge bis seq 47. Was kommt danach?"
Bob:   "Hier sind meine Einträge 48, 49, 50."
Alice: "Und hier sind meine Einträge die du noch nicht hast."
```

Das ist alles. Kein Full State Exchange. Kein Broadcast an N Members. Kein DAG, keine Hash-Verlinkung. Nur: "Was hast du, was ich nicht habe?"

**Warum das den Loop löst:**

Jeder Peer schreibt nur in seinen EIGENEN Log. Empfangene Einträge werden in den Log des Absenders geschrieben, nicht in den eigenen. Es gibt physisch keine Möglichkeit, empfangene Daten als eigene weiterzusenden.

**CRDT-Agnostik:**

Der Log-Eintrag enthält einen verschlüsselten Blob. Das Protokoll weiß nicht ob da ein Yjs-Update, ein Automerge-Change oder ein Loro-Op drin steckt. Der CRDT-Adapter auf dem Client entschlüsselt den Blob und wendet ihn an. Das Sync-Protokoll selbst ist CRDT-frei.

### Schicht 2: Kompression

Log-Einträge akkumulieren über Zeit. Bei einem Dokument mit tausenden Änderungen über Monate wird der Log groß. Ein neuer Peer müsste alle einzelnen Einträge herunterladen und anwenden — langsam (Niks Erfahrung: 250k Einträge = 1,6 Sekunden).

**Lösung: Deterministische Kompression.**

Alte Log-Einträge werden zu größeren Chunks zusammengefasst. Der Chunk enthält den komprimierten CRDT-State für diesen Abschnitt der History. Alle Peers berechnen unabhängig dieselben Chunks — kein Koordinator nötig, kein byzantinisches Problem.

**Das Sedimentree-Prinzip:**

- Chunk-Grenzen werden durch Hash-Eigenschaften bestimmt (z.B. führende Null-Bytes im BLAKE3-Hash eines Eintrags)
- Level 1 Chunks: ca. alle 256 Einträge
- Level 2 Chunks: ca. alle 65.536 Einträge
- Ältere History → größere Chunks → weniger Metadaten
- Für 1 Million Einträge: nur ~15 Level-2-Chunks in der minimalen Struktur

**Wann wird komprimiert?**

Jeder Peer komprimiert lokal und unabhängig. Es gibt keinen Zeitpunkt an dem "der Snapshot erstellt wird" — die Kompression ergibt sich mathematisch aus den Einträgen selbst. Verschiedene Peers komprimieren zu verschiedenen Zeiten, kommen aber auf dieselben Chunks.

### Schicht 3: Reconciliation

Wenn zwei Peers stark divergiert sind (z.B. nach Wochen offline), wäre es ineffizient alle fehlenden Einträge einzeln aufzuzählen. Stattdessen: effiziente Set-Reconciliation.

**RIBLT (Rateless Invertible Bloom Lookup Tables):**

- Peer A streamt Coded Symbols
- Peer B vergleicht mit seinen eigenen
- Ergebnis: beide wissen exakt was dem anderen fehlt
- Datenmenge: 1,35x die tatsächliche Differenz (mathematisch bewiesen)
- Parameterlos — kein Tuning nötig
- 1 Milliarde Items, 5 Unterschiede → ca. 240 Bytes

**Wann wird RIBLT genutzt?**

Nicht bei jedem Sync. RIBLT kommt zum Einsatz wenn:
- Ein Peer sehr lange offline war
- Zwei Peers sich zum ersten Mal begegnen
- Die Sequenznummern-basierte Sync nicht ausreicht (Lücken, Kompression)

Für den normalen Echtzeit-Sync (Schicht 1) reichen die Sequenznummern.

---

## 3. Verschlüsselung

Alles was das Gerät verlässt ist verschlüsselt und signiert.

### Zwei Schemata

**Für geteilte Daten (Spaces):**

Alle Mitglieder eines Spaces teilen einen symmetrischen Schlüssel. Log-Einträge werden damit verschlüsselt. Bei Member-Entfernung: neuer Schlüssel, an alle verbleibenden Members verteilt.

```
Klartext-Update → AES-256-GCM (Space Key) → verschlüsselter Log-Eintrag
```

**Für 1:1-Nachrichten (Attestations, Einladungen):**

Sender verschlüsselt mit dem öffentlichen Schlüssel des Empfängers. Forward Secrecy durch ephemere Schlüssel.

```
Klartext → X25519 ECIES (Empfänger Public Key) → verschlüsselte Nachricht
```

### Was der Broker sieht

Der Broker sieht:
- Verschlüsselte Blobs
- Wer an wen sendet (DIDs)
- Zeitstempel
- Dokumenten-IDs
- Sequenznummern

Der Broker sieht NICHT:
- Den Inhalt der Daten
- Welcher CRDT-Typ verwendet wird
- Was in den Dokumenten steht

---

## 4. Broker

Ein Broker ist ein Peer mit Superkräften:

| Eigenschaft | Normaler Peer | Broker |
|-------------|--------------|--------|
| Online | Manchmal | Immer |
| Speichert Daten | Lokal (CompactStore) | Für alle Members |
| Push Notifications | Nein | Ja (UnifiedPush/ntfy) |
| Erreichbar | Nur im LAN / via NAT Traversal | Öffentliche IP |
| Betrieben von | User | Community oder Anbieter |

### Was ein Broker speichert

- **Verschlüsselte Log-Einträge** für alle Dokumente seiner User
- **Komprimierte Chunks** (Sedimentree) für alte History
- **Inbox-Nachrichten** für async Delivery (Push-Trigger)
- **Push-Endpoints** für Offline-Notifications

### Multi-Broker

Ein User kann mehrere Broker nutzen. Daten werden auf alle repliziert. Failover automatisch — wenn Broker A down ist, nutzt der Client Broker B.

Broker kommunizieren NICHT miteinander. Es gibt kein Federation-Protokoll. Der Client repliziert zu mehreren Brokern, das reicht.

### Jede Community kann einen Broker betreiben

Ein Broker ist ein einfacher Service:
- Nimmt verschlüsselte Blobs entgegen
- Speichert sie (SQLite, S3, was auch immer)
- Liefert sie auf Anfrage aus
- Sendet Push-Notifications wenn User offline sind

Kein Domain-Name nötig (IP reicht). Kein Verständnis der Daten nötig. Kein CRDT-Code nötig. Dumm und einfach — wie ein Nostr-Relay, aber mit Autorisierung durch das Web of Trust.

---

## 5. Transport

Das Sync-Protokoll ist transport-agnostisch. Es funktioniert über:

- **WebSocket** — Echtzeit, Browser-kompatibel (jetzt)
- **QUIC** — Effizienter, Multipath, NAT Traversal (via Iroh, später)
- **Bluetooth / WiFi Direct** — Lokales Mesh ohne Internet
- **Sneakernet** — USB-Stick, QR-Code, E-Mail-Anhang (wie Willow's Drop Format)

### Live-Sync vs. Catch-Up

**Live-Sync (beide online):**

```
Peer A erzeugt neuen Log-Eintrag
    → signiert + verschlüsselt
    → sendet an verbundene Peers (Push)
    → Peers wenden an
```

**Catch-Up (nach Offline-Phase):**

```
Peer A verbindet sich mit Peer B
    → tauschen Sequenznummern aus
    → senden fehlende Einträge
    → bei großer Divergenz: RIBLT
```

**Push-Notification (Peer ist offline):**

```
Broker empfängt neuen Eintrag
    → Prüft: ist der Empfänger-Peer online?
    → Wenn nein: Push via UnifiedPush/ntfy
    → Peer wacht auf, verbindet sich, holt fehlende Einträge
```

---

## 6. Nicht-Ziele (für dieses Dokument)

Diese Themen sind wichtig, aber werden separat spezifiziert:

- **Permissions / Gruppen** — Wer darf was? Rollen-Modell, Key Rotation
- **Identity** — BIP39, Ed25519, did:key (bereits in wot-spec/001)
- **Datenmodell** — PersonalDoc-Aufbau, Space-Struktur, Module
- **Discovery** — Wie finden sich Peers? Wie findet man Broker?
- **CRDT-Adapter** — Wie übersetzt Yjs/Automerge in Log-Einträge?

---

## 7. Implementierungs-Roadmap

| Phase | Was | Wie |
|-------|-----|-----|
| **1. Log** | Append-only Logs mit Sequenznummern | Unseren Relay umbauen: statt Message-Queue → Log-Store. Fix für den Sync-Loop. |
| **2. Broker** | Relay + Vault zusammenführen | Ein Service statt zwei. Persistente Logs + Push-Notifications. |
| **3. Kompression** | Sedimentree-Prinzip | Alte Einträge deterministisch zu Chunks komprimieren. Löst Doc-Wachstum. |
| **4. Reconciliation** | RIBLT | Für Reconnect nach langer Offline-Zeit. TypeScript-Implementierung von ORP nutzbar. |
| **5. P2P** | Direktes Sync zwischen Peers | Iroh für NAT Traversal. Selbes Protokoll wie Broker-Sync. |

Jede Phase ist unabhängig deploybar. Phase 1 löst das akute Problem. Phase 2-5 verbessern schrittweise.

---

## 8. Herkunft der Ideen

| Idee | Von wem | Warum |
|------|---------|-------|
| Append-only Logs | Jazz, p2panda | Einfach, CRDT-agnostisch, löst den Loop |
| Deterministische Kompression | Sedimentree (Ink & Switch) | Löst byzantinisches Snapshot-Problem |
| RIBLT | Beelay, ORP (Nik Graf) | Parameterlos, 1.35x Overhead |
| Peer = Peer | p2panda (Shared Nodes), Iroh | Broker ist nur ein Peer der immer online ist |
| Push als Wecker | RFC-0004, NextGraph (Inbox) | User muss nicht die App offen haben |
| Dumme Server | Nostr | Server versteht nichts, Client hat die Intelligenz |
| Kein Federation | NextGraph, Nostr | Client repliziert zu Brokern, kein Inter-Broker-Protokoll |
| Drei-Schichten | Niks Erfahrung (secsync → ORP) | Einzelne Updates → Snapshots → deterministische Kompression |

---

*Dieses Dokument ist die destillierte Essenz aus einem Forschungstag mit 10 Projekt-Analysen, 4 Research Papers, 9 Conference Talks und einem Telefonat mit Nik Graf.*
