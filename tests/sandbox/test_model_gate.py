"""sandbox/hostside/model_gate.py against a fake OpenAI-compatible server
(DV4-PLAN §5.6.3, Δ146; DV4 step 2c; Δ505). No model is called: the upstream
is an invented server on loopback that records what reaches it (its model
list and chat completions under /v1, a /version at its root), and the
gate listens on a Unix socket in a temporary directory, as in a Route B run.
The endpoint and model allowlists, the pinned options as OpenAI fields, the
caps, the counts (reasoning tokens included), the saturation flag and the
server's context-length refusal, the served-model check at start, the
discovery of the host's server and model (discover()) and the streamed
pass-through."""

import http.client
import http.server
import json
import os
import shutil
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
GATE = ROOT / "sandbox" / "hostside" / "model_gate.py"
PINS = {"temperature": 0, "seed": 11, "max_tokens": 32, "top_k": 20, "top_p": 0.9}
MODEL = "fake-model"


class Upstream(http.server.BaseHTTPRequestHandler):
    seen = []
    prompt_tokens = 5
    served = []
    refuse_ctx = False

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
        if self.path == "/v1/models":
            return self.send_json({"object": "list", "data": [
                {"object": "model", "owned_by": "fake", **m} for m in Upstream.served]})
        if self.path == "/version":
            return self.send_json({"version": "fake-0"})
        self.send_json({"error": "no"}, 404)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        Upstream.seen.append(("POST", self.path, body))
        if self.path != "/v1/chat/completions":
            return self.send_json({"error": "no"}, 404)
        if Upstream.refuse_ctx:
            return self.send_json({"object": "error", "type": "BadRequestError", "code": 400,
                                   "message": "This model's maximum context length is 2048 "
                                              "tokens. However, you requested 4000 tokens."}, 400)
        usage = {"prompt_tokens": Upstream.prompt_tokens, "completion_tokens": 3,
                 "completion_tokens_details": {"reasoning_tokens": 2}}
        if body.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            parts = [{"choices": [{"delta": {"reasoning": "hm"}}]},
                     {"choices": [{"delta": {"content": "a"}}]},
                     {"choices": [{"delta": {"content": "b"}, "finish_reason": "stop"}]}]
            if (body.get("stream_options") or {}).get("include_usage"):
                parts.append({"choices": [], "usage": usage})
            for part in parts:
                line = ("data: " + json.dumps({"system_fingerprint": "fake-fp", **part})
                        + "\n\n").encode()
                self.wfile.write(b"%x\r\n%s\r\n" % (len(line), line))
                self.wfile.flush()
                time.sleep(0.05)
            end = b"data: [DONE]\n\n"
            self.wfile.write(b"%x\r\n%s\r\n0\r\n\r\n" % (len(end), end))
            return
        self.send_json({"system_fingerprint": "fake-fp", "usage": usage,
                        "choices": [{"message": {"role": "assistant", "content": "ok",
                                                 "reasoning": "hm"}, "finish_reason": "stop"}]})


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, path):
        super().__init__("localhost", timeout=30)
        self.path_ = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.path_)


class Base(unittest.TestCase):
    """The fake server and the helpers; a subclass starts the gate."""

    CFG = {"model": MODEL, "options": PINS, "caps": {"calls": 3}, "margin": 512,
           "max_model_len": 2048}

    def setUp(self):
        Upstream.seen, Upstream.prompt_tokens, Upstream.refuse_ctx = [], 5, False
        Upstream.served = [{"id": MODEL, "max_model_len": 2048}]
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.dir = Path(tempfile.mkdtemp(prefix="dvl0-gate-"))
        self.addCleanup(lambda: shutil.rmtree(self.dir, ignore_errors=True))

    def start(self, cfg, expect_ready=True):
        (self.dir / "cfg.json").write_text(json.dumps(cfg))
        self.sock = self.dir / "gate.sock"
        ready = self.dir / "ready"
        self.proc = subprocess.Popen(
            [sys.executable, "-B", str(GATE), "--socket", str(self.sock), "--config",
             str(self.dir / "cfg.json"), "--log", str(self.dir / "gate.log"), "--counts",
             str(self.dir / "counts.json"), "--ready", str(ready), "--upstream",
             f"http://127.0.0.1:{self.srv.server_address[1]}/v1"], stderr=subprocess.PIPE)
        self.addCleanup(self.stop)
        if not expect_ready:
            return
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

    def chat(self, model=MODEL, **fields):
        return self.ask("POST", "/v1/chat/completions",
                        {"model": model, "messages": [{"role": "user", "content": "x"}],
                         "stream": False, **fields})


