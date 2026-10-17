"""The opencode agent run (DV4 step 3a) and scripts/contract_local.sh's live replay
(step 3b), against a fake docker and a fake gate. No container starts and no
model is called: `docker` is a fake on PATH that answers the run's
subcommands, including opencode's two debug views and its run (canned event
streams), and the gate is replaced by a stub that writes the counts a real one
would. The real runs are archived in the author probe archive (dv5b/dv4s3).

Every fixture is a decoy in a throwaway root (sandbox_common.make_root): the
invented module Q98, decoy files, an invented apparatus file."""

import gzip
import io
import json
import os
import sys
import tarfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sandbox_common as sc  # noqa: E402
from dvl import sandbox  # noqa: E402
from dvl import contract_local as cl  # noqa: E402

DIGEST = "ab" * 32
APPARATUS = f"""schema = 1
[backend.qwen]
version = "0.0.0-fake"
binary = "~/fake-opencode"
sha256 = "{{sha}}"
model = "qwen3.8:latest"
num_ctx = 262144
num_predict = 32768
external_ok = []
[model_server]
version = "0.0.0-fake"
models = {{{{ "qwen3.8:latest" = "{DIGEST}" }}}}
margin = 512
options = {{{{ temperature = 0.6, seed = 1, num_predict = 32768, num_ctx = 262144 }}}}
"""

FAKE_DOCKER = r'''#!/usr/bin/env python3
import io, json, os, sys, tarfile
st = os.environ["FAKE_DOCKER_STATE"]
ctl_p = os.path.join(st, "control.json")
ctl = json.load(open(ctl_p)) if os.path.exists(ctl_p) else {}
args = sys.argv[1:]
with open(os.path.join(st, "calls.jsonl"), "a") as fh:
    fh.write(json.dumps(args) + "\n")
def save(name, s):
    json.dump(s, open(os.path.join(st, name + ".json"), "w"))
cmd = args[0]
if cmd == "version":
    print("29.1.3"); sys.exit(0)
if cmd == "image":
    print(args[-1]); sys.exit(0)
if cmd == "run":
    name = args[args.index("--name") + 1]
    save(name, {"Running": True, "OOMKilled": False})
    print("f" * 64); sys.exit(0)
if cmd == "exec":
    i = 1
    while args[i].startswith("--"):
        i += 2 if args[i] in ("--env", "--workdir") else 1
    name, rest = args[i], args[i + 1:]
    if rest[0] == "/usr/bin/tar" and "--extract" in rest:
        where = rest[rest.index("--directory") + 1]
        tag = "home" if where == "/home/agent" else "in"
        open(os.path.join(st, f"{name}.{tag}.tar"), "wb").write(sys.stdin.buffer.read()); sys.exit(0)
    if rest[0] == "/usr/bin/tar" and "--create" in rest:
        src = tarfile.open(os.path.join(st, name + ".in.tar"))
        buf = io.BytesIO(); out = tarfile.open(fileobj=buf, mode="w")
        for m in src.getmembers():
            data = src.extractfile(m).read()
            if m.name in ctl.get("return_text", {}):
                data = ctl["return_text"][m.name].encode()
            ti = tarfile.TarInfo(m.name); ti.size = len(data); out.addfile(ti, io.BytesIO(data))
        out.close(); sys.stdout.buffer.write(buf.getvalue()); sys.exit(0)
    if "/opt/dvl/bin/controls" in rest:
        sys.stdin.read()
        print(json.dumps({"schema": 1, "ok": True, "controls": [{"id": "C1", "ok": True, "detail": "fake"}]}))
        sys.exit(0)
    if "/opt/dvl/agent/opencode" in rest:
        k = rest.index("/opt/dvl/agent/opencode")
        sub = rest[k + 1:]
        if sub[:2] == ["debug", "config"]:
            conf = json.load(tarfile.open(os.path.join(st, name + ".home.tar")).extractfile("opencode.json"))
            conf.update(ctl.get("config_extra", {}))
            print(json.dumps(conf)); sys.exit(0)
        if sub[:3] == ["debug", "agent", "build"]:
            conf = json.load(tarfile.open(os.path.join(st, name + ".home.tar")).extractfile("opencode.json"))
            tools = {t: False for t in ("invalid", "question", "task", "webfetch", "todowrite", "skill")}
            tools.update({t: True for t, v in conf["tools"].items() if t != "*" and v})
            tools.update(ctl.get("tools_extra", {}))
            print(json.dumps({"tools": tools, "steps": conf["agent"]["build"]["steps"],
                              "permission": [{"permission": "external_directory", "pattern": "/tmp/opencode/*",
                                              "action": "allow"}] + ctl.get("perm_extra", [])}))
            sys.exit(0)
        if sub[0] == "run":
            json.dump(args, open(os.path.join(st, "agent-argv.json"), "w"))
            ev = [{"type": "step_start", "part": {}},
                  {"type": "tool_use", "part": {"tool": "edit", "state": {"status": "completed"}}},
                  {"type": "step_finish", "part": {"reason": "tool-calls"}},
                  {"type": "text", "part": {"text": ctl.get("agent_text", "done")}},
                  {"type": "step_finish", "part": {"reason": "stop"}}]
            print("\n".join(json.dumps(e) for e in ev)); sys.exit(ctl.get("agent_exit", 0))
    beh = ctl.get("tools", {})
    tool = next((a for a in rest if a.startswith("/work/scripts/")), "")
    if tool.endswith("vcheck") and "--json" in rest:
        print(json.dumps({"verdict": beh.get("verdict", "verified"), "exit_code": beh.get("gate_exit", 0),
                          "holes": [], "verified_count": 1}))
        sys.exit(beh.get("gate_exit", 0))
    if tool.endswith("vcheck"):
        print("vcheck: x [dafny, gate]: verified — 1 verified, 0 holes, 0 errors"); sys.exit(beh.get("gate_exit", 0))
    print("tool: 0 finding(s)"); sys.exit(beh.get("other_exit", 0))
if cmd == "inspect":
    p = os.path.join(st, args[-1] + ".json")
    if not os.path.exists(p):
        sys.exit(1)
    print(open(p).read()); sys.exit(0)
if cmd in ("rm", "kill"):
    p = os.path.join(st, args[-1] + ".json")
    if os.path.exists(p):
        os.unlink(p)
    sys.exit(0)
sys.exit(0)
'''


