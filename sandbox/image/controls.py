#!/usr/bin/python3
"""The in-container containment controls (/opt/dvl/bin/controls; DV4-PLAN §5.4 item 6).

    controls check          read a JSON request on stdin, print a JSON report
    controls door <name> …  one regression fixture of tests/acceptance/sandbox_doors.py
                            (only in `scripts/mksandbox-run --probe` runs)

`check` runs before anything else in every live run, as uid 1000 with no
capability, and reports each control as {id, ok, detail}; scripts/mksandbox-run
stops the run (infra-failed) when one fails. The controls are neutral
regression checks: each is a plain operation that must be refused, beside a
positive control that must work.

  C1  the effective capability set is empty, the user is uid 1000, no new privileges
  C2  the root file system, /usr, /opt and every read-only input under /work refuse
      a write; /tmp, the home tmpfs and the editable directories accept one
  C3  no container-runtime socket is reachable
  C4  no network interface but loopback, and no route
  C5  (model networks) the relay answers GET /api/version on 127.0.0.1
  C6  (model networks) no host listener answers on any address the run names
  C7  no public address answers (IPv4 and IPv6)
  C8  no public name resolves

The doors (`door <name>`) make the operations the acceptance script expects
the sandbox to bound: memory (`alloc`), processes (`pids`), wall clock
(`sleep`), the return path (`stage-return <dir>`), a credential-shaped string
in a returned file (`secret <file>`), and one request through the relay
(`http METHOD PATH MODEL [option=value …]`, the gate's controls C9-C11).
Standard library only.
"""

import errno
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

RUNTIME_SOCKETS = ("/var/run/docker.sock", "/run/docker.sock", "/run/containerd/containerd.sock",
                   "/var/run/containerd/containerd.sock", "/run/podman/podman.sock",
                   "/run/user/1000/docker.sock", "/run/user/1000/podman/podman.sock",
                   "/run/crio/crio.sock", "/run/buildkit/buildkitd.sock")
REFUSED_WRITE = (errno.EROFS, errno.EACCES, errno.EPERM)


def _status():
    out = {}
    with open("/proc/self/status", encoding="ascii") as fh:
        for line in fh:
            k, _, v = line.partition(":")
            out[k] = v.strip()
    return out


