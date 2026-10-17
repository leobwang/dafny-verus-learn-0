"""sandbox/hostside/ollama_gate.py against a fake model server (DV4-PLAN §5.6.3,
Δ146; DV4 step 2c). No model is called: the upstream is an invented server
on loopback that records what reaches it, and the gate listens on a Unix
socket in a temporary directory, as in a Route B run. The endpoint and model
allowlists, the pinned options, the caps, the counts, the saturation flag,
the resident-model record and the streamed pass-through."""

import http.client
import http.server
import json
import os
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "sandbox" / "hostside" / "ollama_gate.py"
PINS = {"temperature": 0, "seed": 11, "num_predict": 32, "num_ctx": 2048, "top_k": 20,
        "top_p": 0.9}


class Upstream(http.server.BaseHTTPRequestHandler):
    seen = []
    prompt_tokens = 5
    resident = ["fake-model:1"]

    def log_message(self, *a):
        pass

    def send_json(self, obj, code=200):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        Upstream.seen.append(("GET", self.path, None))
        if self.path == "/api/version":
            return self.send_json({"version": "fake-0"})
        if self.path == "/api/ps":
            return self.send_json({"models": [{"name": n, "size": 1, "size_vram": 1}
                                              for n in Upstream.resident]})
        self.send_json({"error": "no"}, 404)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        Upstream.seen.append(("POST", self.path, body))
        if self.path == "/api/chat" and body.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            for part in ({"message": {"content": "a"}, "done": False},
                         {"message": {"content": "b"}, "done": False},
                         {"done": True, "prompt_eval_count": Upstream.prompt_tokens, "eval_count": 2}):
                line = (json.dumps(part) + "\n").encode()
                self.wfile.write(b"%x\r\n%s\r\n" % (len(line), line))
                self.wfile.flush()
                time.sleep(0.05)
            self.wfile.write(b"0\r\n\r\n")
            return
        if self.path == "/api/chat":
            return self.send_json({"done": True, "prompt_eval_count": Upstream.prompt_tokens,
                                   "eval_count": 3, "message": {"content": "ok"}})
        if self.path == "/v1/chat/completions":
            return self.send_json({"choices": [], "usage": {"prompt_tokens": 4, "completion_tokens": 1}})
        self.send_json({"error": "no"}, 404)


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, path):
        super().__init__("localhost", timeout=30)
        self.path_ = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.path_)


