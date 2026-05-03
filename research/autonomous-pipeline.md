# Autonomous Spec-Driven Development Pipeline

> **Nicht normativ:** Dieses Dokument ist Hintergrund, Analyse oder Planung. Normative Anforderungen stehen in den Spec-Dokumenten und in `CONFORMANCE.md`.

*Stand: 2. Mai 2026*

## Kontext

Die Web-of-Trust-Entwicklung laeuft seit Q4 2025 weitgehend spec-driven: normative Dokumente, Test-Vektoren, Schemas und ein Conformance-Manifest (`conformance/manifest.json`) definieren, was korrekt ist. Die TypeScript-Referenzimplementierung (`web-of-trust`) wird gegen diese Spec gebaut.

Der Flaschenhals ist die Orchestrierung. Heute startet, steuert und reviewed ein Mensch (Anton) jeden Arbeitsschritt manuell:

```
Anton denkt: "Was ist als Naechstes dran?"
Anton sagt zu Claude: "Implementier das."
Anton sagt zu Codex: "Bau das."
Anton sagt zu Claude: "Review mal was Codex gemacht hat."
Anton merged.
```

Dieses Dokument beschreibt, wie diese Schleife automatisiert wird, sodass Antons Rolle sich vom Ausfuehren zum Entscheiden verschiebt.

Operative Umsetzung: Die konkrete Level-1-Basis fuer die TypeScript-Referenzimplementierung liegt in `web-of-trust/docs/PROJECT-FLOW.md` und `web-of-trust/docs/automation/`. Dort werden Task-Contract-Format, Review-Rollen und das lokale PR-Review-Paket-Script beschrieben. Dieses Research-Dokument bleibt die Pipeline-Vision; die `web-of-trust`-Dokumente beschreiben die ausfuehrbare Projektschicht.

## Grundannahme

Die Spezifikation ist die Programmiersprache fuer die Agents. Je praeziser die Spec, desto autonomer koennen Claude und Codex arbeiten:

| Spec-Praezision | Agent-Autonomie | Beispiel |
|---|---|---|
| Test-Vektor (Input + erwartetes Output) | Vollstaendig autonom | `phase-1-interop.json` |
| JSON Schema + MUST/SHOULD-Regeln | Weitgehend autonom | `attestation-vc-payload.schema.json` |
| Prosa mit klaren Anforderungen | Braucht gelegentlich Rueckfrage | `001-identitaet-und-schluesselableitung.md` |
| Vage Prosa oder fehlend | Nicht autonom moeglich | Zurueck an Mensch |

Die Pipeline wird daher umso leistungsfaehiger, je mehr Spec-Abschnitte durch Test-Vektoren und Schemas abgedeckt sind.

## Architektur

```
MENSCHLICHE EBENE
  Anton + Team: Spec schreiben, Architektur-Entscheidungen,
  Merge-Gate, Richtung vorgeben
       |                              ^
       | pusht Spec                   | approved / rejected
       v                              |
SPEC REPOSITORY (wot-spec/)           |
  01-wot-identity/                    |
  02-wot-trust/                       |
  03-wot-sync/                        |
  test-vectors/                       |
  schemas/                            |
  conformance/manifest.json           |
  ROADMAP.md                          |
       |                              |
       v                              |
ORCHESTRIERUNG                        |
  Scheduled Agents + GitHub Actions   |
       |                              |
       +---> Conformance-Waechter ----+
       +---> Gap-Analyse              |
       +---> Task-Generierung         |
       +---> Implementierung (Claude / Codex)
       +---> Cross-Review             |
       +---> Human Gate --------------+
```

## Die sieben Phasen

### Phase 0: Conformance-Waechter

**Frequenz:** Taeglich, plus bei jedem Push auf `main`

**Agent:** Claude `/schedule`

**Aufgabe:**
1. `npm run validate` in `wot-spec/` ausfuehren (Schemas, Vektoren, Manifest)
2. `pnpm --filter @web_of_trust/core test` in `web-of-trust/` ausfuehren
3. Ergebnis als GitHub Issue zusammenfassen, falls Regressionen

**Trigger-Bedingung:** Nur bei Rot wird ein Issue erstellt. Gruene Laeufe erzeugen hoechstens einen kurzen Statuskommentar auf einem bestehenden Tracking-Issue.

