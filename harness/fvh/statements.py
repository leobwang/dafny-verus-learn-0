"""fvh.statements — the `statements` pin and the unseal of a sealed lab stratum
(QPLAN §28.1, §28.6, §30 Q64; DV4-PLAN §4.5; the DV5c gaps lane).

A module whose lab tasks ship sealed (Lab 3: `bench/local/q/crate/tasks.tar.age`)
names, in the frozen file expected/<ID>.statements (guard rule 2f), the statement
files the tasks wait on and the sha256 of each one's shipped form:

    <sha256 of the shipped form>  <course path>

`check` passes only when every listed file is tracked by git, its working copy is
the committed one (no staged or unstaged change), and the committed content
differs from the shipped form: the learner has written the statements and
committed them. The committed hashes go into the batch's records (fvh.batch's
`statements` plan key) and into the unseal record.

`unseal` runs `check` first and then, for each sealed stratum of the module
(bench/local/<q|r>/<lab>/STRATUM.toml with `module = "<ID>"` and an `archive`),
checks the archive against the stratum's archive_sha256, decrypts it with the
pinned age binary (~/.local/bin/age, its sha256 pinned by the sandbox/truth.toml
[[lab]] whose recipient the stratum names, beside the identity's location),
parses the tar stream in memory (regular files only, every name under
labs/<LAB>/, no link, no absolute or parent path), checks every file against the
plaintext's MANIFEST.sha256 (and that manifest's sha256 and file count against
the stratum's pins, and every card against the stratum's [[card]] ids), and only
then writes the cards' files into the stratum directory: bench/local/<t>/<lab>/
<card>/tasks/…. It never overwrites a file that differs (an identical one is
left as it is, so a second unseal is a no-op), and it writes UNSEALED.toml beside
STRATUM.toml: the date, the statements' committed hashes, the archive's and the
manifest's sha256 and the file count.

  read_pins(root, module) -> list[(path, shipped sha256)]   [] when none
  check(root, module) -> dict[path, committed sha256]       or StatementsRefused
  sealed_strata(root, module) -> list[Path]                 the STRATUM.toml files
  unseal(root, module, *, dry_run=False, age=None, identity=None, part=None,
         once=False, into=None) -> dict
  unseal_ledger(root) -> list[dict]                         research/unseals.jsonl, checked

Single use (the challenge tier: QPLAN §31.3, the coordinator's D-6, DELTAS Δ402).
With `part`, only the strata whose STRATUM.toml names `part = "<part>"` are unsealed.
With `once`, a part is unsealed at most once: the hash-chained ledger
research/unseals.jsonl (one canonical JSON object per line, "prev" the sha256 of the
line before, GENESIS first; written only here) must hold no earlier entry for the
same module, part and archive_sha256, or the unseal is refused; the entry it appends
marks the part consumed and retired (its plaintext is in the run's records; a new
seal is the author's only override). With `into` (a directory outside the course
tree, required with `once`), the cards are written there and not into the stratum
directory, and no UNSEALED.toml is written (the ledger is the record).

Public cards (D76; QPLAN §33.4, DELTAS Δ411). A card with `source = "public"` names its
public task in its sealed form's second line (`// Source: <set> <task file> (...)`), and is
either a `role = "card"` or a `role = "spare"` with a `spare_order`. Before anything is
written, every public card whose task the learner has met is excluded: a task file named
in Lab 1's stratum (bench/local/q/lab1/STRATUM.toml) or run records (research/runs/Q12/),
in any lab's [[draw]] record (bench/public/POOLS.toml) or in Lab alpha's lists
(bench/local/r/labalpha/STRATUM.toml, FREEZE.toml) when the tree has them. Each excluded
card is replaced by the next spare, in spare order, that is not excluded itself; the part
is refused when the spares run out. Unused spares are not written. The replacements (card
ids only) go into the result and the ledger entry.

Refusals (StatementsRefused, exit 3 at the command line) name the file and the
reason; nothing is written before every check passes. Frozen (guard rule 2f),
standard library only.
"""

import datetime
import hashlib
import io
import json
import os
import re
import subprocess
import tarfile
import tomllib
from pathlib import Path, PurePosixPath

