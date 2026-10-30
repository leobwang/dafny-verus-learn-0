"""dvl.contract_local: scripts/contract_local.sh (DV4-PLAN §6). The checks and
the dry run were built at DV4 step 1b without Docker or a model; the live
replay at DV4 step 3b.

contract_local.sh replays a module's contract under opencode and a local Qwen
in a per-run container, from the same starting state the learner's /contract
run had, and returns a patch the learner reads before deciding whether to
apply it. This build does every step that needs neither Docker nor a model:

  --available   the refusal checks of §6 step 1 only, one line per failing
                check (the module and its registry record, the Qwen budget, the
                ledger against its anchors, the apparatus, Docker access)
  --dry-run     steps 2-4 too: the CONTRACT header parsed and every allowed path
                validated as /contract validates it (.claude/skills/contract/
                SKILL.md §1-§2); the starting state found from the commit of the
                snapshot a `scripts/specfreeze --against` acceptance line names
                (or --from); the sandbox manifest built and checked by
                scripts/mksandbox-run's library (materialized, self-tested, its
                docker argv printed); the acceptance lines sorted into the forms
                the verification container checks and the audit list. Nothing
                runs and nothing is written outside the run directory, which is
                removed again.
  (no flag)     the live replay (step 3b): the checks; one attempt in the
                module's ledger (fvh.budget: planned, running, then scored, or
                infra-failed or deferred, with the batch anchored in
                research/ledger-heads.jsonl); the agent container (opencode
                and the pinned Qwen behind the run's gate, dvl.sandbox's
                live_run); the return path and the secret scan; then a fresh
                verification container on the returned files, which runs the
                acceptance lines of the forms fvh.contract checks; the run
                directory research/runs/<ID>/<run-id>/; one line per
                acceptance line and one verdict line.

The patch is never applied: the learner reads patch.diff and applies it by hand.

The run directory holds run.json (fvh.runlog.RunMeta, mode "agent"),
manifest.json and selftest.json, sandbox.json (the agent container's record:
the controls, the agent's per-run gate, its end, the return), gate.log.gz and
gate-counts.json (every model request, compressed, and the totals), transcript.jsonl.gz
(the agent's event stream, after the secret scan), inputs.tar.gz and
inputs.sha256 (the files as staged), patch.diff and returned/ (the changed
files), and verify.json (the verification container's run of each checked
acceptance line).

Exit codes: 0 done (--available: available; --dry-run: the run is ready but for
what it reports; a replay: completed, whatever the verdict), 1 a step failed
(the self-test, the agent's per-run gate, a container), 2 usage, 3 refused
(also: deferred, memory short or the GPU calendar lock held).
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from dvl import sandbox  # noqa: E402

HARNESS = REPO_ROOT / "harness"
# The model is the one the host's server serves (Δ505: --model, else DVL_MODEL,
# else the server's only model; dvl.sandbox.discover_server).
NO_MODEL = "(the served model)"   # the dry run's stand-in when no server answers
TURN_CAP = 40            # [A] DV4-PLAN §4.1: Q07's replay, at most its qwen_calls
WALL_CLOCK_S = 2700      # [A] 45 minutes
VERIFY_WALL_CLOCK_S = 1800   # [A] the verification container's acceptance commands
ARM = "replay"


def _fvh():
    """fvh's frozen core (standard library only), imported from this checkout."""
    if str(HARNESS) not in sys.path:
        sys.path.insert(0, str(HARNESS))
    from fvh import apparatus, budget, runlog
    return apparatus, budget, runlog

KEYS = ("goal", "allowed-files", "acceptance")
# /contract's §2: frozen, solo, guard and reference paths never enter an allowlist
FORBIDDEN_NAMES = ("CLAUDE.md", "CLAUDE.local.md", "dfyconfig.toml", "Cargo.toml", "Cargo.lock",
                   "build.rs", "rust-toolchain", "rust-toolchain.toml", "pyproject.toml", "uv.lock",
                   "conftest.py", "pytest.ini", "setup.cfg", "setup.py", "tox.ini",
                   "sitecustomize.py", "usercustomize.py")
FORBIDDEN_PREFIXES = ("Challenges/", "agents/", "harness/fvh/", "harness/tests/", "paper/rubrics/",
                      "expected/", "Solutions/", "paper/solutions/", "tests/", ".claude/",
                      "scripts/", "sandbox/", "instructor/", "dafny/options/", ".toolchain/",
                      ".vscode/", ".config/", "research/runs/", "bench/public/", "Hidden/")
FORBIDDEN_EXACT = ("MODULES.toml", ".mcp.json", "research/ledger-heads.jsonl", "research/runs",
                   "bench/manifest.toml")


class Refused(Exception):
    pass


class Failed(Exception):
    pass


def say(msg, err=False):
    print(f"contract_local: {msg}", file=sys.stderr if err else sys.stdout)


# --- the CONTRACT header (§6 step 2; SKILL.md §1) -----------------------------------------------

