#!/usr/bin/env python3
"""sandbox_doors.py: the sandbox's by-hand acceptance (DV4-PLAN §9, §11 step 2d).

    python3 tests/acceptance/sandbox_doors.py [all | SECTION ...] [--archive DIR]
                                              [--units Q01,Q02,...]

Needs Docker (host action H1) and no model: no inference request ever reaches
Ollama (the one real upstream request is GET /api/version, control C5; the
gate's other controls run against a fake model server on loopback). Run it
before a merge that changes sandbox/, scripts/mksandbox-run,
scripts/dvl/sandbox.py or an image digest. Never in CI.

Every check is a neutral regression check (Solutions/plans/DV4-author-notes.md
§2.2): the plain operation that must be refused, beside a positive control
that must work. Each section prints one PASS or FAIL line per control with its
evidence; --archive writes results.json and every run's records there.

Sections (the control ids of the author notes):
  access    Docker access through mksandbox-run --check-access
  images    sandbox/build-images.sh --check: the lock names the local images
  controls  C1-C4, C7, C8 in a verification container; C1-C8 in a probe agent
            container on the model network (Route B: the relay to the gate,
            C5 GET /api/version through it, C6 every host listener refused)
  gate      C9 model management refused, C10 another model refused, C11 the
            pinned options set and the override logged, the call cap (429),
            through the relay, against a fake model server
  memory    C13: a verification and an agent container allocating past
            --memory are killed(memory); a solver job past a small container's
            memory is reported killed(memory) by vcheck from memory.events
  pids      C14: a spawn past --pids-limit fails and the run goes on
  wall      C15: a run past wall_clock_s is killed (exit 124) and removed
  watcher   C16: mksandbox-run killed mid-run: the watcher removes the
            container, stops the gate and removes the run directory
  reap      mksandbox-run --reap removes a dvl.run container whose owner is
            gone and keeps one whose owner lives
  return    C17: an unlisted file, a symlink, a FIFO, a hard link and an
            oversize file in /work never return; filling the tmpfs stops at
            its cap
  secret    C18: a credential-shaped string in a returned file withholds it
  canary    C19: the canary prefix in a staged file stops the run before any
            container starts; and for each tree of sandbox/canaries.sha256 its planted
            DVLCANARY file hashes to its line and a staged copy is attributed to it
  parity    C20: every armed unit of Q01-Q06 (or --units): the gate's verdict,
            counts and holes in the verification container (fvh's
            ContainerRunner) and in a probe agent container (container-agent
            mode) equal the host's (fvh's HostRunner); and every armed Python
            learner file (or --py-units; "none" skips them): its gate (the
            holes, then the frozen acceptance tests through uv and the image's
            seeded wheels) gives the same verdict, counts, holes and per-test
            statuses in both container modes as on the host
  e2e       DV4 step 2b: fvh's executor with a Scripted and a Mock policy,
            every Verify in a fresh verification container (the work copy
            streamed in over the course's files)
  exposure  DV4 step 2c's record: from a container on a per-run --internal
            network (Route A's starting point, no filter), which host
            listeners answer on the gateway and the host's addresses

Memory (CLAUDE.md §Resources): one container at a time, each at its --memory
cap (Verus parity at 16 GB); the free-memory check of mksandbox-run applies.
Exit: 0 every control passed, 1 one failed, 2 usage.
"""

import argparse
import http.server
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MK = ROOT / "scripts" / "mksandbox-run"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "harness"))

from dvl import sandbox  # noqa: E402

SECTIONS = ("access", "images", "controls", "gate", "memory", "pids", "wall", "watcher", "reap",
            "return", "secret", "canary", "parity", "e2e", "exposure")
DAFNY_T = "dafny/Q/Q01_Hello/agent/Q01_AgentRepair.dfy"
VERUS_CRATE = "verus/q/q01_hello"
RESULTS = []
ARCHIVE = None
TMP = None


def note(section, cid, ok, evidence):
    RESULTS.append({"section": section, "id": cid, "ok": bool(ok), "evidence": evidence})
    print(f"{'PASS' if ok else 'FAIL'} {section} {cid}: {evidence}", flush=True)


def keep(name, path):
    if ARCHIVE and Path(path).exists():
        dest = ARCHIVE / name
        if Path(path).is_dir():
            shutil.copytree(path, dest, dirs_exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)


def mk(args, timeout=3600):
    return subprocess.run([sys.executable, "-B", str(MK), *args], capture_output=True, text=True,
                          timeout=timeout, cwd=ROOT)


def build(target, argv, *, kind="verify", network="none", mem_gb=None, module=None, run_id=None):
    args = ["--build-verify", "--target", str(target), "--argv", json.dumps(argv), "--kind", kind,
            "--network", network]
    if mem_gb:
        args += ["--mem-gb", f"{mem_gb:g}"]
    if module:
        args += ["--module", module]
    p = mk(args, 300)
    if p.returncode != 0:
        raise RuntimeError(f"build-verify {target}: {p.stderr.strip()}")
    m = json.loads(p.stdout)["manifest"]
    if run_id:
        m["run_id"] = run_id
    return m