__all__ = ["LEDGER", "PIN_DIR", "StatementsRefused", "check", "read_pins", "sealed_strata",
           "unseal", "unseal_ledger"]

PIN_DIR = "expected"
LEDGER = "research/unseals.jsonl"
GENESIS = "0" * 64
TRUTH_FILE = "sandbox/truth.toml"
AGE = "~/.local/bin/age"


def _platform():
    """This host's platform id, as scripts/dvl/host.py current() names it."""
    u = os.uname()
    if u.sysname == "Linux" and u.machine == "x86_64":
        return "linux-x86_64"
    if u.sysname == "Darwin" and u.machine == "arm64":
        return "macos-arm64"
    return f"unsupported-{u.sysname.lower()}-{u.machine}"


def _pinned(value, platform=None):
    """A per-platform pin here (dvl.host.pinned's rule): a table {platform id:
    value} gives this platform's entry; a plain value holds on linux-x86_64 only."""
    platform = platform or _platform()
    if isinstance(value, dict):
        return value.get(platform)
    return value if platform == "linux-x86_64" else None
MAX_PLAIN = 64 << 20
_CARD = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
_SHA = re.compile(r"[0-9a-f]{64}")
_SOURCE = re.compile(rb"^// Source: (\S+) (\S+) \(", re.M)
_TASK_FILE = re.compile(r"[\w.+-]+\.(?:dfy|rs)")
SEEN_FILES = ("bench/local/q/lab1/STRATUM.toml", "bench/public/POOLS.toml",
              "bench/local/r/labalpha/STRATUM.toml", "bench/local/r/labalpha/FREEZE.toml")
SEEN_DIRS = ("research/runs/Q12",)


class StatementsRefused(RuntimeError):
    """The statements are not committed yet, or a sealed stratum cannot be unsealed."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(root, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, timeout=60)


def pin_file(root, module) -> Path:
    return Path(root) / PIN_DIR / f"{module}.statements"


def read_pins(root, module) -> list:
    """The (path, shipped sha256) lines of expected/<ID>.statements, in file order."""
    p = pin_file(root, module)
    if not p.is_file():
        return []
    out = []
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2 or not _SHA.fullmatch(parts[0]):
            raise StatementsRefused(f"{p.name} line {n}: not '<sha256>  <course path>'")
        rel = parts[1].strip()
        if rel.startswith("/") or ".." in rel.split("/"):
            raise StatementsRefused(f"{p.name} line {n}: {rel} is not a course path")
        out.append((rel, parts[0]))
    return out


def check(root, module) -> dict:
    """{path: committed sha256} of the module's statement files, or StatementsRefused."""
    root = Path(root)
    pins = read_pins(root, module)
    if not pins:
        raise StatementsRefused(f"{PIN_DIR}/{module}.statements names no statement file: "
                                f"{module} has no statements pin")
    if _git(root, "rev-parse", "--verify", "HEAD").returncode != 0:
        raise StatementsRefused(f"{root} is not a git checkout with a commit: the statements "
                                "pin reads the committed files")
    out = {}
    for rel, shipped in pins:
        p = root / rel
        if not p.is_file():
            raise StatementsRefused(f"{rel} is missing")
        if _git(root, "ls-files", "--error-unmatch", "--", rel).returncode != 0:
            raise StatementsRefused(f"{rel} is not tracked by git: commit your statements "
                                    "first (QPLAN §28.6)")
        st = _git(root, "status", "--porcelain", "--", rel)
        if st.returncode != 0 or st.stdout.strip():
            raise StatementsRefused(f"{rel} has changes that are not committed: commit it "
                                    "first; the tasks unseal only against committed statements")
        blob = _git(root, "show", f"HEAD:{rel}")
        if blob.returncode != 0:
            raise StatementsRefused(f"{rel}: its committed content cannot be read")
        committed = _sha(blob.stdout)
        if committed != _sha(p.read_bytes()):
            raise StatementsRefused(f"{rel}: the working copy differs from the commit")
        if committed == shipped:
            raise StatementsRefused(f"{rel} is still the shipped form: write your statements "
                                    "into it and commit them (QPLAN §28.3 step 2)")
        out[rel] = committed
    return out


