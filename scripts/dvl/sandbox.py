"""dvl.sandbox: the host side of the per-run agent sandbox (DV4-PLAN §5).

`scripts/mksandbox-run` is the one program that starts a container (rule 1f's
single route, Δ83); this library is everything it does before and after one,
and it never runs a container itself. Standard library only.

Built at DV4 step 1b, without Docker:

  manifests       schema 1 (TOML or JSON), its roles and the refused source
                  classes (§5.3): `load_manifest`, `validate`, `source_class`
  materialization the run directory under $XDG_RUNTIME_DIR/dvl-runs/<random>/
                  with in/ work/ out/ state/ (§5.3): `materialize`
  the self-test   the static part (§5.4 items 1-5): closure, canary prefix,
                  attested task cards, public answers, and the author-only
                  checks recorded as skipped in a study run (P6): `selftest`
  the docker argv every container flag of §5.5 and the two tar streams of
                  §5.8 (golden lines for `--dry-run`): `docker_argv`
  the return path a `docker exec … tar --create` stream parsed member by
                  member without extraction (§5.8): `parse_return`
  the secret scan the credential formats and an exact token (§5.7): `secret_scan`
  records         manifest.json and selftest.json for research/runs (§3.6):
                  `write_records`
  docker access   the read-only check and its diagnosis; never sudo (§5.1, P8):
                  `check_access`
  attestation     the author-only scan of a lab task card (§5.4 item 3):
                  `attest` (self-gated, Δ103); the scan is `author_scan` over
                  `scan_index` (DV5e: whole and renamed answer spans, generic
                  structure set aside)

Built at DV4 step 2 (Docker, no model):

  the layout      /work is a size-capped tmpfs that only root may write; each
                  directory that holds an editable file is a tmpfs of its own
                  (mode 1777), so that uid 1000 can write the editable files
                  beside the read-only binds runc mounts there; every other
                  directory under /work is runc's (root, 0755): `docker_argv`
  commands        a manifest's [[command]] lines: the trusted course tools
                  (scripts/vcheck, scripts/vaudit, scripts/specfreeze) on staged
                  paths, run with `docker exec` after the input stream
  the verify      `build_verify`: the verify manifest of one tool command on
  manifest        one target (a course path, or a work copy outside the course
                  root whose course path is found by suffix), with the module's
                  given chain, project files, tools and pins read-only
  the live run    `live_run`: the memory preflight, one sandbox job at a time,
                  the gate (model networks, Route B), the watcher, docker run,
                  the input stream, the in-container controls, the commands,
                  the return stream (agent runs), the removal, the records
  the reaper      `reap`: remove every dvl.run container whose owner is gone

Built at DV4 step 3 (Docker and the local model):

  the agent       an [agent] cli "opencode" run (`agent_lines`, `_run_agent`):
                  the GPU calendar lock, the gate with the apparatus file's
                  pins and caps (`agent_gate_config`), the agent's config in
                  (`opencode_config`), the per-run gate on its two debug views
                  (`opencode_precheck`), the run under the in-container
                  timeout, the event stream after the secret scan
                  (transcript.jsonl.gz); the tool copies the contract names are
                  executable, so its lines run unchanged in container-agent mode

Neutral wording: the self-test's regression checks name what must be refused,
never how a delivery could get past it.
"""

from __future__ import annotations

import dataclasses
import difflib
import hashlib
import io
import json
import os
import posixpath
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import tomllib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SCHEMA = 1
KINDS = ("agent", "verify")
NETWORKS = ("none", "ollama", "anthropic")
ROLES = ("editable", "task", "given", "project", "tool", "expected", "snapshot", "contract")
READ_ONLY_ROLES = tuple(r for r in ROLES if r != "editable")
# Roles whose content may be written inline (`text`) by the trusted builder
# (fvh or contract_local.sh): a stripped task statement, the contract text, a
# generated project file (a workspace that lists only the run's crates).
TEXT_ROLES = ("task", "contract", "project")
# "none": a probe agent container (`mksandbox-run --probe` only): the agent image, the
# agent memory bound and container-agent mode, and no agent CLI ever starts in it.
AGENT_CLIS = ("opencode", "claude", "none")

TOP_KEYS = {"schema", "run_id", "module", "kind", "image", "network", "limits", "file",
            "return", "agent", "command", "truth"}
COMMAND_KEYS = {"argv"}
MAX_COMMANDS = 12
# [[command]] argv[0] -> (flag options, options that take a staged path)
COMMAND_TOOLS = {
    "scripts/vcheck": ({"--gate", "--json", "--brittleness", "--test"}, {"--lab-task"}),
    "scripts/vaudit": ({"--json"}, {"--compare"}),
    "scripts/specfreeze": (set(), {"--against"}),
}
CONTROLS = "/opt/dvl/bin/controls"          # the image's containment controls (sandbox/image/)
# The grader container's truth mode (DV4-PLAN §5.9, QPLAN §30 Q49): the image's grader,
# the pins of the sealed archives, and where a truth run binds the archive and the key.
TRUTHCHECK = "/opt/dvl/bin/truthcheck"
TRUTH_FILE = "sandbox/truth.toml"
TRUTH_DIR = "/run/dvl-truth"
TRUTH_KEYS = {"lab", "archive", "sha256"}
TRUTH_MODES = ("manifest", "validate", "judge")   # judge: dvl.judge builds its manifest
DOORS = ("alloc", "pids", "sleep", "stage-return", "secret", "http")
CONTAINER_SCRATCH = "/tmp/dvl-scratch"      # DVL_SCRATCH inside a container (fvh redacts it)
CONTAINER_PYTHON = "/usr/bin/python3"
FILE_KEYS = {"src", "dst", "role", "sha256", "rev", "text"}
AGENT_KEYS = {"cli", "model", "turns", "gpu_s"}     # gpu_s: optional, the run's GPU-seconds cap
# [limits]: name -> (type, lowest, highest). mem_gb is bounded by the pins
# instead (memory_bound_gb).
LIMITS = {
    "mem_gb": (float, 0.5, None),
    "cpus": (float, 0.5, 8.0),
    "pids": (int, 32, 4096),
    "wall_clock_s": (int, 1, 4 * 3600),
    "work_mb": (int, 16, 2048),
    "tmp_mb": (int, 16, 4096),
}
LIMIT_DEFAULTS = {"cpus": 2.0, "pids": 512, "wall_clock_s": 1800, "work_mb": 512, "tmp_mb": 1536}
NOFILE = 4096
CONTAINER_UID = "1000:1000"
WORK = "/work"
RELAY_DIR = "/run/dvl"
ENTRY = "/opt/dvl/bin/entry"        # the image's entry point (sandbox/, step 2a)
RUNS_DIR_NAME = "dvl-runs"

# --- source classes (§5.3) ------------------------------------------------------------------
#
# What never enters a sandbox, by source class, refused before anything is
# copied. The reference rows are the guard's (rule 1's RX_SPOIL_DIR in
# .claude/hooks/spoiler-guard.sh) and the checker's (is_reference in
# scripts/check_course_map.py: a path component named solutions*, hidden or
# leak_patterns, <id>_solutions, or an .age file); `class_drift` (the static
# job's check) keeps the three in step: every path either of them treats as
# reference is refused here.
#   (class, kind, pattern): kind "prefix" (a repo-relative path prefix),
#   "component" (any path component equal), "regex" (re.search on the path).
REFUSED_CLASSES = (
    ("reference", "prefix", "Solutions/"),
    ("reference", "prefix", "paper/solutions/"),
    ("reference", "prefix", "tests/instructor/leak_patterns/"),
    ("reference", "prefix", "tests/instructor/fixtures/"),
    ("reference", "regex", r"(?i)(^|/)(solutions|leak_patterns|[rq]\d\d_solutions)[^/]*(/|$)"),
    ("reference", "regex", r"(?i)(^|/)[^/]*\.age$"),
    ("held-out", "regex", r"(?i)(^|/)hidden(/|\.|$)"),
    ("held-out", "regex", r"(?i)(^|/)unseal"),
    ("instructor", "prefix", "instructor/"),
    ("guard", "prefix", ".claude/"),
    ("guard", "regex", r"(^|/)CLAUDE(\.local)?\.md$"),
    ("history", "component", ".git"),
    ("bench-answers", "regex", r"^bench/(.*/)?answers(/|$)"),
    ("bench-config", "prefix", "bench/manifest.toml"),
    ("research", "prefix", "research/"),
    ("chapters", "prefix", "docs/"),
    ("written", "prefix", "paper/"),
    ("tests", "prefix", "tests/"),
    ("sandbox-config", "prefix", "sandbox/"),
    ("build-output", "regex", r"(^|/)(target|build|\.verus-log|\.verus-solver-log|__pycache__|"
                              r"TestResults|\.venv|\.pytest_cache|[^/]+-(py|go|java))(/|$)"),
    ("solo", "prefix", "Challenges/"),
    ("solo", "prefix", "agents/"),
)
# The one exception (§5.3, §6): a `snapshot` a CONTRACT names may be read
# from research/, at a commit (`rev`), never from the working tree.
SNAPSHOT_EXEMPT = ("research",)

# The trusted course tools the in-container verifier runs (§5.3, author
# notes §1.5). Beyond the plan's list: the modules vcheck imports
# (check_course_map.py, gen_units.py), the files it reads (course_mode.sh for
# the learner prefix, dafny/options/ for the per-tier Dafny options) and
# get_toolchain.sh, whose --check every solver call runs first.
TRUSTED_TOOLS = ("scripts/vcheck", "scripts/vaudit", "scripts/specfreeze",
                 "scripts/course_items.py", "scripts/check_course_map.py", "scripts/gen_units.py",
                 "scripts/course_mode.sh", "scripts/get_toolchain.sh", "MODULES.toml")
TRUSTED_TOOL_DIRS = ("scripts/dvl/",)
TRUSTED_TOOL_EXT = (".py", ".toml")
PROJECT_NAMES = ("dfyconfig.toml", "Cargo.toml", "Cargo.lock", "rust-toolchain.toml",
                 "rust-toolchain", "pyproject.toml", "uv.lock")
OPTIONS_DIR = "dafny/options/"

# Canaries (§5.4 item 2): detected by their public prefix, attributed by the
# sha256 of the full token in sandbox/canaries.sha256. No secret is needed.
CANARY_PREFIX = "DVLCANARY-"
CANARY_TOKEN = re.compile(rb"DVLCANARY-[A-Za-z0-9_-]+")

# Public answers (§5.4 item 4): normalized token windows (comments dropped,
# identifiers, numbers and single punctuation characters). Calibrated at DV4
# step 1b against the five sets installed at their pins (3,647 answer files):
# with the given layers excluded, the 174 shipped Q01-Q06 files share up to 10
# distinct windows of 24 tokens with one answer (shared idioms such as an array
# swap or a bounded forall), and none at 32 tokens. So the plan's [A] 24 tokens
# and 3 windows would misfire on course files, and the pins are 32 tokens and
# 4 windows (a copied run of 35 tokens or more), which leaves a margin for the
# lines a learner adds. A task's own shipped form is excluded, so no public
# task form is flagged as staged.
WINDOW_TOKENS = 32
WINDOW_THRESHOLD = 4

# The return path (§5.8) [A].
RETURN_CAP_BYTES = 1 << 20

