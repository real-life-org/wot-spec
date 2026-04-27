# Identity Migration — Schlüsselrotation und DID-Wechsel

> **Nicht normativ:** Dieses Dokument ist Hintergrund, Analyse oder Planung. Normative Anforderungen stehen in den Spec-Dokumenten und in `CONFORMANCE.md`.

- **Status:** Research
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-23

## Zusammenfassung

Dieses Dokument beschreibt wie eine WoT-Identität migriert werden kann — sei es wegen Schlüsselkompromittierung, Algorithmus-Upgrade oder DID-Methoden-Wechsel. Die Migration funktioniert unterschiedlich je nach DID-Methode, aber das Protokoll ist durch die `resolve()`-Abstraktion ([Identity 003](../01-wot-identity/003-did-resolution.md)) DID-Methoden-agnostisch: der Migrationsmechanismus ändert sich, das Protokoll darüber nicht.

## Wann wird Migration gebraucht?

| Anlass | Dringlichkeit | Häufigkeit |
|---|---|---|
| **Seed-Kompromittierung** (Gerät gestohlen, Seed extrahiert) | Sofort | Selten |
| **DID-Methoden-Wechsel** (did:key → did:webvh) | Geplant | Einmalig |
| **Algorithmus-Upgrade** (Ed25519 → Post-Quantum) | Langfristig | Einmalig |
| **Spec-Konformanz** (HKDF-Pfad geändert) | Geplant | Einmalig |

## Migration je nach DID-Methode

### did:key — Neue DID + signierte Verknüpfung

Bei did:key IST die DID der Public Key. Jede Key-Änderung erzeugt eine neue DID. Migration bedeutet: die alte DID zeigt auf die neue.

**Migrations-Nachricht (JWS):**

```json
{
  "type": "identity-migration",
  "oldDid": "did:key:z6Mk...(alt)",
  "newDid": "did:key:z6Mk...(neu)",
  "timestamp": "2026-04-23T10:00:00Z"
}
```

Signiert als JWS mit dem **alten** Ed25519-Key (siehe [Identity 002](../01-wot-identity/002-signaturen-und-verifikation.md)). Die Signatur beweist: der Besitzer der alten Identität autorisiert den Wechsel.

**Propagation:**

1. **Profil-Service:** Altes Profil (`/p/{oldDid}`) bekommt ein `migratedTo`-Feld mit der neuen DID. Neues Profil (`/p/{newDid}`) wird angelegt.
2. **Inbox:** Migrations-Nachricht an alle bekannten Kontakte (Inbox-Nachricht `identity-migration/1.0`).
3. **Kontakt-Update:** Empfänger verifizieren die JWS-Signatur mit dem alten Public Key und aktualisieren ihr Adressbuch.

**Trust-Kontinuität:**

Bestehende Attestations referenzieren die alte DID. Verifier folgen der Migrationskette:

```
Attestation verweist auf did:key:z6Mk...(alt)
  → Migrations-Nachricht: alt → neu (JWS-signiert mit altem Key)
  → Attestation gilt für did:key:z6Mk...(neu)
```

**DIDComm `from_prior`:** DIDComm v2.1 definiert ein standardisiertes JWT für DID-Rotation. Wenn wir DIDComm-Envelope-Kompatibilität anstreben, SOLLTE die Migrations-Nachricht zusätzlich als `from_prior` JWT kodiert werden:

```json
{
  "sub": "did:key:z6Mk...(neu)",
  "iss": "did:key:z6Mk...(alt)",
  "iat": 1745398800
}
```

Signiert mit dem alten Key. DIDComm-Clients können das verstehen.

### did:webvh — DID bleibt stabil, Log-Update

Bei did:webvh ist die DID ein **stabiler Identifier** — unabhängig vom aktuellen Key. Key-Rotation wird durch einen neuen Eintrag im verifiable History Log dokumentiert.

**Keine "Migration" im eigentlichen Sinne** — die DID ändert sich nicht. Der User aktualisiert sein DID-Dokument:

