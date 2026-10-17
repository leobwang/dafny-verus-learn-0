"""fvh.judging — `fvh report <ID> --judge RUN|all`: every lab run's delivered task
file re-judged against the lab's sealed reference in the grader container
(QPLAN §25.5-§25.6, §30 Q49; DV4-PLAN §5.9).

  judge(root, module, which="all", *, archive, mem_gb=None, runner=None) -> list[Judged]
      For each run of research/runs/<ID>/ (fvh.runlog.run_dirs; `which` one
      run id or "all") whose apparatus names a lab card's task form
      (`lab_task`, bench/local/<q|r>/<lab>/<card>/tasks/<card>.<ext>): the
      delivered file is the run's returned copy of the task form
      (returned/<lab_task>), else its staged input. The files are written to a
      scratch directory, one judging spec per language, and each spec goes to
      `scripts/mksandbox-run --truth <archive> --truth-check judge --judge
      <spec>` (`archive` must be the one the module's sandbox/truth.toml row
      pins: the command line names it on purpose, as mksandbox-run's truth
      mode does, so that guard rule 1c refuses the judging run in a study
      session: the learner runs the grader themselves; one container per
      language; nothing of the hidden truth reaches the host:
      the grader prints a verdict word and outcome words per candidate). A
      run whose apparatus names no lab card is not judged (listed with the
      reason), nor is a run whose outcome is unscored or an exclusion
      (fvh.runlog.UNSCORED, EXCLUSIONS: listed with excluded=True and never
      counted). `runner(argv) -> (exit code, stdout)` replaces the subprocess
      (tests).

The verdicts are the frozen reference oracles' (faithful, weak, strong,
vacuous, undecided; `mismatch` when the delivery changed the declaration's
signature, `context` when its definitions do not verify alone): the hidden
verdicts the learner's oracle verdicts are compared with (the confusion
matrix and κ of the pre-registration). They are printed, never written into a
run directory (its files are the run's record).

Frozen (guard rule 2f), standard library only.
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path

from fvh import runlog

__all__ = ["Judged", "judge", "LAB_TASK"]

LAB_TASK = re.compile(r"bench/local/[qr]/[a-z0-9]+/([a-z0-9][a-z0-9-]{0,63})/tasks/\1\.(dfy|rs)")
LANG = {"dfy": "dafny", "rs": "verus"}


@dataclass(frozen=True)
class Judged:
    run_id: str
    card: str
    verdict: str          # a grader verdict word, or "" when not judged
    detail: str = ""      # the outcome words, or why the run was not judged
    excluded: bool = False  # an unscored or excluded outcome: never judged, never counted


def _archive(root, module, named):
    try:
        data = tomllib.loads((Path(root) / "sandbox" / "truth.toml").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(f"sandbox/truth.toml is unreadable ({type(e).__name__})") from None
    rows = [r for r in data.get("lab", []) if isinstance(r, dict) and r.get("id") == module]
    if len(rows) != 1 or not isinstance(rows[0].get("archive"), str):
        raise ValueError(f"no sealed archive of {module} is pinned in sandbox/truth.toml")
    if named != rows[0]["archive"]:
        raise ValueError(f"--truth names {named!r}, not the archive sandbox/truth.toml pins for "
                         f"{module}")
    return rows[0]["archive"]


def _default_runner(root):
    def run(argv):
        p = subprocess.run([sys.executable, "-B", str(Path(root) / "scripts" / "mksandbox-run")]
                           + argv, cwd=root, capture_output=True, text=True, timeout=6 * 3600)
        return p.returncode, p.stdout
    return run


def judge(root, module: str, which: str = "all", *, archive: str, mem_gb=None,
          runner=None) -> list:
    root = Path(root)
    archive = _archive(root, module, archive)
    out, pending = [], {}
    for d in runlog.run_dirs(root, module):
        try:
            meta = runlog.load_meta(d)
        except ValueError:
            continue
        if which != "all" and meta.run_id != which:
            continue
        if meta.outcome in runlog.UNSCORED or meta.outcome in runlog.EXCLUSIONS:
            out.append(Judged(meta.run_id, "", "", f"excluded outcome {meta.outcome}: not judged",
                              excluded=True))       # never reaches the analysis (DV5d fix)
            continue
        task = (meta.apparatus or {}).get("lab_task") or ""
        m = LAB_TASK.fullmatch(task)
        if not m:
            out.append(Judged(meta.run_id, "", "", "not a lab card's run (no lab_task)"))
            continue
        ret = d / "returned" / task
        if ret.is_file() and not ret.is_symlink():
            data = ret.read_bytes()
        else:
            data = runlog.read_inputs(d).get(task)
        if data is None:
            out.append(Judged(meta.run_id, m.group(1), "", "the run holds no copy of its task file"))
            continue
        pending.setdefault(LANG[m.group(2)], []).append((meta.run_id, m.group(1), m.group(2), data))
    if which != "all" and not out and not pending:
        raise ValueError(f"no run {which} under research/runs/{module}/")
    run = runner or _default_runner(root)
    tmp = Path(tempfile.mkdtemp(prefix="fvh-judge-"))
    try:
        for lang, items in sorted(pending.items()):
            cands = []
            for k, (rid, card, ext, data) in enumerate(items):
                f = tmp / f"{lang}-{k:04d}.{ext}"
                f.write_bytes(data)
                cands.append({"id": rid, "card": card, "file": str(f)})
            spec = tmp / f"{lang}.json"
            spec.write_text(json.dumps({"candidates": cands}), encoding="utf-8")
            argv = ["--truth", archive, "--truth-check", "judge", "--judge", str(spec)]
            if mem_gb is not None:
                argv += ["--mem-gb", f"{float(mem_gb):g}"]
            code, stdout = run(argv)
            doc = None
            for line in (stdout or "").splitlines():
                line = line.strip()
                if line.startswith("{"):
                    try:
                        doc = json.loads(line)
                    except ValueError:
                        doc = None
            rows = {r.get("id"): r for r in (doc or {}).get("judged", []) if isinstance(r, dict)}
            for rid, card, _, _ in items:
                r = rows.get(rid)
                if r is None:
                    why = (doc or {}).get("error") or f"the judging run ended with exit {code}"
                    out.append(Judged(rid, card, "", str(why)))
                    continue
                words = ", ".join(f"{k} {r[k]}" for k in ("base", "spec_implies_ref",
                                                          "ref_implies_spec", "vacuity")
                                  if isinstance(r.get(k), str))
                out.append(Judged(rid, card, str(r.get("verdict", "")), words))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out