def run(m, name, *, probe=True, extra=(), timeout=7200):
    """(exit code, run.json or None, stderr) of one live run of manifest `m`."""
    d = Path(tempfile.mkdtemp(prefix=f"{name}-", dir=TMP))
    man = d / "manifest.json"
    man.write_text(json.dumps(m), encoding="utf-8")
    p = mk((["--probe"] if probe else []) + list(extra) + ["--records", str(d / "rec"), str(man)],
           timeout)
    rj = d / "rec" / "run.json"
    rec = json.loads(rj.read_text()) if rj.is_file() else None
    (d / "stderr.txt").write_text(p.stderr, encoding="utf-8")
    keep(name, d)
    return p.returncode, rec, p.stderr


def door(name, *args):
    return [sandbox.CONTROLS, "door", name, *args]


def gate_argv(t):
    return ["scripts/vcheck", "--gate", "--json", t]


def container_gone(name):
    p = subprocess.run(["docker", "ps", "--all", "--filter", f"name=^{name}$", "--format",
                        "{{.Names}}"], capture_output=True, text=True, timeout=60)
    return p.stdout.strip() == ""


# --- sections --------------------------------------------------------------------------------

def s_access():
    p = mk(["--check-access"], 60)
    note("access", "docker", p.returncode == 0, (p.stdout + p.stderr).strip())


def s_images():
    p = subprocess.run(["bash", str(ROOT / "sandbox" / "build-images.sh"), "--check"],
                       capture_output=True, text=True, timeout=1800)
    note("images", "lock", p.returncode == 0, (p.stderr.strip().splitlines() or ["?"])[-1])
    lock = sandbox.read_images_lock(ROOT)
    note("images", "names", {k.split("@")[0] for k in lock} == {"dvl-toolchain", "dvl-agent"},
         ", ".join(sorted(lock)))


def s_controls():
    m = build(DAFNY_T, gate_argv(DAFNY_T), run_id="doors-controls-verify")
    code, rec, err = run(m, "controls-verify", probe=False)
    ctl = (rec or {}).get("controls", {}).get("controls", [])
    for c in ctl:
        note("controls", f"{c['id']} (verify, network none)", c["ok"], c["detail"])
    note("controls", "verify run", code == 0 and rec and rec["ended_by"] == "done" and rec["removed"],
         f"exit {code}, ended_by {(rec or {}).get('ended_by')}, removed {(rec or {}).get('removed')}")
    m = build(DAFNY_T, gate_argv(DAFNY_T), kind="agent", network="ollama", run_id="doors-controls-agent")
    code, rec, err = run(m, "controls-agent")
    ctl = (rec or {}).get("controls", {}).get("controls", [])
    for c in ctl:
        note("controls", f"{c['id']} (probe agent, network ollama, Route B)", c["ok"], c["detail"])
    ids = {c["id"] for c in ctl}
    note("controls", "C5 and C6 ran", {"C5", "C6"} <= ids, f"controls {sorted(ids)}; host targets "
         f"{(rec or {}).get('host_targets')}")
    log = (rec or {}).get("gate", {}).get("gate.log", "")
    reqs = [json.loads(x) for x in log.splitlines() if x.strip()]
    paths = [(r.get("method"), r.get("path"), r.get("status")) for r in reqs if r["event"] == "request"]
    note("controls", "C5 the only upstream request", paths == [("GET", "/api/version", 200)],
         f"gate.log requests {paths}")