def parse_header(text):
    """{'goal': str, 'allowed-files': [...], 'acceptance': [...]} from the
    CONTRACT block that opens line 1, or Refused naming what is wrong."""
    lines = text.split("\n")
    if not lines or lines[0].strip() not in ("/* CONTRACT", '"""CONTRACT'):
        raise Refused("line 1 does not open a CONTRACT header (`/* CONTRACT` or `\"\"\"CONTRACT`)")
    end = "*/" if lines[0].strip() == "/* CONTRACT" else '"""'
    body = []
    for line in lines[1:]:
        if line.strip() == end:
            break
        body.append(line)
    else:
        raise Refused("the CONTRACT header is never closed")
    out, key = {}, None
    for line in body:
        if not line.strip():
            continue
        m = re.match(r"^([a-z-]+):\s*(.*)$", line)
        if m and not line.startswith((" ", "\t")):
            key, rest = m.group(1), m.group(2).strip()
            if key not in KEYS:
                raise Refused(f"the CONTRACT header has a key {key!r}: exactly goal, allowed-files "
                              "and acceptance")
            if key in out:
                raise Refused(f"the CONTRACT header repeats {key!r}")
            out[key] = rest if key == "goal" else []
            if key != "goal" and rest:
                raise Refused(f"{key}: is a list, one `  - ` item per line")
            continue
        m = re.match(r"^\s+-\s+(.*)$", line)
        if m and key in ("allowed-files", "acceptance"):
            out[key].append(m.group(1).strip())
            continue
        if key == "acceptance" and out[key] and line.startswith(" "):
            out[key][-1] += " " + line.strip()        # a wrapped bullet
            continue
        raise Refused(f"the CONTRACT header has a line outside its three keys: {line.strip()[:60]!r}")
    for k in KEYS:
        if k not in out:
            raise Refused(f"the CONTRACT header lacks {k!r}")
        if not out[k]:
            raise Refused(f"the CONTRACT header's {k!r} is empty")
    return out


def path_problem(p, rec):
    """Why an allowed-files path is refused (SKILL.md §2, plus research/runs and
    the ledger anchors, DV4-PLAN §8), or None."""
    if not sandbox.rel_ok(p):
        return "not a repo-relative path (no leading / or ./, no .., no glob)"
    if not sandbox.agentic_ok(p, rec):
        return f"not in {rec['id']}'s agentic list"
    if p in FORBIDDEN_EXACT or p.startswith(FORBIDDEN_PREFIXES):
        return "a frozen, solo, guard, reference or run-record path"
    parts = p.split("/")
    if "given" in parts or ".cargo" in parts or PurePosixPath(p).name in FORBIDDEN_NAMES \
            or p.endswith(".pth"):
        return "a frozen, guard or build-configuration path"
    if re.search(r"(^|/)[^/]*trust[-_]report", p) and p.startswith(("dafny/R/", "verus/r/", "harness/r/")):
        return "R16's trust-report (solo work)"
    if re.match(r"^harness/q/[^/]+/gate(/|\.py$)", p):
        return "Q's gate (solo work)"
    if sandbox.source_class(p) and not p.startswith("research/"):
        return f"in a refused source class ({sandbox.source_class(p)})"
    return None


# --- acceptance-line forms (§6) -------------------------------------------------------------------

def classify_line(line):
    """(form, detail) of one acceptance line: vcheck-gate, zero-holes,
    specfreeze-against, vaudit, vaudit-compare (checked in the verification
    container), git-diff (evidence: patch.diff) or audit (the learner's)."""
    cmd = re.search(r"`([^`]+)`", line)
    c = cmd.group(1) if cmd else ""
    if re.match(r"^scripts/vcheck --gate \S+$", c) and "exits 0" in line:
        return "vcheck-gate", c.split()[-1]
    m = re.match(r"^scripts/specfreeze --against (\S+) (\S+)$", c)
    if m and "no change" in line:
        return "specfreeze-against", m.group(1)
    m = re.match(r"^scripts/vaudit --compare (expected/\S+\.audit) (\S+)$", c)
    if m and "no difference" in line:
        return "vaudit-compare", m.group(1)
    if re.match(r"^scripts/vaudit \S+$", c) and "no finding" in line:
        return "vaudit", c.split()[-1]
    if re.search(r"\bzero\b.*\bholes?\b", line) and not cmd:
        return "zero-holes", ""
    if c.startswith("git diff") or line.lstrip().startswith("`git diff"):
        return "git-diff", "patch.diff"
    return "audit", ""


# --- the registry and git --------------------------------------------------------------------------

def git(root, *args):
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def record(root, mid):
    try:
        return sandbox.registry_record(root, mid)
    except sandbox.ManifestError as e:
        raise Refused(str(e)) from None


def module_checks(rec):
    """§6 step 1's registry refusals, as a list of one-line problems."""
    mid = rec["id"]
    out = []
    if rec.get("status") == "planned":
        out.append(f"{mid} is planned: not authored yet")
    if rec.get("solo"):
        out.append(f"{mid} is a solo challenge module: no contract runs for it")
    if not rec.get("agentic"):
        out.append(f"{mid} has no agentic exercise (registry `agentic` is empty)")
    if "agent" not in rec.get("engines", []):
        out.append(f"{mid}'s engines do not include agent: its contract has no local replay")
    b = rec.get("budget", {})
    if not b.get("qwen_runs") or not b.get("gpu_hours") or not b.get("qwen_calls"):
        out.append(f"{mid}'s registry budget allows no Qwen run (qwen_runs, qwen_calls and "
                   "gpu_hours must all be positive)")
    return out


