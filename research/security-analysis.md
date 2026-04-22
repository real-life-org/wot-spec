# Security Analysis — WoT Spec

*Adversarial review, ursprünglich 2026-04-18. Tabellenkopf und Fix-Markierungen aktualisiert 2026-04-19.*

Eine kritische Analyse der aktuellen Spec aus Angreifer-Perspektive. Die Schwachstellen reichen von implementierungsabhängigen Problemen bis zu fundamentalen Protokoll-Lücken. Eingeteilt nach Schwere und Wahrscheinlichkeit.

Aus Transparenzgründen bleibt dieses Dokument vollständig — auch bereits behobene Schwachstellen bleiben dokumentiert, damit sichtbar ist was wir gefunden und wie wir reagiert haben.

## Status-Übersicht

### ✅ Bereits behoben

| ID | Schwachstelle | Schwere | Behoben am | Fix |
|----|---------------|---------|------------|-----|
| [K2](#k2-nonce-reuse-bei-aes-256-gcm--katastrophaler-schlüsselverlust) | Nonce-Reuse bei AES-256-GCM | 🔴 Kritisch | 2026-04-18 | Deterministische Nonce aus `(deviceId, seq)` — [Sync 005](../02-wot-sync/005-verschluesselung.md) |
| [K4](#k4-jws-alg-konfusion) | JWS `alg`-Konfusion | 🔴 Kritisch | 2026-04-18 | Normativer `alg=EdDSA`-Strict-Check — [Core 002](../01-wot-core/002-signaturen-und-verifikation.md#algorithmus-validierung-muss) |
| [S2](#s2-nonce-reuse-attacke-bei-challenge-response) | Nonce-Reuse bei Challenge-Response | 🟠 Schwer | 2026-04-18 | Nonce-History (24h) im Broker — [Sync 007](../02-wot-sync/007-transport-und-broker.md) |
| [S4](#s4-capability-replay-innerhalb-der-gleichen-generation) | Capability-Replay ohne Ablauf | 🟠 Schwer | 2026-04-18 | `validUntil` als Pflichtfeld — [Sync 007](../02-wot-sync/007-transport-und-broker.md#capability-format) |
| [M1](#m1-timing-angriffe-bei-decryption) | Timing-Angriffe bei Decryption | 🟡 Mittel | 2026-04-19 | Constant-Time-Anforderung (MUSS) — [Sync 005](../02-wot-sync/005-verschluesselung.md#konstante-laufzeit-constant-time--muss) |
| [M5](#m5-jcs-canonicalization-edge-cases) | JCS-Canonicalization Edge Cases | 🟡 Mittel | 2026-04-18 | Test-Vektoren (Unicode, Zahlen) — [Core 002](../01-wot-core/002-signaturen-und-verifikation.md) |
| [S3](#s3-split-brain-durch-broker-manipulation) | Split-Brain durch Broker (80-90%) | 🟠 Schwer | 2026-04-19 | Multi-Source-Sync + Heads-Vergleich — [Sync 006](../02-wot-sync/006-sync-protokoll.md#censorship--und-split-brain-detection) |
| [S5](#s5-silent-log-censorship-durch-admin) | Silent Log-Censorship (80-90%) | 🟠 Schwer | 2026-04-19 | Identisch mit S3-Fix (Multi-Source-Sync) — [Sync 006](../02-wot-sync/006-sync-protokoll.md#censorship--und-split-brain-detection) |

### ⏳ Noch offen

| ID | Schwachstelle | Schwere | Geplant für | Fix-Doku |
|----|---------------|---------|-------------|----------|
| [K1](#k1-admin-key-kompromittierung--totale-gruppen-übernahme) | Admin-Key-Kompromittierung | 🔴 Kritisch | v1.2 | [security-fixes.md](security-fixes.md#fix-k1-multi-admin--threshold-signatures) |
| [K3](#k3-fehlende-feld-level-permissions-im-crdt) | Fehlende Feld-Level-Permissions | 🔴 Kritisch | v1.2 | [security-fixes.md](security-fixes.md#fix-k3-admin-only-felder-für-space-metadata) |
| [S1](#s1-keine-forward-secrecy-bei-inbox-nachrichten) | Keine Forward Secrecy | 🟠 Schwer | v2.0 | [security-fixes.md](security-fixes.md#fix-s1-forward-secrecy-via-double-ratchet) |
| [M2](#m2-metadata-leak-durch-broker) | Metadata-Leak | 🟡 Mittel | v2.0 | Forward/Routing (DIDComm) |
| [M3](#m3-sybil-resistance-umgehung) | Sybil-Resistance-Umgehung | 🟡 Mittel | Forschung | Community-Governance, Liability-ADR |
| [M4](#m4-unbegrenzte-attestation-spam) | Attestation-Spam | 🟡 Mittel | v1.1 | [security-fixes.md](security-fixes.md#fix-m4-attestation-rate-limiting) |
| [M6](#m6-forgotten-device-permanent-backdoor) | Forgotten-Device | 🟡 Mittel | v1.1 | [security-fixes.md](security-fixes.md#fix-m6-device-revokation-und-ttl) |

---

## 🔴 Kritische Schwachstellen

### K1. Admin-Key-Kompromittierung = totale Gruppen-Übernahme

**Status:** ⏳ Offen — geplant für v1.2

**Problem:** Ein einziger Schlüssel kontrolliert alles. Wenn der Admin Key eines Space-Admins kompromittiert wird, kann der Angreifer:

- Alle Mitglieder entfernen
- Sich selbst als neue Mitglieder "hinzufügen"
- Beliebige Capabilities ausstellen
- Den Space faktisch übernehmen

**Spec-Lücke:**

- Kein Multi-Signatur-Modell für kritische Aktionen
- Keine Cooldown-Periode bei Admin-Aktionen
- Keine Möglichkeit einen kompromittierten Admin-Key zu widerrufen

**Exploit-Szenario:**

```
Angreifer bekommt Zugriff auf Alices Gerät (gestohlen, kompromittiert)
  → extrahiert Private Key aus Keystore
  → sendet vom eigenen Gerät: "Entferne Bob, Carol, Dave"
  → rotiert Space Key (nur er hat den neuen)
  → Alle anderen Mitglieder sind ausgesperrt
  → Angreifer hat die Daten, niemand kann ihn aufhalten
```

**Mitigation:** Threshold-Signaturen für destruktive Aktionen (M-von-N Admins müssen zustimmen). Alternativ: Cooldown-Period vor Mitglieder-Entfernung.

---

### K2. Nonce-Reuse bei AES-256-GCM = katastrophaler Schlüsselverlust

**Status:** ✅ Behoben 2026-04-18 — deterministische Nonce aus `SHA-256(deviceId || "|" || seq)`. Da `(deviceId, seq)` per Spec eindeutig sind, sind Kollisionen ausgeschlossen.

**Problem:** AES-GCM ist **extrem anfällig** gegen Nonce-Reuse. Bei **zwei Nachrichten mit gleicher Nonce und gleichem Key** kann ein Angreifer:

- Klartext-Differenzen berechnen (XOR-Analyse)
- Den Authentifikations-Key (H) wiederherstellen → beliebige Forgeries möglich

**Spec-Lücke (vor Fix):** Die Spec sagte nur "12 Bytes zufällig pro Verschlüsselung". Das klang sicher, war aber bei **2^48 Nachrichten** (Birthday Paradox) bereits problematisch — bei einem aktiven Space mit häufigen Updates realistisch.

**Exploit-Szenario (vor Fix):**

```
Ein Space existiert seit 3 Jahren, hat viele Mitglieder.
Der Space Key wird nicht oft rotiert (nur bei Entfernungen).
Mit schwachem RNG (manche Mobile-Implementierungen) oder
nach 2^32 Nachrichten (~4 Milliarden) wird eine Nonce-Kollision
statistisch signifikant.

→ Angreifer sammelt Ciphertexts, findet Kollision
→ Kann Space-Daten entschlüsseln
→ Kann beliebige Forgeries in den Log einschleusen
```

**Fix:** Nonce wird deterministisch aus `(deviceId, seq)` abgeleitet — Werten die ohnehin per Log-Struktur eindeutig sind. Kein neuer State, kein RNG-Risiko.

---

### K3. Fehlende Feld-Level-Permissions im CRDT

**Status:** ⏳ Offen — geplant für v1.2

**Problem:** Die Spec ist explizit darin: "Jedes Mitglied mit dem Space Key kann beliebige Daten schreiben." Das ist gewollt — aber es ermöglicht **internen Missbrauch**.

**Exploit-Szenario:**

```
Ein Space hat Metadata wie { name, description, modules, settings }.
Ein Member (nicht Admin) will Chaos stiften:
  → schreibt CRDT-Update: metadata.name = "PWNED"
  → schreibt: modules = []
  → schreibt: description = "rekrutiere für Sekte XY"

Andere Mitglieder sehen diese Änderungen. Die CRDT akzeptiert sie.
Der Admin kann den Täter im Log identifizieren und entfernen,
aber der Schaden ist schon da.
```

**Spec-Status:** Als "bewusste Entscheidung" markiert. Aber: **in realen Communities ist das gefährlich**. Ein disgruntled Ex-Member kann noch Schaden anrichten bevor er entfernt wird.

**Mitigation:** Mindestens Admin-only Felder für Space-Metadata.

---

### K4. JWS `alg`-Konfusion

**Status:** ✅ Behoben 2026-04-18 — Spec verlangt normativ `alg=EdDSA` und MUSS alle anderen Werte ablehnen.

**Problem:** JWS erlaubt verschiedene Algorithmen im Header. Eine **klassische Schwachstelle** ist das Akzeptieren von `alg=none` oder algorithmischer Konfusion (z.B. Public Key als HMAC-Secret).

**Spec-Lücke (vor Fix):** Unsere Spec sagte `alg=EdDSA` ist Standard, aber schrieb nicht explizit dass **Verifier nur EdDSA akzeptieren dürfen**.

**Exploit-Szenario (vor Fix):**

```
Ein naive Implementierung liest den JWS-Header, sieht alg=HS256,
und nutzt den Public Key (der öffentlich aus der DID kommt) als HMAC-Secret.
→ Angreifer kann beliebige Nachrichten "signieren"
→ Die Verifikation passt, weil HMAC mit bekanntem "Secret" trivial ist.

Auch möglich: alg=none (keine Signatur)
→ Verifier akzeptiert unsignierte Nachrichten
```

**Fix:** Core 002 verlangt jetzt normativ (MUSS): Verifier prüfen das `alg`-Feld strikt gegen die erlaubten Werte (nur `EdDSA`). Abweichende Werte — inklusive `none`, `HS256`, `RS256` — MÜSSEN abgelehnt werden.

---

## 🟠 Schwere Schwachstellen

### S1. Keine Forward Secrecy bei Inbox-Nachrichten

**Status:** ⏳ Offen — geplant für v2.0

**Problem:** Authcrypt nutzt den **statischen Sender-Key** für ECDH. Wenn der Sender-Key später kompromittiert wird, können alle historischen Nachrichten entschlüsselt werden.

**Exploit-Szenario:**

```
Alice sendet an Bob: "Hier ist der Space Key für unseren geheimen Space"
Monate später wird Alice's Private Key kompromittiert.
Angreifer hat aufgezeichnete Nachrichten (vom Broker, vom Netzwerk-Dump).
→ Kann jahrelang zurück entschlüsseln
```

**Spec-Status:** Als "keine Forward Secrecy" erwähnt, aber Tragweite unterschätzt. Besonders kritisch für Key-Rotation-Nachrichten die langlebige Space Keys enthalten.

**Mitigation:** Double-Ratchet-Protokoll (Signal-Style) für hochsensitive Nachrichten. Oder: regelmäßige Key-Rotation des Sender-X25519-Keys.

---

### S2. Nonce-Reuse-Attacke bei Challenge-Response

**Status:** ✅ Behoben 2026-04-18 — Broker speichert Challenge-Nonces für mindestens 24h und weist Wiederholungen ab.

**Problem:** Challenge-Nonces sind 32 Bytes. Wenn ein Gerät eine **kompromittierte/schwache RNG** hat (ältere Android-Versionen, billige IoT-Devices), sind Kollisionen möglich.

**Exploit-Szenario (vor Fix):**

```
Alice hat ein altes Android (schwache RNG beim Systemstart)
Sie erstellt Challenge 1: nonce_A (vorhersagbar)
Später: Challenge 2: nonce_A (reuse!)

Angreifer der Challenge 1 aufgezeichnet hat:
  → hat die signierte Response
  → präsentiert diese als Response auf Challenge 2
  → wird als Alice akzeptiert (Signatur ist gültig)
```

**Spec-Lücke (vor Fix):** Keine Nonce-History-Prüfung.

**Fix:** Sync 007 verlangt: der Empfänger MUSS Nonces für mindestens 24h speichern und Wiederholungen ablehnen. Das entschärft schwache RNGs als Bedrohungsquelle.

---

### S3. Split-Brain durch Broker-Manipulation

**Status:** ✅ Zu 80-90% behoben 2026-04-19 — Multi-Source-Sync + Heads-Vergleich in [Sync 006](../02-wot-sync/006-sync-protokoll.md#censorship--und-split-brain-detection). Strukturelle Grenzen (Single-Broker-Communities ohne P2P-Option) bleiben unvermeidbar bestehen.

**Problem:** Der Broker kann Nachrichten selektiv zustellen. Wenn er eine **Mitglieder-Entfernung** nur an einige Clients zustellt, entstehen inkonsistente Sichten.

**Exploit-Szenario:**

```
Admin entfernt Bob aus dem Space.
Broker ist korrumpiert (oder staatlich gezwungen).
Broker leitet member-update Nachricht an Alice und Carol weiter,
aber NICHT an Dave und Eve.

Resultat:
- Alice, Carol: sehen Bob als entfernt
- Dave, Eve: sehen Bob noch als Mitglied  
- Bob: weiß nicht dass er entfernt wurde
- CRDT-State divergiert still
```

**Spec-Lücke (vor Fix):** Keine Detection von fehlenden Nachrichten. Keine End-to-End-Bestätigung dass alle Mitglieder den State sehen.

**Fix:** Sync 006 empfiehlt Multi-Source-Sync — Clients SOLLEN regelmäßig gegen mehrere Broker oder direkte P2P-Peers syncen und die zurückgegebenen Heads vergleichen. Divergenz wird dem User als Status-Indikator sichtbar gemacht, mit Handlungsoptionen (alternativer Broker, P2P-Sync, ignorieren).

**Strukturelle Grenze:** Communities mit einem einzigen Broker und ohne P2P-Kapazität haben keinen unabhängigen Vergleichspunkt — auch ein formales Digest-Protokoll könnte das nicht lösen. Das ist ein Architektur- und Betriebsthema, nicht ein Protokoll-Defizit.

---

### S4. Capability-Replay innerhalb der gleichen Generation

**Status:** ✅ Behoben 2026-04-18 — Capabilities haben jetzt ein Pflichtfeld `validUntil`.

**Problem:** Capabilities hatten eine `generation`, aber **kein `validUntil`**. Ein einmal ausgestellter Capability war unbegrenzt gültig bis zur nächsten Rotation.

**Exploit-Szenario (vor Fix):**

```
Bob bekommt Capability Gen 3 für doc X.
Bob verlässt den Space (normale Kündigung, keine Entfernung).
Admin rotiert Keys aber nicht — wozu, Bob hat ja gekündigt?

Bob hat die Capability noch, kann weiter auf doc X zugreifen.
→ "Left but never removed" Problem
```

**Spec-Lücke (vor Fix):** Spec unterschied nicht zwischen "entfernt" und "ausgetreten". Capabilities hatten keine Zeit-Begrenzung.

**Fix:** Sync 007 verlangt jetzt `validUntil` als Pflichtfeld. Empfohlene Dauer: 6 Monate (normal), 1 Monat (hochsensitiv), 1 Jahr (persönliches Doc). Der Admin erneuert Capabilities für aktive Members rechtzeitig; inaktive Members verlieren den Zugriff automatisch.

---

### S5. Silent Log-Censorship durch Admin

**Status:** ✅ Zu 80-90% behoben 2026-04-19 — derselbe Multi-Source-Sync-Mechanismus wie bei S3 deckt diesen Angriff ab. Siehe [Sync 006](../02-wot-sync/006-sync-protokoll.md#censorship--und-split-brain-detection).

**Problem:** Ein böswilliger Admin könnte den Log **editieren bevor andere Member ihn verteilt bekommen**. Er sieht einen Log-Eintrag den er nicht mag, verwirft ihn lokal und liefert ihn nicht weiter.

**Spec-Lücke (vor Fix):** Keine Censorship-Detection im Log. Keine End-to-End-Log-Verifikation zwischen nicht-Admin-Peers.

**Fix:** Wenn Mitglieder außerhalb des Admin-Kanals syncen können (zweiter Broker, P2P), zeigt der Heads-Vergleich die unterdrückten Einträge. Sub-Spezialfall von S3 — dieselbe Lösung.

**Strukturelle Grenze:** Wenn alle Sync-Pfade durch den malicious Admin laufen, gibt es keinen unabhängigen Vergleichspunkt. Das ist nicht protokollarisch lösbar.

---

## 🟡 Relevante Schwachstellen

### M1. Timing-Angriffe bei Decryption

**Status:** ✅ Behoben 2026-04-19 — normative Constant-Time-Anforderung in [Sync 005](../02-wot-sync/005-verschluesselung.md#konstante-laufzeit-constant-time--muss).

**Problem:** Wenn Decryption nicht konstant-zeit implementiert ist, kann ein Angreifer mit vielen Versuchen den Klartext inferieren.

**Abhängigkeit:** Web Crypto API ist in modernen Browsern konstant-zeit. Ältere/Mobile-Implementierungen oder Eigenimplementierungen in JavaScript nicht garantiert.

**Fix:** Sync 005 verlangt jetzt normativ (MUSS): alle Krypto-Operationen (AES-GCM Tag-Verifikation, X25519 Scalar Multiplication, HKDF/HMAC-Vergleich) laufen in konstanter Zeit. Implementierungen MÜSSEN die Web Crypto API oder eine äquivalent auditierte native Bibliothek verwenden — kein JavaScript-Eigenbau von AES, X25519, HKDF oder HMAC.

---

### M2. Metadata-Leak durch Broker

**Status:** ⏳ Offen — geplant für v2.0

**Problem:** Broker sieht:

- DID-zu-Device-Zuordnung
- Zeit-Pattern der Nutzung
- Nachrichten-Größen
- Verbindungs-Graph (wer kommuniziert mit wem)

**Spec-Status:** Dokumentiert als bekannte Limitation. Aber für manche Anwendungsfälle (z.B. Journalisten unter autoritärem Regime) katastrophal.

**Mitigation:** Tor-Integration als Option. Cover-Traffic. Onion-Routing zwischen Mediators (DIDComm Forward, geplant für v2.0).

---

### M3. Sybil-Resistance-Umgehung

**Status:** ⏳ Offen — Forschungsthema

**Problem:** In-Person-Verifikation verhindert einfache Bot-Accounts. Aber nicht:

- Bezahlte "Verifikations-Mühlen" (jemand trifft viele Leute für Geld und erstellt Accounts)
- Kompromittierte Verifizierer (gekaufter Trust-Level)
- Soziale Manipulation

**Spec-Lücke:** Keine Mechanismen zur Detection von anomalen Verifikations-Patterns.

**Mitigation:** Out-of-Band. Community-basierte Governance. Liability-Mechanismen (Sebastians ADR).

---

### M4. Unbegrenzte Attestation-Spam

**Status:** ⏳ Offen — geplant für v1.1

**Problem:** Jeder kann beliebig viele Attestations für beliebige Subjects erzeugen. Im Empfängerprinzip landen sie in der Inbox.

**Exploit-Szenario:**

```
Angreifer erstellt 10.000 Attestations für Alice:
"Alice ist ein Dieb"
"Alice ist pädophil"
...

Alice muss entscheiden ob sie akzeptiert. Aber die Metadata
(Absender-DIDs, Zeitstempel, Inhalte) werden vom Broker
verarbeitet, an Alice's Geräte weitergeleitet.

Resultat: 
- Bandbreiten-Verbrauch
- Storage auf Alice's Geräten  
- Psychologische Last für Alice
```

**Mitigation:** Rate-Limiting pro Sender-DID. Auto-Reject von Attestations von unbekannten DIDs.

---

### M5. JCS-Canonicalization Edge Cases

**Status:** ✅ Behoben 2026-04-18 — Spec enthält jetzt Test-Vektoren für Unicode-Normalisierung und Zahlen-Formatierung.

**Problem:** RFC 8785 (JCS) hat Edge Cases bei:

- Unicode-Normalisierung
- Number-Formatting (0.1 vs 1e-1)
- Leere Strings vs. fehlende Felder
- Verschiedene Implementierungen können divergieren

**Spec-Lücke (vor Fix):** Keine Test-Vektoren für JCS-Edge-Cases.

**Exploit-Szenario (vor Fix):**

```
Implementierung A kanonisiert: {"name":"€"} → bestimmte Bytes
Implementierung B kanonisiert: {"name":"€"} → andere Bytes

Signatur von A verifiziert sich nicht gegen Kanonisierung von B.
→ Interop-Break
→ Oder: clever craftet, um eine Signatur gültig in einer,
  ungültig in anderer Impl zu machen
```

**Fix:** Core 002 enthält jetzt Test-Vektoren mit Unicode-Edge-Cases, Zahlen-Formatierung und Null-/Leer-Feldern. Implementierungen MÜSSEN gegen diese Vektoren testen.

---

### M6. Forgotten-Device Permanent Backdoor

**Status:** ⏳ Offen — geplant für v1.1

**Problem:** Ein Device-Key lebt unbegrenzt. Wenn Alice ein Gerät hat das sie nicht mehr nutzt (aber nicht offiziell abgemeldet hat), und jemand Zugriff darauf bekommt (Diebstahl, Verkauf, Müll), kann dieser als Alice agieren — **für immer**.

**Spec-Lücke:** Device-Revokation ist nicht spezifiziert.

**Mitigation:** Device-Enrollment-Limits, regelmäßige Device-Re-Auth. Oder: Device-Keys haben TTL.

---

## 🟢 Kleinere Issues

### L1. Keine DoS-Schutz am Broker

Spec spezifiziert kein Rate-Limiting. Authentifizierte Peers können Broker flooden.

### L2. Endlose Inbox-Speicherung

"Delete after all devices ACK" — wenn ein Device nie ACK sendet, wird Speicher nie freigegeben.

### L3. Keine Key-Rotation für Identitäts-Keys

BIP39-Seed ist forever. Keine Spec für Identitäts-Migration (außer im Research-Dokument).

### L4. Keine Audit-Logs für Admin-Aktionen

Admin kann entfernen, aber kein Log zeigt "warum", nur "von wem".

### L5. Profile-Service als Single Point of Failure

Wenn der Profile-Service manipuliert wird, können falsche Broker-URLs oder Keys verteilt werden. Kein Trust-Anchor für Profile-Service selbst.

---

## Konkrete Exploits

### Exploit A: Der "Dormant Key"-Angriff

**Szenario:** Alice ist in einem wichtigen Space. Sie lässt ihr altes Smartphone in der Schublade liegen. Der Dieb erreicht sie nicht, das Telefon liegt dort.

Ein Jahr später wird die Wohnung eingebrochen. Das Telefon wird mitgenommen. Forensik bricht den Keystore (ältere Android-Version). Der Angreifer hat Alice's Keys.

**Was passiert:**

1. Angreifer meldet sich beim Broker an (DID+deviceId)
2. Broker prüft Challenge-Response — gültig (der Key ist ja Alices)
3. Angreifer schreibt CRDT-Updates mit authorDid=Alice
4. Andere Members sehen "Alice hat das geschrieben"

**Warum Spec nicht schützt:**

- Keine Device-Revokation
- Keine End-of-Life für Keys
- Keine anomaly detection für Device-Aktivität

---

### Exploit B: Der "Malicious Admin Pivot"

**Szenario:** Admin einer großen Community-Gruppe wird sozial korrumpiert (Geld, Erpressung, ideologische Umkehrung).

**Was er tun kann:**

1. Alle Member entfernen die ihm widersprechen
2. Space-Metadata übernehmen ("wir heißen jetzt anders, unser Zweck ist...")
3. Key rotieren — nur er hat den neuen
4. Den alten Key behalten und alles historische sehen

**Mitigation-Lücke:** Admin hat zu viel Macht. Keine Balance.

---

### Exploit C: Der "Broker Censor"-Angriff

**Szenario:** Staat zwingt Broker-Betreiber zur Kooperation. Oder: böser Ex-Member der einen Broker betreibt.

**Was er tun kann:**

1. Nachrichten an bestimmte DIDs nicht zustellen
2. Push-Notifications an bestimmte Devices nicht senden
3. Capabilities selektiv prüfen (einige ablehnen, andere akzeptieren)
4. Bei Key-Rotation: neuen Key an einige Mitglieder nicht zustellen → Isolation

**Warum Spec nicht schützt:**

- Keine End-to-End-Zustellbestätigung zwischen Mitgliedern
- Clients vertrauen dass Broker alle Nachrichten weiterleitet
- Keine Redundanz zwischen mehreren Brokern bei Key-Rotation

---

### Exploit D: Die "Signaturen-Ersetzung" (behoben)

**Status:** ✅ Behoben 2026-04-18 (siehe K4).

**Szenario:** Bug in einer Implementierung akzeptiert `alg=none` oder `alg=HS256`.

**Was passierte:**

1. Angreifer baut ein JWS mit `alg=none` und beliebigem Payload
2. Sendet an naive Implementierung
3. Implementierung sieht "alg=none", verifiziert nicht
4. Akzeptiert den Payload als gültig

**Fix:** Core 002 verlangt normativ (MUSS): nur `alg=EdDSA` wird akzeptiert, alle anderen Werte — inklusive `none` — MÜSSEN abgelehnt werden.

---

### Exploit E: Das "Time-Travel-Paradox"

**Szenario:** Zwei Geräte von Alice, beide offline.

Alice (Laptop): erstellt Log-Eintrag seq=42 für docId=X
Alice (Handy): erstellt Log-Eintrag seq=42 für docId=X (auch, separat)

**Problem:** Gleiche deviceId? Nein, verschiedene. Also seq eindeutig pro deviceId. Gut.

Aber: beide signieren als Alice. Beide sind gültig. Beide werden in den Log gemerged. Der CRDT muss entscheiden welcher gewinnt.

**Wenn die beiden Einträge widersprüchlich sind** (z.B. "Admin entfernt Bob" vs "Admin fügt Bob hinzu"), dann ist das Verhalten **undefiniert**.

**Spec-Lücke:** Kein Konflikt-Auflösungs-Mechanismus für widersprüchliche Admin-Aktionen.

---

## Zusammenfassung der Empfehlungen

### Sofort — für Version 1.0 (erledigt 2026-04-18 / 2026-04-19)

1. ✅ **alg=EdDSA strict enforcement** explizit in 002 spezifizieren (K4)
2. ✅ **Capability validUntil** als Pflichtfeld einführen (S4)
3. ✅ **Nonce-History** im Challenge-Response-Protokoll (S2)
4. ✅ **Deterministische Nonces** aus `(deviceId, seq)` (K2)
5. ✅ **JCS-Test-Vektoren** für Unicode-Edge-Cases (M5)
6. ✅ **Constant-Time Crypto** normativ verlangen (M1)
7. ✅ **Multi-Source-Sync** für Censorship-Detection (S3, S5 — 80-90%-Lösung)

### Mittelfristig — v1.1 / v1.2

8. ⏳ **Multi-Admin-Modell** für große Gruppen (K1)
9. ⏳ **Admin-only Space-Metadata** (K3)
10. ⏳ **Device-Revokation** und Device-TTL (M6)
11. ⏳ **Rate-Limiting** für Attestations (M4)

### Langfristig — v2.0+

12. ⏳ **Double-Ratchet für Inbox** (Forward Secrecy, S1)
13. ⏳ **Forward/Routing** für Broker-Anonymität (M2)
14. ⏳ **Capability-Chains** (Keyhive-Style) statt soziale Permissions
15. ⏳ **Anomaly Detection** für Verifikations-Patterns (M3)

## Der ehrliche Stand

Die Spec ist ein **guter Wurf** aber nicht Production-Ready für hochsensitive Anwendungen. Für Communities mit bestehender sozialer Kontrolle (Nachbarschaftsnetze, Kooperativen) ist sie ausreichend. Für adversarial-heavy Kontexte (Journalisten, Aktivisten unter Repression) fehlen kritische Schutzmaßnahmen.

Die am 18.04.2026 behobenen Quick Wins schließen die **implementierungsnahen** Lücken — kryptographische Fehler, die bei einer nachlässigen Umsetzung zu katastrophalen Kompromittierungen geführt hätten (K2, K4, S2, S4, M5). Diese Fixes waren billig und haben das Protokoll auf ein solides Fundament gestellt.

Die größten verbleibenden Schwachstellen sind **architektonisch**, nicht kryptographisch:

- Zu mächtiger Admin (Single Point of Failure) — K1, K3
- Fehlende End-to-End-Bestätigung (Broker kann manipulieren) — S3, S5
- Keine Forward Secrecy (zeitliche Kompromittierung) — S1

Die Kryptographie selbst ist solide gewählt (moderne Primitive, Standards). Die Protokoll-Logik hat Lücken — die meisten in [security-fixes.md](security-fixes.md) mit Aufwand und Trade-offs adressiert.
