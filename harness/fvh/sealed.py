"""fvh.sealed — the sealed run: one fvh batch inside the run's agent container, for the
learner's sealed challenge arm and for the course's frozen par agent beside it
(QPLAN §31.3, §32.5; DELTAS Δ418's design, Δ419 as built; the user's D68, D102, D103).

A challenge's sealed part is unsealed once, by the learner, into a directory outside the
course tree (`python -m fvh unseal <ID> --part P --once --into DIR`; research/
unseals.jsonl records it). Its tasks are then run only here, in one apparatus (D102):
the dvl-agent image's own opencode as the Qwen transport, the run's own Route C model
gate (the relay on 127.0.0.1:8000 in the container, the gate container, the host gate,
upstream the host's model server as found, Δ505), and every Verify in the same
container. Two routes, one form:

  python -m fvh run <ID> --plan PLAN --sealed P --unsealed DIR
      the learner's arm(s): the plan's batch is opened (and later closed) in the
      module's ledger on the host as for any batch; its attempts run in the container
      (`scripts/mksandbox-run --sealed-run SPEC`, whose one command is the image's
      /opt/dvl/bin/batchrun), and the run directories come back into research/runs/
      <ID>/<run id>/, each settling its ledger id. The learner's records are whole:
      their prompts and transcripts are theirs.
  python -m fvh par <ID> --truth ARCHIVE --sealed P --unsealed DIR --plan PLAN [--beside ARM]
      the course's par agent (the sealed part `par-agent` of sandbox/truth.toml: its
      policy package and a frozen fvh plan fragment, labs/<ID>/par/, no task) on the same
      unsealed part, at the learner's plan's base seed and the B, repeats and attempts of
      the arm it runs beside (`scripts/mksandbox-run --truth ARCHIVE --truth-check par-run
      --par SPEC`: the image's grader `truthcheck par-run`, the one grader mode on the model
      network). For a Q32 tranche the census of Δ412 runs first: the course's one-shot
      baseline's first sample on every task (the fragment's [census] arm); a task it
      closes is dropped from the analysis and counted, never replaced, and par does not
      run on it. Par's calls are reserved in the module's ledger first (a `par` line,
      fvh.budget) and count in its budget.
      The return is counts only (D103): each par run comes back into research/runs/<ID>/
      par-<part>-<run id>/ as run.json with the outcome, the verification, the call
      counts and the verified files (inputs.tar.gz, inputs.sha256, returned/) and nothing
      else, no transcript, call log, proposal, observation or gate log, and no field that
      reveals par's prompts (prompt hashes, the policy's name and source digest, the plan's
      digest): counts_only() is that filter, applied in the container and again here, on
      the return path. `fvh report --reverify` re-verifies par's claimed successes like
      the learner's.

Both routes check the unsealed directory against its research/unseals.jsonl entry
(unsealed_part: its file count and files_sha256) before anything is staged, run attempts
in chunks of container runs (a container's wall clock is at most 4 h, so a run starts no
attempt it cannot finish and the next chunk takes the ids left), give every chunk's gate
the seeds the plan pre-registers for its ids (the gate's seed_pool: a request runs only on
one of them, each once) and a call cap of their rounds, and hold the GPU calendar lock
for the whole route.

Inside the container (inside(), from batchrun and from truthcheck's par child): the
batch is fvh.batch's own, with a scratch ledger under /work/grader/runs/, the
transport above (container_transport), the in-container runner (SealedRunner, which
runs each instrument from /work, as truthcheck gate-agree does) and the host's apparatus
facts with the transport's (D102: `transport.binary` the image's opencode,
`transport.pinned_by` the image digest), so a sealed record says which apparatus ran it.

Frozen (guard rule 2f), standard library only. This file names the agent CLI and the
container route: scripts/check_single_route.py's allowlist lists it.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from fvh import apparatus, backends, batch, budget, runlog, statements, tools

__all__ = ["CENSUS_ARM", "COUNTS_ONLY_APPARATUS", "COUNTS_ONLY_FILES", "PAR_ARM", "PAR_PART",
           "SealedRefused", "SealedRunner", "UnsealedPart", "counts_only", "inside",
           "par_plan_text", "part_tasks", "run_par", "run_sealed", "unsealed_part"]

ROOT = Path(__file__).resolve().parents[2]
PAR_PART = "par-agent"          # sandbox/truth.toml's part of a module's par agent
PAR_ARM = "par"                 # par's arm in its plan and its records
CENSUS_ARM = "census"           # the Δ412 census's arm (Q32's tranches)
GRADER = "grader"               # the run's writable /work/grader (dvl.sandbox GRADER_DIR)
GRADER_IN = "grader-in"         # the host's inline inputs
SPEC = f"{GRADER_IN}/spec.json"
PLAN = f"{GRADER_IN}/plan.toml"
APPARATUS = f"{GRADER_IN}/apparatus.toml"
RUNS = "runs"                   # /work/grader/runs/: the run's one returned directory
RELAY_URL = "http://127.0.0.1:8000/v1"           # the container's relay (Route C; Δ505)
IMAGE_OPENCODE = "/opt/dvl/agent/opencode"       # dvl.sandbox.OPENCODE
GATE_VIEW = "/run/dvl/gate/gate-counts.json"     # the host gate's running counts, read-only
WALL_S = 4 * 3600               # a container's wall clock (dvl.sandbox's [limits] bound)
MARGIN_S = 900                  # what a chunk keeps for its return stream and removal
CENSUS_MODULES = ("Q32",)       # Δ412: the one-shot leg of Q32's tranche admission
PART_RX = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,31}")
MKSANDBOX = "scripts/mksandbox-run"

# D103's return path: what a par run brings back. Everything else of its run directory
# stays in the container; run.json is rewritten from these fields only.
COUNTS_ONLY_FILES = ("run.json", "inputs.tar.gz", "inputs.sha256")
COUNTS_ONLY_DIRS = ("returned",)
COUNTS_ONLY_META = ("run_id", "module", "arm", "task_id", "lang", "attempt", "repeat", "mode",
                    "backend", "outcome", "lab", "ended_by", "verify", "usage", "apparatus",
                    "course_commit", "course_dirty", "inputs_sha256", "return_summary",
                    "secret_scan", "findings", "prereg_sha256", "started", "ended")
COUNTS_ONLY_APPARATUS = ("apparatus_sha256", "course_commit", "course_dirty", "fvh_tree",
                         "fvh_dirty", "model_gate", "pins", "model_server_found", "seeds",
                         "instrument", "lab_task", "acceptance", "lab_code", "feedback",
                         "statements_sha256", "gate", "gate_sha256", "crate", "transport",
                         "counts_only", "par")
COUNTS_ONLY_USAGE = ("calls", "client_calls", "input_tokens", "output_tokens", "turns", "wall_s",
                     "gpu_s", "outputs", "gate_calls", "gate_prompt_tokens", "gate_output_tokens",
                     "gate_gpu_s", "gate_reasoning_tokens")
FINDING = re.compile(r"(ctx-saturated|unattributed-calls|over-cap|secret-scan|runner-killed)"
                     r"(:[A-Za-z0-9_.-]{0,40})?")


class SealedRefused(RuntimeError):
    """A sealed run or par run cannot start (exit 3 at the command line)."""


def _say(log):
    return log or (lambda m: print(f"fvh: {m}", flush=True))


# =====================================================================================
# The unsealed part (host)
# =====================================================================================

@dataclass(frozen=True)
class UnsealedPart:
    module: str
    part: str
    stratum: str                # the stratum's course directory
    files: dict                 # course path -> bytes
    entry: dict                 # its research/unseals.jsonl entry
    cards: tuple = ()

    @property
    def files_sha256(self) -> str:
        return self.entry.get("files_sha256", "")


def _read_stratum(root, rel):
    try:
        return tomllib.loads((Path(root) / rel).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        raise SealedRefused(f"{rel}: unreadable") from None


def unsealed_part(root, module, part, into) -> UnsealedPart:
    """The learner's single-use unsealed copy of `part` (module docstring), checked
    against its research/unseals.jsonl entry: every file a regular file under a card of
    the stratum, as many as the entry wrote and with its files_sha256. SealedRefused."""
    root = Path(root)
    if not isinstance(part, str) or not PART_RX.fullmatch(part):
        raise SealedRefused(f"part {part!r} is not a part name")
    try:
        ledger = statements.unseal_ledger(root)
    except statements.StatementsRefused as e:
        raise SealedRefused(str(e)) from None
    mine = [e for e in ledger if e.get("module") == module and e.get("part") == part]
    if not mine:
        raise SealedRefused(f"part {part} of {module} was never unsealed ({statements.LEDGER} "
                            f"has no entry): `python -m fvh unseal {module} --part {part}` first")
    entry = mine[-1]
    st_rel = str(entry.get("stratum", ""))
    if not re.fullmatch(r"bench/local/[qr]/(agentic/)?[a-z0-9][a-z0-9-]*/STRATUM\.toml", st_rel):
        raise SealedRefused(f"{statements.LEDGER} seq {entry.get('seq')}: no stratum")
    meta = _read_stratum(root, st_rel)
    if meta.get("module") != module or meta.get("part") != part \
            or meta.get("archive_sha256") != entry.get("archive_sha256"):
        raise SealedRefused(f"{st_rel} is not the stratum {statements.LEDGER} seq "
                            f"{entry.get('seq')} unsealed (module, part, archive_sha256)")
    want = entry.get("files_sha256")
    if not isinstance(want, str) or not re.fullmatch(r"[0-9a-f]{64}", want):
        raise SealedRefused(f"{statements.LEDGER} seq {entry.get('seq')} records no files_sha256 "
                            "(an unseal from before Δ419): the part cannot be checked, and a "
                            "part is single use; ask the author for a new seal")
    d = Path(into).expanduser()
    try:
        d = d.resolve(strict=True)
    except OSError:
        raise SealedRefused(f"{into}: no such directory (the --into of the part's unseal)") \
            from None
    if not d.is_dir():
        raise SealedRefused(f"{into} is not a directory")
    try:
        d.relative_to(root.resolve())
        raise SealedRefused(f"{into} lies inside the course tree: a single-use part never does")
    except ValueError:
        pass
    cards = {c.get("id") for c in meta.get("card", []) if isinstance(c, dict)}
    got = {}
    for p in sorted(d.rglob("*")):
        rel = p.relative_to(d).as_posix()
        if p.is_symlink():
            raise SealedRefused(f"{into}/{rel} is a link: an unsealed part holds files only")
        if p.is_dir():
            continue
        if not p.is_file():
            raise SealedRefused(f"{into}/{rel} is not a regular file")
        parts = rel.split("/")
        if len(parts) < 3 or parts[1] != "tasks" or parts[0] not in cards:
            raise SealedRefused(f"{into}/{rel} is not a task file of a card of {st_rel}")
        got[rel] = p.read_bytes()
    if len(got) != entry.get("files") or statements.tree_sha256(got) != want:
        raise SealedRefused(f"{into} is not the part {statements.LEDGER} seq {entry.get('seq')} "
                            f"wrote ({len(got)} files here, {entry.get('files')} written; or "
                            "a file differs): stage the part exactly as it was unsealed")
    stratum = str(PurePosixPath(st_rel).parent)
    return UnsealedPart(module, part, stratum, {f"{stratum}/{k}": v for k, v in got.items()},
                        dict(entry), tuple(sorted({k.split("/", 1)[0] for k in got})))


def part_tasks(up: UnsealedPart) -> dict:
    """{card id: course path} of an unsealed part's tasks: a card's one task file, or its
    tasks directory when it holds a crate (Cargo.toml)."""
    out = {}
    for card in up.cards:
        base = f"{up.stratum}/{card}/tasks"
        mine = sorted(k for k in up.files if k.startswith(base + "/"))
        if f"{base}/Cargo.toml" in up.files:
            out[card] = base
            continue
        forms = [k for k in mine if k.count("/") == base.count("/") + 1
                 and k.endswith((".dfy", ".rs"))]
        if len(forms) != 1:
            raise SealedRefused(f"card {card} of {up.stratum} has {len(forms)} task files, not one")
        out[card] = forms[0]
    return out


# =====================================================================================
# The spec and the launch (host)
# =====================================================================================

def _registry(root, module):
    try:
        data = tomllib.loads((Path(root) / "MODULES.toml").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise SealedRefused(f"the registry is unusable ({type(e).__name__})") from None
    for m in data.get("module", []):
        if isinstance(m, dict) and m.get("id") == module:
            if m.get("status") == "planned":
                raise SealedRefused(f"{module} is planned: not authored yet")
            if not m.get("solo"):
                raise SealedRefused(f"{module} is not a challenge module: a sealed run runs a "
                                    "challenge's sealed part")
            return m
    raise SealedRefused(f"module {module!r} is not in MODULES.toml")


def _apparatus_check(app, root):
    """The apparatus drift a sealed route refuses on: every pin but the host's Qwen
    transport (D102: the sealed arm runs the image's opencode, which images.lock pins
    through pins.images_lock_sha256)."""
    drift = [d for d in apparatus.check(app, root) if not d.field.startswith("backend.")]
    if drift:
        raise SealedRefused("apparatus drift: " + "; ".join(d.line() for d in drift))


def _server(app):
    from fvh.backends import gate as G
    try:
        return G.discover(app)
    except G.GateError as e:
        raise SealedRefused(f"no model server: {e}") from None


def _spec_base(root, module, kind, up, app, found, *, ids, seed_pool, calls, prereg, stmts,
               plan_sha256):
    facts = apparatus.collect(app, root)
    facts["model_server_found"] = found
    return {"schema": 1, "kind": kind, "module": module, "part": up.part,
            "stratum": up.stratum, "files_sha256": up.files_sha256, "ids": list(ids),
            "seed_pool": sorted(seed_pool), "calls": int(calls), "prereg_sha256": prereg or "",
            "statements_sha256": dict(stmts or {}), "facts": facts,
            "course": apparatus.git_facts(root), "server": found, "model": found["model"],
            "max_model_len": found.get("max_model_len"),
            "options": dict(app.model_gate().get("options") or {}),
            "apparatus_text": Path(app.path).read_text(encoding="utf-8"),
            "plan_sha256": plan_sha256, "deadline_s": WALL_S - MARGIN_S}


def default_launch(root, spec, records, *, archive=None, mem_gb=None, calendar_fd=None,
                   log=None):
    """Run one chunk through scripts/mksandbox-run (the one route that starts a container,
    guard rule 1f): --sealed-run SPEC, or --truth ARCHIVE --truth-check par-run --par SPEC.
    Returns its exit code; the records (run.json, grader/runs/...) are in `records`."""
    say = _say(log)
    root = Path(root)
    fd, sp = tempfile.mkstemp(prefix="fvh-sealed-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump({**spec, "unsealed": str(spec["unsealed"])}, fh)
        argv = [sys.executable, "-B", str(root / MKSANDBOX), "--records", str(records)]
        argv += (["--truth", archive, "--truth-check", "par-run", "--par", sp] if archive
                 else ["--sealed-run", sp])
        if mem_gb is not None:
            argv += ["--mem-gb", f"{float(mem_gb):g}"]
        if calendar_fd is not None:
            argv += ["--calendar-fd", str(calendar_fd)]
        p = subprocess.run(argv, cwd=root, stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           pass_fds=(calendar_fd,) if calendar_fd is not None else (),
                           timeout=WALL_S + 1800)
        for line in (p.stderr or "").strip().splitlines()[-12:]:
            say(line)
        if archive:                      # the grader's verdict line: counts only (D103)
            for line in (p.stdout or "").strip().splitlines()[-1:]:
                say(f"par-run: {line}")
        return p.returncode
    finally:
        os.unlink(sp)


def _calendar():
    from fvh.backends import gate as G
    return G.GpuCalendar()


# =====================================================================================
# The return path (host)
# =====================================================================================

def _keys_of(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from _keys_of(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _keys_of(v)


def counts_only(meta: dict, *, part: str, archive_sha256: str) -> dict:
    """D103's run.json of a par run: COUNTS_ONLY_META's fields, the apparatus held to
    COUNTS_ONLY_APPARATUS (never the prompt hashes, the policy's name or source digest,
    the plan's digest or the calls' records), the usage to its counts, the findings to
    their fixed words; marked counts_only, with par's part and sealed archive. The result
    loads as a RunMeta (ValueError otherwise)."""
    if not isinstance(meta, dict):
        raise ValueError("a run record is a JSON object")
    out = {k: meta[k] for k in COUNTS_ONLY_META if k in meta}
    app = meta.get("apparatus") if isinstance(meta.get("apparatus"), dict) else {}
    app = {k: app[k] for k in COUNTS_ONLY_APPARATUS if k in app}
    app["counts_only"] = True
    app["par"] = {"part": part, "archive_sha256": archive_sha256}
    out["apparatus"] = app
    use = meta.get("usage") if isinstance(meta.get("usage"), dict) else {}
    out["usage"] = {k: use[k] for k in COUNTS_ONLY_USAGE
                    if isinstance(use.get(k), (int, float)) and not isinstance(use.get(k), bool)}
    out["findings"] = sorted({f for f in meta.get("findings") or ()
                              if isinstance(f, str) and FINDING.fullmatch(f)})
    rs = meta.get("return_summary") if isinstance(meta.get("return_summary"), dict) else {}
    out["return_summary"] = {"files_sha256": dict(rs.get("files_sha256") or {})} \
        if isinstance(rs.get("files_sha256"), dict) else {}
    sc = meta.get("secret_scan") if isinstance(meta.get("secret_scan"), dict) else {}
    out["secret_scan"] = {k: sc[k] for k in ("withheld", "hits", "scanned") if k in sc}
    out["manifest_sha256"], out["selftest"], out["ledger_seq"] = "", {}, 0
    rm = runlog.RunMeta(**out)            # it must still be a run record
    return rm.to_dict()


def _copy_tree(src: Path, dest: Path, allowed=None):
    """Copy the regular files of src into dest (no link, nothing outside it); with
    `allowed` (top-level files, top-level dirs) only those."""
    files, dirs = allowed if allowed else ((), ())
    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src)
        if p.is_symlink() or not (p.is_file() or p.is_dir()):
            continue
        if allowed and not ((len(rel.parts) == 1 and rel.parts[0] in files and p.is_file())
                            or (rel.parts[0] in dirs)):
            continue
        t = dest / rel
        if p.is_dir():
            t.mkdir(parents=True, exist_ok=True)
            continue
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_bytes(p.read_bytes())


def returned_runs(records) -> list:
    """(run dir, RunMeta) of every run directory a chunk returned (grader/runs/<id>/
    holding a run.json that loads), in name order; the others are skipped."""
    base = Path(records) / GRADER / RUNS
    out = []
    for d in sorted(base.iterdir()) if base.is_dir() else []:
        if d.is_symlink() or not d.is_dir() or not (d / "run.json").is_file():
            continue
        try:
            out.append((d, runlog.load_meta(d)))
        except ValueError:
            continue
    return out


def import_par(root, module, d: Path, *, part, archive_sha256) -> Path:
    """One par run directory into research/runs/<ID>/par-<part>-<run id>/, counts only
    (D103): run.json rewritten by counts_only, then inputs.tar.gz, inputs.sha256 and
    returned/ and nothing else. Returns the new directory."""
    meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
    rec = counts_only(meta, part=part, archive_sha256=archive_sha256)
    name = re.sub(r"[^A-Za-z0-9_.+-]+", "-", f"par-{part}-{rec['run_id']}")
    dest = Path(root) / "research" / "runs" / module / name
    if dest.exists():
        raise SealedRefused(f"research/runs/{module}/{name} exists already")
    dest.mkdir(parents=True)
    _copy_tree(d, dest, allowed=(tuple(f for f in COUNTS_ONLY_FILES if f != "run.json"),
                                 COUNTS_ONLY_DIRS))
    (dest / "run.json").write_text(json.dumps(rec, sort_keys=True, indent=1, ensure_ascii=False)
                                   + "\n", encoding="utf-8")
    return dest


def _save_sandbox_record(root, module, records, name):
    """The chunk's container record (mksandbox-run's run.json) under research/runs/<ID>/
    sealed/, its gate log left out (the run's counts stay)."""
    src = Path(records) / "run.json"
    if not src.is_file():
        return None
    try:
        rec = json.loads(src.read_text(encoding="utf-8"))
    except ValueError:
        return None
    gate = rec.get("gate") if isinstance(rec.get("gate"), dict) else {}
    rec["gate"] = {k: v for k, v in gate.items() if k != "gate.log"}
    dest = Path(root) / "research" / "runs" / module / "sealed" / f"{name}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(rec, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    return dest


# =====================================================================================
# The learner's arm (host): python -m fvh run <ID> --plan PLAN --sealed P --unsealed DIR
# =====================================================================================

class _NoTransport:
    """Batch.open() builds no transport: the attempts run in the container."""

    def __call__(self, *a, **k):
        raise SealedRefused("a sealed batch's attempts run in its container")


def _check_plan(plan, up):
    for t, (rel, _lang) in plan.tasks.items():
        if not rel.startswith(up.stratum + "/"):
            raise SealedRefused(f"task {t} ({rel}) is not a task of part {up.part} "
                                f"({up.stratum}/): a sealed batch runs its part's tasks only")
    for a in plan.arms:
        if a.agent:
            raise SealedRefused(f"arm {a.name}: an agent-mode arm cannot run in a sealed run's "
                                "container (it would need a container of its own)")
        if a.family != budget.QWEN:
            raise SealedRefused(f"arm {a.name}: a challenge has no Claude arm (D66)")
        if a.name in (PAR_ARM, CENSUS_ARM):
            raise SealedRefused(f"arm {a.name}: the names {PAR_ARM} and {CENSUS_ARM} are par's")


def run_sealed(root, module, plan_path, part, into, *, mem_gb=None, log=None, launch=None,
               app=None, found=None, calendar=None) -> int:
    """The learner's sealed arm (module docstring). Exit: 0 every id settled and the batch
    closed, 1 ids left re-issuable, 3 refused or stopped (the batch stays open)."""
    say = _say(log)
    root = Path(root)
    _registry(root, module)
    up = unsealed_part(root, module, part, into)
    try:
        plan = batch.load_plan(plan_path, root, tasks_at={up.stratum: Path(into).expanduser()})
    except batch.BatchError as e:
        raise SealedRefused(str(e)) from None
    _check_plan(plan, up)
    if app is None:
        try:
            app = apparatus.load(root=root)
        except apparatus.ApparatusError as e:
            raise SealedRefused(str(e)) from None
        _apparatus_check(app, root)
    try:
        budget.check_anchors(root, module)
    except (budget.AnchorError, budget.LedgerError) as e:
        raise SealedRefused(str(e)) from None
    ledger = budget.Ledger(budget.ledger_path(root, module))
    last = budget.last_anchor(root, module)
    note = batch.batch_note(ledger) if last is not None and last["event"] == "open" else None
    if note is not None:
        mine = [n for n in ledger.notes("sealed-run") if n.get("batch") == note.get("batch")]
        if note.get("plan_sha256") != plan.sha256 or not mine or mine[-1].get("part") != part \
                or mine[-1].get("files_sha256") != up.files_sha256:
            raise SealedRefused(f"{module}'s open batch is not this sealed run (its plan, part "
                                "or unsealed files differ): settle it first")
        prereg, stmts = note.get("prereg_sha256") or "", note.get("statements_sha256") or {}
        say(f"{module}: continuing the open sealed batch {note.get('batch')}")
    else:
        if last is not None and last["event"] == "open":
            raise SealedRefused(f"{module}'s last batch is still open: resume it (fvh resume)")
        if not found:
            try:
                backends.refuse_if_disabled()
            except backends.ModelDisabled as e:
                raise SealedRefused(str(e)) from None
        b = batch.Batch(root, module, plan, transports=_NoTransport(), log=say, app=app)
        b.sealed_route = True
        try:
            n = b.open()
        except batch.BatchError as e:
            raise SealedRefused(str(e)) from None
        ledger = b.ledger
        note = batch.batch_note(ledger)
        ledger.append({"kind": "note", "note": "sealed-run", "batch": note.get("batch"),
                       "part": part, "stratum": up.stratum, "files_sha256": up.files_sha256,
                       "plan_sha256": plan.sha256})
        prereg, stmts = b.prereg, b.statements
        say(f"{module}: sealed batch opened ({n} attempt(s) planned and anchored)")
    batch.reconcile(root, module, ledger, plan, log=say)
    if found is None:
        found = _server(app)
    launch = launch or (lambda spec, rec, fd: default_launch(root, spec, rec, mem_gb=mem_gb,
                                                             calendar_fd=fd, log=say))
    plan_text = Path(plan_path).read_text(encoding="utf-8")
    cal = calendar if calendar is not None else _calendar()
    try:
        cal.__enter__()
    except backends.Deferred as e:
        raise SealedRefused(f"deferred: {e}") from None
    k = 0
    try:
        while True:
            ids = budget.resume_order(ledger, max_reissue=plan.max_reissue)
            if not ids:
                break
            k += 1
            pool = [s for aid in ids for s in plan.seeds(aid)]
            calls = sum(plan.arm(aid.split("/")[0]).rounds for aid in ids)
            spec = _spec_base(root, module, "sealed-run", up, app, found, ids=ids,
                              seed_pool=pool, calls=calls, prereg=prereg, stmts=stmts,
                              plan_sha256=plan.sha256)
            spec.update(plan_text=plan_text, unsealed=str(Path(into).expanduser().resolve()))
            recs = Path(tempfile.mkdtemp(prefix="fvh-sealed-records-"))
            try:
                fh = getattr(cal, "fh", None)
                code = launch(spec, recs, fh.fileno() if fh is not None else None)
                bid = note.get("batch", "b")
                _save_sandbox_record(root, module, recs, f"{bid}-{part}-{k:02d}")
                moved = _settle(root, module, ledger, plan, recs, set(ids), say)
            finally:
                shutil.rmtree(recs, ignore_errors=True)
            say(f"chunk {k}: container exit {code}; {moved} of {len(ids)} id(s) came back")
            if not moved:
                say("no id came back from the last container run: the batch stays open "
                    "(run the same line again once the cause is fixed)")
                return 3
    finally:
        cal.__exit__(None, None, None)
    left = budget.resume_order(ledger, max_reissue=plan.max_reissue)
    if left:
        say(f"{len(left)} id(s) left: the batch stays open")
        return 1
    budget.close_batch(root, module, course_commit=apparatus.git_facts(root)["course_commit"])
    say("every id is settled: the sealed batch is closed (commit research/)")
    return 0


def _settle(root, module, ledger, plan, recs, sent, say) -> int:
    """Each returned run of a learner chunk into research/runs/<ID>/<run id>/ and its
    ledger id moved to the state its outcome gives; the number settled."""
    att = ledger.attempts()
    n = 0
    for d, meta in returned_runs(recs):
        aid = budget.attempt_id(meta.arm, meta.task_id, meta.repeat, meta.attempt)
        a = att.get(aid)
        if aid not in sent or a is None or a.state not in ("planned", "deferred", "infra-failed"):
            say(f"returned run {d.name}: {aid} was not sent in this chunk; ignored")
            continue
        dest = Path(root) / "research" / "runs" / module / meta.run_id
        if dest.exists():
            say(f"returned run {d.name}: research/runs/{module}/{meta.run_id} exists; ignored")
            continue
        dest.mkdir(parents=True)
        _copy_tree(d, dest)
        ledger.move(aid, "running", max_reissue=plan.max_reissue, run_id=meta.run_id)
        info = {"run_id": meta.run_id, "outcome": meta.outcome,
                "calls": int(meta.usage.get("calls", 0) or 0),
                "gpu_s": round(float(meta.usage.get("gpu_s", 0) or 0), 3),
                "detail": "a sealed run's attempt (fvh.sealed)"}
        ledger.move(aid, batch._scored_state(meta.outcome), **info)
        att = ledger.attempts()
        n += 1
    return n


# =====================================================================================
# Par (host): python -m fvh par <ID> --truth ARCHIVE --sealed P --unsealed DIR --plan PLAN
# =====================================================================================

def _par_pin(root, module, archive):
    try:
        data = tomllib.loads((Path(root) / "sandbox" / "truth.toml").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        raise SealedRefused("sandbox/truth.toml is unreadable") from None
    pins = [t for t in data.get("lab", []) if isinstance(t, dict) and t.get("id") == module
            and t.get("part") == PAR_PART]
    if len(pins) != 1 or pins[0].get("archive") != archive:
        raise SealedRefused(f"{archive} is not {module}'s par agent (sandbox/truth.toml's "
                            f"[[lab]] id = \"{module}\", part = \"{PAR_PART}\")")
    f = Path(root) / archive
    import hashlib
    if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest() != pins[0].get("sha256"):
        raise SealedRefused(f"{archive} is missing or does not match its pinned sha256")
    return pins[0]


def par_plan_text(fragment: dict, *, seed, tasks, rounds, repeats, attempts, lab, lever_check,
                  gate="", gate_sha256="", census=False) -> str:
    """Par's plan (fvh.batch's PLAN.toml) from its sealed fragment (labs/<ID>/par/PLAN.toml:
    an [arm] table, its construct, policy and caps, and for a census module a [census]
    table; optional system and instructions) over the part's tasks, at the learner's base
    seed, B (rounds), repeats and attempts (module docstring). ValueError on a fragment
    that is not one."""
    arm = fragment.get("arm")
    if not isinstance(arm, dict) or not isinstance(arm.get("policy"), str):
        raise ValueError("the fragment has no [arm] with a policy")
    allowed = {"construct", "policy", "family", "turns", "tokens", "wall_s", "gpu_s",
               "acceptance", "lab_code"}
    for t in ("arm", "census"):
        tab = fragment.get(t)
        if tab is not None and (not isinstance(tab, dict) or set(tab) - allowed
                                or tab.get("family", budget.QWEN) != budget.QWEN
                                or tab.get("construct", "model") == "agent"):
            raise ValueError(f"the fragment's [{t}] is not a Qwen policy arm")
    if census and not isinstance(fragment.get("census"), dict):
        raise ValueError("a census module's par fragment has a [census] arm")

    def q(v):
        return json.dumps(v, ensure_ascii=False)
    lines = [f"seed = {int(seed)}", f"tasks = {q(sorted(tasks))}", f"repeats = {int(repeats)}",
             f"attempts = {int(attempts)}", f"lever_check = {'true' if lever_check else 'false'}"]
    if lab:
        lines.append(f"lab = {q(lab)}")
    for k in ("system", "instructions"):
        if isinstance(fragment.get(k), str):
            lines.append(f"{k} = {q(fragment[k])}")
    if gate:
        lines += [f"gate = {q(gate)}", f"gate_sha256 = {q(gate_sha256)}"]
    for t, rel in sorted(tasks.items()):
        lines += ["", f"[task.{q(t)}]", f"path = {q(rel)}"]
    for name, tab, n in ((PAR_ARM, arm, rounds),
                         (CENSUS_ARM, fragment.get("census") if census else None, 1)):
        if tab is None:
            continue
        lines += ["", "[[arm]]", f"name = {q(name)}", 'family = "qwen"', f"rounds = {int(n)}",
                  f"construct = {q(tab.get('construct', 'model'))}", f"policy = {q(tab['policy'])}"]
        for k in ("turns", "tokens", "wall_s", "gpu_s", "acceptance", "lab_code"):
            if k in tab:
                lines.append(f"{k} = {q(tab[k])}")
    return "\n".join(lines) + "\n"


def _par_ids(cards, rounds, repeats, attempts, census):
    items = budget.enumerate_plan([budget.Arm(PAR_ARM, budget.QWEN, rounds)], list(cards),
                                  repeats=repeats, attempts=attempts)
    ids = [p.id for p in items]
    cen = [budget.attempt_id(CENSUS_ARM, c, 1, 1) for c in cards] if census else []
    return cen, ids


def _par_done(root, module, part, archive_sha256):
    """{attempt id: RunMeta} of the par runs of this part already in research/runs/<ID>/."""
    out = {}
    for d in runlog.run_dirs(root, module):
        if not d.name.startswith(f"par-{part}-"):
            continue
        try:
            m = runlog.load_meta(d)
        except ValueError:
            continue
        p = (m.apparatus or {}).get("par") or {}
        if p.get("part") == part and p.get("archive_sha256") == archive_sha256:
            out[budget.attempt_id(m.arm, m.task_id, m.repeat, m.attempt)] = m
    return out


def _closed(meta) -> bool:
    return meta.outcome == "verified" and runlog.hole_count(meta.verify) == 0


def run_par(root, module, archive, part, into, plan_path, *, beside=None, mem_gb=None, log=None,
            launch=None, app=None, found=None, calendar=None) -> int:
    """The course's par agent on the learner's unsealed part (module docstring). Exit: 0
    every par id ran (or was dropped by the census), 1 ids left, 3 refused."""
    say = _say(log)
    root = Path(root)
    _registry(root, module)
    pin = _par_pin(root, module, archive)
    up = unsealed_part(root, module, part, into)
    try:
        plan = batch.load_plan(plan_path, root, tasks_at={up.stratum: Path(into).expanduser()})
    except batch.BatchError as e:
        raise SealedRefused(str(e)) from None
    _check_plan(plan, up)
    qwen = [a for a in plan.arms if a.family == budget.QWEN]
    if beside is None:
        if len(qwen) != 1:
            raise SealedRefused(f"the plan has {len(qwen)} Qwen arms: name the one par runs "
                                "beside (--beside ARM)")
        arm = qwen[0]
    else:
        try:
            arm = plan.arm(beside)
        except KeyError:
            raise SealedRefused(f"the plan has no arm {beside!r}") from None
    tasks = part_tasks(up)
    census = module in CENSUS_MODULES
    cen_ids, par_ids = _par_ids(sorted(tasks), arm.rounds, plan.repeats, plan.attempts, census)
    seeds = {aid: [batch.derive_seed(plan.seed, aid, n) for n in
                   range(1 if aid.startswith(CENSUS_ARM + "/") else arm.rounds)]
             for aid in cen_ids + par_ids}
    learner = {s for aid in (p.id for p in plan.items()) for s in plan.seeds(aid)}
    if learner & {s for v in seeds.values() for s in v}:
        raise SealedRefused("a par seed equals one of the learner's: choose another base seed")
    cap = sum(len(v) for v in seeds.values())
    if app is None:
        try:
            app = apparatus.load(root=root)
        except apparatus.ApparatusError as e:
            raise SealedRefused(str(e)) from None
        _apparatus_check(app, root)
    try:
        budget.check_anchors(root, module)
    except (budget.AnchorError, budget.LedgerError) as e:
        raise SealedRefused(str(e)) from None
    ledger = budget.Ledger(budget.ledger_path(root, module))
    mine = [r for r in ledger.par_lines(part) if r.get("archive_sha256") == pin["sha256"]]
    if any(r.get("event") == "done" for r in mine):
        raise SealedRefused(f"par ran on part {part} already (ledger seq "
                            f"{[r['seq'] for r in mine if r.get('event') == 'done'][-1]})")
    if not mine:
        try:
            reg = budget.registry_budget(root, module)
        except budget.BudgetError as e:
            raise SealedRefused(str(e)) from None
        used = ledger.used()[budget.QWEN]
        for unit, key, n in (("calls", "qwen_calls", cap), ("runs", "qwen_runs",
                                                             len(cen_ids) + len(par_ids))):
            have = reg.get(key, 0) if isinstance(reg.get(key), int) else 0
            if used[unit] + n > have:
                raise SealedRefused(f"par needs {n} qwen {unit} with the ledger's {used[unit]}; "
                                    f"the registry allows {key} = {have}")
        if not found:
            try:
                backends.refuse_if_disabled()
            except backends.ModelDisabled as e:
                raise SealedRefused(str(e)) from None
        ledger.par("planned", calls=cap, runs=len(cen_ids) + len(par_ids), part=part,
                   archive_sha256=pin["sha256"], files_sha256=up.files_sha256, beside=arm.name,
                   seed=plan.seed, rounds=arm.rounds, census=len(cen_ids))
        say(f"{module}: par reserved {cap} call(s) and {len(cen_ids) + len(par_ids)} run(s) "
            f"on part {part} (beside arm {arm.name}, B = {arm.rounds})")
    if found is None:
        found = _server(app)
    launch = launch or (lambda spec, rec, fd: default_launch(root, spec, rec, archive=archive,
                                                             mem_gb=mem_gb, calendar_fd=fd,
                                                             log=say))
    par = {"seed": plan.seed, "rounds": arm.rounds, "repeats": plan.repeats,
           "attempts": plan.attempts, "tasks": tasks, "census": census, "lab": plan.lab,
           "lever_check": plan.lever_check, "gate": plan.gate, "gate_sha256": plan.gate_sha256,
           "archive_sha256": pin["sha256"]}
    cal = calendar if calendar is not None else _calendar()
    try:
        cal.__enter__()
    except backends.Deferred as e:
        raise SealedRefused(f"deferred: {e}") from None
    k = 0
    try:
        while True:
            done = _par_done(root, module, part, pin["sha256"])
            dropped = sorted(t for aid, m in done.items()
                             if aid.startswith(CENSUS_ARM + "/") and _closed(m)
                             for t in [m.task_id])
            todo = [aid for aid in cen_ids if aid not in done]
            if not todo:
                todo = [aid for aid in par_ids if aid not in done
                        and aid.split("/")[1] not in dropped]
            if not todo:
                break
            k += 1
            spec = _spec_base(root, module, "par-run", up, app, found, ids=todo,
                              seed_pool=[s for aid in todo for s in seeds[aid]],
                              calls=sum(len(seeds[aid]) for aid in todo), prereg=note_prereg(
                                  ledger), stmts={}, plan_sha256="")
            spec.update(par=dict(par, dropped=dropped),
                        unsealed=str(Path(into).expanduser().resolve()))
            recs = Path(tempfile.mkdtemp(prefix="fvh-par-records-"))
            try:
                fh = getattr(cal, "fh", None)
                code = launch(spec, recs, fh.fileno() if fh is not None else None)
                _save_sandbox_record(root, module, recs, f"par-{part}-{k:02d}")
                moved = 0
                for d, meta in returned_runs(recs):
                    aid = budget.attempt_id(meta.arm, meta.task_id, meta.repeat, meta.attempt)
                    if aid not in todo or aid in done:
                        continue
                    import_par(root, module, d, part=part, archive_sha256=pin["sha256"])
                    moved += 1
            finally:
                shutil.rmtree(recs, ignore_errors=True)
            say(f"par chunk {k}: container exit {code}; {moved} of {len(todo)} id(s) came back")
            if not moved:
                say("no par id came back from the last container run: par's reservation "
                    "stays; run the same line again once the cause is fixed")
                return 3
    finally:
        cal.__exit__(None, None, None)
    done = _par_done(root, module, part, pin["sha256"])
    runs = [m for aid, m in done.items() if aid.startswith(PAR_ARM + "/")]
    cens = [m for aid, m in done.items() if aid.startswith(CENSUS_ARM + "/")]
    counts = {"runs": len(runs), "solved": sum(_closed(m) for m in runs),
              "calls": sum(int(m.usage.get("calls", 0) or 0) for m in done.values()),
              "census_tasks": len(cens), "census_dropped": sum(_closed(m) for m in cens)}
    ledger.par("done", part=part, archive_sha256=pin["sha256"], **counts)
    say(f"par on part {part}: " + ", ".join(f"{k} {v}" for k, v in counts.items())
        + f"; `python -m fvh report {module} --reverify all` re-verifies its claims")
    return 0


def note_prereg(ledger):
    note = batch.batch_note(ledger)
    return (note or {}).get("prereg_sha256") or ""


# =====================================================================================
# Inside the container: the batch (batchrun; truthcheck par-run's child)
# =====================================================================================

class ViewGate:
    """The run's host gate as the container sees it: its running counts (GATE_VIEW, a
    read-only bind), relative to when this view was made (one attempt's share)."""

    NUMERIC = ("calls", "prompt_tokens", "output_tokens", "reasoning_tokens", "tokens", "gpu_s",
               "refused", "capped", "ctx_saturated", "overrides", "admitted")

    def __init__(self, path=GATE_VIEW):
        self.path = Path(path)
        self.base = self._read()

    def _read(self) -> dict:
        try:
            obj = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return obj if isinstance(obj, dict) else {}

    def counts(self) -> dict:
        now = self._read()
        out = dict(now)
        for k in self.NUMERIC:
            a, b = now.get(k), self.base.get(k)
            if not isinstance(a, (int, float)) or isinstance(a, bool):
                continue
            b = b if isinstance(b, (int, float)) and not isinstance(b, bool) else 0
            out[k] = round(a - b, 3) if isinstance(a, float) or isinstance(b, float) else a - b
        return out

    def stop(self):
        return None


class _Seeded:
    """A recording transport whose n-th call carries the attempt's n-th pre-registered
    seed, whatever the policy asks (the host gate admits a seed of its pool once)."""

    def __init__(self, inner, seeds):
        self._inner, self._seeds, self._n = inner, list(seeds), 0

    def complete(self, message, *, system="", seed=None):
        if self._n >= len(self._seeds):
            raise backends.TransportError("gate", "the attempt's seeds are used up")
        s = self._seeds[self._n]
        self._n += 1
        return self._inner.complete(message, system=system, seed=s)

    def __getattr__(self, name):
        return getattr(self._inner, name)


def container_transport(spec, run_dir, seeds, *, view=None):
    """The Qwen transport inside a sealed run's container (module docstring; D102)."""
    from fvh.backends import opencode as OC
    app_tab = {"version": spec.get("opencode_version", "1.18.25"),
               "provider_npm": "@ai-sdk/openai-compatible",
               "call_timeout_s": spec.get("call_timeout_s", 900),
               "external_ok": ["/tmp/opencode/*"]}
    state = Path(tempfile.gettempdir()) / "fvh-qwen-state"
    state.mkdir(mode=0o700, parents=True, exist_ok=True)
    inner = OC.Transport(app_tab, gate_url=RELAY_URL, model=spec["model"],
                         context=spec.get("max_model_len"), options=spec.get("options") or {},
                         state_base=state, binary=spec.get("opencode", IMAGE_OPENCODE),
                         pinned_by=spec["image"])
    view = view if view is not None else ViewGate()
    t = batch.RecordingTransport(inner, run_dir, gate=view, seeds=seeds)
    t.gate_handle = view
    return _Seeded(t, seeds)


class SealedRunner(tools.HostRunner):
    """Each instrument from /work, in this container (truthcheck gate-agree's runner): no
    memory preflight (the container's own bound holds), no refusal of an agent target
    (the container is the isolation), and the lab gate's lever check against the staged
    task form when the plan runs it."""

    name = "container"
    isolated = True

    def __init__(self, root, *, lab_task=None, lab_code="preserve"):
        super().__init__(root, preflight=False)
        self.lab_task, self.lab_code = lab_task, lab_code

    def argv(self, instrument, target):
        cmd = super().argv(instrument, target)
        if self.lab_task and instrument == "vcheck --gate":
            cmd[-1:-1] = ["--lab-task", self.lab_task]
            if self.lab_code == "own":
                cmd[-1:-1] = ["--lab-code", "own"]
        return cmd

    def execute(self, instrument, target, *, timeout_s=None):
        from fvh.tools import runners as R
        R._check_instrument(instrument)
        shown = R._shown(R._real(target, self.root), self.root)
        argv = self.argv(instrument, shown)
        limit = timeout_s if timeout_s is not None else \
            R.default_timeout(self.root, R.lang_of(shown))
        scratch = tempfile.mkdtemp(prefix="fvh-tool-", dir=R._scratch_base(self.root))
        try:
            rc, o, e, timed_out = R._spawn([sys.executable, "-B", str(self.root / argv[0]),
                                            *argv[1:]], self.root, R._tool_env(scratch), limit)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        return R.make_result(instrument, shown, "agent", self.name, rc, o, e, timed_out,
                             R._redactor(self.root, scratch), "--json" in argv)


class SealedBatch(batch.Batch):
    """fvh.batch's Batch inside the container: the attempts of the spec's ids, with the
    transport and runner above, a scratch ledger, and the host's facts."""

    def __init__(self, root, module, plan, *, spec, app, log=None, view=None):
        super().__init__(root, module, plan, transports=self._make_transport, log=log, app=app)
        self.spec = spec
        self._view = view
        self.prereg = spec.get("prereg_sha256") or ""
        self.statements = dict(spec.get("statements_sha256") or {})
        course = spec.get("course") or {}
        self.facts = {"course_commit": course.get("course_commit", ""),
                      "course_dirty": bool(course.get("course_dirty", False)),
                      **{k: v for k, v in course.items() if k not in ("course_commit",
                                                                       "course_dirty")}}
        self.server = spec.get("server")
        runs = Path(root) / GRADER / RUNS
        runs.mkdir(parents=True, exist_ok=True)
        self.ledger = budget.Ledger(runs / "ledger.jsonl")

    def _make_transport(self, family, run_dir, seeds, caps):
        if family != budget.QWEN:
            raise backends.TransportError("cli-crash", "a sealed run has Qwen arms only")
        view = ViewGate(self._view) if self._view is not None else ViewGate()
        return container_transport(self.spec, run_dir, seeds, view=view)

    def _runner(self, task_rel, lang, arm=None):
        return SealedRunner(self.root, lab_task=task_rel if self.plan.lever_check else None,
                            lab_code=arm.lab_code if arm else "preserve")

    def _collect_facts(self) -> dict:
        facts = dict(self.spec.get("facts") or {})
        facts["transport"] = {"route": "sealed-run container (D102)", "binary":
                              self.spec.get("opencode", IMAGE_OPENCODE),
                              "pinned_by": self.spec.get("image"), "gate": "Route C",
                              "relay": RELAY_URL}
        return facts


def inside(work="/work", *, plan_path=None, view=None, log=None, clock=time.monotonic,
           on_attempt=None) -> dict:
    """The container's batch (module docstring): the spec's ids, in its order, while the
    deadline leaves an attempt's wall clock; for par, the census first and no par
    attempt on a task it closed. Returns {"ran", "left", "states", "closed"}."""
    say = log or (lambda m: None)
    work = Path(work)
    started = clock()
    spec = json.loads((work / SPEC).read_text(encoding="utf-8"))
    tmp = work / GRADER / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    old_tmp, old_env = tempfile.tempdir, os.environ.get("TMPDIR")
    os.environ["TMPDIR"] = str(tmp)           # work copies under /work, as gate-agree's are
    tempfile.tempdir = str(tmp)
    try:
        return _inside(work, spec, plan_path, view, say, clock, started, on_attempt)
    finally:
        tempfile.tempdir = old_tmp
        if old_env is None:
            os.environ.pop("TMPDIR", None)
        else:
            os.environ["TMPDIR"] = old_env


def _inside(work, spec, plan_path, view, say, clock, started, on_attempt):
    app = apparatus.load(work / APPARATUS)
    plan = batch.load_plan(Path(plan_path) if plan_path else work / PLAN, work)
    if spec.get("kind") == "sealed-run" and plan.sha256 != spec.get("plan_sha256"):
        raise SealedRefused("the staged plan is not the one the host opened")
    b = SealedBatch(work, spec["module"], plan, spec=spec, app=app, log=say, view=view)
    wanted = set(spec["ids"])
    items = [p for p in plan.items() if p.id in wanted]
    b.ledger.plan(items)
    order = [p.id for p in items]
    cen = [a for a in order if a.startswith(CENSUS_ARM + "/")]
    rest = [a for a in order if a not in cen]
    dropped = set((spec.get("par") or {}).get("dropped") or ())
    ran, closed = [], set()
    deadline = started + float(spec.get("deadline_s", WALL_S - MARGIN_S))

    def fits(aid):
        arm = plan.arm(aid.split("/")[0])
        need = float(arm.caps.get("wall_s", app.defaults().wall_s or 2700))
        return clock() + need <= deadline

    for phase in (cen, rest):
        for aid in phase:
            if b.stop or not fits(aid):
                break
            if aid in rest and aid.split("/")[1] in dropped | closed:
                continue
            b.attempt(aid)
            ran.append(aid)
            if on_attempt:
                on_attempt(aid)
            if aid in cen:
                rids = [r.get("run_id") for r in b.ledger.read()
                        if r.get("id") == aid and r.get("run_id")]
                try:
                    if rids and _closed(runlog.load_meta(b.ledger.path.parent / rids[-1])):
                        closed.add(aid.split("/")[1])
                except (ValueError, OSError):
                    pass
        if b.stop:
            break
    states = {aid: s.state for aid, s in b.ledger.attempts().items()}
    left = [aid for aid in order if aid not in ran and aid.split("/")[1] not in
            (dropped | closed if aid in rest else set())]
    return {"ran": ran, "left": left, "states": states, "closed": sorted(closed),
            "stop": b.stop or ""}


def strip_counts_only(work="/work", *, part, archive_sha256) -> int:
    """In the container, before the return: every par run directory under /work/grader/
    runs/ reduced to counts_only's files (D103's first pass; the host's import is the
    second). Returns the number of run directories kept."""
    base = Path(work) / GRADER / RUNS
    n = 0
    for d in sorted(base.iterdir()) if base.is_dir() else []:
        if not d.is_dir() or d.is_symlink():
            if d.name != "ledger.jsonl":
                _rm(d)
            continue
        try:
            meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
            rec = counts_only(meta, part=part, archive_sha256=archive_sha256)
        except (OSError, ValueError, TypeError):
            _rm(d)
            continue
        for p in list(d.iterdir()):
            if p.name in COUNTS_ONLY_FILES or (p.name in COUNTS_ONLY_DIRS and p.is_dir()
                                               and not p.is_symlink()):
                continue
            _rm(p)
        (d / "run.json").write_text(json.dumps(rec, sort_keys=True, indent=1) + "\n",
                                    encoding="utf-8")
        n += 1
    led = base / "ledger.jsonl"
    if led.exists():
        _rm(led)                     # its lines name par's run ids only, but nothing else returns
    return n


def _rm(p: Path):
    if p.is_dir() and not p.is_symlink():
        shutil.rmtree(p, ignore_errors=True)
    else:
        try:
            p.unlink()
        except OSError:
            pass
