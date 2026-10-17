"""fvh.runlog — the run directory, RunMeta, and the map from a run's outcome to
fvh.records.RunRecord (DV4-PLAN §3.6; Δ149, Δ150).

A run directory research/runs/<ID>/<run-id>/ (learner-owned; written only by fvh
and scripts/mksandbox-run) holds the files of RUN_FILES:

  run.json            RunMeta
  actions.jsonl       every proposal (fvh.policies: the record format)
  observations.jsonl  their observations, and the final verification
  transcript.jsonl.gz the CLI's event stream, after the secret scan
  inputs.tar.gz       the editable inputs exactly as staged (a deterministic tar)
  inputs.sha256       one line per input, "<sha256>  <path>", sorted; the tree
                      hash (inputs_tree_sha256) is the sha256 of this file's text
  patch.diff, returned/   the returned files and their diff against the inputs
  verify.json         the final verification document
  manifest.json, selftest.json, gate.log, egress.log   the sandbox's records
  calls.jsonl         one line per model call (fvh.batch): seed, wall clock, the
                      client's usage, the window verdict, the gate's counts
  gate.log.gz, gate-counts.json   a run's model gate, compressed, and its totals
  sandbox.json        an agent run's container record (scripts/contract_local.sh)

What git tracks (Δ150, and its open item as decided here): every file of a run
directory is tracked, and the run directory as a whole is held to CAP_BYTES
(5 MB). A run over the cap keeps every file (nothing is dropped, since the
evidence is what `fvh report` re-derives from) and carries the finding
`over-cap:<bytes>`, which `fvh report` lists as a disclosure item.

RunMeta (frozen, validated like RunRecord) has DV4-PLAN §3.6's fields plus
`lang`, which the RunRecord mapping needs. Its `outcome`:

  a verdict word (fvh.records.VERDICTS)   scored: that verdict, with holes,
                                          errors and verified_count from
                                          `verify`
  "malformed"                             scored: verdict error, 0 holes,
                                          1 error, 0 verified
  "truncated:<cause>"                     scored, never re-issued: verdict
                                          inconclusive, the counts of the last
                                          verification (or 0)
  "infra-failed", "apparatus-mismatch"    not scored; re-issuable; counted per
                                          arm in the disclosure
  "replay-diverged"                       not scored (a report-time finding)
  "planned", "deferred"                   not scored

  to_run_record(meta) -> RunRecord | None
  split(metas) -> Split(records, excluded, rows)
      records   the scored RunRecords, in input order
      excluded  arm -> {outcome: count} of the unscored attempts that count
                as exclusions (infra-failed, apparatus-mismatch,
                replay-diverged); planned and deferred ids are not attempts
      rows      one Scored(record, repeat, outcome, run_id) per scored record:
                what Q12's report.LabRun(record, repeat, outcome) is built from

Frozen (guard rule 2f), standard library only.
"""

import dataclasses
import difflib
import gzip
import hashlib
import io
import json
import re
import tarfile
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

from fvh import budget
from fvh.records import VERDICTS, RunRecord

__all__ = ["CAP_BYTES", "ENDED_BY", "MODES", "OUTCOMES", "RUN_FILES", "RunMeta", "Scored",
           "Split", "cap_finding", "error_count", "hole_count", "inputs_tree_sha256",
           "load_meta", "new_run_id", "read_inputs", "run_dirs", "scored", "split",
           "to_run_record", "write_inputs", "write_meta", "write_patch"]

RUN_FILES = ("run.json", "actions.jsonl", "observations.jsonl", "transcript.jsonl.gz",
             "inputs.tar.gz", "inputs.sha256", "patch.diff", "returned", "verify.json",
             "manifest.json", "selftest.json", "gate.log", "egress.log",
             # the batch runner's (fvh.batch) and the replay's (Δ202) additions
             "calls.jsonl", "gate.log.gz", "gate-counts.json", "sandbox.json")