def gpu_used_s(ledger):
    """GPU-seconds the module's scored and infra-failed replays recorded."""
    return sum(float(r.get("gpu_s") or 0) for r in ledger.read()
               if r.get("kind") == "attempt" and r.get("state") in ("scored", "infra-failed"))


def ledger_checks(root, rec):
    """The ledger against its anchors (§4.2, fvh.budget) and the module's Qwen
    budget: qwen_runs planned so far, and the GPU-seconds recorded against
    gpu_hours. An open batch with its attempt re-issuable (an infrastructure
    failure before model output, or a deferred run) is resumed, not refused."""
    _, budget, _ = _fvh()
    mid = rec["id"]
    try:
        budget.check_anchors(root, mid)
        ledger = budget.Ledger(budget.ledger_path(root, mid))
        last = budget.last_anchor(root, mid)
        if last is not None and last["event"] == "open":
            if budget.resume_order(ledger):
                return []
            return [f"{mid}'s last replay batch is still open and holds nothing to re-issue "
                    f"(see `fvh ledger {mid}`)"]
        b = rec.get("budget") or {}
        used = ledger.used()[budget.QWEN]
        if used["runs"] >= int(b.get("qwen_runs") or 0):
            return [f"{mid}'s qwen_runs ({b.get('qwen_runs')}) is used: its ledger holds "
                    f"{used['runs']} planned replay(s) (research/runs/{mid}/ledger.jsonl)"]
        if gpu_used_s(ledger) >= float(b.get("gpu_hours") or 0) * 3600:
            return [f"{mid}'s gpu_hours ({b.get('gpu_hours')}) is used"]
    except (budget.AnchorError, budget.LedgerError, budget.BudgetError, ValueError) as e:
        return [str(e)]
    return []


def apparatus_checks(root):
    """`fvh apparatus --check` (the pinned opencode binary, the toolchain and
    images pins) and the replay's settings: a [backend.qwen] table and the
    [model_gate] request options and endpoints."""
    apparatus, _, _ = _fvh()
    try:
        app = apparatus.load(root=root)
    except apparatus.ApparatusError as e:
        return [str(e)]
    if "qwen" not in app.families():
        return [f"{app.path}: no [backend.qwen] table: the replay's opencode is not pinned"]
    out = [f"apparatus drift: {d.line()}" for d in apparatus.check(app, root)]
    if not isinstance(app.model_gate().get("options"), dict):
        out.append(f"{app.path}: [model_gate] has no request options")
    if not isinstance(app.model_gate().get("endpoints"), list):
        out.append(f"{app.path}: [model_gate] has no endpoints")
    return out


def server_checks(root, model=None):
    """The host's model server (Δ505): [] when one answers and its model can be
    chosen, else the reason."""
    try:
        sandbox.discover_server(root, model=model)
    except sandbox.SandboxError as e:
        return [f"model server: {e}"]
    return []


def image_checks(root, *, local=True):
    """The agent and toolchain images of sandbox/images.lock, and (`local`, which
    needs Docker access) each present here by its digest."""
    lock = sandbox.read_images_lock(root)
    out = []
    for name in ("dvl-agent", "dvl-toolchain"):
        ref = next((k for k in lock if k.startswith(name + "@")), None)
        if ref is None:
            out.append(f"the sandbox images are not built yet (sandbox/images.lock lists no {name}; "
                       "sandbox/build-images.sh)")
            continue
        if not local:
            continue
        p = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", ref.split("@")[1]],
                           capture_output=True, text=True, timeout=60)
        if p.returncode != 0 or p.stdout.strip() != ref.split("@")[1]:
            out.append(f"the image {ref} is not built here (sandbox/build-images.sh; then "
                       "sandbox/build-images.sh --check)")
    return out


def docker_checks():
    ok, msg = sandbox.check_access()
    return [] if ok else [msg]


def availability(root, rec, model=None):
    out = module_checks(rec) + ledger_checks(root, rec) + apparatus_checks(root) \
        + server_checks(root, model)
    docker = docker_checks()
    return out + docker + image_checks(root, local=not docker)


# --- the starting state (§6 step 3) --------------------------------------------------------------

def starting_state(root, contract, from_rev):
    """(rev, snapshot path or None): the commit the replay starts from."""
    snaps = [d for f, d in (classify_line(x) for x in contract["acceptance"]) if f == "specfreeze-against"]
    if len(set(snaps)) > 1:
        raise Refused(f"the CONTRACT names more than one snapshot ({sorted(set(snaps))})")
    snap = snaps[0] if snaps else None
    if from_rev:
        rc, rev, err = git(root, "rev-parse", "--verify", "--quiet", f"{from_rev}^{{commit}}")
        if rc != 0:
            raise Refused(f"--from {from_rev} is not a commit")
    elif snap:
        if not (Path(root) / snap).is_file():
            raise Refused(f"the snapshot {snap} that the CONTRACT names is missing")
        rc, _, _ = git(root, "ls-files", "--error-unmatch", "--", snap)
        if rc != 0:
            raise Refused(f"the snapshot {snap} is not tracked: commit it before the /contract run, "
                          "so its commit marks the starting state")
        rc, out, _ = git(root, "status", "--porcelain", "--", snap)
        if out:
            raise Refused(f"the snapshot {snap} differs from its committed version (git show "
                          f"HEAD:{snap}): commit or restore it")
        rc, rev, _ = git(root, "log", "-1", "--format=%H", "--", snap)
        if rc != 0 or not rev:
            raise Refused(f"no commit changed {snap}")
    else:
        raise Refused("the CONTRACT names no snapshot in a `scripts/specfreeze --against <snapshot> "
                      "<file>` acceptance line and no --from <rev> was given: the starting state is "
                      "never guessed")
    for p in contract["allowed-files"]:
        rc, out, _ = git(root, "ls-tree", rev, "--", p)
        if rc != 0 or not out:
            raise Refused(f"{p} did not exist at the starting commit {rev[:12]}")
    if snap and from_rev:
        rc, out, _ = git(root, "ls-tree", rev, "--", snap)
        if rc != 0 or not out:
            raise Refused(f"the snapshot {snap} did not exist at --from {from_rev}")
    return rev, snap