def c1():
    st = _status()
    caps = {k: st.get(k, "?") for k in ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb")}
    uid = st.get("Uid", "").split()
    ok = (all(int(v, 16) == 0 for v in caps.values() if v != "?") and "?" not in caps.values()
          and uid[:1] == ["1000"] and st.get("NoNewPrivs") == "1")
    return ok, f"Uid {' '.join(uid)}; " + ", ".join(f"{k} {v}" for k, v in caps.items()) + \
        f"; NoNewPrivs {st.get('NoNewPrivs')}; Seccomp {st.get('Seccomp')}"


def _try_create(d):
    p = os.path.join(d, f".dvl-control-{os.getpid()}")
    try:
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as e:
        return False, errno.errorcode.get(e.errno, str(e.errno))
    os.close(fd)
    os.unlink(p)
    return True, "written"


def c2(req):
    bad = []
    edirs = [x.strip("/") for x in req.get("editable_dirs", [])]
    roots = ("/", "/usr", "/opt", "/etc", "/opt/dvl") + (() if "" in edirs else ("/work",))
    for d in roots:
        ok, why = _try_create(d)
        if ok:
            bad.append(f"{d} accepted a new file")
    for rel in req.get("readonly", []):
        p = os.path.join("/work", rel)
        try:
            fd = os.open(p, os.O_WRONLY | os.O_APPEND)
        except OSError as e:
            if e.errno not in REFUSED_WRITE:
                bad.append(f"/work/{rel}: {errno.errorcode.get(e.errno, e.errno)}")
            continue
        os.close(fd)
        bad.append(f"/work/{rel} opened for writing")
    good = []
    for d in ["/tmp", os.environ.get("HOME", "/home/agent")] + [os.path.join("/work", x) if x
                                                               else "/work" for x in edirs]:
        ok, why = _try_create(d)
        if ok:
            good.append(d)
        else:
            bad.append(f"{d} refused a write ({why})")
    return not bad, (f"{len(req.get('readonly', []))} read-only inputs and the root refused; "
                     f"writable: {', '.join(good)}" if not bad else "; ".join(bad))


def c3():
    found = [p for p in RUNTIME_SOCKETS if os.path.lexists(p)]
    return not found, ("no runtime socket" if not found else "present: " + ", ".join(found))


def c4():
    ifaces = sorted(os.listdir("/sys/class/net"))
    routes = []
    try:
        with open("/proc/net/route", encoding="ascii") as fh:
            routes = [ln.split()[0] for ln in fh.readlines()[1:] if ln.strip()]
    except OSError:
        pass
    ok = ifaces == ["lo"] and not routes
    return ok, f"interfaces {ifaces}; IPv4 routes {len(routes)}"


def c5(req):
    port = int(req.get("relay_port", 11434))
    url = f"http://127.0.0.1:{port}{req.get('relay_path', '/api/version')}"
    try:
        with urllib.request.urlopen(url, timeout=float(req.get("timeout_s", 3)) * 3) as r:
            body = r.read(4096).decode("utf-8", "replace")
            return r.status == 200, f"GET {url}: {r.status} {body[:120]!r}"
    except Exception as e:  # noqa: BLE001 - the report names whatever failed
        return False, f"GET {url}: {type(e).__name__}: {e}"


def _connect(addr, port, timeout):
    fam = socket.AF_INET6 if ":" in addr else socket.AF_INET
    s = socket.socket(fam, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((addr, int(port)))
        return True, "connected"
    except OSError as e:
        return False, type(e).__name__ if e.errno is None else errno.errorcode.get(e.errno, str(e.errno))
    finally:
        s.close()


def c6(req):
    t = float(req.get("timeout_s", 2))
    targets = req.get("host_targets", [])
    open_ = []
    reasons = {}
    for addr, port in targets:
        ok, why = _connect(addr, port, t)
        if ok:
            open_.append(f"{addr}:{port}")
        reasons[why] = reasons.get(why, 0) + 1
    return not open_, (f"{len(targets)} host address:port pairs, none answered ({reasons})"
                       if not open_ else "answered: " + ", ".join(open_))


def c7(req):
    t = float(req.get("timeout_s", 2))
    out, bad = [], []
    for addr, port in req.get("public", [["1.1.1.1", 443], ["2606:4700:4700::1111", 443]]):
        ok, why = _connect(addr, port, t)
        (bad if ok else out).append(f"{addr}:{port} {why}")
    return not bad, "; ".join(bad or out)


def c8(req):
    name = req.get("public_name", "example.com")
    try:
        infos = socket.getaddrinfo(name, 443)
    except socket.gaierror as e:
        return True, f"{name}: {e.args[-1] if e.args else e}"
    except OSError as e:
        return True, f"{name}: {type(e).__name__}"
    return False, f"{name} resolved to {sorted({i[4][0] for i in infos})}"


def check(req):
    res = []

    def add(cid, fn, *a):
        try:
            ok, detail = fn(*a)
        except Exception as e:  # noqa: BLE001
            ok, detail = False, f"the control raised {type(e).__name__}: {e}"
        res.append({"id": cid, "ok": bool(ok), "detail": detail})

    add("C1", c1)
    add("C2", c2, req)
    add("C3", c3)
    add("C4", c4)
    if req.get("network", "none") != "none":
        add("C5", c5, req)
        add("C6", c6, req)
    add("C7", c7, req)
    add("C8", c8, req)
    return {"schema": 1, "ok": all(r["ok"] for r in res), "controls": res}


# --- the doors (tests/acceptance/sandbox_doors.py) --------------------------------------------

def door_alloc(args):
    step = 64 << 20
    held = []
    total = 0
    while True:
        b = bytearray(step)
        for i in range(0, step, 4096):
            b[i] = 1
        held.append(b)
        total += step
        print(f"held {total >> 20} MiB", flush=True)


def door_pids(args):
    n, procs = 0, []
    limit = int(args[0]) if args else 10000
    try:
        while n < limit:
            procs.append(subprocess.Popen(["/bin/sleep", "30"]))
            n += 1
    except OSError as e:
        print(json.dumps({"spawned": n, "stopped_by": errno.errorcode.get(e.errno, str(e.errno))}),
              flush=True)
    else:
        print(json.dumps({"spawned": n, "stopped_by": None}), flush=True)
    for p in procs:
        p.kill()
    for p in procs:
        p.wait()
    return 0


def door_sleep(args):
    time.sleep(float(args[0]) if args else 3600)
    return 0


def door_stage_return(args):
    d = os.path.join("/work", args[0])
    keep = args[1] if len(args) > 1 else None
    rep = {}
    with open(os.path.join(d, "unlisted.txt"), "w") as fh:
        fh.write("an unlisted file\n")
    rep["unlisted"] = True
    os.symlink("/etc/passwd", os.path.join(d, "link-to-host-path"))
    rep["symlink"] = True
    os.mkfifo(os.path.join(d, "a-fifo"))
    rep["fifo"] = True
    if keep:
        os.link(os.path.join(d, keep), os.path.join(d, "hard-link"))
        rep["hardlink"] = True
    with open(os.path.join(d, "big.txt"), "w") as fh:
        fh.write("x" * ((1 << 20) + 1))
    rep["oversize"] = True
    n = 0
    try:
        with open(os.path.join(d, "fill.bin"), "wb") as fh:
            while True:
                fh.write(b"\0" * (1 << 20))
                fh.flush()
                n += 1
    except OSError as e:
        rep["fill_stopped"] = errno.errorcode.get(e.errno, str(e.errno))
    rep["fill_mib"] = n
    os.unlink(os.path.join(d, "fill.bin"))
    print(json.dumps(rep), flush=True)
    return 0


def door_secret(args):
    p = os.path.join("/work", args[0])
    with open(p, "a") as fh:
        # a fabricated string in a credential format (never a real token)
        fh.write("\n// sk-ant-oat01-" + "Q" * 40 + "\n")
    print("appended", flush=True)
    return 0


def _num(v):
    for t in (int, float):
        try:
            return t(v)
        except ValueError:
            pass
    return v


def door_http(args):
    """One request through the relay: METHOD PATH MODEL [option=value …]."""
    method, path, model = args[0], args[1], args[2]
    opts = {k: _num(v) for k, v in (a.split("=", 1) for a in args[3:])}
    body = None
    if method == "POST":
        msgs = [{"role": "user", "content": "door"}]
        if path == "/api/chat":
            body = {"model": model, "messages": msgs, "stream": False, "options": opts}
        elif path == "/v1/chat/completions":
            body = {"model": model, "messages": msgs, "stream": False, **opts}
        else:
            body = {"model": model, "name": model}
    req = urllib.request.Request(f"http://127.0.0.1:11434{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status, text = r.status, r.read(4096).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        status, text = e.code, e.read(4096).decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        status, text = None, f"{type(e).__name__}: {e}"
    print(json.dumps({"method": method, "path": path, "status": status, "body": text[:1000]}),
          flush=True)
    return 0


DOORS = {"http": door_http, "alloc": door_alloc, "pids": door_pids, "sleep": door_sleep,
         "stage-return": door_stage_return, "secret": door_secret}


def main(argv):
    if len(argv) >= 2 and argv[1] == "check":
        req = json.loads(sys.stdin.read() or "{}")
        rep = check(req)
        print(json.dumps(rep, sort_keys=True))
        return 0 if rep["ok"] else 1
    if len(argv) >= 3 and argv[1] == "door" and argv[2] in DOORS:
        return DOORS[argv[2]](argv[3:]) or 0
    print("usage: controls check | controls door " + "|".join(sorted(DOORS)) + " …", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
