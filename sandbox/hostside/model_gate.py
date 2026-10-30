#!/usr/bin/env python3
"""model_gate.py: the host-side model gate, one per run (DV4-PLAN §5.6.3; Δ146;
an OpenAI-compatible model server since DELTAS Δ505).

Every Qwen request of every mode passes a gate; fvh and the sandbox never
talk to the model server directly. The model server is not the course's: an
OpenAI-compatible server the host already runs on localhost (127.0.0.1) port
8000 or 8001 (Δ505). The gate is a small HTTP proxy (standard library) in
front of it:

    model_gate.py --socket PATH | --port N [--bind ADDR]   --config CONFIG.json
                  --log GATE.log [--counts COUNTS.json] [--upstream URL] [--ready FILE]
                  [--owner-pid PID]

  --socket PATH  listen on a Unix socket, mode 0600 (Route B's; no run uses
                 it since Route C, the unit tests still do)
  --port N       listen on TCP instead (host policy runs; and Route C, DELTAS
                 Δ504: a sandbox run's gate container forwards to it); 0 picks
                 a free port, written to --ready
  --bind ADDR    the TCP address (default 127.0.0.1): on Linux a run's
                 upstream bridge's gateway address, which only that run's gate
                 container reaches; a loopback or private address only
  --upstream     the model server's OpenAI base URL, a loopback http URL with
                 its path (the one discover() found; the config's "upstream"
                 otherwise). Loopback only: the gate sends no key
  --config       the run's settings (JSON): {"model": <the served model id>,
                 "options": {...}, "caps": {"calls": n, "tokens": n, "gpu_s": s},
                 "margin": 512, "max_model_len": <the served one, or null>,
                 "check_served": <bool, optional>, "upstream": <base URL>,
                 "seeds": <the run's per-request seeds, optional>}
  --log          one JSON line per request and response, prompts and replies
                 included (gate.log in the run directory)
  --counts       the running totals (JSON), rewritten after every request
  --ready        a file written once the gate listens (its address)

For every request it:
  - admits only POST /v1/chat/completions and GET /v1/models, and answers
    403 to everything else, logged;
  - admits only the run's model id (403 otherwise, logged);
  - sets the course's sampling options as OpenAI request fields
    (temperature, top_p, top_k, seed, max_tokens; a server that ignores one
    still receives it) and logs every value it overrode; a client's
    max_completion_tokens gives way to max_tokens; a streamed request gets
    stream_options.include_usage, so its last chunk carries the usage;
  - counts calls and tokens from the response's `usage` (prompt, completion
    and, where the server reports them, reasoning tokens, which are part of
    the completion count) and the request's busy seconds as GPU-seconds,
    and answers 429 once a cap is reached;
  - flags `ctx-saturated` when a prompt's token count reaches max_model_len
    less the margin (only when the server reports a max_model_len), and
    whenever the server refuses a request for its context length;
  - records the first system_fingerprint a response carries (counts and log);
  - passes streamed responses through unchanged, chunk by chunk.
One request is in flight at a time. It never retries a request.

The live batch runner (fvh.batch) adds two config keys and one option, so
that a lab's repeats are independent samples and a host gate never outlives
its run:
  - "seeds": [s0, s1, ...]: the n-th admitted inference request of the run
    gets seed s_n in place of the "seed" option (logged as an override when
    the client sent another), and a request past the list is answered 429
    ("the run's seeds are used up"); without the key every request gets the
    configured seed (Q07's single replay);
  - "seeds" are pre-registered per run by the batch plan (fvh.batch's
    derivation), never chosen by the client;
  - --owner-pid PID: the gate stops once that process is gone, so a runner
    killed mid-batch leaves no gate.

Two of the gate's own upstream requests at start, never a client's, both
read only, with "check_served": GET <base>/models (the run's model id must
still be served, or the gate exits 3 before it listens; the served
max_model_len, when reported, is the context check's) and GET /version at
the server's root (logged and counted as an observed fact; null where the
server has none).

discover(endpoints, url=None, model=None) is the one place that finds the
server and its model (fvh.backends.gate and scripts/dvl/sandbox.py load it
from this file): the first base URL whose GET /models answers (DVL_MODEL_URL,
when set, in place of the list), its only served model (or DVL_MODEL), the
served max_model_len (or None) and /version (or None).
"""

