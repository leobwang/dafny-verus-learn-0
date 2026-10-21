#!/usr/bin/env python3
"""sandbox/seal_hidden.py: seal a lab's hidden truth for the grader container
(DV4-PLAN §5.9, QPLAN §30 Q49, design §10.3). Author-only (the three-condition
test of Δ103, dvl.sandbox.author_gate); guard rule 1c refuses it in a study
session (it names the sealed archive).

    python3 sandbox/seal_hidden.py <LAB> --src DIR [--dry-run]
    python3 sandbox/seal_hidden.py <LAB> --src DIR --stratum bench/local/q/<s> [--dry-run]
    python3 sandbox/seal_hidden.py <LAB> --src DIR --tasks bench/local/q/agentic/<s> [--dry-run]

With --tasks (topic (e)'s sealed task parts, DELTAS Δ409), the tree is the stratum's task
forms (labs/<LAB>/<card>/tasks/<file>, the layout fvh.statements.unseal reads): it is
sealed to the stratum's recipient into the path its STRATUM.toml names as `archive`, and
archive_sha256, files and manifest_sha256 are written back into that STRATUM.toml.

With --stratum, the tree is a sealed stratum's reference deliveries (labs/<LAB>/refs/
<card>/<path>; Lab 3's, DV6 fix round): it is sealed to the stratum's own recipient into
the path its STRATUM.toml names as `refs_archive`, and the pins are written back into that
STRATUM.toml (refs_sha256, refs_files, refs_manifest_sha256), where dvl.sandbox's
attestation scan reads them (the user's decision D31).

DIR holds the plaintext tree labs/<LAB>/ with its MANIFEST.sha256 (the author
archive's staged copy; it never enters the checkout). The tool

  1. checks every file of DIR/labs/<LAB>/ against MANIFEST.sha256 (each
     listed file present with its sha256, no unlisted file, no link);
  2. writes one deterministic tar stream of the tree (sorted names, mtime 0,
     uid and gid 0, mode 0644; regular files only) and encrypts it with the
     pinned age binary (~/.local/bin/age, its sha256 in sandbox/truth.toml
     and VERSIONS.md §1.4) to the recipient sandbox/truth.toml pins, into the
     archive path pinned there (Hidden/labs/<LAB>/verdicts.tar.age);
  3. writes the archive's sha256, its file count and the sha256 of the
     plaintext manifest back into sandbox/truth.toml.

It never decrypts: the round trip is checked in the grader container
(`scripts/mksandbox-run --truth <archive> --truth-check manifest`). An age
encryption is randomized, so every seal gives a new archive sha256.
Exit: 0 sealed, 1 failed, 2 usage, 3 refused.
"""

import argparse
import hashlib
import io
import os
import re
import subprocess
import sys
import tarfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from dvl import sandbox  # noqa: E402

TRUTH = ROOT / sandbox.TRUTH_FILE