class Gate(Base):
    def setUp(self):
        super().setUp()
        self.start(self.CFG)

    def test_the_socket_is_private(self):
        self.assertEqual(stat.S_IMODE(os.stat(self.sock).st_mode), 0o600)

    def test_the_model_list_passes_and_nothing_else_reaches_the_server(self):
        status, data = self.ask("GET", "/v1/models")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data)["data"][0]["id"], MODEL)
        for method, path in (("POST", "/v1/completions"), ("POST", "/v1/embeddings"),
                             ("POST", "/v1/responses"), ("GET", "/version"), ("GET", "/metrics"),
                             ("POST", "/api/chat"), ("POST", "/api/pull"), ("GET", "/api/tags"),
                             ("GET", "/v1/chat/completions"), ("PUT", "/v1/chat/completions"),
                             ("DELETE", "/v1/models"), ("GET", "/")):
            status, _ = self.ask(method, path, {"model": MODEL})
            self.assertEqual(status, 403, (method, path))
        self.assertEqual(Upstream.seen, [("GET", "/v1/models", None)])
        refused = [r for r in self.log() if r["event"] == "refused"]
        self.assertEqual(len(refused), 12)
        self.assertEqual(self.counts()["refused"], 12)

    def test_another_model_is_refused(self):
        self.assertEqual(self.chat("other-model")[0], 403)
        self.assertEqual(self.ask("POST", "/v1/chat/completions", {"messages": []})[0], 403)
        self.assertEqual(Upstream.seen, [])

    def test_the_pinned_options_are_set_as_openai_fields_and_every_override_logged(self):
        status, data = self.chat(temperature=0.7, seed=11, max_tokens=9999,
                                 max_completion_tokens=50)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data)["choices"][0]["message"]["content"], "ok")
        sent = Upstream.seen[0][2]
        self.assertEqual({k: sent[k] for k in PINS}, PINS)
        self.assertNotIn("max_completion_tokens", sent)
        self.assertNotIn("options", sent)
        over = [o for r in self.log() for o in r.get("overrides", [])]
        self.assertEqual(sorted(o["option"] for o in over),
                         ["max_completion_tokens", "max_tokens", "temperature"])

    def test_a_streamed_request_gets_include_usage_and_is_counted(self):
        c = UnixHTTPConnection(str(self.sock))
        c.request("POST", "/v1/chat/completions", body=json.dumps(
            {"model": MODEL, "messages": [], "stream": True,
             "stream_options": {"include_usage": False}}).encode())
        r = c.getresponse()
        text = r.read().decode()
        c.close()
        chunks = [json.loads(x[6:]) for x in text.split("\n\n") if x.startswith("data: {")]
        self.assertEqual([ch["choices"][0]["delta"].get("content") for ch in chunks
                          if ch["choices"]], [None, "a", "b"])
        self.assertTrue(text.rstrip().endswith("data: [DONE]"))
        self.assertEqual(Upstream.seen[0][2]["stream_options"], {"include_usage": True})
        c = self.counts()
        self.assertEqual((c["prompt_tokens"], c["output_tokens"], c["reasoning_tokens"]), (5, 3, 2))
        req = [r for r in self.log() if r["event"] == "request"][0]
        self.assertEqual(req["system_fingerprint"], "fake-fp")
        self.assertIn({"option": "stream_options.include_usage", "sent": False, "pinned": True},
                      req["overrides"])

    def test_calls_tokens_and_the_cap(self):
        for _ in range(3):
            self.assertEqual(self.chat()[0], 200)
        status, data = self.chat()
        self.assertEqual(status, 429)
        self.assertIn("calls", json.loads(data)["error"])
        c = self.counts()
        self.assertEqual((c["calls"], c["prompt_tokens"], c["output_tokens"], c["reasoning_tokens"],
                          c["tokens"]), (3, 15, 9, 6, 24))
        self.assertEqual(c["capped"], 1)
        self.assertEqual(len([s for s in Upstream.seen if s[0] == "POST"]), 3)

    def test_a_prompt_near_max_model_len_is_ctx_saturated(self):
        Upstream.prompt_tokens = 2048 - 100
        self.assertEqual(self.chat()[0], 200)
        self.assertEqual(self.counts()["ctx_saturated"], 1)
        req = [r for r in self.log() if r["event"] == "request"][0]
        self.assertEqual(req["finding"], "ctx-saturated")
        self.assertEqual(req["usage"], {"prompt_tokens": 1948, "output_tokens": 3,
                                        "reasoning_tokens": 2})

    def test_the_servers_context_refusal_is_ctx_saturated(self):
        Upstream.refuse_ctx = True
        status, data = self.chat()
        self.assertEqual(status, 400)
        self.assertIn("maximum context length", json.loads(data)["message"])
        c = self.counts()
        self.assertEqual((c["calls"], c["ctx_saturated"], c["tokens"]), (1, 1, 0))
        req = [r for r in self.log() if r["event"] == "request"][0]
        self.assertEqual(req["finding"], "ctx-saturated")