class FakeModel(http.server.BaseHTTPRequestHandler):
    seen = []

    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        FakeModel.seen.append(("GET", self.path, None))
        if self.path == "/api/ps":
            return self._send(200, {"models": [{"name": "door-model:1", "size": 1, "size_vram": 1}]})
        if self.path == "/api/version":
            return self._send(200, {"version": "fake"})
        self._send(404, {"error": "not here"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        FakeModel.seen.append(("POST", self.path, body))
        if self.path == "/api/chat":
            return self._send(200, {"model": body.get("model"), "done": True, "prompt_eval_count": 5,
                                    "eval_count": 2, "message": {"role": "assistant", "content": "ok"}})
        if self.path == "/v1/chat/completions":
            return self._send(200, {"choices": [{"message": {"role": "assistant", "content": "ok"}}],
                                    "usage": {"prompt_tokens": 5, "completion_tokens": 2}})
        self._send(404, {"error": "not here"})


def s_gate():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeModel)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    FakeModel.seen = []
    try:
        cfg = {"model": "door-model:1", "margin": 512, "caps": {"calls": 2},
               "options": {"temperature": 0, "seed": 7, "num_predict": 64, "num_ctx": 4096,
                           "top_k": 20, "top_p": 0.9}}
        cf = Path(TMP) / "gate-config.json"
        cf.write_text(json.dumps(cfg))
        m = build(DAFNY_T, gate_argv(DAFNY_T), kind="agent", network="ollama", run_id="doors-gate")
        m["command"] = [{"argv": door("http", "POST", "/api/pull", "door-model:1")},
                        {"argv": door("http", "POST", "/api/delete", "door-model:1")},
                        {"argv": door("http", "POST", "/api/create", "door-model:1")},
                        {"argv": door("http", "GET", "/api/tags", "door-model:1")},
                        {"argv": door("http", "POST", "/api/chat", "other-model:1")},
                        {"argv": door("http", "POST", "/api/chat", "door-model:1", "temperature=0.8",
                                      "num_ctx=999999")},
                        {"argv": door("http", "POST", "/v1/chat/completions", "door-model:1",
                                      "temperature=0.5")},
                        {"argv": door("http", "POST", "/api/chat", "door-model:1")}]
        code, rec, err = run(m, "gate", extra=["--gate-config", str(cf), "--gate-upstream",
                                               f"http://127.0.0.1:{srv.server_address[1]}"])
    finally:
        srv.shutdown()
    outs = [json.loads(c["stdout"]) for c in (rec or {}).get("commands", []) if c["stdout"].strip()]
    st = [o["status"] for o in outs]
    note("gate", "run", code == 0 and len(outs) == 8, f"exit {code}, {len(outs)} door results; {err[-300:]}")
    if len(outs) != 8:
        return
    note("gate", "C9 model management refused", st[:4] == [403, 403, 403, 403],
         f"pull, delete, create, tags -> {st[:4]}")
    note("gate", "C10 another model refused", st[4] == 403, f"other-model:1 -> {st[4]}")
    upstream_posts = [(p, b) for meth, p, b in FakeModel.seen if meth == "POST"]
    note("gate", "C9/C10 never reach the model server",
         [p for p, _ in upstream_posts] == ["/api/chat", "/v1/chat/completions"],
         f"upstream POSTs {[p for p, _ in upstream_posts]}")
    if len(upstream_posts) == 2:
        o1, o2 = upstream_posts[0][1].get("options", {}), upstream_posts[1][1]
        note("gate", "C11 pinned options on /api/chat",
             st[5] == 200 and o1 == cfg["options"], f"status {st[5]}; options sent upstream {o1}")
        note("gate", "C11 pinned options on /v1/chat/completions",
             st[6] == 200 and o2.get("temperature") == 0 and o2.get("max_tokens") == 64
             and o2.get("seed") == 7 and o2.get("top_p") == 0.9,
             f"status {st[6]}; temperature {o2.get('temperature')}, max_tokens {o2.get('max_tokens')}")
    log = [json.loads(x) for x in (rec or {}).get("gate", {}).get("gate.log", "").splitlines() if x]
    over = [o for r in log for o in r.get("overrides", [])]
    note("gate", "C11 overrides logged",
         any(o.get("option") == "temperature" and o.get("sent") == 0.8 for o in over)
         and any(o.get("option") == "num_ctx" and o.get("sent") == 999999 for o in over)
         and any(o.get("note") for o in over), f"{len(over)} override records")
    note("gate", "call cap", st[7] == 429, f"third inference call -> {st[7]}")
    refused = [r for r in log if r.get("event") == "refused"]
    note("gate", "refusals logged", len(refused) == 6, f"{len(refused)} refusal lines in gate.log")
    counts = json.loads((rec or {}).get("gate", {}).get("gate-counts.json", "{}"))
    note("gate", "counts", counts.get("calls") == 2 and counts.get("tokens") == 14,
         f"calls {counts.get('calls')}, tokens {counts.get('tokens')}, gpu_s {counts.get('gpu_s')}")


HEAVY_VERUS = "verus/q/q01_hello/src/agent.rs"


def heavy_copy():
    """A memory fixture: a work copy of a Verus file with thousands of small proof
    functions, whose front end needs more than half a gigabyte."""
    work = Path(tempfile.mkdtemp(prefix="heavy-", dir=TMP))
    (work / HEAVY_VERUS).parent.mkdir(parents=True)
    lines = ["// a memory fixture: many small proof functions", "use vstd::prelude::*;", "verus! {"]
    lines += [f"proof fn l{i}(x: nat) ensures x + {i} >= {i} {{ }}" for i in range(6000)]
    (work / HEAVY_VERUS).write_text("\n".join(lines + ["}"]) + "\n")
    return work / HEAVY_VERUS


def s_memory():
    for kind in ("verify", "agent"):
        m = build(DAFNY_T, gate_argv(DAFNY_T), kind=kind, mem_gb=0.5, run_id=f"doors-mem-{kind}")
        m["command"] = [{"argv": door("alloc")}, {"argv": gate_argv(DAFNY_T)}]
        code, rec, err = run(m, f"memory-{kind}")
        cmds = (rec or {}).get("commands", [])
        note("memory", f"C13 a {kind} container: an allocation past --memory is killed(memory)",
             code == 0 and rec and rec.get("oom_killed") and cmds and cmds[0]["killed"] == "memory"
             and cmds[0]["exit_code"] == 137,
             f"exit {code}, ended_by {(rec or {}).get('ended_by')}, OOMKilled {(rec or {}).get('oom_killed')}, "
             f"command exit {cmds[0]['exit_code'] if cmds else None} killed {cmds[0]['killed'] if cmds else None}")
        note("memory", f"C13 a {kind} container: the run goes on after it",
             len(cmds) == 2 and cmds[1]["exit_code"] is not None and cmds[1]["killed"] is None,
             f"next command exit {cmds[1]['exit_code'] if len(cmds) == 2 else None}")
    heavy = heavy_copy()
    for kind, mode in (("verify", "container-verify"), ("agent", "container-agent")):
        m = build(heavy, gate_argv(HEAVY_VERUS), kind=kind, mem_gb=0.5, run_id=f"doors-mem-job-{kind}")
        code, rec, err = run(m, f"memory-job-{kind}")
        doc = {}
        try:
            doc = json.loads(rec["commands"][0]["stdout"])
        except (TypeError, KeyError, IndexError, ValueError):
            pass
        note("memory", f"C13 a solver job past the container's memory ({mode})",
             code == 0 and rec["ended_by"] == "done" and doc.get("verdict") == "killed(memory)"
             and doc.get("exit_code") in (137, 143),
             f"exit {code}, ended_by {(rec or {}).get('ended_by')}, vcheck verdict {doc.get('verdict')}, "
             f"exit_code {doc.get('exit_code')}, the container survived {(rec or {}).get('ended_by') == 'done'}")


def s_pids():
    m = build(DAFNY_T, gate_argv(DAFNY_T), run_id="doors-pids")
    m["limits"]["pids"] = 64
    m["command"] = [{"argv": door("pids", "500")}, {"argv": gate_argv(DAFNY_T)}]
    code, rec, err = run(m, "pids")
    cmds = (rec or {}).get("commands", [])
    first = json.loads(cmds[0]["stdout"]) if cmds and cmds[0]["stdout"].strip() else {}
    note("pids", "C14 spawn past --pids-limit fails",
         first.get("stopped_by") in ("EAGAIN", "ENOMEM") and first.get("spawned", 999) < 64,
         f"spawned {first.get('spawned')}, stopped by {first.get('stopped_by')}")
    note("pids", "C14 the run goes on", code == 0 and len(cmds) == 2 and cmds[1]["exit_code"] is not None,
         f"exit {code}; second command exit {cmds[1]['exit_code'] if len(cmds) == 2 else None}")


def s_wall():
    m = build(DAFNY_T, gate_argv(DAFNY_T), run_id="doors-wall")
    m["limits"]["wall_clock_s"] = 15
    m["command"] = [{"argv": door("sleep", "300")}]
    t0 = time.monotonic()
    code, rec, err = run(m, "wall")
    took = time.monotonic() - t0
    note("wall", "C15 killed at the wall clock",
         code == 124 and rec and rec["ended_by"] == "wall-clock" and rec["removed"] and took < 120,
         f"exit {code}, ended_by {(rec or {}).get('ended_by')}, removed {(rec or {}).get('removed')}, "
         f"{took:.0f} s")


def s_watcher():
    m = build(DAFNY_T, gate_argv(DAFNY_T), kind="agent", network="ollama", run_id="doors-watcher")
    m["command"] = [{"argv": door("sleep", "300")}]
    d = Path(tempfile.mkdtemp(prefix="watcher-", dir=TMP))
    (d / "manifest.json").write_text(json.dumps(m))
    before = set(sandbox.runs_base().glob("*"))
    p = subprocess.Popen([sys.executable, "-B", str(MK), "--probe", str(d / "manifest.json")],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=ROOT)
    name = "dvl-doors-watcher"
    for _ in range(120):
        if not container_gone(name):
            break
        time.sleep(0.5)
    started = not container_gone(name)
    runs = [x for x in set(sandbox.runs_base().glob("*")) - before if x.is_dir()]
    gate_pids = subprocess.run(["pgrep", "-f", "ollama_gate.py --socket " + (str(runs[0]) if runs else "x")],
                               capture_output=True, text=True).stdout.split()
    time.sleep(3)
    p.send_signal(signal.SIGKILL)
    p.wait()
    gone = False
    for _ in range(60):
        if container_gone(name):
            gone = True
            break
        time.sleep(0.5)
    time.sleep(2)
    gate_alive = [x for x in gate_pids if Path(f"/proc/{x}").exists()]
    note("watcher", "C16 container removed after the owner's SIGKILL", started and gone,
         f"started {started}, removed {gone}")
    note("watcher", "C16 gate stopped", bool(gate_pids) and not gate_alive,
         f"gate pids {gate_pids}, alive after {gate_alive}")
    note("watcher", "C16 run directory removed", bool(runs) and not any(r.exists() for r in runs),
         f"run dirs {[str(r) for r in runs]}")


def s_reap():
    lock = sandbox.read_images_lock(ROOT)
    img = next(k for k in lock if k.startswith("dvl-toolchain@"))
    me = f"{os.getpid()}:{sandbox._proc_start(os.getpid())}"
    names = {"dvl-doors-reap-dead": "999999:1", "dvl-doors-reap-live": me}
    for n, owner in names.items():
        subprocess.run(["docker", "rm", "--force", n], capture_output=True)
        subprocess.run(["docker", "run", "--detach", "--name", n, "--label", "dvl.run=doors-reap",
                        "--label", f"dvl.owner={owner}", "--network", "none", "--memory", "128m",
                        "--memory-swap", "128m", "--cap-drop", "ALL", "--read-only", "--user",
                        "1000:1000", img, sandbox.ENTRY, "verify"], capture_output=True, check=True)
    p = mk(["--reap"], 300)
    dead_gone, live_kept = container_gone("dvl-doors-reap-dead"), not container_gone("dvl-doors-reap-live")
    subprocess.run(["docker", "rm", "--force", "dvl-doors-reap-live"], capture_output=True)
    note("reap", "an orphan is removed, a live owner's container kept", dead_gone and live_kept,
         f"{p.stderr.strip().splitlines()[-1] if p.stderr.strip() else p.stdout.strip()}; dead removed "
         f"{dead_gone}, live kept {live_kept}")


def s_return():
    m = build(DAFNY_T, gate_argv(DAFNY_T), kind="agent", run_id="doors-return")
    m["return"] = [DAFNY_T]
    d = os.path.dirname(DAFNY_T)
    m["command"] = [{"argv": door("stage-return", d, os.path.basename(DAFNY_T))}]
    code, rec, err = run(m, "return")
    cmds = (rec or {}).get("commands", [])
    staged = json.loads(cmds[0]["stdout"]) if cmds and cmds[0]["stdout"].strip() else {}
    ret = (rec or {}).get("return") or {}
    rej = {Path(r["name"]).name: r["why"] for r in ret.get("rejected", [])}
    want = {"unlisted.txt", "link-to-host-path", "a-fifo", "big.txt"}
    note("return", "C17 staged in the container", all(staged.get(k) for k in
                                                      ("unlisted", "symlink", "fifo", "hardlink", "oversize")),
         json.dumps(staged))
    note("return", "C17 none of them returns", code == 0 and want <= set(rej)
         and ("hard-link" in rej or Path(DAFNY_T).name in rej) and not ret.get("returned"),
         f"rejected {rej}; returned {ret.get('returned')}")
    note("return", "C17 the tmpfs fill stops at its cap",
         staged.get("fill_stopped") == "ENOSPC" and 0 < staged.get("fill_mib", 0) <= m["limits"].get("work_mb", 512),
         f"stopped by {staged.get('fill_stopped')} after {staged.get('fill_mib')} MiB")
    note("return", "C17 every rejection by size and sha256 only",
         all(set(r) == {"name", "size", "sha256", "why"} for r in ret.get("rejected", [])),
         f"{len(ret.get('rejected', []))} records")


def s_secret():
    m = build(DAFNY_T, gate_argv(DAFNY_T), kind="agent", run_id="doors-secret")
    m["return"] = [DAFNY_T]
    m["command"] = [{"argv": door("secret", DAFNY_T)}]
    d = Path(tempfile.mkdtemp(prefix="secret-", dir=TMP))
    (d / "manifest.json").write_text(json.dumps(m))
    p = mk(["--probe", "--records", str(d / "rec"), str(d / "manifest.json")], 1800)
    rec = json.loads((d / "rec" / "run.json").read_text()) if (d / "rec" / "run.json").is_file() else {}
    keep("secret", d)
    w = (rec.get("secret_scan") or {}).get("withheld", [])
    texts = [f.read_text(errors="replace") for f in (d / "rec").rglob("*") if f.is_file()]
    leaked = any("sk-ant-oat01-QQQQ" in t for t in texts)
    note("secret", "C18 the returned file is withheld",
         p.returncode == 0 and len(w) == 1 and w[0]["name"] == DAFNY_T and "anthropic-token" in w[0]["findings"]
         and not (d / "rec" / "returned" / DAFNY_T).exists(), f"withheld {w}")
    note("secret", "C18 the content is absent from the records", not leaked,
         f"{len(texts)} record files scanned for the planted string")


def s_canary():
    work = Path(tempfile.mkdtemp(prefix="canary-work-", dir=TMP))
    (work / DAFNY_T).parent.mkdir(parents=True)
    (work / DAFNY_T).write_text((ROOT / DAFNY_T).read_text() + "\n// DVLCANARY-doors01\n")
    m = build(work / DAFNY_T, gate_argv(DAFNY_T), run_id="doors-canary")
    code, rec, err = run(m, "canary", probe=False)
    note("canary", "C19 refused before any container starts",
         code == 1 and rec is None and "canaries" in err and container_gone("dvl-doors-canary"),
         (err.strip().splitlines() or ["?"])[0][:200])
    # One fixture per planted tree (DV4-PLAN §14 Q5, the DV5c gaps lane): the tree's
    # DVLCANARY file hashes to its line of sandbox/canaries.sha256, and a staged copy of a
    # course file with that file appended is refused and attributed to the tree. Only
    # counts, tree names and hashes are printed, never a token.
    import hashlib
    listed = sandbox.read_canaries(ROOT)
    note("canary", "trees listed", len(listed) >= 6, f"{len(listed)} tree(s) in sandbox/canaries.sha256")
    for i, (h, tree) in enumerate(sorted(listed.items(), key=lambda kv: kv[1])):
        if tree.endswith(".tar.age"):
            # a sealed archive's canary is inside its plaintext (topic (e)'s references,
            # Δ409): nothing to read here without the grader's key, so the line is noted
            note("canary", f"tree {tree}", (ROOT / tree).is_file(), "sealed: its token is inside the archive")
            continue
        top = Path(os.path.expanduser(tree)) if tree.startswith("~") else ROOT / tree
        f = top / "DVLCANARY"
        if not f.is_file():
            ok = tree.startswith("bench/public/") and not top.is_dir()
            note("canary", f"tree {tree}", ok, "no answers/ in this set: nothing to plant" if ok
                 else "its DVLCANARY file is missing")
            continue
        body = f.read_text(encoding="utf-8")
        tok = (body.split() or [""])[0]
        if hashlib.sha256(tok.encode()).hexdigest() != h:
            note("canary", f"tree {tree}", False, "the file's token does not hash to its line")
            continue
        w = Path(tempfile.mkdtemp(prefix="canary-tree-", dir=TMP))
        (w / DAFNY_T).parent.mkdir(parents=True)
        (w / DAFNY_T).write_text((ROOT / DAFNY_T).read_text() + "\n/*\n" + body + "*/\n")
        rid = f"doors-canary-t{i}"
        m = build(w / DAFNY_T, gate_argv(DAFNY_T), run_id=rid)
        code, rec, err = run(m, f"canary-t{i}", probe=False)
        note("canary", f"tree {tree}",
             code == 1 and rec is None and f"({tree})" in err and container_gone(f"dvl-{rid}"),
             f"exit {code}; attributed: {f'({tree})' in err}")


def armed_units(only):
    import check_course_map as ccm
    data, err = ccm.load_registry(ROOT)
    out = []
    for mrec in data["module"]:
        if mrec["id"] in only:
            out += [(mrec["id"], u) for u in mrec.get("units", [])]
    return out


def armed_python(spec):
    if spec == "none":
        return []
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / "dvl" / "python.py"), "files",
                        "--armed"], capture_output=True, text=True, cwd=ROOT, timeout=120)
    files = [x.strip() for x in p.stdout.splitlines() if x.strip()]
    return files if spec == "armed" else [f for f in files if f in spec.split(",")]


