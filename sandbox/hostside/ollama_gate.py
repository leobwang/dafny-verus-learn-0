#!/usr/bin/env python3
"""ollama_gate.py: the host-side Ollama gate, one per run (DV4-PLAN §5.6.3; Δ146).

Every Qwen request of every mode passes a gate; fvh and the sandbox never
talk to Ollama directly. The gate is a small HTTP proxy (standard library):

    ollama_gate.py --socket PATH | --port N   --config CONFIG.json   --log GATE.log
                   [--counts COUNTS.json] [--upstream URL] [--ready FILE]
                   [--owner-pid PID]

  --socket PATH  listen on a Unix socket (Route B: the run's state/ollama.sock,
                 mode 0600, bind-mounted into the container at /run/dvl/,
                 where the image's relay forwards 127.0.0.1:11434 to it)
  --port N       listen on 127.0.0.1:N instead (host policy runs; 0 picks a
                 free port, written to --ready)
  --upstream     the model server (default http://127.0.0.1:11434; Ollama
                 listens on loopback only, Δ146)
  --config       the run's pins (JSON): {"model": tag, "options": {...},
                 "caps": {"calls": n, "tokens": n, "gpu_s": s}, "margin": 512,
                 "digest": <the tag's full digest, optional>,
                 "unload_on_stop": <bool, optional>,
                 "seeds": <the run's per-request seeds, optional>}
  --log          one JSON line per request and response, prompts and replies
                 included (gate.log in the run directory)
  --counts       the running totals (JSON), rewritten after every request
  --ready        a file written once the gate listens (its address)

For every request it:
  - admits only POST /api/chat, /api/generate, /v1/chat/completions and GET
    /api/version, and answers 403 to everything else (model management in
    particular: pull, push, create, copy, delete, show, tags, ps), logged;
  - admits only the run's pinned model tag (403 otherwise, logged);
  - sets the pinned options on the request and logs every value it
    overrode (on the OpenAI-compatible endpoint the options it can carry:
    temperature, seed, top_p and max_tokens for num_predict; num_ctx and
    top_k cannot be set there, and the log says so);
  - counts calls and tokens (Ollama's own counts where the response carries
    them) and the request's busy seconds as GPU-seconds, and answers 429
    once a cap is reached;
  - flags `ctx-saturated` when a prompt's token count reaches num_ctx less
    the margin (Ollama then cuts the prompt without an error);
  - reads /api/ps after each inference request and records any other
    resident model;
  - passes streamed responses through unchanged, chunk by chunk.
One request is in flight at a time. It never pulls, deletes or changes a
model, and it never retries a request.

The live batch runner (fvh.batch, DV4 step 1a's remainder) adds two config
keys and one option, so that a lab's repeats are independent samples and a
host gate never outlives its run:
  - "seeds": [s0, s1, ...]: the n-th admitted inference request of the run
    gets seed s_n in place of the pinned "seed" option (logged as an
    override when the client sent another), and a request past the list is
    answered 429 ("the run's seeds are used up"); without the key every
    request gets the pinned seed, as before (Q07's single replay);
  - "seeds" are pre-registered per run by the batch plan (fvh.batch's
    derivation), never chosen by the client;
  - --owner-pid PID: the gate stops (and unloads, with "unload_on_stop")
    once that process is gone, so a runner killed mid-batch leaves no gate.

Step 3a adds two of the gate's own upstream requests, never a client's:
  - with "digest" in the config, GET /api/tags once at start: the pinned tag
    must carry that digest, or the gate exits 3 before it listens (the run
    never starts on another model);
  - with "unload_on_stop", POST /api/generate {"model": tag, "keep_alive": 0}
    when the gate stops, so that the model leaves the GPU after the run
    (DV4-PLAN §10), logged as the "unload" event.
"""

import argparse
import http.client
import http.server
import json
import os
import socketserver
import sys
import threading
import time
import urllib.parse

INFERENCE = {"/api/chat": "ollama", "/api/generate": "ollama", "/v1/chat/completions": "openai"}
OPEN_GET = {"/api/version"}
# pinned option -> the OpenAI-compatible key that carries it (None: cannot be set there)
OPENAI_KEYS = {"temperature": "temperature", "seed": "seed", "top_p": "top_p",
               "num_predict": "max_tokens", "num_ctx": None, "top_k": None}
MAX_BODY = 8 << 20


