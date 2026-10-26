"""dvl.python — the course's Python adapter (phase DV4; QPLAN §11.8, §6 Q19).

The third language library beside dvl.dafny and dvl.verus, for the learner
Python files of harness/q/fvh_q/ and harness/r/fvh_r/ (types in dvl.common):

  holes(target, *, root=None) -> list[Hole]
      the tool-counted Python holes, through the frozen core's counter
      fvh.holes (the syntax tree, never text): one Hole per function whose
      body is `raise NotImplementedError("<item id>")`, kind
      `raise-not-implemented`, label the item id. HoleCountError when the
      file does not parse.
  lint(paths, mode="learner", *, root=None) -> list[Finding]
      the static rules of a learner Python file (below); mode reference adds
      every hole as a finding (a twin is hole-free).
  audit(target, lint_mode="learner", *, root=None) -> list[Finding]
      the lint of one file in the learner (or reference) mode: what
      scripts/vaudit reports for it.
  source_holes(text, *, root=None) -> [(item, name, line)]
      the counter on source text (firsttry's static scan).
  spec_hash(path, symbols=None) -> {qualified name: sha256}
      the frozen statements: each function's and class's signature (name,
      parameters with annotations and defaults, return annotation,
      decorators, bases), never its body or docstring.
  acceptance_tests(target, *, root=None) -> list[Path]
      the frozen acceptance tests of a registry harness file:
      harness/<t>/fvh_<t>/<sub>/<stem>.py -> harness/tests/<t>/<sub>/test_<stem>.py.
  test(target, names=None, *, root=None) -> Result
      those tests through pytest (below); per_symbol {node id: passed |
      failed | error | skipped}.
  check(target, gate=False, *, root=None) -> Result
      what scripts/vcheck runs on a .py file: the holes, then the tests. The
      learner loop's verdict is the tests'; the gate's is `verified` only with
      zero holes and every test passing.
  ref_check(twin, *, root=None) -> Result
      the reference gate of a twin (Solutions/harness/<path>): the twin laid
      over a scratch copy of harness/ (and of tests/corpus/, read by Q09's
      frozen tests) and the same tests run there; it also
      needs zero holes and a clean reference lint.
  triv_bodies(twin_text) -> {item id: body}
      the `# triv: <statement>` lines of each H item's block in a twin.
  empty_body(twin, item, *, root=None) -> Result
      the Python TRIV mode of the empty-body gate: the item's body replaced by
      its declared trivial body, on top of the reference, in a scratch
      overlay; verdict `failed` when the tests reject it (the hole is
      admitted), `verified` when they pass (it is not).
  lint_hollow(path, *, root=None) -> list[Finding]
      the shipping lint of a learner Python file: every H item holds exactly
      one counted hole, no other hole, no hole-like body (firsttry
      --lint-hollow's Python branch).
  summary_line(res, shown, mode) -> str
      `vcheck: <file> [python, <mode>]: <verdict> — <p> passed, <f> failed,
      <n> holes`.

How tests run. `uv run --offline --frozen --directory <harness> pytest -q -p
no:cacheprovider --junitxml <raw>/junit.xml <test files>`, through
dvl.common.run_capped (a memory-capped scope, pool `python`, wall-clock net),
with dvl's scrubbed environment plus PYTHONDONTWRITEBYTECODE=1, so a run
writes nothing into harness/ (no bytecode, no .pytest_cache). uv's project
environment lives in scratch (<scratch root>/py-env/<lock digest>), never in
the course tree, and the user's uv configuration is not read. Results come
from pytest's JUnit XML, never from its console text. A run needs uv's cache
to hold the locked packages (`uv sync --directory harness` once, online).

The learner lint (rules, each a Finding kind):
  bare-raise, hole-form, hole-id-mismatch, hole-not-alone, renamed-exception,
  empty-body, duplicate-hole, malformed-marker, parse-error
                       fvh.holes.lint: code that looks like a hole and is not
  import-outside-tier  an import beyond the standard library, the core `fvh`
                       and the file's own track package (fvh_q / fvh_r)
  reference-import     an import of the reference (solutions…)
  sys-path             sys.path or a dynamic import (__import__,
                       importlib.import_module)
  stats-reimplementation
                       a function named like a public fvh.stats function, or
                       an estimator's building block (math.comb, math.perm,
                       math.erf, math.erfc, statistics.NormalDist): statistics
                       code lives in the core (design §9.2 rule 4). A
                       heuristic: it flags the means, not the intent.

Pins: an optional [python] table in scripts/dvl/pins.toml (mem_gb,
wall_clock_s, jobs); defaults 4 GB, 600 s, 1 job.

CLI (scripts/ci.sh's harness job and by hand; prints locations, counts and
statuses, never file content):
  python3 scripts/dvl/python.py holes [--json] FILE...
  python3 scripts/dvl/python.py lint [--mode learner|reference] FILE...
  python3 scripts/dvl/python.py hollow [--root R] FILE...
  python3 scripts/dvl/python.py test [--root R] [--name N]... FILE
  python3 scripts/dvl/python.py check [--gate] [--json] [--root R] FILE
  python3 scripts/dvl/python.py spec-hash FILE
  python3 scripts/dvl/python.py files [--armed [--ids]] [--root R]
  python3 scripts/dvl/python.py ref [--root R] TWIN           (author-only)
  python3 scripts/dvl/python.py triv [--root R] TWIN [ITEM...] (author-only)
`files` lists the learner Python files on disk (with --armed: those the
non-planned registry records list in `harness`; with --ids: those records'
ids); `triv` runs the TRIV mode on
every H item the twin's learner file holds a hole for (or on the named items)
and passes when each declared trivial body fails the tests.
Exit: 0 ok · 1 failed · 2 usage · 3 refused.
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from dvl import common  # noqa: E402
from dvl.common import Diag, DvlError, Finding, Hole, Result  # noqa: E402
import course_items as ci  # noqa: E402  (the ONE item parser, Δ71)

LANG = "python"
HOLE_KIND = "raise-not-implemented"
MODES = ("learner", "reference")
HARNESS = "harness"
REF_DIR = "Solutions"
LEARNER_FILE = re.compile(r"harness/(q|r)/fvh_(q|r)/(?P<rest>.+)\.py")
# A challenge module's solo Python (QPLAN §31.4, DELTAS Δ402): agents/q<NN>_<name>/…,
# NN in 19..33; its frozen tests live under harness/tests/challenges/<package>/.
AGENT_DIR = "agents"
AGENT_FILE = re.compile(r"agents/(?P<pkg>q(?P<num>19|2[0-9]|3[0-3])_[a-z0-9_]+)/(?P<rest>.+)\.py")
AGENT_PKG = re.compile(r"q(19|2[0-9]|3[0-3])_[a-z0-9_]+")
TRIV_LINE = re.compile(r"^\s*#\s*triv:\s?(.*)$")
STATS_NAMES = ("pass_at_k", "wilson_interval", "bootstrap_ci", "mcnemar", "permutation_test",
               "holm", "mde_two_proportions")
STATS_PRIMITIVES = {("math", "comb"), ("math", "perm"), ("math", "erf"), ("math", "erfc"),
                    ("statistics", "NormalDist")}
COPY_IGNORE = shutil.ignore_patterns(".venv", "__pycache__", ".pytest_cache", "*.pyc")
DEFAULTS = {"mem_gb": 4, "wall_clock_s": 600, "jobs": 1}


class Refused(DvlError):
    """The adapter refuses this target (no tool runs)."""


class HoleCountError(DvlError):
    """holes() could not count: the file does not parse. `.result` holds it."""

    def __init__(self, message, result):
        super().__init__(message)
        self.result = result


def pins():
    """The [python] pins with their defaults (the table is optional)."""
    got = common.load_pins().get("python", {})
    return {k: got.get(k, v) for k, v in DEFAULTS.items()}


# =====================================================================================
# Roots, paths and the frozen core
# =====================================================================================

def course_root(path=None, root=None):
    """The course root: `root` when given, else the nearest directory above
    `path` that holds MODULES.toml and harness/, else the scripts' checkout."""
    if root is not None:
        return Path(root).resolve()
    if path is not None:
        for d in Path(path).resolve().parents:
            if (d / "MODULES.toml").is_file() and (d / HARNESS).is_dir():
                return d
    return common.REPO_ROOT


