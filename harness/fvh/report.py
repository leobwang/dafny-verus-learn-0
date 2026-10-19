"""fvh.report — the frozen half of `fvh report` (DV4-PLAN §3.6, §4.2; §14 Q6 as
DV5 confirmed it: the analysis tables are the learner's).

  build(root, module) -> Report
      for every run directory of research/runs/<ID>/ (fvh.runlog.run_dirs):
        - re-derives the run's outcome from its logs: the staged inputs
          (inputs.tar.gz, checked against inputs.sha256), the recorded
          proposals replayed by policies.ReplayPolicy (the work copy's digests
          checked at every step) and the recorded verification results
          replayed in order (executor.LogRunner), through the same executor.
          A verdict or `malformed` must come out equal to run.json's outcome;
          an outcome from outside the run (truncated, infra-failed,
          apparatus-mismatch, deferred) must replay without divergence. A
          difference is a report finding (`replay-diverged` or `outcome
          differs`), and the run is listed as not reproduced;
        - re-checks the module's ledger chain against its anchors
          (budget.check_anchors);
        - collects the apparatus blocks, the pre-registration hashes, the
          exclusions and truncations per arm (runlog.split), the runs over
          the 5 MB cap, and whether the heads file has uncommitted changes.
  format_report(report) -> str
      the reproduction and the apparatus and disclosure block. The
      sensitivity line gives each arm's success rate with the truncated
      attempts counted as failures and with them excluded (Δ149).

  An agent-mode run (scripts/contract_local.sh's replay, or an fvh.batch agent
  arm's attempt: no actions.jsonl, the agent ran its own tool loop) is
  re-derived from its records: the staged inputs checked against
  inputs.sha256, every returned file a file the run staged, and the recorded
  verification (verify.json's gate document) equal to run.json's outcome. Its
  verification itself is repeated by --reverify (a crate task's on the crate,
  with the lab gate's lever check for a lab run, as for harness-executed runs).

  reverify(root, module, run_id, *, runner=None, mem_gb=None) -> Reverified
      `fvh report --reverify <run>` (DV4-PLAN §3.6; Docker needed): the run's
      inputs re-materialized from inputs.tar.gz (checked against
      inputs.sha256), its returned files (returned/: the final work copy of a
      harness-executed run, the changed files of an agent run) laid over
      them, and the course's gate run on the target in a fresh verification
      container, every trusted course file staged from the run's own course
      commit (`git show <course_commit>:<path>`) and, for a lab run, the lab
      gate's lever check against the task form again. The new verdict, hole
      count and verified count must equal the recorded ones (run.json's
      `verify`); a difference is a report finding. `run_id` "all" re-verifies
      every run of the module that recorded a verification.

  labalpha(root, module, *, budget=10, primary=("best", "best-raw"), ...) -> LabAlpha
      Lab alpha's tables from the logs only (DVR4 plan sections 3.1-3.3, 3.6):
      every run's first-success call T (run.json's outcome `verified` at its
      last model call, counted in calls.jsonl), its cluster (the `R12_CLUSTER:`
      line of the task's statement in the batch plans the module's batches
      copied), its class (success; policy failure, scored as no success:
      failed, malformed, inconclusive and the model-path truncations; apparatus
      failure, excluded: infra-failed, apparatus-mismatch, replay-diverged,
      killed(memory), truncated:container, truncated:host-memory,
      truncated:interrupted); per arm the share of runs solved at call 1 and never
      solved, S(b) for b = 1..B with cluster-bootstrap bands, the calls' tokens,
      GPU-seconds and wall clock, the feedback's bytes and the equal cap's
      truncation rate, the share of replies cut at the output cap (output tokens
      >= length_cap, opencode's min(num_predict, 32000)); per cluster and arm the
      AUC; and, for the primary arms, the paired sign-flip test of the cluster
      differences (fvh.stats.permutation_test), their bootstrap interval and the
      worst-case sensitivity for excluded runs (0 in the first arm, 1 in the
      second). `rejudged` (run id -> bool, from --reverify) marks successes the
      verification container reproduced; a success not marked is listed.
  format_labalpha(tables) -> str
      the same as Markdown tables

Frozen (guard rule 2f), standard library only.
"""

