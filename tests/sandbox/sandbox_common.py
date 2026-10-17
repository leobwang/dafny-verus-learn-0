"""Shared helpers for the sandbox suites (DV4-PLAN §9, `tests/sandbox/`).

The suites run with the standard library only and never start a container:
the docker they meet is a fake on PATH that answers like a refused daemon
(or, for the live-run refusal, like an accepting one). Throwaway course roots
hold an invented module Q98 (layer L4, like the adapter suite's Q98) with
decoy files only: no reference material, no real exercise. The run
directories live under a temporary XDG_RUNTIME_DIR.

This module holds no TestCase: unittest discovery imports it and finds nothing.
"""

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
MKSANDBOX = SCRIPTS / "mksandbox-run"
TMP_BASE = os.environ.get("DVL_TEST_TMP") or None
GIT = ["git", "-c", "user.name=sandbox-tests", "-c", "user.email=sandbox-tests@example.invalid",
       "-c", "init.defaultBranch=main"]
DIGEST = "sha256:" + "ab" * 32
IMAGE = f"dvl-agent@{DIGEST}"
VIMAGE = f"dvl-toolchain@{'sha256:' + 'cd' * 32}"

AGENT_D = "dafny/Q/Q98_Sandbox/agent/Q98_Agent.dfy"
AGENT_V = "verus/q/q98_sandbox/src/agent.rs"
EX_D = "dafny/Q/Q98_Sandbox/std/Q98_Sandbox.dfy"
GIVEN_D = "dafny/given/Q/QG_L1_BigNat.dfy"
GIVEN_D4 = "dafny/given/Q/QG_L4_BigNat.dfy"
GIVEN_V = "verus/given/qg_bignat_l2/src/lib.rs"
PROJ_D = "dafny/Q/Q98_Sandbox/std/dfyconfig.toml"
PROJ_V = "verus/q/q98_sandbox/Cargo.toml"

REGISTRY = """schema = 1

[[module]]
id = "Q98"
track = "Q"
status = "authoring"
title = "Sandbox fixture module"
layer = "L4"
units = ["dafny/Q/Q98_Sandbox/std", "verus/q/q98_sandbox"]
exercises = ["dafny/Q/Q98_Sandbox/std/Q98_Sandbox.dfy", "verus/q/q98_sandbox/src/lib.rs"]
exits = []
agentic = ["dafny/Q/Q98_Sandbox/agent/Q98_Agent.dfy", "verus/q/q98_sandbox/src/agent.rs"]
harness = []
engines = ["contract", "agent"]
solo = false
budget = { claude_calls = 0, claude_runs = 0, qwen_calls = 40, qwen_runs = 1, gpu_hours = 1 }

[[module]]
id = "Q97"
track = "Q"
status = "authoring"
title = "Another fixture module"
layer = "L4"
units = ["dafny/Q/Q97_Other/std"]
exercises = ["dafny/Q/Q97_Other/std/Q97_Other.dfy"]
exits = []
agentic = ["dafny/Q/Q97_Other/agent/Q97_Agent.dfy"]
harness = []
engines = ["contract"]
solo = false
budget = { claude_calls = 0, claude_runs = 0, qwen_calls = 0, qwen_runs = 0, gpu_hours = 0 }
"""

AGENT_TEXT = ("/* CONTRACT\ngoal: a decoy goal for the sandbox suites\nallowed-files:\n  - "
              + AGENT_D + "\nacceptance:\n  - `scripts/vcheck --gate " + AGENT_D + "` exits 0\n*/\n"
              "lemma Decoy(n: nat) ensures n + 0 == n { }\n")


def tmpdir(prefix):
    if TMP_BASE:
        Path(TMP_BASE).mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=prefix, dir=TMP_BASE))


def sha(data):
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()


def write(root, rel, text):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def make_root(git=False, lock=True):
    """A throwaway course root holding the Q98 fixture module."""
    root = tmpdir("dvl0-sandbox-root-")
    write(root, "MODULES.toml", REGISTRY)
    write(root, AGENT_D, AGENT_TEXT)
    write(root, AGENT_V, "// decoy agentic file\nuse vstd::prelude::*;\n")
    write(root, EX_D, "// decoy exercise\n")
    write(root, "dafny/Q/Q97_Other/agent/Q97_Agent.dfy", "// decoy agentic file of Q97\n")
    write(root, GIVEN_D, "// decoy given layer L1\nfunction One(): nat { 1 }\n")
    write(root, GIVEN_D4, "// decoy given layer L4\n")
    write(root, "dafny/given/Q/QG_L5_BigNat.dfy", "// decoy given layer L5 (outside Q98's chain)\n")
    write(root, GIVEN_V, "// decoy given crate L2\n")
    write(root, "verus/given/qg_bignat_l2/Cargo.toml", '[package]\nname = "qg_bignat_l2"\n')
    write(root, PROJ_D, 'includes = ["*.dfy"]\n')
    write(root, PROJ_V, '[package]\nname = "q98_sandbox"\nbuild = false\n')
    write(root, "verus/Cargo.toml", '[workspace]\nmembers = ["q/q98_sandbox"]\n')
    for t in ("vcheck", "vaudit", "specfreeze", "course_items.py", "check_course_map.py",
              "gen_units.py", "course_mode.sh", "get_toolchain.sh", "dvl/common.py", "dvl/pins.toml",
              "ci.sh"):
        write(root, f"scripts/{t}", f"# decoy copy of scripts/{t}\n")
    write(root, "expected/Q98.counts", "# decoy counts pin\n")
    write(root, "expected/Q98.freeze", "# decoy freeze pin\n")
    write(root, "expected/Q98_Agent.audit", "# decoy audit pin\n")
    write(root, "expected/Q97.counts", "# decoy counts pin of Q97\n")
    write(root, "research/snapshots/Q98_Agent.dfy", "// decoy snapshot\n")
    write(root, "docs/Q98_Sandbox.md", "# decoy chapter\n")
    write(root, "Solutions/dafny/Q/Q98_Sandbox/std/Q98_Sandbox.dfy", "// decoy twin\n")
    write(root, "bench/public/decoyset/tasks/t1.dfy", "// decoy public task\n")
    write(root, "bench/public/decoyset/answers/t1.dfy", "// decoy public answer\n")
    write(root, "bench/local/q/card01/tasks/task.dfy", "// decoy lab task card\n")
    write(root, "bench/local/q/card01/answers/answer.dfy", "// decoy learner answer\n")
    write(root, "sandbox/canaries.sha256", "# none\n")
    write(root, "sandbox/attested.toml", "schema = 1\n")
    if lock:
        write(root, "sandbox/images.lock",
              f'schema = 1\n\n[[image]]\nname = "dvl-agent"\ndigest = "{DIGEST}"\n\n'
              f'[[image]]\nname = "dvl-toolchain"\ndigest = "sha256:{"cd" * 32}"\n')
    else:
        write(root, "sandbox/images.lock", "schema = 1\n")
    if git:
        subprocess.run(GIT + ["init", "-q", str(root)], check=True)
        subprocess.run(GIT + ["-C", str(root), "add", "-A"], check=True)
        subprocess.run(GIT + ["-C", str(root), "commit", "-q", "-m", "fixture"], check=True)
    return root