```
DID-Log (JSONL):
  Entry 0 (Genesis):  { keys: [pubkey_0], keyAgreement: [x25519_0], service: [...] }
  Entry 1 (Rotation): { keys: [pubkey_1], keyAgreement: [x25519_1], service: [...], prev: hash(entry_0) }
```

Jeder Eintrag ist signiert und hash-verkettet. Kontakte die das Log kennen, können die Kette verifizieren.

**Propagation:**

1. **Profil-Service:** Neues DID-Dokument publizieren (ersetzt das alte). Optional: `GET /p/{did}/log` liefert das vollständige JSONL-Log.
2. **Inbox:** Update-Nachricht (`did-document-update/1.0`) an alle Kontakte mit dem neuen Log-Eintrag.
3. **Sync-Layer:** Log-Eintrag wird über den normalen Sync-Mechanismus verteilt.

**Trust-Kontinuität:**

Bestehende Attestations referenzieren dieselbe DID — sie bleiben unverändert gültig. Kein Adressbuch-Update nötig. Nur der gecachte Key wird aktualisiert.

**Key-Overlap-Period:** Nach einer Rotation SOLLTE der alte Key für eine Übergangszeit (z.B. 7 Tage) weiterhin im DID-Dokument stehen, damit Kontakte die das Update noch nicht haben weiterhin verschlüsseln können. Danach wird er entfernt.

### did:peer — Neue DID + `from_prior`

did:peer-DIDs können nicht in-place aktualisiert werden (die DID kodiert die Keys). Key-Rotation erzeugt eine neue DID — wie bei did:key. DIDComm definiert dafür `from_prior`:

```
Alte DID: did:peer:2.Vz6Mk...(alt).Ez6LS...(alt).S...
Neue DID: did:peer:2.Vz6Mk...(neu).Ez6LS...(neu).S...
```

Die erste Nachricht mit der neuen DID enthält ein `from_prior` JWT (signiert mit dem alten Key), das die Kontinuität beweist.

**Propagation:** Bilateral zwischen den Peers — did:peer-DIDs sind pairwise. Jeder Kommunikationspartner bekommt die Rotation direkt bei der nächsten Nachricht.

## Migration zwischen DID-Methoden

### did:key → did:webvh (geplant für Phase 2)

Der wichtigste Migrationspfad: Wenn das Protokoll von did:key auf did:webvh wechselt, muss jeder User seine Identität migrieren.

**Ablauf:**

```
1. User erstellt did:webvh-Identität (Genesis-Log-Eintrag mit denselben Keys)
2. User signiert Migrations-Nachricht: did:key → did:webvh (JWS mit altem Key)
3. User publiziert neues Profil unter did:webvh + Migrationsverweis unter did:key
4. Kontakte empfangen Migrations-Nachricht und aktualisieren Adressbuch
5. Neue Attestations referenzieren die did:webvh-DID
6. Alte Attestations bleiben verifizierbar über die Migrationskette
```

**Schlüssel-Kontinuität:** Die Ed25519- und X25519-Keys können identisch bleiben — nur die DID-Methode ändert sich. Damit ist die Migration ein reines Re-Encoding, kein kryptographischer Wechsel.

### did:key → did:peer (pairwise)

Für DIDComm-spezifische Kommunikationskanäle kann ein User zusätzlich zu seiner primären did:key/did:webvh-Identität pairwise did:peer-DIDs nutzen. Diese sind nicht "Migrationen" sondern zusätzliche kontextspezifische Identitäten, die an die primäre Identität gebunden sind.

## Sicherheits-Überlegungen

### Seed-Kompromittierung

Bei Seed-Kompromittierung ist die Migration dringlich — der Angreifer kann die alte Identität missbrauchen. Der User muss:

1. Sofort neuen Seed generieren → neue DID
2. Migrations-Nachricht signieren (mit dem alten Key, der ja noch kontrolliert wird)
3. An alle Kontakte propagieren
4. Alle Space Keys rotieren (siehe [Sync 005](../03-wot-sync/005-gruppen.md))