class FakeHost(unittest.TestCase):
    """The shared set-up: a fake docker, a fake gate, a fake opencode binary under a
    fake HOME, the apparatus file and an images lock."""

    def setUp(self):
        self.root = sc.make_root(git=True)
        self.bin = sc.tmpdir("dvl0-agent-bin-")
        self.xdg = sc.tmpdir("dvl0-agent-xdg-")
        self.state = sc.tmpdir("dvl0-agent-docker-")
        self.home = sc.tmpdir("dvl0-agent-home-")
        self.addCleanup(sc.cleanup, self.root, self.bin, self.xdg, self.state, self.home)
        sc.fake_bin(self.bin, "docker", "").write_text(FAKE_DOCKER)
        oc = self.home / "fake-opencode"
        oc.write_text("#!/bin/sh\necho 0.0.0-fake\n")
        oc.chmod(0o755)
        sha = sandbox.sha256_bytes(oc.read_bytes())
        sc.write(self.root, "sandbox/apparatus.toml", APPARATUS.format(sha=sha))
        env = {"PATH": f"{self.bin}:{os.environ.get('PATH', '/usr/bin:/bin')}",
               "XDG_RUNTIME_DIR": str(self.xdg), "FAKE_DOCKER_STATE": str(self.state),
               "HOME": str(self.home)}
        p = mock.patch.dict(os.environ, env)
        p.start()
        self.addCleanup(p.stop)
        for k in ("DVL_NO_DOCKER", "FVH_APPARATUS", "CI"):
            os.environ.pop(k, None)
        m = mock.patch.object(sandbox, "mem_available_gb", return_value=100.0)
        m.start()
        self.addCleanup(m.stop)
        self.gate_cfgs = []
        self.gate_calls = 3
        g = mock.patch.object(sandbox, "start_gate", side_effect=self.fake_gate)
        g.start()
        self.addCleanup(g.stop)

    def fake_gate(self, manifest, run, cfg=None, upstream=None, out=None):
        self.gate_cfgs.append(cfg)
        out = out or run.out
        (out / "gate.log").write_text('{"event": "start"}\n')
        (out / "gate-counts.json").write_text(json.dumps(
            {"calls": self.gate_calls, "gpu_s": 4.5, "prompt_tokens": 100, "output_tokens": 10,
             "ctx_saturated": 0, "capped": 0}))

        class P:
            pid = None

            def terminate(self):
                pass

            def wait(self, timeout=None):
                return 0
        return P()

    def control(self, **kw):
        (self.state / "control.json").write_text(json.dumps(kw))

    def calls(self):
        p = self.state / "calls.jsonl"
        return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