def sealed_strata(root, module) -> list:
    """The STRATUM.toml files of the module's sealed local strata (sorted)."""
    root = Path(root)
    track = "q" if module.startswith("Q") else "r"
    out = []
    base = root / "bench" / "local" / track
    # a lab's strata sit one level down; topic (e)'s under agentic/ (QPLAN §33.4, Δ409)
    for p in sorted([*base.glob("*/STRATUM.toml"), *base.glob("agentic/*/STRATUM.toml")]):
        try:
            data = tomllib.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if data.get("module") == module and data.get("archive"):
            out.append(p)
    return out


def _truth_pin(root, recipient):
    try:
        data = tomllib.loads((Path(root) / TRUTH_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for lab in data.get("lab", []):
        if lab.get("recipient") == recipient:
            return lab
    return None


def _plaintext(stream: bytes, lab: str) -> dict:
    """{name relative to labs/<lab>/: bytes}, regular files only; or StatementsRefused."""
    files = {}
    prefix = f"labs/{lab}/"
    try:
        with tarfile.open(fileobj=io.BytesIO(stream), mode="r:") as tf:
            for m in tf.getmembers():
                if m.isdir():
                    continue
                if not m.isfile():
                    raise StatementsRefused("the archive holds something other than regular "
                                            "files")
                name = PurePosixPath(m.name).as_posix()
                if (name.startswith("/") or ".." in name.split("/")
                        or not name.startswith(prefix)):
                    raise StatementsRefused(f"the archive holds a file outside {prefix}")
                rel = name[len(prefix):]
                if rel in files:
                    raise StatementsRefused("the archive holds a file twice")
                fh = tf.extractfile(m)
                files[rel] = fh.read() if fh is not None else b""
    except tarfile.TarError:
        raise StatementsRefused("the unsealed archive is not a tar stream") from None
    return files


def _manifest(files: dict) -> tuple:
    man = files.get("MANIFEST.sha256")
    if man is None:
        raise StatementsRefused("the archive holds no MANIFEST.sha256")
    listed = {}
    for line in man.decode("utf-8", "replace").splitlines():
        parts = line.split(None, 1)
        if len(parts) != 2 or not _SHA.fullmatch(parts[0]):
            raise StatementsRefused("the archive's MANIFEST.sha256 has a malformed line")
        listed[parts[1].strip()] = parts[0]
    have = set(files) - {"MANIFEST.sha256"}
    if have != set(listed):
        raise StatementsRefused(f"the archive's files ({len(have)}) differ from its manifest "
                                f"({len(listed)})")
    bad = [k for k, h in listed.items() if _sha(files[k]) != h]
    if bad:
        raise StatementsRefused(f"{len(bad)} file(s) of the archive do not match its manifest")
    return listed, _sha(man)


def learner_seen(root) -> set:
    """D76's unseal-time exclusion: the task file names the learner's tree records as met
    (Lab 1's stratum and run records, every [[draw]] record, Lab alpha's lists)."""
    root = Path(root)
    paths = [root / rel for rel in SEEN_FILES]
    for rel in SEEN_DIRS:
        d = root / rel
        if d.is_dir():
            paths += sorted(p for p in d.rglob("*") if p.is_file())
    seen = set()
    for p in paths:
        try:
            if not p.is_file() or p.is_symlink() or p.stat().st_size > MAX_PLAIN:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if p.name == "POOLS.toml":
            # the pools list every member; only the [[draw]] records say what a lab took
            try:
                draws = tomllib.loads(text).get("draw", [])
            except ValueError:
                draws = []
            text = json.dumps(draws)
        seen.update(_TASK_FILE.findall(text))
    return seen


def _public_plan(rel_sp, meta, files, seen) -> tuple:
    """(ids of the public cards not to write, [(excluded card, its spare)]) for one
    stratum, or StatementsRefused when the spares run out."""
    pub = [c for c in meta.get("card", []) if c.get("source") == "public"]
    if not pub:
        return set(), []

    def task_of(c):
        for rel, body in files.items():
            if rel.startswith(f"{c.get('id')}/tasks/"):
                m = _SOURCE.search(body)
                if m:
                    return m.group(2).decode("utf-8", "replace")
        raise StatementsRefused(f"{rel_sp}: public card {c.get('id')} names no source")

    cards = [c for c in pub if c.get("role", "card") == "card"]
    spares = sorted((c for c in pub if c.get("role") == "spare"),
                    key=lambda c: int(c.get("spare_order") or 0))
    free = [s for s in spares if task_of(s) not in seen]
    keep, replaced = set(), []
    for c in cards:
        if task_of(c) not in seen:
            keep.add(c["id"])
            continue
        if not free:
            raise StatementsRefused(f"{rel_sp}: {len([x for x in cards if task_of(x) in seen])} "
                                    "public card(s) are tasks you have met (D76's exclusion) and "
                                    "the spares have run out: this part cannot be unsealed")
        s = free.pop(0)
        keep.add(s["id"])
        replaced.append((c["id"], s["id"]))
    return {c["id"] for c in pub} - keep, replaced


def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def unseal_ledger(root) -> list:
    """The single-use ledger's entries, its chain checked (StatementsRefused if broken)."""
    p = Path(root) / LEDGER
    if not p.is_file():
        return []
    out, prev = [], GENESIS
    for n, line in enumerate(p.read_text(encoding="utf-8").split("\n"), 1):
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            raise StatementsRefused(f"{LEDGER}:{n}: not a JSON line") from None
        if e.get("prev") != prev or e.get("seq") != len(out) + 1 or _canon(e) != line:
            raise StatementsRefused(f"{LEDGER}:{n}: the hash chain is broken")
        out.append(e)
        prev = _sha(line.encode("utf-8"))
    return out


def unseal(root, module, *, dry_run=False, age=None, identity=None, part=None, once=False,
           into=None) -> dict:
    """Unseal the module's sealed strata into the tree (module docstring).

    `age` = (path, sha256) and `identity` (a path) replace the pinned binary and
    the truth file's key location (tests). Returns {"statements": {...},
    "strata": [{"stratum", "archive_sha256", "manifest_sha256", "files", "written",
    "kept"}]}; with dry_run every check runs and nothing is written."""
    root = Path(root)
    if once and (into is None or part is None):
        raise StatementsRefused("a single-use unseal names its part and a directory outside "
                                "the course tree (--part, --into)")
    if into is not None:
        into = Path(into).resolve()
        try:
            into.relative_to(root.resolve())
        except ValueError:
            pass
        else:
            raise StatementsRefused(f"{into}: a single-use part is written outside the course tree")
    ledger = unseal_ledger(root) if once else []
    committed = check(root, module)
    seen = learner_seen(root)
    strata = sealed_strata(root, module)
    if part is not None:
        strata = [sp for sp in strata
                  if tomllib.loads(sp.read_text(encoding="utf-8")).get("part") == part]
    if not strata:
        raise StatementsRefused(f"{module} has no sealed stratum (a STRATUM.toml with "
                                f"module = \"{module}\" and an archive"
                                + (f", part = \"{part}\"" if part is not None else "") + ")")
    plans = []
    for sp in strata:
        meta = tomllib.loads(sp.read_text(encoding="utf-8"))
        lab = meta.get("lab") or module
        arc = root / str(meta["archive"])
        rel_sp = sp.relative_to(root).as_posix()
        if not arc.is_file():
            raise StatementsRefused(f"{rel_sp}: its archive {meta['archive']} is missing")
        data = arc.read_bytes()
        if _sha(data) != meta.get("archive_sha256"):
            raise StatementsRefused(f"{rel_sp}: {meta['archive']} does not match its "
                                    "archive_sha256")
        for e in ledger:
            if (e.get("module"), e.get("part"), e.get("archive_sha256")) == \
                    (module, part, meta.get("archive_sha256")):
                raise StatementsRefused(f"{rel_sp}: part {part!r} was unsealed once already "
                                        f"({e.get('date')}, {LEDGER} seq {e.get('seq')}): a part "
                                        "is single use, and only a new seal replaces it")
        pin = _truth_pin(root, meta.get("recipient"))
        if age is None:
            if pin is None:
                raise StatementsRefused(f"{rel_sp}: no [[lab]] of {TRUTH_FILE} pins the age "
                                        "binary and key of its recipient")
            binary, want = Path(os.path.expanduser(AGE)), _pinned(pin.get("age_sha256"))
        else:
            binary, want = Path(age[0]), age[1]
        if not binary.is_file() or _sha(binary.read_bytes()) != want:
            raise StatementsRefused(f"{binary} is missing or not the pinned age binary")
        ident = Path(os.path.expanduser(identity if identity is not None
                                        else (pin or {}).get("identity", "")))
        if not ident.is_file():
            raise StatementsRefused("the key that unseals the tasks is not on this machine "
                                    f"(the location {TRUTH_FILE} names)")
        try:
            p = subprocess.run([str(binary), "--decrypt", "--identity", str(ident), str(arc)],
                               capture_output=True, timeout=300)
        except (OSError, subprocess.TimeoutExpired):
            raise StatementsRefused(f"{rel_sp}: the archive could not be unsealed") from None
        if p.returncode != 0 or not p.stdout or len(p.stdout) > MAX_PLAIN:
            raise StatementsRefused(f"{rel_sp}: the archive could not be unsealed with the key")
        files = _plaintext(p.stdout, lab)
        listed, man_sha = _manifest(files)
        if man_sha != meta.get("manifest_sha256") or len(listed) != meta.get("files"):
            raise StatementsRefused(f"{rel_sp}: the archive's manifest differs from the "
                                    "stratum's pins (manifest_sha256, files)")
        cards = {c.get("id") for c in meta.get("card", [])}
        skip, replaced = _public_plan(rel_sp, meta, files, seen)
        writes = []
        for rel in sorted(listed):
            parts = rel.split("/")
            if (len(parts) < 3 or parts[1] != "tasks" or parts[0] not in cards
                    or not _CARD.fullmatch(parts[0])):
                raise StatementsRefused(f"{rel_sp}: the archive holds a file that is not a "
                                        "listed card's task file")
            if parts[0] in skip:
                continue
            dest = (into / rel) if into is not None else sp.parent / rel
            shown = dest if into is not None else dest.relative_to(root)
            if dest.is_symlink() or (dest.exists() and not dest.is_file()):
                raise StatementsRefused(f"{shown} is in the way")
            if dest.is_file() and dest.read_bytes() != files[rel]:
                raise StatementsRefused(f"{shown} exists and differs from the "
                                        "sealed task: nothing is overwritten")
            writes.append((dest, files[rel]))
        plans.append((sp, meta, _sha(data), man_sha, writes, replaced))
    out = {"statements": committed, "strata": []}
    for sp, meta, arc_sha, man_sha, writes, replaced in plans:
        written = kept = 0
        for dest, body in writes:
            if dest.is_file():
                kept += 1
                continue
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(body)
                os.chmod(dest, 0o644)
            written += 1
        rec = {"stratum": sp.relative_to(root).as_posix(), "archive_sha256": arc_sha,
               "manifest_sha256": man_sha, "files": len(writes), "written": written,
               "kept": kept}
        if replaced:
            rec["public_replaced"] = [list(x) for x in replaced]
        if not dry_run and once:
            prev = (_sha(_canon(ledger[-1]).encode("utf-8")) if ledger else GENESIS)
            entry = {"seq": len(ledger) + 1, "prev": prev,
                     "date": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                     "module": module, "part": part, "stratum": sp.relative_to(root).as_posix(),
                     "archive_sha256": arc_sha, "manifest_sha256": man_sha, "files": len(writes),
                     "statements": dict(sorted(committed.items()))}
            if replaced:
                entry["public_replaced"] = [list(x) for x in replaced]
            lp = root / LEDGER
            lp.parent.mkdir(parents=True, exist_ok=True)
            with open(lp, "a", encoding="utf-8") as f:
                f.write(_canon(entry) + "\n")
            ledger.append(entry)
        elif not dry_run and into is None:
            lines = ["# UNSEALED.toml: written by `python -m fvh unseal` (fvh.statements); a "
                     "record, never read back.",
                     f'date = "{datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}"',
                     f'module = "{meta.get("module")}"',
                     f'archive_sha256 = "{arc_sha}"', f'manifest_sha256 = "{man_sha}"',
                     f"files = {len(writes)}", "", "[statements]"]
            lines += [f'"{k}" = "{v}"' for k, v in sorted(committed.items())]
            (sp.parent / "UNSEALED.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
        out["strata"].append(rec)
    return out