def _rel(path, root):
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return None


def _core_holes(root):
    """The frozen counter fvh.holes, loaded from the course root's harness
    (else the scripts' checkout) under a private module name."""
    for base in (Path(root), common.REPO_ROOT):
        f = base / HARNESS / "fvh" / "holes.py"
        if f.is_file():
            name = f"_dvl_fvh_holes_{hashlib.sha256(str(f).encode()).hexdigest()[:12]}"
            if name not in sys.modules:
                spec = importlib.util.spec_from_file_location(name, f)
                mod = importlib.util.module_from_spec(spec)
                sys.modules[name] = mod
                spec.loader.exec_module(mod)
            return sys.modules[name]
    raise Refused(f"no frozen hole counter: {HARNESS}/fvh/holes.py is missing")


def _read(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise Refused(f"{path}: cannot read ({e})") from None


def _refused(target, message):
    return Result(LANG, str(target), None, "refused", "cli",
                  findings=[Finding(str(target), 0, "refused", message)])


# =====================================================================================
# Holes, lint and statements
# =====================================================================================

def holes(target, *, root=None):
    """The tool-counted holes of one Python file (see the module doc)."""
    p = Path(target).resolve()
    root = course_root(p, root)
    text = _read(p)
    try:
        found = _core_holes(root).count_holes(text)
    except SyntaxError as e:
        res = Result(LANG, str(p), None, "failed", "parse",
                     diagnostics=[Diag(str(p), e.lineno or 0, e.offset or 0, "error",
                                       f"the file does not parse: {e.msg}", "syntax")])
        raise HoleCountError(f"{p}: the file does not parse; holes cannot be counted",
                             res) from None
    return [Hole(str(p), h.line, 1, HOLE_KIND, h.item) for h in found]


def _track(rel):
    m = LEARNER_FILE.fullmatch(rel or "")
    if m and m.group(1) == m.group(2):
        return m.group(1)
    return "q" if AGENT_FILE.fullmatch(rel or "") else None


def agent_packages_allowed(num):
    """The `agents` package numbers a challenge module q<num> may import: its own
    and the earlier modules' of its topic (Q19-Q21, Q22-Q24, ..., three each;
    QPLAN §31.4 item 1, the py-agents tier)."""
    first = 19 + 3 * ((int(num) - 19) // 3)
    return {f"{n:02d}" for n in range(first, int(num) + 1)}


def _agent_heads(rel):
    """For an agents/ file, a predicate on an import head: an allowed agents
    package of its topic. None for any other file."""
    m = AGENT_FILE.fullmatch(rel or "")
    if not m:
        return None
    ok = agent_packages_allowed(m.group("num"))
    return lambda head: bool(AGENT_PKG.fullmatch(head)) and head[1:3] in ok


def _import_findings(path, tree, track, agent_heads=None):
    out = []
    own = {"fvh"} | ({f"fvh_{track}"} if track else set())
    std = set(sys.stdlib_module_names) | {"__future__"}

    def judge(line, head):
        if head.lower().startswith("solutions"):
            out.append(Finding(str(path), line, "reference-import",
                               f"imports {head}: learner code never reaches the reference"))
        elif head not in std and head not in own and not (agent_heads and agent_heads(head)):
            allowed = "the standard library, fvh" + (f" and fvh_{track}" if track else "")
            if agent_heads:
                allowed += " and the agents packages of this module and its topic's earlier modules"
            out.append(Finding(str(path), line, "import-outside-tier",
                               f"imports {head}; a learner Python file imports {allowed} only"))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                judge(node.lineno, a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            judge(node.lineno, node.module.split(".")[0])
            if node.module in ("math", "statistics"):
                for a in node.names:
                    if (node.module, a.name) in STATS_PRIMITIVES:
                        out.append(Finding(str(path), node.lineno, "stats-reimplementation",
                                           f"imports {node.module}.{a.name}, an estimator's "
                                           "building block: compose fvh.stats instead"))
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if (node.value.id, node.attr) in STATS_PRIMITIVES:
                out.append(Finding(str(path), node.lineno, "stats-reimplementation",
                                   f"uses {node.value.id}.{node.attr}, an estimator's building "
                                   "block: compose fvh.stats instead"))
            if node.value.id == "sys" and node.attr == "path":
                out.append(Finding(str(path), node.lineno, "sys-path",
                                   "sys.path reaches files outside the package"))
            if node.value.id == "importlib" and node.attr == "import_module":
                out.append(Finding(str(path), node.lineno, "sys-path",
                                   "a dynamic import reaches modules the import lint cannot see"))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and \
                node.func.id == "__import__":
            out.append(Finding(str(path), node.lineno, "sys-path",
                               "a dynamic import reaches modules the import lint cannot see"))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in STATS_NAMES:
            out.append(Finding(str(path), node.lineno, "stats-reimplementation",
                               f"defines {node.name}, a function of fvh.stats: compose the core "
                               "instead of re-deriving it"))
    return out


def lint(paths, mode="learner", *, root=None):
    """The static rules over Python files (see the module doc). A file that
    cannot be read or does not parse is one finding."""
    if mode not in MODES:
        raise ValueError(f"lint mode must be one of {', '.join(MODES)}, not {mode!r}")
    out = []
    for raw in ([paths] if isinstance(paths, (str, Path)) else paths):
        p = Path(raw).resolve()
        r = course_root(p, root)
        try:
            text = _read(p)
        except Refused as e:
            out.append(Finding(str(p), 0, "unreadable", str(e)))
            continue
        core = _core_holes(r)
        out += [Finding(str(p), f.line, f.kind, f.message) for f in core.lint(text)]
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue          # the core's lint already reported parse-error
        rel = _rel(p, r)
        if rel and rel.startswith(REF_DIR + "/"):
            rel = rel[len(REF_DIR) + 1:]
        out += _import_findings(p, tree, _track(rel), _agent_heads(rel))
        if mode == "reference":
            out += [Finding(str(p), h.line, "hole", f"{h.item}: a hole in a reference file")
                    for h in core.count_holes(text)]
    return sorted(set(out), key=lambda f: (f.file, f.line, f.kind, f.message))


def audit(target, lint_mode="learner", *, root=None):
    """The assumption audit of one Python file (scripts/vaudit): its lint in
    the reference mode when lint_mode is `reference`, else the learner mode."""
    return lint([target], "reference" if lint_mode == "reference" else "learner", root=root)


def source_holes(text, *, root=None):
    """[(item id, qualified name, def line)] of the holes in Python source text
    (the frozen counter, for callers that hold text, not a file: firsttry's
    static hole scan). Raises SyntaxError when the text does not parse."""
    return [(h.item, h.name, h.line)
            for h in _core_holes(course_root(None, root)).count_holes(text)]


def _signature(node):
    """The normalized statement of a function or class (no body, no docstring)."""
    deco = [ast.unparse(d) for d in node.decorator_list]
    if isinstance(node, ast.ClassDef):
        bases = [ast.unparse(b) for b in node.bases] + [ast.unparse(k) for k in node.keywords]
        return f"{deco} class {node.name}({', '.join(bases)})"
    kind = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    ret = f" -> {ast.unparse(node.returns)}" if node.returns is not None else ""
    return f"{deco} {kind} {node.name}({ast.unparse(node.args)}){ret}"


def spec_hash(path, symbols=None):
    """{qualified name: sha256 of its normalized statement} of a Python file
    (classes `C`, methods `C.m`, nested functions `f.<locals>.g`), optionally
    only `symbols`. Raises SyntaxError for a file that does not parse."""
    tree = ast.parse(_read(path))
    out = {}

    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{prefix}{child.name}"
                out[name] = hashlib.sha256(_signature(child).encode("utf-8")).hexdigest()
                walk(child, f"{name}." if isinstance(child, ast.ClassDef)
                     else f"{name}.<locals>.")
            else:
                walk(child, prefix)
    walk(tree, "")
    if symbols is not None:
        want = set(symbols)
        out = {k: v for k, v in out.items() if k in want}
    return out


# =====================================================================================
# Acceptance tests
# =====================================================================================

def acceptance_tests(target, *, root=None):
    """The frozen acceptance tests of a learner harness file that a registry
    record lists in `harness` (repo-relative paths under harness/tests/).
    Refused for any other file or when the test file is missing."""
    p = Path(target).resolve()
    r = course_root(p, root)
    rel = _rel(p, r)
    m = LEARNER_FILE.fullmatch(rel or "")
    a = AGENT_FILE.fullmatch(rel or "")
    if (not m or m.group(1) != m.group(2)) and not a:
        raise Refused(f"{rel or p}: not a learner harness file (harness/q/fvh_q/…, "
                      "harness/r/fvh_r/… or agents/q<NN>_<name>/…)")
    import check_course_map as ccm
    data, err = ccm.load_registry(r)
    if err:
        raise Refused(f"the module registry is unusable: {err}")
    owners = [x.get("id") for x in data.get("module", [])
              if isinstance(x, dict) and rel in (x.get("harness") or [])]
    if not owners:
        raise Refused(f"{rel}: no module lists it in `harness` (MODULES.toml), so it has no "
                      "acceptance tests")
    if a:
        rest = Path(a.group("rest"))
        test_rel = (Path(HARNESS) / "tests" / "challenges" / a.group("pkg") / rest.parent
                    / f"test_{rest.name}.py")
    else:
        rest = Path(m.group("rest"))
        test_rel = Path(HARNESS) / "tests" / m.group(1) / rest.parent / f"test_{rest.name}.py"
    if not (r / test_rel).is_file():
        raise Refused(f"{rel}: its acceptance tests {test_rel.as_posix()} do not exist "
                      f"({owners[0]})")
    return [test_rel]


# =====================================================================================
# Running pytest
# =====================================================================================

def uv_binary():
    """The host's uv (VERSIONS.md §1.4; harness/pyproject.toml's required-version
    refuses one older than 0.11.0, DELTAS Δ503)."""
    for cand in (shutil.which("uv"), str(Path.home() / ".local" / "bin" / "uv")):
        if cand and Path(cand).is_file() and os.access(cand, os.X_OK):
            return str(Path(cand).resolve())
    raise Refused("uv is not installed (the pinned host tool, VERSIONS.md §1.4)")


def project_env(harness_dir):
    """uv's project environment for this lock: in scratch, never in the tree."""
    lock = Path(harness_dir) / "uv.lock"
    digest = hashlib.sha256(lock.read_bytes() if lock.is_file() else b"no-lock").hexdigest()
    d = common.scratch_root() / "py-env" / digest[:16]
    d.parent.mkdir(parents=True, exist_ok=True)
    return d


def run_env(harness_dir):
    """dvl's scrubbed environment for a pytest run (no user uv configuration)."""
    env = common.default_env()
    conf = common.scratch_root() / "py-config"
    conf.mkdir(parents=True, exist_ok=True)
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "UV_PROJECT_ENVIRONMENT": str(project_env(
        harness_dir)), "XDG_CONFIG_HOME": str(conf), "UV_NO_PROGRESS": "1", "NO_COLOR": "1"})
    # The CI harness job resolves uv's cache before it swaps HOME for an empty
    # one (DV4-PLAN §9): pass that cache through, so the offline run finds pytest.
    if os.environ.get("UV_CACHE_DIR"):
        env["UV_CACHE_DIR"] = os.environ["UV_CACHE_DIR"]
    else:
        seeded = container_cache()
        if seeded is not None:
            env["UV_CACHE_DIR"] = str(seeded)
    return env


SEED_CACHE_ENV = "DVL_UV_SEED_CACHE"


def container_cache():
    """In a sandbox container (DVL_CAP container-verify or container-agent), the
    image's seeded uv cache (the locked wheels, DVL_UV_SEED_CACHE, read-only)
    copied once into the run's scratch, since uv needs a writable cache; None
    elsewhere (DV4-PLAN §5.9: Python acceptance tests run in the verification
    container)."""
    seed = os.environ.get(SEED_CACHE_ENV)
    if not seed or not os.environ.get("DVL_CAP", "").startswith("container") \
            or not Path(seed).is_dir():
        return None
    dst = common.scratch_root() / "uv-cache"
    if not dst.is_dir():
        tmp = common.scratch_root() / f"uv-cache.{os.getpid()}"
        shutil.copytree(seed, tmp, symlinks=True)
        for d, dirs, files in os.walk(tmp):
            for n in dirs + files:
                q = Path(d) / n
                if not q.is_symlink():
                    q.chmod(q.stat().st_mode | 0o200)
        Path(tmp).chmod(Path(tmp).stat().st_mode | 0o200)
        tmp.rename(dst)
    return dst


def _files(test_rels):
    """The test files relative to the harness dir (pytest's arguments)."""
    return [Path(t).relative_to(HARNESS).as_posix() for t in test_rels]


def _named(node, name):
    """True when a node id is the named test: the node id itself, its last
    part, or that part without its parameters (every parametrization)."""
    last = node.split("::")[-1]
    return node == name or node.endswith("::" + name) or last.split("[")[0] == name


def _junit(path, harness_dir):
    """({node id: status}, [Diag]) from pytest's JUnit XML report."""
    per, diags = {}, []
    tree = ET.parse(path)
    for case in tree.iter("testcase"):
        cls, name = case.get("classname", ""), case.get("name", "")
        parts = cls.split(".")
        node = None
        for k in range(len(parts), 0, -1):
            f = Path(harness_dir, *parts[:k]).with_suffix(".py")
            if f.is_file():
                node = "::".join([Path(*parts[:k]).with_suffix(".py").as_posix()]
                                 + parts[k:] + [name])
                break
        node = node or f"{cls}::{name}"
        status, detail = "passed", None
        for tag in ("failure", "error", "skipped"):
            el = case.find(tag)
            if el is not None:
                status = {"failure": "failed", "error": "error", "skipped": "skipped"}[tag]
                detail = el
                break
        per[node] = status
        if status in ("failed", "error"):
            text = (detail.text or "") if detail is not None else ""
            msg = (detail.get("message") if detail is not None else "") or status
            file = node.split("::", 1)[0]
            line = 0
            for m in re.finditer(rf"^{re.escape(file)}:(\d+):", text, re.M):
                line = int(m.group(1))
            diags.append(Diag(str(Path(harness_dir) / file), line, 0, "error",
                              f"{node}: {msg.splitlines()[0] if msg else status}", "pytest"))
    return per, diags


def run_pytest(harness_dir, test_files, target, names=()):
    """One pytest run of the test files in harness_dir (see the module doc).
    Returns a Result (stage test) with per_symbol and one error Diag per
    failing test. With `names`, every test still runs, but only the named
    ones are reported and judged; a name that ran no test is a finding."""
    harness_dir = Path(harness_dir).resolve()
    try:
        uv = uv_binary()
    except Refused as e:
        return _refused(target, str(e))
    p = pins()
    raw = common.scratch_dir("python-test")
    junit = raw / "junit.xml"
    argv = [uv, "run", "--offline", "--frozen", "--directory", str(harness_dir), "pytest", "-q",
            "-p", "no:cacheprovider", "--junitxml", str(junit), *test_files]
    try:
        rc, out, err = common.run_capped(argv, p["mem_gb"], p["wall_clock_s"],
                                         env=run_env(harness_dir), cwd=raw, pool="python",
                                         out_dir=raw)
    except common.CapError as e:
        return Result(LANG, str(target), None, "error", "cli", raw_dir=str(raw), cmd=argv,
                      findings=[Finding(str(target), 0, "cap", str(e))])
    res = Result(LANG, str(target), rc, "error", "test", None, raw_dir=str(raw), cmd=argv)
    if common.is_killed(rc):
        res.verdict = "killed(memory)"
        return res
    if rc == common.WALL_CLOCK_EXIT:
        res.verdict = "inconclusive"
        return res
    if not junit.is_file():
        tail = Path(err).read_text(encoding="utf-8", errors="replace").strip().splitlines()
        why = tail[-1] if tail else f"exit {rc}"
        hint = "; fill uv's cache once with `uv sync --directory harness`" \
            if "offline" in why.lower() or "network" in why.lower() else ""
        res.stage = "cli"
        res.findings.append(Finding(str(target), 0, "pytest-not-run",
                                    f"pytest did not run (exit {rc}): {why}{hint}"))
        return res
    try:
        per, diags = _junit(junit, harness_dir)
    except ET.ParseError as e:
        res.findings.append(Finding(str(target), 0, "junit-unreadable", f"{e}"))
        return res
    names = list(names or [])
    missing = [n for n in names if not any(_named(k, n) for k in per)]
    if names:
        per = {k: v for k, v in per.items() if any(_named(k, n) for n in names)}
        diags = [d for d in diags if d.message.split(": ", 1)[0] in per]
    res.per_symbol, res.diagnostics = per, diags
    res.verified_count = sum(1 for v in per.values() if v == "passed")
    for n in missing:
        res.findings.append(Finding(str(target), 0, "test-not-run", f"{n}: the test did not run"))
    if not per:
        res.findings.append(Finding(str(target), 0, "no-tests",
                                    "no test ran: exit 0 alone is not a pass"))
    if rc in (3, 4):
        res.stage = "cli"
        return res
    bad = [k for k, v in per.items() if v in ("failed", "error")]
    ok_rc = rc in (0, 1) if names else rc == 0
    res.verdict = "verified" if (ok_rc and per and not bad and not missing) else "failed"
    return res


def test(target, names=None, *, root=None):
    """The acceptance tests of a learner harness file, run in place (pytest
    writes nothing into harness/)."""
    p = Path(target).resolve()
    r = course_root(p, root)
    try:
        tests = acceptance_tests(p, root=r)
    except Refused as e:
        return _refused(p, str(e))
    names = list(names or [])
    return run_pytest(r / HARNESS, _files(tests), p, names)


def check(target, gate=False, *, root=None):
    """scripts/vcheck on a .py file: the holes, then the acceptance tests."""
    p = Path(target).resolve()
    r = course_root(p, root)
    if p.suffix != ".py" or not p.is_file():
        return _refused(p, f"{p}: not a Python file")
    try:
        found = holes(p, root=r)
    except HoleCountError as e:
        return e.result
    except Refused as e:
        return _refused(p, str(e))
    res = test(p, root=r)
    res.target = str(p)
    res.holes = found
    if gate and res.verdict == "verified" and found:
        res.verdict = "failed"
    return res


# =====================================================================================
# The reference: overlays, the reference gate and the TRIV mode
# =====================================================================================

def learner_of_twin(twin, root):
    """(learner path, its path from the course root) of a twin
    Solutions/harness/<rest> or Solutions/agents/<rest> (a challenge's
    author-only twin, QPLAN §31.4)."""
    rel = _rel(twin, root)
    for top in (HARNESS, AGENT_DIR):
        prefix = f"{REF_DIR}/{top}/"
        if rel is not None and rel.startswith(prefix):
            inner = f"{top}/{rel[len(prefix):]}"
            break
    else:
        raise Refused(f"{twin}: not a twin under {REF_DIR}/{HARNESS}/ or {REF_DIR}/{AGENT_DIR}/")
    learner = Path(root) / inner
    if not learner.is_file():
        raise Refused(f"{rel}: its learner file {inner} does not exist")
    return learner, inner


def _overlay(root, inner, text):
    """A scratch copy of harness/ (and of agents/ when the root has it) with
    `text` at <inner> (a path from the course root), and of tests/corpus/
    when the root has it: a frozen test that reads the cheat corpus through
    fvh.corpus's default root (Q09's gate core) then runs in the overlay as
    it does in place, instead of skipping (DV3b kits, Δ167)."""
    s = common.scratch_dir("python-overlay")
    shutil.copytree(Path(root) / HARNESS, s / HARNESS, ignore=COPY_IGNORE, symlinks=True)
    agents = Path(root) / AGENT_DIR
    if agents.is_dir():
        shutil.copytree(agents, s / AGENT_DIR, ignore=COPY_IGNORE, symlinks=True)
    if inner.startswith(AGENT_DIR + "/"):
        # a challenge twin composes the learner's earlier work (Q31's gate imports the Q18
        # gate, fvh_q.gate.gate_v2): in its reference check that work is the reference's,
        # so every harness twin and every earlier agents twin is laid over the copy (Δ406)
        for top in (HARNESS, AGENT_DIR):
            ref = Path(root) / REF_DIR / top
            if ref.is_dir():
                for f in ref.rglob("*.py"):
                    if not {"__pycache__", ".venv"} & set(f.parts):
                        dest = s / top / f.relative_to(ref)
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(f, dest)
    corpus = Path(root) / "tests" / "corpus"
    if corpus.is_dir():
        shutil.copytree(corpus, s / "tests" / "corpus", ignore=COPY_IGNORE, symlinks=True)
    (s / inner).parent.mkdir(parents=True, exist_ok=True)
    (s / inner).write_text(text, encoding="utf-8")
    return s


def _remap(res, scratch, root):
    """Locations under a scratch overlay, moved back to the course root."""
    base, to = str(Path(scratch).resolve()), str(Path(root).resolve())

    def m(p):
        return to + p[len(base):] if p and p.startswith(base) else p
    res.diagnostics = [dataclasses.replace(d, file=m(d.file)) for d in res.diagnostics]
    res.findings = [dataclasses.replace(f, file=m(f.file)) for f in res.findings]
    return res


def ref_check(twin, *, root=None):
    """The reference gate of a twin: zero holes, a clean reference lint and
    every acceptance test passing, run on the twin laid over a scratch copy
    of harness/. The overlay is deleted afterwards."""
    t = Path(twin).resolve()
    r = course_root(t, root)
    try:
        learner, inner = learner_of_twin(t, r)
        tests = acceptance_tests(learner, root=r)
        text = _read(t)
        found = holes(t, root=r)
    except HoleCountError as e:
        return e.result
    except Refused as e:
        return _refused(t, str(e))
    s = _overlay(r, inner, text)
    try:
        res = run_pytest(s / HARNESS, _files(tests), t)
        _remap(res, s, r)
    finally:
        shutil.rmtree(s, ignore_errors=True)
    res.target = str(t)
    res.holes = found
    res.findings += lint([t], "reference", root=r)
    if res.verdict == "verified" and (found or res.findings):
        res.verdict = "failed"
    return res


def _blocks(text, core):
    """{item id: (first line, last line)} of the item blocks of a Python file."""
    marks = core.markers(text)
    n = len(text.split("\n"))
    out = {}
    for k, m in enumerate(marks):
        end = marks[k + 1].line - 1 if k + 1 < len(marks) else n
        out.setdefault(m.item, (m.line, end))
    return out


def triv_bodies(twin_text, *, root=None):
    """{item id: body} from the `# triv:` lines of each item block (one or more
    lines; joined with newlines)."""
    core = _core_holes(course_root(None, root))
    lines = twin_text.split("\n")
    out = {}
    for item, (a, b) in _blocks(twin_text, core).items():
        got = [m.group(1) for ln in range(a, b + 1) if (m := TRIV_LINE.match(lines[ln - 1]))]
        if got:
            out[item] = "\n".join(got).rstrip()
    return out


def _with_body(text, item, body, core):
    """`text` with the body (after its docstring) of the function in `item`'s
    block replaced by `body`."""
    tree = ast.parse(text)
    blocks = _blocks(text, core)
    if item not in blocks:
        raise Refused(f"{item}: no item block in the twin")
    a, b = blocks[item]
    fns = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
           and a < n.lineno <= b]
    if not fns:
        raise Refused(f"{item}: its block holds no function")
    fn = min(fns, key=lambda n: n.lineno)
    stmts = list(fn.body)
    if stmts and isinstance(stmts[0], ast.Expr) and isinstance(stmts[0].value, ast.Constant) \
            and isinstance(stmts[0].value.value, str):
        stmts = stmts[1:]
    if not stmts:
        raise Refused(f"{item}: the function has no body to replace")
    first, last = stmts[0], stmts[-1]
    lines = text.split("\n")
    indent = " " * first.col_offset
    new = [indent + x if x.strip() else x for x in body.split("\n")]
    return "\n".join(lines[:first.lineno - 1] + new + lines[last.end_lineno:])