class AgentRun(FakeHost):
    def live(self, m, **kw):
        man = sandbox.validate(m, self.root)
        run = sandbox.materialize(man, self.root)
        try:
            return sandbox.live_run(man, run, root=self.root, **kw)
        finally:
            sandbox.remove_run(run)

    def manifest(self):
        m = sc.agent_manifest(self.root)
        m["limits"] = {"mem_gb": 0.5, "wall_clock_s": 600}
        m["agent"] = {"cli": "opencode", "model": "qwen3.8:latest", "turns": 12, "gpu_s": 900}
        return m

    def test_an_opencode_run_is_configured_gated_run_and_returned(self):
        self.control(return_text={sc.AGENT_D: sc.AGENT_TEXT + "// the agent's edit\n"})
        code, rec = self.live(self.manifest())
        self.assertEqual((code, rec["ended_by"]), (0, "done"), rec.get("agent"))
        cfg = self.gate_cfgs[0]
        self.assertEqual(cfg["caps"], {"calls": 12, "gpu_s": 900.0})       # calls == turns
        self.assertEqual((cfg["digest"], cfg["unload_on_stop"]), (DIGEST, True))
        self.assertEqual(cfg["options"]["num_predict"], 32768)
        with tarfile.open(self.state / "dvl-q98-run1.home.tar") as tf:
            conf = json.load(tf.extractfile("opencode.json"))
        self.assertEqual(conf["agent"], {"build": {"steps": 12}, "title": {"disable": True}})
        self.assertEqual(conf["compaction"], {"auto": False})
        self.assertEqual(conf["provider"]["fvhgate"]["options"]["baseURL"], sandbox.OPENCODE_RELAY_URL)
        self.assertEqual(sorted(t for t, v in conf["tools"].items() if v), sorted(sandbox.OPENCODE_TOOLS))
        self.assertEqual(conf["permission"]["external_directory"], "deny")
        self.assertTrue(rec["agent"]["precheck"]["ok"])
        argv = json.loads((self.state / "agent-argv.json").read_text())
        self.assertIn("DVL_CAP=container-agent", argv)
        self.assertIn("OPENCODE_DISABLE_PROJECT_CONFIG=1", argv)
        self.assertEqual(rec["agent"]["summary"]["steps"], 1)
        self.assertEqual(rec["agent"]["ended"], "exit")
        self.assertEqual(rec["return"]["returned"], [sc.AGENT_D])
        dest = self.state / "rec"
        sandbox.write_live_records(dest, rec, name="sandbox.json")
        events = gzip.decompress((dest / "transcript.jsonl.gz").read_bytes()).decode().splitlines()
        self.assertEqual(json.loads(events[-1])["part"]["reason"], "stop")
        self.assertIn("+// the agent's edit", (dest / "patch.diff").read_text())
        self.assertNotIn("_transcript", json.loads((dest / "sandbox.json").read_text()))

    def test_a_failed_per_run_gate_stops_before_the_agent_runs(self):
        for kw, match in (({"tools_extra": {"webfetch": True}}, "tools on"),
                          ({"perm_extra": [{"permission": "external_directory", "pattern": "/home/*",
                                            "action": "allow"}]}, "external_directory"),
                          ({"config_extra": {"mcp": {"x": {"type": "local"}}}}, "MCP"),
                          ({"config_extra": {"agent": {"build": {"steps": 12}}}}, "title")):
            self.control(**kw)
            (self.state / "agent-argv.json").unlink(missing_ok=True)
            code, rec = self.live(self.manifest())
            self.assertEqual((code, rec["ended_by"]), (1, "agent-precheck-failed"), kw)
            self.assertTrue(any(match in p for p in rec["agent"]["precheck"]["problems"]),
                            (kw, rec["agent"]["precheck"]))
            self.assertFalse((self.state / "agent-argv.json").exists(), kw)      # never ran
            self.assertTrue(rec["removed"])

    def test_a_credential_shaped_string_withholds_the_transcript(self):
        self.control(agent_text="the key is sk-ant-oat01-" + "Q" * 40)
        code, rec = self.live(self.manifest())
        self.assertEqual(code, 0)
        self.assertNotIn("_transcript", rec)
        self.assertIn("transcript_withheld", rec["agent"])
        dest = self.state / "rec"
        sandbox.write_live_records(dest, rec, name="sandbox.json")
        self.assertFalse((dest / "transcript.jsonl.gz").exists())
        for f in dest.rglob("*"):
            if f.is_file():
                self.assertNotIn("sk-ant-oat01-QQQQ", f.read_text(errors="replace"))

    def test_another_qwen_batch_defers_the_run(self):
        import fcntl
        fd = os.open(self.xdg / sandbox.GPU_LOCK, os.O_RDWR | os.O_CREAT, 0o600)
        self.addCleanup(os.close, fd)
        fcntl.flock(fd, fcntl.LOCK_EX)
        with self.assertRaisesRegex(sandbox.Deferred, "GPU calendar"):
            self.live(self.manifest())
        self.assertEqual(self.calls(), [])

    def test_no_agent_starts_without_the_apparatus_pins(self):
        (self.root / "sandbox" / "apparatus.toml").unlink()
        with self.assertRaisesRegex(sandbox.SandboxError, "apparatus"):
            self.live(self.manifest())
        self.assertEqual(self.calls(), [])

    def test_the_agent_wall_clock_is_recorded_and_the_return_still_follows(self):
        self.control(agent_exit=124, return_text={sc.AGENT_D: sc.AGENT_TEXT + "// half done\n"})
        code, rec = self.live(self.manifest())
        self.assertEqual((code, rec["agent"]["ended"]), (0, "wall-clock"))
        self.assertEqual(rec["return"]["returned"], [sc.AGENT_D])

    def test_claude_code_in_a_container_is_refused(self):
        m = self.manifest()
        m["network"] = "anthropic"
        m["agent"] = {"cli": "claude", "model": "x", "turns": 2}
        with self.assertRaisesRegex(sandbox.SandboxError, "4c"):
            self.live(m)


