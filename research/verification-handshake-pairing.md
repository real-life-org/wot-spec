# Verification-Handshake & Pairing — Design-Konzept

- **Status:** Konzept / non-normativ (Denkstand, keine Spec-Entscheidung)
- **Datum:** 2026-06-14
- **Kontext:** Entstanden aus der Marker-Frage für `/p/{did}/v` vs `/p/{did}/a` (wot-spec#100/#34, web-of-trust#101/#102). Hält die Diskussion über das ehrliche Verifikationsmodell und Alternativen zum QR-Handshake fest, damit die konkreten Spec-Fragen separat geklärt werden können.
- **Beteiligt:** Anton, Timo (NFC-Wearable-Vision), Claude

## 1. Das ehrliche Verifikationsmodell

**Kern: Eine Verifikation beweist eine frische Live-Mutual-Interaktion zweier Keys zu einem Zeitpunkt — NICHT eine physische Begegnung.**

Physische Anwesenheit ist in Software kryptographisch nicht beweisbar. Jeder eingebettete Beweis reduziert sich auf „diese beiden Keys haben einen Live-Austausch gemacht"; zwei willige Parteien können das remote nachstellen. Das „in-person" ruht allein auf der Air-Gap-Annahme des Bootstrap-Kanals (z.B. Kamera↔Bildschirm), nicht auf Krypto. (Distance-Bounding-/Relay-Problem, ohne Spezial-Hardware ungelöst.)

### Beweis-Artefakt: co-signiertes Transkript

Statt einseitiger, nur-empfänger-prüfbarer Nonce → ein **beidseitig co-signiertes Transkript**, eingebettet als `evidence` in die Verification-VC, dadurch self-contained und drittprüfbar.

Geteiltes Transkript (JCS-kanonisiert, beide signieren exakt dies):

```json
{
  "context": "wot/verification/mutual/v1",
  "parties": ["did:key:...A", "did:key:...B"],
  "nonces": { "did:key:...A": "<nA b64url>", "did:key:...B": "<nB b64url>" },
  "created_time": 1776765600
}
```

Beweis-Objekt = Transkript + zwei Detached-Signaturen (`sigA` via `didA#sig-0`, `sigB` via `didB#sig-0`). Eingebettet im VC-Standardfeld `evidence`.

Drittprüfung: beide Signaturen über `JCS(transcript)` verifizieren, `parties == {issuer, subject}`, Nonces wohlgeformt/verschieden, `created_time` plausibel → „beide Keys haben ein frisches Transkript co-signiert".

### Sicherheitseigenschaften (Claims / Non-Claims)

**Garantiert:**
- Key-Substitution-MITM verhindert (Transkript bindet beide DIDs + Nonces).
- Einseitige Fälschung verhindert (keine „Verifikation von B" ohne Bs Signatur).
- Replay/Rückdatierung verhindert (frische beidseitige Nonces + `created_time`).
- Drittprüfbarkeit (Beweis self-contained, kein Geheimwissen des Original-Empfängers nötig).

**Ausdrücklich NICHT garantiert:**
- Physische Anwesenheit (in Software unbeweisbar; willige Parteien co-signieren remote).
- Relay / Mafia-Fraud / Proximity (gültige Nachrichten relayen ist für Krypto unsichtbar; enge Zeitfenster heben die Latte, schließen sie nicht).
- Sybil-Resistenz (Angreifer mit beiden Keys erzeugt gültige Transkripte gratis).

**Sybil und Begegnungs-Vertrauen leben eine Ebene höher — im Graphen (HMC): Trust fließt von echten, bereits vertrauten Knoten; Fake-Cluster bekommen diesen Zufluss nicht. Nie pro Einzelkante.**

## 2. Kanal-Agnostik (zentrale Erkenntnis)

Das co-signierte Transkript ist **byte-identisch, egal über welchen Kanal** Nonces/Signaturen liefen. Der Bootstrap-Scan/Tap ist ein Air-Gap-Ereignis — für die Krypto unsichtbar. Ein Dritter kann Ein-Scan nicht von Zwei-Scan, NFC nicht von QR unterscheiden.

→ **Die Wahl des Pairing-Kanals ist eine App-/Zeremonie-Entscheidung, keine Wire-/Spec-Entscheidung.** Die Spec definiert das Transkript + die Claims; die Zeremonie bleibt der App überlassen und kann frei evolvieren.

**Anker vs. Transport sind verschiedene Rollen** und werden oft verwechselt:
- **Anker** = bindet eine DID an das physische Gerät/Person gegenüber (QR-Scan, NFC-Tap).
- **Transport** = trägt Nonces + Signatur-Austausch (BLE, Broker/Relay, QR-Payload).

## 3. Pairing-Kanäle

| Achse | QR | NFC | BLE |
|---|---|---|---|
| Proximity-Anker | mittel (Sichtlinie ~0,1–1 m) | stark (~4 cm Touch) | schwach (Meter, RSSI spoofbar) |
| Bystander-Interception | Broadcast (jeder in Sicht scannt) | praktisch keine (4 cm) | Broadcast + Geräte-Auswahl-Problem |
| Mutual-Anker in einer Geste | nein (2 Scans) | ja (Tap bindet beidseitig) | nein (braucht OOB-Anker) |
| Relay-Decke | offen (Foto-Relay) | offen, höhere Latte | offen (Range) |
| Als Datenkanal | begrenzt (statisch) | begrenzt (kleine Payloads) | exzellent (bidirektional GATT) |
| UX | universell, vertraut | am besten („bump") | Discovery/Pairing-Friktion |
| Plattform | überall (Kamera+Display, auch Web) | iOS-P2P faktisch blockiert; Android HCE ok | iOS-Web-BLE blockiert; nativ ok, iOS-Peripheral limitiert |

### QR: Ein-Scan vs. Zwei-Scan

Der Air-Gap-Scan ist gerichtet: Wer scannt, ist verankert; wer zeigt, nicht (sein QR ist Broadcast — jeder in Kamerareichweite kann ihn scannen und sich dazwischenschieben).
- **Zwei-Scan:** beide richten die Kamera aufeinander → beide verankert.
- **Ein-Scan:** nur der Scanner verankert; der Anzeigende ist exponiert (Scan-and-Substitute, real im Crowd-Setting — genau dem Zielumfeld). Convenience-Delta = ein Kamera-Tap.
- **Mittelweg Ein-Scan + verbaler SAS** (beide lesen einen kurzen Code aus dem Transkript-Hash vor; bei Substitution matchen die Codes nicht) holt fast die Zwei-Scan-Sicherheit zurück, Friktion ≈ zweiter Scan.

### NFC

Bester **Anker** (4 cm killt das Broadcast-Problem; bindet beidseitig in einer Geste → löst Convenience + Anchoring zugleich). **Aber:** iOS sperrt Device-to-Device-NFC für Dritt-Apps faktisch → cross-platform nicht als Default tragbar. EU-DMA-Öffnung (2024, HCE/entitlement-gated) ist ein Watch-Point.

### BLE

**Kein Anker, sondern Transport** (schwache Proximity, RSSI spoofbar, „Just-Works"-Pairing unauthentifiziert → braucht immer einen OOB-Anker wie QR/NFC/SAS). Als Datenkanal exzellent.

### Empfehlung Kanäle

- **QR als universelle Baseline** (einziger wirklich cross-platform Mechanismus, auch Web).
- **NFC-„Bump" als Premium-Enhancement, wo verfügbar** (Android-lastig wegen iOS).
- **BLE nur als Transport-Komfortschicht** auf einem QR-/NFC-Anker, nie als Anker.
- iOS ist gleichwertig wichtig → QR bleibt Default; NFC/BLE sind plattform-bedingte Extras.

## 4. NFC-Wearables (Timos Vision)

Bruchlinie: **passiver Tag vs. Secure Element.**

- **Passives Wearable** (NFC-Ring/Band/Sticker): nur statische Daten, keine Liveness, kein eigener Key → kann **nicht** an der Challenge-Response teilnehmen. Aber **exzellent für Discovery/Kontakt-Austausch** (Tap → DID/Profil; Klonbarkeit harmlos, da DID öffentlich; cross-platform lesbar inkl. iPhone). Liefert das Vision-Gefühl schon heute, null Protokolländerung.
- **Secure Wearable** (Secure Element / JavaCard): hält einen Key, signiert Challenge-Response → architektonisch **ein delegierter Device Key** (Identity 004 Device-Key-Delegation). Kohärent, aber Nischen-Hardware, Provisioning, Kosten, und iOS-NFC-limitiert. Zukunfts-/Premium-Pfad.

**Trennung: Discovery (wer bist du → Tap, replaybar-egal, öffentlich) ≠ Verifikation (Live-Präsenz beweisen → Challenge-Response). „Tap to connect" nicht mit „tap to verify" verwechseln.**

## 5. Phonelose Identitäten (Kinder / „Tag als Ausweis")

Szenario: Kinder bei Abenteuer/Workshop bekommen Attestations, ohne Handy.

**Kann eine Signatur einen Tag unkopierbar machen? Nein.** Signatur über statische Daten wird mitkopiert. Unkopierbar nur durch ein **Geheimnis on-chip** in Challenge-Response pro Tap.

Hardware-Stufen:
- **Dummes NTAG** (~0,10 €): DID-Zeiger. Kopierbar — aber egal, wenn der Tag nur **Empfänger** ist.
- **NTAG 424 DNA** (~0,5–2 €, passiv): wechselnder CMAC + Zähler pro Tap, AES-Secret on-chip → praktisch unkopierbar, aber **symmetrisch/backend-verifiziert** (nicht der DID-Key). Für „echter Org-Tag, nicht geklont".
- **Secure-Element-Karte** (~2–10 €): hält den Ed25519-DID-Key, peer-verifizierbar, unkopierbar. Schwerste Stufe, iOS-wacklig.

**Schlüsselunterscheidung:**
- **Tag als Empfänger** (Kind sammelt Attestations): öffentlicher DID-Zeiger; Attestation ist durch die **Aussteller-Signatur** an die Kind-DID gebunden; ein Klon kann nichts stehlen/fälschen → **kein Kopierschutz nötig**, dummes NTAG reicht.
- **Tag als Ausweis** (Kind beweist „ich bin's" für Zutritt/Vorteil): Besitz zählt → Klon = Diebstahl → **Kopierschutz nötig** (NTAG 424 / Secure Element).

**Key-Custody:** Ein phoneloses Kind hat trotzdem eine DID = ein Keypair. Sauberster Fit: **Guardianship** (Eltern/Org custodieren die DID, Tag zeigt darauf, Attestations laufen auf, später Handover) — hängt an Guardian-Vouching (Spec v2) + Identity-Migration. Löst auch Verlust (Tag ersetzbarer Zeiger statt einziger Key-Träger).

## 6. Stand: entschieden vs. offen

**Vorgeschlagene Richtung (noch nicht ratifiziert):**
- Ehrliches Modell: Verifikation = beweisbare Live-Mutual-Interaktion, nicht Begegnung.
- Co-signiertes Transkript als self-contained, drittprüfbares Beweis-Artefakt.
- Kanal-agnostisch; QR-Baseline; Trust-Gewichtung im Graphen.

**Offen / unausgereift (eigene, spätere Vertiefung):**
- NFC/BLE als konkrete Enhancements, Ein-/Zwei-Scan-Default (Sebastians UX-Feld).
- Wearable-Szenarien (Discovery-Tag bald; Secure-Wearable = Device-Key-Zukunft).
- Kinder-/Ausweis-Szenarien (Empfänger vs. Authenticator; Guardianship-Detail).

## 7. Konsequenz für die offenen Spec-Fragen

Das ehrliche Modell verschiebt die Marker-Frage aus wot-spec#100: Wenn eine Verifikation über ein **gültiges co-signiertes Transkript** (evidence) erkennbar wird, ist das ein self-beweisender Diskriminator — besser als ein nackter `type`-String. Das berührt web-of-trust#101 (Marker + `/v`÷`/a`-Split) und #102 (Vektoren). Die konkrete Entscheidung (Split behalten/kollabieren, Marker type vs. evidence, Mutual-Transkript jetzt vs. eigener Trust-002-Slice) wird separat geklärt — siehe die offenen Spec-Fragen.

Verwandt: [`security-analysis.md`](security-analysis.md) (Sybil/Split-Brain-Threats), Identity 004 (Device-Key-Delegation), [`project_wot_spec_v2`] Guardian-Vouching.