import argparse
import http.client
import http.server
import json
import os
import re
import socketserver
import sys
import threading
import time
import urllib.parse

URL_ENV, MODEL_ENV = "DVL_MODEL_URL", "DVL_MODEL"
LOOPBACK_URL = re.compile(r"http://127\.0\.0\.1:\d{1,5}(/[A-Za-z0-9._~/-]*)?")
INFERENCE = {"/v1/chat/completions"}
OPEN_GET = {"/v1/models"}
CLIENT_PREFIX = "/v1"
MAX_BODY = 8 << 20
# what an OpenAI-compatible server's refusal of an over-long request says ("This
# model's maximum context length is N tokens ...", "max_tokens=N cannot be
# greater than max_model_len=M", "... is too large: ..." and the like)
CTX_ERROR = re.compile(r"context length|context window|max_model_len|maximum context|"
                       r"prompt is too long|too many tokens|is too large", re.I)
CTX_STATUS = (400, 413, 422)


class Gate:
    def __init__(self, cfg, upstream, log_path, counts_path):
        self.cfg = cfg
        u = urllib.parse.urlsplit(upstream)
        if u.scheme != "http" or not u.hostname:
            raise ValueError(f"--upstream must be an http URL, not {upstream!r}")
        self.up_host, self.up_port = u.hostname, u.port or 80
        self.up_base = u.path.rstrip("/")         # "/v1" on an OpenAI-compatible server
        self.log_path = log_path
        self.counts_path = counts_path
        self.lock = threading.Lock()          # one request in flight
        self.log_lock = threading.Lock()
        self.counts = {"calls": 0, "prompt_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0,
                       "tokens": 0, "gpu_s": 0.0, "refused": 0, "capped": 0, "ctx_saturated": 0,
                       "other_served": [], "server_version": None, "system_fingerprint": None,
                       "overrides": 0, "admitted": 0}
        seeds = cfg.get("seeds")
        if seeds is not None and (not isinstance(seeds, list) or not all(
                isinstance(x, int) and not isinstance(x, bool) and x >= 0 for x in seeds)):
            raise ValueError("the config's seeds must be a list of integers >= 0")
        self.seeds = seeds
        mml = cfg.get("max_model_len")
        self.max_model_len = mml if isinstance(mml, int) and not isinstance(mml, bool) else None
        self.write_counts()

    # --- records ---------------------------------------------------------------------------

    def log(self, rec):
        rec = {"t": round(time.time(), 3), **rec}
        with self.log_lock, open(self.log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")

    def write_counts(self):
        if not self.counts_path:
            return
        tmp = self.counts_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.counts, fh, sort_keys=True, indent=1)
        os.replace(tmp, self.counts_path)

    # --- policy ----------------------------------------------------------------------------

    def cap_reached(self):
        caps = self.cfg.get("caps") or {}
        c = self.counts
        for unit, have in (("calls", c["calls"]), ("tokens", c["tokens"]), ("gpu_s", c["gpu_s"])):
            lim = caps.get(unit)
            if isinstance(lim, (int, float)) and have >= lim:
                return unit
        return None

    def next_seed(self):
        """The seed of the next admitted inference request: the run's n-th seed
        when the config lists seeds (None once they are used up), else the
        pinned option's (None when there is no pin either)."""
        n = self.counts["admitted"]
        if self.seeds is None:
            return (self.cfg.get("options") or {}).get("seed")
        return self.seeds[n] if n < len(self.seeds) else None

    def pin(self, body, seed=None):
        """Set the pinned options on a request body as OpenAI fields (and the run's
        seed for this request, when the config lists seeds); returns the overrides."""
        pins = dict(self.cfg.get("options") or {})
        if seed is not None:
            pins["seed"] = seed
        over = []
        for k, v in sorted(pins.items()):
            if k in body and body[k] != v:
                over.append({"option": k, "sent": body[k], "pinned": v})
            body[k] = v
        if "max_tokens" in pins and "max_completion_tokens" in body:
            over.append({"option": "max_completion_tokens", "sent": body.pop("max_completion_tokens"),
                         "pinned": None, "note": "the pinned max_tokens caps the output"})
        if body.get("stream") is True:
            so = body.get("stream_options") if isinstance(body.get("stream_options"), dict) else {}
            if so.get("include_usage") is not True:
                if "include_usage" in so:
                    over.append({"option": "stream_options.include_usage",
                                 "sent": so["include_usage"], "pinned": True})
                body["stream_options"] = {**so, "include_usage": True}
        return over

    def _upstream(self, method, path, timeout=30):
        c = http.client.HTTPConnection(self.up_host, self.up_port, timeout=timeout)
        try:
            c.request(method, path)
            r = c.getresponse()
            return r.status, r.read()
        finally:
            c.close()

    def served(self):
        """The server's /models list as [{id, max_model_len}] (None when
        unreachable or not a model list)."""
        try:
            status, raw = self._upstream("GET", self.up_base + "/models")
            data = json.loads(raw or b"{}")
        except (OSError, ValueError, http.client.HTTPException):
            return None
        if status != 200 or not isinstance(data, dict) or not isinstance(data.get("data"), list):
            return None
        return [{"id": m.get("id"), "max_model_len": m.get("max_model_len")}
                for m in data["data"] if isinstance(m, dict)]

    def server_version(self):
        """GET /version at the server's root, where it has one; None elsewhere."""
        try:
            status, raw = self._upstream("GET", "/version", timeout=10)
            data = json.loads(raw or b"{}")
        except (OSError, ValueError, http.client.HTTPException):
            return None
        return data.get("version") if status == 200 and isinstance(data, dict) else None