def entry(root, src, role, dst=None, rev=None):
    data = (Path(root) / src).read_bytes()
    e = {"src": src, "dst": dst or src, "role": role, "sha256": sha(data)}
    if rev:
        e["rev"] = rev
    return e


def text_entry(dst, role, text):
    return {"dst": dst, "role": role, "text": text, "sha256": sha(text)}


def agent_manifest(root, **over):
    m = {"schema": 1, "run_id": "q98-run1", "module": "Q98", "kind": "agent", "image": IMAGE,
         "network": "ollama",
         "limits": {"cpus": 2, "pids": 256, "wall_clock_s": 2700, "work_mb": 256, "tmp_mb": 512},
         "file": [entry(root, AGENT_D, "editable"), entry(root, GIVEN_D, "given"),
                  entry(root, PROJ_D, "project"), entry(root, "scripts/vcheck", "tool"),
                  entry(root, "expected/Q98.counts", "expected"),
                  text_entry("CONTRACT.md", "contract", "# decoy contract text\n")],
         "return": [AGENT_D],
         "agent": {"cli": "opencode", "model": "qwen3.8:latest", "turns": 40}}
    m.update(over)
    return m


def verify_manifest(root, **over):
    files = over.pop("file", None) or [entry(root, AGENT_D, "editable"), entry(root, GIVEN_D, "given"),
                                       entry(root, "scripts/vcheck", "tool")]
    m = {"schema": 1, "run_id": "q98-verify1", "module": "Q98", "kind": "verify", "image": VIMAGE,
         "network": "none", "file": files, "return": []}
    m.update(over)
    return m


def write_manifest(dirpath, m, name="manifest.json"):
    p = Path(dirpath) / name
    p.write_text(json.dumps(m, indent=2), encoding="utf-8")
    return p


def fake_bin(dirpath, name, script):
    p = Path(dirpath) / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("#!/bin/sh\n" + script, encoding="utf-8")
    p.chmod(0o755)
    return p


def run_mk(args, env_extra=None, path_first=None, runtime=None):
    env = {k: v for k, v in os.environ.items() if k not in ("CI", "DVL_NO_DOCKER", "DVL_CAP")}
    if path_first:
        env["PATH"] = f"{path_first}:{env.get('PATH', '/usr/bin:/bin')}"
    if runtime:
        env["XDG_RUNTIME_DIR"] = str(runtime)
    env.update(env_extra or {})
    return subprocess.run([sys.executable, "-B", str(MKSANDBOX), *args], capture_output=True,
                          text=True, env=env, timeout=300)


class TarBuilder:
    """A fabricated `tar --create -C /work .` stream, member by member."""

    def __init__(self):
        self.buf = io.BytesIO()
        self.tf = tarfile.open(fileobj=self.buf, mode="w", format=tarfile.GNU_FORMAT)

    def dir(self, name):
        ti = tarfile.TarInfo(name)
        ti.type = tarfile.DIRTYPE
        ti.mode = 0o755
        self.tf.addfile(ti)
        return self

    def file(self, name, data):
        if isinstance(data, str):
            data = data.encode()
        ti = tarfile.TarInfo(name)
        ti.size = len(data)
        ti.mode = 0o644
        self.tf.addfile(ti, io.BytesIO(data))
        return self

    def special(self, name, kind, linkname=""):
        ti = tarfile.TarInfo(name)
        ti.type = kind
        ti.linkname = linkname
        self.tf.addfile(ti)
        return self

    def stream(self):
        self.tf.close()
        return io.BytesIO(self.buf.getvalue())


def cleanup(*paths):
    for p in paths:
        if p and Path(p).exists():
            for dirpath, _, _ in os.walk(p):
                os.chmod(dirpath, 0o700)
            shutil.rmtree(p, ignore_errors=True)