class Precheck(unittest.TestCase):
    def setUp(self):
        self.root = sc.make_root()
        self.addCleanup(sc.cleanup, self.root)
        m = sc.agent_manifest(self.root)
        m["agent"]["turns"] = 7
        self.man = sandbox.validate(m, self.root, check_image=False)

    def views(self, **over):
        conf = sandbox.opencode_config(self.man, {"num_ctx": 1000, "num_predict": 100})
        agent = {"tools": {**{t: True for t in sandbox.OPENCODE_TOOLS}, "webfetch": False,
                           "task": False}, "steps": 7, "permission": []}
        conf.update(over.pop("conf", {}))
        agent.update(over.pop("agent", {}))
        return json.dumps(conf), json.dumps(agent)

    def test_the_built_config_passes(self):
        self.assertEqual(sandbox.opencode_precheck(*self.views(), self.man), [])

    def test_each_departure_is_named(self):
        cases = [({"conf": {"provider": {"x": {"options": {"baseURL": "http://10.0.0.1/v1"}}}}}, "provider URLs"),
                 ({"conf": {"model": "fvhgate/other:1"}}, "model"),
                 ({"conf": {"compaction": {}}}, "compaction"),
                 ({"agent": {"steps": 8}}, "step limit"),
                 ({"agent": {"tools": {"bash": True}}}, "tools on"),
                 ({"agent": {"permission": [{"permission": "external_directory", "pattern": "/x/*",
                                             "action": "allow"}]}}, "external_directory")]
        for over, match in cases:
            problems = sandbox.opencode_precheck(*self.views(**over), self.man)
            self.assertTrue(any(match in p for p in problems), (over, problems))
        self.assertEqual(sandbox.opencode_precheck("not json", "{}", self.man),
                         ["a debug view is not a JSON object"])