class DiscoveryError(RuntimeError):
    """No model server answers, or its model cannot be chosen: no run starts."""


def _get_json(url, timeout):
    """(status, JSON) of a GET, (None, None) when nothing answers."""
    u = urllib.parse.urlsplit(url)
    try:
        c = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=timeout)
        try:
            c.request("GET", u.path or "/")
            r = c.getresponse()
            return r.status, json.loads(r.read() or b"null")
        finally:
            c.close()
    except (OSError, ValueError, http.client.HTTPException):
        return None, None


def discover(endpoints, url=None, model=None, timeout=5.0):
    """The host's model server and model (module docstring) as {"base_url",
    "model", "max_model_len", "served", "version"}; DiscoveryError otherwise.
    `url` and `model` default to DVL_MODEL_URL and DVL_MODEL."""
    url = url if url is not None else (os.environ.get(URL_ENV) or None)
    model = model if model is not None else (os.environ.get(MODEL_ENV) or None)
    cands = [url] if url else list(endpoints or [])
    if not cands:
        raise DiscoveryError("no model server address to try (the apparatus file's "
                             f"[model_gate] endpoints, or {URL_ENV})")
    tried = []
    for base in cands:
        if not isinstance(base, str) or not LOOPBACK_URL.fullmatch(base.rstrip("/")):
            raise DiscoveryError(f"{base!r} is not a loopback http URL (http://127.0.0.1:PORT/v1; "
                                 "never `localhost`, which may resolve to ::1)")
        base = base.rstrip("/")
        status, data = _get_json(base + "/models", timeout)
        if status == 200 and isinstance(data, dict) and isinstance(data.get("data"), list):
            served = [m for m in data["data"] if isinstance(m, dict) and isinstance(m.get("id"), str)]
            ids = [m["id"] for m in served]
            if model is not None:
                if model not in ids:
                    raise DiscoveryError(f"{MODEL_ENV}={model} is not served at {base} (it serves "
                                         f"{', '.join(ids) or 'none'})")
                pick = model
            elif len(ids) == 1:
                pick = ids[0]
            else:
                raise DiscoveryError(f"{base} serves {len(ids)} models ({', '.join(ids) or 'none'}): "
                                     f"set {MODEL_ENV} to the one to use")
            mml = next(m.get("max_model_len") for m in served if m["id"] == pick)
            if isinstance(mml, bool) or not isinstance(mml, int) or mml < 1:
                mml = None
            u = urllib.parse.urlsplit(base)
            vs, vd = _get_json(f"{u.scheme}://{u.netloc}/version", timeout)
            version = vd.get("version") if vs == 200 and isinstance(vd, dict) else None
            return {"base_url": base, "model": pick, "max_model_len": mml, "served": ids,
                    "version": version if isinstance(version, str) else None}
        tried.append(base)
    raise DiscoveryError("no OpenAI-compatible model server answers GET /models at "
                         + ", ".join(tried) + " (start yours on localhost (127.0.0.1) port 8000 "
                         f"or 8001, or set {URL_ENV})")