# --- the manifest (§6 step 4) --------------------------------------------------------------------

def contract_text(root, rec, contract, forms):
    """The instructions: the parsed contract, CLAUDE.md §Contractor contract
    (the fallback rules and the learner's own Q-vN and R-vN sections,
    verbatim), and nothing else of CLAUDE.md."""
    src = (Path(root) / "CLAUDE.md").read_text(encoding="utf-8")
    m = re.search(r"(?ms)^## §Contractor contract\n.*?(?=^## |\Z)", src)
    section = re.sub(r"(?s)<!-- Slot format.*?-->\n?", "", m.group(0)) if m else ""
    out = [f"# Contract replay: {rec['id']}", "", "## The CONTRACT", "",
           f"goal: {contract['goal']}", "allowed-files:"]
    out += [f"  - {p}" for p in contract["allowed-files"]]
    out.append("acceptance:")
    out += [f"  - {a}" for a in contract["acceptance"]]
    out += ["", section.rstrip(), ""]
    return "\n".join(out)


def build_manifest(root, rec, contract, rev, snap, model, run_id="contract-local"):
    root = Path(root)
    mid = rec["id"]
    allowed = contract["allowed-files"]
    langs = {sandbox.lang_pool(p) for p in allowed}
    files = []

    def add(src, role, rev_=None, dst=None):
        e = {"src": src, "dst": dst or src, "role": role}
        if rev_:
            e["rev"] = rev_
        data = sandbox.read_source(root, sandbox.Entry(src, e["dst"], role, "0" * 64, rev_))
        e["sha256"] = sandbox.sha256_bytes(data)
        files.append(e)

    def add_text(dst, role, text):
        files.append({"dst": dst, "role": role, "text": text, "sha256": sandbox.sha256_bytes(text.encode())})

    for p in allowed:
        add(p, "editable", rev)
    if snap:
        add(snap, "snapshot", rev)
    forms = [classify_line(a) for a in contract["acceptance"]]
    audits = []
    for form, detail in forms:
        if form == "vaudit-compare":
            if not (root / detail).is_file():
                raise Refused(f"an acceptance line names {detail}, which does not exist")
            if not sandbox.expected_ok(detail, mid):
                raise Refused(f"an acceptance line names {detail}, which is not one of {mid}'s pins")
            audits.append(detail)
    # the module's given chain, project files, trusted tools and pins (DV4-PLAN §6
    # step 4), as every sandbox run builds them (dvl.sandbox.readonly_inputs)
    for src, role in sandbox.readonly_inputs(root, rec, langs, audits=audits):
        if src != "verus/Cargo.toml":
            add(src, role)
    if "verus" in langs:
        add_text("verus/Cargo.toml", "project", sandbox.verus_workspace(root, rec))
    add_text("CONTRACT.md", "contract", contract_text(root, rec, contract, forms))
    lock = sandbox.read_images_lock(root)
    image = next((k for k in lock if k.startswith("dvl-agent@")), "dvl-agent@sha256:" + "0" * 64)
    # opencode's step limit; with its title request disabled and automatic
    # compaction off, every step is one gated call (step 3a's call accounting),
    # so the turn cap and the registry's qwen_calls agree
    turns = min(TURN_CAP, int(rec.get("budget", {}).get("qwen_calls") or TURN_CAP))
    return {"schema": 1, "run_id": run_id, "module": mid, "kind": "agent", "image": image,
            "network": "model", "limits": {"wall_clock_s": WALL_CLOCK_S},
            "file": files, "return": list(allowed),
            "agent": {"cli": "opencode", "model": model, "turns": turns}}


# --- the live replay (§6 steps 5-7; DV4 step 3b) ------------------------------------------------

def _git_head(root):
    rc, out, _ = git(root, "rev-parse", "HEAD")
    return out if rc == 0 else ""


def acceptance_commands(contract):
    """[(line index, form, argv)] of the checked acceptance lines: the gate as a
    --json document (holes, verdict, exit code), the plain gate too when a line
    asks that it print only the summary line, specfreeze --against, vaudit and
    vaudit --compare, each exactly as the line writes it."""
    out = []
    holes_line = None
    for i, line in enumerate(contract["acceptance"]):
        form, _ = classify_line(line)
        m = re.search(r"`([^`]+)`", line)
        words = m.group(1).split() if m else []
        if form == "vcheck-gate":
            out.append((i, "vcheck-gate-json", words[:2] + ["--json"] + words[2:]))
            if "summary line" in line:
                out.append((i, "vcheck-gate", words))
        elif form in ("specfreeze-against", "vaudit", "vaudit-compare"):
            out.append((i, form, words))
        elif form == "zero-holes":
            holes_line = i
    if holes_line is not None and not any(f == "vcheck-gate-json" for _, f, _ in out):
        for p in contract["allowed-files"]:
            out.append((holes_line, "vcheck-gate-json", ["scripts/vcheck", "--gate", "--json", p]))
    return out


