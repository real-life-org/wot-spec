# Security Analysis — WoT Spec

*Adversarial review, 2026-04-18*

Eine kritische Analyse der aktuellen Spec aus Angreifer-Perspektive. Die Schwachstellen reichen von implementierungsabhängigen Problemen bis zu fundamentalen Protokoll-Lücken. Eingeteilt nach Schwere und Wahrscheinlichkeit.

## 🔴 Kritische Schwachstellen

### K1. Admin-Key-Kompromittierung = totale Gruppen-Übernahme

**Problem:** Ein einziger Schlüssel kontrolliert alles. Wenn der Private Key des Admins (members[0]) kompromittiert wird, kann der Angreifer:
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

**Problem:** AES-GCM ist **extrem anfällig** gegen Nonce-Reuse. Bei **zwei Nachrichten mit gleicher Nonce und gleichem Key** kann ein Angreifer:
- Klartext-Differenzen berechnen (XOR-Analyse)
- Den Authentifikations-Key (H) wiederherstellen → beliebige Forgeries möglich

**Spec-Lücke:** Die Spec sagt nur "12 Bytes zufällig pro Verschlüsselung". Das klingt sicher, ist aber bei **2^48 Nachrichten** (Birthday Paradox) bereits problematisch — bei einem aktiven Space mit häufigen Updates realistisch.

**Exploit-Szenario:**
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

**Mitigation:**
- Nonce muss deterministisch sein (Counter + Device-ID)
- ODER: Space Key muss automatisch nach N Nachrichten rotieren
- ODER: XChaCha20-Poly1305 statt AES-GCM (24-Byte Nonce, kein Birthday Problem)

---

### K3. Fehlende Feld-Level-Permissions im CRDT

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

**Problem:** JWS erlaubt verschiedene Algorithmen im Header. Eine **klassische Schwachstelle** ist das Akzeptieren von `alg=none` oder algorithmischer Konfusion (z.B. Public Key als HMAC-Secret).

**Spec-Lücke:** Unsere Spec sagt `alg=EdDSA` ist Standard, aber schreibt nicht explizit dass **Verifier nur EdDSA akzeptieren dürfen**.

**Exploit-Szenario:**
```
Ein naive Implementierung liest den JWS-Header, sieht alg=HS256,
und nutzt den Public Key (der öffentlich aus der DID kommt) als HMAC-Secret.
→ Angreifer kann beliebige Nachrichten "signieren"
→ Die Verifikation passt, weil HMAC mit bekanntem "Secret" trivial ist.

Auch möglich: alg=none (keine Signatur)
→ Verifier akzeptiert unsignierte Nachrichten
```

**Mitigation:** Spec muss **normativ** verlangen: Verifier MÜSSEN alg-Feld gegen erlaubte Werte (EdDSA) prüfen und alle anderen ablehnen.

---

## 🟠 Schwere Schwachstellen

### S1. Keine Forward Secrecy bei Inbox-Nachrichten

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

**Problem:** Challenge-Nonces sind 32 Bytes. Wenn ein Gerät eine **kompromittierte/schwache RNG** hat (ältere Android-Versionen, billige IoT-Devices), sind Kollisionen möglich.

**Exploit-Szenario:**
```
Alice hat ein altes Android (schwache RNG beim Systemstart)
Sie erstellt Challenge 1: nonce_A (vorhersagbar)
Später: Challenge 2: nonce_A (reuse!)

Angreifer der Challenge 1 aufgezeichnet hat:
  → hat die signierte Response
  → präsentiert diese als Response auf Challenge 2
  → wird als Alice akzeptiert (Signatur ist gültig)
```

**Spec-Lücke:** Keine Anforderung an RNG-Qualität. Keine Nonce-History-Prüfung.

**Mitigation:** Empfänger MUSS Nonces für mindestens 24h speichern und Wiederholungen ablehnen.

---

### S3. Split-Brain durch Broker-Manipulation

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

**Spec-Lücke:** Keine Detection von fehlenden Nachrichten. Keine End-to-End-Bestätigung dass alle Mitglieder den State sehen.

**Mitigation:** Regelmäßige State-Digests die Mitglieder untereinander austauschen. Wenn Hashes divergieren → Alarm.

---

### S4. Capability-Replay innerhalb der gleichen Generation

**Problem:** Capabilities haben eine `generation`. Aber sie haben **kein `validUntil`**. Ein einmal ausgestellter Capability ist unbegrenzt gültig bis zur nächsten Rotation.

**Exploit-Szenario:**
```
Bob bekommt Capability Gen 3 für doc X.
Bob verlässt den Space (normale Kündigung, keine Entfernung).
Admin rotiert Keys aber nicht — wozu, Bob hat ja gekündigt?

Bob hat die Capability noch, kann weiter auf doc X zugreifen.
→ "Left but never removed" Problem
```

**Spec-Lücke:** Spec unterscheidet nicht zwischen "entfernt" und "ausgetreten". Capabilities haben keine Zeit-Begrenzung.

**Mitigation:** Capabilities MÜSSEN ein `validUntil` haben. Austritte MÜSSEN Key-Rotation triggern.

---

### S5. Silent Key-Compromise via CRDT-Injection

**Problem:** Wer den Space Key hat, kann **beliebige Log-Einträge erzeugen**, auch mit fremder `authorDid`. Die Signatur verhindert das normalerweise — aber **wenn ein Angreifer sowohl den Space Key als auch irgendeinen gültigen Private Key hat**, kann er CRDT-Änderungen als andere User signieren.

**Warte, das geht nicht direkt.** Ed25519-Signaturen schützen. Aber:

**Subtlerer Angriff:** Ein böswilliger Admin könnte den Log **editieren bevor er andere Member verteilt bekommen**. Er sieht einen Log-Eintrag den er nicht mag, verwirft ihn lokal und liefert ihn nicht weiter.