# A frozen acceptance test whose input is a refused source class skips where that input is
# absent, by design, so the container run counts it skipped (DV4-PLAN §5.3): recorded, not a
# parity failure, when every other test, the verdict, the stage and the holes agree.
KNOWN_SKIPS = {
    "tests/q/gate/test_core.py::test_q_half_matches_the_corpus":
        "reads tests/corpus/ (the tests class never enters a sandbox); it skips where the "
        "corpus is absent",
}


def s_parity_python(spec):
    from fvh import tools
    from fvh.tools import runners as R
    host = tools.HostRunner(ROOT)
    for f in armed_python(spec):
        h = host.execute("vcheck --gate", f)
        cv = tools.ContainerRunner(ROOT).execute("vcheck --gate", f)
        m = build(f, R.HostRunner(ROOT).argv("vcheck --gate", f), kind="agent",
                  run_id=f"doors-pyparity-{Path(f).stem.replace('_', '-')}")
        code, rec, err = run(m, f"pyparity-{Path(f).stem}")
        try:
            c = rec["commands"][0]
            ca = R.make_result("vcheck --gate", f, h.provenance, "container", c["exit_code"],
                               c["stdout"], c["stderr"], c.get("killed") == "wall-clock",
                               R._redactor(Path(rec["root"]), rec["scratch"]), True)
        except (TypeError, KeyError, IndexError) as e:
            note("parity", f"C20 {f}", False, f"the agent-mode run failed: exit {code} {e} {err[-300:]}")
            continue

        hp = dict(h.document.get("per_symbol") or {})
        skips = sorted(t for t in KNOWN_SKIPS if hp.get(t) == "passed"
                       and (cv.document.get("per_symbol") or {}).get(t) == "skipped"
                       and (ca.document.get("per_symbol") or {}).get(t) == "skipped")

        def key(r):
            d = r.document
            holes = sorted((x.get("line"), x.get("kind"), x.get("label")) for x in d.get("holes") or [])
            per = {k: v for k, v in (d.get("per_symbol") or {}).items() if k not in skips}
            vc = d.get("verified_count")
            if isinstance(vc, int) and r is h:
                vc -= len(skips)
            return (d.get("verdict"), vc, d.get("exit_code"), d.get("stage"), holes,
                    sorted(per.items()))
        same = key(h) == key(cv) == key(ca)
        keys = sorted(set(h.document) | set(cv.document) | set(ca.document))
        differ = [k for k in keys if not (h.document.get(k) == cv.document.get(k) == ca.document.get(k))]
        allowed = {"cmd"} | ({"per_symbol", "verified_count"} if skips else set())
        note("parity", f"C20 {f}", same and h.killed is None and set(differ) <= allowed,
             f"host {key(h)[:4]} holes {len(key(h)[4])} tests {len(key(h)[5])}; container-verify "
             f"{key(cv)[:4]}; container-agent {key(ca)[:4]}; keys that differ {differ}"
             + (f"; known skips in the containers: {[(t, KNOWN_SKIPS[t]) for t in skips]}"
                if skips else ""))
        if ARCHIVE:
            (ARCHIVE / "parity").mkdir(exist_ok=True)
            (ARCHIVE / "parity" / f"{f.replace('/', '_')}.json").write_text(json.dumps(
                {"host": h.to_dict(), "container_verify": cv.to_dict(), "container_agent": ca.to_dict()},
                indent=1, sort_keys=True))