import json
import math
import re
import tomllib
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from fvh import budget, executor, policies, protocol, runlog, stats, tools
from fvh.records import VERDICTS

__all__ = ["APPARATUS_FAILURES", "LabAlpha", "Report", "Reverified", "RunCheck", "build",
           "format_labalpha", "format_report", "labalpha", "rederive", "reverify",
           "reverify_all"]


@dataclass(frozen=True)
class RunCheck:
    run_id: str
    recorded: str
    derived: str
    ok: bool
    detail: str = ""


@dataclass
class Report:
    module: str
    metas: list = field(default_factory=list)
    checks: list = field(default_factory=list)
    unreadable: list = field(default_factory=list)
    ledger: str = ""
    ledger_ok: bool = True
    disclosure: list = field(default_factory=list)
    split: runlog.Split | None = None

    @property
    def reproduced(self) -> bool:
        return self.ledger_ok and not self.unreadable and all(c.ok for c in self.checks)


def _returned(run_dir) -> dict:
    """{course path: bytes} of a run's returned/ files (regular files only)."""
    base = Path(run_dir) / "returned"
    out = {}
    for f in sorted(base.rglob("*")) if base.is_dir() else []:
        if f.is_symlink():
            raise ValueError(f"returned/{f.relative_to(base)} is a link")
        if f.is_file():
            out[f.relative_to(base).as_posix()] = f.read_bytes()
    return out