**Output-Schema:**
```
## Conformance Report — {Datum}

### wot-spec validate
- schemas: {pass|fail} ({n} schemas)
- test-vectors: {pass|fail} ({n} vectors)
- conformance: {pass|fail}

### web-of-trust tests
- @web_of_trust/core: {pass|fail} ({n}/{m} tests)
- typecheck: {pass|fail}
- build: {pass|fail}

### Regressions
- {Liste der neu fehlgeschlagenen Tests mit Commit-Referenz}
```

### Phase 1: Gap-Analyse

**Frequenz:** Woechentlich (Montag), plus bei Spec-Aenderungen

**Agent:** Claude `/schedule`

**Aufgabe:**
1. `conformance/manifest.json` einlesen — welche Profile, welche Spec-Dokumente, welche Test-Vektoren
2. Fuer jedes Conformance-Profil pruefen:
   - Existieren alle referenzierten Test-Vektoren?
   - Haben alle Test-Vektor-Sektionen entsprechende Tests in `web-of-trust`?
   - Existieren alle referenzierten Schemas?
   - Gibt es MUST/SHOULD-Anforderungen in der Spec ohne Test-Vektor?
3. `ROADMAP.md` Milestone-Status aktualisieren
4. Ergebnis als GitHub Issue mit Label `gap-analysis`

**Konkret fuer den aktuellen Stand:**

Das Conformance-Manifest definiert 6 Profile (`wot-identity@0.1`, `wot-trust@0.1`, `wot-sync@0.1`, `wot-device-delegation@0.1`, `wot-rls@0.1`, `wot-hmc@0.1`). Die Gap-Analyse prueft fuer jedes Profil den Deckungsgrad zwischen Spec-Anforderungen, Schemas, Test-Vektoren und Implementierung.

**Output-Schema:**
```
## Gap Analysis — {Datum}

### Per Conformance-Profil

#### wot-identity@0.1
- Spec-Dokumente: 3/3 vorhanden
- Schemas: 1/1 vorhanden
- Test-Vektor-Sektionen: identity (impl: ja), did_resolution (impl: ja)
- Offene MUST-Anforderungen ohne Vektor: {Liste}

#### wot-sync@0.1
- Test-Vektor-Sektionen: ecies (impl: ja), log_entry_jws (impl: teilweise), ...
- Offene MUST-Anforderungen ohne Vektor: {Liste}

### Neue Gaps seit letzter Analyse
- {Liste mit Spec-Referenz und Dateipfad}

### Priorisierte naechste Schritte
1. {Hoechste Prioritaet mit Begruendung}
2. ...
```

### Phase 2: Task-Generierung

**Trigger:** Nach jeder Gap-Analyse, oder manuell durch Anton

**Agent:** Claude (synchron oder `/schedule`)

**Aufgabe:** Gaps in ausfuehrbare, atomare Tasks zerlegen.

**Regeln fuer einen guten Task:**
- **Ein Task = ein PR.** Nicht groesser als ein zusammenhaengendes Feature oder eine Korrektur.
- **Spec-Referenz ist Pflicht.** Jeder Task referenziert exakt welche Spec-Abschnitte, Test-Vektoren oder Schema-Dateien er adressiert.
- **Done-Kriterien sind maschinenlesbar.** Welche Tests muessen gruen sein? Welche Validierungen muessen laufen?
- **Constraints sind explizit.** Welche Dateien duerfen geaendert werden? Welche Interfaces sind stabil? Welche Layer-Grenzen gelten?
- **Komplexitaet ist geschaetzt.** `small` (< 100 Zeilen), `medium` (100-500), `large` (> 500, sollte gesplittet werden).

**Task-Format (GitHub Issue):**
```
## Task: {Titel}

**Spec Reference:** {Dokument} Section {N}, Test-Vektoren: {Liste}
**Conformance Profile:** {Profil aus manifest.json}

**Scope:**
- {Dateipfade die geaendert werden}

**Done Criteria:**
- [ ] {Konkrete Test- oder Validierungsbedingung}
- [ ] `pnpm --filter @web_of_trust/core test` gruen
- [ ] `pnpm --filter @web_of_trust/core typecheck` gruen

**Constraints:**
- {Layer-Grenzen, Interface-Stabilitaet, etc.}

**Complexity:** small | medium | large
**Labels:** agent-task, ready, {conformance-profile}
```

**Menschliches Gate:** Tasks mit Complexity `large` oder unklarer Spec bekommen Label `needs-human` statt `ready`.