def s_parity(only):
    from fvh import tools
    from fvh.tools import runners as R
    host = tools.HostRunner(ROOT)
    for mid, unit in armed_units(only):
        lang = "verus" if unit.startswith("verus/") else "dafny"    # a unit directory
        mem = 16 if lang == "verus" else None
        h = host.execute("vcheck --gate", unit)
        cv = tools.ContainerRunner(ROOT, mem_gb=mem).execute("vcheck --gate", unit)
        m = build(unit, R.HostRunner(ROOT).argv("vcheck --gate", unit), kind="agent", mem_gb=mem or 15.5,
                  run_id=f"doors-parity-{mid.lower()}-{lang}")
        code, rec, err = run(m, f"parity-{mid}-{lang}")
        try:
            c = rec["commands"][0]
            ca = R.make_result("vcheck --gate", unit, h.provenance, "container", c["exit_code"],
                               c["stdout"], c["stderr"], c.get("killed") == "wall-clock",
                               R._redactor(Path(rec["root"]), rec["scratch"]), True)
        except (TypeError, KeyError, IndexError) as e:
            note("parity", f"C20 {unit}", False, f"the agent-mode run failed: exit {code} {e} {err[-300:]}")
            continue

        def key(r):
            d = r.document
            holes = sorted((x.get("file"), x.get("line"), x.get("col"), x.get("kind"), x.get("label"))
                           for x in d.get("holes", []) or [])
            return (d.get("verdict"), d.get("verified_count"), d.get("exit_code"), holes)
        same = key(h) == key(cv) == key(ca)
        keys = sorted(set(h.document) | set(cv.document) | set(ca.document))
        differ = [k for k in keys if not (h.document.get(k) == cv.document.get(k) == ca.document.get(k))]
        # the one expected difference: `cmd` names the toolchain where it is installed
        # (the checkout's .toolchain/ on the host, /opt/dvl/toolchain/ in the images)
        docs = f"keys that differ {differ}; the two container modes' documents equal {cv.document == ca.document}"
        same = same and set(differ) <= {"cmd"}
        note("parity", f"C20 {unit}", same and h.killed is None,
             f"host {key(h)[:3]} holes {len(key(h)[3])}; container-verify {key(cv)[:3]}; "
             f"container-agent {key(ca)[:3]}; {docs}; output sha256 equal "
             f"{h.output_sha256 == cv.output_sha256 == ca.output_sha256}")
        if ARCHIVE:
            (ARCHIVE / "parity").mkdir(exist_ok=True)
            (ARCHIVE / "parity" / f"{unit.replace('/', '_')}.json").write_text(json.dumps(
                {"host": h.to_dict(), "container_verify": cv.to_dict(), "container_agent": ca.to_dict()},
                indent=1, sort_keys=True))


