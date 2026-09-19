#!/usr/bin/env python3
"""Prueft die normativen Woerter in docs/ gegen meta/CONVENTIONS.md.

Drei Regeln, alle drei sind stumme Fehler, wenn sie niemand prueft:

1. SOLL und SOLLEN sind keine Schluesselwoerter. Eine Empfehlung heisst
   SOLLTE, eine Pflicht MUSS.
2. Umlaute werden geschrieben: MUESSEN, DUERFEN, KOENNEN sind falsch.
3. Englische Schluesselwoerter gehoeren nicht in eine deutsche Spec.
   rltp/ ist die englische Dokumentklasse (IETF-Draft, BCP 14) und wird
   deshalb nicht geprueft, archive/ ebenfalls nicht: eingefrorene Guesse
   bleiben, wie sie waren.

Aufruf: python3 scripts/check-normative-words.py [pfad ...]
Ohne Argument wird das ganze Repository geprueft. Exit 1 bei Befunden.
"""
import re
import sys
from pathlib import Path

REGELN = [
    (re.compile(r"\bSOLL(?:EN)?\b"), "SOLL/SOLLEN ist kein Schluesselwort — SOLLTE (Empfehlung) oder MUSS (Pflicht)"),
    (re.compile(r"\b(?:MUESSEN|DUERFEN|KOENNEN|MUESSTE|DUERFTE)\b"), "Umlaut fehlt — MÜSSEN, DÜRFEN, KÖNNEN"),
    (re.compile(r"\b(?:MUST NOT|MUST|SHOULD NOT|SHOULD|SHALL NOT|SHALL|MAY|REQUIRED|OPTIONAL|RECOMMENDED)\b"),
     "englisches Schluesselwort in einer deutschen Spec — die englische Klasse ist rltp/"),
]

# Dokumente der englischen Klasse ausserhalb von rltp/: sie richten sich an
# externe Implementierer und folgen BCP 14 in englischer Form.
ENGLISCHE_DOKUMENTE = {
    "conformance/rust-hmc-checklist.md",
    "research/autonomous-pipeline.md",
}

# Ein Satz, der ueber die Woerter selbst spricht, statt eines zu benutzen.
UEBER_DIE_WOERTER = re.compile(r"nicht SOLLTE|kein Schluesselwort|Schlüsselwort")


def pruefe(pfad: Path) -> list[str]:
    befunde = []
    for nr, zeile in enumerate(pfad.read_text(encoding="utf-8").splitlines(), 1):
        if UEBER_DIE_WOERTER.search(zeile):
            continue
        for muster, grund in REGELN:
            treffer = muster.search(zeile)
            if treffer:
                befunde.append(f"{pfad}:{nr}: {treffer.group(0)} — {grund}")
    return befunde


def main() -> int:
    wurzeln = [Path(a) for a in sys.argv[1:]] or [Path(".")]
    befunde = []
    for wurzel in wurzeln:
        for pfad in sorted(wurzel.rglob("*.md")):
            if "archive" in pfad.parts or pfad.parts[0] in {"rltp", ".git"}:
                continue
            if pfad.as_posix() in ENGLISCHE_DOKUMENTE:
                continue
            befunde += pruefe(pfad)
    for zeile in befunde:
        print(zeile)
    if befunde:
        print(f"\n{len(befunde)} Befund(e). Regeln: meta/CONVENTIONS.md")
        return 1
    print("normative Woerter in Ordnung")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