CAP_BYTES = 5 * 1000 * 1000
MODES = ("policy", "harness-executed", "agent")
UNSCORED = ("infra-failed", "apparatus-mismatch", "replay-diverged", "planned", "deferred")
EXCLUSIONS = ("infra-failed", "apparatus-mismatch", "replay-diverged")
OUTCOMES = (*VERDICTS, "malformed", *(f"truncated:{c}" for c in budget.TRUNCATION_CAUSES),
            *UNSCORED)
ENDED_BY = ("", "stop", "malformed", *budget.CAP_CAUSES.values(),
            *(f"truncated:{c}" for c in budget.TRUNCATION_CAUSES), "infra-failed",
            "apparatus-mismatch", "replay-diverged", "deferred", "script-end", "gate-pass")
_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.+-]*")
_SHA = re.compile(r"[0-9a-f]{64}")


def scored(outcome: str) -> bool:
    return outcome in OUTCOMES and outcome not in UNSCORED


@dataclass(frozen=True)
class RunMeta:
    """One run's record (run.json); see the module docstring."""

    run_id: str
    module: str
    arm: str
    task_id: str
    lang: str
    attempt: int
    repeat: int
    mode: str
    backend: str
    outcome: str
    lab: str = ""
    ended_by: str = ""
    verify: dict | None = None
    usage: dict = dataclasses.field(default_factory=dict)
    apparatus: dict = dataclasses.field(default_factory=dict)
    course_commit: str = ""
    course_dirty: bool = False
    inputs_sha256: str = ""
    manifest_sha256: str = ""
    selftest: dict = dataclasses.field(default_factory=dict)
    return_summary: dict = dataclasses.field(default_factory=dict)
    secret_scan: dict = dataclasses.field(default_factory=dict)
    findings: tuple = ()
    prereg_sha256: str = ""
    ledger_seq: int = 0
    started: str = ""
    ended: str = ""

    def __post_init__(self):
        for name in ("run_id", "module", "arm", "task_id", "lang", "mode", "backend",
                     "outcome", "lab", "ended_by", "course_commit", "inputs_sha256",
                     "manifest_sha256", "prereg_sha256", "started", "ended"):
            if not isinstance(getattr(self, name), str):
                raise TypeError(f"RunMeta.{name} must be a str")
        for name in ("run_id", "module", "arm", "task_id", "lang", "backend"):
            if not getattr(self, name):
                raise ValueError(f"RunMeta.{name} must not be empty")
        if not _RUN_ID.fullmatch(self.run_id):
            raise ValueError(f"RunMeta.run_id {self.run_id!r} is not a file-safe id")
        for name in ("attempt", "repeat", "ledger_seq"):
            v = getattr(self, name)
            if isinstance(v, bool) or not isinstance(v, int) or v < (0 if name == "ledger_seq" else 1):
                raise ValueError(f"RunMeta.{name} must be an int >= "
                                 f"{0 if name == 'ledger_seq' else 1}")
        if self.mode not in MODES:
            raise ValueError(f"RunMeta.mode must be one of {', '.join(MODES)}")
        if self.outcome not in OUTCOMES:
            raise ValueError(f"RunMeta.outcome {self.outcome!r} is not an outcome")
        if self.ended_by not in ENDED_BY:
            raise ValueError(f"RunMeta.ended_by {self.ended_by!r} is not an end cause")
        if not isinstance(self.course_dirty, bool):
            raise TypeError("RunMeta.course_dirty must be a bool")
        if self.verify is not None and not isinstance(self.verify, dict):
            raise TypeError("RunMeta.verify must be a dict or None")
        for name in ("usage", "apparatus", "selftest", "return_summary", "secret_scan"):
            if not isinstance(getattr(self, name), dict):
                raise TypeError(f"RunMeta.{name} must be a dict")
        object.__setattr__(self, "findings", tuple(self.findings))
        if not all(isinstance(f, str) for f in self.findings):
            raise TypeError("RunMeta.findings are strings")
        for name in ("inputs_sha256", "manifest_sha256", "prereg_sha256"):
            v = getattr(self, name)
            if v and not _SHA.fullmatch(v):
                raise ValueError(f"RunMeta.{name} must be empty or 64 lower-case hex digits")
        try:
            json.dumps(self.to_dict())
        except (TypeError, ValueError) as e:
            raise ValueError(f"RunMeta must be JSON data ({e})") from None

    def __hash__(self):
        return hash((self.run_id, self.module, self.outcome))

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["findings"] = list(self.findings)
        return d