def s_e2e():
    from fvh import budget, executor, policies, protocol, tools
    text = (ROOT / DAFNY_T).read_text(encoding="utf-8")
    host = tools.HostRunner(ROOT).execute("vcheck --gate", DAFNY_T).document
    ctx = protocol.Context("doors-e2e", "dafny", "a neutral fixture task", (DAFNY_T,), (), DAFNY_T)
    edited = text + "\n// a scripted edit, a comment only\n"
    broken = text + "\nthis line is not a Dafny declaration\n"
    # the positive control: a neutral program that verifies (no item of the file's task)
    neutral = "lemma DoorsFixture(n: nat)\n  ensures n + 0 == n\n{\n}\n"
    script = policies.ScriptedPolicy([
        [protocol.Read(DAFNY_T, 1, 5)],
        [protocol.Verify("gate")],
        [protocol.Edit(DAFNY_T, "", edited), protocol.Verify("gate")],
        [protocol.Edit(DAFNY_T, "", broken), protocol.Verify("gate")],
        [protocol.Edit(DAFNY_T, "", neutral), protocol.Verify("gate")],
        [protocol.Stop("give-up", "the doors' script ends")]])
    rd = Path(tempfile.mkdtemp(prefix="e2e-scripted-", dir=TMP))
    ex = executor.Executor(ctx, {DAFNY_T: text}, runner=tools.ContainerRunner(ROOT), run_dir=rd,
                           root=ROOT, meter=budget.Meter())
    res = ex.run(script)
    keep("e2e-scripted", rd)
    obs = [json.loads(x) for x in (rd / "observations.jsonl").read_text().splitlines()]
    verdicts = [t["verdict"] for o in obs for t in o["tools"]
                for t in [t["document"]] if isinstance(t, dict) and "verdict" in t]
    stages = [t["document"].get("stage") for o in obs for t in o["tools"]]
    note("e2e", "Scripted: four verifications, each in its own container",
         len(verdicts) == 4 and all(t["runner"] == "container" for o in obs for t in o["tools"]),
         f"verdicts {verdicts}, stages {stages}")
    note("e2e", "Scripted: the course file's verdict equals the host's",
         verdicts[:1] == [host.get("verdict")], f"host {host.get('verdict')}, container {verdicts[:1]}")
    note("e2e", "Scripted: the edited work copy is what the container verified",
         len(stages) == 4 and stages[2] == "parse" and verdicts[2] == "failed",
         f"after the breaking edit: {verdicts[2:3]} at stage {stages[2:3]}")
    note("e2e", "Scripted: a verifying work copy passes the gate in the container",
         len(verdicts) == 4 and verdicts[3] == "verified", f"after the neutral program: {verdicts[3:]}")
    note("e2e", "Scripted: the run's outcome", res.outcome == "verified" and res.ended_by == "stop",
         f"outcome {res.outcome}, ended_by {res.ended_by}, steps {res.steps}")

    def mock(state, ctx_, b):
        return [protocol.Verify("gate")] if state.step == 0 else [protocol.Stop("done", "")]
    rd2 = Path(tempfile.mkdtemp(prefix="e2e-mock-", dir=TMP))
    res2 = executor.Executor(ctx, {DAFNY_T: text}, runner=tools.ContainerRunner(ROOT), run_dir=rd2,
                             root=ROOT, meter=budget.Meter()).run(policies.MockPolicy(mock))
    keep("e2e-mock", rd2)
    note("e2e", "Mock: one verification, the outcome its verdict",
         res2.outcome == host.get("verdict") and res2.ended_by == "stop" and (rd2 / "verify.json").is_file(),
         f"outcome {res2.outcome}, ended_by {res2.ended_by}")