class GateServed(Base):
    """check_served: the run's model must be served before the gate listens; the
    served max_model_len (when reported) is the context check's, and the
    server's version is recorded as observed."""

    CFG = {**Base.CFG, "check_served": True, "max_model_len": None}

    def test_a_served_model_starts_and_its_facts_are_recorded(self):
        Upstream.served.append({"id": "other"})
        self.start(self.CFG)
        ev = {r["event"]: r for r in self.log()}
        self.assertEqual(ev["served"]["found"], {"id": MODEL, "max_model_len": 2048})
        self.assertEqual((ev["served"]["version"], ev["served"]["other_served"]), ("fake-0", ["other"]))
        c = self.counts()
        self.assertEqual((c["server_version"], c["other_served"]), ("fake-0", ["other"]))
        self.assertEqual([s[1] for s in Upstream.seen], ["/v1/models", "/version"])
        Upstream.prompt_tokens = 1600                        # 1600 >= 2048 - 512
        self.assertEqual(self.chat()[0], 200)
        self.assertEqual(self.counts()["ctx_saturated"], 1)
        self.assertEqual(self.counts()["system_fingerprint"], "fake-fp")

    def test_a_model_the_server_does_not_list_never_starts(self):
        Upstream.served = [{"id": "someone-else"}]
        self.start(self.CFG, expect_ready=False)
        self.assertEqual(self.proc.wait(timeout=20), 3)
        self.assertIn("not a model the server lists", self.proc.stderr.read().decode())
        self.assertFalse((self.dir / "ready").exists())

    def test_without_a_reported_length_only_the_servers_refusal_counts(self):
        Upstream.served = [{"id": MODEL}]
        self.start(self.CFG)
        Upstream.prompt_tokens = 10 ** 6
        self.assertEqual(self.chat()[0], 200)
        self.assertEqual(self.counts()["ctx_saturated"], 0)  # margin-free: no length known
        Upstream.refuse_ctx = True
        self.assertEqual(self.chat()[0], 400)
        self.assertEqual(self.counts()["ctx_saturated"], 1)


