"""CONTRACT
goal: implement this file to the INTERFACE block below its header: a command-line tool that reads `scripts/vcheck --json` and `scripts/vaudit --json` documents and prints one JSON object per file with its hole count by kind, its assumption findings by kind and its verdict, taken from the documents only
allowed-files:
  - tools/Q12/holecount.py
acceptance:
  - re-run `python3 tools/Q12/test_holecount.py` after every edit; never stack unverified edits
  - `python3 tools/Q12/test_holecount.py` exits 0
  - the tool reads documents only: it runs no verifier or course tool, starts no process, and never opens or scans a source file; every count it prints comes from a document's own fields
  - the standard library only; no file is written
"""
# Q12 — the toolwright (rung 10; `/contract Q12`; QPLAN §22.4)
#
# This file is the contract's only allowed file. It ships with no code: the
# contractor writes all of it, to the interface you write below.
#
# Before the run (you, about 8 minutes):
#   1. Write the INTERFACE block below: the input (one or more documents, as
#      `scripts/vcheck --json` and `scripts/vaudit --json` print them, read
#      from files named on the command line or from standard input; say
#      which), the output (one JSON object per file the documents are about,
#      with the hole count by kind, the assumption findings by kind and the
#      verdict), what it does with a document it cannot read, and its exit
#      codes.
#   2. Write the acceptance tests tools/Q12/test_holecount.py (standard
#      library `unittest`, run as `python3 tools/Q12/test_holecount.py`)
#      over fixtures you copy from earlier modules' recorded documents (for
#      example under harness/tests/q/fixtures/), each with the expected
#      object written out. The tests are yours, outside the contract: the
#      contractor never edits them.
#   3. Commit both, then run `/contract Q12` in a fresh session.
#
# After the run (about 7 minutes): run the tool on two documents the tests do
# not contain; audit its source (does it count from the source text? does it
# read a missing key as zero?); fill the AUDIT block at the end.

# INTERFACE (the reference's own; a learner's INTERFACE may differ, and the contract is
# satisfiable against any reasonable one: DV6 fix round, spec §12.1's twin rule)
#   input: one or more JSON files named on the command line, or one document on standard
#     input when none is named; each holds one `scripts/vcheck --json` or `scripts/vaudit
#     --json` document, bare or as the course's recorded fixtures wrap it (an object with
#     "instrument" and "document", harness/tests/q/fixtures/)
#   output: one JSON object per line, one per document target (the document's "target"),
#     sorted by target: {"file": <target>, "holes": {<kind>: <n>}, "hole_count": <n>,
#     "findings": {<kind>: <n>}, "verdict": <vcheck's verdict, or null with no vcheck
#     document>}; the holes and the verdict come from vcheck documents, the findings from
#     vaudit documents (the assumption audit), each counted from the document's own list
#   unreadable input: a file that is not JSON, or a document that is neither form (a vcheck
#     document lacks its "verdict" string or its "holes" list; a vaudit document its
#     "findings" list; either its "target"), is named on standard error and contributes
#     nothing: a missing key is never read as zero
#   exit codes: 0 every input read; 1 an input was unreadable (the others still printed);
#     2 usage

import json
import sys
from collections import Counter


class Unreadable(Exception):
    pass


def unwrap(obj):
    """The document itself: a recorded fixture's "document", or the object as it is."""
    if isinstance(obj, dict) and "instrument" in obj and isinstance(obj.get("document"), dict):
        return obj["document"]
    return obj


def classify(doc):
    """("vcheck" | "vaudit", target) of a document, or Unreadable."""
    if not isinstance(doc, dict):
        raise Unreadable("not a JSON object")
    target = doc.get("target")
    if not isinstance(target, str) or not target:
        raise Unreadable("no target")
    if "verdict" in doc or "holes" in doc:
        if not isinstance(doc.get("verdict"), str) or not isinstance(doc.get("holes"), list):
            raise Unreadable("a vcheck document without its verdict or its holes list")
        return "vcheck", target
    if isinstance(doc.get("findings"), list):
        return "vaudit", target
    raise Unreadable("neither a vcheck nor a vaudit document")


def kinds(items, what):
    out = Counter()
    for x in items:
        if not isinstance(x, dict) or not isinstance(x.get("kind"), str):
            raise Unreadable(f"a {what} entry without its kind")
        out[x["kind"]] += 1
    return out


def summarize(docs):
    """{target: object} over (name, document) pairs; [(name, why)] for the unreadable."""
    rows, bad = {}, []
    for name, raw in docs:
        try:
            doc = unwrap(raw)
            kind, target = classify(doc)
            row = rows.setdefault(target, {"file": target, "holes": Counter(),
                                           "findings": Counter(), "verdict": None})
            if kind == "vcheck":
                row["holes"] += kinds(doc["holes"], "hole")
                row["verdict"] = doc["verdict"]
            else:
                row["findings"] += kinds(doc["findings"], "finding")
        except Unreadable as e:
            bad.append((name, str(e)))
    out = []
    for target in sorted(rows):
        r = rows[target]
        out.append({"file": target, "holes": dict(sorted(r["holes"].items())),
                    "hole_count": sum(r["holes"].values()),
                    "findings": dict(sorted(r["findings"].items())), "verdict": r["verdict"]})
    return out, bad


def read_inputs(paths, stdin):
    docs, bad = [], []
    if not paths:
        try:
            docs.append(("<stdin>", json.loads(stdin.read())))
        except ValueError:
            bad.append(("<stdin>", "not JSON"))
        return docs, bad
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                docs.append((p, json.load(f)))
        except (OSError, ValueError, UnicodeDecodeError) as e:
            bad.append((p, "cannot be read as JSON" if isinstance(e, ValueError) else str(e)))
    return docs, bad


def main(argv=None, stdin=None, stdout=None, stderr=None):
    argv = sys.argv[1:] if argv is None else argv
    stdin, stdout, stderr = stdin or sys.stdin, stdout or sys.stdout, stderr or sys.stderr
    if any(a.startswith("-") and a != "-" for a in argv):
        print("usage: holecount.py [DOCUMENT.json ...]   (none: one document on stdin)",
              file=stderr)
        return 2
    docs, bad = read_inputs([a for a in argv if a != "-"], stdin)
    rows, bad2 = summarize(docs)
    for r in rows:
        print(json.dumps(r, sort_keys=True), file=stdout)
    for name, why in bad + bad2:
        print(f"holecount: {name}: {why}", file=stderr)
    return 1 if bad or bad2 else 0


if __name__ == "__main__":
    sys.exit(main())
