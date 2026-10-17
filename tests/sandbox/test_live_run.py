"""The live run of scripts/mksandbox-run against a fake docker (DV4-PLAN §5.5-§5.10,
DV4 step 2b), the verify manifest builder, the [[command]] rules, the /work
layout, and the reaper. No container starts: `docker` is a fake on PATH that
keeps its state in a temporary directory and answers each subcommand the run
uses (run, exec, inspect, rm, kill, ps). The real runs are the by-hand
acceptance script tests/acceptance/sandbox_doors.py.

Every fixture is a decoy in a throwaway root (sandbox_common.make_root)."""

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

FAKE_DOCKER = r'''#!/usr/bin/env python3
import io, json, os, sys, tarfile, time
st = os.environ["FAKE_DOCKER_STATE"]
ctl_p = os.path.join(st, "control.json")
ctl = json.load(open(ctl_p)) if os.path.exists(ctl_p) else {}
args = sys.argv[1:]
with open(os.path.join(st, "calls.jsonl"), "a") as fh:
    fh.write(json.dumps(args) + "\n")
def state(name):
    p = os.path.join(st, name + ".json")
    return json.load(open(p)) if os.path.exists(p) else None
def save(name, s):
    json.dump(s, open(os.path.join(st, name + ".json"), "w"))
cmd = args[0]
if cmd == "version":
    print("29.1.3"); sys.exit(0)
if cmd == "run":
    name = args[args.index("--name") + 1]
    save(name, {"Running": True, "OOMKilled": False})
    print("f" * 64); sys.exit(ctl.get("run_exit", 0))
if cmd == "exec":
    i = 1
    while args[i].startswith("--"):
        i += 2 if args[i] == "--env" else 1
    name, rest = args[i], args[i + 1:]
    if rest[0] == "/usr/bin/tar" and "--extract" in rest:
        open(os.path.join(st, name + ".in.tar"), "wb").write(sys.stdin.buffer.read()); sys.exit(0)
    if rest[0] == "/usr/bin/tar" and "--create" in rest:
        src = tarfile.open(os.path.join(st, name + ".in.tar"))
        buf = io.BytesIO()
        out = tarfile.open(fileobj=buf, mode="w")
        for m in src.getmembers():
            data = src.extractfile(m).read()
            if m.name in ctl.get("return_text", {}):
                data = ctl["return_text"][m.name].encode()
            ti = tarfile.TarInfo(m.name); ti.size = len(data)
            out.addfile(ti, io.BytesIO(data))
        for extra in ctl.get("return_extra", []):
            ti = tarfile.TarInfo(extra); ti.size = 3
            out.addfile(ti, io.BytesIO(b"new"))
        out.close()
        sys.stdout.buffer.write(buf.getvalue()); sys.exit(0)
    if "/opt/dvl/bin/controls" in rest and rest[-1] == "check":
        req = json.loads(sys.stdin.read() or "{}")
        json.dump(req, open(os.path.join(st, "controls-request.json"), "w"))
        rep = ctl.get("controls", {"schema": 1, "ok": True,
                                   "controls": [{"id": "C1", "ok": True, "detail": "fake"}]})
        print(json.dumps(rep)); sys.exit(0 if rep["ok"] else 1)
    beh = ctl.get("command", {})
    time.sleep(beh.get("sleep", 0))
    if beh.get("die"):
        save(name, {"Running": False, "OOMKilled": True, "ExitCode": 137, "Error": ""})
        sys.exit(137)
    print(beh.get("stdout", json.dumps({"verdict": "verified", "target": "/work/x"})))
    sys.exit(beh.get("exit", 0))
if cmd == "inspect":
    s = state(args[-1])
    if s is None:
        sys.exit(1)
    print(json.dumps(s)); sys.exit(0)
if cmd in ("rm", "kill"):
    p = os.path.join(st, args[-1] + ".json")
    if os.path.exists(p):
        os.unlink(p)
    sys.exit(0)
if cmd == "ps":
    print(ctl.get("ps", ""), end=""); sys.exit(0)
sys.exit(0)
'''


