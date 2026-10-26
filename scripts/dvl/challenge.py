#!/usr/bin/env python3
"""dvl.challenge — the library of scripts/challenge_gate.sh (QPLAN §31.1, §31.5;
spec §2.3.8; design §7.6; DELTAS Δ402).

    scripts/challenge_gate.sh <ID> [--json] [--no-record] [--root R]
    scripts/challenge_gate.sh --abandon <ID> [--no-record] [--root R]

The gate of a solo challenge module (Q19-Q33). It reads the module's registry
record and its frozen statement manifest `Challenges/<Topic>/<ID>_<Name>/<ID>_Statement.toml`
(rule 2f by its name; listed in the record's `statements`), runs each check below
once, prints one line per check, and on PASS or DISTINCTION appends the gradebook's
`challenge` row (the only writer of that row: CORE.md). It never edits a learner file.

  1 statements    every `statements[]` file's working copy and committed blob have
                  the pinned sha256 (no PENDING); each [[against]] pair passes
                  `scripts/specfreeze --against`; each [interface] Python file's
                  signatures hash as pinned (dvl.python.spec_hash)
  2 holes         per language: Dafny and Verus from `scripts/vcheck --gate --json`
                  (the tool's own hole list), Python from dvl.python.holes; any hole fails
  3 audit         `scripts/vaudit --json` on every Dafny and Verus target; a finding
                  fails unless it is a trust leap the module's TRUST.md table lists
                  (design item 5)
  4 trust-leap    dvl.trustleap.diff over the module's files and its TRUST.md table,
                  both ways
  5 seeds         `scripts/vcheck --brittleness --json` (Dafny with --solvers when the
                  manifest asks): every seed's verdict verified. The label printed and
                  recorded is fixed: "solver diversity and seed variation: not
                  independent checking" (spec §11.5 item 2); Verus adds "one solver"
  6 reach         dvl.reach.scan with the manifest's [reach] table
  7 completeness  every gate document complete (verdict, holes, verified_count present)
                  and verified_count at or above the manifest's minimum; the widest
                  seed-sweep CV printed, and gating only when the manifest says so
  8 harness       (review_bar = "harness") every Python file's frozen acceptance tests
                  through dvl.python.check(gate=True), and the grader record
                  research/runs/<ID>/grader/result.json the grader container's modes
                  write (QPLAN §31.3); without it the stage fails

The manifest (TOML, schema 1):

    schema = 1
    module = "Q31"
    trust = "research/TRUST.md"          # the learner's ledger; its "## Q31" table
    solver_swap = true                   # Dafny targets: the bundled solvers too
    cv_gates = false
    distinction = "grader"               # "grader" (the grader record decides) | "none"
    [min_verified]                       # target -> minimum verified count
    "Challenges/Agentic/Q31_GateBench/Q31_GateBench.dfy" = 8
    [[against]]                          # specfreeze --against <statement> <file>
    statement = "Challenges/Agentic/Q31_GateBench/Q31_GateBenchStatement.dfy"
    file = "Challenges/Agentic/Q31_GateBench/Q31_GateBench.dfy"
    [interface."agents/q31_gate_bench/gate.py"]
    "gate_task" = "<sha256 of its signature>"
    [reach]                              # dvl.reach's table
    deny_names = []

Exit: 0 PASS or DISTINCTION · 1 FAIL · 2 usage · 3 refused (a planned module: nothing
to gate; a broken record or manifest) · 137/143 a tool killed by memory, recorded as
killed(memory), never a verdict (CLAUDE.md §Resources). Standard library only; every
solver job runs through the wrappers (dvl.common.run_capped), one at a time; the course
applies no memory management of its own (Δ503: the memory is the host's).
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from dvl import reach as RE  # noqa: E402
from dvl import trustleap as TL  # noqa: E402

LABEL = "solver diversity and seed variation: not independent checking"
CHECKS = ("statements", "holes", "audit", "trust-leap", "seeds", "reach", "completeness",
          "harness")
KILLED = (137, 143)
RETRO_HEADINGS = ("## What I attempted", "## Where it broke",
                  "## What the next attempt would change", "## Hours spent")
MANIFEST_KEYS = {"schema", "module", "trust", "solver_swap", "cv_gates", "distinction",
                 "min_verified", "against", "interface", "reach"}


class Refused(Exception):
    pass


class Killed(Exception):
    def __init__(self, code, what):
        super().__init__(what)
        self.code = code


@dataclass
class Report:
    module: str
    lines: list = field(default_factory=list)      # (check, ok, detail)
    word: str = "FAIL"
    manifest_sha: str = ""
    gate_sha: str = ""
    assisted: int = 0
    labels: list = field(default_factory=list)

    def add(self, check, problems, detail=""):
        self.lines.append((check, not problems, detail if not problems else "; ".join(problems)))

    @property
    def passed(self):
        return all(ok for _, ok, _ in self.lines)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(p):
    return sha256_bytes(Path(p).read_bytes())


class Tools:
    """The instruments, as subprocesses of the course's own wrappers. Tests replace it."""

    def __init__(self, root):
        self.root = Path(root)

    def _run(self, argv):
        p = subprocess.run(argv, cwd=self.root, capture_output=True, text=True)
        if p.returncode in KILLED:
            raise Killed(p.returncode, " ".join(argv[:3]))
        return p.returncode, p.stdout

    def json_doc(self, argv):
        code, out = self._run(argv)
        try:
            return code, json.loads(out)
        except json.JSONDecodeError:
            return code, None

    def vcheck_gate(self, target):
        return self.json_doc([str(self.root / "scripts/vcheck"), "--json", "--gate", target])

    def vaudit(self, target):
        return self.json_doc([str(self.root / "scripts/vaudit"), "--json", target])

    def brittleness(self, target, solvers):
        argv = [str(self.root / "scripts/vcheck"), "--json", "--brittleness"]
        return self.json_doc(argv + (["--solvers"] if solvers else []) + [target])

    def specfreeze_against(self, statement, target):
        code, _ = self._run([str(self.root / "scripts/specfreeze"), "--against", statement, target])
        return code

    def committed_blob(self, rel):
        p = subprocess.run(["git", "-C", str(self.root), "show", f"HEAD:{rel}"],
                           capture_output=True)
        return p.stdout if p.returncode == 0 else None

    def python_holes(self, rel):
        from dvl import python as PY
        return [h.label for h in PY.holes(self.root / rel, root=self.root)]

    def python_check(self, rel):
        from dvl import python as PY
        return PY.check(self.root / rel, gate=True, root=self.root).verdict

    def spec_hash(self, rel, symbols):
        from dvl import python as PY
        return PY.spec_hash(self.root / rel, symbols)