### Phase 3: Implementierung

**Trigger:** GitHub Issue mit Labels `agent-task` + `ready`

**Agents:** Claude und Codex arbeiten parallel aus dem Task-Pool.

**Routing — wer bekommt welchen Task:**

| Kriterium | Agent | Begruendung |
|---|---|---|
| Neuen Test-Vektor implementieren | Codex | Klar eingegrenzt: Input/Output gegeben |
| Neues Schema validieren | Codex | Mechanisch, Schema liegt vor |
| Spec-Section erstmalig implementieren | Codex | Fokussiert, spec-nah, schnell |
| Refactoring / Layer-Migration | Claude | Architektur-Kontext, Cross-Cutting |
| Bug aus Conformance-Regression | Codex | Klar eingegrenzt durch fehlschlagenden Test |
| Neuen Test-Vektor *schreiben* | Claude | Braucht Spec-Interpretation |
| Adapter auf neues Port-Interface umstellen | Codex | Mechanisch, Interface definiert |
| Spec-Ambiguitaet → Implementation erfordert Entscheidung | Keiner | Zurueck an Anton |

**Ablauf pro Agent:**

1. Agent liest den Task-Issue komplett (Spec-Referenz, Scope, Done Criteria, Constraints)
2. Agent erstellt Branch: `agent/{claude|codex}/{issue-number}-{slug}`
3. Agent implementiert innerhalb des definierten Scope
4. Agent fuehrt Done-Criteria-Checks lokal aus (Tests, Typecheck, Build)
5. Agent erstellt PR mit:
   - Referenz auf Task-Issue (`Closes #{issue}`)
   - Zusammenfassung der Aenderungen
   - Ergebnis der Done-Criteria-Checks
6. PR bekommt Label `needs-cross-review`

**Fehlerfall:** Wenn ein Agent die Done-Kriterien nicht erfuellen kann (Test bleibt rot, Spec unklar, Scope zu gross), erstellt er einen Kommentar auf dem Task-Issue mit einer Analyse statt eines PRs. Das Issue bekommt Label `blocked`.

### Phase 4: Cross-Review

**Trigger:** PR mit Label `needs-cross-review`

**Ablauf:**

```
PR erstellt von Agent A
  |
  v
GitHub Action erkennt Label "needs-cross-review"
  |
  v
Agent B wird getriggert (Claude reviewt Codex, Codex reviewt Claude)
  |
  +-- Prueft:
  |   1. Spec-Konformitaet: Stimmt die Implementierung mit der
  |      referenzierten Spec-Section und den Test-Vektoren ueberein?
  |   2. Layer-Grenzen: Werden die Import-Regeln aus
  |      IMPLEMENTATION-ARCHITECTURE.md eingehalten?
  |   3. Security: Crypto korrekt, keine Injection, OWASP-konform?
  |   4. Done Criteria: Sind alle Checks aus dem Task-Issue erfuellt?
  |   5. Konsistenz: Passt der PR zur restlichen Codebase?
  |
  v
Review-Ergebnis als PR-Kommentar
  |
  +-- Approve          --> Label "ready-for-human"
  +-- Request Changes  --> Agent A ueberarbeitet, neuer Review-Zyklus
  +-- Uneinigkeit      --> Label "needs-discussion", Summary fuer Anton
```

**Review-Format:**
```
## Cross-Review von {Agent}

**Spec Conformance:** {pass|fail} — {Details}
**Layer Boundaries:** {pass|fail} — {Details}
**Security:** {pass|warn|fail} — {Details}
**Done Criteria:** {pass|fail} — {Checkliste}
**Consistency:** {pass|warn} — {Details}

**Verdict:** approve | request-changes | needs-discussion
**Summary:** {1-2 Saetze}
```

### Phase 5: Human Gate

**Trigger:** PR mit Label `ready-for-human` oder `needs-discussion`

**Antons reduzierter Aufwand:**

| PR-Typ | Aktion | Zeitaufwand |
|---|---|---|
| `ready-for-human` (beide Agents approved) | Kurz draufschauen, mergen | ~30 Sekunden |
| `needs-discussion` (Agents uneinig) | Lesen, entscheiden, kommentieren | ~5 Minuten |
| `blocked` (Agent kam nicht weiter) | Spec klaeren oder Task anpassen | ~15 Minuten |