def empty_body(twin, item, *, root=None):
    """The Python TRIV mode for one hole (see the module doc). per_symbol
    {"TRIV": verified | failed | …}; verdict failed = the hole is admitted."""
    t = Path(twin).resolve()
    r = course_root(t, root)
    try:
        learner, inner = learner_of_twin(t, r)
        tests = acceptance_tests(learner, root=r)
        text = _read(t)
        body = triv_bodies(text, root=r).get(item)
        if body is None:
            raise Refused(f"{item}: its twin block declares no `# triv:` body (QPLAN §11.8)")
        variant = _with_body(text, item, body, _core_holes(r))
    except SyntaxError as e:
        return _refused(t, f"the twin does not parse (line {e.lineno})")
    except Refused as e:
        return _refused(t, str(e))
    s = _overlay(r, inner, variant)
    try:
        res = run_pytest(s / HARNESS, _files(tests), t)
        _remap(res, s, r)
    finally:
        shutil.rmtree(s, ignore_errors=True)
    res.target = str(t)
    res.per_symbol = {"TRIV": res.verdict}
    return res


# =====================================================================================
# The shipping lint and the summary line
# =====================================================================================

def lint_hollow(path, *, root=None):
    """The shipping lint of a learner Python file as shipped (QPLAN §11.8):
    every H item holds exactly one counted hole labelled with its id
    (hole-missing, hole-count), no hole outside an H, X or T item
    (stray-hole), and the learner lint is clean. Never runs a tool."""
    p = Path(path).resolve()
    r = course_root(p, root)
    rel = _rel(p, r) or str(p)
    text = _read(p)
    items, errs = ci.parse_items(rel, text)
    out = [Finding(str(p), int(e.split(":")[1]) if e.split(":")[1:2] and
                   e.split(":")[1].isdigit() else 0, "marker-grammar", e) for e in errs]
    out += lint([p], "learner", root=r)
    try:
        found = holes(p, root=r)
    except HoleCountError:
        return sorted(set(out), key=lambda f: (f.line, f.kind))
    by_item = {}
    for h in found:
        by_item.setdefault(h.label, []).append(h)
    kinds = {it["id"]: it["kind"] for it in items}
    for it in items:
        if it["kind"] != "H":
            continue
        n = len(by_item.get(it["id"], []))
        if n == 0:
            out.append(Finding(str(p), it["line_start"], "hole-missing",
                               f"{it['id']} ships no counted hole"))
        elif n > 1:
            out.append(Finding(str(p), it["line_start"], "hole-count",
                               f"{it['id']} ships {n} counted holes; an item ships one"))
    for h in found:
        if kinds.get(h.label) not in ("H", "X", "T"):
            out.append(Finding(str(p), h.line, "stray-hole",
                               f"a hole labelled {h.label}, which is no H, X or T item here"))
    return sorted(set(out), key=lambda f: (f.line, f.kind, f.message))