# Secret scan (§5.7): the credential formats, by id. Hits are reported by id
# and offset, never by content.
SECRET_PATTERNS = (
    ("anthropic-token", re.compile(rb"sk-ant-[a-z]{2,6}\d{2}-[A-Za-z0-9_-]{20,}")),
    ("oauth-json-key", re.compile(rb'"(accessToken|refreshToken)"\s*:\s*"[^"]{8,}"')),
    ("bearer-header", re.compile(rb"(?i)authorization:\s*bearer\s+[A-Za-z0-9._~+/=-]{20,}")),
    ("private-key", re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("github-token", re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
)


class ManifestError(Exception):
    """The manifest is refused (exit 3). `problems` lists every reason."""

    def __init__(self, problems):
        self.problems = list(problems) if isinstance(problems, (list, tuple)) else [str(problems)]
        super().__init__("; ".join(self.problems))


class SandboxError(Exception):
    """A step of the sandbox failed (exit 1): materialization, the stream."""


# --- small helpers ---------------------------------------------------------------------------

def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load_pins():
    from dvl import common
    return common.load_pins()


def container_pins():
    """The [container] table of scripts/dvl/pins.toml (read-only pins; never
    from the environment, §5.9)."""
    c = load_pins().get("container")
    if not isinstance(c, dict):
        raise SandboxError("scripts/dvl/pins.toml has no [container] table")
    for k in ("margin_gb", "work_gb", "tmp_gb", "home_gb", "agent_allowance_gb"):
        if not isinstance(c.get(k), (int, float)) or c[k] < 0:
            raise SandboxError(f"scripts/dvl/pins.toml [container] lacks a number {k}")
    return c


def tmpfs_gb(c=None):
    c = c or container_pins()
    return float(c["work_gb"]) + float(c["tmp_gb"]) + float(c["home_gb"])


def job_cap_gb(pool):
    pins = load_pins()
    t = pins.get(pool)
    if isinstance(t, dict) and isinstance(t.get("mem_gb"), (int, float)):
        return float(t["mem_gb"])
    return 4.0 if pool == "python" else 8.0


def home_mb():
    """The home tmpfs in MiB (pins [container] home_gb)."""
    return int(float(container_pins()["home_gb"]) * 1024)


def lang_pool(path):
    suffix = PurePosixPath(path).suffix
    return {".dfy": "dafny", ".rs": "verus", ".py": "python"}.get(suffix)


def memory_bound_gb(kind, pools):
    """The container's --memory (= --memory-swap) cap (§5.10): the largest
    pinned job cap of the run's languages + the margin + the tmpfs caps, plus
    the agent allowance in an agent container."""
    c = container_pins()
    cap = max([job_cap_gb(p) for p in pools] or [job_cap_gb("dafny")])
    bound = cap + float(c["margin_gb"]) + tmpfs_gb(c)
    if kind == "agent":
        bound += float(c["agent_allowance_gb"])
    return bound


def rel_ok(p):
    """A repo- or /work-relative path: no leading /, no ./ or .. segment, no glob."""
    if not isinstance(p, str) or not p or p.startswith("/") or "\\" in p or "\0" in p:
        return False
    parts = p.split("/")
    if any(x in ("", ".", "..") for x in parts):
        return False
    return not any(ch in p for ch in "*?[]")


def source_class(rel):
    """The refused class of a repo-relative path, or None when it may enter."""
    for cls, kind, pat in REFUSED_CLASSES:
        if kind == "prefix" and (rel == pat.rstrip("/") or rel.startswith(pat)):
            return cls
        if kind == "component" and pat in rel.split("/"):
            return cls
        if kind == "regex" and re.search(pat, rel):
            return cls
    return None


def runs_base():
    """$XDG_RUNTIME_DIR/dvl-runs (a per-user tmpfs, mode 0700, §5.3)."""
    base = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    return Path(base) / RUNS_DIR_NAME


# --- the registry ---------------------------------------------------------------------------

def registry_record(root, mid):
    """The module's record through check_course_map (the one registry reader)."""
    import check_course_map as ccm
    data, err = ccm.load_registry(Path(root))
    if err:
        raise ManifestError(f"the registry is unusable: {err}")
    for m in data.get("module", []):
        if str(m.get("id", "")).upper() == str(mid).upper():
            return m
    raise ManifestError(f"module {mid!r} is not in MODULES.toml")


def layer_chain(layer):
    if not layer:
        return ()
    import gen_units
    return tuple(gen_units.layer_chain(layer))


PY_GIVEN = (
    re.compile(r"^harness/fvh/(?:[A-Za-z0-9_]+/)*[A-Za-z0-9_]+\.py$"),     # the frozen core
    re.compile(r"^harness/tests/conftest\.py$"),                           # the network tripwire
    re.compile(r"^harness/tests/([qr])/(?:[A-Za-z0-9_]+/)*test_[A-Za-z0-9_]+\.py$"),
    re.compile(r"^harness/([qr])/fvh_\1/(?:[A-Za-z0-9_]+/)*__init__\.py$"),   # package markers
)
PY_PROJECT = ("harness/pyproject.toml", "harness/uv.lock")


def python_given_ok(rel, rec):
    """Is `rel` a support file of a Python acceptance run for module `rec`: the
    frozen core harness/fvh/, the tests' conftest and frozen acceptance tests,
    the learner packages' __init__ markers, and the module's own recorded
    fixtures harness/tests/<q|r>/fixtures/<id>/ (DV4-PLAN §5.9: Python
    acceptance tests run only in the verification container)?"""
    if not rec.get("harness") or source_class(rel) is not None:
        return False
    if any(rx.match(rel) for rx in PY_GIVEN):
        return True
    mid = str(rec.get("id", "")).lower()
    return bool(mid) and re.match(rf"^harness/tests/[qr]/fixtures/{re.escape(mid)}/", rel) is not None


def python_support(root, rec, rel, rev=None):
    """[(src, role)] of the read-only inputs a Python acceptance run of the
    learner file `rel` needs (python_given_ok's files and the project's
    pyproject.toml and uv.lock), listed from the tree (or at `rev`)."""
    m = re.match(r"^harness/([qr])/fvh_\1/(.+)\.py$", rel)
    if not m:
        return []
    t, rest = m.group(1), m.group(2)
    names = _tree_files(root, "harness", rev)
    out = [(f, "project") for f in PY_PROJECT if f in names]
    sub = rest.rsplit("/", 1)[0] + "/" if "/" in rest else ""
    test = f"harness/tests/{t}/{sub}test_{rest.rsplit('/', 1)[-1]}.py"
    mid = str(rec.get("id", "")).lower()
    battery = f"expected/{rec.get('id')}.battery"
    if battery in _tree_files(root, "expected", rev):
        out.append((battery, "expected"))
    for f in sorted(names):
        if f.startswith("harness/fvh/") and PY_GIVEN[0].match(f):
            out.append((f, "given"))
        elif f == "harness/tests/conftest.py" or f == test:
            out.append((f, "given"))
        elif PY_GIVEN[3].match(f) and (f.startswith(f"harness/{t}/fvh_{t}/{sub}") or
                                       f.count("/") <= 3):
            out.append((f, "given"))
        elif mid and f.startswith(f"harness/tests/{t}/fixtures/{mid}/") and source_class(f) is None:
            out.append((f, "given"))
    return out


def _tree_files(root, prefix, rev=None):
    """The regular files under `prefix` (course-relative), from the working tree
    or, with `rev`, from git at that commit."""
    root = Path(root)
    if rev:
        p = subprocess.run(["git", "-C", str(root), "ls-tree", "-r", "--name-only", rev, "--",
                            prefix], capture_output=True, text=True, timeout=60)
        if p.returncode != 0:
            raise ManifestError(f"{prefix} cannot be listed at {rev}")
        return {x for x in p.stdout.splitlines() if x}
    out = set()
    base = root / prefix
    for f in base.rglob("*") if base.is_dir() else []:
        r = f.relative_to(root).as_posix()
        if f.is_file() and not f.is_symlink() and source_class(r) is None:
            out.add(r)
    return out


def given_ok(rel, rec):
    """Is `rel` a given file of the module's layer chain (Dafny file group or
    Verus layer crate), or a support file of its Python acceptance runs
    (python_given_ok)?"""
    import gen_units
    if python_given_ok(rel, rec):
        return True
    chain = layer_chain(rec.get("layer", ""))
    for layer in chain:
        track = gen_units.layer_track(layer)
        ddir = f"dafny/given/{track}/"
        if rel.startswith(ddir) and "/" not in rel[len(ddir):] \
                and rel[len(ddir):].startswith(gen_units.dafny_layer_prefix(layer)):
            return True
        vdir = gen_units.verus_given_crate_dir(layer) + "/"
        if rel.startswith(vdir) and source_class(rel) is None:
            return True
    return False


def unit_dirs(rec):
    return [u.rstrip("/") for u in rec.get("units", [])]


def project_ok(rel, rec):
    name = PurePosixPath(rel).name
    if rel.startswith(OPTIONS_DIR):
        return True
    if name not in PROJECT_NAMES:
        return False
    parent = str(PurePosixPath(rel).parent)
    if parent in unit_dirs(rec):
        return True
    if rel in ("verus/Cargo.toml", "verus/Cargo.lock", "verus/rust-toolchain.toml",
               "harness/pyproject.toml", "harness/uv.lock"):
        return True
    return given_ok(rel, rec)


def tool_ok(rel):
    if rel in TRUSTED_TOOLS:
        return True
    return any(rel.startswith(d) and "/" not in rel[len(d):] and rel.endswith(TRUSTED_TOOL_EXT)
               for d in TRUSTED_TOOL_DIRS)


def expected_ok(rel, mid):
    m = re.fullmatch(r"expected/([A-Za-z0-9_.-]+)", rel)
    if not m:
        return False
    name = m.group(1)
    if name in (f"{mid}.counts", f"{mid}.freeze", "verus_trust.toml", f"{mid}.battery"):
        return True             # verus_trust.toml: the trust allowlist every Verus gate reads;
                                # <ID>.battery: a Python acceptance test's pinned outcome (Q12)
    return name.lower().startswith(mid.lower()) and name.endswith(".audit")


def agentic_ok(rel, rec):
    for a in rec.get("agentic", []):
        if rel == a or (a.endswith("/") and rel.startswith(a)):
            return True
    return False


LEARNER_LISTS = ("exercises", "exits", "agentic", "harness")


def learner_ok(rel, rec):
    """Is `rel` one of the module's learner files: a path its registry lists
    (exercises, exits, agentic, harness), or a source file of one of its units
    (never a project file, never a refused class)? A verify run's editable
    inputs are these, or a benchmark task."""
    if source_class(rel) is not None:
        return False
    for key in LEARNER_LISTS:
        for a in rec.get(key, []):
            if rel == a or (a.endswith("/") and rel.startswith(a)):
                return True
    if PurePosixPath(rel).name in PROJECT_NAMES:
        return False
    return any(rel.startswith(u + "/") for u in unit_dirs(rec))


def bench_task(rel):
    """A benchmark task path: `bench/public/<set>/tasks/…`, `bench/local/<q|r>/<lab>/tasks/…`
    or a lab card's `bench/local/<q|r>/<lab>/<card>/tasks/…` (Lab 1's and Lab 2's layout),
    or a crate card's `…/tasks` directory itself (Lab 3's layout: the crate is the task)."""
    return re.match(r"^bench/(public/[^/]+|local/[qr]/[^/]+(/[^/]+)?)/tasks(/|$)", rel) is not None


def stratum_module(root, rel):
    """The module a local benchmark task belongs to: the `lab` field of its
    stratum's `bench/local/<q|r>/<lab>/STRATUM.toml`, or None (a public task,
    no stratum file, no field)."""
    m = re.match(r"^bench/local/([qr])/([^/]+)/", rel)
    if not m or not bench_task(rel):
        return None
    p = Path(root) / "bench" / "local" / m.group(1) / m.group(2) / "STRATUM.toml"
    try:
        lab = tomllib.loads(p.read_text(encoding="utf-8")).get("lab")
    except (OSError, ValueError):
        return None
    return lab if isinstance(lab, str) and lab else None


def lab_card(rel):
    return rel.startswith("bench/local/")


# --- manifests --------------------------------------------------------------------------------

@dataclass(frozen=True)
class Entry:
    src: str | None
    dst: str
    role: str
    sha256: str
    rev: str | None = None
    text: str | None = None


@dataclass(frozen=True)
class Manifest:
    schema: int
    run_id: str
    module: str
    kind: str
    image: str
    network: str
    limits: dict
    files: tuple
    returns: tuple
    agent: dict | None
    commands: tuple = ()
    truth: dict | None = None
    raw: dict = field(compare=False, repr=False, default_factory=dict)

    def doc(self):
        """The normalized manifest as plain data (what manifest.json records)."""
        return {"schema": self.schema, "run_id": self.run_id, "module": self.module,
                "kind": self.kind, "image": self.image, "network": self.network,
                "limits": dict(self.limits),
                "file": [{k: v for k, v in dataclasses.asdict(e).items() if v is not None}
                         for e in self.files],
                "return": list(self.returns),
                **({"agent": dict(self.agent)} if self.agent else {}),
                **({"command": [{"argv": list(c)} for c in self.commands]} if self.commands else {}),
                **({"truth": dict(self.truth)} if self.truth else {})}

    def editable_dirs(self):
        """The /work-relative directories that hold an editable file ("" for /work)."""
        return sorted({posixpath.dirname(e.dst) for e in self.files if e.role == "editable"})

    def sha256(self):
        return sha256_bytes(canonical_json(self.doc()).encode())

    def pools(self):
        return run_pools(self.files)


def run_pools(files):
    """The solver languages a run's memory bound is sized for: those of its
    editable files (what its commands verify), else of every staged file. A
    Python acceptance run stages recorded Dafny and Verus fixtures as data;
    they never size its container."""
    def lang(e):
        return lang_pool(e.dst if isinstance(e, Entry) else e.get("dst", ""))

    def role(e):
        return e.role if isinstance(e, Entry) else e.get("role")
    ed = {x for e in files if role(e) == "editable" for x in [lang(e)] if x}
    return sorted(ed or {x for e in files for x in [lang(e)] if x})


def load_manifest(path):
    """The raw manifest (a dict) from a .toml or .json file."""
    p = Path(path)
    try:
        data = p.read_bytes()
    except OSError as e:
        raise ManifestError(f"cannot read the manifest {path}: {e.strerror}") from None
    try:
        if p.suffix == ".json":
            raw = json.loads(data)
        else:
            raw = tomllib.loads(data.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        raise ManifestError(f"the manifest {path} does not parse: {e}") from None
    if not isinstance(raw, dict):
        raise ManifestError("the manifest is not a table")
    return raw


def read_images_lock(root):
    path = Path(root) / "sandbox" / "images.lock"
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as e:
        raise ManifestError(f"sandbox/images.lock is unusable: {e}") from None
    out = {}
    for img in data.get("image", []):
        name, digest = img.get("name"), img.get("digest")
        if isinstance(name, str) and isinstance(digest, str) \
                and re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            out[f"{name}@{digest}"] = img
    return out


def git_blob(root, rev, rel):
    """(content, mode) of rel at rev, or ManifestError. Only a regular file."""
    if not re.fullmatch(r"[0-9A-Za-z._/~^-]{1,80}", rev or ""):
        raise ManifestError(f"{rel}: rev {rev!r} is not a revision name")
    try:
        ls = subprocess.run(["git", "-C", str(root), "ls-tree", rev, "--", rel],
                            capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ManifestError(f"{rel}: git ls-tree failed ({e})") from None
    line = ls.stdout.decode("utf-8", "replace").strip()
    if ls.returncode != 0 or not line:
        raise ManifestError(f"{rel} does not exist at {rev}")
    mode, kind = line.split()[0], line.split()[1]
    if kind != "blob" or mode not in ("100644", "100755"):
        raise ManifestError(f"{rel} at {rev} is not a regular file (mode {mode} {kind})")
    show = subprocess.run(["git", "-C", str(root), "show", f"{rev}:{rel}"], capture_output=True,
                          timeout=60)
    if show.returncode != 0:
        raise ManifestError(f"{rel} at {rev} cannot be read")
    return show.stdout, mode


def read_source(root, e):
    """The bytes an entry stages: inline text, a blob at rev, or a regular file."""
    if e.text is not None:
        return e.text.encode("utf-8")
    if e.rev:
        return git_blob(root, e.rev, e.src)[0]
    p = Path(root) / e.src
    try:
        st = os.lstat(p)
    except OSError:
        raise ManifestError(f"{e.src} does not exist") from None
    if not stat.S_ISREG(st.st_mode):
        raise ManifestError(f"{e.src} is not a regular file (no symlink, device or directory "
                            "enters a sandbox)")
    # every parent directory must be a real directory too (no symlinked dir)
    cur = Path(root)
    for part in PurePosixPath(e.src).parts[:-1]:
        cur = cur / part
        if os.path.islink(cur):
            raise ManifestError(f"{e.src}: its directory {part}/ is a symlink")
    return p.read_bytes()


def validate(raw, root=REPO_ROOT, *, record=None, check_image=True, read=True):
    """A Manifest, or ManifestError listing every problem found.

    Checks the schema (no unknown key: there is no field for a host network,
    a socket, a device, a capability or a privileged mode), the kind and the
    network, the limits against their bounds and the memory pins, the image
    against sandbox/images.lock (unless `check_image` is false: --dry-run
    reports it separately), every file's role, source class, path and sha256,
    and the return set."""
    root = Path(root)
    problems = []

    def bad(msg):
        problems.append(msg)

    unknown = sorted(set(raw) - TOP_KEYS)
    if unknown:
        bad(f"unknown manifest key(s) {unknown}: schema 1 has no other field")
    if raw.get("schema") != SCHEMA:
        bad(f"schema must be {SCHEMA}, not {raw.get('schema')!r}")
    run_id = raw.get("run_id")
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", run_id):
        bad("run_id must be 1-64 characters of [A-Za-z0-9._-]")
        run_id = "invalid"
    mid = raw.get("module")
    rec = None
    if not isinstance(mid, str) or not re.fullmatch(r"[QR]\d\d", mid):
        bad("module must be a registry id (Qnn or Rnn)")
    else:
        try:
            rec = record if record is not None else registry_record(root, mid)
        except ManifestError as e:
            bad(str(e))
    kind = raw.get("kind")
    if kind not in KINDS:
        bad(f"kind must be one of {list(KINDS)}")
    network = raw.get("network", "none")
    if network not in NETWORKS:
        bad(f"network must be one of {list(NETWORKS)}")
    if kind == "verify" and network != "none":
        bad("a verify run is always network = \"none\"")
    image = raw.get("image")
    if not isinstance(image, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._/-]*@sha256:[0-9a-f]{64}", image):
        bad("image must be <name>@sha256:<64 hex digits>, a digest from sandbox/images.lock")
    elif check_image and image not in read_images_lock(root):
        bad(f"image {image} is not in sandbox/images.lock (the images are built at DV4 step 2a)")

    limits = dict(LIMIT_DEFAULTS)
    lim = raw.get("limits", {})
    if not isinstance(lim, dict):
        bad("[limits] must be a table")
        lim = {}
    for k in sorted(set(lim) - set(LIMITS)):
        bad(f"unknown [limits] key {k!r}")
    for k, (typ, lo, hi) in LIMITS.items():
        if k not in lim:
            continue
        v = lim[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or (typ is int and not isinstance(v, int)):
            bad(f"[limits] {k} must be a {typ.__name__}")
            continue
        if v < lo or (hi is not None and v > hi):
            bad(f"[limits] {k} = {v} is outside [{lo}, {hi if hi is not None else '…'}]")
            continue
        limits[k] = typ(v)

    probe_agent = (kind == "agent" and isinstance(raw.get("agent"), dict)
                   and raw["agent"].get("cli") == "none")
    rule = "verify" if probe_agent else kind      # whose editable rule applies
    files, seen_dst, snapshots = [], set(), 0
    raw_files = raw.get("file", [])
    if not isinstance(raw_files, list) or not raw_files:
        bad("a manifest stages at least one [[file]]")
        raw_files = []
    for i, f in enumerate(raw_files):
        where = f"[[file]] #{i + 1}"
        if not isinstance(f, dict):
            bad(f"{where} is not a table")
            continue
        unknown = sorted(set(f) - FILE_KEYS)
        if unknown:
            bad(f"{where}: unknown key(s) {unknown}")
        role, src, dst = f.get("role"), f.get("src"), f.get("dst")
        text, rev, digest = f.get("text"), f.get("rev"), f.get("sha256")
        where = f"[[file]] {src or dst or '#' + str(i + 1)}"
        if role not in ROLES:
            bad(f"{where}: role must be one of {list(ROLES)}")
            continue
        if not rel_ok(dst):
            bad(f"{where}: dst must be a relative path under /work (no '..', no glob)")
            continue
        if dst in seen_dst:
            bad(f"{where}: dst {dst} is staged twice")
            continue
        seen_dst.add(dst)
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            bad(f"{where}: sha256 must be 64 lower-case hex digits")
            continue
        if text is not None:
            # A verify run's editable file may be inline: the work copy or the
            # returned file it verifies (agent output), at its course path. So may
            # an agent run's editable benchmark task file: the work copy an fvh
            # agent-mode attempt continues from (arm G's refused stop; DV5d), whose
            # card the self-test still requires attested (selftest item 3).
            verify_text = role == "editable" and (
                kind == "verify" or probe_agent
                or (kind == "agent" and isinstance(dst, str) and bench_task(dst)))
            if role not in TEXT_ROLES and not verify_text:
                bad(f"{where}: only roles {list(TEXT_ROLES)} may carry inline text "
                    "(and an editable file of a verify run, or an agent run's editable "
                    "benchmark task file)")
                continue
            if src is not None or rev is not None:
                bad(f"{where}: an inline text has no src or rev")
                continue
            if not isinstance(text, str):
                bad(f"{where}: text must be a string")
                continue
            if role == "project" and PurePosixPath(dst).name not in PROJECT_NAMES:
                bad(f"{where}: a generated project file is one of {list(PROJECT_NAMES)}")
                continue
            if verify_text:
                if len(text.encode("utf-8")) > RETURN_CAP_BYTES:
                    bad(f"{where}: an inline editable file is over the size cap ({RETURN_CAP_BYTES} bytes)")
                    continue
                cls = source_class(dst)
                if cls:
                    bad(f"{where}: {dst} is in a refused source class ({cls})")
                    continue
                if rec is not None:
                    why = _role_problem(role, dst, None, rec, mid, kind)
                    if why:
                        bad(f"{where}: {why}")
                        continue
            e = Entry(None, dst, role, digest, None, text)
        else:
            if not rel_ok(src):
                bad(f"{where}: src must be a course-relative path (no leading '/', no '..', no glob)")
                continue
            if rev is not None and not isinstance(rev, str):
                bad(f"{where}: rev must be a string")
                continue
            cls = source_class(src)
            if cls and not (role == "snapshot" and cls in SNAPSHOT_EXEMPT and rev):
                bad(f"{where}: {src} is in a refused source class ({cls}); it never enters a sandbox")
                continue
            if rec is not None:
                why = _role_problem(role, src, rev, rec, mid, rule)
                if why:
                    bad(f"{where}: {why}")
                    continue
            e = Entry(src, dst, role, digest, rev, None)
        if role == "snapshot":
            snapshots += 1
            if not e.rev:
                bad(f"{where}: a snapshot is read at a commit (rev), never from the working tree")
                continue
        if read:
            try:
                content = read_source(root, e)
            except ManifestError as err:
                bad(f"{where}: {err}")
                continue
            if sha256_bytes(content) != digest:
                bad(f"{where}: its content does not match its sha256")
                continue
        files.append(e)
    if snapshots > 1:
        bad("at most one snapshot (the one a CONTRACT names) may enter")

    returns = raw.get("return", [])
    if not isinstance(returns, list):
        bad("[[return]] must be a list")
        returns = []
    paths = []
    for r in returns:
        p = r.get("path") if isinstance(r, dict) else r
        if not rel_ok(p):
            bad(f"return path {p!r} must be a relative path under /work")
            continue
        paths.append(p)
    editable = {e.dst for e in files if e.role == "editable"}
    if kind == "verify" and paths:
        bad("a verify run returns nothing ([[return]] must be empty)")
    if kind == "agent":
        if not paths and not probe_agent:
            bad("an agent run names its [[return]] paths (the allowed files)")
        for p in paths:
            if p not in editable:
                bad(f"return path {p} is not a staged editable file")
        if not editable:
            bad("an agent run stages at least one editable file")
    if len(set(paths)) != len(paths):
        bad("a return path is listed twice")

    agent = raw.get("agent")
    if agent is not None:
        if not isinstance(agent, dict):
            bad("[agent] must be a table")
            agent = None
        else:
            for k in sorted(set(agent) - AGENT_KEYS):
                bad(f"unknown [agent] key {k!r}")
            if agent.get("cli") not in AGENT_CLIS:
                bad(f"[agent] cli must be one of {list(AGENT_CLIS)}")
            if not isinstance(agent.get("model"), str) or not agent.get("model"):
                bad("[agent] model must name a pinned model tag")
            t = agent.get("turns")
            if isinstance(t, bool) or not isinstance(t, int) or not 1 <= t <= 200:
                bad("[agent] turns must be an integer in [1, 200]")
            g = agent.get("gpu_s")
            if g is not None and (isinstance(g, bool) or not isinstance(g, (int, float))
                                  or not 1 <= g <= 10 * 3600):
                bad("[agent] gpu_s (the run's GPU-seconds cap) must be a number in [1, 36000]")
    if kind == "agent" and agent is None:
        bad("an agent run has an [agent] table (cli, model, turns)")
    if kind == "verify" and agent is not None:
        bad("a verify run has no [agent] table")
    if kind == "agent" and network == "none" and not probe_agent:
        bad("an agent run reaches its model: network = \"ollama\" or \"anthropic\"")
    if probe_agent and network == "anthropic":
        bad("a probe agent container uses network = \"none\" or \"ollama\"")
    if agent and agent.get("cli") == "opencode" and network != "ollama":
        bad("an opencode run uses network = \"ollama\"")
    if agent and agent.get("cli") == "claude" and network != "anthropic":
        bad("a Claude Code run uses network = \"anthropic\"")

    truth = raw.get("truth")
    if truth is not None:
        why = truth_problem(truth, root, kind, network, read=read)
        if why:
            bad(f"[truth]: {why}")
            truth = None
        else:
            truth = dict(truth)
    commands = []
    raw_cmds = raw.get("command", [])
    if not isinstance(raw_cmds, list):
        bad("[[command]] must be a list of tables")
        raw_cmds = []
    if len(raw_cmds) > MAX_COMMANDS:
        bad(f"at most {MAX_COMMANDS} [[command]] lines")
    staged = {e.dst for e in files}
    tools = {e.dst for e in files if e.role == "tool"}
    for i, c in enumerate(raw_cmds[:MAX_COMMANDS]):
        where = f"[[command]] #{i + 1}"
        if not isinstance(c, dict) or set(c) - COMMAND_KEYS or "argv" not in c:
            bad(f"{where}: a command is a table with one key, argv")
            continue
        why = command_problem(c["argv"], staged, tools, truth=truth)
        if why:
            bad(f"{where}: {why}")
            continue
        commands.append(tuple(c["argv"]))
    if raw.get("truth") is not None and (not commands or any(c[0] != TRUTHCHECK
                                                              for c in commands)):
        bad("a truth run's commands are the grader's (/opt/dvl/bin/truthcheck) and nothing else")

    try:
        c = container_pins()
        for k, pin in (("work_mb", "work_gb"), ("tmp_mb", "tmp_gb")):
            if limits[k] > float(c[pin]) * 1024:
                bad(f"[limits] {k} = {limits[k]} exceeds the pinned tmpfs cap "
                    f"({float(c[pin]) * 1024:g} MiB, scripts/dvl/pins.toml [container] {pin})")
    except SandboxError as err:
        bad(str(err))
    pools = run_pools(files)
    if kind in KINDS:
        try:
            bound = memory_bound_gb(kind, pools)
        except SandboxError as err:
            bad(str(err))
            bound = None
        if bound is not None:
            if "mem_gb" in lim and isinstance(lim["mem_gb"], (int, float)) and lim["mem_gb"] > bound:
                bad(f"[limits] mem_gb = {lim['mem_gb']} exceeds the pinned bound {bound:g} "
                    f"for a {kind} container (CLAUDE.md §Resources)")
            limits.setdefault("mem_gb", bound)
            if "mem_gb" not in lim:
                limits["mem_gb"] = bound
    if problems:
        raise ManifestError(problems)
    return Manifest(SCHEMA, run_id, mid, kind, image, network, limits, tuple(files),
                    tuple(paths), dict(agent) if agent else None, tuple(commands),
                    truth=truth, raw=raw)


_ARG = re.compile(r"[A-Za-z0-9_./=:-]{1,200}")


def command_problem(argv, staged, tools, truth=None):
    """Why a [[command]] argv may not run, or None. A command is a trusted course
    tool from the run's tool copies, with its options from a fixed list and
    every path a staged file or a directory that holds one; or a door of the
    image's controls (run only by `mksandbox-run --probe`); or, in a truth
    run only, the image's grader `truthcheck <mode> <lab> [<card> ...]`."""
    if not isinstance(argv, list) or not argv or len(argv) > 16 \
            or not all(isinstance(a, str) and _ARG.fullmatch(a) for a in argv):
        return "argv is a list of 1-16 plain words"
    if argv[0] == TRUTHCHECK:
        if not truth:
            return "the grader (truthcheck) runs only in a truth run (a [truth] table)"
        if len(argv) < 3 or argv[1] not in TRUTH_MODES or argv[2] != truth.get("lab"):
            return (f"the grader runs as `{TRUTHCHECK} <{'|'.join(TRUTH_MODES)}> "
                    f"{truth.get('lab')} [<card> ...]`")
        if argv[3:] and (argv[1] != "validate" or not all(
                re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", a) for a in argv[3:])):
            return "card ids are lower-case words, for validate only"
        return None
    if argv[0] == CONTROLS:
        if len(argv) < 3 or argv[1] != "door" or argv[2] not in DOORS:
            return f"the controls run as `{CONTROLS} door <{'|'.join(DOORS)}> …`"
        return None
    if argv[0] not in COMMAND_TOOLS:
        return f"argv[0] must be one of {sorted(COMMAND_TOOLS)} (a trusted tool copy)"
    if argv[0] not in tools:
        return f"{argv[0]} is not staged as a tool"
    flags, valued = COMMAND_TOOLS[argv[0]]
    dirs = set()
    for s in staged:
        parts = s.split("/")
        dirs.update("/".join(parts[:k]) for k in range(1, len(parts)))
    args = iter(argv[1:])
    for a in args:
        if a.startswith("-"):
            if a == "--lab-code" and argv[0] == "scripts/vcheck":
                if next(args, None) != "own":
                    return "--lab-code accepts own (omit it to preserve code)"
                if "--lab-task" not in argv or "--gate" not in argv:
                    return "--lab-code requires --gate and --lab-task"
                continue
            if a in flags:
                continue
            if a in valued:
                p = next(args, None)
                if p is None or (p not in staged and not (
                        a == "--lab-task" and p in dirs and p.startswith(LAB_TASK_DIR + "/"))):
                    # a lab gate's crate task form is a staged directory (DV5c gaps lane)
                    return f"{a} takes a staged path"
                continue
            return f"option {a} is not one {argv[0]} takes in a sandbox"
        if a not in staged and a not in dirs:
            return f"{a} is neither a staged file nor a directory that holds one"
    return None


def _role_problem(role, src, rev, rec, mid, kind=None):
    """Why `src` may not enter in `role` for module `rec`, or None."""
    if role == "editable":
        if agentic_ok(src, rec) or bench_task(src):
            return None
        if kind == "verify" and learner_ok(src, rec):
            return None             # a verify run checks one of the module's own files
        if kind == "verify":
            return (f"{src} is not one of {mid}'s files (its registry lists and units) and not "
                    "a benchmark task")
        return (f"{src} is not in {mid}'s agentic list and not a benchmark task: no other "
                "module's file and no finished exercise enters as editable")
    if role == "task":
        return None if bench_task(src) else f"{src}: a task is a stripped statement (inline text) or a benchmark task file"
    if role == "given":
        return None if given_ok(src, rec) else f"{src} is not a given file of {mid}'s layer chain"
    if role == "project":
        return None if project_ok(src, rec) else f"{src} is not a project file of {mid}'s units or the workspace pins"
    if role == "tool":
        return None if tool_ok(src) else f"{src} is not one of the trusted course tools"
    if role == "expected":
        return None if expected_ok(src, mid) else f"{src} is not one of {mid}'s pins under expected/"
    if role == "snapshot":
        return None if rev else "a snapshot is read at a commit (rev)"
    if role == "contract":
        return "the contract text is written inline (text), never copied from a file"
    return f"unknown role {role}"


# --- materialization (§5.3) ---------------------------------------------------------------------

@dataclass
class RunDir:
    path: Path

    @property
    def inp(self):
        return self.path / "in"

    @property
    def work(self):
        return self.path / "work"

    @property
    def out(self):
        return self.path / "out"

    @property
    def state(self):
        return self.path / "state"


def materialize(manifest, root=REPO_ROOT, base=None):
    """Stage every file into a fresh run directory (mode 0700) under
    $XDG_RUNTIME_DIR/dvl-runs/, or under `base`. in/ is made read-only after
    staging. Returns a RunDir; on any failure nothing is left behind."""
    base = Path(base) if base else runs_base()
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(base, 0o700)
    path = Path(tempfile.mkdtemp(prefix="", dir=base))
    run = RunDir(path)
    try:
        for d in (run.inp, run.work, run.out, run.state):
            d.mkdir(mode=0o700)
        for e in manifest.files:
            content = read_source(root, e)
            if sha256_bytes(content) != e.sha256:
                raise SandboxError(f"{e.src or e.dst} changed while it was staged")
            target = run.inp / e.dst
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "xb") as fh:
                fh.write(content)
        _read_only(run.inp, executable={e.dst for e in manifest.files
                                        if e.role == "tool" and e.dst in COMMAND_TOOLS})
        if manifest.truth:
            stage_truth(manifest, run, root)
    except BaseException:
        remove_run(run)
        raise
    return run


# --- the grader container's truth mode (DV4-PLAN §5.9; QPLAN §30 Q49) ---------------------------
#
# sandbox/truth.toml pins each lab's sealed archive (its course path, sha256 and
# recipient) and where the grader's key lives on the author's machine (outside
# the checkout, in the reference class: no study session reads it). A truth run
# is a verify manifest with a [truth] table naming the archive; materialize copies
# the archive and the key, as opaque bytes, into the run directory's truth/
# (mode 0700, each file 0400), which the container binds read-only at
# /run/dvl-truth/. The host never unseals anything: only the image's grader
# (sandbox/image/truthcheck.py) does, in the container, and it prints
# verdict-level fields only.

def truth_pins(root=REPO_ROOT):
    """{lab: pin} from sandbox/truth.toml (schema 1, [[lab]] tables)."""
    p = Path(root) / TRUTH_FILE
    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise ManifestError(f"{TRUTH_FILE}: unreadable ({type(e).__name__})") from None
    if data.get("schema") != 1:
        raise ManifestError(f"{TRUTH_FILE}: schema 1 is needed")
    out = {}
    for t in data.get("lab", []):
        if isinstance(t, dict) and isinstance(t.get("id"), str):
            out[t["id"]] = dict(t)
    return out


def truth_problem(truth, root, kind, network, *, read=True):
    """Why a manifest's [truth] table is refused, or None."""
    if kind != "verify" or network != "none":
        return "only a verification container (kind verify, network none) unseals truth"
    if not isinstance(truth, dict) or set(truth) != TRUTH_KEYS:
        return f"the table has exactly the keys {sorted(TRUTH_KEYS)}"
    try:
        pin = truth_pins(root).get(truth.get("lab"))
    except ManifestError as e:
        return str(e)
    if pin is None:
        return f"no lab {truth.get('lab')!r} is pinned in {TRUTH_FILE}"
    if truth.get("archive") != pin.get("archive") or truth.get("sha256") != pin.get("sha256"):
        return f"the archive and its sha256 must be the ones {TRUTH_FILE} pins"
    if read:
        f = Path(root) / pin["archive"]
        if not f.is_file() or f.is_symlink() or sha256_bytes(f.read_bytes()) != pin["sha256"]:
            return f"{pin['archive']} is missing or does not match its pinned sha256"
    return None


def truth_identity(pin):
    """The grader's key file (outside the checkout); SandboxError when it is absent."""
    spec = pin.get("identity", "")
    if not isinstance(spec, str) or not spec.startswith("~/"):
        raise SandboxError(f"{TRUTH_FILE}: the identity is written relative to HOME (\"~/...\")")
    p = Path(os.path.expanduser(spec))
    if not p.is_file() or p.is_symlink():
        raise SandboxError(f"the grader's key ({spec}) is not on this machine: the truth mode "
                           "runs where the author made the key (DV4 author notes)")
    return p


def stage_truth(manifest, run, root):
    """Copy the sealed archive and the key, unread, into run/truth/ (0700; 0400 each)."""
    pin = truth_pins(root)[manifest.truth["lab"]]
    d = run.path / "truth"
    d.mkdir(mode=0o700)
    data = (Path(root) / pin["archive"]).read_bytes()
    if sha256_bytes(data) != pin["sha256"]:
        raise SandboxError(f"{pin['archive']} changed while it was staged")
    for name, content in (("archive.tar.age", data),
                          ("identity", truth_identity(pin).read_bytes())):
        f = d / name
        with open(f, "xb") as fh:
            fh.write(content)
        os.chmod(f, 0o400)
    os.chmod(d, 0o500)


def build_truth(root, lab, mode, *, cards=(), mem_gb=None, run_id=None, lang=None):
    """The raw manifest of one truth run of `lab` (`mode` manifest or validate):
    for validate, the lab's local task forms (its stratum's STRATUM.toml cards,
    or the named ones) staged as editable files at their course paths, which
    the grader overwrites with each reference program in turn; the module's
    given chain, project files, tools and pins read-only; the [truth] table;
    and the one grader command. `lang` keeps one language's cards: a
    verification container's memory bound is its language's (container-verify
    mode refuses a Dafny job in a container sized for Verus), so a lab with
    both languages validates in two runs; `mem_gb` is held to that bound."""
    root = Path(root).resolve()
    if mode not in TRUTH_MODES:
        raise ManifestError(f"the grader's mode is one of {list(TRUTH_MODES)}")
    if mode == "judge":
        raise ManifestError("a judging run's manifest is dvl.judge.build_judge's (it stages "
                            "the candidates)")
    pin = truth_pins(root).get(lab)
    if pin is None:
        raise ManifestError(f"no lab {lab!r} is pinned in {TRUTH_FILE}")
    rec = registry_record(root, lab)
    forms = []
    for st in sorted((root / "bench" / "local").glob("*/*/STRATUM.toml")):
        try:
            data = tomllib.loads(st.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if data.get("lab") != lab:
            continue
        for c in data.get("card", []):
            cid, clang = c.get("id"), c.get("lang")
            ext = {"dafny": ".dfy", "verus": ".rs"}.get(clang)
            if isinstance(cid, str) and ext:
                forms.append((cid, (st.parent / cid / "tasks" / f"{cid}{ext}")
                              .relative_to(root).as_posix()))
    if cards:
        unknown = sorted(set(cards) - {c for c, _ in forms})
        if unknown:
            raise ManifestError(f"no local card(s) {unknown} in {lab}'s stratum")
        forms = [(c, f) for c, f in forms if c in cards]
    if lang is not None:
        forms = [(c, f) for c, f in forms if lang_pool(f) == lang]
    if mode == "validate" and len({lang_pool(f) for _, f in forms}) > 1:
        raise ManifestError("a truth run validates one language's cards (name --truth-lang)")
    files, seen = [], set()

    def add(src, role):
        if src in seen:
            return
        seen.add(src)
        data = read_source(root, Entry(src, src, role, "0" * 64))
        files.append({"src": src, "dst": src, "role": role, "sha256": sha256_bytes(data)})
    if mode == "validate":
        if not forms:
            raise ManifestError(f"{lab} has no local stratum cards to validate")
        for _, f in forms:
            # inline, as a verify run stages a work copy: no agent sees a grader's
            # inputs, so the attestation of an agent's task card does not apply
            text = read_source(root, Entry(f, f, "editable", "0" * 64)).decode("utf-8")
            seen.add(f)
            files.append({"dst": f, "role": "editable", "text": text,
                          "sha256": sha256_bytes(text.encode("utf-8"))})
    langs = {lang_pool(f) for _, f in forms} - {None} if mode == "validate" else set()
    for src, role in readonly_inputs(root, rec, langs):
        if src == "verus/Cargo.toml":
            continue
        add(src, role)
    if "verus" in langs:
        seen.add("verus/Cargo.toml")
        text = verus_workspace(root, rec)
        files.append({"dst": "verus/Cargo.toml", "role": "project", "text": text,
                      "sha256": sha256_bytes(text.encode("utf-8"))})
    lock = read_images_lock(root)
    image = next((k for k in lock if k.startswith("dvl-toolchain@")),
                 "dvl-toolchain@sha256:" + "0" * 64)
    argv = [TRUTHCHECK, mode, lab] + ([c for c, _ in forms] if mode == "validate" and
                                      (cards or lang) else [])
    raw = {"schema": SCHEMA, "run_id": run_id or f"t{os.getpid()}-{secrets.token_hex(4)}",
           "module": rec["id"], "kind": "verify", "image": image, "network": "none",
           "limits": {"wall_clock_s": 4 * 3600}, "file": files, "return": [],
           "command": [{"argv": argv}],
           "truth": {"lab": lab, "archive": pin["archive"], "sha256": pin["sha256"]}}
    if mem_gb is not None:
        bound = memory_bound_gb("verify", run_pools(files))
        raw["limits"]["mem_gb"] = min(float(mem_gb), bound)
    return raw


def _read_only(top, executable=()):
    """Every staged file 0444 and every directory 0555; the trusted tool copies
    in `executable` (scripts/vcheck, vaudit, specfreeze) 0555, so that a
    command an acceptance line names (`scripts/vcheck <file>`) runs unchanged
    inside the container (DV4-PLAN §6 step 5; step 3a)."""
    top = Path(top)
    for dirpath, dirnames, filenames in os.walk(top, topdown=False):
        for name in filenames:
            f = os.path.join(dirpath, name)
            rel = Path(f).relative_to(top).as_posix()
            os.chmod(f, 0o555 if rel in executable else 0o444)
        os.chmod(dirpath, 0o555)


def remove_run(run):
    if run is None:
        return
    for dirpath, dirnames, filenames in os.walk(run.path):
        os.chmod(dirpath, 0o700)
    shutil.rmtree(run.path, ignore_errors=True)


# --- the self-test (§5.4, static part) ------------------------------------------------------------

def read_canaries(root):
    """{sha256 of a full token: the tree it marks} from sandbox/canaries.sha256."""
    out = {}
    try:
        text = (Path(root) / "sandbox" / "canaries.sha256").read_text(encoding="utf-8")
    except OSError:
        return out
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) == 2 and re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            out[parts[0]] = parts[1]
    return out


def read_attested(root):
    """{sha256: card path} from sandbox/attested.toml."""
    try:
        data = tomllib.loads((Path(root) / "sandbox" / "attested.toml").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {c["sha256"]: c.get("path", "") for c in data.get("card", [])
            if isinstance(c, dict) and isinstance(c.get("sha256"), str)}


_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_']*|\d+|[^\sA-Za-z0-9_]")
_C_COMMENTS = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
_HASH_COMMENTS = re.compile(r"#[^\n]*")
_MOD = (1 << 61) - 1


def tokens(text, name=""):
    """Normalized tokens: comments dropped (by the file's language), then
    identifiers, numbers and single punctuation characters."""
    suffix = PurePosixPath(name).suffix
    if suffix in (".dfy", ".rs", ".dfy.specimen", ".rs.specimen") or name.endswith((".dfy.specimen", ".rs.specimen")):
        text = _C_COMMENTS.sub(" ", text)
    elif suffix == ".py":
        text = _HASH_COMMENTS.sub(" ", text)
    return _TOKEN.findall(text)


_IDS: dict = {}


def windows(toks, n=WINDOW_TOKENS):
    """The set of rolling hashes of every n-token window (token ids are shared
    by every call in a process, so window sets compare)."""
    if len(toks) < n:
        return set()
    ids = _IDS
    seq = [ids.setdefault(t, len(ids) + 1) for t in toks]
    base, h, out = 1_000_003, 0, set()
    top = pow(base, n - 1, _MOD)
    for i, v in enumerate(seq):
        if i >= n:
            h = (h - seq[i - n] * top) % _MOD
        h = (h * base + v) % _MOD
        if i >= n - 1:
            out.add(h)
    return out


def _text(data):
    return data.decode("utf-8", "replace")


def public_answer_files(root):
    """Every public and local benchmark answer file: (path, matching task file or None)."""
    root = Path(root)
    out = []
    for top in sorted((root / "bench").glob("public/*/answers")) + \
            sorted((root / "bench").glob("local/*/*/answers")):
        tasks = top.parent / "tasks"
        for p in sorted(top.rglob("*")):
            if p.is_file() and not p.is_symlink():
                rel = p.relative_to(top)
                t = tasks / rel
                out.append((p, t if t.is_file() else None))
    return out


def shipped_form(root, rel):
    """The course's first committed version of a file (its shipped form), or None."""
    try:
        p = subprocess.run(["git", "-C", str(root), "log", "--diff-filter=A", "--format=%H", "--", rel],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    revs = p.stdout.split()
    if p.returncode != 0 or not revs:
        return None
    try:
        return git_blob(root, revs[-1], rel)[0]
    except ManifestError:
        return None


def public_answer_check(files, answers, *, exclude=(), n=WINDOW_TOKENS, threshold=WINDOW_THRESHOLD):
    """§5.4 item 4. `files`: {name: bytes} of sandbox files; `answers`: [(path,
    task path or None)]; `exclude`: texts whose windows never count (the given
    layers, the tasks' shipped forms). Returns [{file, answer, shared, equal}]
    for every pair that is equal or shares at least `threshold` distinct
    windows outside the excluded text and the answer's own task file."""
    ex = set()
    for name, data in exclude:
        ex |= windows(tokens(_text(data), name), n)
    cand = {name: windows(tokens(_text(data), name), n) - ex for name, data in files.items()}
    digests = {sha256_bytes(d): name for name, d in files.items()}
    union = set().union(*cand.values()) if cand else set()
    hits = []
    for apath, tpath in answers:
        try:
            adata = Path(apath).read_bytes()
        except OSError:
            continue
        aname = str(apath)
        if sha256_bytes(adata) in digests:
            hits.append({"file": digests[sha256_bytes(adata)], "answer": aname, "shared": None,
                         "equal": True})
            continue
        if not union:
            continue
        aw = windows(tokens(_text(adata), aname), n) & union
        if not aw:
            continue
        if tpath is not None:
            try:
                aw -= windows(tokens(_text(Path(tpath).read_bytes()), str(tpath)), n)
            except OSError:
                pass
        for name, w in cand.items():
            k = len(w & aw)
            if k >= threshold:
                hits.append({"file": name, "answer": aname, "shared": k, "equal": False})
    return hits


def answer_index(answers, n=WINDOW_TOKENS):
    """{window: set of answer indices} over every answer, each minus its own
    task file's windows: the calibration's index (one pass over the sets)."""
    index = {}
    for i, (apath, tpath) in enumerate(answers):
        w = windows(tokens(_text(Path(apath).read_bytes()), str(apath)), n)
        if tpath is not None:
            w -= windows(tokens(_text(Path(tpath).read_bytes()), str(tpath)), n)
        for h in w:
            index.setdefault(h, set()).add(i)
    return index


def max_shared(index, wins):
    """(the largest number of distinct windows `wins` shares with one answer,
    that answer's index or None)."""
    counts = {}
    for h in wins:
        for i in index.get(h, ()):
            counts[i] = counts.get(i, 0) + 1
    if not counts:
        return 0, None
    i = max(counts, key=counts.get)
    return counts[i], i


def calibration(root=REPO_ROOT, n=WINDOW_TOKENS):
    """[(shared, file, answer)] for every shipped file of the armed modules
    (exercises, exits, agentic and harness files, and the given layers),
    against the installed answers, with the given layers' windows excluded:
    §5.4 item 4's calibration set. Empty when no set is installed."""
    import check_course_map as ccm
    root = Path(root)
    answers = public_answer_files(root)
    if not answers:
        return []
    index = answer_index(answers, n)
    given = sorted((root / "dafny" / "given").rglob("*.dfy")) + sorted((root / "verus" / "given").rglob("*.rs"))
    gw = set()
    for p in given:
        gw |= windows(tokens(_text(p.read_bytes()), p.name), n)
    data, err = ccm.load_registry(root)
    if err:
        raise ManifestError(err)
    files = list(given)
    for m in data.get("module", []):
        if m.get("status") == "planned":
            continue
        for key in ("exercises", "exits", "agentic", "harness"):
            for f in m.get(key, []):
                p = root / f
                if f.endswith("/"):
                    files += sorted(x for x in p.rglob("*") if x.is_file()) if p.is_dir() else []
                elif p.is_file():
                    files.append(p)
    out = []
    for p in files:
        k, i = max_shared(index, windows(tokens(_text(p.read_bytes()), p.name), n) - gw)
        out.append((k, p.relative_to(root).as_posix(),
                    None if i is None else Path(answers[i][0]).relative_to(root).as_posix()))
    return sorted(out, reverse=True)


def selftest(manifest, run, root=REPO_ROOT, *, author=False, answers=None):
    """The static self-test (§5.4 items 1-5) on a materialized run directory.
    Returns the report (a dict; "ok" is the verdict). In a study run the
    author-only checks are recorded as skipped (P6)."""
    root = Path(root)
    report = {"schema": 1, "manifest_sha256": manifest.sha256(), "checks": {}, "ok": True}

    def fail(check, msg):
        report["checks"].setdefault(check, {"ok": True, "problems": []})
        report["checks"][check]["ok"] = False
        report["checks"][check]["problems"].append(msg)
        report["ok"] = False

    def passed(check, **extra):
        report["checks"].setdefault(check, {"ok": True, "problems": []}).update(extra)

    # 1. closure
    want = {e.dst: e for e in manifest.files}
    seen = set()
    for dirpath, dirnames, filenames in os.walk(run.inp):
        for name in dirnames + filenames:
            p = Path(dirpath) / name
            rel = p.relative_to(run.inp).as_posix()
            st = os.lstat(p)
            if stat.S_ISDIR(st.st_mode):
                continue
            if not stat.S_ISREG(st.st_mode):
                fail("closure", f"in/{rel} is not a regular file")
                continue
            e = want.get(rel)
            if e is None:
                fail("closure", f"in/{rel} is not in the manifest")
                continue
            if sha256_bytes(p.read_bytes()) != e.sha256:
                fail("closure", f"in/{rel} does not match its sha256")
                continue
            seen.add(rel)
    for rel in sorted(set(want) - seen):
        fail("closure", f"in/{rel} is missing")
    passed("closure", files=len(seen))

    # 2. canaries (public prefix; attribution by hash)
    known = read_canaries(root)
    hits = 0
    for e in manifest.files:
        data = (run.inp / e.dst).read_bytes() if (run.inp / e.dst).is_file() else b""
        for m in CANARY_TOKEN.finditer(data):
            tree = known.get(sha256_bytes(m.group(0)), "an unlisted tree")
            fail("canaries", f"{e.dst} carries a canary token ({tree})")
            hits += 1
    passed("canaries", listed=len(known), hits=hits)

    # 3. attested task cards
    att = read_attested(root)
    n_cards = 0
    for e in manifest.files:
        if e.src and lab_card(e.src) and e.role in ("task", "editable"):
            n_cards += 1
            if e.sha256 not in att:
                fail("attestation", f"{e.src}: a lab task card enters only when its sha256 is in "
                                    "sandbox/attested.toml (the author attests it once)")
        elif e.src is None and manifest.kind == "agent" and e.role == "editable" \
                and lab_card(e.dst):
            # an agent run's work copy of a card, inline (a continuation, DV5d): the
            # card it continues, the course's file at that path, must be attested
            n_cards += 1
            card = Path(root) / e.dst
            have = sha256_bytes(card.read_bytes()) if card.is_file() and not card.is_symlink() \
                else None
            if have is None or have not in att:
                fail("attestation", f"{e.dst}: an agent run's work copy of a lab task card enters "
                                    "only when the card itself is in sandbox/attested.toml")
    passed("attestation", cards=n_cards)

    # 4. public answers
    files = {}
    exclude = []
    for e in manifest.files:
        data = (run.inp / e.dst).read_bytes() if (run.inp / e.dst).is_file() else b""
        if e.role == "given":
            exclude.append((e.dst, data))
            continue
        if e.role in ("tool", "expected", "contract"):
            continue
        files[e.dst] = data
        if e.src and e.role in ("editable", "task", "snapshot"):
            shipped = shipped_form(root, e.src)
            if shipped is None and bench_task(e.src):
                shipped = data      # a fetched set's task file is its own shipped form (digest-pinned)
            if shipped is not None:
                exclude.append((e.src, shipped))
        elif e.src is None and e.role in ("editable", "task"):
            # an inline work copy at its course path, or a lab run's task form at
            # lab-task/<path>: the shipped form of that path never counts (a
            # delivery of a public task shares its task form's text by design)
            rel = e.dst[len(LAB_TASK_DIR) + 1:] if e.dst.startswith(LAB_TASK_DIR + "/") else e.dst
            shipped = shipped_form(root, rel)
            if shipped is None and bench_task(rel) and (Path(root) / rel).is_file():
                shipped = (Path(root) / rel).read_bytes()
            if shipped is not None:
                exclude.append((rel, shipped))
    ans = public_answer_files(root) if answers is None else answers
    found = public_answer_check(files, ans, exclude=exclude)
    for h in found:
        what = "equals" if h["equal"] else f"shares {h['shared']} windows of {WINDOW_TOKENS} tokens with"
        fail("public-answers", f"{h['file']} {what} {Path(h['answer']).relative_to(root) if str(h['answer']).startswith(str(root)) else h['answer']}")
    passed("public-answers", answers=len(ans), window=WINDOW_TOKENS, threshold=WINDOW_THRESHOLD)

    # 5. author-only checks
    if author:
        # the course's twins only: the sealed references are read at attestation (D31)
        problems = author_scan(root, {e.dst: (run.inp / e.dst).read_bytes() for e in manifest.files
                                      if e.role in ("task", "editable")}, sealed=False)
        for p in problems:
            fail("author", p)
        passed("author", ran=True)
    else:
        report["checks"]["author"] = {
            "ok": True, "ran": False,
            "skipped": "study mode: the reference fingerprints and leak patterns run only under "
                       "--author (DV4-PLAN §5.4 item 5; P6)", "problems": []}
    return report


# --- the author-only scan (attestation) -------------------------------------------------------

SHINGLE = 7


def author_gate(root=REPO_ROOT):
    """None when an author-only mode may run here, else the reason it may not
    (Δ103: CI=true, or inside git, a linked worktree, HEAD off the learner
    prefix that scripts/course_mode.sh names)."""
    if os.environ.get("CI") == "true":
        return None

    def git(*args):
        try:
            p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                               timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return p.stdout.strip() if p.returncode == 0 else None

    gd = git("rev-parse", "--path-format=absolute", "--git-dir")
    cd = git("rev-parse", "--path-format=absolute", "--git-common-dir")
    if gd is None or cd is None:
        return "not inside a git checkout"
    if gd == cd:
        return "this is the primary worktree"
    prefix = "leobwang-"
    try:
        m = re.search(r"^LEARNER_PREFIX=['\"]?([A-Za-z0-9_.-]+)",
                      (Path(root) / "scripts" / "course_mode.sh").read_text(encoding="utf-8"), re.M)
        prefix = m.group(1) if m else prefix
    except OSError:
        pass
    branch = git("symbolic-ref", "--short", "-q", "HEAD")
    if branch and branch.startswith(prefix):
        return "HEAD is on a learner branch"
    return None


def _shingles(text, name, n=SHINGLE):
    toks = tokens(text, name)
    return {" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)}


_SCAN_SUFFIXES = (".dfy", ".rs", ".py")
_SCAN_SKIP_PARTS = {"target", ".venv", "__pycache__", "node_modules", ".toolchain"}


def _course_code_files(root, tops):
    """The course's code files under `tops` (paths relative to root): git's
    tracked and untracked-but-not-ignored files when root is a checkout, else
    a walk. Build outputs and virtual environments are skipped."""
    root = Path(root)
    rels = None
    try:
        p = subprocess.run(["git", "-C", str(root), "ls-files", "-co", "--exclude-standard", "-z",
                            "--", *tops], capture_output=True, timeout=120)
        if p.returncode == 0:
            rels = [x for x in p.stdout.decode("utf-8", "replace").split("\0") if x]
    except (OSError, subprocess.TimeoutExpired):
        rels = None
    if rels is None:
        rels = [q.relative_to(root).as_posix() for t in tops if (root / t).is_dir()
                for q in sorted((root / t).rglob("*"))]
    out = []
    for rel in sorted(set(rels)):
        q = root / rel
        if PurePosixPath(rel).suffix in _SCAN_SUFFIXES and not _SCAN_SKIP_PARTS & set(PurePosixPath(rel).parts) \
                and q.is_file() and not q.is_symlink():
            out.append(rel)
    return out


def _read(p):
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


SPAN_TOKENS = 10
POOL_COMMON = 2
SCAN_RULE = "DV6"           # recorded with each attestation (`scan`): the rule a card passed
# (DV5d's spans, DV5e's generic set and renamed copies, the user's decision D25; DV6: the
# sealed references are twins too, D31)

# The renamed form's literal tokens: the keywords and builtin names of Dafny, Rust/Verus
# and Python. Every other identifier becomes its first-occurrence index in the span.
_KEYWORDS = frozenset("""
abstract allocated as assert assume bool break by calc case char class codatatype colemma
const constructor continue copredicate datatype decreases default else ensures exists
export expect extends false fresh forall function ghost greatest if imap import in include
inductive int invariant is iset iterator label least lemma map match method modifies modify
module multiset nat new newtype null object old opaque opened ORDINAL predicate print
provides reads real refines requires return returns reveal reveals seq set static string
then this trait true twostate type unchanged var while witness yield yields
fn pub let mut impl struct enum use mod crate self Self super where loop for dyn ref move
unsafe extern async await u8 u16 u32 u64 u128 usize i8 i16 i32 i64 i128 isize str Vec
Option Some None Result Ok Err Box String verus proof spec exec open closed tracked
broadcast uninterp external_body external verifier Seq Set Map Ghost Tracked vstd prelude
std assert_seqs_equal choose implies arbitrary
def lambda not and or True False pass raise try except finally with global nonlocal del
elif from
""".split())
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_']*")
_DECL_NAME = re.compile(r"\b(?:function|predicate|lemma|method|datatype|codatatype|type|newtype|"
                        r"const|fn|struct|enum|trait)\s+(?:method\s+|ghost\s+)?"
                        r"([A-Za-z_][A-Za-z0-9_']*)")
_HEADER = re.compile(r"^\s*(?:(?:pub(?:\([a-z]+\))?|ghost|proof|spec|exec|open|closed|broadcast|"
                     r"static|opaque|twostate|least|greatest|async|unsafe|const)\s+)*"
                     r"(?:fn|lemma|function|predicate|method|datatype|codatatype|struct|enum|"
                     r"trait|impl|type|newtype|module|mod|use|import|include|class|def|from)\b")
_BRACKETS = frozenset("{}()[];,")


def _shingle_set(toks, n=SHINGLE):
    return {" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def renamed_form(toks, literal=_KEYWORDS):
    """The token sequence with every identifier outside `literal` replaced by the
    index of its first occurrence ($0, $1, …): a consistently renamed copy has the
    same form."""
    seen = {}
    return tuple(f"${seen.setdefault(t, len(seen))}" if t not in literal and _IDENT.fullmatch(t)
                 else t for t in toks)


def structure_line(line, name=""):
    """True for a line of language structure: no tokens but brackets and separators
    (or none: blank or comment only), or a declaration header (a signature, a
    module, an import)."""
    if all(t in _BRACKETS for t in tokens(line, name)):
        return True
    text = _HASH_COMMENTS.sub(" ", line) if name.endswith(".py") else _C_COMMENTS.sub(" ", line)
    return bool(_HEADER.match(text))


def _api_names(root):
    """The names the given layers declare (a delivery calls them by name, so a renamed
    copy keeps them)."""
    out = set()
    for rel in _course_code_files(root, ["dafny/given", "verus/given"]):
        out |= set(_DECL_NAME.findall(_read(Path(root) / rel)))
    return frozenset(out)


def _pool_files(root):
    """The installed public benchmark files (bench/public/<set>/{tasks,answers}/**)."""
    out = []
    for top in sorted((Path(root) / "bench" / "public").glob("*")):
        for sub in ("tasks", "answers"):
            d = top / sub
            if d.is_dir() and not d.is_symlink():
                out += [p for p in sorted(d.rglob("*")) if p.suffix in (".dfy", ".rs")
                        and p.is_file() and not p.is_symlink()]
    return out


def _twin_pairs(root):
    """(twin, learner file) pairs: Solutions/{dafny,verus,harness}/** (learner
    file: the same path without Solutions/) and the lab cards' references
    Solutions/bench/local/<q|r>/<lab>/<card>/<f> (learner file:
    bench/local/<q|r>/<lab>/<card>/tasks/<f>)."""
    root = Path(root)
    pairs = []
    for rel in _course_code_files(root, ["Solutions/dafny", "Solutions/verus", "Solutions/harness"]):
        pairs.append((root / rel, root / PurePosixPath(rel).relative_to("Solutions")))
    for rel in _course_code_files(root, ["Solutions/bench/local"]):
        parts = PurePosixPath(rel).parts          # Solutions bench local q lab card f…
        if len(parts) >= 7:
            card = PurePosixPath(*parts[1:6])
            pairs.append((root / rel, root / card / "tasks" / PurePosixPath(*parts[6:])))
    return pairs


# --- the sealed references as twins (the user's decision D31, 2026-10-14) ---------------------
#
# Lab 2's reference specifications are the sealed hidden truth (a [[lab]] of sandbox/truth.toml
# named by a local stratum's `lab`, its cards' tasks/<card>/ in the archive) and Lab 3's
# reference deliveries are sealed beside it (a sealed stratum's `refs_archive`, pinned in its
# STRATUM.toml with refs_sha256, refs_files and refs_manifest_sha256; its tree refs/<card>/<path>,
# sealed by `sandbox/seal_hidden.py --stratum`; DV6 fix round: they had lived only in an
# unversioned author cache). A directory of plaintext deliveries (SEALED_REFERENCE_DIRS) is
# still read for a sealed stratum that pins no refs archive (the tests' decoys). At attestation time the scan reads both as twins,
# decrypted into memory with the pinned age binary and the key truth.toml names, and never
# written: no file, log line or exception message holds their text (a failure says what could
# not be read, never what was read). A source that is declared but cannot be read refuses the
# attestation (fail-closed) and changes nothing in sandbox/attested.toml.

AGE = "~/.local/bin/age"            # the pinned age binary (VERSIONS.md §1.4; truth.toml's age_sha256)
MAX_SEALED_PLAIN = 64 << 20
# A sealed stratum (its task forms in an archive) -> the directory of its reference deliveries
# (<card>/<path under tasks/>), in the reference class outside the checkout.
SEALED_REFERENCE_DIRS = {}
_SEALED_CARD = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")


class SealedRefsError(Exception):
    """A sealed reference source could not be read. The message names the source and the
    check that failed, never any of its text."""


@dataclass(frozen=True)
class SealedTwin:
    """A reference held in memory only: `label` names it (no text), `name` gives the suffix
    the tokenizer reads, `twin` and `learner` are the reference and the file a learner sees."""
    label: str
    name: str
    twin: bytes = field(repr=False)
    learner: bytes = field(repr=False)


def _sealed_tree(root, archive_rel, *, want_sha, want_manifest, want_files, recipient, lab):
    """{path under labs/<lab>/: bytes} of a sealed archive, decrypted into memory with the
    pinned age binary and the key truth.toml names for `recipient`; every pin checked."""
    root = Path(root)
    arc = root / archive_rel
    if not archive_rel or not arc.is_file() or arc.is_symlink():
        raise SealedRefsError(f"{archive_rel or 'a sealed archive'} is missing")
    data = arc.read_bytes()
    if sha256_bytes(data) != want_sha:
        raise SealedRefsError(f"{archive_rel} does not match its pinned sha256")
    try:
        truth = tomllib.loads((root / "sandbox" / "truth.toml").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise SealedRefsError("sandbox/truth.toml cannot be read") from None
    pin = next((x for x in truth.get("lab", []) if isinstance(x, dict)
                and x.get("recipient") == recipient), None)
    if pin is None:
        raise SealedRefsError(f"no [[lab]] of sandbox/truth.toml pins the key of {archive_rel}'s "
                              "recipient")
    binary = Path(os.path.expanduser(AGE))
    try:
        ok_bin = binary.is_file() and sha256_bytes(binary.read_bytes()) == pin.get("age_sha256")
    except OSError:
        ok_bin = False
    if not ok_bin:
        raise SealedRefsError(f"{AGE} is missing or not the pinned age binary")
    ident = Path(os.path.expanduser(str(pin.get("identity", ""))))
    if not str(pin.get("identity", "")) or not ident.is_file():
        raise SealedRefsError("the key that unseals the references is not on this machine (the "
                              "location sandbox/truth.toml names)")
    try:
        p = subprocess.run([str(binary), "--decrypt", "--identity", str(ident), str(arc)],
                           capture_output=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired):
        raise SealedRefsError(f"{archive_rel} could not be unsealed") from None
    if p.returncode != 0 or not p.stdout or len(p.stdout) > MAX_SEALED_PLAIN:
        raise SealedRefsError(f"{archive_rel} could not be unsealed with the key")
    files, prefix = {}, f"labs/{lab}/"
    try:
        with tarfile.open(fileobj=io.BytesIO(p.stdout), mode="r:") as tf:
            for m in tf.getmembers():
                if m.isdir():
                    continue
                name = PurePosixPath(m.name).as_posix()
                if (not m.isfile() or name.startswith("/") or ".." in name.split("/")
                        or not name.startswith(prefix) or name[len(prefix):] in files):
                    raise SealedRefsError(f"{archive_rel} holds an entry outside {prefix}, twice, "
                                          "or not a regular file")
                fh = tf.extractfile(m)
                files[name[len(prefix):]] = fh.read() if fh is not None else b""
    except SealedRefsError:
        raise
    except Exception:
        raise SealedRefsError(f"{archive_rel}'s plaintext is not a tar stream") from None
    man = files.get("MANIFEST.sha256")
    if man is None or sha256_bytes(man) != want_manifest:
        raise SealedRefsError(f"{archive_rel}'s manifest differs from its pin")
    listed = {}
    for line in man.decode("utf-8", "replace").splitlines():
        parts = line.split(None, 1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            raise SealedRefsError(f"{archive_rel}'s manifest has a malformed line")
        name = parts[1].strip()         # the truth archives list labs/<lab>/…, the strata not
        listed[name[len(prefix):] if name.startswith(prefix) else name] = parts[0]
    if set(files) - {"MANIFEST.sha256"} != set(listed) or (want_files is not None
                                                            and len(listed) != want_files):
        raise SealedRefsError(f"{archive_rel}'s files differ from its manifest or its pinned count")
    if any(sha256_bytes(files[k]) != h for k, h in listed.items()):
        raise SealedRefsError(f"{archive_rel}: a file does not match its manifest")
    return files


def _strata(root):
    out = []
    for p in sorted((Path(root) / "bench" / "local").glob("*/*/STRATUM.toml")):
        try:
            meta = tomllib.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise SealedRefsError(f"{p.relative_to(root).as_posix()} cannot be read") from None
        out.append((p.parent.relative_to(root).as_posix(), meta))
    return out


def _lab2_twins(root, lab_pin):
    """The sealed hidden truth of a lab whose cards a local stratum lists: each card's
    reference program (tasks/<card>/<file>) and its reference statement (reference.toml's
    definitions and clauses, one per line), each against the card's task form."""
    root = Path(root)
    lab = str(lab_pin.get("id", ""))
    files = _sealed_tree(root, str(lab_pin.get("archive", "")), want_sha=lab_pin.get("sha256"),
                         want_manifest=lab_pin.get("manifest_sha256"),
                         want_files=lab_pin.get("files"), recipient=lab_pin.get("recipient"),
                         lab=lab)
    out = []
    for rel in sorted(k for k in files if re.fullmatch(r"tasks/[^/]+/reference\.toml", k)):
        card = rel.split("/")[1]
        if not _SEALED_CARD.fullmatch(card):
            raise SealedRefsError(f"sealed {lab}: a card id is malformed")
        try:
            ref = tomllib.loads(files[rel].decode("utf-8", "replace"))
        except Exception:
            raise SealedRefsError(f"sealed {lab} {rel} cannot be parsed") from None
        form = ref.get("task_form")
        if not isinstance(form, str) or not rel_ok(form) or not lab_card(form):
            raise SealedRefsError(f"sealed {lab} {rel}: its task_form is not a card path")
        fp = root / form
        if not fp.is_file() or fp.is_symlink():
            raise SealedRefsError(f"sealed {lab} {rel}: its task form {form} is not in the tree")
        learner = fp.read_bytes()
        suffix = PurePosixPath(form).suffix
        for k in sorted(files):
            if k.startswith(f"tasks/{card}/") and PurePosixPath(k).suffix in (".dfy", ".rs"):
                out.append(SealedTwin(f"sealed {lab} {k}", k, files[k], learner))
        lines = []
        for key in ("definitions", "requires", "ensures"):
            vals = ref.get(key)
            vals = [vals] if isinstance(vals, str) else (vals if isinstance(vals, list) else [])
            for v in vals:
                if isinstance(v, str) and v.strip():
                    lines.append(v if key == "definitions" else f"{key} {v}")
        if lines:
            out.append(SealedTwin(f"sealed {lab} {rel}", f"reference{suffix}",
                                  ("\n".join(lines) + "\n").encode("utf-8"), learner))
    return out


def _lab3_refs(root, stratum, meta, ref_dir):
    """{card: {path under the delivery: bytes}} of a sealed stratum's reference deliveries:
    from its sealed refs archive (refs/<card>/<path>) when the stratum pins one, else from
    the directory `ref_dir` (<card>/<path>)."""
    out = {}
    if meta.get("refs_archive"):
        files = _sealed_tree(root, str(meta.get("refs_archive", "")),
                             want_sha=meta.get("refs_sha256"),
                             want_manifest=meta.get("refs_manifest_sha256"),
                             want_files=meta.get("refs_files"), recipient=meta.get("recipient"),
                             lab=meta.get("lab") or meta.get("module"))
        for k in sorted(files):
            parts = PurePosixPath(k).parts
            if k == "MANIFEST.sha256":
                continue
            if len(parts) < 3 or parts[0] != "refs":
                raise SealedRefsError(f"{stratum}: its refs archive holds an entry outside refs/")
            out.setdefault(parts[1], {})[PurePosixPath(*parts[2:]).as_posix()] = files[k]
        return out
    if ref_dir is None:
        raise SealedRefsError(f"{stratum} is sealed and names no source of its reference "
                              "deliveries (a refs_archive in its STRATUM.toml)")
    base = Path(os.path.expanduser(ref_dir))
    if not base.is_dir():
        raise SealedRefsError(f"{stratum}: the directory of its reference deliveries is not on "
                              "this machine (SEALED_REFERENCE_DIRS)")
    for d in sorted(x for x in base.iterdir() if x.is_dir()):
        out[d.name] = {q.relative_to(d).as_posix(): q.read_bytes()
                       for q in sorted(d.rglob("*")) if q.is_file() and not q.is_symlink()}
    return out


def _lab3_twins(root, stratum, meta, ref_dir=None):
    """A sealed stratum's reference deliveries (_lab3_refs) against the task forms of its
    archive (<card>/tasks/<path>), both in memory."""
    files = _sealed_tree(root, str(meta.get("archive", "")), want_sha=meta.get("archive_sha256"),
                         want_manifest=meta.get("manifest_sha256"), want_files=meta.get("files"),
                         recipient=meta.get("recipient"), lab=meta.get("lab") or meta.get("module"))
    refs_all = _lab3_refs(root, stratum, meta, ref_dir)
    out = []
    for c in [c for c in meta.get("card", []) if isinstance(c, dict)]:
        cid = str(c.get("id", ""))
        if not _SEALED_CARD.fullmatch(cid):
            raise SealedRefsError(f"{stratum}: a card id is malformed")
        refs = refs_all.get(cid, {})
        if c.get("kind") == "possible" and not refs:
            raise SealedRefsError(f"{stratum}: the reference delivery of {cid} is missing")
        for sub in sorted(refs):
            if PurePosixPath(sub).suffix not in _SCAN_SUFFIXES:
                continue
            learner = files.get(f"{cid}/tasks/{sub}")
            if learner is None:
                raise SealedRefsError(f"{stratum}: {cid}'s reference file {sub} has no task form")
            out.append(SealedTwin(f"sealed {stratum} reference {cid}/{sub}", sub,
                                  refs[sub], learner))
    return out


def sealed_reference_twins(root):
    """([SealedTwin], digest): Lab 2's sealed reference specifications and Lab 3's reference
    deliveries (D31), read into memory; digest is "<n> twins, sha256 <16 hex>" over the twins'
    labels and digests (recorded with each attestation as `refs`). SealedRefsError when a
    declared source cannot be read: a lab of sandbox/truth.toml that a stratum without an
    archive names, and every stratum with an archive."""
    root = Path(root)
    twins = []
    try:
        strata = _strata(root)
        truth = {}
        tp = root / "sandbox" / "truth.toml"
        if tp.is_file():
            try:
                truth = tomllib.loads(tp.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                raise SealedRefsError("sandbox/truth.toml cannot be read") from None
        pins = {x.get("id"): x for x in truth.get("lab", []) if isinstance(x, dict)}
        for lab in sorted({str(m.get("lab")) for _, m in strata
                           if not m.get("archive") and m.get("lab") in pins}):
            twins += _lab2_twins(root, pins[lab])
        for stratum, meta in strata:
            if not meta.get("archive"):
                continue
            twins += _lab3_twins(root, stratum, meta, SEALED_REFERENCE_DIRS.get(stratum))
    except SealedRefsError:
        raise
    except Exception as e:
        raise SealedRefsError(f"the sealed references could not be read ({type(e).__name__}; "
                              "its message is withheld)") from None
    h = hashlib.sha256()
    for t in sorted(twins, key=lambda t: t.label):
        h.update(f"{t.label} {sha256_bytes(t.twin)} {sha256_bytes(t.learner)}\n".encode())
    return twins, f"{len(twins)} twins, sha256 {h.hexdigest()[:16]}"


def _sealed_fingerprint(root):
    """What the sealed twins depend on (paths, sizes, mtimes; never content)."""
    root = Path(root)
    parts = [root / "sandbox" / "truth.toml", Path(os.path.expanduser(AGE))]
    parts += sorted((root / "bench" / "local").glob("*/*/STRATUM.toml"))
    parts += sorted((root / "bench" / "local").glob("*/*/*.age"))
    parts += sorted((root / "Hidden").rglob("*.age")) if (root / "Hidden").is_dir() else []
    for d in SEALED_REFERENCE_DIRS.values():
        b = Path(os.path.expanduser(d))
        parts += sorted(b.rglob("*")) if b.is_dir() else [b]
    h = hashlib.sha256()
    for p in parts:
        try:
            st = p.stat()
            h.update(f"{p} {st.st_size} {st.st_mtime_ns}\n".encode())
        except OSError:
            h.update(f"{p} -\n".encode())
    return h.hexdigest()


def visible_shingles(root):
    """The 7-token shingles of every learner-visible course code file under
    dafny/, verus/ and harness/ (the given layers and every module's shipped
    files; never bench/)."""
    out = set()
    for rel in _course_code_files(root, ["dafny", "verus", "harness"]):
        out |= _shingles(_read(Path(root) / rel), rel)
    return out


@dataclass
class Span:
    """A minimal run of whole consecutive answer lines of a twin (lines the twin holds
    and its learner file does not) with at least SPAN_TOKENS tokens."""
    twin: str                       # a twin's course path, or a sealed twin's label (no text)
    shingles: frozenset = field(repr=False)
    forms: tuple = field(repr=False)  # renamed forms: (every identifier, the layers' names kept)
    content: bool                   # holds a line that is not structure_line
    sealed: bool = False            # a sealed reference's span (D31): its exact copy counts even
                                    # when the public pools show it
    exact: bool = False             # an exact copy counts: a shingle that is not generic
    renamed: tuple = (False, False)  # a renamed copy counts, per form


def _answer_blocks(root, sealed=()):
    """[(twin name, twin label, [lines], sealed)]: each twin's runs of answer lines (the
    course's twins by path; the sealed twins, SealedTwin, from memory by label)."""
    root = Path(root)
    out = []
    pairs = [(twin.name, twin.relative_to(root).as_posix(), _read(twin),
              _read(learner) if learner.is_file() else "", False)
             for twin, learner in _twin_pairs(root)]
    pairs += [(t.name, t.label, _text(t.twin), _text(t.learner), True) for t in sealed]
    for name, rel, text, ll, is_sealed in pairs:
        lines = set(x.strip() for x in ll.splitlines())
        twin = PurePosixPath(name)
        cur = []
        for x in text.splitlines():
            if x.strip() and x.strip() not in lines:
                cur.append(x)
            elif x.strip():
                if cur:
                    out.append((twin, rel, cur, is_sealed))
                cur = []
        if cur:
            out.append((twin, rel, cur, is_sealed))
    return out


class ScanIndex:
    """The reference twins' answer spans and what makes each one count (author_scan).

    Generic material never counts: (1) text a learner-visible course code file shows
    (the definitions a card copies from the given layers, every shipped file); (2) a
    shape common to the public pools: an exact shingle, or a span's renamed form,
    found in at least POOL_COMMON installed public benchmark files (the shape, for
    the renamed test only; see below); (3) language structure: a span of
    declaration headers, brackets and comments only has no renamed form that counts (an exact copy of it still does, when (1) and (2) leave
    a shingle).

    The exact test sets aside only (1) and pool-common shingles, never a span's
    shape: an exact copy of a pool-common or course-visible shape still counts
    when the card's identifiers match a twin's (fail-closed: an invented textbook
    lemma or loop that happens to equal a twin's answer word for word is refused,
    and the author renames or reworks it). Setting pool-common shapes aside for
    the exact test too was measured and not taken (DV5e review, 2026-10-13): it
    lost 15 of 626 planted whole answer regions (623 to 608) and 235 of 2,934
    single answer lines, for no card of the 78 (archive dv5e/reviewfix/); the
    user's decision D35 (2026-10-14) keeps the exact test so.

    The sealed references (D31; `sealed`, SealedTwin, from sealed_reference_twins)
    are twins like the course's, by label, with one difference: for their exact test
    the pool-common shingles are not set aside either, only text a learner-visible
    course file shows. Lab 2's public cards are drawn from the installed upstream
    sets, which hold their reference statements, so the pool rule would set aside the
    very copy the scan exists to catch (measured, 2026-10-14: 10 of the 68 sealed
    twins had no span that counted). Their renamed test keeps every set-aside."""

    def __init__(self, root, sealed=(), refs="0 twins"):
        root = Path(root)
        self.root = root
        self.refs = refs                # the sealed twins read (sealed_reference_twins' digest)
        self.visible = visible_shingles(root)
        self.literal = (_KEYWORDS, _KEYWORDS | _api_names(root))
        self.spans = []
        for twin, rel, blk, is_sealed in _answer_blocks(root, sealed):
            sizes = [len(tokens(x, twin.name)) for x in blk]
            for i in range(len(blk)):
                n = 0
                for j in range(i, len(blk)):
                    n += sizes[j]
                    if n >= SPAN_TOKENS:
                        toks = tokens("\n".join(blk[i:j + 1]), twin.name)
                        self.spans.append(Span(
                            rel, frozenset(_shingle_set(toks)),
                            tuple(renamed_form(toks, lit) for lit in self.literal),
                            any(not structure_line(x, twin.name) for x in blk[i:j + 1]),
                            sealed=is_sealed))
                        break
        self.anchors = ({}, {})
        for s in self.spans:
            for k in (0, 1):
                self.anchors[k].setdefault(s.forms[k][:SHINGLE], set()).add(s.forms[k])
        seen_forms = (set(), set())
        for rel in _course_code_files(root, ["dafny", "verus", "harness"]):
            f = self.forms_in(tokens(_read(root / rel), rel))
            seen_forms[0].update(f[0])
            seen_forms[1].update(f[1])
        cand = set().union(*(s.shingles for s in self.spans)) if self.spans else set()
        df, dform = {}, ({}, {})
        pools = _pool_files(root)
        digest = hashlib.sha256()
        for p in pools:
            data = p.read_bytes()
            digest.update(f"{p.relative_to(root).as_posix()} {sha256_bytes(data)}\n".encode())
            toks = tokens(_text(data), p.name)
            for x in _shingle_set(toks) & cand:
                df[x] = df.get(x, 0) + 1
            for k, found in enumerate(self.forms_in(toks)):
                for f in found:
                    dform[k][f] = dform[k].get(f, 0) + 1
        self.pool_files = len(pools)
        self.pool_sha256 = digest.hexdigest()
        for s in self.spans:
            s.exact = any(x not in self.visible and (s.sealed or df.get(x, 0) < POOL_COMMON)
                          for x in s.shingles)
            s.renamed = tuple(s.content and s.forms[k] not in seen_forms[k]
                              and dform[k].get(s.forms[k], 0) < POOL_COMMON for k in (0, 1))

    def forms_in(self, toks):
        """(set, set): the spans' renamed forms, per form, that occur in toks."""
        found = (set(), set())
        for k in (0, 1):
            anchors, lit = self.anchors[k], self.literal[k]
            for i in range(len(toks) - SHINGLE + 1):
                cands = anchors.get(renamed_form(toks[i:i + SHINGLE], lit))
                if not cands:
                    continue
                for f in cands:
                    if i + len(f) <= len(toks) and renamed_form(toks[i:i + len(f)], lit) == f:
                        found[k].add(f)
        return found

    def hits(self, text, name):
        """[(span, "whole" | "renamed")]: the spans the text holds, whole (every
        shingle of a span that counts as an exact copy) or as a renamed copy."""
        toks = tokens(text, name)
        have = _shingle_set(toks)
        forms = self.forms_in(toks)
        out = []
        for s in self.spans:
            if s.exact and s.shingles <= have:
                out.append((s, "whole"))
            elif any(s.renamed[k] and s.forms[k] in forms[k] for k in (0, 1)):
                out.append((s, "renamed"))
        return out


_SCAN_INDEX: dict = {}


def _scan_fingerprint(root):
    root = Path(root)
    h = hashlib.sha256()
    rels = _course_code_files(root, ["dafny", "verus", "harness", "Solutions/dafny",
                                     "Solutions/verus", "Solutions/harness", "Solutions/bench/local",
                                     "bench/local"])
    for p in [root / r for r in rels] + _pool_files(root):
        try:
            st = p.stat()
        except OSError:
            continue
        h.update(f"{p} {st.st_size} {st.st_mtime_ns}\n".encode())
    return h.hexdigest()


def scan_index(root, sealed=True):
    """The ScanIndex of root, kept for the process while no input file changes. With
    `sealed` (attestation) the sealed references are twins too (D31): read into memory
    by sealed_reference_twins, never written; SealedRefsError when a declared source
    cannot be read. A failure while they are in memory is reported by its type only."""
    key = (str(Path(root).resolve()), _scan_fingerprint(root),
           _sealed_fingerprint(root) if sealed else None)
    if key not in _SCAN_INDEX:
        _SCAN_INDEX.clear()
        if sealed:
            twins, refs = sealed_reference_twins(root)
            try:
                _SCAN_INDEX[key] = ScanIndex(root, twins, refs)
            except Exception as e:
                if not twins:
                    raise
                raise SealedRefsError(f"the scan failed ({type(e).__name__}) while the sealed "
                                      "references were in memory; its message is withheld") from None
            finally:
                del twins
        else:
            _SCAN_INDEX[key] = ScanIndex(root)
    return _SCAN_INDEX[key]


def answer_spans(root, visible=None):
    """[(twin path, frozenset of shingles)]: the spans an exact copy of which counts
    (ScanIndex; `visible` is accepted for the DV5d signature and unused)."""
    return [(s.twin, s.shingles) for s in scan_index(root).spans if s.exact]


def author_scan(root, files, sealed=True):
    """Problems (strings) when any file matches a leak pattern or holds a span of a
    reference twin's answer lines, whole or renamed (ScanIndex). Author context only.
    `sealed`: the sealed references are twins too (attestation, D31); a run's self-test
    passes False (DV6 review: an author run that stages a Lab 2 reference program, or
    runs where a sealed source is unreadable, is not an attestation).

    The recalibrations. DV5d: the first scan refused a file that shared any single
    7-token shingle with the twins' answer lines, and every Lab 2 card failed it on
    its own given text; a hit became a whole span of answer lines (at least
    SPAN_TOKENS tokens, every one of its shingles in the file), and text a
    learner-visible course file shows stopped counting. DV5e (the user's decision
    D25): generic structure stops counting (the shapes common to the public pools,
    and declaration headers, brackets and comments, in a renamed form; an exact
    copy of a twin's span, names and all, still counts: ScanIndex), and a renamed
    copy counts: a span's renamed form (renamed_form, with every identifier, and with
    the given layers' names kept) found as a contiguous run of the file's tokens is a
    hit when no learner-visible course file and fewer than POOL_COMMON public files
    show it. DV6 (the user's decision D31): Lab 2's sealed reference specifications
    and Lab 3's reference deliveries are twins too (sealed_reference_twins: decrypted
    into memory at attestation time, never written; their spans are named by label).
    Calibration (2026-10-13; Solutions/plans/DV4-author-notes.md): the 42
    shipped Lab 1 and Lab 2 cards and Lab 3's 36 sealed files pass at 9 tokens and
    above; a planted copy of a twin's whole answer region is caught in 623 of 626
    cases, renamed in 581 of 626. A shorter answer line alone is not caught (a known
    limit: it is caught inside a longer copied run; the leak patterns and the pool
    validation's task-form check remain)."""
    root = Path(root)
    problems = []
    pats = []
    lp = root / "tests" / "instructor" / "leak_patterns"
    for p in sorted(lp.glob("*.txt")) if lp.is_dir() else []:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("exempt:"):
                continue
            try:
                pats.append((p.name, re.compile(line, re.M)))
            except re.error:
                continue
    index = scan_index(root, sealed=sealed)
    for name, data in files.items():
        text = data.decode("utf-8", "replace")
        for pname, rx in pats:
            if rx.search(text):
                problems.append(f"{name} matches a leak pattern of {pname}")
                break
        try:
            found = index.hits(text, name)
        except Exception as e:
            raise SealedRefsError(f"the scan of {name} failed ({type(e).__name__}); its message "
                                  "is withheld (the sealed references are in memory)") from None
        if found:
            twins = sorted(set(s.twin for s, _ in found))
            renamed = sum(1 for _, how in found if how == "renamed")
            problems.append(f"{name} holds {len(found)} span(s) of a reference twin's answer lines "
                            f"({len(found) - renamed} whole, {renamed} renamed; "
                            f"{', '.join(twins[:3])}"
                            + (f" and {len(twins) - 3} more" if len(twins) > 3 else "") + ")"
                            + ("; no public pool is installed, so the pools' common shapes "
                               "were not set aside (scripts/get_bench.sh fetches them)"
                               if renamed and not index.pool_files else ""))
    return problems


def attest(root, card_rel, *, today=None):
    """Attest one lab task card's stripped form (author context only): scan it
    and, when clean, append its sha256 to sandbox/attested.toml. Returns
    (ok, message)."""
    root = Path(root)
    why = author_gate(root)
    if why:
        return False, (f"--attest is author-only and refuses to run here ({why}); the author "
                       "attests task cards in the authoring worktree (Δ103)")
    p = root / card_rel
    if rel_ok(card_rel) and lab_card(card_rel) and (not p.is_file() or p.is_symlink()):
        return False, f"{card_rel} is not a regular file"
    data = p.read_bytes() if p.is_file() and not p.is_symlink() else b""
    return attest_data(root, card_rel, data, today=today)


def _attested_entries(text):
    """(head, [(entry text, parsed entry)]) of sandbox/attested.toml's text."""
    parts = re.split(r"(?m)^(?=\[\[card\]\]\s*$)", text)
    head, out = parts[0], []
    for chunk in parts[1:]:
        try:
            data = tomllib.loads(chunk).get("card", [{}])[0]
        except (ValueError, IndexError):
            data = {}
        out.append((chunk, data))
    return head, out


def attest_data(root, card_rel, data, *, today=None, source=None):
    """attest() on given bytes: a sealed stratum's card (Lab 3's crate tasks,
    bench/local/q/crate/tasks.tar.age) is attested from the author's decrypted
    copy before any learner may unseal it, at the path `fvh unseal` writes it
    to. `source` (optional) is recorded with the entry.

    Each entry records the scan rule it passed (`scan`, SCAN_RULE), the public
    pools that rule read (`pools`) and the sealed reference twins it read (`refs`,
    sealed_reference_twins' digest: D31). A card attested under an earlier rule, or
    against other sealed references (a re-seal), is scanned again: when it passes, its
    entry is rewritten (the date, the rule, the pools, the references; an earlier
    `source` is kept unless a new one is given); when it fails, the entry is withdrawn.
    When a sealed reference source cannot be read the card is refused and the file is
    not changed (fail-closed; an earlier entry is neither rewritten nor withdrawn)."""
    root = Path(root)
    why = author_gate(root)
    if why:
        return False, (f"--attest is author-only and refuses to run here ({why}); the author "
                       "attests task cards in the authoring worktree (Δ103)")
    if not rel_ok(card_rel) or not lab_card(card_rel):
        return False, f"{card_rel}: a lab task card lives under bench/local/"
    cls = source_class(card_rel)
    if cls:
        return False, f"{card_rel} is in a refused source class ({cls})"
    digest = sha256_bytes(data)
    try:
        index = scan_index(root)
        problems = None
    except SealedRefsError as e:
        return False, (f"not attested, and sandbox/attested.toml is unchanged: the sealed "
                       f"references the scan reads as twins could not be read ({e}; D31)")
    path = root / "sandbox" / "attested.toml"
    text = path.read_text(encoding="utf-8") if path.is_file() else "schema = 1\n"
    head, entries = _attested_entries(text)
    mine = [e for e in entries if e[1].get("sha256") == digest]
    if any(e[1].get("scan") == SCAN_RULE and e[1].get("path") == card_rel
           and e[1].get("refs") == index.refs for e in mine):
        return True, f"{card_rel} is already attested ({digest[:16]}…)"
    try:
        problems = author_scan(root, {card_rel: data})
    except SealedRefsError as e:
        return False, f"not attested, and sandbox/attested.toml is unchanged: {e}"
    rest = [e for e in entries if e[1].get("sha256") != digest]
    if problems:
        if mine:
            body = head + "".join(e[0] for e in rest)
            path.write_text(body if body.endswith("\n") else body + "\n", encoding="utf-8")
            return False, ("not attested, and its earlier attestation is withdrawn: "
                           + "; ".join(problems))
        return False, "not attested: " + "; ".join(problems)
    if source is None:
        source = next((e[1].get("source") for e in mine if e[1].get("source")), None)
    entry = (f'[[card]]\npath = "{card_rel}"\nsha256 = "{digest}"\n'
             f'attested = "{(today or date.today()).isoformat()}"\n'
             f'scan = "{SCAN_RULE}"\n'
             f'pools = "{index.pool_files} files, sha256 {index.pool_sha256[:16]}"\n'
             f'refs = "{index.refs}"\n')
    if source:
        entry += f"source = {json.dumps(source, ensure_ascii=False)}\n"
    if mine:
        # rewritten in place: the first of its entries keeps its position, the others go
        kept = [e for e in entries if e is mine[0] or e not in mine]
        body = head + "".join((entry + ("\n" if i < len(kept) - 1 else "")) if e is mine[0]
                              else e[0] for i, e in enumerate(kept))
        verb = "re-attested"
    else:
        if not text.endswith("\n"):
            text += "\n"
        body = text + "\n" + entry
        verb = "attested"
    path.write_text(body if body.endswith("\n") else body + "\n", encoding="utf-8")
    return True, f"{verb} {card_rel} ({digest[:16]}…) in sandbox/attested.toml"



def rescan_attested(root, *, today=None):
    """Re-scan every entry of sandbox/attested.toml under SCAN_RULE (author context only;
    the user's decision D31: every attested entry is re-scanned once with the sealed
    references as twins). An entry's bytes come from the tree, or, for a sealed stratum's
    file, from its archive decrypted into memory at the path `fvh unseal` writes. Returns
    (ok, [{"path", "sha256", "result", "detail"}]): result is `re-attested`, `already`
    (attested under this rule against these references), `withdrawn` (the scan found a
    hit: the entry is removed), `stale` (no file of the tree, and no sealed file, holds
    the entry's sha256 at its path: left as is, not re-scanned) or `refused` (another
    refusal, the entry left as is). ok is False when nothing could be scanned (the author
    gate, or a sealed reference source that cannot be read)."""
    root = Path(root)
    why = author_gate(root)
    if why:
        return False, [{"path": "", "sha256": "", "result": "refused",
                        "detail": f"--attest-rescan is author-only and refuses to run here ({why})"}]
    try:
        scan_index(root)
        sealed = {}
        for stratum, meta in _strata(root):
            if meta.get("archive"):
                files = _sealed_tree(root, str(meta["archive"]), want_sha=meta.get("archive_sha256"),
                                     want_manifest=meta.get("manifest_sha256"),
                                     want_files=meta.get("files"), recipient=meta.get("recipient"),
                                     lab=meta.get("lab") or meta.get("module"))
                sealed.update({f"{stratum}/{k}": v for k, v in files.items()
                               if k != "MANIFEST.sha256"})
    except SealedRefsError as e:
        return False, [{"path": "", "sha256": "", "result": "refused",
                        "detail": f"nothing re-scanned: {e}"}]
    path = root / "sandbox" / "attested.toml"
    text = path.read_text(encoding="utf-8") if path.is_file() else "schema = 1\n"
    out = []
    for _, e in _attested_entries(text)[1]:
        rel, want = str(e.get("path", "")), str(e.get("sha256", ""))
        data = sealed.get(rel)
        if data is None and rel_ok(rel) and (root / rel).is_file() and not (root / rel).is_symlink():
            data = (root / rel).read_bytes()
        if data is None or sha256_bytes(data) != want:
            out.append({"path": rel, "sha256": want, "result": "stale",
                        "detail": "no file at its path holds its sha256; left as is"})
            continue
        ok, msg = attest_data(root, rel, data, today=today)
        if ok:
            result = "already" if "already attested" in msg else "re-attested"
        else:
            result = "withdrawn" if "withdrawn" in msg else "refused"
        out.append({"path": rel, "sha256": want, "result": result,
                    "detail": "" if ok else msg})
    return True, out

# --- the docker argv (§5.5, §5.6.2, §5.8) ---------------------------------------------------------

def container_name(manifest):
    return f"dvl-{manifest.run_id}"


def work_mounts(manifest):
    """[(destination, docker --mount value)] of /work: the /work tmpfs, one
    tmpfs per directory that holds an editable file, and a read-only bind for
    every other input, parents before children (DV4-PLAN §5.5, as built at
    step 2b: runc creates a bind's missing parent directories as root, so an
    editable file's directory is a tmpfs of its own, mode 1777, where uid 1000
    may write beside the read-only binds; the sticky bit keeps those binds,
    which are root's mount points, from being renamed or removed)."""
    lim = manifest.limits
    edirs = manifest.editable_dirs()
    sub = [d for d in edirs if d]
    share = max(16, lim["work_mb"] // max(1, len(sub))) if sub else lim["work_mb"]
    root_mb = lim["work_mb"] if "" in edirs else 1
    out = [(WORK, f"type=tmpfs,destination={WORK},tmpfs-size={root_mb * 1024 * 1024},"
                  f"tmpfs-mode={'1777' if '' in edirs else '755'}")]
    for d in sub:
        out.append((f"{WORK}/{d}", f"type=tmpfs,destination={WORK}/{d},"
                                   f"tmpfs-size={share * 1024 * 1024},tmpfs-mode=1777"))
    return out


def owner_label():
    """dvl.owner=<pid>:<start time>: the reaper's test that the run's owner lives."""
    return f"{os.getpid()}:{_proc_start(os.getpid())}"


def _proc_start(pid):
    try:
        with open(f"/proc/{pid}/stat", encoding="ascii") as fh:
            return fh.read().rsplit(")", 1)[1].split()[19]
    except (OSError, IndexError):
        return "0"


def exec_env(manifest):
    cap_mode = "container-agent" if manifest.kind == "agent" else "container-verify"
    return ["--env", f"DVL_CAP={cap_mode}", "--env", f"DVL_RUN={manifest.run_id}",
            "--env", f"DVL_SCRATCH={CONTAINER_SCRATCH}", "--env", "DVL_DAFNY_JOBS=1",
            "--env", "DVL_VERUS_JOBS=1"]


def command_argv(manifest, argv):
    """The docker exec line of one [[command]]: a tool copy through the image's
    python3 (the binds are 0444: nothing under /work is executed directly)."""
    name = container_name(manifest)
    if argv[0] == CONTROLS:
        return ["docker", "exec", name, CONTAINER_PYTHON, "-B", *argv]
    if argv[0] == TRUTHCHECK:
        return ["docker", "exec", *exec_env(manifest), name, CONTAINER_PYTHON, "-B", *argv]
    return ["docker", "exec", *exec_env(manifest), name, CONTAINER_PYTHON, "-B",
            f"{WORK}/{argv[0]}", *argv[1:]]


def docker_argv(manifest, run_path, owner="$OWNER"):
    """The argv lines of one run, in order: run (detached; the entry process
    waits), the input stream of the editable files into /work, the in-container
    controls, each [[command]], the return stream out of the editable
    directories (agent runs), and the removal. `run_path` is the run directory
    and `owner` the dvl.owner label (placeholders in --dry-run's golden
    lines). An opencode agent run adds agent_lines after the commands: its
    config in, the two debug views of the per-run gate, and the run (shown
    with the manifest's wall clock; a live run passes what is left of it)."""
    rp = str(run_path)
    lim = manifest.limits
    mem = f"{lim['mem_gb']:g}g"
    name = container_name(manifest)
    argv = ["docker", "run", "--detach", "--name", name, "--label", f"dvl.run={manifest.run_id}",
            "--label", f"dvl.owner={owner}", "--user", CONTAINER_UID, "--read-only",
            "--tmpfs", f"/tmp:rw,nosuid,nodev,exec,size={lim['tmp_mb']}m",
            "--tmpfs", f"/home/agent:rw,nosuid,nodev,size={home_mb()}m,uid=1000,gid=1000,mode=0700"]
    mounts = [(d, m) for d, m in work_mounts(manifest)]
    for e in manifest.files:
        if e.role != "editable":
            mounts.append((f"{WORK}/{e.dst}",
                           f"type=bind,source={rp}/in/{e.dst},destination={WORK}/{e.dst},readonly"))
    if manifest.network != "none":
        sock = "ollama.sock" if manifest.network == "ollama" else "egress.sock"
        mounts.append((f"{RELAY_DIR}/{sock}",
                       f"type=bind,source={rp}/state/{sock},destination={RELAY_DIR}/{sock}"))
    if manifest.truth:
        mounts.append((TRUTH_DIR, f"type=bind,source={rp}/truth,destination={TRUTH_DIR},readonly"))
    for _, m in sorted(mounts, key=lambda x: (x[0].count("/"), x[0])):
        argv += ["--mount", m]
    argv += ["--network", "none",
             "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
             "--pids-limit", str(lim["pids"]), "--memory", mem, "--memory-swap", mem,
             "--cpus", f"{lim['cpus']:g}", "--ulimit", f"nofile={NOFILE}:{NOFILE}", "--init",
             *exec_env(manifest), "--workdir", WORK, manifest.image, ENTRY, manifest.kind]
    lines = [argv]
    lines.append(["docker", "exec", "--interactive", name, "/usr/bin/tar", "--extract",
                  "--no-same-owner", "--no-same-permissions", "--directory", WORK, "--file", "-"])
    lines.append(["docker", "exec", "--interactive", name, CONTAINER_PYTHON, "-B", CONTROLS, "check"])
    for c in manifest.commands:
        lines.append(command_argv(manifest, c))
    if manifest.kind == "agent" and (manifest.agent or {}).get("cli") == "opencode":
        lines += agent_lines(manifest, lim["wall_clock_s"])
    if manifest.kind == "agent":
        lines.append(["docker", "exec", name, "/usr/bin/tar", "--create", "--directory", WORK,
                      "--file", "-", *[d or "." for d in manifest.editable_dirs()]])
    lines.append(["docker", "rm", "--force", name])
    return lines


def input_stream(manifest, run):
    """The tar stream of the editable files (regular files only, uid 1000,
    mode 0644), as bytes."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tf:
        for e in sorted(manifest.files, key=lambda x: x.dst):
            if e.role != "editable":
                continue
            data = (run.inp / e.dst).read_bytes()
            ti = tarfile.TarInfo(e.dst)
            ti.size, ti.mode, ti.uid, ti.gid, ti.mtime = len(data), 0o644, 1000, 1000, 0
            ti.uname = ti.gname = "agent"
            tf.addfile(ti, io.BytesIO(data))
    return buf.getvalue()


# --- the return path (§5.8) ----------------------------------------------------------------------

@dataclass
class ReturnResult:
    returned: dict = field(default_factory=dict)     # dst -> bytes (changed returned files)
    unchanged: list = field(default_factory=list)
    deleted: list = field(default_factory=list)
    rejected: list = field(default_factory=list)     # {name, size, sha256, why}
    diff: str = ""

    def summary(self):
        return {"returned": sorted(self.returned), "unchanged": sorted(self.unchanged),
                "deleted": sorted(self.deleted), "rejected": self.rejected}


def _member_name(name):
    n = name
    while n.startswith("./"):
        n = n[2:]
    return n.rstrip("/")


def _drain(fobj, limit):
    """(kept bytes or None when over `limit`, total size, sha256) of a member,
    reading at most `limit` bytes into memory."""
    h, kept, total = hashlib.sha256(), bytearray(), 0
    while True:
        chunk = fobj.read(65536)
        if not chunk:
            break
        total += len(chunk)
        h.update(chunk)
        if total <= limit:
            kept += chunk
    return (bytes(kept) if total <= limit else None), total, h.hexdigest()


def parse_return(stream, manifest, staged, *, cap=RETURN_CAP_BYTES):
    """Parse a `tar --create -C /work .` stream (a binary file object) member by
    member, never extracting it and never opening a path the container made.
    `staged`: {dst: bytes} of what entered (editable files and the read-only
    roles). Returns a ReturnResult; its `diff` is the patch of the returned
    files against the staged inputs, under their course paths."""
    returns = set(manifest.returns)
    src_of = {e.dst: (e.src or e.dst) for e in manifest.files}
    res = ReturnResult()
    seen = set()

    def reject(name, size, digest, why):
        res.rejected.append({"name": name, "size": size, "sha256": digest, "why": why})

    try:
        tf = tarfile.open(fileobj=stream, mode="r|")
    except tarfile.TarError as e:
        raise SandboxError(f"the return stream is not a tar stream: {e}") from None
    with tf:
        try:
            for m in tf:
                raw = m.name
                name = _member_name(raw)
                if name in ("", "."):
                    continue
                if raw.startswith("/") or ".." in name.split("/") or "\0" in name:
                    reject(raw, m.size, None, "a path that leaves /work")
                    continue
                if name in seen:
                    reject(name, m.size, None, "a repeated member")
                    continue
                seen.add(name)
                if m.isdir():
                    continue
                if not m.isreg():
                    kind = ("symlink" if m.issym() else "hard link" if m.islnk() else
                            "device" if (m.ischr() or m.isblk()) else "FIFO" if m.isfifo() else
                            "special member")
                    reject(name, m.size, None, f"a {kind} (only regular files return)")
                    continue
                fobj = tf.extractfile(m)
                if fobj is None:
                    reject(name, m.size, None, "unreadable member")
                    continue
                if name in returns:
                    data, size, digest = _drain(fobj, cap)
                    if data is None:
                        reject(name, size, digest, f"over the size cap ({cap} bytes)")
                        continue
                    try:
                        data.decode("utf-8")
                    except UnicodeDecodeError:
                        reject(name, size, digest, "not valid UTF-8")
                        continue
                    if data == staged.get(name):
                        res.unchanged.append(name)
                    else:
                        res.returned[name] = data
                    continue
                data, size, digest = _drain(fobj, cap)
                if name in staged and data is not None and data == staged[name]:
                    continue        # a read-only input, as it entered
                reject(name, size, digest, "not a return path" if name not in staged
                       else "a changed read-only input")
        except tarfile.TarError as e:
            raise SandboxError(f"the return stream broke off: {e}") from None
    for p in sorted(returns - set(res.returned) - set(res.unchanged)):
        if p not in {r["name"] for r in res.rejected}:
            res.deleted.append(p)
    res.diff = unified_patch(res, staged, src_of)
    return res


def unified_patch(res, staged, src_of):
    """A git-style patch of the returned and deleted files, under course paths."""
    out = []
    for dst in sorted(set(res.returned) | set(res.deleted)):
        path = src_of.get(dst, dst)
        old = staged.get(dst, b"").decode("utf-8", "replace").splitlines(keepends=True)
        new = [] if dst in res.deleted else res.returned[dst].decode("utf-8").splitlines(keepends=True)
        out.append(f"diff --git a/{path} b/{path}\n")
        if dst in res.deleted:
            out.append("deleted file mode 100644\n")
        body = list(difflib.unified_diff(old, new, f"a/{path}", "/dev/null" if dst in res.deleted else f"b/{path}"))
        for line in body:
            out.append(line if line.endswith("\n") else line + "\n\\ No newline at end of file\n")
    return "".join(out)


# --- the secret scan (§5.7) -----------------------------------------------------------------------

def secret_scan(data, exact=()):
    """[(finding id, offset)] for every credential format in `data` (bytes),
    and for each exact token value given. Never returns the content."""
    hits = []
    for pid, rx in SECRET_PATTERNS:
        for m in rx.finditer(data):
            hits.append((pid, m.start()))
    for tok in exact:
        if tok:
            b = tok.encode() if isinstance(tok, str) else tok
            i = data.find(b)
            if i >= 0:
                hits.append(("exact-token", i))
    return hits


def withheld_record(name, data, hits):
    return {"name": name, "size": len(data), "sha256": sha256_bytes(data),
            "findings": sorted({h[0] for h in hits})}


# --- records (§3.6) -------------------------------------------------------------------------------

def write_records(dest, manifest, report):
    """manifest.json (the normalized manifest with its sha256) and
    selftest.json (the self-test report) in a run's record directory."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    doc = manifest.doc()
    # inline texts are recorded by hash only: the contract text is in the
    # learner's own CLAUDE.md, the task statement in its card
    for f in doc["file"]:
        if "text" in f:
            f["text"] = None
            f["text_sha256"] = f["sha256"]
    (dest / "manifest.json").write_text(
        json.dumps({"sha256": manifest.sha256(), "manifest": doc}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    (dest / "selftest.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                        encoding="utf-8")
    return dest / "manifest.json", dest / "selftest.json"


# --- docker access (§5.1) -------------------------------------------------------------------------

def check_access(timeout_s=10):
    """(ok, message). A read-only `docker version`; on refusal, a diagnosis
    read from `id` and `getent` only. Never sg, never sudo (P8). With
    DVL_NO_DOCKER=1 (the CI environment) it refuses before running anything."""
    if os.environ.get("DVL_NO_DOCKER") == "1":
        return False, "DVL_NO_DOCKER=1 is set (the CI environment): no container runs here"
    try:
        p = subprocess.run(["docker", "version", "--format", "{{.Server.Version}}"],
                           capture_output=True, text=True, timeout=timeout_s, stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        return False, "docker is not installed (no docker on PATH)"
    except subprocess.TimeoutExpired:
        return False, f"docker version did not answer within {timeout_s} s (is the daemon running?)"
    if p.returncode == 0 and p.stdout.strip():
        return True, f"docker access: ok (server {p.stdout.strip()})"
    err = (p.stderr.strip().splitlines() or ["(no message)"])[-1]
    return False, diagnose(err)


def _cmd_out(argv):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=10, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return p.stdout if p.returncode == 0 else ""


def diagnose(err):
    user = (_cmd_out(["id", "-un"]) or "").strip() or os.environ.get("USER", "this user")
    groups = (_cmd_out(["id", "-nG"]) or "").split()
    entry = (_cmd_out(["getent", "group", "docker"]) or "").strip()
    members = entry.split(":")[3].split(",") if entry.count(":") >= 3 and entry.split(":")[3] else []
    if not entry:
        return (f"docker refused ({err}); there is no docker group on this host. "
                "Container runs need Docker installed with its group (design §13.3).")
    if user in members and "docker" not in groups:
        return (f"docker refused ({err}). {user} is listed in the docker group, but this login "
                "predates the change: log in again (or start a shell with `newgrp docker`) and re-run.")
    if user not in members:
        return (f"docker refused ({err}). Δ60's host action (H1) is not done: the human runs "
                f"`sudo usermod -aG docker {user}` and logs in again. This script never escalates.")
    return f"docker refused ({err}), although {user} is in the docker group; is the daemon running?"


# --- the course inputs of a run (step 2b) ---------------------------------------------------------

def readonly_inputs(root, rec, langs, *, audits=()):
    """[(src, role)] of the read-only inputs a run of module `rec` in the given
    languages needs: the given layer chain, the project files (dafny/options,
    every unit's dfyconfig.toml or Cargo.toml, the workspace pins), the trusted
    tools and the module's pins (counts, freeze, the trust allowlist, and the
    named .audit files). The Verus workspace file is generated (`verus_workspace`)."""
    import gen_units
    root = Path(root)
    out = []
    chain = layer_chain(rec.get("layer", ""))
    if "dafny" in langs:
        for layer in chain:
            d = root / "dafny" / "given" / gen_units.layer_track(layer)
            for f in sorted(d.glob(gen_units.dafny_layer_glob(layer))):
                out.append((f.relative_to(root).as_posix(), "given"))
        od = root / "dafny" / "options"
        for f in sorted(od.glob("*")) if od.is_dir() else []:
            if f.is_file() and not f.is_symlink():
                out.append((f.relative_to(root).as_posix(), "project"))
        for u in unit_dirs(rec):
            if (root / u / "dfyconfig.toml").is_file():
                out.append((f"{u}/dfyconfig.toml", "project"))
    if "verus" in langs:
        for layer in chain:
            cdir = root / gen_units.verus_given_crate_dir(layer)
            for f in sorted(cdir.rglob("*")) if cdir.is_dir() else []:
                rel = f.relative_to(root).as_posix()
                if f.is_file() and not f.is_symlink() and source_class(rel) is None:
                    out.append((rel, "given"))
        for u in unit_dirs(rec):
            if u.startswith("verus/") and (root / u / "Cargo.toml").is_file():
                out.append((f"{u}/Cargo.toml", "project"))
        for f in ("verus/Cargo.lock", "verus/rust-toolchain.toml"):
            if (root / f).is_file():
                out.append((f, "project"))
    for t in TRUSTED_TOOLS:
        if (root / t).is_file():
            out.append((t, "tool"))
    for f in sorted((root / "scripts" / "dvl").glob("*")):
        rel = f.relative_to(root).as_posix()
        if f.is_file() and not f.is_symlink() and tool_ok(rel):
            out.append((rel, "tool"))
    mid = rec["id"]
    for name in (f"{mid}.counts", f"{mid}.freeze") + (("verus_trust.toml",) if "verus" in langs else ()):
        if (root / "expected" / name).is_file():
            out.append((f"expected/{name}", "expected"))
    for a in audits:
        out.append((a, "expected"))
    seen, uniq = set(), []
    for src, role in out:
        if src not in seen:
            seen.add(src)
            uniq.append((src, role))
    return uniq


def verus_workspace(root, rec):
    """The generated workspace file: the module's crates and its given chain only
    (the checkout's workspace lists every module, whose crates never enter)."""
    import gen_units
    root = Path(root)
    members = [gen_units.verus_given_crate_dir(layer)[len("verus/"):]
               for layer in layer_chain(rec.get("layer", ""))
               if (root / gen_units.verus_given_crate_dir(layer)).is_dir()]
    members += [u[len("verus/"):] for u in unit_dirs(rec)
                if u.startswith("verus/") and (root / u / "Cargo.toml").is_file()]
    return ("# Generated by scripts/mksandbox-run: the run's workspace, only the module's\n"
            "# crates and its layer chain (the checkout's workspace lists every module).\n"
            "[workspace]\nresolver = \"2\"\nmembers = [" + ", ".join(json.dumps(m) for m in members)
            + "]\n")


def _all_records(root):
    import check_course_map as ccm
    data, err = ccm.load_registry(Path(root))
    if err:
        raise ManifestError(f"the registry is unusable: {err}")
    return [m for m in data.get("module", []) if m.get("status") != "planned"]


def course_path(root, target):
    """(course-relative path, work-copy base or None) of a target: a path in the
    course root, or a copy outside it or under research/ (the executor's work
    copy, a returned file) whose course path is the longest suffix that names a
    module's file, a unit directory or a benchmark task."""
    root = Path(root).resolve()
    p = Path(target)
    if not p.is_absolute():
        p = root / p
    p = Path(os.path.abspath(p))
    try:
        rel = p.relative_to(root).as_posix()
        if source_class(rel) != "research":
            return rel, None
    except ValueError:
        pass
    # a copy outside the course root, or an agent's files under research/
    recs = _all_records(root)
    parts = p.parts
    for i in range(1, len(parts)):
        cand = "/".join(parts[i:])
        if not rel_ok(cand):
            continue
        if bench_task(cand) or any(learner_ok(cand, r) or cand in unit_dirs(r) for r in recs):
            return cand, Path(*parts[:i])
    raise ManifestError(f"{target}: no suffix of this path is a course file, a unit or a "
                        "benchmark task")


def module_of(root, rel):
    hits = [r for r in _all_records(root) if learner_ok(rel, r) or rel in unit_dirs(r)
            or any(u.startswith(rel + "/") for u in unit_dirs(r))]
    if len(hits) != 1:
        raise ManifestError(f"{rel}: {'no' if not hits else len(hits)} module(s) declare it; name "
                            "the module")
    return hits[0]


def _unit_files(root, rec, rel):
    """The learner files a verification of `rel` needs: every source file of the
    unit that holds it (or that it is), else `rel` itself (or the files under it)."""
    root = Path(root)
    units = [u for u in unit_dirs(rec) if rel == u or rel.startswith(u + "/")]
    tops = units or [rel]
    out = []
    for t in tops:
        p = root / t
        if p.is_file():
            out.append(t)
            continue
        for f in sorted(p.rglob("*")) if p.is_dir() else []:
            r = f.relative_to(root).as_posix()
            if f.is_file() and not f.is_symlink() and source_class(r) is None \
                    and f.name not in PROJECT_NAMES:
                out.append(r)
    return out


LAB_TASK_DIR = "lab-task"        # fvh.tools.runners.LAB_TASK_DIR: a lab run's staged task form


def build_verify(root, target, argv, *, module=None, run_id=None, kind="verify", mem_gb=None,
                 network="none", model="qwen3.8:latest", audits=(), lab_task=None, rev=None):
    """The raw manifest of one tool command on one target (DV4-PLAN §5.9).

    `target` is a course path, or a copy outside the course root (its course
    path is found by `course_path`; every regular file under the copy's base
    enters inline, as agent output, over the course's own files). `argv` is
    the tool command with the course path in it (`scripts/vcheck --gate --json
    <path>`). kind "verify" gives a verification container; kind "agent" a
    probe agent container (`[agent] cli = "none"`, for the parity acceptance
    and the doors; `mksandbox-run --probe` only).

    `lab_task` (a lab batch's lever check, Δ182): the task form's course path
    (a benchmark task); its text is staged read-only (role task) at
    lab-task/<path>, where `argv`'s `--lab-task` names it. `rev` (`fvh report
    --reverify`): every course file staged from the checkout is read at that
    commit instead. A Python target (a learner harness file) also gets its
    acceptance run's support files (python_support): the frozen core, the
    frozen tests and the module's fixtures, the project's pins."""
    root = Path(root).resolve()
    rel, base = course_path(root, target)
    lab = None if module else stratum_module(root, rel)
    rec = registry_record(root, module or lab) if (module or lab) else module_of(root, rel)
    texts = {}
    if base is not None:
        for f in sorted(Path(base).rglob("*")):
            if f.is_symlink() or not f.is_file():
                continue
            r = f.relative_to(base).as_posix()
            if len(texts) >= 64:
                raise ManifestError(f"{base}: more than 64 files")
            data = f.read_bytes()
            try:
                texts[r] = data.decode("utf-8")
            except UnicodeDecodeError:
                raise ManifestError(f"{r}: not valid UTF-8") from None
    files, seen = [], set()

    def add(src, role):
        if src in seen:
            return
        seen.add(src)
        data = read_source(root, Entry(src, src, role, "0" * 64, rev))
        f = {"src": src, "dst": src, "role": role, "sha256": sha256_bytes(data)}
        if rev:
            f["rev"] = rev
        files.append(f)

    def add_text(dst, role, text):
        seen.add(dst)
        files.append({"dst": dst, "role": role, "text": text,
                      "sha256": sha256_bytes(text.encode("utf-8"))})

    editable = _unit_files(root, rec, rel) if (root / rel).exists() else []
    for r in sorted(set(editable) | set(texts)):
        if r in texts:
            add_text(r, "editable", texts[r])
        else:
            add(r, "editable")
    langs = {lang_pool(r) for r in seen} - {None}
    # at a commit, the read-only inputs are the ones that exist there (the tree's
    # listing may hold files committed later)
    at_rev = _tree_files(root, ".", rev) if rev else None
    for src, role in readonly_inputs(root, rec, langs, audits=audits):
        if src == "verus/Cargo.toml" or (at_rev is not None and src not in at_rev):
            continue
        add(src, role)
    if "python" in langs:
        for src, role in python_support(root, rec, rel, rev):
            add(src, role)
    if "verus" in langs:
        add_text("verus/Cargo.toml", "project", verus_workspace(root, rec))
    if lab_task is not None:
        if not rel_ok(lab_task) or not bench_task(lab_task):
            raise ManifestError(f"--lab-task {lab_task}: the lab gate's task form is a benchmark "
                                "task (bench/local/<q|r>/<lab>/[<card>/]tasks/… or "
                                "bench/public/<set>/tasks/…)")
        want = f"{LAB_TASK_DIR}/{lab_task}"
        if want not in list(argv):
            raise ManifestError(f"--lab-task: the command does not name {want} (vcheck --gate "
                                f"--lab-task {want} <delivery>)")
        if rev is None:
            is_dir = (root / lab_task).is_dir()
            forms = sorted(f.relative_to(root).as_posix() for f in (root / lab_task).rglob("*")
                           if f.is_file() and not f.is_symlink()
                           and "target" not in f.relative_to(root / lab_task).parts) \
                if is_dir else []
        else:
            at = _tree_files(root, lab_task, rev)
            is_dir = lab_task not in at and bool(at)
            forms = sorted(x for x in at if "/target/" not in x[len(lab_task):] + "/")
        if is_dir:
            # a crate card (Lab 3): every regular file of the task form's directory,
            # each staged read-only under lab-task/<card dir>/ (the lever check compares
            # the two directories file by file); at `rev`, the files of that commit
            if not forms or len(forms) > 64:
                raise ManifestError(f"--lab-task {lab_task}: a crate task form holds 1 to 64 "
                                    "files")
            for r in forms:
                data = read_source(root, Entry(r, r, "task", "0" * 64, rev))
                try:
                    add_text(f"{LAB_TASK_DIR}/{r}", "task", data.decode("utf-8"))
                except UnicodeDecodeError:
                    raise ManifestError(f"{r}: the task form is not valid UTF-8") from None
        else:
            data = read_source(root, Entry(lab_task, lab_task, "task", "0" * 64, rev))
            try:
                add_text(want, "task", data.decode("utf-8"))
            except UnicodeDecodeError:
                raise ManifestError(f"{lab_task}: the task form is not valid UTF-8") from None
    lock = read_images_lock(root)
    want = "dvl-toolchain@" if kind == "verify" else "dvl-agent@"
    image = next((k for k in lock if k.startswith(want)), want + "sha256:" + "0" * 64)
    raw = {"schema": SCHEMA, "run_id": run_id or f"v{os.getpid()}-{secrets.token_hex(4)}",
           "module": rec["id"], "kind": kind, "image": image, "network": network,
           "limits": {"wall_clock_s": 3 * 1800 + 600}, "file": files, "return": [],
           "command": [{"argv": list(argv)}]}
    if mem_gb is not None:
        # a cap (a lane's memory share), never above the pinned bound of the
        # run's language: a Dafny job runs in container-verify mode only in a
        # container no larger than its own bound (scripts/dvl/pins.toml)
        raw["limits"]["mem_gb"] = min(float(mem_gb), memory_bound_gb(kind, run_pools(files)))
    if kind == "agent":
        raw["agent"] = {"cli": "none", "model": model, "turns": 1}
    return raw, rel


AGENT_BRIEF = "TASK.md"          # an agent-mode attempt's brief, at /work's top (build_agent)
CRATE_MAX_FILES = 64


def task_files(root, task):
    """(editable, companions) of a benchmark task, as course paths: a task file is
    its own one editable file; a crate task's directory (Lab 3's layout) has its
    src/**/*.rs editable and its other regular files (Cargo.toml, frozen.rs, ...)
    as read-only companions. ManifestError for anything else (a link, a target/
    tree's files are skipped, more than CRATE_MAX_FILES files)."""
    root = Path(root)
    if not rel_ok(task) or not bench_task(task):
        raise ManifestError(f"{task}: an agent-mode task is a benchmark task (a task file, or a "
                            "crate card's tasks directory)")
    p = root / task
    if p.is_file() and not p.is_symlink():
        return (task,), ()
    if not p.is_dir() or p.is_symlink():
        raise ManifestError(f"{task}: no such task file or crate directory")
    if not (p / "Cargo.toml").is_file() or not (p / "src" / "lib.rs").is_file():
        raise ManifestError(f"{task}: a crate task's directory holds Cargo.toml and src/lib.rs")
    ed, co = [], []
    for f in sorted(p.rglob("*")):
        r = f.relative_to(p)
        if "target" in r.parts:
            continue
        if f.is_symlink():
            raise ManifestError(f"{task}: a crate task holds no link ({r.as_posix()})")
        if not f.is_file():
            continue
        (ed if r.parts[0] == "src" and f.suffix == ".rs" else co).append(f"{task}/{r.as_posix()}")
    if len(ed) + len(co) > CRATE_MAX_FILES:
        raise ManifestError(f"{task}: more than {CRATE_MAX_FILES} files")
    return tuple(ed), tuple(co)


def build_agent(root, task, *, brief, model, turns, module=None, run_id=None, wall_s=2700,
                gpu_s=None, mem_gb=None, texts=None):
    """The raw manifest of one fvh agent-mode attempt on a benchmark task (fvh.batch
    with fvh.backends.agent; DV5d): opencode and the pinned model behind the run's
    gate, as contract_local.sh's replay, with a task in place of a contract.

    Staged: the brief inline at AGENT_BRIEF (role task; the file agent_brief
    points the agent at); the task's editable files (task_files: the task file,
    or a crate's src/**/*.rs) by src, or, with `texts` ({course path: text} of
    every editable file), inline as the work copy a continuation starts from;
    a crate's companions read-only (role task) by src; the module's given chain,
    project files, trusted tools and pins (readonly_inputs) and, for Verus, the
    generated workspace. The module is `module`, else the task's stratum's lab
    (STRATUM.toml). The return set is the editable files. `mem_gb` caps the
    container (a lane's share), never above the pinned agent bound of the run's
    language; `wall_s` is the run's wall clock, `turns` opencode's step limit
    and the gate's call cap, `gpu_s` the gate's GPU-seconds cap. Returns the raw
    manifest (validate() it)."""
    root = Path(root).resolve()
    ed, co = task_files(root, task)
    mid = module or stratum_module(root, task)
    if not mid:
        raise ManifestError(f"{task}: no module (name one, or give the stratum a lab field)")
    rec = registry_record(root, mid)
    if texts is not None and set(texts) != set(ed):
        raise ManifestError("a continuation stages every editable file of the task inline, "
                            "and nothing else")
    files = [{"dst": AGENT_BRIEF, "role": "task", "text": brief,
              "sha256": sha256_bytes(brief.encode("utf-8"))}]
    seen = {AGENT_BRIEF}

    def add(src, role):
        if src in seen:
            return
        seen.add(src)
        data = read_source(root, Entry(src, src, role, "0" * 64))
        files.append({"src": src, "dst": src, "role": role, "sha256": sha256_bytes(data)})

    for r in ed:
        if texts is not None:
            seen.add(r)
            files.append({"dst": r, "role": "editable", "text": texts[r],
                          "sha256": sha256_bytes(texts[r].encode("utf-8"))})
        else:
            add(r, "editable")
    for r in co:
        add(r, "task")
    langs = {lang_pool(r) for r in ed} - {None}
    for src, role in readonly_inputs(root, rec, langs):
        if src != "verus/Cargo.toml":
            add(src, role)
    if "verus" in langs:
        seen.add("verus/Cargo.toml")
        files.append({"dst": "verus/Cargo.toml", "role": "project",
                      "text": verus_workspace(root, rec),
                      "sha256": sha256_bytes(verus_workspace(root, rec).encode("utf-8"))})
    lock = read_images_lock(root)
    image = next((k for k in lock if k.startswith("dvl-agent@")), "dvl-agent@sha256:" + "0" * 64)
    raw = {"schema": SCHEMA, "run_id": run_id or f"a{os.getpid()}-{secrets.token_hex(4)}",
           "module": rec["id"], "kind": "agent", "image": image, "network": "ollama",
           "limits": {"wall_clock_s": int(wall_s)}, "file": files, "return": list(ed),
           "agent": {"cli": "opencode", "model": model, "turns": int(turns)}}
    if gpu_s is not None:
        raw["agent"]["gpu_s"] = max(1, min(36000, int(gpu_s)))
    if mem_gb is not None:
        raw["limits"]["mem_gb"] = min(float(mem_gb), memory_bound_gb("agent", run_pools(files)))
    return raw


# --- the agent CLI: opencode in the container (DV4-PLAN §3.5, step 3a) --------------------------
#
# As probed at step 3a on opencode 1.18.25 in dvl-agent, --network none, through
# the relay and a per-run gate (Solutions/plans/DV4-author-notes.md §9):
#   - the provider package @ai-sdk/openai-compatible is bundled: an empty cache
#     and no network suffice, so nothing is fetched or pre-seeded;
#   - one session costs one title request unless agent.title is disabled, and
#     one request per step; with `steps` = N the N-th request carries opencode's
#     "maximum steps reached" text and the run ends there, so with the title
#     agent disabled and automatic compaction off, calls == steps <= turns;
#   - the OpenAI-compatible endpoint ignores num_ctx and top_k (Ollama then
#     uses its unit's context, OLLAMA_CONTEXT_LENGTH); the gate pins the rest
#     and flags a prompt past the pinned num_ctx as ctx-saturated.

OPENCODE = "/opt/dvl/agent/opencode"          # the pinned binary in dvl-agent (sandbox/images/)
AGENT_HOME = "/home/agent"
OPENCODE_PROVIDER = "fvhgate"
OPENCODE_RELAY_URL = "http://127.0.0.1:11434/v1"   # the in-container relay (Route B)
OPENCODE_TOOLS = ("bash", "edit", "glob", "grep", "read", "write")
# opencode's own external_directory allow rules (its tool-output directory under
# HOME and its tmp directory); every other external path is denied
OPENCODE_EXTERNAL_OK = (f"{AGENT_HOME}/.local/share/opencode/tool-output/*", "/tmp/opencode/*")
OPENCODE_DISABLE = tuple(f"OPENCODE_DISABLE_{s}" for s in (
    "CLAUDE_CODE", "EXTERNAL_SKILLS", "PROJECT_CONFIG", "AUTOUPDATE", "MODELS_FETCH",
    "LSP_DOWNLOAD", "SHARE", "DEFAULT_PLUGINS"))
AGENT_KILL_AFTER_S = 15
APPARATUS_FILE = "sandbox/apparatus.toml"     # fvh.apparatus.DEFAULT (FVH_APPARATUS overrides)
GPU_LOCK = "dvl-gpu-calendar.lock"            # DV4-PLAN §10: one Qwen batch at a time

AGENT_MESSAGE = (
    "Work in /work, a copy of part of a course repository. Your task is in /work/{brief}: "
    "read it first and carry it out. Edit only the files it allows. Run the course tools it "
    "names from /work exactly as it writes them (for example `scripts/vcheck <file>`); they "
    "work in this copy. When every acceptance line holds, or when you cannot make further "
    "progress, stop and reply with a short summary: what you changed, and what each check "
    "printed.")


def agent_brief(manifest):
    """The staged instructions the agent is pointed at: the contract text, else an
    agent-mode brief (AGENT_BRIEF, build_agent's), else a task."""
    for role in ("contract", "task"):
        for e in manifest.files:
            if e.role == role and (role == "contract" or e.dst == AGENT_BRIEF):
                return e.dst
    for e in manifest.files:
        if e.role == "task":
            return e.dst
    raise SandboxError("an agent run stages its instructions (a contract or a task file)")


def apparatus_pins(root=REPO_ROOT):
    """The apparatus file's [model_server] table (the model digests, the unit's
    settings and the request options), read-only. SandboxError when the file
    or the table is missing: no model run starts without its pins."""
    p = Path(os.environ.get("FVH_APPARATUS") or Path(root) / APPARATUS_FILE)
    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SandboxError(f"no apparatus file at {p}: no model run starts without its pins") from None
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise SandboxError(f"{p}: unreadable apparatus file ({type(e).__name__})") from None
    ms = data.get("model_server")
    if data.get("schema") != 1 or not isinstance(ms, dict) or not isinstance(ms.get("models"), dict) \
            or not isinstance(ms.get("options"), dict):
        raise SandboxError(f"{p}: schema 1 with a [model_server] table (models, options) is needed")
    return ms


def agent_model(root=REPO_ROOT):
    """The model tag of an fvh agent-mode session: the apparatus file's
    [backend.qwen] model, which must have its digest in [model_server] models
    (as contract_local.sh's pinned tags). SandboxError otherwise."""
    p = Path(os.environ.get("FVH_APPARATUS") or Path(root) / APPARATUS_FILE)
    ms = apparatus_pins(root)
    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise SandboxError(f"{p}: unreadable apparatus file ({type(e).__name__})") from None
    tag = ((data.get("backend") or {}).get("qwen") or {}).get("model")
    if not isinstance(tag, str) or tag not in ms["models"]:
        raise SandboxError(f"{p}: [backend.qwen]'s model has no digest in [model_server] models")
    return tag


def agent_gate_config(manifest, root=REPO_ROOT):
    """The gate's config for a model run (DV4-PLAN §5.6.3): the pinned tag and its
    digest, the pinned request options, and the caps: calls = the run's turns
    (opencode's step limit, so the two agree), GPU-seconds from [agent] gpu_s;
    the model leaves the GPU when the gate stops (keep_alive 0, §10)."""
    ms = apparatus_pins(root)
    tag = manifest.agent["model"]
    digest = ms["models"].get(tag)
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise SandboxError(f"the model {tag} has no digest pin in the apparatus file's "
                           "[model_server] models")
    caps = {"calls": int(manifest.agent["turns"])}
    if manifest.agent.get("gpu_s") is not None:
        caps["gpu_s"] = float(manifest.agent["gpu_s"])
    return {"model": tag, "digest": digest, "options": dict(ms["options"]), "caps": caps,
            "margin": int(ms.get("margin", 512)), "unload_on_stop": True}


def opencode_config(manifest, options):
    """The agent's opencode config (DV4-PLAN §3.5): the agent tools only (read,
    glob, grep, edit, write, bash), every other tool and the web denied, every
    external directory denied, no MCP, no title request, no automatic
    compaction, the step limit at the run's turns, and one provider: the relay."""
    tag = manifest.agent["model"]
    num_ctx = int(options.get("num_ctx", 32768))
    num_predict = int(options.get("num_predict", 8192))
    perm = {"*": "deny", "read": "allow", "glob": "allow", "grep": "allow", "edit": "allow",
            "bash": "allow", "external_directory": "deny", "webfetch": "deny", "task": "deny",
            "skill": "deny", "todowrite": "deny", "question": "deny", "doom_loop": "deny"}
    return {"$schema": "https://opencode.ai/config.json", "autoupdate": False, "share": "disabled",
            "mcp": {}, "model": f"{OPENCODE_PROVIDER}/{tag}", "permission": perm,
            "tools": {"*": False, **{t: True for t in OPENCODE_TOOLS}},
            "compaction": {"auto": False},
            "agent": {"build": {"steps": int(manifest.agent["turns"])}, "title": {"disable": True}},
            "provider": {OPENCODE_PROVIDER: {
                "npm": "@ai-sdk/openai-compatible", "name": "the run's model gate (relay)",
                "options": {"baseURL": OPENCODE_RELAY_URL},
                "models": {tag: {"name": tag, "limit": {"context": num_ctx, "output": num_predict}}}}}}


def opencode_env(manifest):
    """docker exec --env pairs of the agent process: the image's environment, the
    container mode (container-agent) and opencode's isolation switches (Δ64)."""
    h = AGENT_HOME
    pairs = [f"HOME={h}", f"XDG_CONFIG_HOME={h}/.config", f"XDG_DATA_HOME={h}/.local/share",
             f"XDG_CACHE_HOME={h}/.cache", f"XDG_STATE_HOME={h}/.local/state", "TERM=dumb",
             f"OPENCODE_CONFIG={h}/opencode.json", *(f"{k}=1" for k in OPENCODE_DISABLE)]
    out = list(exec_env(manifest))
    for p in pairs:
        out += ["--env", p]
    return out


def config_stream(config):
    """The tar stream of the agent's config into its home directory."""
    data = (json.dumps(config, indent=1, sort_keys=True) + "\n").encode()
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tf:
        ti = tarfile.TarInfo("opencode.json")
        ti.size, ti.mode, ti.uid, ti.gid, ti.mtime = len(data), 0o600, 1000, 1000, 0
        ti.uname = ti.gname = "agent"
        tf.addfile(ti, io.BytesIO(data))
    return buf.getvalue()


def agent_lines(manifest, timeout_s):
    """The docker exec lines of the agent: its config in, the per-run gate's two
    debug views (no model call), and the run, under the in-container timeout."""
    name = container_name(manifest)
    env = opencode_env(manifest)
    tag = manifest.agent["model"]
    return [
        ["docker", "exec", "--interactive", name, "/usr/bin/tar", "--extract", "--no-same-owner",
         "--no-same-permissions", "--directory", AGENT_HOME, "--file", "-"],
        ["docker", "exec", *env, "--workdir", WORK, name, OPENCODE, "debug", "config", "--pure"],
        ["docker", "exec", *env, "--workdir", WORK, name, OPENCODE, "debug", "agent", "build",
         "--pure"],
        ["docker", "exec", *env, "--workdir", WORK, name, "/usr/bin/timeout",
         f"--kill-after={AGENT_KILL_AFTER_S}", str(int(timeout_s)), OPENCODE, "run", "--pure",
         "--format", "json", "-m", f"{OPENCODE_PROVIDER}/{tag}",
         AGENT_MESSAGE.format(brief=agent_brief(manifest))],
    ]


def _urls(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "baseURL" and isinstance(v, str):
                yield v
            else:
                yield from _urls(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _urls(v)


def opencode_precheck(config_out, agent_out, manifest):
    """The per-run gate on opencode's two debug views (DV4-PLAN §3.5): problems,
    empty when it passes. The resolved config names the relay as its only
    provider URL, the pinned model, no MCP server, the title agent disabled and
    automatic compaction off; the build agent has exactly the agent tools on,
    the step limit at the run's turns, and no external_directory allow rule but
    opencode's own two."""
    out = []
    try:
        conf = json.loads(config_out)
        agent = json.loads(agent_out)
        assert isinstance(conf, dict) and isinstance(agent, dict)
    except (ValueError, AssertionError):
        return ["a debug view is not a JSON object"]
    urls = sorted(set(_urls(conf)))
    if urls != [OPENCODE_RELAY_URL]:
        out.append(f"provider URLs {urls}, not only the relay {OPENCODE_RELAY_URL}")
    if conf.get("model") != f"{OPENCODE_PROVIDER}/{manifest.agent['model']}":
        out.append(f"model {conf.get('model')!r}, not the pinned {manifest.agent['model']}")
    if conf.get("mcp") not in ({}, None):
        out.append("an MCP server is configured")
    if ((conf.get("agent") or {}).get("title") or {}).get("disable") is not True:
        out.append("the title agent is not disabled (one extra request per session)")
    if (conf.get("compaction") or {}).get("auto") is not False:
        out.append("automatic compaction is not off (extra requests beyond the step limit)")
    tools = agent.get("tools")
    if not isinstance(tools, dict) or not tools:
        out.append("debug agent build lists no tools table")
    else:
        on = sorted(k for k, v in tools.items() if v is not False)
        if on != sorted(OPENCODE_TOOLS):
            out.append(f"tools on: {on}, not exactly {sorted(OPENCODE_TOOLS)}")
    if agent.get("steps") != manifest.agent["turns"]:
        out.append(f"step limit {agent.get('steps')!r}, not the run's {manifest.agent['turns']} turns")
    for rule in agent.get("permission") or []:
        if isinstance(rule, dict) and rule.get("permission") == "external_directory" \
                and rule.get("action") == "allow" and rule.get("pattern") not in OPENCODE_EXTERNAL_OK:
            out.append(f"an external_directory allow rule: {rule.get('pattern')}")
    return out


def transcript_summary(stdout):
    """(events, steps, tool calls by tool, finish reasons, text tail) of a
    `run --format json` stream."""
    events, steps, tools, reasons, texts = 0, 0, {}, [], []
    for line in stdout.decode("utf-8", "replace").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if not isinstance(e, dict):
            continue
        events += 1
        part = e.get("part") if isinstance(e.get("part"), dict) else {}
        if e.get("type") == "step_start":
            steps += 1
        elif e.get("type") == "tool_use":
            t = str(part.get("tool"))
            tools[t] = tools.get(t, 0) + 1
        elif e.get("type") == "step_finish":
            reasons.append(part.get("reason"))
        elif e.get("type") == "text" and isinstance(part.get("text"), str):
            texts.append(part["text"])
    return {"events": events, "steps": steps, "tool_calls": tools, "finish": reasons,
            "last_text": ("".join(texts[-1:]))[-2000:]}


def calendar_held_by(fd):
    """Whether the open file `fd` holds the GPU calendar lock: it is the lock file
    (the same inode as $XDG_RUNTIME_DIR/<GPU_LOCK>) and an exclusive flock on it
    succeeds at once, which, for a lock taken through another open file, it could
    not (an fvh agent-mode batch passes the fd it locked to the live run of each
    session, `mksandbox-run --agent-session --calendar-fd N`, DV5d)."""
    import fcntl
    base = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    try:
        st, want = os.fstat(fd), os.stat(os.path.join(base, GPU_LOCK))
        if (st.st_dev, st.st_ino) != (want.st_dev, want.st_ino):
            return False
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, ValueError):
        return False
    return True


class _GpuCalendar:
    """The per-user GPU calendar lock (DV4-PLAN §10): every Qwen batch holds it;
    another holder defers the run (exit 3), never queues it silently."""

    def __init__(self):
        self.fd = None

    def __enter__(self):
        import fcntl
        base = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
        fd = os.open(os.path.join(base, GPU_LOCK), os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd)
            raise Deferred("another Qwen batch holds the GPU calendar lock "
                           f"($XDG_RUNTIME_DIR/{GPU_LOCK}); the run is deferred") from None
        self.fd = fd
        return self

    def __exit__(self, *exc):
        if self.fd is not None:
            os.close(self.fd)
        return False


# --- the live run (step 2b) -----------------------------------------------------------------------

RESERVE_GB = 15                 # CLAUDE.md §Resources: the free-memory reserve
DOCKER_TIMEOUT_S = 120


class Deferred(Exception):
    """The host cannot start the run now (memory); nothing was started (exit 3)."""


def mem_available_gb():
    try:
        with open("/proc/meminfo", encoding="ascii") as fh:
            for line in fh:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) / 1048576
    except (OSError, ValueError, IndexError):
        pass
    return None


class _SandboxSlot:
    """One of FVH_SANDBOX_JOBS (default 1) sandbox containers at a time across
    this user's processes (DV4-PLAN §5.10): an flock under the runs directory."""

    def __init__(self):
        n = os.environ.get("FVH_SANDBOX_JOBS", "1")
        self.n = int(n) if n.isdigit() and int(n) >= 1 else 1
        self.fd = None

    def __enter__(self):
        import fcntl
        base = runs_base()
        base.mkdir(mode=0o700, parents=True, exist_ok=True)
        while True:
            for k in range(self.n):
                fd = os.open(base / f".slot-{k}.lock", os.O_RDWR | os.O_CREAT, 0o600)
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    os.close(fd)
                    continue
                self.fd = fd
                return self
            time.sleep(1.0)

    def __exit__(self, *exc):
        if self.fd is not None:
            os.close(self.fd)
        return False


_WATCH_SH = r"""
name="$1"; gate="$2"; rundir="$3"
IFS= read -r line
docker rm --force "$name" >/dev/null 2>&1
if [ "$gate" != "-" ]; then kill "$gate" >/dev/null 2>&1; fi
if [ -z "$line" ] && [ "$rundir" != "-" ] && [ -d "$rundir" ]; then
  chmod -R u+rwx "$rundir" >/dev/null 2>&1; rm -rf "$rundir"
fi
exit 0
"""


def start_watcher(name, gate_pid=None, run_path=None):
    """A detached watcher (DV4-PLAN §5.10): when this process writes `done`, the
    watcher removes the container (a no-op by then) and stops the run's gate;
    when this process dies first (the pipe closes with nothing written), it
    also removes the run directory. Returns the pipe's write end."""
    r, w = os.pipe()
    try:
        subprocess.run(["setsid", "-f", "sh", "-c", _WATCH_SH, "dvl-watch", name,
                        str(gate_pid) if gate_pid else "-", str(run_path) if run_path else "-"],
                       stdin=r, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       close_fds=True, check=True, timeout=30)
    finally:
        os.close(r)
    return w


def stop_watcher(w):
    try:
        os.write(w, b"done\n")
    except OSError:
        pass
    os.close(w)


def host_targets(limit=256):
    """[(address, port)] for control C6: every TCP port the host listens on, at
    every non-loopback address it holds (IPv4 and IPv6), read from `ss -ltn`
    and `ip -o addr` at run start."""
    ports = set()
    out = _cmd_out(["ss", "-ltnH"]) or ""
    for line in out.splitlines():
        cols = line.split()
        if len(cols) >= 4:
            port = cols[3].rsplit(":", 1)[-1]
            if port.isdigit():
                ports.add(int(port))
    addrs = []
    for line in (_cmd_out(["ip", "-o", "addr", "show"]) or "").splitlines():
        cols = line.split()
        if len(cols) >= 4 and cols[2] in ("inet", "inet6"):
            a = cols[3].split("/")[0]
            if a in ("127.0.0.1", "::1") or a.startswith("fe80:"):
                continue
            addrs.append(a)
    pairs = [(a, p) for a in sorted(set(addrs)) for p in sorted(ports)]
    return pairs[:limit], {"ports": sorted(ports), "addresses": sorted(set(addrs)),
                           "pairs": len(pairs), "tried": min(len(pairs), limit)}


def controls_request(manifest, targets):
    return {"network": manifest.network,
            "readonly": sorted(e.dst for e in manifest.files if e.role != "editable"),
            "editable_dirs": manifest.editable_dirs(),
            "host_targets": [list(t) for t in targets],
            "public": [["1.1.1.1", 443], ["2606:4700:4700::1111", 443]],
            "public_name": "example.com", "relay_port": 11434, "relay_path": "/api/version",
            "timeout_s": 1}


def _docker(argv, *, input=None, timeout=DOCKER_TIMEOUT_S):
    return subprocess.run(argv, input=input, capture_output=True, timeout=timeout)


def _clip(b, cap=4 << 20):
    t = b.decode("utf-8", "replace")
    return t if len(t) <= cap else t[:cap] + "\n[clipped]\n"


GATE_UPSTREAM = "http://127.0.0.1:11434"     # Ollama listens on loopback only (Δ146)


def start_gate(manifest, run, cfg=None, upstream=None, out=None):
    """The Ollama gate on the run's socket (Route B). Without a config no
    inference is forwarded (calls cap 0); an opencode run passes
    agent_gate_config's pins and caps (step 3a). A probe may pass its own
    config and a loopback upstream (the doors' fake server). `out`: where the
    gate writes its log and its running counts (default: the run's out/; an
    fvh agent-mode attempt passes its own run directory, so that a runner
    killed outright leaves the counts `fvh resume` settles the attempt by)."""
    cfg = dict(cfg) if cfg else {"model": manifest.agent["model"], "options": {},
                                 "caps": {"calls": 0}, "margin": 512}
    upstream = upstream or GATE_UPSTREAM
    if not re.fullmatch(r"http://127\.0\.0\.1:\d{1,5}", upstream):
        raise SandboxError(f"the gate's upstream must be a loopback http address, not {upstream!r}")
    out = Path(out) if out is not None else run.out
    out.mkdir(parents=True, exist_ok=True)
    (run.state / "gate.json").write_text(json.dumps(cfg), encoding="utf-8")
    ready = run.state / "gate.ready"
    p = subprocess.Popen([sys.executable, "-B", str(REPO_ROOT / "sandbox" / "hostside" / "ollama_gate.py"),
                          "--socket", str(run.state / "ollama.sock"), "--config",
                          str(run.state / "gate.json"), "--log", str(out / "gate.log"),
                          "--counts", str(out / "gate-counts.json"), "--ready", str(ready),
                          "--upstream", upstream],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=open(run.out / "gate.stderr", "wb"), start_new_session=True)
    for _ in range(100):
        if ready.is_file():
            return p
        if p.poll() is not None:
            break
        time.sleep(0.1)
    p.kill()
    try:
        why = (run.out / "gate.stderr").read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        why = ""
    raise SandboxError("the Ollama gate did not start" + (f": {why.splitlines()[-1]}" if why
                                                            else " (see gate.stderr)"))


def live_run(manifest, run, *, probe=False, log=None, gate_cfg=None, gate_upstream=None,
             root=REPO_ROOT, seeds=None, gate_dir=None, calendar_held=False, exact_secrets=()):
    """One live run (DV4-PLAN §5.5-§5.10). Returns (exit code, record dict).
    Exit 0: completed (whatever each command's verdict, and however the agent
    ended); 1: a step failed (the controls, a stream, the agent's config or its
    per-run gate, the container ended early, a memory kill); 124: the run's
    wall clock during a command; Deferred (exit 3) when memory is short or
    another Qwen batch holds the GPU calendar lock.

    An opencode agent run (step 3a) takes the GPU calendar lock, starts the
    gate with the apparatus file's pins and caps (agent_gate_config), and after
    the controls and the commands writes the agent's config, checks its two
    debug views (opencode_precheck) and runs it under the in-container timeout
    with what is left of the wall clock; the agent's end (its exit, the wall
    clock) is recorded and the return stream follows either way. The event
    stream is kept as rec["_transcript"] after the secret scan.

    fvh's agent-mode batches (fvh.batch, fvh.backends.agent; DV5d) add three
    keywords, none of them a probe's: `seeds`, the run's per-request seeds
    (the gate gives the n-th admitted request the n-th seed and answers 429
    past the list, so a run needs at least its turns' worth; recorded in
    rec["seeds"]); `gate_dir`, where the gate writes gate.log and
    gate-counts.json (the caller's run directory: the files stay there, for
    the caller's own secret scan, and rec["gate"] names them instead of
    holding their text); `calendar_held`, the caller holds the GPU calendar
    lock for its whole batch (the lock is per open file, so a second take in
    the same process would defer the run).

    The secret scan's fallback form (DV4-PLAN §5.7; DV5d): `exact_secrets`,
    the exact credential values the run was given (each a string of at least
    16 characters, held in memory only, never recorded), joins the credential
    formats in every scan of what comes back: the returned files, the agent's
    event stream, gate.log and each command's output. A command output with a
    hit keeps neither stream (its entry's `withheld` record instead, the name
    `command-<n>.log`); rec["secret_scan"] lists every withheld record and
    `exact_values`, how many values were matched against (never which)."""
    say = log or (lambda m: None)
    if isinstance(exact_secrets, (str, bytes)) or not all(
            isinstance(x, str) and len(x) >= 16 for x in exact_secrets):
        raise SandboxError("exact_secrets is a list of credential values, each a string of at "
                           "least 16 characters (DV4-PLAN §5.7's fallback form)")
    exact = tuple(exact_secrets)
    need = float(manifest.limits["mem_gb"]) + RESERVE_GB
    have = mem_available_gb()
    if have is None or have < need:
        raise Deferred(f"{'unknown' if have is None else f'{have:.1f}'} GB available, {need:g} GB "
                       f"needed (the container's --memory plus the {RESERVE_GB} GB reserve, "
                       "CLAUDE.md §Resources); the run is deferred")
    cli = (manifest.agent or {}).get("cli") if manifest.kind == "agent" else None
    if cli == "claude":
        raise SandboxError("Claude Code in a container is DV4 step 4c's (harness-executed runs "
                           "until then)")
    if not probe and cli == "none":
        raise SandboxError("a probe agent container (cli \"none\") runs only under --probe")
    if not probe and any(c[0] == CONTROLS for c in manifest.commands):
        raise SandboxError("a door of the controls runs only under --probe")
    if not probe and (gate_cfg or gate_upstream):
        raise SandboxError("the gate's config and upstream are a probe's (--probe) only")
    if manifest.network == "anthropic":
        raise SandboxError("the egress proxy (network \"anthropic\") is DV4 step 4c")
    if seeds is not None:
        if cli != "opencode":
            raise SandboxError("per-request seeds are an agent run's (cli \"opencode\")")
        if not isinstance(seeds, (list, tuple)) or not all(
                isinstance(x, int) and not isinstance(x, bool) and x >= 0 for x in seeds):
            raise SandboxError("seeds is a list of integers >= 0")
        if len(seeds) < int(manifest.agent["turns"]):
            raise SandboxError(f"{len(seeds)} seed(s) for {manifest.agent['turns']} turns: the gate "
                               "answers 429 past its seeds, so a run needs one seed per turn")
    rec = {"schema": 1, "run_id": manifest.run_id, "kind": manifest.kind, "probe": probe,
           "image": manifest.image, "container": container_name(manifest),
           "network": manifest.network, "memory_gb": manifest.limits["mem_gb"],
           "root": WORK, "scratch": CONTAINER_SCRATCH, "ended_by": None, "commands": []}
    name = container_name(manifest)
    started = time.monotonic()
    deadline = started + int(manifest.limits["wall_clock_s"])

    def left():
        return max(1.0, deadline - time.monotonic())

    if cli == "opencode" and gate_cfg is None:
        gate_cfg = agent_gate_config(manifest, root)
    if seeds is not None:
        gate_cfg = dict(gate_cfg, seeds=[int(x) for x in seeds])
        rec["seeds"] = [int(x) for x in seeds]
    gate_out = Path(gate_dir) if gate_dir is not None else run.out
    log_withheld = []                    # command outputs withheld by the secret scan
    import contextlib
    with contextlib.ExitStack() as hold:
        if cli == "opencode" and not calendar_held:
            hold.enter_context(_GpuCalendar())
        hold.enter_context(_SandboxSlot())
        rec["started"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        gate = start_gate(manifest, run, gate_cfg, gate_upstream, out=gate_out) \
            if manifest.network == "ollama" else None
        watcher = start_watcher(name, gate.pid if gate else None, run.path)
        lines = docker_argv(manifest, run.path, owner_label())
        try:
            p = _docker(lines[0])
            if p.returncode != 0:
                rec["ended_by"] = "start-failed"
                rec["detail"] = _clip(p.stderr)[-2000:]
                return 1, rec
            rec["container_id"] = p.stdout.decode().strip()[:64]
            say(f"started {name} ({manifest.image.split('@')[0]}, --memory {manifest.limits['mem_gb']:g}g)")
            p = _docker(lines[1], input=input_stream(manifest, run), timeout=left())
            if p.returncode != 0:
                rec["ended_by"] = "stream-in-failed"
                rec["detail"] = _clip(p.stderr)[-2000:]
                return 1, rec
            targets, tinfo = host_targets() if manifest.network != "none" else ([], None)
            rec["host_targets"] = tinfo
            p = _docker(lines[2], input=json.dumps(controls_request(manifest, targets)).encode(),
                        timeout=min(left(), 900))
            try:
                rec["controls"] = json.loads(p.stdout or b"{}")
            except ValueError:
                rec["controls"] = {"ok": False, "raw": _clip(p.stdout)[:2000]}
            if p.returncode != 0 or not rec["controls"].get("ok"):
                rec["ended_by"] = "controls-failed"
                say("containment controls FAILED: " + "; ".join(
                    f"{c['id']} {c['detail']}" for c in rec["controls"].get("controls", []) if not c["ok"]))
                return 1, rec
            say("containment controls: " + ", ".join(c["id"] for c in rec["controls"]["controls"]) + " OK")
            for c, line in zip(manifest.commands, lines[3:3 + len(manifest.commands)]):
                oom_before = bool((_inspect(name) or {}).get("OOMKilled"))
                t0 = time.monotonic()
                try:
                    p = _docker(line, timeout=left())
                    rc, out, err = p.returncode, p.stdout, p.stderr
                    timed_out = False
                except subprocess.TimeoutExpired as e:
                    rc, out, err, timed_out = None, e.stdout or b"", e.stderr or b"", True
                entry = {"argv": list(c), "exit_code": rc, "wall_s": round(time.monotonic() - t0, 2),
                         "stdout": _clip(out), "stderr": _clip(err), "killed": None}
                hits = secret_scan(out, exact) + secret_scan(err, exact)
                if hits:                     # a log is scanned like a returned file (§5.7)
                    entry["stdout"] = entry["stderr"] = ""
                    entry["withheld"] = withheld_record(
                        f"command-{len(rec['commands']) + 1}.log", out + err, hits)
                    log_withheld.append(entry["withheld"])
                    rec["secret_scan"] = {"withheld": list(log_withheld), "scanned": 0,
                                          "exact_values": len(exact)}
                rec["commands"].append(entry)
                if timed_out:
                    entry["killed"] = "wall-clock"
                    rec["ended_by"] = "wall-clock"
                    _docker(["docker", "kill", name], timeout=60)
                    return 124, rec
                st = _inspect(name)
                if st and st.get("OOMKilled") and not oom_before:
                    entry["oom_event"] = True       # the container's OOM killer took a process
                    if rc != 0:
                        entry["killed"] = "memory"
                if st and not st.get("Running"):
                    entry["killed"] = "memory" if st.get("OOMKilled") else None
                    rec["ended_by"] = "killed(memory)" if st.get("OOMKilled") else "container-exited"
                    rec["state"] = {k: st.get(k) for k in ("OOMKilled", "ExitCode", "Error")}
                    return 1, rec
                say(f"command {' '.join(c)}: exit {rc} ({entry['wall_s']} s)")
            if cli == "opencode":
                code = _run_agent(manifest, rec, lines[3 + len(manifest.commands):-2], gate_cfg,
                                  left, say, exact)
                if code:
                    return code, rec
            if manifest.kind == "agent" and manifest.returns:
                staged = {e.dst: (run.inp / e.dst).read_bytes() for e in manifest.files}
                p = subprocess.Popen(lines[-2], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                try:
                    res = parse_return(p.stdout, manifest, staged)
                finally:
                    p.stdout.close()
                    rc = p.wait(timeout=left())
                withheld, kept = [], {}
                for fname, data in sorted(res.returned.items()):
                    hits = secret_scan(data, exact)
                    if hits:
                        withheld.append(withheld_record(fname, data, hits))
                    else:
                        kept[fname] = data
                if withheld:
                    # the patch never carries a withheld file's content (§5.7)
                    src_of = {e.dst: (e.src or e.dst) for e in manifest.files}
                    res = ReturnResult(returned=kept, unchanged=res.unchanged, deleted=res.deleted,
                                       rejected=res.rejected)
                    res.diff = unified_patch(res, staged, src_of)
                rec["secret_scan"] = {"withheld": log_withheld + withheld,
                                      "scanned": len(kept) + len(withheld),
                                      "exact_values": len(exact)}
                rec["return"] = res.summary()
                rec["return"]["tar_exit"] = rc
                rec["_returned"] = res
            rec["ended_by"] = "done"
            return 0, rec
        finally:
            st = _inspect(name)
            rec["oom_killed"] = bool(st and st.get("OOMKilled"))
            _docker(["docker", "rm", "--force", name], timeout=120)
            rec["removed"] = _inspect(name) is None
            if gate is not None:
                gate.terminate()
                try:
                    gate.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    gate.kill()
                for f in ("gate.log", "gate-counts.json"):
                    if gate_dir is not None:
                        # the files stay in the caller's directory (its own scan)
                        if (gate_out / f).is_file():
                            rec.setdefault("gate", {"dir": "the caller's", "files": []})[
                                "files"].append(f)
                    elif (run.out / f).is_file():
                        text = (run.out / f).read_text(encoding="utf-8")
                        hits = secret_scan(text.encode(), exact) if f == "gate.log" else []
                        rec.setdefault("gate", {})[f] = text if not hits else json.dumps(
                            withheld_record(f, text.encode(), hits))
            stop_watcher(watcher)
            rec["wall_s"] = round(time.monotonic() - started, 2)


def _run_agent(manifest, rec, lines, gate_cfg, left, say, exact=()):
    """The agent step of an opencode run (live_run's docstring); 0, or the
    run's exit code when the step failed before the agent could start (1)."""
    name = container_name(manifest)
    ag = rec["agent"] = {"cli": "opencode", "model": manifest.agent["model"],
                         "turns": manifest.agent["turns"], "binary": OPENCODE}
    conf = opencode_config(manifest, gate_cfg.get("options") or {})
    ag["config_sha256"] = sha256_bytes((json.dumps(conf, indent=1, sort_keys=True) + "\n").encode())
    p = _docker(lines[0], input=config_stream(conf), timeout=min(left(), 120))
    if p.returncode != 0:
        rec["ended_by"] = "agent-config-failed"
        rec["detail"] = _clip(p.stderr)[-2000:]
        return 1
    views = []
    for line in lines[1:3]:
        try:
            q = _docker(line, timeout=min(left(), 180))
            views.append((q.returncode, q.stdout, q.stderr))
        except subprocess.TimeoutExpired:
            views.append((None, b"", b"timed out"))
    if any(rc != 0 for rc, _, _ in views):
        problems = [f"a debug view failed (exit {rc}): {_clip(err)[-300:]}"
                    for rc, _, err in views if rc != 0]
    else:
        problems = opencode_precheck(views[0][1], views[1][1], manifest)
    ag["precheck"] = {"ok": not problems, "problems": problems}
    if problems:
        rec["ended_by"] = "agent-precheck-failed"
        say("the agent's per-run gate FAILED: " + "; ".join(problems))
        return 1
    say(f"the agent's per-run gate: tools {', '.join(OPENCODE_TOOLS)} only, the relay the only "
        f"provider, {manifest.agent['turns']} steps")
    # what is left of the wall clock, less a reserve for the return stream and the removal
    budget_s = max(30, int(left()) - 60)
    run_line = list(lines[3])
    i = run_line.index("/usr/bin/timeout")
    run_line[i + 2] = str(budget_s)
    t0 = time.monotonic()
    try:
        p = _docker(run_line, timeout=budget_s + AGENT_KILL_AFTER_S + 30)
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        rc, out, err = None, e.stdout or b"", e.stderr or b""
        _docker(["docker", "exec", name, "/usr/bin/pkill", "-KILL", "-f", OPENCODE], timeout=60)
    hits = secret_scan(out, exact) + secret_scan(err, exact)
    summary = transcript_summary(out)
    ag.update(exit_code=rc, wall_s=round(time.monotonic() - t0, 2), budget_s=budget_s,
              stderr="" if hits else _clip(err)[-4000:], summary=summary)
    ag["ended"] = ("wall-clock" if rc in (None, 124, 137) else "exit" if rc == 0 else "error")
    if hits:
        # nothing of a stream that holds a credential-shaped string is kept (§5.7)
        summary["last_text"] = ""
        ag["transcript_withheld"] = withheld_record("transcript.jsonl", out + err, hits)
    else:
        rec["_transcript"] = out
    st = _inspect(name)
    if st and not st.get("Running"):
        rec["ended_by"] = "killed(memory)" if st.get("OOMKilled") else "container-exited"
        rec["state"] = {k: st.get(k) for k in ("OOMKilled", "ExitCode", "Error")}
        return 1
    say(f"agent: exit {rc} after {ag['wall_s']} s ({ag['summary']['steps']} steps, "
        f"{sum(ag['summary']['tool_calls'].values())} tool calls)")
    return 0


def _inspect(name):
    try:
        p = _docker(["docker", "inspect", "--format", "{{json .State}}", name], timeout=60)
    except subprocess.TimeoutExpired:
        return None
    if p.returncode != 0:
        return None
    try:
        return json.loads(p.stdout)
    except ValueError:
        return None


def write_live_records(dest, rec, name="run.json"):
    """run.json (the run's facts, the controls and every command's output), and
    for an agent run patch.diff and returned/ after the secret scan, and the
    agent's event stream as transcript.jsonl.gz. `name`: the record's file
    name (contract_local.sh writes it as sandbox.json beside fvh's run.json)."""
    import gzip
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    tr = rec.pop("_transcript", None)
    if tr is not None:
        (dest / "transcript.jsonl.gz").write_bytes(gzip.compress(tr, mtime=0))
    res = rec.pop("_returned", None)
    if res is not None:
        # live_run has run the secret scan: res.returned holds only the kept files
        for fname, data in res.returned.items():
            p = dest / "returned" / fname
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        (dest / "patch.diff").write_text(res.diff, encoding="utf-8")
    (dest / name).write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return dest / name


def reap(log=None):
    """Remove every container labelled dvl.run whose dvl.owner process is gone
    (DV4-PLAN §5.10). Returns the names removed."""
    p = _docker(["docker", "ps", "--all", "--filter", "label=dvl.run", "--format",
                 '{{.Names}}\t{{.Label "dvl.owner"}}'])
    gone = []
    for line in p.stdout.decode().splitlines():
        name, _, owner = line.partition("\t")
        pid, _, start = owner.partition(":")
        alive = pid.isdigit() and _proc_start(int(pid)) == start and start != "0"
        if not alive:
            _docker(["docker", "rm", "--force", name])
            gone.append(name)
            if log:
                log(f"reaped {name} (owner {owner or 'unknown'} is gone)")
    return gone


# --- class drift (the static job's check, §9) --------------------------------------------------------

def class_drift(root=REPO_ROOT, hook=None):
    """Problems (strings) where the guard or the checker treats a path as
    reference material that this library would let into a sandbox. The
    guard's reference directories come from RX_SPOIL_DIR in the hook's source,
    and each is also replayed through the hook itself (study mode, a Read of a
    sample path under it must be blocked by rule 1 or 1c); the checker's
    names come from REFERENCE_STEMS and REFERENCE_FILE in check_course_map.py."""
    root = Path(root)
    hook = Path(hook) if hook else root / ".claude" / "hooks" / "spoiler-guard.sh"
    problems = []
    src = hook.read_text(encoding="utf-8")
    m = re.search(r'^RX_SPOIL_DIR="\((.*?)\)\(/\|\\\$\)"', src, re.M)
    if not m:
        return ["the hook's RX_SPOIL_DIR could not be read"]
    alts = m.group(1).split("|")
    samples = []
    for a in alts:
        a = a.replace("\\\\", "").replace("${COURSE}", "dafny-verus-learn-0")
        a = a.lstrip("/")
        if a.startswith(".cache/") or a.startswith("tmp/"):
            continue                    # the course cache and the author lanes' scratch
            #                             (/tmp/dvl0-dv…) lie outside every checkout
        samples.append(a + "/sample.txt")
    import check_course_map as ccm
    for stem in sorted(ccm.REFERENCE_STEMS):
        samples += [f"dafny/Q/{stem}/x.dfy", f"verus/q/q04_x/src/{stem}.rs"]
    samples += ["verus/q/q04_solutions/src/lib.rs", "notes/archive.tar.age"]
    tmp = Path(tempfile.mkdtemp(prefix="dvl0-classdrift-", dir="/tmp"))
    try:
        for s in samples:
            if source_class(s) is None:
                problems.append(f"{s}: reference to the guard or the checker, but no refused class here")
            if s.endswith("sample.txt"):
                inp = json.dumps({"tool_name": "Read", "tool_input": {"file_path": s}, "cwd": str(tmp)})
                env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(tmp),
                       "CLAUDE_PROJECT_DIR": str(tmp)}
                p = subprocess.run(["bash", str(hook)], input=inp, capture_output=True, text=True,
                                   env=env, timeout=60)
                if p.returncode != 2 or not re.search(r"\(rule 1c?\)", p.stderr):
                    problems.append(f"{s}: RX_SPOIL_DIR names it, yet the hook did not block a "
                                    f"read of it under rule 1 or 1c (exit {p.returncode})")
            elif not ccm.is_reference(s):
                problems.append(f"{s}: the checker's is_reference no longer flags it")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return problems
