"""dvl.bench: the benchmark fetcher behind scripts/get_bench.sh (DV4-PLAN §7).

bench/manifest.toml (frozen, guard rule 2f) holds one [[set]] per benchmark:
its repository and full commit, its licence and its upstream sources' licences
as checked, its mode (`fetch` or `vendor`), the DV5 leak scan that a vendored
set needs, the layout map that turns the upstream tree into tasks/ and
answers/, the licence and notice files kept verbatim (with their sha256), and
the tree digest of the normalized set (written by the author-only --pin).

    get_bench.sh SET...            fetch the pinned commit (never a branch),
                                   check it, normalize, compare the digest,
                                   install into bench/public/SET/ (idempotent)
    get_bench.sh --all             every set
    get_bench.sh --check [SET...]  offline: re-compute installed sets' digests,
                                   their licence and notice files
    get_bench.sh --list            the sets, licences, modes, install state
    get_bench.sh --validate SET [--only NAME...] [--sample N --seed S]
                 [--workers N --mem-gb SHARE] [--restart]
                                   each answer through scripts/vcheck --gate
                                   --json and scripts/vaudit --json in a
                                   scratch copy (one solver job at a time by
                                   default), and each task form must fail the
                                   gate as shipped; resumable (rows go to
                                   SET/validation.partial.jsonl as they finish,
                                   and a re-run of the same command continues),
                                   stoppable (SIGINT/SIGTERM keep the finished
                                   rows); writes SET/validation.jsonl
    get_bench.sh --pin-pool SET... author-only: record a finished validation's
                                   pool (its members, their sha256, the counts)
                                   in bench/public/POOLS.toml, which --check
                                   compares with an installed validation.jsonl
    get_bench.sh --pin SET...      author-only (Δ103's three-condition test,
                                   guard rule 1b): fetch, normalize and write
                                   the set's tree digest into the manifest

A set installs only when everything matches: the fetched commit equals the
pin, every licence and notice file equals its recorded sha256, and the
normalized tree's digest equals the manifest's; any difference refuses (exit
3) and installs nothing. The licence rule (§7.2, P7): `vendor` only when the
repository and every recorded upstream are MIT or Apache-2.0 and `leak_scan`
names DV5's scan; every set starts as `fetch`, and a fetch set's directory
must be ignored by git (it is never committed).

Exit codes: 0 done, 1 a step failed (network, a solver job), 2 usage, 3 refused.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from dvl import benchstrip  # noqa: E402

SCHEMA = 1
MODES = ("fetch", "vendor")
VENDOR_LICENCES = ("MIT", "Apache-2.0")
SET_KEYS = {"name", "title", "repo", "commit", "licence", "upstream", "mode", "leak_scan",
            "layout", "keep", "subset", "sha256", "notes"}
LAYOUT_KEYS = {"from", "to", "glob", "strip_suffix", "recursive", "transform"}
KEEP_KEYS = {"path", "sha256", "kind"}
NOT_DIGESTED = ("validation.jsonl", "validation.partial.jsonl", "answers/DVLCANARY")
# The canary of a set's answers (DV4-PLAN §5.4 item 2, §14 Q5; the DV5c gaps lane): a
# file answers/DVLCANARY whose first line is a token derived from the set's name and
# pinned commit, so sandbox/canaries.sha256 can list its hash without a secret and the
# sandbox self-test names the set when a staged file carries it. Not digested.
CANARY_FILE = "DVLCANARY"
CANARY_PREFIX = "DVLCANARY" + "-"


def canary_token(s):
    h = hashlib.sha256(f"{s['name']}\0{s['commit']}".encode()).hexdigest()[:32]
    return f"{CANARY_PREFIX}bench-{s['name']}-{h}"


def canary_line(s):
    """The set's line of sandbox/canaries.sha256."""
    return f"{hashlib.sha256(canary_token(s).encode()).hexdigest()}  bench/public/{s['name']}/answers/"


def plant_canary(root, s):
    """Write answers/DVLCANARY into an installed set that has answers/ (idempotent)."""
    d = set_dir(root, s["name"]) / "answers"
    if not d.is_dir():
        return False
    body = (canary_token(s) + "\n"
            f"This file marks bench/public/{s['name']}/answers/ for the sandbox self-test "
            "(DV4-PLAN §5.4 item 2).\nscripts/get_bench.sh writes it; it is not part of the "
            "set's digest. Keep it in place.\n")
    f = d / CANARY_FILE
    if not f.is_file() or f.read_text(encoding="utf-8") != body:
        f.write_text(body, encoding="utf-8")
    return True
SOLVER_EXT = {".dfy": "dafny", ".rs": "verus"}


class Refused(Exception):
    """Exit 3."""


class Failed(Exception):
    """Exit 1."""


def say(msg, err=False):
    print(f"get_bench: {msg}", file=sys.stderr if err else sys.stdout, flush=True)


# --- the manifest --------------------------------------------------------------------------

def load_manifest(root):
    path = Path(root) / "bench" / "manifest.toml"
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise Refused(f"{path} does not exist") from None
    except (OSError, ValueError) as e:
        raise Refused(f"bench/manifest.toml is unusable: {e}") from None
    if data.get("schema") != SCHEMA:
        raise Refused(f"bench/manifest.toml: schema must be {SCHEMA}")
    sets, problems = {}, []
    for s in data.get("set", []):
        name = s.get("name", "?")
        problems += [f"{name}: {p}" for p in set_problems(s)]
        if name in sets:
            problems.append(f"{name}: listed twice")
        sets[name] = s
    if problems:
        raise Refused("bench/manifest.toml: " + "; ".join(problems))
    return data, sets


def set_problems(s):
    out = []
    unknown = sorted(set(s) - SET_KEYS)
    if unknown:
        out.append(f"unknown key(s) {unknown}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", str(s.get("name", ""))):
        out.append("name must be lower-case [a-z0-9_-]")
    if not re.fullmatch(r"(https://|file://)\S+", str(s.get("repo", ""))):
        out.append("repo must be an https:// (or, in tests, file://) URL")
    if not re.fullmatch(r"[0-9a-f]{40}", str(s.get("commit", ""))):
        out.append("commit must be a full 40-hex sha (never a branch)")
    lic = s.get("licence")
    if not isinstance(lic, dict) or not lic.get("spdx") or not lic.get("checked") or not lic.get("method"):
        out.append("licence must record spdx, checked (a date) and method")
    if s.get("mode") not in MODES:
        out.append(f"mode must be one of {list(MODES)}")
    ups = s.get("upstream", [])
    if not isinstance(ups, list) or any(not isinstance(u, dict) or "licence" not in u for u in ups):
        out.append("upstream must be a list of tables, each with a licence")
    if s.get("mode") == "vendor":
        out += vendor_problems(s)
    for row in s.get("layout", []):
        unknown = sorted(set(row) - LAYOUT_KEYS)
        if unknown:
            out.append(f"layout row {row.get('from')}: unknown key(s) {unknown}")
        if not row.get("from") or not row.get("to") or not str(row.get("to")).startswith(("tasks", "answers")):
            out.append(f"layout row {row.get('from')}: needs from and to (under tasks/ or answers/)")
        for k in ("from", "to"):
            if ".." in str(row.get(k, "")).split("/") or str(row.get(k, "")).startswith("/"):
                out.append(f"layout row {row.get('from')}: {k} must stay inside the set")
        if "transform" in row and row["transform"] not in benchstrip.TRANSFORMS:
            out.append(f"layout row {row.get('from')}: unknown transform {row['transform']!r} "
                       f"(known: {sorted(benchstrip.TRANSFORMS)})")
    keeps = s.get("keep", [])
    if not keeps:
        out.append("keep must list the upstream licence file (kept verbatim)")
    for k in keeps:
        if set(k) - KEEP_KEYS or not k.get("path") or "/" in k.get("path", "") \
                or not re.fullmatch(r"[0-9a-f]{64}", str(k.get("sha256", ""))):
            out.append(f"keep {k.get('path')}: a top-level path and its sha256")
    sub = s.get("subset")
    if sub is not None and (not isinstance(sub, dict) or not {"index", "key", "by"} <= set(sub)
                            or set(sub) - {"index", "key", "by", "exclude"}):
        out.append("subset must be {index, key, by, exclude}")
    if s.get("sha256") and not re.fullmatch(r"[0-9a-f]{64}", s["sha256"]):
        out.append("sha256 must be empty (not pinned yet) or 64 hex digits")
    return out


