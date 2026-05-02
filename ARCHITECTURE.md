# Architektur-Kompass

> **Nicht normativ:** Dieses Dokument ist ein Arbeitskompass fuer Spec-Architektur und Implementierungs-Mapping. Normative Anforderungen stehen in den nummerierten Spec-Dokumenten, Schemas, Test-Vektoren und `CONFORMANCE.md`.

## Ziel

Diese Arbeit soll ein gemeinsames Architekturverstaendnis schaffen, bevor die TypeScript-Implementierung weiter umgebaut wird.

Das Zielbild ist:

```txt
Spec mit klaren Dokumentgrenzen
+ Abschnitts-READMEs als Lesefuehrung
+ pruefbare Conformance-Artefakte
+ TypeScript-Mapping ohne implizite Architekturentscheidungen
```

## Drei Ebenen

| Ebene | Zweck | Beispiele |
|---|---|---|
| 1. Root-README | Gesamtueberblick und Einstieg in die Spec. | `README.md` |
| 2. Abschnitts-README | Lesefuehrung innerhalb einer Dokumentfamilie. | `01-wot-identity/README.md`, `02-wot-trust/README.md`, `03-wot-sync/README.md` |
| 3. Detaildokumente | Normative Regeln, Formate, Flows und Verifikation. | `001-*`, `002-*`, Schemas, Test-Vektoren |

Regel: Je tiefer die Ebene, desto normativer und detaillierter. Hoehere Ebenen duerfen erklaeren und verbinden, aber keine Detailregeln duplizieren oder ueberstimmen.

## Arbeitsprinzipien

1. Spec-Dokumente sind die Source of Truth.
2. Abschnitts-READMEs verbinden Dokumente, statt sie zu kopieren.
3. Unklare Regeln werden in den nummerierten Spec-Dokumenten korrigiert.
4. Diagramme bleiben klein und beantworten eine konkrete Architekturfrage.
5. Conformance-Profile sind Implementierungs-Claims, keine eigenen Architekturbausteine.
6. Implementierungsdetails duerfen die Spec informieren, aber nicht heimlich ersetzen.

## Architekturfragen Vor Dem TS-Mapping

Diese Fragen muessen ausreichend klar sein, bevor die TypeScript-Architektur systematisch angepasst wird.

| Bereich | Zu klaeren |
|---|---|
| Identity | Was ist Identity Core? Was ist nur Erweiterung? Welche Signaturpruefung liegt bei Identity, welche Semantik bei Trust oder Sync? |
| Trust | Was ist Attestation-Semantik? Was ist Verification? Was gehoert nicht in Trust, z.B. Device-Key-Authority oder Sync-Zustellung? |
| Sync | Was ist Protokoll, was Transport, was Broker? Was ist persistentes WoT-Objekt, was ephemerer Envelope? Was bleibt CRDT-/App-agnostisch? |
| Extensions | Welche Semantik ist RLS/HMC-spezifisch? Welche Extension nutzt nur Trust, welche braucht Sync? |
| Conformance | Welche Claims sind pruefbar? Welche Spec-Abschnitte, Schemas und Test-Vektoren belegen sie? |
| TypeScript | Welche Module entsprechen Identity, Trust, Sync, Ports, Adapters und App? Welche aktuellen Module vermischen diese Grenzen? |

## Reihenfolge

1. Root-README auf Gesamtueberblick und Leseregeln stabilisieren.
2. Abschnitts-README fuer Identity fertigstellen.
3. Abschnitts-README fuer Trust erstellen.
4. Abschnitts-README fuer Sync erstellen.
5. RLS/HMC nur so weit strukturieren, wie es fuer Trust-/Sync-Grenzen noetig ist.
6. Danach TypeScript-Mapping dokumentieren und erst dann groessere TS-Refactors fortsetzen.

## Definition of Done Vor Groesseren TS-Refactors

Vor einem groesseren TypeScript-Umbau sollte gelten:

1. Root-README beschreibt die Dokumentfamilien und Leseregeln klar.
2. Identity, Trust und Sync haben je eine knappe Abschnitts-README.
3. Die wichtigsten Schichtgrenzen sind in der Spec verlinkt, nicht nur im Kopf bekannt.
4. Offene Architektur-Kanten sind explizit benannt.
5. Fuer das TS-Mapping ist klar, welche Spec-Familie welchem Modul-/Port-Bereich entspricht.
6. `npm run validate` in `wot-spec` ist gruen.

## Implementierungs-Kompass

Das konkrete TypeScript-Mapping steht in [IMPLEMENTATION-ARCHITECTURE.md](IMPLEMENTATION-ARCHITECTURE.md). Zielrichtung:

```txt
protocol <- application <- react <- app
ports <- application
ports <- adapters
```

Dabei gilt:

1. `protocol` bildet normative Spec-Objekte und Verifikation ab.
2. `application` orchestriert Workflows, ohne Wire-Regeln neu zu definieren.
3. `ports` beschreiben externe Faehigkeiten wie Storage, Crypto, Network, Broker oder CRDT.
4. `adapters` implementieren Ports, duerfen aber keine Protokollautoritaet besitzen.
5. UI/App-Code konsumiert Application-Use-Cases, nicht rohe Protokollinternals.