**Race-Condition:** Wenn der Angreifer schneller ist und seinerseits eine Migrations-Nachricht sendet (auf eine von ihm kontrollierte DID), gibt es einen Konflikt. Kontakte sehen zwei konkurrierende Migrationen für dieselbe alte DID. **Auflösung:** Die zeitlich erste Migrations-Nachricht gewinnt — daher die Dringlichkeit. Kontakte SOLLTEN bei widersprüchlichen Migrationen den User über einen unabhängigen Kanal (persönlich, Telefon) kontaktieren.

### Kettenlänge

Mehrfache Migrationen (A → B → C → D) erzeugen Ketten die bei der Verifikation aufgelöst werden müssen. Implementierungen SOLLTEN eine maximale Kettenlänge akzeptieren (z.B. 10). Längere Ketten deuten auf ein Problem hin.

### Irreversibilität

Eine publizierte Migrations-Nachricht kann nicht rückgängig gemacht werden — sie ist JWS-signiert und möglicherweise bereits bei Kontakten angekommen. Der einzige Weg zurück wäre eine erneute Migration (B → A), signiert mit dem Key von B.

### Seed-Verlust — Social Recovery via Guardian-Vouching

Alle bisherigen Migrations-Szenarien setzen voraus, dass der User den **alten Key noch kontrolliert** und damit die Migration signieren kann. Aber was wenn der Seed verloren ist? Gerät kaputt, Backup vernichtet, Mnemonic vergessen — der User hat keinen Zugriff auf seinen Private Key mehr.

In diesem Fall kann **kein** kryptographischer Beweis mehr erbracht werden, dass die neue Identität dieselbe Person ist. Die einzige Brücke ist das **soziale Netzwerk** — die Menschen die den User persönlich kennen.

**Guardian-Vouching (geplant für NLnet WP2)**

Das Prinzip: Der User hat vor dem Verlust eine Gruppe von **Guardians** (vertrauenswürdige Kontakte) benannt. Bei Seed-Verlust bestätigen genügend Guardians die neue Identität — nicht kryptographisch, sondern durch signierte Attestations.

**Ablauf:**

```
Vor dem Verlust:
  Alice benennt 5 Guardians (Bob, Carol, Dave, Eve, Frank)
  → Jeder Guardian speichert lokal: "Ich bin Guardian für Alice (did:key:z6Mk...alt)"
  → Kein Shamir, kein Secret-Sharing — nur ein sozialer Vertrag

Nach dem Verlust:
  1. Alice generiert neuen Seed → neue DID (did:key:z6Mk...neu)
  2. Alice kontaktiert ihre Guardians persönlich (Telefon, Treffen, Messenger)
  3. Alice sagt: "Ich habe meinen Seed verloren. Meine neue DID ist did:key:z6Mk...neu"
  4. Jeder Guardian verifiziert Alice's Identität (persönlich, Stimme, gemeinsame Erinnerungen)
  5. Jeder Guardian erstellt eine Recovery-Attestation:

     VC-Payload:
     {
       "@context": ["https://www.w3.org/ns/credentials/v2", "https://web-of-trust.de/vocab/v1"],
       "type": ["VerifiableCredential", "WotAttestation", "GuardianRecovery"],
       "issuer": "did:key:z6Mk...bob",
       "credentialSubject": {
         "id": "did:key:z6Mk...neu",
         "claim": "recovery-vouching",
         "previousDid": "did:key:z6Mk...alt"
       },
       "validFrom": "2026-04-23T10:00:00Z"
     }

  6. Wenn genügend Guardians (z.B. 3 von 5) die Recovery bestätigt haben,
     betrachten Kontakte die neue DID als Nachfolger der alten
```

**Was Guardian-Vouching NICHT ist:**