def verify_manifest(root, rec, manifest, after, cmds, run_id):
    """The verification container's manifest (§5.9): the agent run's read-only
    inputs (the contract text aside), every editable file as the agent
    returned it (inline, at its course path), and the acceptance commands."""
    files = []
    for f in manifest.raw["file"]:
        if f["role"] == "contract":
            continue
        if f["role"] == "editable":
            text = after[f["dst"]].decode("utf-8")
            files.append({"dst": f["dst"], "role": "editable", "text": text,
                          "sha256": sandbox.sha256_bytes(text.encode("utf-8"))})
        else:
            files.append(dict(f))
    lock = sandbox.read_images_lock(root)
    image = next(k for k in lock if k.startswith("dvl-toolchain@"))
    return {"schema": 1, "run_id": f"{run_id}-verify"[:64], "module": rec["id"], "kind": "verify",
            "image": image, "network": "none", "limits": {"wall_clock_s": VERIFY_WALL_CLOCK_S},
            "file": files, "command": [{"argv": list(c)} for _, _, c in cmds]}


def judge(contract, cmds, results):
    """[(line, form, met (True/False/None for the learner's audit), evidence)]
    and the gate's --json document."""
    by_line = {}
    doc = None
    for (i, form, argv), res in zip(cmds, results):
        by_line.setdefault(i, []).append((form, argv, res))
        if form == "vcheck-gate-json" and doc is None:
            try:
                doc = json.loads(res.get("stdout") or "")
            except ValueError:
                doc = None
    out = []
    for i, line in enumerate(contract["acceptance"]):
        form, _ = classify_line(line)
        runs = by_line.get(i, [])
        if form == "vcheck-gate":
            js = next((r for f, _, r in runs if f == "vcheck-gate-json"), None)
            plain = next((r for f, _, r in runs if f == "vcheck-gate"), None)
            met = js is not None and js.get("exit_code") == 0
            ev = f"vcheck --gate --json: exit {js.get('exit_code') if js else None}"
            if plain is not None:
                lines = [x for x in (plain.get("stdout") or "").splitlines() if x.strip()]
                met = met and plain.get("exit_code") == 0 and len(lines) == 1
                ev += f"; the plain gate: exit {plain.get('exit_code')}, {len(lines)} output line(s)"
            out.append((line, form, met, ev))
        elif form == "zero-holes":
            holes = (doc or {}).get("holes")
            n = len(holes) if isinstance(holes, list) else holes
            out.append((line, form, n == 0, f"the gate's document: {n} hole(s)"))
        elif form in ("specfreeze-against", "vaudit", "vaudit-compare"):
            r = runs[0][2] if runs else None
            first = ((r or {}).get("stdout") or "").strip().splitlines()[-1:] or [""]
            out.append((line, form, r is not None and r.get("exit_code") == 0,
                        f"exit {(r or {}).get('exit_code')}: {first[0][:160]}"))
        elif form == "git-diff":
            out.append((line, form, None, "patch.diff is this line's evidence (no .git enters a "
                                          "container)"))
        else:
            out.append((line, form, None, "for your audit, with the transcript"))
    return out, doc


def _redact(text):
    return (text or "").replace(sandbox.WORK + "/", "").replace(sandbox.CONTAINER_SCRATCH, "<scratch>")