class Discovery(unittest.TestCase):
    """discover(): the first endpoint whose GET /models answers, its only model
    (or DVL_MODEL), the served max_model_len (or None) and /version (or None);
    DVL_MODEL_URL in place of the list."""

    def setUp(self):
        Upstream.seen, Upstream.served = [], [{"id": MODEL, "max_model_len": 2048}]
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}/v1"
        self.dead = "http://127.0.0.1:9/v1"
        spec = __import__("importlib.util").util.spec_from_file_location("dvl_model_gate_t", GATE)
        self.mg = __import__("importlib.util").util.module_from_spec(spec)
        spec.loader.exec_module(self.mg)
        env = __import__("unittest.mock").mock.patch.dict(os.environ, {}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        for k in ("DVL_MODEL_URL", "DVL_MODEL"):
            os.environ.pop(k, None)

    def test_the_first_answering_endpoint_and_its_only_model(self):
        found = self.mg.discover([self.dead, self.url])
        self.assertEqual(found, {"base_url": self.url, "model": MODEL, "max_model_len": 2048,
                                 "served": [MODEL], "version": "fake-0"})

    def test_several_models_need_dvl_model(self):
        Upstream.served = [{"id": "a"}, {"id": "b"}]
        with self.assertRaisesRegex(self.mg.DiscoveryError, "DVL_MODEL"):
            self.mg.discover([self.url])
        os.environ["DVL_MODEL"] = "b"
        found = self.mg.discover([self.url])
        self.assertEqual((found["model"], found["max_model_len"]), ("b", None))
        os.environ["DVL_MODEL"] = "c"
        with self.assertRaisesRegex(self.mg.DiscoveryError, "not served"):
            self.mg.discover([self.url])

    def test_dvl_model_url_replaces_the_list(self):
        os.environ["DVL_MODEL_URL"] = self.url
        self.assertEqual(self.mg.discover([self.dead])["base_url"], self.url)
        os.environ["DVL_MODEL_URL"] = self.dead
        with self.assertRaisesRegex(self.mg.DiscoveryError, "no OpenAI-compatible model server"):
            self.mg.discover([self.url])

    def test_only_loopback_urls(self):
        for bad in ("http://localhost:8000/v1", "http://10.0.0.1:8000/v1", "https://127.0.0.1/v1"):
            with self.assertRaisesRegex(self.mg.DiscoveryError, "loopback"):
                self.mg.discover([bad])
        with self.assertRaisesRegex(self.mg.DiscoveryError, "no OpenAI-compatible model server"):
            self.mg.discover([self.dead])


class GateSeeds(Gate):
    """The batch runner's per-run seeds (fvh.batch): the n-th admitted request gets
    the run's n-th seed, whatever the client sends; past the list, 429."""

    CFG = {**Base.CFG, "caps": {"calls": 5}, "seeds": [101, 202]}

    def test_each_request_gets_the_runs_next_seed_and_the_list_bounds_the_run(self):
        self.assertEqual(self.chat(seed=7)[0], 200)
        self.assertEqual(self.chat(seed=7)[0], 200)
        status, data = self.chat()
        self.assertEqual(status, 429)
        self.assertIn("seeds are used up", json.loads(data)["error"])
        sent = [b for m, p, b in Upstream.seen if m == "POST"]
        self.assertEqual([s["seed"] for s in sent], [101, 202])
        reqs = [r for r in self.log() if r["event"] == "request"]
        self.assertEqual([r["seed"] for r in reqs], [101, 202])
        over = [o for r in reqs for o in r.get("overrides", []) if o["option"] == "seed"]
        self.assertEqual([(o["sent"], o["pinned"]) for o in over], [(7, 101), (7, 202)])
        self.assertEqual((self.counts()["admitted"], self.counts()["calls"]), (2, 2))

    def test_the_other_controls_are_unchanged(self):
        self.assertEqual(self.chat("other-model")[0], 403)
        self.assertEqual(self.ask("POST", "/api/pull", {"name": "x"})[0], 403)
        self.assertEqual(Upstream.seen, [])

    test_calls_tokens_and_the_cap = None
    test_the_pinned_options_are_set_as_openai_fields_and_every_override_logged = None
    test_a_prompt_near_max_model_len_is_ctx_saturated = None
    test_the_servers_context_refusal_is_ctx_saturated = None
    test_a_streamed_request_gets_include_usage_and_is_counted = None
    test_the_model_list_passes_and_nothing_else_reaches_the_server = None
    test_another_model_is_refused = None


class GateConfig(unittest.TestCase):
    def test_a_malformed_seeds_list_is_refused_before_listening(self):
        d = Path(tempfile.mkdtemp(prefix="dvl0-gate-"))
        self.addCleanup(lambda: shutil.rmtree(d, ignore_errors=True))
        (d / "cfg.json").write_text(json.dumps({"model": "m", "options": {}, "seeds": [1, "x"]}))
        p = subprocess.run([sys.executable, "-B", str(GATE), "--port", "0", "--config",
                            str(d / "cfg.json"), "--log", str(d / "gate.log"),
                            "--upstream", "http://127.0.0.1:9/v1"],
                           capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 2)
        self.assertIn("seeds", p.stderr)
        p = subprocess.run([sys.executable, "-B", str(GATE), "--port", "0", "--config",
                            str(d / "cfg.json"), "--log", str(d / "gate.log")],
                           capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 2)
        self.assertIn("upstream", p.stderr)              # no upstream: nothing to forward to

    def test_an_unreachable_server_with_check_served_never_starts(self):
        d = Path(tempfile.mkdtemp(prefix="dvl0-gate-"))
        self.addCleanup(lambda: shutil.rmtree(d, ignore_errors=True))
        (d / "cfg.json").write_text(json.dumps({"model": "m", "options": {}, "check_served": True}))
        p = subprocess.run([sys.executable, "-B", str(GATE), "--port", "0", "--config",
                            str(d / "cfg.json"), "--log", str(d / "gate.log"), "--ready",
                            str(d / "ready"), "--upstream", "http://127.0.0.1:9/v1"],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 3)
        self.assertIn("does not answer", p.stderr)
        self.assertFalse((d / "ready").exists())

    def test_the_gate_stops_when_its_owner_is_gone(self):
        d = Path(tempfile.mkdtemp(prefix="dvl0-gate-"))
        self.addCleanup(lambda: shutil.rmtree(d, ignore_errors=True))
        (d / "cfg.json").write_text(json.dumps({"model": "m", "options": {}}))
        owner = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        g = subprocess.Popen([sys.executable, "-B", str(GATE), "--port", "0", "--config",
                              str(d / "cfg.json"), "--log", str(d / "gate.log"), "--ready",
                              str(d / "ready"), "--owner-pid", str(owner.pid),
                              "--upstream", "http://127.0.0.1:9/v1"])
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