**Fuer Teammitglieder (Sebastian, Tillmann):** Sie sehen dieselben PRs und koennen kommentieren. Agents reagieren auf Kommentare von jedem Teammitglied, nicht nur von Anton.

**Geschaetzter Tagesaufwand:** 15-30 Minuten statt mehrerer Stunden manueller Steuerung.

### Phase 6: Merge und Feedback-Loop

**Nach dem Merge:**

1. CI laeuft (existierende `ci.yml`)
2. Conformance-Waechter (Phase 0) bestaetigt, dass nichts kaputt ist
3. Task-Issue wird geschlossen
4. Falls die Implementierung Spec-Luecken aufgedeckt hat: neues Issue in `wot-spec/` mit Label `spec-gap`

**Feedback-Loop zurueck in die Spec:**

```
Implementierung deckt Ambiguitaet auf
  |
  v
Agent erstellt Issue in wot-spec/ mit:
  - Betroffener Spec-Abschnitt
  - Was unklar ist
  - Vorschlag (falls moeglich)
  - Label: spec-gap
  |
  v
Anton/Team entscheidet
  |
  v
Spec-Aenderung --> Neuer Gap-Analyse-Zyklus
```

## Ressourcen und Kontingente

| Ressource | Verfuegbar | Einsatz |
|---|---|---|
| Claude Max | Unbegrenzte Messages | Gap-Analyse, Task-Generierung, Reviews, Architektur-Tasks |
| ChatGPT Pro (Codex) | Kontingent-basiert | Fokussierte Implementierungstasks, mechanische Korrekturen |
| GitHub Actions | CI-Minuten (2000/Monat Free, mehr bei Pro) | Cross-Review-Trigger, Conformance-Checks, PR-Automatisierung |
| `/schedule` (Claude Code) | Cron-basierte Agents | Conformance-Waechter, Gap-Analyse |

**Optimale Kontingentnutzung:**

- Claude uebernimmt die kontinuierlichen, kontextschweren Aufgaben (Analyse, Review, Architektur)
- Codex uebernimmt die fokussierten, klar eingegrenzten Implementierungstasks
- GitHub Actions ist der Event-basierte Kleber dazwischen

## Voraussetzungen

Was existiert und was fehlt:

| Komponente | Status | Aufwand |
|---|---|---|
| Spec-Repository mit Test-Vektoren und Schemas | Existiert (`wot-spec/`) | — |
| Conformance-Manifest | Existiert (`conformance/manifest.json`) | — |
| CI Pipeline | Existiert (`.github/workflows/ci.yml`) | — |
| ROADMAP.md mit Milestones | Existiert (`ROADMAP.md`) | — |
| IMPLEMENTATION-ARCHITECTURE.md | Existiert (`IMPLEMENTATION-ARCHITECTURE.md`) | — |
| Claude `/schedule` | Verfuegbar | Konfigurieren |
| Codex CLI/API | Verfuegbar (ChatGPT Pro) | GitHub Action bauen |
| Maschinenlesbarer Impl-Status pro Spec-Section | Fehlt | `conformance/impl-status.json` anlegen |
| Cross-Review GitHub Action | Fehlt | Workflow schreiben |
| Task-Template als Issue-Template | Fehlt | `.github/ISSUE_TEMPLATE/agent-task.md` |
| Routing-Logik (Label-basiert) | Fehlt | Einfache Action oder Bot |

## Implementierungsreihenfolge

Jede Stufe ist einzeln nutzbar. Man muss nicht alles auf einmal bauen.

### Stufe 1: Conformance-Waechter (1 Tag)

- Claude `/schedule` Agent der taeglich `npm run validate` und `pnpm test` prueft
- Issue nur bei Regression
- **Sofortiger Nutzen:** Regressions-Fruehwarnung ohne manuelles Pruefen

### Stufe 2: Gap-Analyse (1 Tag)

- Claude `/schedule` Agent der woechentlich `manifest.json` gegen Implementierung abgleicht
- Output als GitHub Issue
- **Nutzen:** Anton muss nicht mehr selbst nachdenken was als naechstes dran ist

### Stufe 3: Task-Template und Issue-Generierung (halber Tag)

- GitHub Issue Template fuer `agent-task`
- Claude generiert Tasks aus Gap-Analyse
- Anton reviewed und labelt mit `ready`
- **Nutzen:** Tasks sind fuer Agents konsumierbar, nicht nur fuer Menschen

### Stufe 4: Cross-Review Action (1-2 Tage)