def replay(root, rec, contract, target, rev, snap, raw):
    """The live replay (module docstring); returns the exit code."""
    apparatus, budget, runlog = _fvh()
    mid = rec["id"]
    docker = docker_checks()
    model = raw["agent"]["model"]
    problems = ledger_checks(root, rec) + apparatus_checks(root) \
        + server_checks(root, None if model == NO_MODEL else model) + docker \
        + image_checks(root, local=not docker)
    if problems:
        raise Refused(problems[0])
    if model == NO_MODEL:
        raise Refused("model server: no model was found (DVL_MODEL or --model names one)")
    task = re.sub(r"[^A-Za-z0-9_.+-]+", "-", PurePosixPath(target).stem).strip("-") or "agent"
    aid = budget.attempt_id(ARM, task, 1, 1)
    ledger = budget.Ledger(budget.ledger_path(root, mid))
    b = rec.get("budget") or {}
    gpu_left = float(b.get("gpu_hours") or 0) * 3600 - gpu_used_s(ledger)
    run_id = runlog.new_run_id(aid)
    raw = dict(raw, run_id=run_id[:64])
    raw["agent"] = dict(raw["agent"], gpu_s=max(1, min(36000, int(gpu_left))))
    try:
        manifest = sandbox.validate(raw, root)
    except sandbox.ManifestError as e:
        raise Refused("the replay's manifest is refused: " + "; ".join(e.problems)) from None
    # the deferrals first, so that a deferred run writes nothing
    need = float(manifest.limits["mem_gb"]) + sandbox.RESERVE_GB
    have = sandbox.mem_available_gb()
    if have is None or have < need:
        raise Refused(f"deferred: {have or 0:.1f} GB available, {need:g} GB needed (the container's "
                      f"--memory plus the {sandbox.RESERVE_GB} GB reserve)")
    try:
        with sandbox._GpuCalendar():
            pass
    except sandbox.Deferred as e:
        raise Refused(f"deferred: {e}") from None
    head = _git_head(root)
    _, dirty, _ = git(root, "status", "--porcelain", "--untracked-files=no")
    last = budget.last_anchor(root, mid)
    try:
        if last is not None and last["event"] == "open":
            if aid not in budget.resume_order(ledger):
                raise Refused(f"{mid}'s open batch does not hold {aid} to re-issue")
            say(f"resuming {mid}'s open batch: {aid} is re-issued under the same id")
        else:
            ledger = budget.open_batch(root, mid, [budget.PlannedAttempt(aid, budget.QWEN,
                                                                         manifest.agent["turns"])],
                                       course_commit=head, budget=b)
        ledger.move(aid, "running", run_id=manifest.run_id)
    except (budget.AnchorError, budget.LedgerError, budget.BudgetError) as e:
        raise Refused(str(e)) from None
    dest = Path(root) / "research" / "runs" / mid / manifest.run_id
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        return _replay_run(root, rec, contract, target, rev, manifest, ledger, aid, task, dest,
                           head, dirty, started)
    except (Refused, Failed):
        raise
    except BaseException as e:
        # never leave the attempt `running`: an unexpected failure is the
        # infrastructure's, re-issuable, and the batch stays open to resume
        st = budget.Ledger(ledger.path).attempts().get(aid)
        if st is not None and st.state == "running":
            ledger.move(aid, "infra-failed", run_id=manifest.run_id,
                        cause=f"{type(e).__name__}: {e}"[:200], gpu_s=0)
        raise