- **Kein Shamir Secret Sharing** — Guardians halten keine Key-Shards. Der Seed wird nicht aufgeteilt und kann nicht rekonstruiert werden. Die alte Identität ist unwiderruflich verloren.
- **Kein automatischer Prozess** — Guardians müssen aktiv und persönlich die Identität bestätigen. Das ist bewusst aufwändig — Recovery soll selten und sorgfältig sein.
- **Kein kryptographischer Beweis** — es ist ein sozialer Beweis. Die Guardians sagen: "Ich kenne diese Person und bestätige, dass sie jetzt diese neue DID hat." Die Sicherheit liegt im Vertrauen zwischen den Menschen, nicht in der Kryptographie.

**Schwelle (Threshold):**

Der User bestimmt vorab wie viele Guardians für Recovery ausreichen. Empfehlung:

| Guardians gesamt | Schwelle | Kommentar |
|---|---|---|
| 3 | 2 | Minimum — für enge Freundeskreise |
| 5 | 3 | Standard — Redundanz bei Nicht-Erreichbarkeit |
| 7 | 4 | Hohe Sicherheit — für Identitäten mit vielen Attestations |

**Trust-Kontinuität nach Recovery:**

Nach erfolgreichem Guardian-Vouching hat die neue DID einen **schwächeren Trust-Status** als eine normal migrierte DID:

- Normal migriert (alter Key signiert): Kryptographischer Beweis der Kontinuität
- Guardian-Recovery: Sozialer Beweis durch N Attestations

Implementierungen DÜRFEN den Unterschied visuell kennzeichnen ("Von 3 Guardians bestätigt" statt "Kryptographisch verifiziert"). Kontakte die die Recovery-Attestations sehen, können selbst entscheiden ob sie der neuen DID vertrauen.

**Guardian-Verwaltung:**

- Guardians werden im Personal Doc gespeichert (verschlüsselt, nur für eigene Geräte sichtbar)
- Der User SOLLTE seine Guardians regelmäßig prüfen (sind sie noch erreichbar? noch vertrauenswürdig?)
- Guardian-Beziehung ist gegenseitig — wenn Alice Bob als Guardian benennt, SOLLTE Bob das wissen
- Guardian-Wechsel (neuen Guardian benennen, alten entfernen) ist eine normale Personal-Doc-Operation

**Interaktion mit DID-Methoden:**

| DID-Methode | Guardian-Recovery |
|---|---|
| **did:key** | Neue DID + Guardian-Attestations die alte und neue DID verknüpfen |
| **did:webvh** | Neues DID-Dokument + Guardian-Attestations. Optional: did:webvh Pre-Rotation-Key bei einem Guardian hinterlegen (der Guardian hält den Hash des nächsten Keys, nicht den Key selbst) |

## Zusammenfassung der Mechanismen

| DID-Methode | DID ändert sich? | Mechanismus | Trust-Kontinuität |
|---|---|---|---|
| **did:key** | Ja | JWS-signierte Migrations-Nachricht (alt → neu) | Migrationskette folgen |
| **did:webvh** | Nein | Neuer Log-Eintrag im verifiable History | DID bleibt, nur Key-Cache aktualisieren |
| **did:peer** | Ja | DIDComm `from_prior` JWT | Bilateral, paarweise |
| **did:key → did:webvh** | Ja (Methode wechselt) | JWS-Migrations-Nachricht + neue Profilanlage | Migrationskette + Schlüssel-Kontinuität |

## Offene Fragen

1. **Automatische Migration bei Phase-2-Rollout:** Soll die App beim Update automatisch eine did:webvh-Migration auslösen, oder muss der User das aktiv bestätigen?
2. **Guardian-Recovery:** Wie interagiert Identity-Migration mit dem geplanten Guardian-Vouching-Recovery (NLnet WP2)?
3. **Multi-Device-Migration:** Wenn Alice auf zwei Geräten die Migration auslöst — welche gewinnt? (Vermutlich: identisches Ergebnis, weil gleicher Seed → gleiche neue Keys.)