def learner_files(root=None, armed=False, ids=False):
    """Repo-relative learner Python files: those on disk under harness/q/fvh_q/
    and harness/r/fvh_r/ (package __init__.py files excepted), or with
    armed=True those that a non-planned registry record lists in `harness`
    (whether or not they exist); with ids=True as well, the ids of those
    records instead. Refused when the registry is unusable."""
    r = course_root(None, root)
    if armed:
        import check_course_map as ccm
        data, err = ccm.load_registry(r)
        if err:
            raise Refused(f"the module registry is unusable: {err}")
        pairs = [(m.get("id"), p) for m in data.get("module", []) if isinstance(m, dict)
                 and m.get("status") != "planned" for p in (m.get("harness") or [])
                 if isinstance(p, str) and (LEARNER_FILE.fullmatch(p) or AGENT_FILE.fullmatch(p))]
        return list(dict.fromkeys(i if ids else p for i, p in pairs))
    out = []
    for t in ("q", "r"):
        d = r / HARNESS / t / f"fvh_{t}"
        if d.is_dir():
            out += [p.relative_to(r).as_posix() for p in d.rglob("*.py")
                    if p.is_file() and p.name != "__init__.py"
                    and not {"__pycache__", ".venv"} & set(p.parts)]
    d = r / AGENT_DIR
    if d.is_dir():
        out += [rel for rel in (q.relative_to(r).as_posix() for q in d.rglob("*.py")
                                if q.is_file() and q.name != "__init__.py"
                                and not {"__pycache__", ".venv"} & set(q.parts))
                if AGENT_FILE.fullmatch(rel)]
    return sorted(out)