def _replay_run(root, rec, contract, target, rev, manifest, ledger, aid, task, dest, head, dirty,
                started):
    apparatus, budget, runlog = _fvh()
    mid = rec["id"]
    run = sandbox.materialize(manifest, root)
    try:
        report = sandbox.selftest(manifest, run, root)
        sandbox.write_records(dest, manifest, report)
        staged = {e.dst: (run.inp / e.dst).read_bytes() for e in manifest.files}
        src_of = {e.dst: (e.src or e.dst) for e in manifest.files}
        runlog.write_inputs(dest, {src_of[e.dst]: staged[e.dst] for e in manifest.files
                                   if e.role == "editable"})
        if not report["ok"]:
            ledger.move(aid, "infra-failed", run_id=manifest.run_id, cause="selftest", gpu_s=0)
            raise Failed("the self-test failed (selftest.json in the run directory)")
        say(f"replay {manifest.run_id}: {mid}, {target}, from {rev[:12]}; agent opencode, "
            f"{manifest.agent['model']}, at most {manifest.agent['turns']} calls")
        try:
            code, live = sandbox.live_run(manifest, run, log=lambda m: say(m), root=root)
        except sandbox.Deferred as e:
            ledger.move(aid, "deferred", run_id=manifest.run_id, reason=str(e))
            raise Refused(f"deferred: {e}") from None
        except sandbox.SandboxError as e:
            ledger.move(aid, "infra-failed", run_id=manifest.run_id, cause=str(e)[:200], gpu_s=0)
            raise Failed(str(e)) from None
        live["manifest_sha256"] = manifest.sha256()
        g = live.pop("gate", None) or {}
        gate_text, counts_text = g.get("gate.log"), g.get("gate-counts.json")
        live["gate"] = {"files": sorted(g)}
        counts = json.loads(counts_text) if counts_text else {}
        ret = live.get("_returned")
        sandbox.write_live_records(dest, live, name="sandbox.json")
        if gate_text is not None:
            # every request carries the whole conversation, so the log grows with the
            # square of the turns (14 MB for Q07's 27-call replay): it is kept
            # compressed, under the run directory's cap (fvh.runlog.CAP_BYTES)
            import gzip
            (dest / "gate.log.gz").write_bytes(gzip.compress(gate_text.encode("utf-8"), mtime=0))
        if counts_text is not None:
            (dest / "gate-counts.json").write_text(counts_text, encoding="utf-8")
        calls, gpu_s = int(counts.get("calls") or 0), float(counts.get("gpu_s") or 0)
        ag = live.get("agent") or {}
        if code != 0 and calls == 0:
            # an infrastructure failure before model output: re-issuable (§4.3 rule 3),
            # the batch stays open for the next run to resume
            ledger.move(aid, "infra-failed", run_id=manifest.run_id, cause=live.get("ended_by"),
                        gpu_s=gpu_s)
            say(f"failed before any model output ({live.get('ended_by')}): the attempt is "
                "re-issuable; the next run resumes it", err=True)
            return 1
        after = dict((k, v) for k, v in staged.items()
                     if any(e.dst == k and e.role == "editable" for e in manifest.files))
        if ret is not None:
            after.update(ret.returned)
        findings = []
        if counts.get("ctx_saturated"):
            findings.append(f"ctx-saturated:{counts['ctx_saturated']}")
        if (live.get("secret_scan") or {}).get("withheld") or ag.get("transcript_withheld"):
            findings.append("secret-scan:withheld")
        deleted = sorted(ret.deleted) if ret is not None else []
        if code != 0:
            outcome = "truncated:container"
            ended_by = "truncated:container"
            verdict_lines, doc, vrec = [], None, None
        else:
            if deleted:
                findings.append("deleted:" + ",".join(deleted))
            cmds = acceptance_commands(contract)
            vraw = verify_manifest(root, rec, manifest, after, cmds, manifest.run_id) \
                if cmds and not deleted else None
            vrec, results = None, []
            if vraw is not None:
                vman = sandbox.validate(vraw, root)
                vrun = sandbox.materialize(vman, root)
                try:
                    say(f"verification container: {len(cmds)} acceptance command(s) on the returned files")
                    vcode, vrec = sandbox.live_run(vman, vrun, log=lambda m: say(m), root=root)
                finally:
                    sandbox.remove_run(vrun)
                results = vrec.get("commands", [])
                if vcode != 0 or len(results) != len(cmds):
                    findings.append(f"verify-container:{vrec.get('ended_by')}")
            verdict_lines, doc = judge(contract, cmds, results)
            outcome = (doc or {}).get("verdict") if (doc or {}).get("verdict") in \
                ("verified", "failed", "inconclusive", "refused", "killed(memory)", "error") else "error"
            ended_by = {"wall-clock": "wall-clock"}.get(ag.get("ended"), "stop")
            if calls >= manifest.agent["turns"]:
                ended_by = "call-cap"
            if counts.get("capped"):
                ended_by = "gpu-cap" if (gpu_s >= manifest.agent.get("gpu_s", 1e9)) else "call-cap"
            if ag.get("ended") == "error":
                outcome, ended_by = "truncated:cli-crash", "truncated:cli-crash"
        vdoc = {"schema": 1, "lines": [{"line": l, "form": f, "met": m, "evidence": _redact(ev)}
                                       for l, f, m, ev in verdict_lines],
                "gate": doc, "commands": [{"argv": c.get("argv"), "exit_code": c.get("exit_code"),
                                           "stdout": _redact(c.get("stdout")),
                                           "stderr": _redact(c.get("stderr"))[-4000:],
                                           "wall_s": c.get("wall_s")}
                                          for c in (vrec or {}).get("commands", [])],
                "container": {k: (vrec or {}).get(k) for k in ("run_id", "image", "ended_by",
                                                                  "memory_gb", "removed", "wall_s")}}
        (dest / "verify.json").write_text(json.dumps(vdoc, indent=1, sort_keys=True) + "\n",
                                          encoding="utf-8")
        cap = runlog.cap_finding(dest)
        if cap:
            findings.append(cap)
        lang = sandbox.lang_pool(target) or "dafny"
        meta = runlog.RunMeta(
            run_id=manifest.run_id, module=mid, arm=ARM, task_id=task, lang=lang, attempt=1,
            repeat=1, mode="agent", backend="opencode", outcome=outcome, ended_by=ended_by,
            verify=doc, usage={"calls": calls, "gpu_s": gpu_s,
                               "prompt_tokens": counts.get("prompt_tokens", 0),
                               "output_tokens": counts.get("output_tokens", 0),
                               "wall_s": live.get("wall_s"),
                               "agent_wall_s": ag.get("wall_s"), "steps": (ag.get("summary") or {}).get("steps")},
            apparatus={**apparatus.collect(apparatus.load(root=root), root),
                       "image": manifest.image, "agent_config_sha256": ag.get("config_sha256"),
                       "model_server_found": dict(live.get("model_server_found") or {}, **(
                           {"system_fingerprint": counts["system_fingerprint"]}
                           if counts.get("system_fingerprint") else {}))},
            course_commit=head, course_dirty=bool(dirty),
            inputs_sha256=runlog.inputs_tree_sha256({src_of[k]: v for k, v in staged.items()
                                                     if k in after}),
            manifest_sha256=manifest.sha256(), selftest={"ok": report["ok"]},
            return_summary=(live.get("return") or {}), secret_scan=(live.get("secret_scan") or {}),
            findings=tuple(findings), ledger_seq=ledger.head()[0], started=started,
            ended=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        runlog.write_meta(dest, meta)
        ledger.move(aid, "scored", run_id=manifest.run_id, outcome=outcome, calls=calls,
                    gpu_s=round(gpu_s, 3))
        budget.close_batch(root, mid, course_commit=head)
    finally:
        sandbox.remove_run(run)
    rel = dest.relative_to(root)
    diff = (dest / "patch.diff").read_text(encoding="utf-8") if (dest / "patch.diff").is_file() else ""
    plus = sum(1 for x in diff.splitlines() if x.startswith("+") and not x.startswith("+++"))
    minus = sum(1 for x in diff.splitlines() if x.startswith("-") and not x.startswith("---"))
    print(f"run directory: {rel}/")
    print(f"patch: {rel}/patch.diff ({plus} line(s) added, {minus} removed); never applied: "
          "read it, and apply it by hand only if you choose to")
    print(f"agent: {calls} model call(s), {gpu_s:.0f} GPU-s, ended by {ended_by}")
    checked = [x for x in verdict_lines if x[2] is not None]
    for line, form, met, ev in verdict_lines:
        tag = "met" if met else "NOT met" if met is False else "for your audit"
        print(f"  [{tag}] {line[:110]}" + (f" ({_redact(ev)})" if met is not None else ""))
    n_bad = sum(1 for x in checked if not x[2])
    print(f"verdict: {outcome}; " + (f"every checked acceptance line met ({len(checked)})" if checked
                                     and not n_bad else f"{n_bad} of {len(checked)} checked "
                                     "acceptance line(s) not met" if checked else
                                     "no acceptance line was checked")
          + f"; {sum(1 for x in verdict_lines if x[2] is None)} line(s) for your audit")
    return 0


# --- the command -------------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(prog="contract_local.sh", allow_abbrev=False,
                                 description="Replay a module's contract under a local Qwen in a "
                                             "per-run container (DV4-PLAN §6).")
    ap.add_argument("module")
    ap.add_argument("--file", metavar="AGENTIC_PATH")
    ap.add_argument("--model")             # default: DVL_MODEL, else the server's only model
    ap.add_argument("--from", dest="from_rev", metavar="REV")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--available", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    ap.add_argument("--root", help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    root = Path(a.root).resolve() if a.root else REPO_ROOT
    try:
        rec = record(root, a.module.upper())
        if a.available:
            problems = availability(root, rec, a.model)
            for p in problems:
                say(f"not available: {p}", err=True)
            if problems:
                return 3
            say(f"{rec['id']}: the replay can run here")
            return 0
        problems = module_checks(rec)
        if problems:
            raise Refused(problems[0])
        agentic = [p for p in rec["agentic"] if not p.endswith("/")]
        if a.file:
            if a.file not in agentic:
                raise Refused(f"--file {a.file} is not in {rec['id']}'s agentic list")
            target = a.file
        elif len(agentic) == 1:
            target = agentic[0]
        else:
            raise Refused(f"{rec['id']} lists {len(agentic)} agentic files: name one with --file")
        path = root / target
        if not path.is_file():
            raise Refused(f"{target} does not exist")
        contract = parse_header(path.read_text(encoding="utf-8"))
        for p in contract["allowed-files"]:
            why = path_problem(p, rec)
            if why:
                raise Refused(f"allowed file {p}: {why}")
        rev, snap = starting_state(root, contract, a.from_rev)
        if not a.model:
            try:
                a.model = sandbox.discover_server(root)["model"]
            except sandbox.SandboxError:
                a.model = NO_MODEL       # the checks below name why (server_checks)
        raw = build_manifest(root, rec, contract, rev, snap, a.model)
        try:
            manifest = sandbox.validate(raw, root, check_image=False)
        except sandbox.ManifestError as e:
            raise Refused("the replay's manifest is refused: " + "; ".join(e.problems)) from None
        if not a.dry_run:
            return replay(root, rec, contract, target, rev, snap, raw)
        run = sandbox.materialize(manifest, root)
        try:
            report = sandbox.selftest(manifest, run, root)
        finally:
            sandbox.remove_run(run)
        say(f"dry run of {rec['id']}'s contract replay ({target}); nothing runs")
        print(f"starting state: {rev}" + (f" (the commit that last changed the snapshot {snap})" if snap
                                          and not a.from_rev else f" (--from {a.from_rev})"))
        print(f"allowed files (staged at that commit; returned as patch.diff, never applied): "
              f"{', '.join(contract['allowed-files'])}")
        print(f"manifest: {len(manifest.files)} files (" + ", ".join(
            f"{r} {sum(1 for e in manifest.files if e.role == r)}" for r in sandbox.ROLES
            if any(e.role == r for e in manifest.files)) + f"), sha256 {manifest.sha256()[:16]}")
        print(f"agent: opencode, {a.model}, at most {manifest.agent['turns']} turns (one gated "
              f"call each); network model (the run's gate); --memory {manifest.limits['mem_gb']:g}g")
        print("acceptance lines:")
        for line in contract["acceptance"]:
            form, _ = classify_line(line)
            where = {"vcheck-gate": "checked in the verification container",
                     "zero-holes": "checked from the same gate run",
                     "specfreeze-against": "checked in the verification container, against the read-only snapshot",
                     "vaudit": "checked in the verification container",
                     "vaudit-compare": "checked in the verification container, with the trusted pin",
                     "git-diff": "for your audit; its evidence is patch.diff",
                     "audit": "for your audit, with the transcript"}[form]
            print(f"  - [{form}] {where}: {line[:100]}")
        print("self-test: " + ("OK" if report["ok"] else "FAILED"))
        for name, chk in report["checks"].items():
            for p in chk.get("problems", []):
                print(f"  {name}: {p}")
        print("docker argv (nothing was run; $RUN is the run directory):")
        for line in sandbox.docker_argv(manifest, "$RUN"):
            print("  " + shlex.join(line))
        docker = docker_checks()
        later = image_checks(root, local=not docker) + ledger_checks(root, rec) \
            + apparatus_checks(root) + server_checks(root, None if a.model == NO_MODEL else a.model) \
            + docker
        for p in later:
            print(f"not yet available: {p}")
        return 0 if report["ok"] else 1
    except Refused as e:
        say(f"refused: {e}", err=True)
        return 3
    except (sandbox.SandboxError, OSError) as e:
        say(f"failed: {e}", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