def s_exposure():
    lock = sandbox.read_images_lock(ROOT)
    img = next(k for k in lock if k.startswith("dvl-toolchain@"))
    net = f"dvl-exposure-{os.getpid()}"
    targets, info = sandbox.host_targets(limit=512)
    subprocess.run(["docker", "network", "create", "--internal", "--label", "dvl.run=doors-exposure",
                    net], capture_output=True, check=True)
    try:
        insp = json.loads(subprocess.run(["docker", "network", "inspect", net], capture_output=True,
                                         text=True, check=True).stdout)[0]
        gw = insp["IPAM"]["Config"][0].get("Gateway")
        ports = info["ports"]
        pairs = [(gw, p) for p in ports] + [t for t in targets]
        code = ("import json,socket,sys\nres=[]\n"
                "for a,p in json.loads(sys.argv[1]):\n"
                " s=socket.socket(socket.AF_INET6 if ':' in a else socket.AF_INET); s.settimeout(1)\n"
                " try:\n  s.connect((a,p)); res.append([a,p,'answered'])\n"
                " except OSError as e: res.append([a,p,type(e).__name__])\n"
                " finally: s.close()\n"
                "print(json.dumps(res))\n")
        p = subprocess.run(["docker", "run", "--rm", "--network", net, "--memory", "256m",
                            "--memory-swap", "256m", "--cap-drop", "ALL", "--read-only", "--user",
                            "1000:1000", "--security-opt", "no-new-privileges", img, sandbox.CONTAINER_PYTHON,
                            "-c", code, json.dumps(pairs)], capture_output=True, text=True, timeout=900)
        res = json.loads(p.stdout or "[]")
    finally:
        subprocess.run(["docker", "network", "rm", net], capture_output=True)
    answered = sorted({f"{a}:{p}" for a, p, r in res if r == "answered"})
    gw_open = sorted({p for a, p, r in res if a == gw and r == "answered"})
    if ARCHIVE:
        (ARCHIVE / "exposure.json").write_text(json.dumps(
            {"gateway": gw, "host_listeners": info, "results": res}, indent=1))
    # a record, not a pass condition: Route B (the plan of record) has no network at all
    note("exposure", "recorded", bool(res), f"internal network gateway {gw}: host ports answering "
         f"there {gw_open}; {len(answered)} of {len(res)} address:port pairs answered in all; IPv6 "
         f"is off on the network (EnableIPv6 {insp.get('EnableIPv6')})")


