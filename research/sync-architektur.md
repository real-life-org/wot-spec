# WoT Sync-Architektur

- **Status:** Entwurf
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-12
- **Grundlage:** Forschungsdokument [sync-alternativen.md](sync-alternativen.md)

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

## 2. Device-Identifikation

### Aktueller Stand: Device-UUIDs (Phase 1)

Für die aktuelle Spec-Version (gemeinsam mit `did:key`) werden Geräte über **zufällige UUIDs** identifiziert, nicht über eigene Schlüsselpaare. Grund: `did:key` kann per Design nur einen einzigen Schlüssel ausdrücken — ein Trust-Anchor-Dokument mit mehreren Device-Keys setzt eine andere DID-Methode voraus (siehe [identitaet-alternativen.md](identitaet-alternativen.md)).

**Das UUID-Modell:**

- Jedes Gerät generiert beim ersten Start eine zufällige UUID v4
- Die UUID wird im lokalen Sync-Log als `deviceId` verwendet (eindeutiger Autor pro Log-Eintrag)
- Die UUID wird im Personal Doc unter `devices` eingetragen (für UI-Anzeige, Device-Deaktivierung als Konvention)
- Alle Signaturen laufen mit dem **Master Key** (aus dem Seed abgeleitet)

**Was damit funktioniert:**

- **Sync-Log-Eindeutigkeit:** UUIDs verhindern Sequenznummern-Konflikte zwischen Geräten desselben Users
- **Double-Spend-Prevention (HMC):** Ein Gutschein "lebt auf Device X123". Der Transfer wird vom Master Key signiert, die UUID lokalisiert den Gutschein. Double-Spend wird verhindert, weil ein Gutschein eine deterministische Owner-UUID hat und jede App-Instanz prüfen kann: "Ist dieser Gutschein jemandem mit UUID X123 zugeordnet? Dann bin ich es nicht, also gehört er mir nicht."
- **Multi-Device-Sync:** Alle Geräte haben den Seed, können lesen und schreiben. Device-UUIDs ordnen Log-Einträge zu.

**Was damit NICHT funktioniert:**

- **Kryptographische Device-Revocation:** Wer den Seed hat, kann jede beliebige UUID generieren und sich als neues Device registrieren. Device-Deaktivierung ist eine Konvention, die nur gegen "ehrliche" Geräte wirkt.
- **Seed-Isolation:** Jedes Gerät hat den vollen Seed. Ein kompromittiertes Gerät bedeutet Kompromittierung der gesamten Identität.
- **Delegierbare Gerätebefugnisse:** Es gibt keine kryptographische Unterscheidung zwischen "primärem Gerät" und "delegiertem Gerät".

### Zukunftsmodell: Echte Device-Keys (Phase 2, gemeinsam mit DID-Migration)

Sobald wir von `did:key` auf eine DID-Methode mit DID-Dokumenten wechseln ([did:peer:4](https://identity.foundation/peer-did-method-spec/) oder [did:webvh](https://identity.foundation/didwebvh/)), werden echte Per-Device-Keys möglich und sinnvoll.

**Hierarchie (zukünftig):**

```
BIP39 Seed (12 Wörter)
  → HKDF("wot/identity/ed25519/v1") → Master Key (= DID)
  → HKDF("wot/encryption/v1")       → Master Encryption Key (X25519)
  → Zufällig generiert               → Device Key A (Handy)
  → Zufällig generiert               → Device Key B (Laptop)
```

Das DID-Dokument enthält alle autorisierten Device-Keys:

```json
{
  "id": "did:peer:4z...",
  "verificationMethod": [
    { "id": "#master", "publicKeyMultibase": "z6Mk...master" },
    { "id": "#device-phone", "publicKeyMultibase": "z6Mk...phone" },
    { "id": "#device-laptop", "publicKeyMultibase": "z6Mk...laptop" }
  ],
  "authentication": ["#device-phone", "#device-laptop"],
  "capabilityInvocation": ["#master"]
}
```

**Vorteile des Zukunftsmodells:**

| Aspekt | UUID (jetzt) | Device-Key (Zukunft) |
|---|---|---|
| Device-Identifikation | Konvention (UUID) | Kryptographisch (Public Key) |
| Device-Revocation | Nicht wirksam gegen Seed-Besitzer | Kryptographisch bedeutungsvoll (Key aus DID-Dokument entfernen) |
| Seed-Verbreitung | Auf jedem Gerät | Nur auf dem primären Gerät |
| Gerätekompromittierung | Kompromittiert alle Geräte | Begrenzbar auf das eine Gerät |
| Onboarding eines zweiten Geräts | Seed eingeben | QR-Code-Austausch, Master signiert neuen Device Key |
| Forward Secrecy pro Gerät | Nicht möglich | Teilweise möglich |

**Wer würde dann was signieren?**

| Aktion | Signiert mit | Warum |
|--------|-------------|-------|
| Attestation | Master Key | Identity-Level — "Ich, Alice" |
| Verification | Master Key | Identity-Level — persönliche Aussage |
| Log-Eintrag (CRDT-Update) | Device Key | Sync-Level — welches Gerät hat das geschrieben? |
| Delegation (neuer Device-Key) | Master Key | Autorisierung eines neuen Geräts |
| Transaktion (Gutschein ausgeben) | Device Key | Double-Spend-Prevention + Gerätebindung |

**Login-Flows im Zukunftsmodell:**

Erstes Gerät (Onboarding):

```
1. Seed eingeben oder generieren
2. Master Key ableiten
3. Zufälligen Device Key generieren
4. Master Key signiert Delegation an Device Key
5. DID-Dokument erstellen, mit Master + Device Key
```

Neues Gerät hinzufügen (mit Master-Gerät verfügbar):

```
1. Neues Gerät: App öffnen → "QR-Code scannen"
2. Neues Gerät: Generiert zufälligen Device Key, zeigt QR-Code
3. Master-Gerät: Scannt QR → "Laptop möchte Zugang" → bestätigen
4. Master-Gerät: Signiert Delegation mit Master Key
5. Master-Gerät: Aktualisiert DID-Dokument, sendet Delegation + Daten
6. Neues Gerät: Hat Device Key + Delegation + Daten, ohne den Seed zu kennen
```

Vorteil: Der Seed verlässt das Master-Gerät nicht.

### Zusammenfassung der Entscheidung

Die aktuelle Spec-Version verwendet **UUIDs**, weil:

1. Es ausreichend ist für Sync-Log-Eindeutigkeit und HMC-Double-Spend-Prevention
2. `did:key` keine Möglichkeit bietet, mehrere Keys in einer DID auszudrücken
3. Die zusätzliche Komplexität (DID-Dokumente, Delegations-Protokoll, Multi-Key-Management) ohne die DID-Methoden-Migration nicht lohnt

Der Wechsel zu Device-Keys erfolgt **gemeinsam mit der DID-Migration** als Phase 2. Siehe [identity-migration.md](identity-migration.md) und [identitaet-alternativen.md](identitaet-alternativen.md) für den geplanten Pfad.

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