class Live(unittest.TestCase):
    def setUp(self):
        self.root = sc.make_root(git=True)
        self.bin = sc.tmpdir("dvl0-live-bin-")
        self.xdg = sc.tmpdir("dvl0-live-xdg-")
        self.state = sc.tmpdir("dvl0-live-docker-")
        self.addCleanup(sc.cleanup, self.root, self.bin, self.xdg, self.state)
        sc.fake_bin(self.bin, "docker", FAKE_DOCKER.split("\n", 1)[1]).write_text(FAKE_DOCKER)
        env = {"PATH": f"{self.bin}:{os.environ.get('PATH', '/usr/bin:/bin')}",
               "XDG_RUNTIME_DIR": str(self.xdg), "FAKE_DOCKER_STATE": str(self.state)}
        p = mock.patch.dict(os.environ, env)
        p.start()
        self.addCleanup(p.stop)
        os.environ.pop("DVL_NO_DOCKER", None)
        m = mock.patch.object(sandbox, "mem_available_gb", return_value=100.0)
        m.start()
        self.addCleanup(m.stop)
        g = mock.patch.object(sandbox, "start_gate", side_effect=self.fake_gate)
        g.start()
        self.addCleanup(g.stop)

    def fake_gate(self, manifest, run, cfg=None, upstream=None, out=None):
        class P:
            pid = None

            def terminate(self):
                pass

            def wait(self, timeout=None):
                return 0
        ((out or run.out) / "gate.log").write_text('{"event": "start"}\n')
        return P()

    def control(self, **kw):
        (self.state / "control.json").write_text(json.dumps(kw))

    def calls(self):
        p = self.state / "calls.jsonl"
        return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []

    def live(self, m, probe=False, **kw):
        man = sandbox.validate(m, self.root)
        run = sandbox.materialize(man, self.root)
        try:
            return sandbox.live_run(man, run, probe=probe, root=self.root, **kw)
        finally:
            sandbox.remove_run(run)

    def vmanifest(self, **over):
        m = sc.verify_manifest(self.root, **over)
        m["limits"] = {"mem_gb": 0.5, "wall_clock_s": 60}
        m["command"] = [{"argv": ["scripts/vcheck", "--gate", "--json", sc.AGENT_D]}]
        return m

    def test_a_verify_run_streams_in_checks_runs_its_commands_and_removes_the_container(self):
        code, rec = self.live(self.vmanifest())
        self.assertEqual((code, rec["ended_by"], rec["removed"]), (0, "done", True))
        self.assertEqual(rec["commands"][0]["exit_code"], 0)
        self.assertEqual(json.loads(rec["commands"][0]["stdout"])["verdict"], "verified")
        self.assertEqual((rec["root"], rec["scratch"]), ("/work", sandbox.CONTAINER_SCRATCH))
        verbs = [c[0] for c in self.calls()]
        self.assertEqual(verbs[0], "run")
        self.assertIn("rm", verbs)
        with tarfile.open(self.state / "dvl-q98-verify1.in.tar") as tf:
            self.assertEqual(tf.getnames(), [sc.AGENT_D])          # editable files only
        req = json.loads((self.state / "controls-request.json").read_text())
        self.assertEqual(req["editable_dirs"], ["dafny/Q/Q98_Sandbox/agent"])
        self.assertIn("scripts/vcheck", req["readonly"])
        run = self.calls()[0]
        for flag in ("--read-only", "--cap-drop", "--network", "--init", "--pids-limit"):
            self.assertIn(flag, run)
        self.assertNotIn("--rm", run)        # removed explicitly, after docker inspect

    def test_failing_controls_stop_the_run_before_any_command(self):
        self.control(controls={"schema": 1, "ok": False,
                               "controls": [{"id": "C4", "ok": False, "detail": "an interface"}]})
        code, rec = self.live(self.vmanifest())
        self.assertEqual((code, rec["ended_by"], rec["commands"]), (1, "controls-failed", []))
        self.assertTrue(rec["removed"])

    def test_the_wall_clock_kills_the_run(self):
        self.control(command={"sleep": 5})
        m = self.vmanifest()
        m["limits"]["wall_clock_s"] = 1
        code, rec = self.live(m)
        self.assertEqual((code, rec["ended_by"], rec["commands"][0]["killed"]), (124, "wall-clock", "wall-clock"))
        self.assertIn(["kill", "dvl-q98-verify1"], self.calls())

    def test_a_container_killed_for_memory_is_never_a_verdict(self):
        self.control(command={"die": True})
        code, rec = self.live(self.vmanifest())
        self.assertEqual((code, rec["ended_by"], rec["commands"][0]["killed"]), (1, "killed(memory)", "memory"))

    def test_an_agent_probe_returns_the_changed_file_as_a_patch(self):
        m = sc.agent_manifest(self.root, agent={"cli": "none", "model": "qwen3.8:latest", "turns": 1})
        m["limits"] = {"mem_gb": 0.5, "wall_clock_s": 60}
        self.control(return_text={sc.AGENT_D: sc.AGENT_TEXT + "// changed\n"}, return_extra=["stray.txt"])
        code, rec = self.live(m, probe=True)
        self.assertEqual((code, rec["ended_by"]), (0, "done"))
        self.assertEqual(rec["return"]["returned"], [sc.AGENT_D])
        self.assertEqual([r["name"] for r in rec["return"]["rejected"]], ["stray.txt"])
        dest = self.state / "rec"
        sandbox.write_live_records(dest, rec)
        self.assertIn("+// changed", (dest / "patch.diff").read_text())
        self.assertTrue((dest / "returned" / sc.AGENT_D).is_file())
        self.assertNotIn("_returned", json.loads((dest / "run.json").read_text()))

    def test_a_credential_shaped_string_withholds_the_returned_file(self):
        m = sc.agent_manifest(self.root, agent={"cli": "none", "model": "qwen3.8:latest", "turns": 1})
        m["limits"] = {"mem_gb": 0.5, "wall_clock_s": 60}
        planted = "// sk-ant-oat01-" + "Q" * 40 + "\n"
        self.control(return_text={sc.AGENT_D: sc.AGENT_TEXT + planted})
        code, rec = self.live(m, probe=True)
        dest = self.state / "rec"
        sandbox.write_live_records(dest, rec)
        doc = json.loads((dest / "run.json").read_text())
        self.assertEqual(doc["secret_scan"]["withheld"][0]["name"], sc.AGENT_D)
        self.assertFalse((dest / "returned" / sc.AGENT_D).exists())
        for f in dest.rglob("*"):
            if f.is_file():
                self.assertNotIn("sk-ant-oat01-QQQQ", f.read_text())

    # A stand-in value with no credential format: only the exact-value scan sees it.
    EXACT = "placeholder-value-0123456789abcdef"

    def test_the_fallback_forms_exact_value_withholds_a_returned_file(self):
        """DV4-PLAN §5.7's fallback form (DV5d): the exact value a run was given
        withholds a returned file that holds it; without it the file is kept."""
        m = sc.agent_manifest(self.root, agent={"cli": "none", "model": "qwen3.8:latest", "turns": 1})
        m["limits"] = {"mem_gb": 0.5, "wall_clock_s": 60}
        self.control(return_text={sc.AGENT_D: sc.AGENT_TEXT + f"// {self.EXACT}\n"})
        code, rec = self.live(m, probe=True)
        self.assertEqual(rec["secret_scan"]["withheld"], [])
        self.assertEqual(rec["return"]["returned"], [sc.AGENT_D])
        code, rec = self.live(m, probe=True, exact_secrets=[self.EXACT])
        self.assertEqual(code, 0)
        [w] = rec["secret_scan"]["withheld"]
        self.assertEqual((w["name"], w["findings"]), (sc.AGENT_D, ["exact-token"]))
        self.assertEqual(rec["secret_scan"]["exact_values"], 1)
        dest = self.state / "rec-exact"
        sandbox.write_live_records(dest, rec)
        self.assertFalse((dest / "returned" / sc.AGENT_D).exists())
        for f in dest.rglob("*"):
            if f.is_file():
                self.assertNotIn(self.EXACT, f.read_text())

    def test_the_fallback_forms_exact_value_withholds_a_command_log(self):
        self.control(command={"stdout": json.dumps({"verdict": "verified", "note": self.EXACT})})
        code, rec = self.live(self.vmanifest(), exact_secrets=(self.EXACT,))
        self.assertEqual((code, rec["ended_by"]), (0, "done"))
        entry = rec["commands"][0]
        self.assertEqual((entry["stdout"], entry["stderr"], entry["exit_code"]), ("", "", 0))
        self.assertEqual((entry["withheld"]["name"], entry["withheld"]["findings"]),
                         ("command-1.log", ["exact-token"]))
        self.assertEqual(rec["secret_scan"]["withheld"], [entry["withheld"]])
        self.assertNotIn(self.EXACT, json.dumps(rec))
        # a credential format in a command's output is withheld with no exact value too
        self.control(command={"stdout": "sk-ant-oat01-" + "Q" * 40})
        code, rec = self.live(self.vmanifest())
        self.assertEqual(rec["commands"][0]["withheld"]["findings"], ["anthropic-token"])
        self.assertNotIn("QQQQ", json.dumps(rec))
        # a clean run records no scan
        self.control()
        code, rec = self.live(self.vmanifest(), exact_secrets=(self.EXACT,))
        self.assertNotIn("secret_scan", rec)
        self.assertNotIn("withheld", rec["commands"][0])
        for bad in ("short", self.EXACT, [b"x" * 20], [None]):
            with self.assertRaisesRegex(sandbox.SandboxError, "at least 16 characters"):
                self.live(self.vmanifest(), exact_secrets=bad)

    def test_what_the_live_run_refuses(self):
        # an opencode run needs the apparatus pins (step 3a); this root has none
        m = sc.agent_manifest(self.root)
        with self.assertRaisesRegex(sandbox.SandboxError, "apparatus"):
            self.live(m)
        p = sc.agent_manifest(self.root, agent={"cli": "none", "model": "qwen3.8:latest", "turns": 1})
        with self.assertRaisesRegex(sandbox.SandboxError, "only under --probe"):
            self.live(p)
        d = self.vmanifest()
        d["command"] = [{"argv": [sandbox.CONTROLS, "door", "sleep", "1"]}]
        with self.assertRaisesRegex(sandbox.SandboxError, "only under --probe"):
            self.live(d)
        with self.assertRaisesRegex(sandbox.SandboxError, "probe"):
            self.live(self.vmanifest(), gate_upstream="http://127.0.0.1:9")
        self.assertEqual(self.calls(), [])                  # nothing reached docker

    def test_memory_short_defers_the_run(self):
        with mock.patch.object(sandbox, "mem_available_gb", return_value=10.0):
            with self.assertRaisesRegex(sandbox.Deferred, "deferred"):
                self.live(self.vmanifest())
        self.assertEqual(self.calls(), [])

    def test_the_reaper_removes_only_containers_whose_owner_is_gone(self):
        me = f"{os.getpid()}:{sandbox._proc_start(os.getpid())}"
        self.control(ps=f"dvl-a\t999999:1\ndvl-b\t{me}\ndvl-c\t\n")
        gone = sandbox.reap()
        self.assertEqual(gone, ["dvl-a", "dvl-c"])
        self.assertIn(["rm", "--force", "dvl-a"], self.calls())
        self.assertNotIn(["rm", "--force", "dvl-b"], self.calls())