- GitHub Action: bei PR mit Label `needs-cross-review`, trigger den jeweils anderen Agent
- Claude reviewed via Claude Code / API
- Codex reviewed via Codex API
- Review als PR-Kommentar
- **Nutzen:** Der groesste Qualitaets-Hebel — jeder PR wird von zwei unabhaengigen Agents geprueft

### Stufe 5: Autonome Implementierung (2-3 Tage)

- Agent pickt `ready`-Issues, erstellt Branch und PR
- Claude via `/schedule` oder Webhook
- Codex via GitHub Action oder API
- **Nutzen:** Implementierung laeuft ohne dass Anton sie anstossen muss

### Stufe 6: Vollstaendige Pipeline (laufend)

- Alle Phasen verbunden
- Feedback-Loop von Implementierung zurueck in Spec
- Metriken: Durchsatz (PRs/Woche), Regressionsrate, Time-to-Merge
- **Nutzen:** Spec-Push loest automatisch die gesamte Kette aus bis zum mergebaren PR

## Risiken und Gegenmassnahmen

| Risiko | Beschreibung | Gegenmassnahme |
|---|---|---|
| Drift | Agents implementieren etwas das der Spec nicht entspricht | Test-Vektoren als harte Gate-Bedingung, Cross-Review |
| Schleifen | Agent A aendert, Agent B reverted, endlos | Max 2 Review-Zyklen, danach `needs-discussion` |
| Spec-Luecken | Agent trifft Entscheidung die in der Spec nicht steht | `blocked`-Label, Rueckfrage an Mensch, kein stilles Raten |
| Kontingent-Verschwendung | Agents arbeiten an niedrig-priorisierten Tasks | Prioritaeten in ROADMAP.md, nur `ready`-Issues werden bearbeitet |
| Merge-Konflikte | Parallele Agents aendern dieselben Dateien | Scope in Task klar definieren, bei Konflikt: juengerer PR rebased |
| Qualitaetserosion | "Zwei Agents approved" wird zum Rubber-Stamp | Conformance-Waechter als unabhaengige dritte Pruefung |

## Metriken (nach Stufe 6)

| Metrik | Ziel | Messung |
|---|---|---|
| Spec-Abdeckung | Jede MUST-Anforderung hat einen Test-Vektor | Gap-Analyse-Report |
| Impl-Abdeckung | Jeder Test-Vektor hat einen gruenen Test | Conformance-Waechter |
| Durchsatz | 5-10 gemergete PRs pro Woche | GitHub API |
| Time-to-Merge | < 48h von Task-Erstellung bis Merge | GitHub API |
| Regressionsrate | < 5% der PRs verursachen eine Regression | Conformance-Waechter |
| Human-Aufwand | < 30 Minuten pro Tag fuer Merge-Entscheidungen | Selbstmessung |

## Abgrenzung

Dieses Konzept beschreibt die Automatisierung des **Implementierungs-Workflows**. Folgendes ist explizit nicht Teil der Pipeline:

- **Spec-Authoring:** Normative Entscheidungen bleiben bei Menschen. Die Pipeline implementiert Spec, sie schreibt sie nicht.
- **Architektur-Entscheidungen:** IMPLEMENTATION-ARCHITECTURE.md wird von Menschen geschrieben. Agents halten sich daran.
- **Release-Management:** Tags, Changelogs und Veroeffentlichungen bleiben manuell oder werden separat automatisiert.
- **Deployment:** Die bestehende Deploy-Pipeline (Docker, NixOS, Watchtower) ist orthogonal.
- **Rust/HMC Track:** Die zweite Implementierung hat eigene Maintainer und einen eigenen Workflow. Die Pipeline liefert ihr Test-Vektoren und Conformance-Checks, nicht Code.

## Zusammenfassung

Die Pipeline verwandelt Spec-Aenderungen in gemergete PRs mit minimalem menschlichen Aufwand:

```
Spec aendern  -->  Gap erkannt  -->  Task generiert  -->  Agent implementiert
     ^                                                           |
     |                                                           v
     +--- Spec-Luecke <--- Feedback <--- Human Gate <--- Cross-Review
```

Die Spezifikation ist die Kontrollschicht. Test-Vektoren sind die maschinenlesbare Autorisierung. Menschen entscheiden *was* gebaut wird (Spec) und *ob* es gut genug ist (Merge-Gate). Maschinen erledigen alles dazwischen.