def summary_line(res, shown, mode):
    """The vcheck summary line of a Python run."""
    if res.verdict == "refused":
        return f"vcheck: {shown} [{LANG}, {mode}]: refused (no tool ran)"
    passed = sum(1 for v in res.per_symbol.values() if v == "passed")
    failed = sum(1 for v in res.per_symbol.values() if v in ("failed", "error"))
    n = len(res.holes)
    parts = [f"{passed} passed", f"{failed} failed", f"{n} hole{'s' if n != 1 else ''}"]
    if res.findings:
        parts.append(f"{len(res.findings)} finding{'s' if len(res.findings) != 1 else ''}")
    if res.stage != "test" and res.verdict != "verified":
        parts.append(f"stage {res.stage}")
    return f"vcheck: {shown} [{LANG}, {mode}]: {res.verdict} — " + ", ".join(parts)


# =====================================================================================
# CLI
# =====================================================================================

def _show(path, root):
    return _rel(path, root) or str(path)


def _print_details(res, root):
    for h in res.holes:
        print(f"{_show(h.file, root)}:{h.line}: hole {h.label}")
    for d in res.diagnostics:
        if d.severity == "error":
            print(f"{_show(d.file, root)}:{d.line}: {d.message}")
    for f in res.findings:
        print(f"{_show(f.file, root)}:{f.line}: {f.kind}: {f.message}")