def _rederive_agent(run_dir, meta, staged) -> RunCheck:
    """An agent-mode run's records checked against each other (module docstring)."""
    try:
        ret = _returned(run_dir)
    except (OSError, ValueError) as e:
        return RunCheck(meta.run_id, meta.outcome, "unreadable", False, f"returned: {e}")
    extra = sorted(set(ret) - set(staged))
    if extra:
        return RunCheck(meta.run_id, meta.outcome, "unreadable", False,
                        "returned files the run never staged: " + ", ".join(extra))
    if meta.outcome not in VERDICTS:
        return RunCheck(meta.run_id, meta.outcome, meta.outcome, True,
                        "an agent run whose outcome is from outside its verification")
    try:
        doc = json.loads((run_dir / "verify.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return RunCheck(meta.run_id, meta.outcome, "unreadable", False, f"verify.json: {e}")
    gate = doc.get("gate") if isinstance(doc, dict) and "gate" in doc else doc
    derived = (gate or {}).get("verdict") if isinstance(gate, dict) else None
    derived = derived if derived in VERDICTS else "error"
    ok = derived == meta.outcome and (meta.verify is None or gate == meta.verify)
    return RunCheck(meta.run_id, meta.outcome, derived, ok,
                    "an agent run: its recorded verification agrees with run.json "
                    "(--reverify repeats it)" if ok else
                    "an agent run: verify.json's gate document differs from run.json")


def rederive(run_dir, meta: runlog.RunMeta) -> RunCheck:
    """Re-derive one run's outcome from its logs (module docstring)."""
    run_dir = Path(run_dir)
    try:
        staged = runlog.read_inputs(run_dir)
        texts = {p: b.decode("utf-8") for p, b in staged.items()}
    except (OSError, ValueError) as e:
        return RunCheck(meta.run_id, meta.outcome, "unreadable", False, f"inputs: {e}")
    if not texts:
        return RunCheck(meta.run_id, meta.outcome, "unreadable", False, "no staged inputs")
    lab_code = (meta.apparatus or {}).get("lab_code", "preserve")
    if lab_code not in ("preserve", "own"):
        raise ValueError(f"{meta.run_id}: invalid recorded lab_code {lab_code!r}")
    if meta.mode == "agent":
        return _rederive_agent(run_dir, meta, staged)
    crate = (meta.apparatus or {}).get("crate") or ""
    support = {}
    if crate:                       # a crate task: its sources editable, its companions not
        support = {p: x for p, x in texts.items()
                   if not (p.startswith(crate + "/src/") and p.endswith(".rs"))}
        texts = {p: x for p, x in texts.items() if p not in support}
        if not texts:
            return RunCheck(meta.run_id, meta.outcome, "unreadable", False,
                            "a crate run without its sources")
    paths = sorted(texts)
    target = f"{crate}/src/lib.rs" if crate and f"{crate}/src/lib.rs" in texts else paths[0]
    ctx = protocol.Context(task_id=meta.task_id, lang=meta.lang, statement="",
                           editable=tuple(paths), readable=tuple(support), target=target)
    inside = meta.outcome in VERDICTS or meta.outcome == "malformed"
    if not (run_dir / "actions.jsonl").is_file():
        if inside:
            return RunCheck(meta.run_id, meta.outcome, "unreadable", False,
                            "no actions.jsonl: a scored outcome without its proposals")
        return RunCheck(meta.run_id, meta.outcome, meta.outcome, True,
                        "an outcome from outside the run, before any proposal")
    try:
        policy = policies.ReplayPolicy(run_dir)
        gated = (meta.apparatus or {}).get("acceptance") == "gate"
        runner = executor.LogRunner(run_dir, skip_acceptance=gated)
        ex = executor.Executor(ctx, texts, runner=runner, meter=budget.Meter(),
                               replay_end=meta.ended_by or "script-end", final_verify=inside,
                               support_files=support, verify_target=crate or None,
                               acceptance=executor.ReplayAcceptance(run_dir) if gated else None)
        res = ex.run(policy)
    except tools.NoRecording as e:
        if not inside:
            # an attempt cut from outside the run (an interruption) may end between
            # a recorded proposal and its verification's record
            return RunCheck(meta.run_id, meta.outcome, meta.outcome, True,
                            f"an outcome from outside the run: its recording ends inside its "
                            f"last step ({e})")
        return RunCheck(meta.run_id, meta.outcome, "unreadable", False,
                        f"replay: {type(e).__name__}: {e}")
    except (OSError, ValueError, KeyError, TypeError) as e:
        return RunCheck(meta.run_id, meta.outcome, "unreadable", False,
                        f"logs: {type(e).__name__}: {e}")
    except Exception as e:                            # a recording that cannot be replayed
        return RunCheck(meta.run_id, meta.outcome, "unreadable", False,
                        f"replay: {type(e).__name__}: {e}")
    if res.outcome == "replay-diverged":
        return RunCheck(meta.run_id, meta.outcome, res.outcome, False, res.detail)
    if inside:
        ok = res.outcome == meta.outcome
        return RunCheck(meta.run_id, meta.outcome, res.outcome, ok,
                        "" if ok else "outcome differs from run.json")
    return RunCheck(meta.run_id, meta.outcome, meta.outcome, True,
                    "an outcome from outside the run: its proposals replay without divergence")


@dataclass(frozen=True)
class Reverified:
    run_id: str
    target: str
    recorded: tuple            # (verdict, holes, verified_count) of run.json's verify
    derived: tuple             # the same, from the fresh verification container
    ok: bool
    detail: str = ""
    document: dict | None = None


def _key(doc):
    if not isinstance(doc, dict):
        return (None, 0, 0)
    return (doc.get("verdict"), runlog.hole_count(doc),
            doc.get("verified_count") if isinstance(doc.get("verified_count"), int) else 0)


def _commit_known(root, rev) -> bool:
    try:
        p = subprocess.run(["git", "-C", str(root), "cat-file", "-e", f"{rev}^{{commit}}"],
                           capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return p.returncode == 0


def reverify(root, module: str, run_id: str, *, runner=None, mem_gb=None) -> Reverified:
    """Re-verify one run's returned files in a fresh verification container
    (module docstring). `runner` replaces the ContainerRunner (tests)."""
    root = Path(root)
    rd = root / "research" / "runs" / module / run_id
    if not (rd / "run.json").is_file():
        raise ValueError(f"no run {run_id} under research/runs/{module}/")
    meta = runlog.load_meta(rd)
    if meta.verify is None:
        return Reverified(run_id, "", _key(None), _key(None), True,
                          "the run recorded no verification: nothing to re-verify")
    staged = runlog.read_inputs(rd)
    files = dict(staged)
    files.update(_returned(rd))
    lab_task = (meta.apparatus or {}).get("lab_task") or None
    lab_code = (meta.apparatus or {}).get("lab_code", "preserve")
    if lab_code not in ("preserve", "own"):
        raise ValueError(f"{run_id}: invalid recorded lab_code {lab_code!r}")
    crate = (meta.apparatus or {}).get("crate") or ""
    if crate:
        targets = [crate]               # a crate task: the gate's target is the crate
    elif meta.mode == "agent":
        targets = sorted(staged)
    else:
        targets = [lab_task] if lab_task in files else sorted(staged)
    if len(targets) != 1:
        raise ValueError(f"{run_id}: {len(targets)} staged files; re-verification needs one "
                         "target")
    target = targets[0]
    notes = []
    verified_of = meta.verify.get("files_sha256") if isinstance(meta.verify, dict) else None
    written = (meta.return_summary or {}).get("files_sha256")
    if isinstance(verified_of, dict) and isinstance(written, dict):
        def now_of(paths):
            out = {}
            for path in paths:
                data = files.get(path)
                out[path] = None if data is None else protocol.text_sha256(
                    data.decode("utf-8", "replace") if isinstance(data, bytes) else data)
            return out
        if now_of(written) == written and now_of(verified_of) != verified_of:
            # a run cut after an edit it never verified: returned/ is what the run wrote,
            # but its recorded verdict is of an earlier work copy, so a fresh verdict of
            # returned/ compares with nothing (a returned/ changed since the run wrote it
            # is re-verified and its difference reported)
            return Reverified(run_id, target, _key(meta.verify), _key(meta.verify), True,
                              "the run's last edit was never verified: its returned files are "
                              "not the copy its verdict is of, nothing comparable (no "
                              "re-verification run)")
    rev = meta.course_commit or None
    if rev and not _commit_known(root, rev):
        raise ValueError(f"{run_id}: its course commit {rev[:12]} is not in this checkout: "
                         "fetch it, or re-verify where the run was made")
    if meta.course_dirty:
        notes.append("the run started from a checkout with uncommitted changes; its trusted "
                     "files are re-read at its commit")
    if runner is None:
        runner = tools.ContainerRunner(root, module=module, mem_gb=mem_gb, lab_task=lab_task,
                                       lab_code=lab_code, rev=rev)
    work = Path(tempfile.mkdtemp(prefix="reverify-"))
    try:
        for path, data in files.items():
            f = work / path
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(data)
        res = tools.run("vcheck --gate", work / target, root=root, runner=runner,
                        provenance="agent")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    doc = executor.verdict_doc(res)
    rec_key, new_key = _key(meta.verify), _key(doc)
    ok = rec_key == new_key
    if not ok:
        notes.append("the fresh verdict differs from the recorded one (a report finding)")
    return Reverified(run_id, target, rec_key, new_key, ok, "; ".join(notes), doc)


def reverify_all(root, module: str, **kw) -> list:
    out = []
    for d in runlog.run_dirs(root, module):
        try:
            meta = runlog.load_meta(d)
        except ValueError:
            continue
        if meta.verify is not None:
            out.append(reverify(root, module, meta.run_id, **kw))
    return out


def _heads_uncommitted(root) -> bool:
    try:
        p = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--",
                            budget.HEADS], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return p.returncode == 0 and bool(p.stdout.strip())


def build(root, module: str) -> Report:
    root = Path(root)
    rep = Report(module)
    for d in runlog.run_dirs(root, module):
        try:
            meta = runlog.load_meta(d)
        except ValueError as e:
            rep.unreadable.append(str(e))
            continue
        rep.metas.append(meta)
        rep.checks.append(rederive(d, meta))
        if any(f.startswith("over-cap:") for f in meta.findings) or runlog.cap_finding(d):
            rep.disclosure.append(f"run {meta.run_id} is over the {runlog.CAP_BYTES} B cap "
                                  "(Δ150): every file kept")
    try:
        n = budget.check_anchors(root, module)
        ledger = budget.Ledger(budget.ledger_path(root, module))
        states = {}
        for a in ledger.attempts().values():
            states[a.state] = states.get(a.state, 0) + 1
        rep.ledger = (f"ledger: {len(ledger.texts())} lines, the chain intact, {n} anchor(s) "
                      "checked; attempts " + (", ".join(f"{k} {v}" for k, v in
                                                        sorted(states.items())) or "none"))
    except (budget.AnchorError, budget.LedgerError) as e:
        rep.ledger, rep.ledger_ok = f"ledger: REFUSED: {e}", False
    if _heads_uncommitted(root):
        rep.disclosure.append(f"{budget.HEADS} has uncommitted changes: commit it after a batch")
    rep.split = runlog.split(rep.metas)
    for arm, counts in sorted(rep.split.excluded.items()):
        rep.disclosure.append(f"arm {arm}: excluded " + ", ".join(
            f"{k} {v}" for k, v in sorted(counts.items())))
    dirty = sorted(m.run_id for m in rep.metas if m.course_dirty)
    if dirty:
        rep.disclosure.append(f"{len(dirty)} run(s) started from a checkout with uncommitted "
                              "changes: " + ", ".join(dirty))
    preregs = sorted({m.prereg_sha256 for m in rep.metas if m.prereg_sha256})
    if len(preregs) > 1:
        rep.disclosure.append("the runs carry more than one pre-registration hash: "
                              + ", ".join(p[:16] for p in preregs))
    # DV5c fix round: what a lab report must not leave out
    nolever = sorted(m.run_id for m in rep.metas if m.lab and m.mode in ("harness-executed", "agent")
                     and not (m.apparatus or {}).get("lab_task"))
    if nolever:
        rep.disclosure.append(f"{len(nolever)} lab run(s) ran without the lab gate's lever "
                              "check (apparatus.lab_task empty): " + ", ".join(nolever))
    apps = sorted({(m.apparatus or {}).get("apparatus_sha256") for m in rep.metas
                   if (m.apparatus or {}).get("apparatus_sha256")})
    if len(apps) > 1:
        rep.disclosure.append("the runs ran on more than one apparatus file: "
                              + ", ".join(a[:16] for a in apps))
    held = sorted(m.run_id for m in rep.metas if (m.secret_scan or {}).get("withheld"))
    if held:
        rep.disclosure.append(f"{len(held)} run(s) had files withheld by the secret scan: "
                              + ", ".join(held))
    try:
        ledger = budget.Ledger(budget.ledger_path(root, module))
        for name, what in (("overage-stop", "an overage stop"),
                           ("apparatus-changed", "an apparatus file change")):
            n = len(ledger.notes(name))
            if n:
                rep.disclosure.append(f"the ledger records {n} {what}(s) ({name} notes)")
    except (budget.LedgerError, OSError):
        pass
    return rep


def _apparatus_lines(metas):
    seen = {}
    for m in metas:
        for fam, e in sorted((m.apparatus.get("backend") or {}).items()):
            key = (fam, e.get("version"), e.get("model"), e.get("pinned_sha256"))
            seen.setdefault(key, 0)
            seen[key] += 1
    return [f"  {fam}: version {v}, model {mod}, binary sha256 {str(sha)[:16]}… ({n} run(s))"
            for (fam, v, mod, sha), n in sorted(seen.items(), key=str)]


def format_report(rep: Report) -> str:
    out = [f"fvh report {rep.module}: {len(rep.metas)} run(s)"]
    for c in rep.checks:
        mark = "ok " if c.ok else "NOT"
        out.append(f"  [{mark}] {c.run_id}: recorded {c.recorded}, derived {c.derived}"
                   + (f" ({c.detail})" if c.detail else ""))
    for u in rep.unreadable:
        out.append(f"  [NOT] {u}")
    out.append(rep.ledger or "ledger: none")
    out.append("apparatus:")
    out += _apparatus_lines(rep.metas) or ["  (no apparatus block recorded)"]
    preregs = sorted({m.prereg_sha256 for m in rep.metas if m.prereg_sha256})
    out.append("pre-registration: " + (", ".join(preregs) if preregs else "none recorded"))
    if rep.split is not None:
        arms = sorted({r.arm for r in rep.split.records})
        out.append("sensitivity (success rate: truncated counted as failures | excluded):")
        for arm in arms:
            rows = [s for s in rep.split.rows if s.record.arm == arm]
            ok = sum(1 for s in rows if s.record.success)
            trunc = sum(1 for s in rows if s.outcome.startswith("truncated:"))
            n_all, n_ex = len(rows), len(rows) - trunc
            a = f"{ok}/{n_all}" if n_all else "-"
            b = f"{ok}/{n_ex}" if n_ex else "-"
            out.append(f"  {arm}: {a} | {b} (truncated {trunc})")
    out.append("disclosure:")
    out += [f"  - {d}" for d in rep.disclosure] or ["  - none"]
    out.append("reproduced: " + ("yes" if rep.reproduced else "NO"))
    return "\n".join(out) + "\n"



# =====================================================================================
# Lab alpha's tables (DVR4 plan section 3), from the logs only
# =====================================================================================

APPARATUS_FAILURES = ("infra-failed", "apparatus-mismatch", "replay-diverged", "killed(memory)",
                      "truncated:container", "truncated:host-memory", "truncated:interrupted",
                      "planned", "deferred")
_CLUSTER = re.compile(r"^R12_CLUSTER: (\S+)$", re.M)


@dataclass
class LabAlpha:
    module: str
    budget: int
    runs: list = field(default_factory=list)          # one dict per run
    arms: dict = field(default_factory=dict)          # arm -> per-arm summary
    clusters: dict = field(default_factory=dict)      # cluster -> {arm: AUC}
    primary: dict = field(default_factory=dict)       # the primary contrast
    findings: list = field(default_factory=list)


def _jsonl(path):
    out = []
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return out
    for line in text.splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                out.append({"unreadable": True})
    return out


def _task_clusters(root, module):
    """{task id: cluster} from the statements of every batch plan the module copied."""
    out = {}
    base = Path(root) / "research" / "runs" / module / "batches"
    for f in sorted(base.glob("*.toml")) if base.is_dir() else []:
        try:
            data = tomllib.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for tid, entry in (data.get("task") or {}).items():
            m = _CLUSTER.search(entry.get("statement", "") if isinstance(entry, dict) else "")
            if m:
                out.setdefault(tid, m.group(1))
    return out


def _run_row(d, meta, clusters, budget_, length_cap=32000):
    calls = _jsonl(d / "calls.jsonl")
    outcome = meta.outcome
    if outcome == "verified":
        cls, t = "success", len(calls)
    elif outcome in APPARATUS_FAILURES:
        cls, t = "apparatus", None
    else:
        cls, t = "failure", None
    fb = [c for c in calls if "feedback_bytes" in c]
    gates = [c.get("gate") or {} for c in calls]
    return {"run_id": meta.run_id, "arm": meta.arm, "task": meta.task_id, "lang": meta.lang,
            "repeat": meta.repeat, "outcome": outcome, "class": cls,
            "first_success": t if (t is not None and t >= 1) else None,
            "cluster": clusters.get(meta.task_id), "calls": len(calls),
            # the gate's token counts in a call record are the run's running totals
            # (fvh.batch.RecordingTransport); its GPU-seconds are per call
            "prompt_tokens": max((int(g.get("prompt_tokens") or 0) for g in gates), default=0),
            "gate_output_tokens": max((int(g.get("output_tokens") or 0) for g in gates), default=0),
            "gpu_s": round(sum(float(g.get("gpu_s") or 0.0) for g in gates), 3),
            "wall_s": round(sum(float(c.get("wall_s") or 0.0) for c in calls), 3),
            "client_out": sum(int((c.get("client_usage") or {}).get("output_tokens") or 0)
                              for c in calls),
            "feedback_calls": len(fb),
            "feedback_bytes": sum(int(c["feedback_bytes"]) for c in fb),
            "feedback_truncated": sum(1 for c in fb if c.get("feedback_truncated")),
            "gate_refusals": sum(1 for g in gates if g.get("capped")),
            # a reply that reached the output cap (opencode sends max_tokens =
            # min(num_predict, 32000)) was cut there: the num_predict truncation
            "length_cut": sum(1 for c in calls if int((c.get("client_usage") or {})
                                                      .get("output_tokens") or 0) >= length_cap),
            "call_errors": sum(1 for c in calls if c.get("error")),
            # model calls that produced no candidate: the replies the hint grammar
            # rejected (fvh.labalpha's failed nodes) and calls that ended in an error
            "failed_nodes": max(0, len(calls) - _candidates(d))}


def _candidates(d):
    """The candidates a run verified: its proposals that hold an edit."""
    n = 0
    for rec in _jsonl(d / "actions.jsonl"):
        if any(isinstance(a, dict) and a.get("type") == "edit" for a in rec.get("actions") or []):
            n += 1
    return n


def labalpha(root, module: str, *, budget: int = 10, primary=("best", "best-raw"),
             n_permutations: int = 10_000, n_resamples: int = 10_000, seed: int = 20261018,
             confidence: float = 0.95, rejudged=None, length_cap: int = 32000) -> LabAlpha:
    """Lab alpha's tables (module docstring). Deterministic: the same logs and seed give
    the same tables."""
    root = Path(root)
    out = LabAlpha(module, budget)
    clusters = _task_clusters(root, module)
    for d in runlog.run_dirs(root, module):
        try:
            meta = runlog.load_meta(d)
        except ValueError as e:
            out.findings.append(f"unreadable run: {e}")
            continue
        row = _run_row(d, meta, clusters, budget, length_cap)
        if row["cluster"] is None:
            out.findings.append(f"run {meta.run_id}: task {meta.task_id} has no R12_CLUSTER line "
                                "in the module's batch plans")
        if row["class"] == "success" and row["first_success"] is None:
            out.findings.append(f"run {meta.run_id}: verified with no recorded model call")
        if row["class"] == "success" and rejudged is not None and not rejudged.get(meta.run_id):
            out.findings.append(f"run {meta.run_id}: a success not re-judged in the "
                                "verification container")
        out.runs.append(row)
    runs = [r for r in out.runs if r["cluster"] is not None]
    for arm in sorted({r["arm"] for r in runs}):
        rs = [r for r in runs if r["arm"] == arm]
        kept = [r for r in rs if r["class"] != "apparatus"]
        by_c = {}
        for r in kept:
            by_c.setdefault(r["cluster"], []).append(r["first_success"])
        curves = {c: stats.success_curve(ts, budget) for c, ts in sorted(by_c.items())}
        aucs = {c: stats.auc_budget(ts, budget) for c, ts in sorted(by_c.items())}
        for c, a in aucs.items():
            out.clusters.setdefault(c, {})[arm] = a
        mean_curve = [math.fsum(v[b] for v in curves.values()) / len(curves)
                      for b in range(budget)] if curves else []
        bands = stats.cluster_bootstrap_ci(list(curves.values()), n_resamples=n_resamples,
                                           confidence=confidence, seed=seed) if curves else []
        fbc = sum(r["feedback_calls"] for r in rs)
        calls = sum(r["calls"] for r in rs)
        out.arms[arm] = {
            "runs": len(rs), "kept": len(kept), "excluded": len(rs) - len(kept),
            "clusters": len(curves),
            "solved_at_call_1": (sum(1 for r in kept if r["first_success"] == 1) / len(kept))
            if kept else None,
            "never_solved": (sum(1 for r in kept if r["first_success"] is None) / len(kept))
            if kept else None,
            "solved_by_B": (sum(1 for r in kept if r["first_success"] is not None
                                and r["first_success"] <= budget) / len(kept)) if kept else None,
            "auc_mean_over_clusters": (math.fsum(aucs.values()) / len(aucs)) if aucs else None,
            "curve": mean_curve, "bands": bands,
            "calls": calls, "failed_nodes": sum(r["failed_nodes"] for r in rs),
            "call_errors": sum(r["call_errors"] for r in rs),
            "prompt_tokens": sum(r["prompt_tokens"] for r in rs),
            "output_tokens": sum(r["client_out"] for r in rs),
            "gpu_s": round(sum(r["gpu_s"] for r in rs), 3),
            "wall_s": round(sum(r["wall_s"] for r in rs), 3),
            "feedback_calls": fbc,
            "feedback_bytes_mean": (sum(r["feedback_bytes"] for r in rs) / fbc) if fbc else None,
            "feedback_truncation_rate": (sum(r["feedback_truncated"] for r in rs) / fbc)
            if fbc else None,
            "length_cut_rate": (sum(r["length_cut"] for r in rs) / calls) if calls else None,
            "gate_refusals": sum(r["gate_refusals"] for r in rs),
            "outcomes": dict(sorted(_count_by(rs, "outcome").items()))}
    a, b = primary
    both = sorted(c for c, v in out.clusters.items() if a in v and b in v)
    if both:
        x = [out.clusters[c][a] for c in both]
        y = [out.clusters[c][b] for c in both]
        d = [p - q for p, q in zip(x, y)]
        res = {"arms": [a, b], "clusters": len(both), "theta": math.fsum(d) / len(d)}
        res["p_value"] = stats.permutation_test(x, y, paired=True, n_permutations=n_permutations,
                                                seed=seed)
        res["ci"] = stats.cluster_bootstrap_ci(d, n_resamples=n_resamples,
                                               confidence=confidence, seed=seed)
        # worst case for the claim: an excluded run scores 0 in arm a and 1 in arm b
        worst = []
        for c in both:
            vals = {}
            for arm, fill in ((a, None), (b, 1)):
                ts = [r["first_success"] if r["class"] != "apparatus" else fill
                      for r in runs if r["arm"] == arm and r["cluster"] == c]
                vals[arm] = stats.auc_budget(ts, budget)
            worst.append(vals[a] - vals[b])
        res["theta_worst_case"] = math.fsum(worst) / len(worst)
        out.primary = res
    return out


def _count_by(rows, key):
    out = {}
    for r in rows:
        out[r[key]] = out.get(r[key], 0) + 1
    return out


def _f(v, nd=3):
    return "n/a" if v is None else (f"{v:.{nd}f}" if isinstance(v, float) else str(v))


def format_labalpha(t: LabAlpha) -> str:
    """Lab alpha's tables as Markdown (every number from labalpha())."""
    lines = [f"# {t.module} Lab alpha tables (from the logs; B = {t.budget})", "",
             "| arm | runs | excluded | clusters | solved at call 1 | never solved | solved by B "
             "| AUC (mean over clusters) | calls | failed nodes | GPU-s | wall s | feedback B/call "
             "| cap truncation | output-cap cut |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for arm, s_ in t.arms.items():
        lines.append(f"| {arm} | {s_['runs']} | {s_['excluded']} | {s_['clusters']} | "
                     f"{_f(s_['solved_at_call_1'])} | {_f(s_['never_solved'])} | "
                     f"{_f(s_['solved_by_B'])} | {_f(s_['auc_mean_over_clusters'])} | "
                     f"{s_['calls']} | {s_['failed_nodes']} | {_f(s_['gpu_s'], 1)} | "
                     f"{_f(s_['wall_s'], 1)} | {_f(s_['feedback_bytes_mean'], 0)} | "
                     f"{_f(s_['feedback_truncation_rate'])} | {_f(s_['length_cut_rate'])} |")
    lines += ["", "## S(b) per arm (mean over clusters, cluster-bootstrap band)", "",
              "| arm | " + " | ".join(f"b={b}" for b in range(1, t.budget + 1)) + " |",
              "|---|" + "---|" * t.budget]
    for arm, s_ in t.arms.items():
        cells = [f"{v:.2f} [{lo:.2f}, {hi:.2f}]" for v, (lo, hi) in zip(s_["curve"], s_["bands"])]
        lines.append(f"| {arm} | " + " | ".join(cells) + " |")
    arms = sorted(t.arms)
    lines += ["", "## AUC per cluster and arm", "", "| cluster | " + " | ".join(arms) + " |",
              "|---|" + "---|" * len(arms)]
    for c in sorted(t.clusters):
        lines.append(f"| {c} | " + " | ".join(_f(t.clusters[c].get(a)) for a in arms) + " |")
    if t.primary:
        p = t.primary
        lines += ["", "## Primary contrast", "",
                  f"theta = mean over {p['clusters']} clusters of AUC({p['arms'][0]}) - "
                  f"AUC({p['arms'][1]}) = {p['theta']:.4f}; 95 % cluster-bootstrap interval "
                  f"[{p['ci'][0]:.4f}, {p['ci'][1]:.4f}]; paired sign-flip p = "
                  f"{p['p_value']:.4f}; worst-case theta for excluded runs = "
                  f"{p['theta_worst_case']:.4f}"]
    if t.findings:
        lines += ["", "## Findings", ""] + [f"- {x}" for x in t.findings]
    return "\n".join(lines) + "\n"