# --------------------------------------------------------------------------------------
# The record and the manifest
# --------------------------------------------------------------------------------------

def load_record(root, mid):
    import check_course_map as ccm
    data, err = ccm.load_registry(Path(root))
    if err:
        raise Refused(f"the module registry is unusable: {err}")
    rec = next((m for m in data.get("module", []) if isinstance(m, dict)
                and str(m.get("id", "")).upper() == mid.upper()), None)
    if rec is None:
        raise Refused(f"{mid}: no such module")
    if rec.get("tier") != "challenge":
        raise Refused(f"{rec['id']}: not a challenge module (Q19-Q33); its done gate is vcheck --gate")
    return rec


def manifest_path(rec):
    rx = re.compile(rf"Challenges/[A-Za-z]+/{rec['id']}_[A-Za-z0-9]+/{rec['id']}_Statement\.toml")
    found = [s["path"] for s in rec.get("statements", []) if isinstance(s, dict)
             and isinstance(s.get("path"), str) and rx.fullmatch(s["path"])]
    if len(found) != 1:
        raise Refused(f"{rec['id']}: statements must list exactly one manifest "
                      f"Challenges/<Topic>/{rec['id']}_<Name>/{rec['id']}_Statement.toml")
    return found[0]


def load_manifest(root, rel, mid):
    try:
        m = tomllib.loads((Path(root) / rel).read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise Refused(f"{rel}: {e}") from None
    if m.get("schema") != 1 or m.get("module") != mid:
        raise Refused(f"{rel}: schema must be 1 and module {mid!r}")
    extra = set(m) - MANIFEST_KEYS
    if extra:
        raise Refused(f"{rel}: unknown key(s) {', '.join(sorted(extra))}")
    r = m.get("reach", {})
    if not isinstance(r, dict) or set(r) - set(RE.KEYS) or not all(
            isinstance(v, list) and all(isinstance(x, str) and x for x in v) for v in r.values()):
        raise Refused(f"{rel}: [reach] holds only {', '.join(RE.KEYS)}, each a list of names")
    if m.get("distinction", "none") not in ("grader", "none"):
        raise Refused(f"{rel}: distinction is 'grader' or 'none'")
    return m


def targets(rec):
    """(dafny files, verus crate dirs, python files) the gate verifies."""
    d, v, py = [], [], []
    for p in rec.get("exercises", []):
        if p.endswith(".dfy") and "Statement" not in Path(p).name:
            d.append(p)
        elif p.endswith("/src/lib.rs"):
            v.append(p[:-len("/src/lib.rs")])
    py = [p for p in rec.get("harness", []) if p.endswith(".py")]
    return d, v, py


def source_files(root, rec):
    d, v, _ = targets(rec)
    out = list(d)
    for crate in v:
        out += sorted(p.relative_to(root).as_posix() for p in (Path(root) / crate / "src").rglob("*.rs"))
    return out


def assisted_depth(root, mid):
    """The largest hint-depth of the module's tutor lines in the ledger (CORE.md)."""
    p = Path(root) / "instructor" / "ledger.md"
    if not p.is_file():
        return 0
    best = 0
    for line in p.read_text(encoding="utf-8").split("\n"):
        if f"tag: {mid}/" in line and "source: tutor" in line:
            m = re.search(r"hint-depth:\s*(\d)", line)
            if m:
                best = max(best, int(m.group(1)))
    return best


# --------------------------------------------------------------------------------------
# The checks
# --------------------------------------------------------------------------------------

def check_statements(root, rec, man, tools):
    probs = []
    for s in rec.get("statements", []):
        path, pin = s.get("path"), s.get("sha256")
        if pin == "PENDING":
            probs.append(f"{path}: pinned PENDING")
            continue
        f = Path(root) / path
        if not f.is_file():
            probs.append(f"{path}: missing")
            continue
        if sha256_file(f) != pin:
            probs.append(f"{path}: the working copy differs from its pin")
        blob = tools.committed_blob(path)
        if blob is None or sha256_bytes(blob) != pin:
            probs.append(f"{path}: the committed blob differs from its pin (commit the frozen file as shipped)")
    for a in man.get("against", []):
        if tools.specfreeze_against(a["statement"], a["file"]) != 0:
            probs.append(f"{a['file']}: its statements differ from {a['statement']} (specfreeze --against)")
    for rel, pins in (man.get("interface") or {}).items():
        try:
            got = tools.spec_hash(rel, list(pins))
        except Exception as e:  # an unreadable or unparsable file is a failed check
            probs.append(f"{rel}: its interface cannot be read ({type(e).__name__})")
            continue
        for sym, want in pins.items():
            if got.get(sym) != want:
                probs.append(f"{rel}: {sym}'s signature differs from the frozen interface")
    return probs


def run_checks(root, rec, man, tools, report):
    d, v, py = targets(rec)
    gate_docs, probs_holes, probs_complete, counts = {}, [], [], {"dafny": 0, "verus": 0, "python": 0}
    for t in d + v:
        code, doc = tools.vcheck_gate(t)
        gate_docs[t] = doc
        lang = "dafny" if t in d else "verus"
        if not isinstance(doc, dict) or not {"verdict", "holes", "verified_count"} <= set(doc):
            probs_complete.append(f"{t}: the gate document is incomplete")
            continue
        counts[lang] += len(doc["holes"])
        if doc["verdict"] != "verified" or code != 0:
            probs_holes.append(f"{t}: {doc['verdict']}")
        need = (man.get("min_verified") or {}).get(t, 1)
        if doc["verified_count"] < need:
            probs_complete.append(f"{t}: verified {doc['verified_count']}, below the minimum {need}")
    for p in py:
        counts["python"] += len(tools.python_holes(p))
    holes = [f"{k} {n}" for k, n in counts.items() if n]
    report.add("holes", holes + probs_holes,
               f"dafny {counts['dafny']} · verus {counts['verus']} · python {counts['python']}")

    files = source_files(root, rec)
    leaps = TL.scan(files, root)
    try:
        entries = TL.read_trust(Path(root) / man.get("trust", "research/TRUST.md"), rec["id"]) \
            if (Path(root) / man.get("trust", "research/TRUST.md")).is_file() else []
    except TL.TrustError as e:
        entries, leap_probs = [], [str(e)]
    else:
        leap_probs = TL.diff(leaps, entries)
    listed = {(lp.file, lp.line) for lp in leaps
              if (lp.file, lp.symbol, lp.construct) in {(e.file, e.symbol, e.construct) for e in entries}}
    audit_probs = []
    for t in d + v:
        _, doc = tools.vaudit(t)
        if not isinstance(doc, dict) or "findings" not in doc:
            audit_probs.append(f"{t}: the audit did not complete")
            continue
        for f in doc["findings"]:
            loc = (_rel(root, f.get("file", "")), f.get("line"))
            if loc not in listed:
                audit_probs.append(f"{loc[0]}:{loc[1]}: {f.get('kind', 'finding')}")
    report.add("audit", audit_probs, f"{len(d) + len(v)} target(s) clean")
    report.add("trust-leap", leap_probs, f"{len(leaps)} leap(s), all listed")

    seed_probs, widest = [], None
    for t in d + v:
        solvers = bool(man.get("solver_swap")) and t in d
        _, doc = tools.brittleness(t, solvers)
        if not isinstance(doc, dict) or "verdicts" not in doc:
            seed_probs.append(f"{t}: the seed sweep did not complete")
            continue
        if not doc.get("stable") or any(x != "verified" for x in doc["verdicts"].values()):
            seed_probs.append(f"{t}: not stable across seeds{' and solvers' if solvers else ''}")
        for s in doc.get("spread", []):
            if s.get("cv") is not None:
                widest = s["cv"] if widest is None else max(widest, s["cv"])
        if man.get("cv_gates") and doc.get("flagged"):
            seed_probs.append(f"{t}: a resource spread above the pinned CV")
    report.labels = [LABEL] + (["verus: one solver"] if v else [])
    report.add("seeds", seed_probs, LABEL)

    report.add("reach", RE.scan(files, man.get("reach") or {}, root), "clean")
    report.add("completeness", probs_complete,
               "complete" + (f"; widest CV {widest:.3f}" if widest is not None else ""))

    if rec.get("review_bar") == "harness":
        h = []
        for p in py:
            verdict = tools.python_check(p)
            if verdict != "verified":
                h.append(f"{p}: {verdict}")
        g = Path(root) / "research" / "runs" / rec["id"] / "grader" / "result.json"
        grader = None
        if not g.is_file():
            h.append("no grader record (research/runs/<ID>/grader/result.json, QPLAN §31.3)")
        else:
            try:
                grader = json.loads(g.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                h.append("the grader record does not parse")
            else:
                if grader.get("module") != rec["id"] or grader.get("word") not in ("PASS", "DISTINCTION", "FAIL"):
                    h.append("the grader record names another module or no word")
                elif grader["word"] == "FAIL":
                    h.append("the grader record says FAIL")
        report.add("harness", h, "frozen tests and grader record")
        return grader
    return None


def _rel(root, p):
    try:
        return Path(p).resolve().relative_to(Path(root).resolve()).as_posix()
    except (ValueError, OSError):
        return str(p)


def gate(root, mid, tools=None):
    root = Path(root)
    tools = tools or Tools(root)
    rec = load_record(root, mid)
    if rec.get("status") == "planned":
        raise Refused(f"{rec['id']} is planned: nothing to gate")
    mrel = manifest_path(rec)
    man = load_manifest(root, mrel, rec["id"])
    rep = Report(rec["id"], manifest_sha=sha256_file(root / mrel),
                 gate_sha=sha256_file(Path(__file__)), assisted=assisted_depth(root, rec["id"]))
    rep.add("statements", check_statements(root, rec, man, tools), "pinned and committed")
    grader = run_checks(root, rec, man, tools, rep)
    if rep.passed:
        rep.word = "DISTINCTION" if (man.get("distinction") == "grader" and grader
                                     and grader.get("word") == "DISTINCTION") else "PASS"
    return rep


def gradebook_row(rep, today=None):
    today = today or datetime.date.today().isoformat()
    parts = [rep.word, f"manifest {rep.manifest_sha[:16]}", f"gate {rep.gate_sha[:16]}",
             "seeds 1-3", *rep.labels]
    if rep.assisted:
        parts.append(f"assisted (max hint-depth {rep.assisted})")
    return f"| {today} | {rep.module} | challenge | {'; '.join(parts)} | — |"


def append_row(root, row):
    p = Path(root) / "instructor" / "gradebook.md"
    text = p.read_text(encoding="utf-8")
    p.write_text(text.rstrip("\n") + "\n" + row + "\n", encoding="utf-8")


def abandon(root, mid):
    rec = load_record(root, mid)
    if rec.get("status") == "planned":
        raise Refused(f"{rec['id']} is planned: nothing to abandon")
    p = Path(root) / "research" / f"{rec['id'].lower()}_retrospective.md"
    if not p.is_file():
        raise Refused(f"{p.relative_to(root)}: write the retrospective first")
    text = p.read_text(encoding="utf-8")
    missing = [h for h in RETRO_HEADINGS if not re.search(rf"^{re.escape(h)}\s*$", text, re.M)]
    bodies = re.split(r"^## .*$", text, flags=re.M)[1:]
    if missing or len(bodies) < len(RETRO_HEADINGS) or any(len(b.split()) < 15 for b in bodies[:4]):
        raise Refused(f"{p.relative_to(root)}: it needs the four sections "
                      f"({', '.join(RETRO_HEADINGS)}), each of 15 words or more")
    return rec["id"], f"abandoned (retrospective {sha256_file(p)[:16]})"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="challenge_gate.sh", allow_abbrev=False)
    ap.add_argument("module")
    ap.add_argument("--abandon", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-record", action="store_true")
    ap.add_argument("--root", default=str(_SCRIPTS.parent))
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    try:
        if a.abandon:
            mid, grade = abandon(root, a.module)
            row = f"| {datetime.date.today().isoformat()} | {mid} | challenge | {grade} | — |"
            if not a.no_record:
                append_row(root, row)
            print(f"challenge: {mid} {grade} (not a pass)")
            return 0
        rep = gate(root, a.module)
    except Refused as e:
        print(f"challenge_gate: refused: {e}", file=sys.stderr)
        return 3
    except Killed as e:
        print(f"challenge_gate: killed(memory) in {e}: no verdict", file=sys.stderr)
        return e.code
    if a.json:
        print(json.dumps({"module": rep.module, "word": rep.word, "labels": rep.labels,
                          "checks": [{"check": c, "ok": ok, "detail": d} for c, ok, d in rep.lines],
                          "manifest_sha256": rep.manifest_sha, "gate_sha256": rep.gate_sha,
                          "assisted": rep.assisted}, indent=1))
    else:
        for c, ok, d in rep.lines:
            print(f"{c:13s} {'ok  ' if ok else 'FAIL'} {d}")
        print(f"challenge: {rep.module} {rep.word}")
    if rep.word != "FAIL" and not a.no_record:
        append_row(root, gradebook_row(rep))
    return 0 if rep.word != "FAIL" else 1


if __name__ == "__main__":
    sys.exit(main())