**Spec-Lücke:** Keine Censorship-Detection im Log. Keine End-to-End-Log-Verifikation zwischen nicht-Admin-Peers.

**Mitigation:** Peers sollten direkt syncen können, nicht nur über den Admin/Broker. Bei Divergenz → Alarm.

---

## 🟡 Relevante Schwachstellen

### M1. Timing-Angriffe bei Decryption

**Problem:** Wenn Decryption nicht konstant-zeit implementiert ist, kann ein Angreifer mit vielen Versuchen den Klartext inferieren.

**Abhängigkeit:** Web Crypto API ist in modernen Browsern konstant-zeit. Ältere/Mobile-Implementierungen nicht garantiert.

**Mitigation:** Spec sollte "constant-time crypto required" normativ verlangen.

---

### M2. Metadata-Leak durch Broker

**Problem:** Broker sieht:
- DID-zu-Device-Zuordnung
- Zeit-Pattern der Nutzung
- Nachrichten-Größen
- Verbindungs-Graph (wer kommuniziert mit wem)

**Spec-Status:** Dokumentiert als bekannte Limitation. Aber für manche Anwendungsfälle (z.B. Journalisten unter autoritärem Regime) katastrophal.

**Mitigation:** Tor-Integration als Option. Cover-Traffic. Onion-Routing zwischen Mediators (DIDComm Forward, aktuell nicht in Spec).

---

### M3. Sybil-Resistance-Umgehung

**Problem:** In-Person-Verifikation verhindert einfache Bot-Accounts. Aber nicht:
- Bezahlte "Verifikations-Mühlen" (jemand trifft viele Leute für Geld und erstellt Accounts)
- Kompromittierte Verifizierer (gekaufter Trust-Level)
- Soziale Manipulation

**Spec-Lücke:** Keine Mechanismen zur Detection von anomalen Verifikations-Patterns.

**Mitigation:** Out-of-Band. Community-basierte Governance. Liability-Mechanismen (Sebastians ADR).

---

### M4. Unbegrenzte Attestation-Spam

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

**Problem:** RFC 8785 (JCS) hat Edge Cases bei:
- Unicode-Normalisierung
- Number-Formatting (0.1 vs 1e-1)
- Leere Strings vs. fehlende Felder
- Verschiedene Implementierungen können divergieren

**Spec-Lücke:** Keine Test-Vektoren für JCS-Edge-Cases.

**Exploit-Szenario:**
```
Implementierung A kanonisiert: {"name":"€"} → bestimmte Bytes
Implementierung B kanonisiert: {"name":"€"} → andere Bytes

Signatur von A verifiziert sich nicht gegen Kanonisierung von B.
→ Interop-Break
→ Oder: clever craftet, um eine Signatur gültig in einer, 
  ungültig in anderer Impl zu machen
```

**Mitigation:** Umfangreiche Test-Vektoren, inklusive Unicode-Edge-Cases, in die Spec aufnehmen.

---

### M6. Forgotten-Device Permanent Backdoor

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
1. Capabilities für ihn selbst ausstellen an anderen Spaces wo er Mitglied ist
2. Wait — er kann nur eigene Spaces kontrollieren. Gut.
3. Aber: er kann alle Member entfernen die ihm widersprechen
4. Er kann Space-Metadata übernehmen ("wir heißen jetzt anders, unser Zweck ist...")
5. Er kann Key rotieren — nur er hat den neuen
6. Er kann den alten Key behalten und alles historische sehen

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

### Exploit D: Die "Signaturen-Ersetzung"

**Szenario:** Bug in einer Implementierung akzeptiert `alg=none` oder `alg=HS256`.

**Was passiert:**
1. Angreifer baut ein JWS mit `alg=none` und beliebigem Payload
2. Sendet an naive Implementierung
3. Implementierung sieht "alg=none", verifiziert nicht
4. Akzeptiert den Payload als gültig

**Mitigation:** Spec muss explizit sagen: **only alg=EdDSA is valid, reject everything else**.

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

### Sofort (für Version 1.0)
1. **alg=EdDSA strict enforcement** explizit in 002 spezifizieren
2. **Capability validUntil** als Pflichtfeld einführen
3. **Threshold-Signaturen für destruktive Admin-Aktionen** als Option
4. **Nonce-History** im Challenge-Response-Protokoll

### Mittelfristig
5. **Multi-Admin-Modell** für große Gruppen
6. **Deterministische Nonces** (Counter + DeviceID) statt random
7. **Device-Revokation** und Device-TTL
8. **State-Digests** zwischen Mitgliedern zur Split-Brain-Detection

### Langfristig
9. **Double-Ratchet für Inbox** (Forward Secrecy)
10. **Capability-Chains** (Keyhive-Style) statt soziale Permissions
11. **Anomaly Detection** für Verifikations-Patterns
12. **Tor/Mix-Net Integration** für Broker-Anonymität

## Der ehrliche Stand

Die Spec ist ein **guter erster Wurf** aber nicht Production-Ready für hochsensitive Anwendungen. Für Communities mit bestehender sozialer Kontrolle (Nachbarschaftsnetze, Kooperativen) ist sie ausreichend. Für adversarial-heavy Kontexte (Journalisten, Aktivisten unter Repression) fehlen kritische Schutzmaßnahmen.

Die größten Schwachstellen sind **architektonisch**, nicht kryptographisch:
- Zu mächtiger Admin (Single Point of Failure)
- Fehlende End-to-End-Bestätigung (Broker kann manipulieren)
- Keine Forward Secrecy (zeitliche Kompromittierung)

Die Kryptographie selbst ist solide gewählt (moderne Primitive, Standards). Die Protokoll-Logik hat Lücken.