def vendor_problems(s):
    out = []
    lic = (s.get("licence") or {}).get("spdx")
    if lic not in VENDOR_LICENCES:
        out.append(f"vendor needs an MIT or Apache-2.0 repository, not {lic}")
    for u in s.get("upstream", []):
        if u.get("licence") not in VENDOR_LICENCES:
            out.append(f"vendor needs every upstream MIT or Apache-2.0; {u.get('what', '?')} is "
                       f"{u.get('licence')!r}")
    if not s.get("upstream"):
        out.append("vendor needs the upstream sources recorded")
    if not s.get("leak_scan"):
        out.append("vendor needs leak_scan to name DV5's scan of the set's answers")
    return out


# --- fetching and normalizing ----------------------------------------------------------------

def git_env(home):
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home), "LANG": "C.UTF-8",
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "/bin/false"}


def fetch(s, tmp):
    """A checkout of exactly the pinned commit (a shallow fetch by sha)."""
    co = Path(tmp) / "checkout"
    env = git_env(tmp)

    def git(*args, timeout=600):
        p = subprocess.run(["git", "-C", str(co), *args], capture_output=True, text=True, env=env,
                           timeout=timeout)
        if p.returncode != 0:
            raise Failed(f"git {args[0]} failed: {(p.stderr.strip().splitlines() or ['?'])[-1]}")
        return p.stdout.strip()

    co.mkdir()
    git("init", "-q")
    try:
        git("fetch", "-q", "--depth", "1", "--no-tags", s["repo"], s["commit"])
    except subprocess.TimeoutExpired:
        raise Failed(f"fetching {s['repo']} timed out") from None
    got = git("rev-parse", "FETCH_HEAD^{commit}")
    if got != s["commit"]:
        raise Refused(f"{s['name']}: the fetched commit is {got}, not the pinned {s['commit']}")
    git("-c", "advice.detachedHead=false", "checkout", "-q", "--detach", "FETCH_HEAD")
    if git("rev-parse", "HEAD") != s["commit"]:
        raise Refused(f"{s['name']}: the checkout is not the pinned commit")
    return co


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _map_name(name, strip):
    if not strip:
        return name
    p = PurePosixPath(name)
    stem, suffix = p.name[:-len(p.suffix)] if p.suffix else p.name, p.suffix
    if stem.endswith(strip):
        stem = stem[:-len(strip)]
    return stem + suffix


def normalize(s, co, stage):
    """Copy the layout map's files (contents unchanged, or through the row's
    transform, dvl.benchstrip) and the kept licence and notice files into
    `stage`; write SOURCE.toml and CHANGES. Returns the counts of task and
    answer files (and, per layout row, of files a transform changed)."""
    stage.mkdir(parents=True)
    counts = {"tasks": 0, "answers": 0, "excluded": 0, "transformed": {}}
    placed = {}
    excluded = subset_exclusions(s, co)
    for ri, row in enumerate(s.get("layout", [])):
        src = co / row["from"]
        if src.is_symlink():
            raise Refused(f"{s['name']}: layout source {row['from']} is a symlink")
        if src.is_file():
            pairs = [(src, row["to"])]
        elif src.is_dir():
            pat = row.get("glob", "*")
            walk = sorted(src.rglob("*")) if row.get("recursive") else sorted(src.iterdir())
            pairs = []
            for f in walk:
                if f.is_symlink() or not f.is_file() or not fnmatch.fnmatch(f.name, pat):
                    continue
                rel = f.relative_to(src).as_posix()
                rel = str(PurePosixPath(rel).parent / _map_name(f.name, row.get("strip_suffix")))
                rel = rel[2:] if rel.startswith("./") else rel
                pairs.append((f, f"{row['to']}/{rel}"))
        else:
            raise Refused(f"{s['name']}: layout source {row['from']} is not in the pinned tree")
        for f, to in pairs:
            if PurePosixPath(to).stem in excluded:
                counts["excluded"] += 1
                continue
            if to in placed:
                raise Refused(f"{s['name']}: {to} would come from both {placed[to]} and "
                              f"{f.relative_to(co)}")
            placed[to] = f.relative_to(co).as_posix()
            dest = stage / to
            dest.parent.mkdir(parents=True, exist_ok=True)
            if row.get("transform"):
                try:
                    data, changed = benchstrip.apply(row["transform"], to, f.read_bytes())
                except (benchstrip.StripError, UnicodeDecodeError) as e:
                    raise Refused(f"{s['name']}: the transform {row['transform']} cannot read "
                                  f"{f.relative_to(co)}: {e}") from None
                dest.write_bytes(data)
                counts["transformed"][ri] = counts["transformed"].get(ri, 0) + int(changed)
            else:
                shutil.copyfile(f, dest)
            counts[to.split("/", 1)[0]] += 1
    for k in s.get("keep", []):
        src = co / k["path"]
        if src.is_symlink() or not src.is_file():
            raise Refused(f"{s['name']}: the kept file {k['path']} is missing upstream")
        if sha256_file(src) != k["sha256"]:
            raise Refused(f"{s['name']}: {k['path']} differs from its recorded sha256 (the licence "
                          "or notice changed upstream: re-check it before re-pinning)")
        shutil.copyfile(src, stage / k["path"])
    (stage / "SOURCE.toml").write_text(source_toml(s), encoding="utf-8")
    (stage / "CHANGES").write_text(changes_text(s, counts), encoding="utf-8")
    return counts