class Replay(FakeHost):
    """contract_local.sh's live replay in-process (cl.main), the fake docker
    standing in for both containers."""

    SNAP = "research/snapshots/Q98_Agent.dfy"

    def setUp(self):
        super().setUp()
        sc.write(self.root, "CLAUDE.md", "# decoy\n\n## §Contractor contract\n\n- a decoy rule\n")
        head = ("/* CONTRACT\ngoal: a decoy goal\nallowed-files:\n  - " + sc.AGENT_D + "\nacceptance:\n"
                f"  - `scripts/vcheck --gate {sc.AGENT_D}` exits 0 and prints only the summary line\n"
                "  - zero tool-counted holes in the allowed file\n"
                f"  - `scripts/specfreeze --against {self.SNAP} {sc.AGENT_D}` reports no change\n"
                "  - `git diff` against the snapshot changes only a body\n*/\nlemma G() {}\n")
        sc.write(self.root, sc.AGENT_D, head)
        sc.write(self.root, "scripts/specfreeze", "# decoy copy of scripts/specfreeze\n")
        sc.write(self.root, self.SNAP, "// the snapshot\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "the snapshot")
        self.control(return_text={sc.AGENT_D: head + "// the agent's edit\n"})

    def git(self, *args):
        import subprocess
        return subprocess.run(sc.GIT + ["-C", str(self.root), *args], capture_output=True, text=True,
                              check=True).stdout

    def main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch("sys.stdout", out), mock.patch("sys.stderr", err):
            code = cl.main(["Q98", "--file", sc.AGENT_D, "--root", str(self.root), *args])
        return code, out.getvalue(), err.getvalue()

    def ledger(self):
        p = self.root / "research" / "runs" / "Q98" / "ledger.jsonl"
        return [json.loads(x) for x in p.read_text().splitlines()]

    def test_a_replay_records_its_run_scores_its_attempt_and_spends_the_budget(self):
        code, out, err = self.main()
        self.assertEqual(code, 0, err)
        self.assertIn("verdict: verified; every checked acceptance line met (3)", out)
        self.assertIn("[for your audit] `git diff`", out)
        self.assertEqual([r["state"] for r in self.ledger()], ["planned", "running", "scored"])
        heads = [json.loads(x) for x in (self.root / "research" / "ledger-heads.jsonl").read_text().splitlines()]
        self.assertEqual([h["event"] for h in heads], ["open", "close"])
        run = next((self.root / "research" / "runs" / "Q98").glob("*-replay-Q98_Agent-1-1"))
        for f in ("run.json", "sandbox.json", "verify.json", "patch.diff", "transcript.jsonl.gz",
                  "gate.log.gz", "gate-counts.json", "inputs.tar.gz", "inputs.sha256", "manifest.json",
                  "selftest.json"):
            self.assertTrue((run / f).is_file(), f)
        meta = json.loads((run / "run.json").read_text())
        self.assertEqual((meta["mode"], meta["backend"], meta["outcome"], meta["ended_by"]),
                         ("agent", "opencode", "verified", "stop"))
        self.assertEqual(meta["usage"]["calls"], 3)
        vdoc = json.loads((run / "verify.json").read_text())
        self.assertEqual([l["met"] for l in vdoc["lines"]], [True, True, True, None])
        # the verification container ran the acceptance commands on the returned file
        vrun = [c for c in self.calls() if c[0] == "run" and "dvl-toolchain" in " ".join(c)]
        self.assertEqual(len(vrun), 1)
        # the budget is spent: the next replay is refused, and --available says why
        code, out, err = self.main()
        self.assertEqual(code, 3)
        self.assertIn("qwen_runs (1) is used", err)
        # the patch is never applied
        self.assertNotIn("the agent's edit", (self.root / sc.AGENT_D).read_text())

    def test_a_failure_before_any_model_output_is_re_issued_under_the_same_id(self):
        self.gate_calls = 0
        self.control(tools_extra={"webfetch": True})          # the per-run gate fails
        code, out, err = self.main()
        self.assertEqual(code, 1)
        self.assertEqual([r["state"] for r in self.ledger()], ["planned", "running", "infra-failed"])
        self.gate_calls = 3
        self.control(return_text={})
        code, out, err = self.main()
        self.assertEqual(code, 0, err)
        self.assertIn("resuming Q98's open batch", out)
        self.assertEqual([r["state"] for r in self.ledger()],
                         ["planned", "running", "infra-failed", "running", "scored"])

    def test_a_replay_waits_while_memory_is_short_and_writes_nothing(self):
        with mock.patch.object(sandbox, "mem_available_gb", return_value=10.0):
            code, out, err = self.main()
        self.assertEqual(code, 3)
        self.assertIn("deferred", err)
        self.assertFalse((self.root / "research" / "runs" / "Q98").exists())

    def test_acceptance_commands_follow_the_lines(self):
        contract = {"allowed-files": [sc.AGENT_D], "acceptance": [
            f"`scripts/vcheck --gate {sc.AGENT_D}` exits 0",
            "zero tool-counted holes in the allowed file",
            f"`scripts/vaudit --compare expected/Q98_Agent.audit {sc.AGENT_D}` reports no difference"]}
        self.assertEqual([(i, f, a) for i, f, a in cl.acceptance_commands(contract)], [
            (0, "vcheck-gate-json", ["scripts/vcheck", "--gate", "--json", sc.AGENT_D]),
            (2, "vaudit-compare", ["scripts/vaudit", "--compare", "expected/Q98_Agent.audit", sc.AGENT_D])])
        only_holes = {"allowed-files": [sc.AGENT_D], "acceptance": ["zero holes in it"]}
        self.assertEqual(cl.acceptance_commands(only_holes),
                         [(0, "vcheck-gate-json", ["scripts/vcheck", "--gate", "--json", sc.AGENT_D])])


if __name__ == "__main__":
    unittest.main()