class Gate(unittest.TestCase):
    def setUp(self):
        Upstream.seen, Upstream.prompt_tokens, Upstream.resident = [], 5, ["fake-model:1"]
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.shutdown)
        self.dir = Path(tempfile.mkdtemp(prefix="dvl0-gate-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(self.dir, ignore_errors=True))
        self.start({"model": "fake-model:1", "options": PINS, "caps": {"calls": 3}, "margin": 512})

    def start(self, cfg):
        (self.dir / "cfg.json").write_text(json.dumps(cfg))
        self.sock = self.dir / "ollama.sock"
        ready = self.dir / "ready"
        self.proc = subprocess.Popen(
            [sys.executable, "-B", str(GATE), "--socket", str(self.sock), "--config",
             str(self.dir / "cfg.json"), "--log", str(self.dir / "gate.log"), "--counts",
             str(self.dir / "counts.json"), "--ready", str(ready), "--upstream",
             f"http://127.0.0.1:{self.srv.server_address[1]}"], stderr=subprocess.PIPE)
        self.addCleanup(self.stop)
        for _ in range(100):
            if ready.exists():
                return
            time.sleep(0.05)
        self.fail("the gate did not start: " + self.proc.stderr.read().decode())

    def stop(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            self.proc.wait(timeout=10)
        self.proc.stderr.close()

    def ask(self, method, path, body=None):
        c = UnixHTTPConnection(str(self.sock))
        c.request(method, path, body=json.dumps(body).encode() if body is not None else None,
                  headers={"Content-Type": "application/json"})
        r = c.getresponse()
        data = r.read()
        c.close()
        return r.status, data

    def log(self):
        return [json.loads(x) for x in (self.dir / "gate.log").read_text().splitlines()]

    def counts(self):
        return json.loads((self.dir / "counts.json").read_text())

    def chat(self, model="fake-model:1", **opts):
        return self.ask("POST", "/api/chat", {"model": model, "messages": [], "stream": False,
                                              "options": opts})

    def test_the_socket_is_private(self):
        self.assertEqual(stat.S_IMODE(os.stat(self.sock).st_mode), 0o600)

    def test_version_passes_and_model_management_never_reaches_the_server(self):
        self.assertEqual(self.ask("GET", "/api/version"), (200, b'{"version": "fake-0"}'))
        for method, path in (("POST", "/api/pull"), ("POST", "/api/push"), ("POST", "/api/create"),
                             ("POST", "/api/copy"), ("DELETE", "/api/delete"), ("POST", "/api/delete"),
                             ("POST", "/api/show"), ("GET", "/api/tags"), ("GET", "/api/ps"),
                             ("POST", "/api/embed"), ("PUT", "/api/chat"), ("GET", "/")):
            status, _ = self.ask(method, path, {"model": "fake-model:1", "name": "fake-model:1"})
            self.assertEqual(status, 403, (method, path))
        self.assertEqual(Upstream.seen, [("GET", "/api/version", None)])
        refused = [r for r in self.log() if r["event"] == "refused"]
        self.assertEqual(len(refused), 12)
        self.assertEqual(self.counts()["refused"], 12)

    def test_another_model_is_refused(self):
        self.assertEqual(self.chat("other-model:7")[0], 403)
        self.assertEqual(self.ask("POST", "/v1/chat/completions", {"model": "x", "messages": []})[0], 403)
        self.assertEqual(Upstream.seen, [])

    def test_the_pinned_options_are_set_and_every_override_logged(self):
        status, data = self.chat(temperature=0.7, seed=11, num_ctx=999999)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data)["message"]["content"], "ok")
        self.assertEqual(Upstream.seen[0][2]["options"], PINS)
        over = [o for r in self.log() for o in r.get("overrides", [])]
        self.assertEqual(sorted(o["option"] for o in over), ["num_ctx", "temperature"])
        status, _ = self.ask("POST", "/v1/chat/completions", {"model": "fake-model:1", "messages": [],
                                                              "temperature": 1.0, "max_tokens": 9999})
        self.assertEqual(status, 200)
        sent = [b for m, p, b in Upstream.seen if p == "/v1/chat/completions"][0]
        self.assertEqual((sent["temperature"], sent["max_tokens"], sent["seed"], sent["top_p"]),
                         (0, 32, 11, 0.9))
        notes = [o for r in self.log() for o in r.get("overrides", []) if o.get("note")]
        self.assertEqual(sorted(o["option"] for o in notes), ["num_ctx", "top_k"])

    def test_calls_tokens_and_the_cap(self):
        self.assertEqual(self.chat()[0], 200)
        self.assertEqual(self.ask("POST", "/v1/chat/completions",
                                  {"model": "fake-model:1", "messages": []})[0], 200)
        self.assertEqual(self.chat()[0], 200)
        status, data = self.chat()
        self.assertEqual(status, 429)
        self.assertIn("calls", json.loads(data)["error"])
        c = self.counts()
        self.assertEqual((c["calls"], c["prompt_tokens"], c["output_tokens"], c["tokens"]), (3, 14, 7, 21))
        self.assertEqual(c["capped"], 1)
        self.assertEqual(len([s for s in Upstream.seen if s[0] == "POST"]), 3)

    def test_a_streamed_reply_passes_through_and_is_counted(self):
        c = UnixHTTPConnection(str(self.sock))
        c.request("POST", "/api/chat", body=json.dumps({"model": "fake-model:1", "messages": [],
                                                        "stream": True}).encode())
        r = c.getresponse()
        lines = [json.loads(x) for x in r.read().decode().splitlines()]
        c.close()
        self.assertEqual([x.get("message", {}).get("content") for x in lines], ["a", "b", None])
        self.assertEqual((self.counts()["prompt_tokens"], self.counts()["output_tokens"]), (5, 2))

    def test_a_saturated_context_and_another_resident_model_are_recorded(self):
        Upstream.prompt_tokens = 2048 - 100
        Upstream.resident = ["fake-model:1", "big-model:2"]
        self.assertEqual(self.chat()[0], 200)
        c = self.counts()
        self.assertEqual((c["ctx_saturated"], c["other_resident"]), (1, ["big-model:2"]))
        req = [r for r in self.log() if r["event"] == "request"][0]
        self.assertEqual(req["finding"], "ctx-saturated")
        self.assertEqual(req["usage"], {"prompt_tokens": 1948, "output_tokens": 3})


class GateSeeds(Gate):
    """The batch runner's per-run seeds (fvh.batch): the n-th admitted request gets
    the run's n-th seed, whatever the client sends; past the list, 429."""

    def setUp(self):
        Upstream.seen, Upstream.prompt_tokens, Upstream.resident = [], 5, ["fake-model:1"]
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.shutdown)
        self.dir = Path(tempfile.mkdtemp(prefix="dvl0-gate-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(self.dir, ignore_errors=True))
        self.start({"model": "fake-model:1", "options": PINS, "caps": {"calls": 5}, "margin": 512,
                    "seeds": [101, 202]})

    def test_each_request_gets_the_runs_next_seed_and_the_list_bounds_the_run(self):
        self.assertEqual(self.chat(seed=7)[0], 200)
        self.assertEqual(self.ask("POST", "/v1/chat/completions",
                                  {"model": "fake-model:1", "messages": [], "seed": 7})[0], 200)
        status, data = self.chat()
        self.assertEqual(status, 429)
        self.assertIn("seeds are used up", json.loads(data)["error"])
        sent = [b for m, p, b in Upstream.seen if m == "POST"]
        self.assertEqual(sent[0]["options"]["seed"], 101)
        self.assertEqual(sent[1]["seed"], 202)
        reqs = [r for r in self.log() if r["event"] == "request"]
        self.assertEqual([r["seed"] for r in reqs], [101, 202])
        over = [o for r in reqs for o in r.get("overrides", []) if o["option"] == "seed"]
        self.assertEqual([(o["sent"], o["pinned"]) for o in over], [(7, 101), (7, 202)])
        self.assertEqual((self.counts()["admitted"], self.counts()["calls"]), (2, 2))

    def test_the_other_controls_are_unchanged(self):
        self.assertEqual(self.chat("other-model:7")[0], 403)
        self.assertEqual(self.ask("POST", "/api/pull", {"name": "x"})[0], 403)
        self.assertEqual(Upstream.seen, [])

    test_calls_tokens_and_the_cap = None
    test_the_pinned_options_are_set_and_every_override_logged = None
    test_a_saturated_context_and_another_resident_model_are_recorded = None
    test_a_streamed_reply_passes_through_and_is_counted = None
    test_version_passes_and_model_management_never_reaches_the_server = None
    test_another_model_is_refused = None


class GateConfig(unittest.TestCase):
    def test_a_malformed_seeds_list_is_refused_before_listening(self):
        d = Path(tempfile.mkdtemp(prefix="dvl0-gate-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        (d / "cfg.json").write_text(json.dumps({"model": "m", "options": {}, "seeds": [1, "x"]}))
        p = subprocess.run([sys.executable, "-B", str(GATE), "--port", "0", "--config",
                            str(d / "cfg.json"), "--log", str(d / "gate.log")],
                           capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 2)
        self.assertIn("seeds", p.stderr)

    def test_the_gate_stops_when_its_owner_is_gone(self):
        d = Path(tempfile.mkdtemp(prefix="dvl0-gate-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        (d / "cfg.json").write_text(json.dumps({"model": "m", "options": {}}))
        owner = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        g = subprocess.Popen([sys.executable, "-B", str(GATE), "--port", "0", "--config",
                              str(d / "cfg.json"), "--log", str(d / "gate.log"), "--ready",
                              str(d / "ready"), "--owner-pid", str(owner.pid),
                              "--upstream", "http://127.0.0.1:9"])
        for _ in range(100):
            if (d / "ready").exists():
                break
            time.sleep(0.05)
        self.assertIsNone(g.poll())
        owner.kill()
        owner.wait()
        self.assertEqual(g.wait(timeout=20), 0)
        events = [json.loads(x)["event"] for x in (d / "gate.log").read_text().splitlines()]
        self.assertEqual(events[-2:], ["owner-gone", "stop"])


if __name__ == "__main__":
    unittest.main()