def subset_exclusions(s, co):
    """The keys (file stems after the layout's renaming) that the set's subset
    leaves out: rows of its index file whose `by` column is in `exclude`."""
    sub = s.get("subset")
    if not sub:
        return set()
    import csv
    idx = co / sub["index"]
    if idx.is_symlink() or not idx.is_file():
        raise Refused(f"{s['name']}: the subset index {sub['index']} is not in the pinned tree")
    with open(idx, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows or sub["key"] not in rows[0] or sub["by"] not in rows[0]:
        raise Refused(f"{s['name']}: the subset index lacks the columns {sub['key']!r} and {sub['by']!r}")
    drop = set(sub.get("exclude", []))
    return {r[sub["key"]] for r in rows if r[sub["by"]] in drop}


def _q(v):
    return json.dumps(v, ensure_ascii=False)


def source_toml(s):
    lic = s["licence"]
    out = ["# Generated by scripts/get_bench.sh from bench/manifest.toml; not edited by hand.",
           f"name = {_q(s['name'])}", f"repo = {_q(s['repo'])}", f"commit = {_q(s['commit'])}",
           f"mode = {_q(s['mode'])}", f"licence = {_q(lic['spdx'])}",
           f"licence_checked = {_q(lic['checked'])}", f"licence_method = {_q(lic['method'])}", ""]
    for u in s.get("upstream", []):
        out += ["[[upstream]]"] + [f"{k} = {_q(v)}" for k, v in sorted(u.items())] + [""]
    return "\n".join(out)


def changes_text(s, counts):
    transforms = any(row.get("transform") for row in s.get("layout", []))
    out = [f"Changes made by scripts/get_bench.sh when it normalized {s['name']}",
           f"(upstream {s['repo']} at {s['commit']}).", "",
           "This notice is the change statement that the upstream licence asks for (Apache-2.0",
           "section 4(b), where it applies)."
           + (" File contents are copied unchanged, except where a line below names a"
              if transforms else " File contents are copied unchanged; only file"),
           ("transform (scripts/dvl/benchstrip.py); file locations and names change as follows:"
            if transforms else "locations and names change, as follows:"), ""]
    for ri, row in enumerate(s.get("layout", [])):
        line = f"- {row['from']}"
        if row.get("glob"):
            line += f"/{row['glob']}" + (" (recursively)" if row.get("recursive") else "")
        line += f" -> {row['to']}"
        if row.get("strip_suffix"):
            line += f" (the suffix {row['strip_suffix']!r} removed from each file name)"
        if row.get("transform"):
            n = counts.get("transformed", {}).get(ri, 0)
            line += (f"; transform {row['transform']}: "
                     f"{benchstrip.TRANSFORM_NOTES[row['transform']]} ({n} file(s) changed)")
        out.append(line)
    for k in s.get("keep", []):
        out.append(f"- {k['path']} -> {k['path']} (verbatim)")
    sub = s.get("subset")
    if sub:
        out.append(f"- left out by the subset: {counts['excluded']} file(s) whose {sub['by']!r} in "
                   f"{sub['index']} is one of {sorted(sub.get('exclude', []))}")
    out += ["", "Every other upstream file is left out.",
            f"Result: {counts['tasks']} task file(s), {counts['answers']} answer file(s).", ""]
    return "\n".join(out)


def tree_digest(top):
    """sha256 over 'path<TAB>sha256' lines of every file (sorted), except
    validation.jsonl."""
    top = Path(top)
    lines = []
    for p in sorted(top.rglob("*")):
        if p.is_symlink():
            raise Refused(f"{p} is a symlink inside an installed set")
        if not p.is_file():
            continue
        rel = p.relative_to(top).as_posix()
        if rel in NOT_DIGESTED:
            continue
        lines.append(f"{rel}\t{sha256_file(p)}\n")
    return hashlib.sha256("".join(lines).encode()).hexdigest()


def set_dir(root, name):
    return Path(root) / "bench" / "public" / name


def ignored_by_git(root, rel):
    """True/False when root is a git checkout, None otherwise."""
    p = subprocess.run(["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        return None
    q = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", "--no-index", rel],
                       capture_output=True, text=True)
    return q.returncode == 0


def check_installed(root, s):
    """Problems (strings) of an installed set; [] when it matches the manifest."""
    d = set_dir(root, s["name"])
    out = []
    for k in s.get("keep", []):
        p = d / k["path"]
        if not p.is_file():
            out.append(f"the kept file {k['path']} is missing")
        elif sha256_file(p) != k["sha256"]:
            out.append(f"the kept file {k['path']} differs from its recorded sha256")
    for f in ("SOURCE.toml", "CHANGES"):
        if not (d / f).is_file():
            out.append(f"{f} is missing")
    if not s.get("sha256"):
        out.append("the manifest pins no digest yet (the author runs get_bench.sh --pin)")
    elif tree_digest(d) != s["sha256"]:
        out.append("its tree digest differs from the manifest's")
    return out


# --- the commands --------------------------------------------------------------------------

def install(root, s, *, pin=False):
    name = s["name"]
    if s["mode"] == "vendor" and vendor_problems(s):
        raise Refused(f"{name}: " + "; ".join(vendor_problems(s)))
    dest = set_dir(root, name)
    if s["mode"] == "fetch":
        ign = ignored_by_git(root, f"bench/public/{name}/SOURCE.toml")
        if ign is False:
            raise Refused(f"{name} is a fetch set, so its directory bench/public/{name}/ must be "
                          "ignored by git (a fetch set is never committed): add it to .gitignore")
    if not pin and not s.get("sha256"):
        raise Refused(f"{name}: the manifest pins no digest yet; the author runs "
                      f"scripts/get_bench.sh --pin {name} first")
    if not pin and dest.is_dir() and not check_installed(root, s):
        say(f"{name}: already installed and current ({s['sha256'][:16]})")
        plant_canary(root, s)
        return s.get("sha256")
    tmp = Path(tempfile.mkdtemp(prefix=f"dvl-bench-{name}-", dir=tmp_base()))
    try:
        say(f"{name}: fetching {s['repo']} at {s['commit'][:12]}")
        co = fetch(s, tmp)
        stage = tmp / "stage"
        counts = normalize(s, co, stage)
        digest = tree_digest(stage)
        if not pin and digest != s["sha256"]:
            raise Refused(f"{name}: the normalized tree's digest {digest[:16]} differs from the "
                          f"manifest's {s['sha256'][:16]}; nothing installed")
        dest.parent.mkdir(parents=True, exist_ok=True)
        new = dest.parent / f".{name}.new"
        old = dest.parent / f".{name}.old"
        for p in (new, old):
            shutil.rmtree(p, ignore_errors=True)
        shutil.copytree(stage, new)
        if dest.exists():
            dest.rename(old)
        new.rename(dest)
        plant_canary(root, s)
        shutil.rmtree(old, ignore_errors=True)
        say(f"{name}: installed into bench/public/{name}/ ({counts['tasks']} task file(s), "
            f"{counts['answers']} answer file(s); digest {digest[:16]})")
        return digest
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def write_pin(root, name, digest):
    path = Path(root) / "bench" / "manifest.toml"
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^(?=\[\[set\]\]\s*$)", text)
    done = False
    for i, b in enumerate(blocks):
        head, sep, tail = b.partition("\n[[set.")      # the set's own keys come first
        if re.search(rf'(?m)^name\s*=\s*"{re.escape(name)}"\s*$', head):
            nh, n = re.subn(r'(?m)^sha256\s*=\s*"[0-9a-f]*"\s*$', f'sha256 = "{digest}"', head, count=1)
            if n != 1:
                raise Refused(f"{name}: its [[set]] has no top-level sha256 line to write")
            blocks[i], done = nh + sep + tail, True
    if not done:
        raise Refused(f"{name} is not in bench/manifest.toml")
    path.write_text("".join(blocks), encoding="utf-8")


def tmp_base():
    """Where get_bench.sh makes its temporary trees: $DVL_BENCH_TMP, else /tmp
    (an author lane points it at its own scratch)."""
    base = os.environ.get("DVL_BENCH_TMP") or "/tmp"
    Path(base).mkdir(parents=True, exist_ok=True)
    return base


def mem_available_gb():
    """MemAvailable in whole GiB, for the run's report only (DELTAS Δ503, D78: the
    course applies no memory management; memory is the host's and the user's)."""
    from dvl import host as plat
    return plat.mem_available_gb()


# --- --validate ----------------------------------------------------------------------------------
#
# A row per answer file. The pool rule (DV4-PLAN §7.2, QPLAN §22.6): the answer
# passes the course's done check (`vcheck --gate`: verified, 0 holes; and
# `vaudit`: no finding); taken as a delivery for its task form it passes the
# lab gate's static half (`specfreeze --lab TASK ANSWER`: no statement changed
# or missing, no lever added or dropped), so it shows the task is solvable as
# posed; and its task form, delivered unchanged, fails the lab gate
# (`vcheck --gate`; the lever check finds nothing on an unchanged file), at the
# verify stage (a task form that does not parse or resolve poses no task). An answer byte-equal to its task file (a shared support file, or a task
# with nothing removed) is not a task: reason `answer-equals-task-form`.
# Jobs killed by memory (137/143) or by the wall-clock net (124), and jobs with
# no JSON document (`no-json`), are never verdicts: their rows are re-run by
# the next invocation (also after a finished run: it continues from
# validation.jsonl). A tool's own `error` verdict is a result.

VALIDATION_SCHEMA = 3
RETRY = ("killed(memory)", "timeout", "no-json")
WORKERS_MAX = 4
MEM_WAIT_S = 1800


def pins_digest():
    from dvl import common
    return hashlib.sha256(json.dumps(common.load_pins(), sort_keys=True, default=str)
                          .encode()).hexdigest()


def strata_of(root, s, rels):
    """{rel: stratum}: `<language>/<source>` from the subset index when the set
    has one (vericoding), else the language by suffix."""
    d = set_dir(root, s["name"])
    by = {}
    sub = s.get("subset")
    if sub:
        import csv
        idx = d / "tasks" / PurePosixPath(sub["index"]).name
        if idx.is_file():
            with open(idx, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    by[r.get(sub["key"], "")] = f"{r.get('language', '?')}/{r.get(sub['by'], '?')}"
    out = {}
    for rel in rels:
        lang = SOLVER_EXT.get(PurePosixPath(rel).suffix, "?")
        out[rel] = by.get(PurePosixPath(rel).stem, lang)
    return out


def stratified_sample(strata, n, seed):
    """A seeded random sample of n rows, allocated to strata in proportion to
    their sizes (largest remainder; every stratum at least one row when n
    allows). Returns (sorted rows, {stratum: [size, drawn]})."""
    import random
    groups = {}
    for rel, k in sorted(strata.items()):
        groups.setdefault(k, []).append(rel)
    total = sum(len(v) for v in groups.values())
    n = min(n, total)
    keys = sorted(groups)
    quota = {k: n * len(groups[k]) / total for k in keys}
    alloc = {k: int(quota[k]) for k in keys}
    if n >= len(keys):
        for k in keys:
            alloc[k] = max(alloc[k], 1)
    frac = {k: quota[k] - int(quota[k]) for k in keys}
    while sum(alloc.values()) < n:
        k = min((k for k in keys if alloc[k] < len(groups[k])), key=lambda k: (-frac[k], k))
        alloc[k] += 1
        frac[k] = -1.0
    while sum(alloc.values()) > n:
        k = min((k for k in keys if alloc[k] > 1), key=lambda k: (frac[k], -alloc[k], k))
        alloc[k] -= 1
        frac[k] = 2.0
    drawn = []
    for k in keys:
        rng = random.Random(f"{seed}:{k}")
        take = min(alloc[k], len(groups[k]))
        drawn += rng.sample(groups[k], take)
        alloc[k] = take
    return sorted(drawn), {k: [len(groups[k]), alloc[k]] for k in keys}


class _Stop(Exception):
    pass


class _Runner:
    """Runs scripts/vcheck and scripts/vaudit as child processes it can stop."""

    def __init__(self, root, scratch, share_gb, workers=1):
        import threading
        self.workers = workers
        self.root = Path(root)
        self.scratch = scratch
        self.share_gb = share_gb
        self.procs = set()
        self.lock = threading.Lock()
        self.stop = threading.Event()

    def cap(self, pool):
        from dvl import common
        return float(common.load_pins().get(pool, {}).get("mem_gb", 8))

    def wait_memory(self, pool):
        """No memory gate (D78): only a stop request ends the wait."""
        if self.stop.is_set():
            raise _Stop()

    def run(self, tool, target, pool, *, gate=False):
        if self.stop.is_set():
            raise _Stop()
        self.wait_memory(pool)
        argv = [sys.executable, "-B", str(self.root / "scripts" / tool)]
        argv += (["--gate"] if gate else []) + ["--json", str(target)]
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        env.update({"DVL_DAFNY_JOBS": str(self.workers), "DVL_VERUS_JOBS": str(self.workers),
                    "DVL_SCRATCH": str(self.scratch / "dvl")})
        t0 = time.monotonic()
        p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                             env=env)
        with self.lock:
            self.procs.add(p)
        try:
            out, _ = p.communicate()
        finally:
            with self.lock:
                self.procs.discard(p)
        secs = round(time.monotonic() - t0, 1)
        if self.stop.is_set() and p.returncode != 0:
            raise _Stop()
        code = p.returncode
        try:
            doc = json.loads(out)
        except ValueError:
            doc = None
        if isinstance(doc, list):
            doc = doc[0] if doc else {}
        if not isinstance(doc, dict):
            verdict = {137: "killed(memory)", 143: "killed(memory)", -9: "killed(memory)",
                       -15: "killed(memory)", 124: "timeout"}.get(code, "no-json")
            return {"verdict": verdict, "exit_code": code, "seconds": secs}
        raw = doc.get("raw_dir")
        if raw:
            try:
                Path(raw).resolve().relative_to(self.scratch.resolve())
                shutil.rmtree(raw, ignore_errors=True)
            except ValueError:
                pass
        if tool == "vaudit":
            found = [f for f in doc.get("findings", []) if isinstance(f, dict)]
            kinds = sorted({f.get("kind", "?") for f in found})
            out = {"findings": len(found), "kinds": kinds, "exit_code": code, "seconds": secs}
            verdict = audit_run_verdict(found)
            if verdict:
                out["verdict"] = verdict          # a run that did not complete: RETRY
            return out
        diags = doc.get("diagnostics", [])
        if code in (124, 137, 143) and doc.get("verdict") != "verified":
            verdict = "timeout" if code == 124 else "killed(memory)"
        else:
            verdict = doc.get("verdict")
        return {"verdict": verdict, "stage": doc.get("stage"), "exit_code": code,
                "holes": len(doc.get("holes", [])),
                "errors": sum(1 for x in diags if x.get("severity") == "error"),
                "findings": sorted({f.get("kind", "?") for f in doc.get("findings", [])}),
                "verified": doc.get("verified_count"), "seconds": secs}

    def static(self, task, answer):
        """The lab gate's static half on (task form, answer): no solver runs."""
        if self.stop.is_set():
            raise _Stop()
        argv = [sys.executable, "-B", str(self.root / "scripts" / "specfreeze"), "--lab",
                str(task), str(answer), "--json"]
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        env["DVL_SCRATCH"] = str(self.scratch / "dvl")
        t0 = time.monotonic()
        p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                             env=env)
        with self.lock:
            self.procs.add(p)
        try:
            out, _ = p.communicate()
        finally:
            with self.lock:
                self.procs.discard(p)
        if self.stop.is_set() and p.returncode != 0:
            raise _Stop()
        try:
            doc = json.loads(out)
        except ValueError:
            return {"verdict": "no-json", "exit_code": p.returncode,
                    "seconds": round(time.monotonic() - t0, 1)}
        found = doc.get("findings", []) if isinstance(doc, dict) else []
        return {"findings": len(found), "kinds": sorted({f.get("kind", "?") for f in found}),
                "exit_code": p.returncode, "seconds": round(time.monotonic() - t0, 1)}

    def kill_all(self):
        import signal as _signal
        with self.lock:
            procs = list(self.procs)
        for p in procs:
            try:
                p.send_signal(_signal.SIGTERM)
            except OSError:
                pass


# The audit's own "did not complete" kinds (dvl.dafny.audit's audit-error,
# dvl.verus.audit's audit-incomplete), read as scripts/vcheck's lab gate reads
# them: an audit killed by memory or stopped by the wall clock is no verdict
# (CLAUDE.md §Resources), so its row is retried, never excluded.
AUDIT_INCOMPLETE = ("audit-error", "audit-incomplete")


def audit_run_verdict(findings):
    """'killed(memory)' or 'timeout' when an assumption audit's findings say
    its run did not complete for memory or time; else None."""
    msgs = [str(f.get("message", "")) for f in findings
            if isinstance(f, dict) and f.get("kind") in AUDIT_INCOMPLETE]
    if any("killed(memory)" in m for m in msgs):
        return "killed(memory)"
    if any("(inconclusive" in m or "wall-clock" in m for m in msgs):
        return "timeout"
    return None


def judge_row(row):
    """Fill row['pool'] and row['reason'] from its job results."""
    a, au, tf = row.get("answer"), row.get("answer_audit"), row.get("task_form")
    ls = row.get("lab_static")
    reason = None
    for part in (a, au, ls, tf):
        if part and part.get("verdict") in RETRY:
            reason = f"retry:{part['verdict']}"
            break
    if reason is None:
        if row.get("support"):
            reason = "answer-equals-task-form"
        elif not a or a.get("verdict") != "verified":
            reason = "answer-not-verified"
        elif a.get("holes"):
            reason = "answer-holes"
        elif not au or au.get("findings") or au.get("exit_code") != 0:
            reason = "answer-audit:" + (",".join(au.get("kinds", [])) or f"exit {au.get('exit_code')}"
                                        if au else "missing")
        elif row.get("task_missing"):
            reason = "no-task-form"
        elif ls is None or ls.get("findings") or ls.get("exit_code") != 0:
            reason = "answer-fails-lab-static:" + (",".join((ls or {}).get("kinds", []))
                                                   or f"exit {(ls or {}).get('exit_code')}")
        elif tf is None:
            reason = "no-task-form"
        elif tf.get("stage") in ("cli", "parse", "resolve"):
            reason = "task-form-does-not-resolve"
        elif tf.get("verdict") == "verified" and not tf.get("holes"):
            reason = "task-form-passes-the-gate"
    row["pool"] = reason is None
    row["reason"] = reason
    return row


def validate_row(runner, d, scratch, rel, stratum):
    """The jobs of one answer, in order, stopping at the first that settles it."""
    lang = SOLVER_EXT[PurePosixPath(rel).suffix]
    a_path, t_path = scratch / "answers" / rel, scratch / "tasks" / rel
    row = {"task": rel, "stratum": stratum}
    t0 = time.monotonic()
    if t_path.is_file() and a_path.read_bytes() == t_path.read_bytes():
        row["support"] = True
        return judge_row(row)
    row["answer"] = runner.run("vcheck", a_path, lang, gate=True)
    if row["answer"].get("verdict") == "verified" and not row["answer"].get("holes"):
        row["answer_audit"] = runner.run("vaudit", a_path, lang)
        if not row["answer_audit"].get("findings") and row["answer_audit"].get("exit_code") == 0:
            if t_path.is_file():
                row["lab_static"] = runner.static(t_path, a_path)
                if not row["lab_static"].get("findings") and row["lab_static"].get("exit_code") == 0:
                    row["task_form"] = runner.run("vcheck", t_path, lang, gate=True)
            else:
                row["task_missing"] = True
    row["seconds"] = round(time.monotonic() - t0, 1)
    return judge_row(row)


def _read_partial(path):
    head, rows, segs = None, {}, []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue      # a line cut by a kill
        if r.get("kind") == "header":
            head = r
        elif r.get("kind") == "segment":
            segs.append(r)
        elif "task" in r:
            rows[r["task"]] = r
    return head, rows, segs


def validate_set(root, s, only=(), *, workers=1, mem_gb=None, sample=None, seed=None,
                 restart=False):
    """§7.2 --validate (see the block comment above). Returns the rows."""
    import signal
    import threading
    from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
    from datetime import datetime, timezone
    from dvl import common
    name = s["name"]
    d = set_dir(root, name)
    probs = check_installed(root, s) if d.is_dir() else ["not installed"]
    if probs:
        raise Refused(f"{name}: " + "; ".join(probs))
    if not 1 <= workers <= WORKERS_MAX:
        raise Refused(f"--workers must be 1..{WORKERS_MAX} (CLAUDE.md §Resources)")
    if (sample is None) != (seed is None):
        raise Refused("--sample and --seed go together (a pre-registered seeded draw)")
    answers = sorted(p.relative_to(d / "answers").as_posix() for p in (d / "answers").rglob("*")
                     if p.is_file() and p.suffix in SOLVER_EXT)
    if only:
        answers = [r for r in answers if r in only or PurePosixPath(r).stem in only]
        if not answers:
            raise Refused(f"{name}: --only names no answer file")
    strata = strata_of(root, s, answers)
    selection = {"only": sorted(only), "sample": None}
    if sample is not None:
        drawn, alloc = stratified_sample(strata, sample, seed)
        selection["sample"] = {
            "n": len(drawn), "seed": seed, "of": len(answers),
            "rule": "stratified by " + ("language/source (the subset index)" if s.get("subset")
                                         else "language") + "; proportional allocation, largest "
                    "remainder, at least one per stratum when n allows; random.Random(f'{seed}:{stratum}')"
                    ".sample over the stratum's sorted answer paths",
            "strata": alloc, "drawn_sha256": hashlib.sha256("\n".join(drawn).encode()).hexdigest()}
        answers = drawn
    caps = {lang: float(common.load_pins().get(lang, {}).get("mem_gb", 8))
            for lang in {SOLVER_EXT[PurePosixPath(r).suffix] for r in answers}}
    share = float(mem_gb) if mem_gb is not None else max(caps.values(), default=8.0)
    head = {"kind": "header", "schema": VALIDATION_SCHEMA, "set": name, "sha256": s["sha256"],
            "pins_sha256": pins_digest(), "selection": selection}
    partial = d / "validation.partial.jsonl"
    final = d / "validation.jsonl"
    done, segs = {}, []
    if not partial.is_file() and final.is_file() and not restart:
        # a finished run of the same selection with rows left to retry: continue it
        old, rows0, _ = _read_partial(final)
        if old and all(old.get(k) == head[k] for k in ("schema", "set", "sha256", "pins_sha256",
                                                        "selection")) and old.get("retry_left"):
            keep = {k: old[k] for k in ("kind", "schema", "set", "sha256", "pins_sha256",
                                        "selection", "started") if k in old}
            prior = {"kind": "segment", "started": 0.0, "ended": float(old.get("wall_s", 0)),
                     "rows": len(rows0), "workers": None, "stopped": None, "note": "prior run"}
            with open(partial, "w", encoding="utf-8") as f:
                f.write(json.dumps(keep, sort_keys=True) + "\n")
                for r in rows0.values():
                    f.write(json.dumps(r, sort_keys=True) + "\n")
                f.write(json.dumps(prior, sort_keys=True) + "\n")
    if partial.is_file():
        old, rows0, segs = _read_partial(partial)
        same = old and all(old.get(k) == head[k] for k in ("schema", "set", "sha256",
                                                           "pins_sha256", "selection"))
        if same:
            done = {k: r for k, r in rows0.items() if not str(r.get("reason") or "").startswith("retry:")}
            say(f"{name}: resuming: {len(done)} of {len(answers)} row(s) already done")
        elif restart:
            partial.unlink()
            segs = []
        else:
            raise Refused(f"{name}: validation.partial.jsonl holds a run of another selection, "
                          "set digest or tool pins; --restart discards it")
    if not partial.is_file():
        head["started"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        partial.write_text(json.dumps(head, sort_keys=True) + "\n", encoding="utf-8")
    else:
        head = _read_partial(partial)[0]
    todo = [r for r in answers if r not in done]
    scratch = Path(tempfile.mkdtemp(prefix=f"dvl-bench-validate-{name}-", dir=tmp_base()))
    runner = _Runner(root, scratch, share, workers)
    wlock = threading.Lock()
    seg_start = time.time()
    stopped = {"why": None}

    def on_signal(signum, frame):
        stopped["why"] = signal.Signals(signum).name
        runner.stop.set()
        runner.kill_all()

    prev = {sig: signal.signal(sig, on_signal) for sig in (signal.SIGINT, signal.SIGTERM)}
    n_new = 0
    try:
        for top in ("tasks", "answers"):
            if (d / top).is_dir():
                shutil.copytree(d / top, scratch / top)
        with open(partial, "a", encoding="utf-8") as out, \
                ThreadPoolExecutor(max_workers=workers) as ex:
            it = iter(todo)
            running = set()
            while True:
                while not runner.stop.is_set() and len(running) < workers:
                    rel = next(it, None)
                    if rel is None:
                        break
                    running.add(ex.submit(validate_row, runner, d, scratch, rel, strata[rel]))
                if not running:
                    break
                fin, running = wait(running, timeout=5, return_when=FIRST_COMPLETED)
                for fu in fin:
                    try:
                        row = fu.result()
                    except _Stop:
                        continue
                    except Failed as e:
                        stopped["why"] = str(e)
                        runner.stop.set()
                        runner.kill_all()
                        continue
                    with wlock:
                        out.write(json.dumps(row, sort_keys=True) + "\n")
                        out.flush()
                        os.fsync(out.fileno())
                    done[row["task"]] = row
                    n_new += 1
                    a = row.get("answer") or {}
                    say(f"{name}/{row['task']}: " + ("pool" if row["pool"] else row["reason"])
                        + (f" ({a.get('seconds')} s)" if a else ""))
            seg = {"kind": "segment", "started": seg_start, "ended": time.time(), "rows": n_new,
                   "workers": workers, "stopped": stopped["why"]}
            out.write(json.dumps(seg, sort_keys=True) + "\n")
            out.flush()
            segs.append(seg)
    finally:
        for sig, h in prev.items():
            signal.signal(sig, h)
        shutil.rmtree(scratch, ignore_errors=True)
    retry = [r for r in answers if str((done.get(r) or {}).get("reason") or "").startswith("retry:")]
    missing = [r for r in answers if r not in done]
    if stopped["why"] or missing:
        raise Failed(f"{name}: stopped ({stopped['why'] or 'unfinished'}) with {len(answers) - len(missing)} "
                     f"of {len(answers)} row(s) done; run the same command again to resume")
    rows = [done[r] for r in answers]
    by_reason, by_stratum = {}, {}
    for r in rows:
        by_reason[r["reason"] or "pool"] = by_reason.get(r["reason"] or "pool", 0) + 1
        st = by_stratum.setdefault(r["stratum"], [0, 0])
        st[0] += 1
        st[1] += int(r["pool"])
    head.update({"finished": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "wall_s": round(sum(x["ended"] - x["started"] for x in segs), 1),
                 "segments": len(segs), "rows": len(rows), "pool": sum(r["pool"] for r in rows),
                 "retry_left": len(retry), "by_reason": by_reason, "by_stratum": by_stratum,
                 "job_seconds": round(sum(r.get("seconds", 0) for r in rows), 1)})
    tmp = d / "validation.jsonl.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps(head, sort_keys=True) + "\n")
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    tmp.replace(d / "validation.jsonl")
    partial.unlink()
    say(f"{name}: {head['pool']} of {len(rows)} task(s) validate ({len(retry)} to retry); "
        f"wall {head['wall_s']} s; wrote bench/public/{name}/validation.jsonl")
    return rows


# --- the pool pins ------------------------------------------------------------------------------
#
# bench/public/POOLS.toml (committed; frozen with bench/public/, rule 2f): one
# [[pool]] per validated set, written by the author-only --pin-pool from a
# finished validation.jsonl. The set directories are gitignored (fetch sets),
# so this file is the course's record of each pool: the set digest and tool
# pins it was validated on, the selection (whole or a seeded sample), the
# counts by reason and stratum, the wall time, and the pool's members (public
# task paths only, never an answer) with their sha256. A lab's pre-registered draw
# from a pool is a [[draw]] table of the same file (scripts/dvl/lab2pub.py record:
# Lab 2's public strata); --pin-pool rewrites the [[pool]] tables and keeps them.

POOLS_FILE = ("bench", "public", "POOLS.toml")


def pools_path(root):
    return Path(root).joinpath(*POOLS_FILE)


def load_pools(root):
    p = pools_path(root)
    if not p.is_file():
        return {}
    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise Refused(f"bench/public/POOLS.toml is unusable: {e}") from None
    return {x.get("set"): x for x in data.get("pool", []) if isinstance(x, dict)}


def pool_digest(members):
    return hashlib.sha256("".join(m + "\n" for m in sorted(members)).encode()).hexdigest()


def read_validation(root, s):
    """(header, rows) of a set's finished validation.jsonl, or Refused."""
    f = set_dir(root, s["name"]) / "validation.jsonl"
    if not f.is_file():
        raise Refused(f"{s['name']}: no validation.jsonl (run get_bench.sh --validate {s['name']})")
    head, rows, _ = _read_partial(f)
    if not head or head.get("schema") != VALIDATION_SCHEMA or "finished" not in head:
        raise Refused(f"{s['name']}: validation.jsonl is not a finished schema-{VALIDATION_SCHEMA} run")
    return head, [rows[k] for k in sorted(rows)]


def _toml_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return json.dumps(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        if not v:
            return "[]"
        if not any(isinstance(x, str) for x in v):
            return "[" + ", ".join(_toml_value(x) for x in v) + "]"
        return "[\n" + "".join(f"  {_toml_value(x)},\n" for x in v) + "]"
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{json.dumps(str(k))} = {_toml_value(x)}" for k, x in sorted(v.items())) + " }"
    raise TypeError(v)


def load_draws(root):
    """The [[draw]] records of bench/public/POOLS.toml (a lab's pre-registered draws from the
    pools, written by the author-only scripts/dvl/lab2pub.py record), in file order."""
    p = pools_path(root)
    if not p.is_file():
        return []
    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise Refused(f"bench/public/POOLS.toml is unusable: {e}") from None
    return [x for x in data.get("draw", []) if isinstance(x, dict)]


def lab_members(root, set_name, lab):
    """The members a lab may draw from a set's pool: the pool's tasks less every task another
    lab's [[draw]] record drew from the same set (the user's decision D30, 2026-10-14: Lab 1's
    task forms keep the specification, so a Lab 1 (Q12) draw that took one of Lab 2's (Q15)
    public HumanEval-Verus tasks would show its Lab 2 reference). Sorted; Refused when the set
    has no pinned pool or its members do not match its pool_sha256."""
    pool = load_pools(root).get(set_name)
    if not pool:
        raise Refused(f"bench/public/POOLS.toml has no pool of {set_name}")
    tasks = sorted(pool.get("tasks", []))
    if pool_digest(tasks) != pool.get("pool_sha256"):
        raise Refused(f"{set_name}: the pool's members do not match its pool_sha256")
    taken = {t for d in load_draws(root) if d.get("set") == set_name and d.get("lab") != lab
             for t in d.get("drawn", [])}
    # D39: a translation is the same problem even when another set/language
    # supplies it. The public draw's card ids pin HumanEval identity without
    # requiring installed reference answers or the upstream subset index.
    problem_ids = set()
    if lab == "Q12" and set_name == "humaneval-verus":
        for draw in load_draws(root):
            if draw.get("lab") == lab or draw.get("lab") != "Q15":
                continue
            for card in draw.get("cards", []):
                m = re.fullmatch(r"[dv]p\d+-he(\d+)", card)
                if m is None:
                    raise Refused(f"Q15 draw has no HumanEval identity for card {card!r}")
                problem_ids.add(int(m.group(1)))
    return [t for t in tasks if t not in taken and not (
        (m := re.match(r"human_eval_(\d+)(?:_|\.)", Path(t).name))
        and int(m.group(1)) in problem_ids)]


DRAW_KEYS = ("lab", "stratum", "set", "subset", "set_sha256", "pins_sha256", "pool_sha256",
             "members", "seed", "order_sha256", "walked", "rule", "prereg_sha256",
             "amendment_sha256", "date",
             "drawn", "cards", "skipped")


def write_draws(root, draws):
    """Replace the [[draw]] records of the same (lab, stratum) with `draws`; keep the others
    and every [[pool]]."""
    new = {(d["lab"], d["stratum"]) for d in draws}
    kept = [d for d in load_draws(root) if (d.get("lab"), d.get("stratum")) not in new]
    write_pools(root, load_pools(root), kept + list(draws))


def write_pools(root, pools, draws=None):
    """Write bench/public/POOLS.toml: the [[pool]] tables, then the [[draw]] records (by
    default the file's own, so that --pin-pool keeps a lab's draws)."""
    if draws is None:
        draws = load_draws(root)
    out = ["# bench/public/POOLS.toml: the validated pools of the public benchmark sets (QPLAN §30",
           "# Q57; DV4-PLAN §7.2). Generated by the author-only scripts/get_bench.sh --pin-pool from",
           "# a finished `get_bench.sh --validate` run; not edited by hand. Each [[pool]] names the",
           "# set digest and tool pins it was validated on, the selection (the whole set, or a",
           "# pre-registered seeded sample), the counts, and the pool: the tasks whose answer passes",
           "# the done check (vcheck --gate, 0 holes; vaudit, no finding) and, as a delivery, the",
           "# lab gate's static half (specfreeze --lab), and whose task form fails the gate as",
           "# shipped at the verify stage. Task paths only (public); no answer is here.",
           "# `get_bench.sh --check` compares an installed validation.jsonl with its entry.",
           "# Each [[draw]] is a lab's pre-registered draw from a pool (its seed, the rule and",
           "# its sha256, the seeded order's sha256, the drawn tasks and every skipped member",
           "# with its reason), written by the author-only scripts/dvl/lab2pub.py record and",
           "# kept by --pin-pool.",
           "", "schema = 1"]
    keys = ("set", "set_sha256", "pins_sha256", "validated", "selection", "rows", "pool",
            "pool_sha256", "by_reason", "by_stratum", "wall_s", "segments", "tasks")
    for name in sorted(pools):
        e = pools[name]
        out += ["", "[[pool]]"]
        for k in keys:
            if k == "selection":
                sel = e.get("selection")
                sel = sel if isinstance(sel, str) else json.dumps(sel, sort_keys=True)
                out.append(f"selection = {_toml_value(sel)}")
            elif k in e:
                out.append(f"{k} = {_toml_value(e[k])}")
    for d in draws:
        out += ["", "[[draw]]"]
        for k in DRAW_KEYS:
            if k in d:
                out.append(f"{k} = {_toml_value(d[k])}")
    pools_path(root).write_text("\n".join(out) + "\n", encoding="utf-8")


def pin_pool(root, s):
    head, rows = read_validation(root, s)
    if head.get("sha256") != s.get("sha256"):
        raise Refused(f"{s['name']}: validation.jsonl was made on another set digest; re-validate")
    if head.get("pins_sha256") != pins_digest():
        raise Refused(f"{s['name']}: validation.jsonl was made on other tool pins; re-validate")
    if head.get("retry_left"):
        raise Refused(f"{s['name']}: {head['retry_left']} row(s) are left to retry; re-run "
                      f"get_bench.sh --validate {s['name']} first")
    members = sorted(r["task"] for r in rows if r.get("pool"))
    pools = load_pools(root)
    pools[s["name"]] = {
        "set": s["name"], "set_sha256": s["sha256"], "pins_sha256": head["pins_sha256"],
        "validated": str(head["finished"])[:10],
        "selection": json.dumps(head.get("selection"), sort_keys=True),
        "rows": len(rows), "pool": len(members), "pool_sha256": pool_digest(members),
        "by_reason": head.get("by_reason", {}),
        "by_stratum": {k: v for k, v in head.get("by_stratum", {}).items()},
        "wall_s": head.get("wall_s", 0), "segments": head.get("segments", 1), "tasks": members}
    write_pools(root, pools)
    return len(members)


def pool_problems(root, s):
    """Problems of a set's pool pin against its installed validation.jsonl (if any)."""
    e = load_pools(root).get(s["name"])
    if not e:
        return []
    out = []
    if e.get("set_sha256") != s.get("sha256"):
        out.append("its pool pin in bench/public/POOLS.toml was made on another set digest")
    if e.get("pins_sha256") != pins_digest():
        out.append("its pool pin in bench/public/POOLS.toml was made on other tool pins "
                   "(scripts/dvl/pins.toml): re-validate and re-pin the pool")
    f = set_dir(root, s["name"]) / "validation.jsonl"
    if f.is_file():
        try:
            head, rows = read_validation(root, s)
        except Refused as x:
            return out + [str(x)]
        if head.get("sha256") == s.get("sha256") and \
                json.dumps(head.get("selection"), sort_keys=True) == e.get("selection"):
            got = pool_digest(r["task"] for r in rows if r.get("pool"))
            if got != e.get("pool_sha256"):
                out.append("its validation.jsonl's pool differs from the pool pinned in "
                           "bench/public/POOLS.toml")
    return out


def author_gate(root):
    from dvl import sandbox
    return sandbox.author_gate(root)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="get_bench.sh", allow_abbrev=False,
                                 description="Fetch and check the course's benchmark sets "
                                             "(DV4-PLAN §7).")
    ap.add_argument("sets", nargs="*")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--all", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--list", action="store_true")
    mode.add_argument("--validate", action="store_true")
    mode.add_argument("--pin", action="store_true")
    mode.add_argument("--pin-pool", action="store_true")
    mode.add_argument("--members", action="store_true",
                      help="SET --lab LAB [--seed S]: the members LAB may draw from SET's pinned "
                           "pool (less the tasks another lab's [[draw]] took; D30), sorted, or in "
                           "the seeded order")
    ap.add_argument("--lab", help="--members: the lab that draws (Q12 for Lab 1)")
    ap.add_argument("--only", nargs="+", default=[])
    ap.add_argument("--sample", type=int, help="--validate: a seeded stratified sample of N answers")
    ap.add_argument("--seed", help="--validate --sample: the pre-registered seed")
    ap.add_argument("--workers", type=int, default=1,
                    help=f"--validate: solver jobs at once (1..{WORKERS_MAX}; default 1)")
    ap.add_argument("--mem-gb", type=float,
                    help="--validate: accepted and ignored (D78: no course-side memory management)")
    ap.add_argument("--restart", action="store_true",
                    help="--validate: discard a partial run of another selection")
    ap.add_argument("--root", help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    root = Path(a.root).resolve() if a.root else REPO_ROOT
    try:
        data, sets = load_manifest(root)
        unknown = [n for n in a.sets if n not in sets]
        if unknown:
            raise Refused(f"unknown set(s) {unknown}; the manifest lists {sorted(sets)}")
        if (a.only or a.sample is not None or (a.seed and not a.members) or a.workers != 1
                or a.mem_gb is not None or a.restart) and not a.validate:
            ap.error("--only, --sample, --seed, --workers, --mem-gb and --restart go with --validate")
        if a.members:
            if len(a.sets) != 1 or not a.lab or not re.fullmatch(r"[QR]\d\d", a.lab):
                ap.error("--members takes exactly one set and --lab <lab id>")
            got = lab_members(root, a.sets[0], a.lab)
            if a.seed:
                random.Random(a.seed).shuffle(got)
            for t in got:
                print(t)
            pool = load_pools(root)[a.sets[0]]
            say(f"{a.sets[0]}: {len(got)} of the pool's {len(pool['tasks'])} member(s) for "
                f"{a.lab} (pool_sha256 {pool['pool_sha256'][:16]}; "
                + (f"seeded order, seed {a.seed!r})" if a.seed else "sorted)"), err=True)
            return 0
        if a.lab:
            ap.error("--lab goes with --members")
        if a.list:
            for n, s in sets.items():
                d = set_dir(root, n)
                state = "not installed"
                if d.is_dir():
                    probs = check_installed(root, s)
                    state = "installed, current" if not probs else "installed, " + "; ".join(probs)
                ups = ", ".join(f"{u.get('what', '?')}: {u.get('licence')}" for u in s.get("upstream", []))
                print(f"{n:16} {s['mode']:6} {s['licence']['spdx']:11} {state}")
                print(f"{'':16} {s['repo']} @ {s['commit'][:12]}; upstream: {ups or 'none recorded'}")
            return 0
        if a.check:
            names = a.sets or [n for n in sets if set_dir(root, n).is_dir()]
            if not names:
                # the empty-set rule (DV6 fix round): nothing checked is no pass
                say("no set is installed, so nothing was checked: install them first "
                    "(scripts/get_bench.sh --all), or name the sets to check", err=True)
                return 3
            bad = False
            for n in names:
                if not set_dir(root, n).is_dir():
                    say(f"{n}: not installed", err=True)
                    bad = True
                    continue
                probs = check_installed(root, sets[n]) + pool_problems(root, sets[n])
                if probs:
                    say(f"{n}: " + "; ".join(probs), err=True)
                    bad = True
                else:
                    pin = load_pools(root).get(n)
                    say(f"{n}: current ({sets[n]['sha256'][:16]})"
                        + (f"; pool pinned: {pin['pool']} of {pin['rows']}" if pin else ""))
            return 3 if bad else 0
        if a.validate:
            if len(a.sets) != 1:
                ap.error("--validate takes exactly one set")
            validate_set(root, sets[a.sets[0]], a.only, workers=a.workers, mem_gb=a.mem_gb,
                         sample=a.sample, seed=a.seed, restart=a.restart)
            return 0
        names = list(sets) if a.all else a.sets
        if not names:
            ap.error("name a set, or --all, --check, --list, --validate, --pin or --pin-pool")
        if a.pin_pool:
            why = author_gate(root)
            if why:
                raise Refused(f"--pin-pool is author-only and refuses to run here ({why}); the "
                              "author pins pools in the authoring worktree (Δ103)")
            for n in names:
                k = pin_pool(root, sets[n])
                say(f"{n}: pinned its pool ({k} task(s)) in bench/public/POOLS.toml")
            return 0
        if a.pin:
            why = author_gate(root)
            if why:
                raise Refused(f"--pin is author-only and refuses to run here ({why}); the author "
                              "pins sets in the authoring worktree (Δ103)")
            for n in names:
                digest = install(root, sets[n], pin=True)
                write_pin(root, n, digest)
                say(f"{n}: pinned sha256 {digest} in bench/manifest.toml")
            return 0
        for n in names:
            install(root, sets[n])
        return 0
    except Refused as e:
        say(f"refused: {e}", err=True)
        return 3
    except Failed as e:
        say(f"failed: {e}", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