def _author(root, tool):
    """The author self-gate (vcheck's: CI=true or the three-condition test)."""
    import importlib.machinery
    if "vcheck" in sys.modules:
        core = sys.modules["vcheck"]
    else:
        loader = importlib.machinery.SourceFileLoader("vcheck", str(_SCRIPTS / "vcheck"))
        spec = importlib.util.spec_from_loader("vcheck", loader)
        core = importlib.util.module_from_spec(spec)
        sys.modules["vcheck"] = core
        loader.exec_module(core)
    why = core.author_gate(root)
    if why:
        raise Refused(f"{tool} is author-only and refuses to run here ({why})")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python.py", description="The course's Python adapter.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("holes", "lint", "hollow", "test", "check", "spec-hash", "ref", "triv",
                 "files"):
        sp = sub.add_parser(name)
        sp.add_argument("--root", type=Path, default=None)
        if name == "files":
            sp.add_argument("--armed", action="store_true")
            sp.add_argument("--ids", action="store_true", help="with --armed: the module ids")
        elif name == "triv":
            sp.add_argument("files", nargs="+", metavar="TWIN [ITEM...]")
        else:
            sp.add_argument("files", nargs="+", metavar="FILE")
        if name in ("holes", "check"):
            sp.add_argument("--json", action="store_true")
        if name == "lint":
            sp.add_argument("--mode", choices=MODES, default="learner")
        if name == "test":
            sp.add_argument("--name", action="append", default=[])
        if name == "check":
            sp.add_argument("--gate", action="store_true")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    if a.cmd == "files":
        try:
            if a.ids and not a.armed:
                print("python.py files: --ids goes with --armed", file=sys.stderr)
                return 2
            for f in learner_files(a.root, armed=a.armed, ids=a.ids):
                print(f)
        except Refused as e:
            print(f"python.py: refused: {e}", file=sys.stderr)
            return 3
        return 0
    if a.cmd in ("test", "check", "ref") and len(a.files) != 1:
        print(f"python.py {a.cmd}: one file", file=sys.stderr)
        return 2
    root = course_root(a.files[0], a.root)
    try:
        if a.cmd == "holes":
            report, code = [], 0
            for f in a.files:
                try:
                    hs = holes(f, root=a.root)
                    report.append({"file": _show(f, root), "holes": [h.label for h in hs]})
                except HoleCountError as e:
                    code = 1
                    report.append({"file": _show(f, root), "error": str(e)})
            if a.json:
                print(json.dumps(report))
            else:
                for x in report:
                    print(f"{x['file']}: " + (x["error"] if "error" in x
                                              else f"{len(x['holes'])} hole(s)"))
            return code
        if a.cmd in ("lint", "hollow"):
            found = lint(a.files, a.mode, root=a.root) if a.cmd == "lint" else \
                [f for x in a.files for f in lint_hollow(x, root=a.root)]
            for f in found:
                print(f"{_show(f.file, root)}:{f.line}: {f.kind}: {f.message}")
            print(f"python.py {a.cmd}: {len(a.files)} file(s), {len(found)} finding(s)")
            return 1 if found else 0
        if a.cmd == "spec-hash":
            for f in a.files:
                for k, v in spec_hash(f).items():
                    print(f"{_show(f, root)} {k} {v}")
            return 0
        if a.cmd == "test":
            res = test(a.files[0], a.name, root=a.root)
            mode = "test"
        elif a.cmd == "check":
            res = check(a.files[0], a.gate, root=a.root)
            mode = "gate" if a.gate else "learner loop"
        elif a.cmd == "ref":
            _author(root, "python.py ref")
            res = ref_check(a.files[0], root=a.root)
            mode = "reference gate"
        else:
            _author(root, "python.py triv")
            twin = Path(a.files[0])
            items = a.files[1:] or sorted(triv_bodies(_read(twin), root=a.root))
            hs = [h.label for h in holes(learner_of_twin(twin.resolve(), root)[0], root=a.root)]
            items = list(dict.fromkeys(items + [x for x in hs if x not in items]))
            if not items:
                print("python.py triv: no H item found (an empty list fails)")
                return 1
            bad = 0
            for item in items:
                res = empty_body(twin, item, root=a.root)
                if res.verdict == "failed":
                    print(f"  ✓ {item}  the declared trivial body fails the acceptance tests")
                else:
                    bad += 1
                    why = "PASSES the acceptance tests" if res.verdict == "verified" else \
                        f"no verdict ({res.verdict}; " + "; ".join(f.message for f in
                                                                  res.findings) + ")"
                    print(f"  ✗ {item}  the trivial body {why}")
            print(f"python.py triv: {len(items) - bad}/{len(items)} hole(s) pass the gate")
            return 1 if bad else 0
        if a.cmd == "check" and a.json:
            print(json.dumps(res.to_dict(), ensure_ascii=False, sort_keys=True))
        else:
            print(summary_line(res, _show(res.target, root), mode))
            if a.cmd != "ref":
                _print_details(res, root)
            else:
                for f in res.findings:
                    print(f"{_show(f.file, root)}:{f.line}: {f.kind}")
        if res.verdict == "refused":
            return 3
        return 0 if res.verdict == "verified" else 1
    except Refused as e:
        print(f"python.py: refused: {e}", file=sys.stderr)
        return 3
    except HoleCountError as e:
        print(f"python.py: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
