#!/usr/bin/env python3
"""Probe runner for the Dafny BigNat spike (author-only tooling).

Every run is archived under
  ~/.cache/dafny-verus-learn-0/author-probes/spike-dafny/<probe-id>/
with cmd.txt, stdout.txt, stderr.txt, exit.txt and meta.txt.
Inputs are either copied (toy files with no reference proof text) or recorded
in INPUT-NOTE.txt by path + sha256 (reference files that must stay under
Solutions/, spec 9.3 law 3).
"""
import datetime
import hashlib
import os
import shlex
import shutil
import subprocess
import time

REPO = "/home/leobwang/code/learn/dafny-verus/dafny-verus-learn-0"
DAFNY = REPO + "/.toolchain/dafny-4.11.0/dafny/dafny"
ARCH = os.path.expanduser("~/.cache/dafny-verus-learn-0/author-probes/spike-dafny")
SPIKE = REPO + "/Solutions/spikes/dafny"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def run(probe_id, argv, cwd, copy_inputs=(), note_inputs=(), note_extra="",
        wall_safety=1800):
    """Run argv in cwd and archive it. Returns (exit_code, stdout, stderr)."""
    d = os.path.join(ARCH, probe_id)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    for p in copy_inputs:
        shutil.copy(p, d)
    notes = []
    for p in note_inputs:
        notes.append(f"{p}\tsha256={sha256(p)}")
    if notes or note_extra:
        with open(os.path.join(d, "INPUT-NOTE.txt"), "w") as f:
            if notes:
                f.write("Input files (reference proof text stays under Solutions/; "
                        "recorded by path and sha256, not copied):\n")
                f.write("\n".join(notes) + "\n")
            if note_extra:
                f.write(note_extra.rstrip("\n") + "\n")
    with open(os.path.join(d, "cmd.txt"), "w") as f:
        f.write(f"cd {shlex.quote(cwd)} && {shlex.join(argv)}\n")
    t0 = time.time()
    try:
        p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                           timeout=wall_safety)
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        rc = "killed-by-wall-safety-net"
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
    dt = time.time() - t0
    for name, content in (("stdout.txt", out), ("stderr.txt", err), ("exit.txt", f"{rc}\n")):
        with open(os.path.join(d, name), "w") as f:
            f.write(content)
    with open(os.path.join(d, "meta.txt"), "w") as f:
        f.write(f"cwd={cwd}\ndate={datetime.datetime.now().astimezone().isoformat(timespec='seconds')}\n"
                f"wall_seconds={dt:.2f}\n")
    return rc, out, err
