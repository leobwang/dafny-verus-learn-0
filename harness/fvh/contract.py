"""fvh.contract — the CONTRACT-header parser, the allowlist validation and the
acceptance-line forms (DV4-PLAN §6; Δ149, Δ162).

The same rules as `.claude/skills/contract/SKILL.md` §1–§2 and as
scripts/dvl/contract_local.py (a core test holds the two to the same results
on the same cases, and this table of refused source classes to
scripts/dvl/sandbox.py's):

  parse_header(text) -> {"goal": str, "allowed-files": [...], "acceptance": [...]}
      line 1 opens the header (`/* CONTRACT` in a .dfy or .rs file, a module
      docstring that opens with CONTRACT in a .py file); exactly the three keys, each list non-empty; anything
      else raises Refused naming what is wrong
  path_problem(path, record) -> str | None
      why an allowed-files path is refused: not repo-relative, not in the
      module's agentic list, a frozen, solo, guard, reference, build or
      run-record path (research/runs/**, research/ledger-heads.jsonl), the
      benchmark manifest or a public set, or a refused source class
  classify_line(line) -> (form, detail)
      vcheck-gate, zero-holes, specfreeze-against, vaudit, vaudit-compare
      (checked in the verification container), git-diff (its evidence is
      patch.diff) or audit (the learner's)
  starting_state(root, contract, from_rev) -> (rev, snapshot or None)
      the commit that last changed the snapshot a `scripts/specfreeze
      --against <snapshot> <file>` line names, or --from's commit; Refused
      when neither exists, the snapshot is missing, untracked or modified,
      or an allowed file did not exist at that commit
  record(root, module) -> the module's registry record (MODULES.toml)

Frozen (guard rule 2f), standard library only.
"""

import re
import subprocess
import tomllib
from pathlib import Path, PurePosixPath

__all__ = ["FORMS", "KEYS", "REFUSED_CLASSES", "Refused", "agentic_ok", "classify_line",
           "parse_header", "path_problem", "record", "rel_ok", "source_class",
           "starting_state"]

KEYS = ("goal", "allowed-files", "acceptance")
FORMS = ("vcheck-gate", "zero-holes", "specfreeze-against", "vaudit", "vaudit-compare",
         "git-diff", "audit")
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
# scripts/dvl/sandbox.py's REFUSED_CLASSES (a core test keeps the two equal)
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


class Refused(Exception):
    """A contract, a path or a starting state that is refused (exit 3)."""


def rel_ok(p) -> bool:
    """A repo-relative path: no leading /, no ./ or .. segment, no glob."""
    if not isinstance(p, str) or not p or p.startswith("/") or "\\" in p or "\0" in p:
        return False
    parts = p.split("/")
    if any(x in ("", ".", "..") for x in parts):
        return False
    return not any(ch in p for ch in "*?[]")


def source_class(rel: str) -> str | None:
    for cls, kind, pat in REFUSED_CLASSES:
        if kind == "prefix" and (rel == pat.rstrip("/") or rel.startswith(pat)):
            return cls
        if kind == "component" and pat in rel.split("/"):
            return cls
        if kind == "regex" and re.search(pat, rel):
            return cls
    return None


def agentic_ok(rel: str, rec) -> bool:
    for a in rec.get("agentic", []):
        if rel == a or (a.endswith("/") and rel.startswith(a)):
            return True
    return False


def parse_header(text: str) -> dict:
    """The CONTRACT header that opens line 1 (module docstring)."""
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


def path_problem(p: str, rec) -> str | None:
    """Why an allowed-files path is refused (module docstring), or None."""
    if not rel_ok(p):
        return "not a repo-relative path (no leading / or ./, no .., no glob)"
    if not agentic_ok(p, rec):
        return f"not in {rec['id']}'s agentic list"
    if p in FORBIDDEN_EXACT or p.startswith(FORBIDDEN_PREFIXES):
        return "a frozen, solo, guard, reference or run-record path"
    parts = p.split("/")
    if "given" in parts or ".cargo" in parts or PurePosixPath(p).name in FORBIDDEN_NAMES \
            or p.endswith(".pth"):
        return "a frozen, guard or build-configuration path"
    if re.search(r"(^|/)[^/]*trust[-_]report", p) and p.startswith(("dafny/R/", "verus/r/",
                                                                    "harness/r/")):
        return "R16's trust-report (solo work)"
    if re.match(r"^harness/q/[^/]+/gate(/|\.py$)", p):
        return "Q's gate (solo work)"
    if source_class(p) and not p.startswith("research/"):
        return f"in a refused source class ({source_class(p)})"
    return None


def classify_line(line: str) -> tuple[str, str]:
    """(form, detail) of one acceptance line (module docstring)."""
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


def record(root, module: str) -> dict:
    """The module's registry record (Refused when the registry or the id is unusable)."""
    try:
        data = tomllib.loads((Path(root) / "MODULES.toml").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise Refused(f"the registry is unusable ({type(e).__name__})") from None
    for m in data.get("module", []):
        if isinstance(m, dict) and str(m.get("id", "")).upper() == str(module).upper():
            return m
    raise Refused(f"module {module!r} is not in MODULES.toml")


def _git(root, *args):
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                       timeout=60)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def starting_state(root, contract: dict, from_rev: str | None = None) -> tuple[str, str | None]:
    """(rev, snapshot path or None): the commit the replay starts from."""
    snaps = [d for f, d in (classify_line(x) for x in contract["acceptance"])
             if f == "specfreeze-against"]
    if len(set(snaps)) > 1:
        raise Refused(f"the CONTRACT names more than one snapshot ({sorted(set(snaps))})")
    snap = snaps[0] if snaps else None
    if from_rev:
        rc, rev, _ = _git(root, "rev-parse", "--verify", "--quiet", f"{from_rev}^{{commit}}")
        if rc != 0:
            raise Refused(f"--from {from_rev} is not a commit")
    elif snap:
        if not (Path(root) / snap).is_file():
            raise Refused(f"the snapshot {snap} that the CONTRACT names is missing")
        rc, _, _ = _git(root, "ls-files", "--error-unmatch", "--", snap)
        if rc != 0:
            raise Refused(f"the snapshot {snap} is not tracked: commit it before the /contract run, "
                          "so its commit marks the starting state")
        rc, out, _ = _git(root, "status", "--porcelain", "--", snap)
        if out:
            raise Refused(f"the snapshot {snap} differs from its committed version (git show "
                          f"HEAD:{snap}): commit or restore it")
        rc, rev, _ = _git(root, "log", "-1", "--format=%H", "--", snap)
        if rc != 0 or not rev:
            raise Refused(f"no commit changed {snap}")
    else:
        raise Refused("the CONTRACT names no snapshot in a `scripts/specfreeze --against <snapshot> "
                      "<file>` acceptance line and no --from <rev> was given: the starting state is "
                      "never guessed")
    for p in contract["allowed-files"]:
        rc, out, _ = _git(root, "ls-tree", rev, "--", p)
        if rc != 0 or not out:
            raise Refused(f"{p} did not exist at the starting commit {rev[:12]}")
    if snap and from_rev:
        rc, out, _ = _git(root, "ls-tree", rev, "--", snap)
        if rc != 0 or not out:
            raise Refused(f"the snapshot {snap} did not exist at --from {from_rev}")
    return rev, snap