def say(msg, err=False):
    print(f"seal_hidden: {msg}", file=sys.stderr if err else sys.stdout)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def plaintext(src, lab):
    """{name: bytes} of src/labs/<lab>/, checked against its MANIFEST.sha256."""
    base = Path(src) / "labs" / lab
    man = base / "MANIFEST.sha256"
    if not man.is_file():
        raise ValueError(f"{man} is missing")
    listed = {}
    for line in man.read_text(encoding="utf-8").splitlines():
        parts = line.split(None, 1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            raise ValueError(f"{man}: a malformed line")
        listed[parts[1].strip()] = parts[0]
    files = {}
    for f in sorted(base.rglob("*")):
        rel = f.relative_to(Path(src)).as_posix()
        if f.is_symlink():
            raise ValueError(f"{rel} is a link")
        if f.is_file():
            files[rel] = f.read_bytes()
    have = set(files) - {f"labs/{lab}/MANIFEST.sha256"}
    if have != set(listed):
        raise ValueError(f"the tree's files ({len(have)}) differ from its manifest ({len(listed)})")
    bad = [k for k, h in listed.items() if sha(files[k]) != h]
    if bad:
        raise ValueError(f"{len(bad)} file(s) do not match the manifest")
    return files, sha(man.read_bytes())


def tar_stream(files):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tf:
        for name in sorted(files):
            data = files[name]
            ti = tarfile.TarInfo(name)
            ti.size, ti.mtime, ti.mode, ti.uid, ti.gid = len(data), 0, 0o644, 0, 0
            ti.uname = ti.gname = ""
            tf.addfile(ti, io.BytesIO(data))
    return buf.getvalue()


def update_pins(lab, digest, count, man_sha):
    """Rewrite the lab's sha256, files and manifest_sha256 lines in sandbox/truth.toml."""
    lines = TRUTH.read_text(encoding="utf-8").splitlines(keepends=True)
    starts = [i for i, x in enumerate(lines) if x.strip() == "[[lab]]"]
    blocks = [(a, (starts + [len(lines)])[k + 1]) for k, a in enumerate(starts)]
    mine = [(a, b) for a, b in blocks if any(x.strip() == f'id = "{lab}"' for x in lines[a:b])]
    if len(mine) != 1:
        raise ValueError(f"{sandbox.TRUTH_FILE} has no single [[lab]] {lab}")
    a, b = mine[0]
    vals = {"sha256": f'"{digest}"', "files": str(count), "manifest_sha256": f'"{man_sha}"'}
    for i in range(a, b):
        key = lines[i].split("=", 1)[0].strip() if "=" in lines[i] else None
        if key in vals:
            lines[i] = f"{key} = {vals.pop(key)}\n"
    if vals:
        raise ValueError(f"{sandbox.TRUTH_FILE}: [[lab]] {lab} lacks {sorted(vals)}")
    TRUTH.write_text("".join(lines), encoding="utf-8")
    tomllib.loads(TRUTH.read_text(encoding="utf-8"))


def update_stratum_pins(stratum_toml, digest, count, man_sha, prefix="refs_"):
    """Rewrite a stratum's refs_sha256, refs_files and refs_manifest_sha256 lines (with
    prefix "" and the archive's key name: archive_sha256, files, manifest_sha256)."""
    lines = stratum_toml.read_text(encoding="utf-8").splitlines(keepends=True)
    if prefix:
        vals = {"refs_sha256": f'"{digest}"', "refs_files": str(count),
                "refs_manifest_sha256": f'"{man_sha}"'}
    else:
        vals = {"archive_sha256": f'"{digest}"', "files": str(count),
                "manifest_sha256": f'"{man_sha}"'}
    for i, x in enumerate(lines):
        if x.lstrip().startswith("["):
            break                       # top-level keys only
        key = x.split("=", 1)[0].strip() if "=" in x else None
        if key in vals:
            lines[i] = f"{key} = {vals.pop(key)}\n"
    if vals:
        raise ValueError(f"{stratum_toml}: lacks {sorted(vals)} (add them above the first table)")
    stratum_toml.write_text("".join(lines), encoding="utf-8")
    tomllib.loads(stratum_toml.read_text(encoding="utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="seal_hidden.py", allow_abbrev=False)
    ap.add_argument("lab")
    ap.add_argument("--src", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--stratum", help="seal a sealed stratum's reference deliveries (its "
                                      "STRATUM.toml's refs_archive)")
    ap.add_argument("--tasks", help="seal a topic (e) stratum's task forms (its STRATUM.toml's "
                                    "archive)")
    a = ap.parse_args(argv)
    if a.stratum and a.tasks:
        say("refused: --stratum or --tasks, not both", err=True)
        return 2
    why = sandbox.author_gate(ROOT)
    if why:
        say(f"refused: author-only ({why})", err=True)
        return 3
    stoml = None
    key = "refs_archive"
    if a.tasks:
        a.stratum, key = a.tasks, "archive"
    if a.stratum:
        stoml = ROOT / a.stratum / "STRATUM.toml"
        try:
            meta = tomllib.loads(stoml.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            say(f"refused: {a.stratum}/STRATUM.toml cannot be read", err=True)
            return 3
        if (meta.get("lab") or meta.get("module")) != a.lab or not meta.get(key):
            say(f"refused: {a.stratum}/STRATUM.toml names no lab {a.lab} with a {key}",
                err=True)
            return 3
        any_pin = next(iter(sandbox.truth_pins(ROOT).values()), None) or {}
        pin = {"archive": meta[key], "recipient": meta.get("recipient"),
               "age_sha256": any_pin.get("age_sha256")}
        if not pin["recipient"] or not pin["age_sha256"]:
            say("refused: the stratum's recipient or the pinned age's sha256 is missing", err=True)
            return 3
    else:
        pin = sandbox.truth_pins(ROOT).get(a.lab)
    if pin is None:
        say(f"refused: no [[lab]] {a.lab} in {sandbox.TRUTH_FILE}", err=True)
        return 3
    age = Path(os.path.expanduser("~/.local/bin/age"))
    if not age.is_file() or sha(age.read_bytes()) != pin.get("age_sha256"):
        say(f"refused: {age} is missing or not the pinned age (sha256 {pin.get('age_sha256')})",
            err=True)
        return 3
    try:
        files, man_sha = plaintext(a.src, a.lab)
    except (OSError, ValueError) as e:
        say(f"failed: {e}", err=True)
        return 1
    stream = tar_stream(files)
    say(f"{a.lab}: {len(files) - 1} files and the manifest, tar {len(stream)} B, plaintext "
        f"manifest sha256 {man_sha[:16]}")
    if a.dry_run:
        return 0
    out = ROOT / pin["archive"]
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    p = subprocess.run([str(age), "--encrypt", "--recipient", pin["recipient"], "--output",
                        str(tmp)], input=stream, capture_output=True, timeout=120)
    if p.returncode != 0:
        say("failed: age --encrypt: " + p.stderr.decode("utf-8", "replace").strip()[-300:], err=True)
        return 1
    os.chmod(tmp, 0o644)
    tmp.replace(out)
    digest = sha(out.read_bytes())
    if stoml is not None:
        update_stratum_pins(stoml, digest, len(files) - 1, man_sha,
                            prefix="" if key == "archive" else "refs_")
        where = stoml.relative_to(ROOT).as_posix()
    else:
        update_pins(a.lab, digest, len(files) - 1, man_sha)
        where = sandbox.TRUTH_FILE
    say(f"sealed {pin['archive']} ({out.stat().st_size} B, sha256 {digest}); pinned in {where}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
