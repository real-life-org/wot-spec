# Härtung: Relay-Wechsel, Log-Lücken und Zustands-Konvergenz

Status: Diskussions-Draft (nicht normativ). Vorschlag für Regel-Ergänzungen in [Sync 002](../03-wot-sync/002-sync-protokoll.md). Anlass ist ein vollständig diagnostizierter Produktions-Vorfall (13.07.2026), dessen Beweiskette unten dokumentiert ist.

## Anlass: der Vorfall in einem Absatz

Ein Gerät (Handy) schrieb sein Personal-Doc-Log `seq 0..51` gegen Broker A (Festival-Box) und nach einem Relay-Wechsel `seq 52..88` gegen Broker B (Live-Relay). Broker B hat `0..51` nie erhalten, das Gerät publizierte sie nicht nach (sie waren lokal `acked`). Ein zweites Gerät (Browser) an Broker B empfing `52..88` vollständig und persistierte sie, konnte aber nichts davon anzeigen: Yjs hält Updates mit fehlenden kausalen Vorgängern intern als *pending* zurück. Ergebnis: bidirektional wirkungsloser Sync zwischen zwei verbundenen, korrekt arbeitenden Geräten, ohne jede Fehlermeldung. Der GapRepair-Mechanismus arbeitete korrekt (8 Nachforderungs-Versuche), gegen einen Broker, der die Einträge strukturell nicht hat.

Beweiskette (Browser-IndexedDB, Box-SQLite, Relay-Stats): Browser-Log `e4827f53: 52..88` lückenlos plus `gapRepair {firstMissing: 0, observedMax: 88, attempts: 8, softSkipped: false}`; Box-Relay `e4827f53: 0..51` lückenlos; Live-Relay nur `52..88`. Transport, Persistenz und Gap-Bookkeeping funktionierten spec-konform. Der Schaden entsteht in drei Regel-Lücken.

## Befund: drei Regel-Lücken