def main(argv=None):
    global ARCHIVE, TMP
    ap = argparse.ArgumentParser(prog="sandbox_doors.py")
    ap.add_argument("sections", nargs="*", default=["all"])
    ap.add_argument("--archive")
    ap.add_argument("--units", default="Q01,Q02,Q03,Q04,Q05,Q06")
    ap.add_argument("--py-units", default="armed")
    a = ap.parse_args(argv)
    want = SECTIONS if a.sections in (["all"], []) else a.sections
    bad = [s for s in want if s not in SECTIONS]
    if bad:
        ap.error(f"unknown section(s) {bad}; sections: {', '.join(SECTIONS)}")
    if a.archive:
        ARCHIVE = Path(a.archive)
        ARCHIVE.mkdir(parents=True, exist_ok=True)
    TMP = tempfile.mkdtemp(prefix="dvl-doors-")
    try:
        for s in want:
            try:
                if s == "parity":
                    s_parity(set(a.units.split(",")))
                    s_parity_python(a.py_units)
                else:
                    globals()[f"s_{s}"]()
            except Exception as e:  # noqa: BLE001 - a section that breaks is a failure, recorded
                note(s, "section", False, f"{type(e).__name__}: {e}")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    n_bad = sum(1 for r in RESULTS if not r["ok"])
    print(f"sandbox_doors: {len(RESULTS) - n_bad} passed, {n_bad} failed")
    if ARCHIVE:
        (ARCHIVE / "results.json").write_text(json.dumps(RESULTS, indent=1))
    return 1 if n_bad else 0


if __name__ == "__main__":
    sys.exit(main())