class Gate:
    def __init__(self, cfg, upstream, log_path, counts_path):
        self.cfg = cfg
        u = urllib.parse.urlsplit(upstream)
        if u.scheme != "http" or not u.hostname:
            raise ValueError(f"--upstream must be an http URL, not {upstream!r}")
        self.up_host, self.up_port = u.hostname, u.port or 80
        self.log_path = log_path
        self.counts_path = counts_path
        self.lock = threading.Lock()          # one request in flight
        self.log_lock = threading.Lock()
        self.counts = {"calls": 0, "prompt_tokens": 0, "output_tokens": 0, "tokens": 0,
                       "gpu_s": 0.0, "refused": 0, "capped": 0, "ctx_saturated": 0,
                       "other_resident": [], "overrides": 0, "admitted": 0}
        seeds = cfg.get("seeds")
        if seeds is not None and (not isinstance(seeds, list) or not all(
                isinstance(x, int) and not isinstance(x, bool) and x >= 0 for x in seeds)):
            raise ValueError("the config's seeds must be a list of integers >= 0")
        self.seeds = seeds
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

    def pin(self, kind, body, seed=None):
        """Set the pinned options on a request body (and the run's seed for
        this request, when the config lists seeds); returns the overrides."""
        pins = dict(self.cfg.get("options") or {})
        if seed is not None:
            pins["seed"] = seed
        over = []
        if kind == "ollama":
            opts = body.get("options")
            if not isinstance(opts, dict):
                opts = {}
            for k, v in sorted(pins.items()):
                if k in opts and opts[k] != v:
                    over.append({"option": k, "sent": opts[k], "pinned": v})
                opts[k] = v
            body["options"] = opts
        else:
            for k, v in sorted(pins.items()):
                key = OPENAI_KEYS.get(k, k)
                if key is None:
                    over.append({"option": k, "pinned": v, "note": "cannot be set on /v1/chat/completions"})
                    continue
                if key in body and body[key] != v:
                    over.append({"option": k, "sent": body[key], "pinned": v})
                body[key] = v
        return over

    def _upstream(self, method, path, body=None, timeout=30):
        c = http.client.HTTPConnection(self.up_host, self.up_port, timeout=timeout)
        try:
            data = json.dumps(body).encode() if body is not None else None
            c.request(method, path, body=data,
                      headers={"Content-Type": "application/json"} if data else {})
            r = c.getresponse()
            return r.status, r.read()
        finally:
            c.close()

    def digest_of(self, tag):
        """The full digest /api/tags lists for `tag` (None when absent or unreachable)."""
        try:
            status, raw = self._upstream("GET", "/api/tags")
            for m in json.loads(raw or b"{}").get("models", []):
                if isinstance(m, dict) and m.get("name") == tag:
                    return m.get("digest")
        except (OSError, ValueError, http.client.HTTPException):
            pass
        return None

    def unload(self, tag):
        """keep_alive 0 for the pinned tag (the HTTP status, or the error's name)."""
        try:
            return self._upstream("POST", "/api/generate", {"model": tag, "keep_alive": 0},
                                  timeout=120)[0]
        except (OSError, http.client.HTTPException) as e:
            return type(e).__name__

    def resident(self):
        try:
            c = http.client.HTTPConnection(self.up_host, self.up_port, timeout=10)
            c.request("GET", "/api/ps")
            r = c.getresponse()
            data = json.loads(r.read() or b"{}")
            c.close()
        except (OSError, ValueError, http.client.HTTPException):
            return None
        return [{"name": m.get("name"), "size_vram": m.get("size_vram"), "size": m.get("size")}
                for m in data.get("models", []) if isinstance(m, dict)]


def usage_from(kind, text):
    """(prompt tokens, output tokens) from a response body (streamed or not)."""
    p = o = None
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
        if kind == "ollama":
            if "prompt_eval_count" in d:
                p = d["prompt_eval_count"]
            if "eval_count" in d:
                o = d["eval_count"]
        else:
            u = d.get("usage")
            if isinstance(u, dict):
                p, o = u.get("prompt_tokens", p), u.get("completion_tokens", o)
    return p, o