class Layout(unittest.TestCase):
    def setUp(self):
        self.root = sc.make_root(git=True)
        self.addCleanup(sc.cleanup, self.root)

    def test_each_editable_directory_is_a_tmpfs_of_its_own(self):
        man = sandbox.validate(sc.agent_manifest(self.root), self.root)
        mounts = sandbox.work_mounts(man)
        self.assertEqual(mounts[0][0], "/work")
        self.assertIn("tmpfs-mode=755", mounts[0][1])
        self.assertEqual(mounts[1][0], "/work/dafny/Q/Q98_Sandbox/agent")
        self.assertIn("tmpfs-mode=1777", mounts[1][1])
        argv = sandbox.docker_argv(man, "/RUN", "1:2")[0]
        dests = [a.split("destination=")[1].split(",")[0] for a in argv if "destination=" in a]
        self.assertEqual(dests, sorted(dests, key=lambda d: (d.count("/"), d)))   # parents first

    def test_commands_are_trusted_tools_on_staged_paths(self):
        staged = {sc.AGENT_D, "scripts/vcheck", "scripts/vaudit", "expected/Q98_Agent.audit"}
        tools = {"scripts/vcheck", "scripts/vaudit"}
        ok = [["scripts/vcheck", "--gate", "--json", sc.AGENT_D],
              ["scripts/vcheck", "--gate", "dafny/Q/Q98_Sandbox/agent"],
              ["scripts/vaudit", "--compare", "expected/Q98_Agent.audit", sc.AGENT_D],
              [sandbox.CONTROLS, "door", "sleep", "3"]]
        for argv in ok:
            self.assertIsNone(sandbox.command_problem(argv, staged, tools), argv)
        bad = [["bash", "-c", "true"], ["scripts/specfreeze", "--against", sc.AGENT_D, sc.AGENT_D],
               ["scripts/vcheck", "--ref", sc.AGENT_D], ["scripts/vcheck", "--gate", "/etc/passwd"],
               ["scripts/vcheck", "--gate", "dafny/Q/Q97_Other/agent/Q97_Agent.dfy"],
               ["scripts/vcheck", "--gate", "a b"], [sandbox.CONTROLS, "check"],
               [sandbox.CONTROLS, "door", "rm"], []]
        for argv in bad:
            self.assertIsNotNone(sandbox.command_problem(argv, staged, tools), argv)

    def test_lab_code_own_requires_a_gate_and_task_and_matches_vcheck_cli(self):
        task = "lab-task/" + sc.AGENT_D
        staged = {sc.AGENT_D, task, "scripts/vcheck"}
        tools = {"scripts/vcheck"}
        argv = ["scripts/vcheck", "--gate", "--lab-task", task,
                "--lab-code", "own", sc.AGENT_D]
        self.assertIsNone(sandbox.command_problem(argv, staged, tools))
        for bad in (argv[:1] + argv[2:],
                    [a for a in argv if a not in ("--lab-task", task)],
                    ["preserve" if a == "own" else a for a in argv],
                    ["other" if a == "own" else a for a in argv]):
            self.assertIsNotNone(sandbox.command_problem(bad, staged, tools), bad)

    def test_a_verify_run_may_carry_a_work_copy_inline_at_a_learner_path(self):
        m = sc.verify_manifest(self.root, file=[
            sc.text_entry(sc.EX_D, "editable", "// a work copy\n"),
            sc.entry(self.root, "scripts/vcheck", "tool")])
        man = sandbox.validate(m, self.root)
        self.assertEqual(man.files[0].text, "// a work copy\n")
        m = sc.verify_manifest(self.root, file=[
            sc.text_entry("dafny/Q/Q97_Other/agent/Q97_Agent.dfy", "editable", "// another module\n")])
        with self.assertRaises(sandbox.ManifestError):
            sandbox.validate(m, self.root)
        a = sc.agent_manifest(self.root)
        a["file"][0] = sc.text_entry(sc.AGENT_D, "editable", "// inline in a real agent run\n")
        with self.assertRaises(sandbox.ManifestError):
            sandbox.validate(a, self.root)

    def test_build_verify_finds_the_course_path_of_a_work_copy(self):
        work = sc.tmpdir("dvl0-live-work-")
        self.addCleanup(sc.cleanup, work)
        sc.write(work, sc.AGENT_D, "// the agent's work copy\n")
        argv = ["scripts/vcheck", "--gate", "--json", sc.AGENT_D]
        raw, rel = sandbox.build_verify(self.root, work / sc.AGENT_D, argv, run_id="b1")
        self.assertEqual(rel, sc.AGENT_D)
        ed = [f for f in raw["file"] if f["role"] == "editable"]
        self.assertEqual([(f["dst"], f.get("text")) for f in ed], [(sc.AGENT_D, "// the agent's work copy\n")])
        roles = {f["dst"]: f["role"] for f in raw["file"]}
        self.assertEqual(roles.get(sc.GIVEN_D), "given")
        self.assertEqual(roles.get("scripts/vcheck"), "tool")
        man = sandbox.validate(raw, self.root, check_image=False)
        self.assertEqual(man.commands, (tuple(argv),))
        with self.assertRaises(sandbox.ManifestError):
            sandbox.build_verify(self.root, work / "notes" / "x.dfy", argv)
        # an agent's returned files under research/ are a copy too, never a course path
        ret = f"research/runs/Q98/r1/returned/{sc.AGENT_D}"
        sc.write(self.root, ret, "// a returned file\n")
        raw, rel = sandbox.build_verify(self.root, ret, argv, run_id="b2")
        self.assertEqual(rel, sc.AGENT_D)
        self.assertEqual([f.get("text") for f in raw["file"] if f["role"] == "editable"],
                         ["// a returned file\n"])


if __name__ == "__main__":
    unittest.main()