_META_FIELDS = {f.name for f in dataclasses.fields(RunMeta)}


def write_meta(run_dir, meta: RunMeta) -> Path:
    p = Path(run_dir) / "run.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name("run.json.tmp")
    tmp.write_text(json.dumps(meta.to_dict(), sort_keys=True, indent=1, ensure_ascii=False)
                   + "\n", encoding="utf-8")
    tmp.replace(p)
    return p


def load_meta(path) -> RunMeta:
    """RunMeta from a run.json (or its run directory); ValueError naming the file."""
    p = Path(path)
    if p.is_dir():
        p = p / "run.json"
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(f"{p}: unreadable run record ({type(e).__name__})") from None
    if not isinstance(obj, dict) or not set(obj) <= _META_FIELDS:
        raise ValueError(f"{p}: a run record holds RunMeta's fields only")
    try:
        return RunMeta(**obj)
    except (TypeError, ValueError) as e:
        raise ValueError(f"{p}: {e}") from None


def run_dirs(root, module: str) -> list[Path]:
    """The module's run directories (those holding a run.json), sorted by name."""
    base = Path(root) / "research" / "runs" / module
    if not base.is_dir():
        return []
    return sorted(d for d in base.iterdir() if d.is_dir() and (d / "run.json").is_file())


def new_run_id(attempt: str, *, now: float | None = None) -> str:
    """A file-safe run id: the UTC time and the attempt id's parts."""
    t = time.gmtime(time.time() if now is None else now)
    safe = re.sub(r"[^A-Za-z0-9_.+-]+", "-", attempt).strip("-")
    return time.strftime("%Y%m%dT%H%M%SZ", t) + ("-" + safe if safe else "")


# =====================================================================================
# Inputs, patch, cap
# =====================================================================================

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inputs_tree_sha256(files: Mapping[str, bytes]) -> str:
    """The tree hash of the inputs: sha256 of inputs.sha256's text."""
    return _sha(_inputs_lines(files).encode("utf-8"))


def _inputs_lines(files):
    return "".join(f"{_sha(files[p])}  {p}\n" for p in sorted(files))