def make_handler(gate):
    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "dvl-ollama-gate"

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
            self.forward(None, None, path)

        def do_POST(self):
            path = urllib.parse.urlsplit(self.path).path
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                return self.refuse(403, "the request body is over the gate's size cap")
            raw = self.rfile.read(n) if n else b""
            kind = INFERENCE.get(path)
            if kind is None:
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
            over = gate.pin(kind, body, seed=seed if gate.seeds is not None else None)
            if over:
                gate.counts["overrides"] += len(over)
            self.forward(body, kind, path, over, seed=seed)

        do_PUT = do_DELETE = do_PATCH = do_HEAD = lambda self: self.refuse(  # noqa: E731
            403, f"{self.command} is not a method this gate admits")

        def forward(self, body, kind, path, over=(), seed=None):
            data = json.dumps(body).encode() if body is not None else None
            with gate.lock:
                started = time.monotonic()
                try:
                    up = http.client.HTTPConnection(gate.up_host, gate.up_port, timeout=3600)
                    hdrs = {"Content-Type": "application/json"} if data is not None else {}
                    up.request(self.command, path, body=data, headers=hdrs)
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
                self.record(body, kind, path, over, r.status, busy, got, seed)
                self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()

        def record(self, body, kind, path, over, status, busy, got, seed=None):
            text = got.decode("utf-8", "replace")
            rec = {"event": "request", "method": self.command, "path": path, "status": status,
                   "busy_s": round(busy, 3), "request": body, "response": text[:1 << 20]}
            if kind is not None and seed is not None:
                rec["seed"] = seed
            if over:
                rec["overrides"] = list(over)
            if kind is not None:
                p, o = usage_from(kind, text)
                c = gate.counts
                c["calls"] += 1
                c["gpu_s"] = round(c["gpu_s"] + busy, 3)
                c["prompt_tokens"] += p or 0
                c["output_tokens"] += o or 0
                c["tokens"] = c["prompt_tokens"] + c["output_tokens"]
                rec["usage"] = {"prompt_tokens": p, "output_tokens": o}
                num_ctx = (gate.cfg.get("options") or {}).get("num_ctx")
                if p is not None and isinstance(num_ctx, int) and \
                        p >= num_ctx - int(gate.cfg.get("margin", 512)):
                    c["ctx_saturated"] += 1
                    rec["finding"] = "ctx-saturated"
                res = gate.resident()
                if res is not None:
                    rec["resident"] = res
                    for m in res:
                        if m["name"] != gate.cfg.get("model") and m["name"] not in c["other_resident"]:
                            c["other_resident"].append(m["name"])
                gate.write_counts()
            gate.log(rec)

    return Handler


class UnixServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


class TCPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ollama_gate.py", allow_abbrev=False)
    where = ap.add_mutually_exclusive_group(required=True)
    where.add_argument("--socket")
    where.add_argument("--port", type=int)
    ap.add_argument("--config", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--counts")
    ap.add_argument("--upstream", default="http://127.0.0.1:11434")
    ap.add_argument("--ready")
    ap.add_argument("--owner-pid", type=int)
    a = ap.parse_args(argv)
    with open(a.config, encoding="utf-8") as fh:
        cfg = json.load(fh)
    if not isinstance(cfg.get("model"), str) or not cfg["model"]:
        print("ollama_gate: the config names no pinned model", file=sys.stderr)
        return 2
    try:
        gate = Gate(cfg, a.upstream, a.log, a.counts)
    except ValueError as e:
        print(f"ollama_gate: {e}", file=sys.stderr)
        return 2
    if cfg.get("digest"):
        found = gate.digest_of(cfg["model"])
        gate.log({"event": "digest", "model": cfg["model"], "pinned": cfg["digest"], "found": found})
        if found != cfg["digest"]:
            print(f"ollama_gate: {cfg['model']} has digest {found!r}, pinned {cfg['digest']!r}",
                  file=sys.stderr)
            return 3
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
        srv = TCPServer(("127.0.0.1", a.port), handler)
        addr = f"http://127.0.0.1:{srv.server_address[1]}"
    gate.log({"event": "start", "listen": addr, "upstream": a.upstream, "model": cfg["model"],
              "options": cfg.get("options") or {}, "caps": cfg.get("caps") or {},
              "seeds": cfg.get("seeds")})
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
        if cfg.get("unload_on_stop"):
            gate.log({"event": "unload", "model": cfg["model"], "status": gate.unload(cfg["model"])})
        gate.log({"event": "stop", "counts": gate.counts})
    return 0


if __name__ == "__main__":
    sys.exit(main())