**B1: Reconnect-Abgleich ist einseitig.** [App-Start und Reconnect](../03-wot-sync/002-sync-protokoll.md#app-start-und-reconnect) Schritt 3/7 normiert nur `broker_seq > local_seq` (Restore/Clone-Regel). Der umgekehrte Fall `local_seq > broker_seq` für die eigene `deviceId` ist nicht definiert. Ein lokal `acked` Eintrag wird nie nachpubliziert, denn `acked` ist faktisch broker-spezifisch, wird aber wie global durabel behandelt. Jeder Relay-Wechsel strandet damit die gesamte bisherige Historie des Geräts.

**B2: „angewandt" ist nicht „wirksam".** [Kontiger Cursor](../03-wot-sync/002-sync-protokoll.md#vollstaendigkeits-cursor-luecken-und-pagination) sagt: „Oberhalb einer Luecke empfangene Eintraege werden angewandt (der CRDT-Merge ist kommutativ und idempotent)." Die Kommutativität gilt für die Merge-Operation, nicht für die Sichtbarkeit: Yjs (und Automerge) puffern Updates mit fehlenden kausalen Vorgängern engine-intern und wenden sie erst bei Ankunft der Vorgänger wirksam an. Eine Lücke versteckt also nicht nur ihren eigenen Inhalt, sie quarantäniert alle kausal späteren Einträge desselben Autors. Auch der spezifizierte Cursor-Soft-Skip ändert daran nichts: er heilt den Nachforderungs-Cursor, nicht die CRDT-Ebene.

**B3: Die stillen Zustände sind unbeobachtbar.** Drei Pufferzustände können unbegrenzt wachsen, ohne dass Nutzer oder Betreiber sie sehen: (a) GapRepairs gegen eine Quelle, die die Einträge nachweislich nicht hat, (b) `blocked-by-key`-Puffer, (c) die CRDT-Pending-Queue. [App-Start](../03-wot-sync/002-sync-protokoll.md#app-start-und-reconnect) Schritt 9 kennt nur binär „aktuell / potentiell veraltet"; ein dauerhaft teilkonvergenter Zustand präsentiert sich als gesund.

**B4 (Folgeschaden): das schlechter informierte Gerät überschreibt abgeleitete Publikationen.** Das teilkonvergente Gerät publizierte seinen unvollständigen Zustand (1 Attestation statt vieler) mit monoton steigenden Versionen auf den Profilserver und schrieb Vault-Snapshots seines unvollständigen Stands. Beides kann das vollständigere Gerät per Monotonie-Guard aussperren bzw. dessen Snapshot verdrängen. Die bestehende Regel „Snapshots duerfen keinen bekannten gueltigen Log-Eintrag zurueckrollen" ([Gemeinsame Regeln](../03-wot-sync/002-sync-protokoll.md#gemeinsame-regeln)) prüft das nicht operationalisierbar.

## Vorgeschlagene Regeln

**R1: Re-Anchor eigener Einträge (MUSS).** Ergibt der Broker-Head-Abgleich (App-Start Schritt 3/7) für die eigene `deviceId` `local_seq > broker_seq`, MUSS der Client die dem Broker fehlenden eigenen Einträge nachpublizieren, als retrybarer Outbox-Zustand mit idempotenter Wiederholung (Dedup via Content-Hash, wie [Lokaler Schreibvorgang](../03-wot-sync/002-sync-protokoll.md#lokaler-schreibvorgang) Schritt 5). `acked` ist damit explizit **pro Broker** definiert, nicht global. Autor ist das Gerät selbst, es entsteht kein Author-Binding-Konflikt.

**R2: Zustands-Konvergenz bei dauerhaft fehlenden Lücken (MUSS).** Ist eine Lücke [autoritativ abwesend](../03-wot-sync/002-sync-protokoll.md#vollstaendigkeits-cursor-luecken-und-pagination) und bleibt sie über die Soft-Skip-Schwellen hinaus unfüllbar, MUSS der Client Konvergenz auf Zustandsebene herstellen: einen Snapshot-mit-Heads (Vault oder Peer) beziehen, dessen Heads-Abdeckung die Lücke einschließt ([Snapshot-Regeln](../03-wot-sync/002-sync-protokoll.md#snapshot--und-full-state-optimierungen)), und ihn mergen. Erst wenn Snapshot-Heads die Lücke abdecken, gilt der Bereich als konvergiert; der Cursor-Skip allein beendet den Lücken-Zustand nicht.

**R3: Beobachtbarkeit teilkonvergenter Zustände (MUSS).** GapRepair-Bestand, `blocked-by-key`-Puffer und CRDT-Pending-Bestand MÜSSEN durabel gezählt und der Anwendung als Sync-Zustand gemeldet werden (mindestens: Anzahl zurückgehaltener Einträge pro `docId`, Alter der ältesten Zurückhaltung). Eine UI MUSS „Sync unvollständig" darstellen können, solange einer der Bestände nicht leer ist. Erweitert App-Start Schritt 9 von binär auf dreiwertig: aktuell / veraltet / **teilkonvergent**.

**R4: Heads-Schutz für abgeleitete Publikationen (SOLL).** Vor dem Überschreiben eines Snapshots oder einer abgeleiteten Ressource (Profilserver-Publikation) SOLL der Client die Heads-Abdeckung des vorhandenen Stands mit der eigenen vergleichen. Ist die eigene Abdeckung eine echte Teilmenge, unterbleibt das Überschreiben. Das operationalisiert die bestehende Nicht-Zurückrollen-Regel über den vorhandenen Heads-Mechanismus.

## Recovery für Bestandsfälle (informativ)

Zwei gleichwertige Pfade, beide idempotent: (1) Reseed der gestrandeten Einträge in den Ziel-Broker (`doc_log`-Insert der signierten Original-JWS; der laufende GapRepair der Clients zieht sie selbstständig). (2) Snapshot-Restore von einem vollständigen Gerät gemäß R2. Nach R1 wären künftige Relay-Wechsel selbstheilend, nach R2 auch Fälle mit endgültig verlorener Quelle.

## Offene Fragen

1. Bound für R1 bei großem Delta gegen einen frischen Broker (alles nachpublizieren vs. Snapshot-Baseline plus Delta)?
2. Darf ein Drittgerät (gleiche DID) gestrandete fremd-authored Einträge reseeden, wenn es sie besitzt? Signatur bleibt gültig, Relay-seitig heute vom Author-Binding abhängig.
3. R3-Schwellen: ab wann meldet die UI (sofort vs. nach Soft-Skip-Mindestalter)?