def write_inputs(run_dir, files: Mapping[str, bytes]) -> str:
    """Write inputs.tar.gz and inputs.sha256; return the tree hash."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for path in sorted(files):
            data = files[path]
            if not isinstance(data, bytes):
                raise TypeError(f"{path}: inputs are bytes")
            info = tarfile.TarInfo(path)
            info.size, info.mtime, info.mode, info.uid, info.gid = len(data), 0, 0o644, 0, 0
            info.uname = info.gname = ""
            tar.addfile(info, io.BytesIO(data))
    (run_dir / "inputs.tar.gz").write_bytes(gzip.compress(buf.getvalue(), mtime=0))
    (run_dir / "inputs.sha256").write_text(_inputs_lines(files), encoding="utf-8")
    return inputs_tree_sha256(files)


def read_inputs(run_dir) -> dict[str, bytes]:
    """The staged inputs of a run, checked against inputs.sha256 (ValueError otherwise).
    Regular files with relative paths only; anything else is refused."""
    run_dir = Path(run_dir)
    raw = gzip.decompress((run_dir / "inputs.tar.gz").read_bytes())
    out = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as tar:
        for m in tar.getmembers():
            if not m.isreg() or m.name.startswith("/") or ".." in m.name.split("/"):
                raise ValueError(f"{run_dir}/inputs.tar.gz: refused member {m.name!r}")
            f = tar.extractfile(m)
            out[m.name] = f.read() if f is not None else b""
    want = (run_dir / "inputs.sha256").read_text(encoding="utf-8")
    if _inputs_lines(out) != want:
        raise ValueError(f"{run_dir}: inputs.tar.gz does not match inputs.sha256")
    return out


def write_patch(run_dir, before: Mapping[str, str], after: Mapping[str, str]) -> int:
    """patch.diff: a git-style unified diff of `after` against `before`; returns its line count."""
    lines = []
    for path in sorted(set(before) | set(after)):
        a, b = before.get(path), after.get(path)
        if a == b:
            continue
        lines += difflib.unified_diff(
            (a or "").splitlines(keepends=True), (b or "").splitlines(keepends=True),
            fromfile=f"a/{path}" if a is not None else "/dev/null",
            tofile=f"b/{path}" if b is not None else "/dev/null")
    text = "".join(x if x.endswith("\n") else x + "\n\\ No newline at end of file\n"
                   for x in lines)
    Path(run_dir, "patch.diff").write_text(text, encoding="utf-8")
    return text.count("\n")


def cap_finding(run_dir, *, cap: int = CAP_BYTES) -> str | None:
    """"over-cap:<bytes>" when the run directory holds more than `cap` bytes."""
    total = sum(f.stat().st_size for f in Path(run_dir).rglob("*") if f.is_file()
                and not f.is_symlink())
    return f"over-cap:{total}" if total > cap else None


# =====================================================================================
# Outcome -> RunRecord
# =====================================================================================

def hole_count(doc) -> int:
    if not isinstance(doc, dict):
        return 0
    h = doc.get("holes")
    if isinstance(h, list):
        return len(h)
    return h if isinstance(h, int) and not isinstance(h, bool) and h >= 0 else 0


def error_count(doc) -> int:
    if not isinstance(doc, dict):
        return 0
    return sum(1 for d in doc.get("diagnostics") or []
               if isinstance(d, dict) and d.get("severity") == "error")


def _verified(doc) -> int:
    v = doc.get("verified_count") if isinstance(doc, dict) else None
    return v if isinstance(v, int) and not isinstance(v, bool) and v >= 0 else 0


def to_run_record(meta: RunMeta) -> RunRecord | None:
    """The RunRecord of a scored run (module docstring), or None for an unscored one."""
    o = meta.outcome
    base = dict(task_id=meta.task_id, arm=meta.arm, attempt=meta.attempt, lang=meta.lang)
    if o in VERDICTS:
        return RunRecord(**base, verdict=o, holes=hole_count(meta.verify),
                         errors=error_count(meta.verify), verified_count=_verified(meta.verify))
    if o == "malformed":
        return RunRecord(**base, verdict="error", holes=0, errors=1, verified_count=0)
    if o.startswith("truncated:"):
        return RunRecord(**base, verdict="inconclusive", holes=hole_count(meta.verify),
                         errors=error_count(meta.verify), verified_count=_verified(meta.verify))
    return None


class Scored(NamedTuple):
    record: RunRecord
    repeat: int
    outcome: str
    run_id: str


class Split(NamedTuple):
    records: tuple
    excluded: dict
    rows: tuple

    def excluded_counts(self) -> dict:
        """arm -> the number of its exclusions (what Q12's paired_table takes)."""
        return {arm: sum(c.values()) for arm, c in self.excluded.items()}


def split(metas: Iterable[RunMeta]) -> Split:
    records, rows, excluded = [], [], {}
    for m in metas:
        r = to_run_record(m)
        if r is not None:
            records.append(r)
            rows.append(Scored(r, m.repeat, m.outcome, m.run_id))
        elif m.outcome in EXCLUSIONS:
            arm = excluded.setdefault(m.arm, {})
            arm[m.outcome] = arm.get(m.outcome, 0) + 1
    return Split(tuple(records), excluded, tuple(rows))