def usage_from(text):
    """(prompt tokens, completion tokens, reasoning tokens, system_fingerprint) from
    a response body, streamed (SSE `data:` lines) or not."""
    p = o = rsn = fp = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            line = line[5:].strip()
        if not line.startswith("{"):
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if not isinstance(d, dict):
            continue
        if isinstance(d.get("system_fingerprint"), str):
            fp = d["system_fingerprint"]
        u = d.get("usage")
        if isinstance(u, dict):
            p, o = u.get("prompt_tokens", p), u.get("completion_tokens", o)
            det = u.get("completion_tokens_details")
            if isinstance(det, dict) and isinstance(det.get("reasoning_tokens"), int):
                rsn = det["reasoning_tokens"]
    return p, o, rsn, fp


def make_handler(gate):
    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "dvl-model-gate"

        def address_string(self):
            return "relay"

        def log_message(self, fmt, *args):      # the gate keeps its own log
            pass

        def answer(self, code, obj):
            data = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def refuse(self, code, why, **extra):
            gate.counts["refused" if code == 403 else "capped"] += 1
            gate.write_counts()
            gate.log({"event": "refused", "status": code, "method": self.command, "path": self.path,
                      "why": why, **extra})
            self.answer(code, {"error": why})

        def do_GET(self):
            path = urllib.parse.urlsplit(self.path).path
            if path not in OPEN_GET:
                return self.refuse(403, f"GET {path} is not an endpoint this gate admits")
            self.forward(None, False, path)

        def do_POST(self):
            path = urllib.parse.urlsplit(self.path).path
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                return self.refuse(403, "the request body is over the gate's size cap")
            raw = self.rfile.read(n) if n else b""
            if path not in INFERENCE:
                return self.refuse(403, f"POST {path} is not an endpoint this gate admits")
            try:
                body = json.loads(raw or b"{}")
                assert isinstance(body, dict)
            except (ValueError, AssertionError):
                return self.refuse(403, "the request body is not a JSON object")
            model = body.get("model")
            if model != gate.cfg.get("model"):
                return self.refuse(403, f"model {model!r} is not the run's pinned model",
                                   model=model)
            cap = gate.cap_reached()
            if cap:
                return self.refuse(429, f"the run's {cap} cap is reached")
            with gate.lock:
                seed = gate.next_seed()
                if gate.seeds is not None and seed is None:
                    return self.refuse(429, "the run's seeds are used up")
                gate.counts["admitted"] += 1
            over = gate.pin(body, seed=seed if gate.seeds is not None else None)
            if over:
                gate.counts["overrides"] += len(over)
            self.forward(body, True, path, over, seed=seed)

        do_PUT = do_DELETE = do_PATCH = do_HEAD = lambda self: self.refuse(  # noqa: E731
            403, f"{self.command} is not a method this gate admits")

        def forward(self, body, inference, path, over=(), seed=None):
            data = json.dumps(body).encode() if body is not None else None
            up_path = gate.up_base + path[len(CLIENT_PREFIX):]
            with gate.lock:
                started = time.monotonic()
                try:
                    up = http.client.HTTPConnection(gate.up_host, gate.up_port, timeout=3600)
                    hdrs = {"Content-Type": "application/json"} if data is not None else {}
                    up.request(self.command, up_path, body=data, headers=hdrs)
                    r = up.getresponse()
                except (OSError, http.client.HTTPException) as e:
                    gate.log({"event": "upstream-error", "path": path, "error": type(e).__name__})
                    return self.answer(502, {"error": "the model server did not answer"})
                self.send_response(r.status)
                for k in ("Content-Type",):
                    if r.getheader(k):
                        self.send_header(k, r.getheader(k))
                self.send_header("Transfer-Encoding", "chunked")
                self.end_headers()
                got = bytearray()
                while True:
                    chunk = r.read1(65536)
                    if not chunk:
                        break
                    got += chunk
                    self.wfile.write(b"%x\r\n%s\r\n" % (len(chunk), chunk))
                    self.wfile.flush()
                busy = time.monotonic() - started
                up.close()
                # the records are written before the reply's last chunk, so that a
                # client that has its answer also finds it counted
                self.record(body, inference, path, over, r.status, busy, got, seed)
                self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()

        def record(self, body, inference, path, over, status, busy, got, seed=None):
            text = got.decode("utf-8", "replace")
            rec = {"event": "request", "method": self.command, "path": path, "status": status,
                   "busy_s": round(busy, 3), "request": body, "response": text[:1 << 20]}
            if inference and seed is not None:
                rec["seed"] = seed
            if over:
                rec["overrides"] = list(over)
            if inference:
                p, o, rsn, fp = usage_from(text)
                c = gate.counts
                c["calls"] += 1
                c["gpu_s"] = round(c["gpu_s"] + busy, 3)
                c["prompt_tokens"] += p or 0
                c["output_tokens"] += o or 0
                c["reasoning_tokens"] += rsn or 0
                c["tokens"] = c["prompt_tokens"] + c["output_tokens"]
                rec["usage"] = {"prompt_tokens": p, "output_tokens": o, "reasoning_tokens": rsn}
                if fp is not None:
                    rec["system_fingerprint"] = fp
                    if c["system_fingerprint"] is None:
                        c["system_fingerprint"] = fp
                mml = gate.max_model_len
                margin = int(gate.cfg.get("margin", 512))
                if status in CTX_STATUS and CTX_ERROR.search(text):
                    c["ctx_saturated"] += 1
                    rec["finding"] = "ctx-saturated"
                    rec["ctx"] = "refused by the server for its context length"
                elif p is not None and isinstance(mml, int) and p >= mml - margin:
                    c["ctx_saturated"] += 1
                    rec["finding"] = "ctx-saturated"
                gate.write_counts()
            gate.log(rec)

    return Handler


class UnixServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


class TCPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


def check_served(gate, cfg):
    """The start-up check of "check_served" (module docstring): 0, or 3 when the
    run's model is not served (or the server does not answer)."""
    found = gate.served()
    mine = next((m for m in found or [] if m["id"] == cfg["model"]), None)
    if mine is not None and isinstance(mine.get("max_model_len"), int) \
            and not isinstance(mine.get("max_model_len"), bool):
        gate.max_model_len = mine["max_model_len"]
    gate.counts["other_served"] = sorted(str(m["id"]) for m in found or [] if m["id"] != cfg["model"])
    gate.counts["server_version"] = gate.server_version()
    gate.write_counts()
    gate.log({"event": "served", "model": cfg["model"], "found": mine,
              "other_served": gate.counts["other_served"], "version": gate.counts["server_version"],
              "reachable": found is not None})
    if mine is None:
        why = "the model server does not answer" if found is None else \
            f"{cfg['model']} is not a model the server lists (it lists " \
            f"{', '.join(str(m['id']) for m in found) or 'none'})"
        print(f"model_gate: {why}", file=sys.stderr)
        return 3
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="model_gate.py", allow_abbrev=False)
    where = ap.add_mutually_exclusive_group(required=True)
    where.add_argument("--socket")
    where.add_argument("--port", type=int)
    ap.add_argument("--config", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--counts")
    ap.add_argument("--upstream")
    ap.add_argument("--ready")
    ap.add_argument("--owner-pid", type=int)
    ap.add_argument("--bind", default="127.0.0.1")
    a = ap.parse_args(argv)
    with open(a.config, encoding="utf-8") as fh:
        cfg = json.load(fh)
    if not isinstance(cfg.get("model"), str) or not cfg["model"]:
        print("model_gate: the config names no pinned model", file=sys.stderr)
        return 2
    upstream = a.upstream or cfg.get("upstream")
    if not isinstance(upstream, str) or not LOOPBACK_URL.fullmatch(upstream.rstrip("/")):
        print(f"model_gate: the upstream must be a loopback http URL, not {upstream!r}",
              file=sys.stderr)
        return 2
    try:
        gate = Gate(cfg, upstream, a.log, a.counts)
    except ValueError as e:
        print(f"model_gate: {e}", file=sys.stderr)
        return 2
    if cfg.get("check_served"):
        rc = check_served(gate, cfg)
        if rc:
            return rc
    handler = make_handler(gate)
    if a.socket:
        if os.path.lexists(a.socket):
            os.unlink(a.socket)
        old = os.umask(0o177)
        try:
            srv = UnixServer(a.socket, handler)
        finally:
            os.umask(old)
        os.chmod(a.socket, 0o600)
        addr = a.socket
    else:
        import ipaddress
        try:
            bind = ipaddress.ip_address(a.bind)
        except ValueError:
            print(f"model_gate: --bind {a.bind!r} is not an address", file=sys.stderr)
            return 2
        if not (bind.is_loopback or bind.is_private) or bind.is_unspecified:
            print(f"model_gate: --bind {a.bind}: a loopback or private address only",
                  file=sys.stderr)
            return 2
        srv = TCPServer((a.bind, a.port), handler)
        addr = f"http://{a.bind}:{srv.server_address[1]}"
    gate.log({"event": "start", "listen": addr, "upstream": upstream, "model": cfg["model"],
              "options": cfg.get("options") or {}, "caps": cfg.get("caps") or {},
              "max_model_len": gate.max_model_len, "seeds": cfg.get("seeds")})
    if a.ready:
        with open(a.ready, "w", encoding="utf-8") as fh:
            fh.write(addr + "\n")
    import signal
    signal.signal(signal.SIGTERM, lambda *_: threading.Thread(target=srv.shutdown, daemon=True).start())
    if a.owner_pid:
        def watch_owner():
            while True:
                time.sleep(1.0)
                try:
                    os.kill(a.owner_pid, 0)
                except ProcessLookupError:
                    gate.log({"event": "owner-gone", "owner_pid": a.owner_pid})
                    srv.shutdown()
                    return
                except PermissionError:
                    pass
        threading.Thread(target=watch_owner, daemon=True).start()
    try:
        srv.serve_forever(poll_interval=0.2)
    finally:
        srv.server_close()
        if a.socket and os.path.lexists(a.socket):
            os.unlink(a.socket)
        gate.log({"event": "stop", "counts": gate.counts})
    return 0


if __name__ == "__main__":
    sys.exit(main())
