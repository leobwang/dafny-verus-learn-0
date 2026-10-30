"""The sandbox side of fvh's agent-mode batches (the user's decision D8; DV5d): the
manifest of one agent session on a benchmark task (dvl.sandbox.build_agent: a task
file, or a crate card whose sources are editable and whose other files are read-only
companions; a continuation's work copy inline), the self-test's attestation of a
card and of a continuation's work copy, live_run's per-request seeds, its gate files
in the caller's directory and a caller that holds the GPU calendar lock
(calendar_held_by), and `mksandbox-run --build-agent` / `--agent-session`.

Against test_agent_run's fake docker and fake gate: no container starts and no model
is called. Every fixture is a decoy in a throwaway root (sandbox_common.make_root):
the invented module Q98, invented task files."""

import fcntl
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
from test_agent_run import FakeHost  # noqa: E402

CARD = "bench/local/q/lab9/c1/tasks"
FILE_TASK = "bench/local/q/lab9/d1/tasks/d1.dfy"
CARGO = '[package]\nname = "decoy_agent_c1"\n'
FROZEN = "// decoy statements\n"
LIB = "// decoy task form\n"


def put_tasks(root):
    sc.write(root, "bench/local/q/lab9/STRATUM.toml", 'schema = 1\nlab = "Q98"\n')
    sc.write(root, f"{CARD}/Cargo.toml", CARGO)
    sc.write(root, f"{CARD}/frozen.rs", FROZEN)
    sc.write(root, f"{CARD}/src/lib.rs", LIB)
    sc.write(root, f"{CARD}/src/extra/more.rs", "// decoy second source\n")
    sc.write(root, FILE_TASK, "// decoy file task\nlemma DecoyD1() ensures true { }\n")


def attest(root, *rels):
    text = (root / "sandbox" / "attested.toml").read_text()
    for r in rels:
        text += (f'\n[[card]]\npath = "{r}"\nsha256 = "{sc.sha((root / r).read_bytes())}"\n'
                 'attested = "2026-10-12"\n')
    (root / "sandbox" / "attested.toml").write_text(text)


class BuildAgent(unittest.TestCase):
    def setUp(self):
        self.root = sc.make_root()
        self.addCleanup(sc.cleanup, self.root)
        put_tasks(self.root)

    def build(self, task, **kw):
        kw.setdefault("brief", "# Task\n\nA decoy brief.\n")
        return sandbox.build_agent(self.root, task, model="fake-served-model", turns=7, **kw)

    def test_a_crate_task_stages_its_sources_editable_and_its_companions_read_only(self):
        raw = self.build(CARD, wall_s=900, gpu_s=600, mem_gb=16, run_id="fvh-x-s1")
        self.assertEqual(raw["module"], "Q98")                    # the stratum's lab
        files = {f["dst"]: f for f in raw["file"]}
        self.assertEqual(raw["file"][0]["dst"], sandbox.AGENT_BRIEF)
        self.assertEqual(files[sandbox.AGENT_BRIEF]["role"], "task")
        for r in ("src/lib.rs", "src/extra/more.rs"):
            self.assertEqual(files[f"{CARD}/{r}"]["role"], "editable", r)
            self.assertEqual(files[f"{CARD}/{r}"]["src"], f"{CARD}/{r}")
        for r in ("Cargo.toml", "frozen.rs"):
            self.assertEqual(files[f"{CARD}/{r}"]["role"], "task", r)
        self.assertEqual(sorted(raw["return"]), [f"{CARD}/src/extra/more.rs", f"{CARD}/src/lib.rs"])
        self.assertEqual(files["verus/Cargo.toml"]["role"], "project")
        self.assertEqual(raw["agent"], {"cli": "opencode", "model": "fake-served-model", "turns": 7,
                                        "gpu_s": 600})
        self.assertEqual((raw["network"], raw["kind"], raw["limits"]["wall_clock_s"]),
                         ("model", "agent", 900))
        m = sandbox.validate(raw, self.root)
        self.assertEqual(m.limits["mem_gb"], 16.0)                # the share, below Verus's 23.5
        self.assertEqual(sandbox.agent_brief(m), sandbox.AGENT_BRIEF)
        self.assertEqual(m.editable_dirs(), [f"{CARD}/src", f"{CARD}/src/extra"])

    def test_a_file_task_and_the_memory_cap_held_to_the_bound(self):
        raw = self.build(FILE_TASK, mem_gb=64)
        m = sandbox.validate(raw, self.root)
        self.assertEqual(m.returns, (FILE_TASK,))
        self.assertEqual(m.limits["mem_gb"], 15.5)                # Dafny's agent bound

    def test_a_continuation_stages_the_work_copy_inline(self):
        texts = {f"{CARD}/src/lib.rs": "// the agent's work\n",
                 f"{CARD}/src/extra/more.rs": "// more work\n"}
        raw = self.build(CARD, texts=texts)
        files = {f["dst"]: f for f in raw["file"]}
        self.assertEqual(files[f"{CARD}/src/lib.rs"]["text"], "// the agent's work\n")
        self.assertNotIn("src", files[f"{CARD}/src/lib.rs"])
        sandbox.validate(raw, self.root)
        with self.assertRaisesRegex(sandbox.ManifestError, "every editable file"):
            self.build(CARD, texts={f"{CARD}/src/lib.rs": "x"})

    def test_only_a_benchmark_task_is_inline_editable_in_an_agent_run(self):
        m = sc.agent_manifest(self.root)
        m["file"][0] = sc.text_entry(sc.AGENT_D, "editable", "// inline agentic file\n")
        with self.assertRaisesRegex(sandbox.ManifestError, "benchmark task file"):
            sandbox.validate(m, self.root)

    def test_refusals(self):
        for task, match in (("dafny/Q/Q98_Sandbox/std/Q98_Sandbox.dfy", "benchmark task"),
                            ("bench/local/q/lab9/c9/tasks", "no such task"),
                            ("bench/local/q/card01/tasks/task.dfy", "no module")):
            with self.assertRaisesRegex(sandbox.ManifestError, match):
                self.build(task)
        (self.root / CARD / "src" / "lib.rs").unlink()
        with self.assertRaisesRegex(sandbox.ManifestError, "Cargo.toml and src/lib.rs"):
            self.build(CARD)

    def test_the_self_test_attests_the_card_and_a_continuations_card(self):
        def report(raw):
            m = sandbox.validate(raw, self.root)
            run = sandbox.materialize(m, self.root)
            try:
                return sandbox.selftest(m, run, self.root)
            finally:
                sandbox.remove_run(run)
        texts = {f"{CARD}/src/lib.rs": "// work\n", f"{CARD}/src/extra/more.rs": "// more\n"}
        for raw in (self.build(CARD), self.build(CARD, texts=texts)):
            rep = report(raw)
            self.assertFalse(rep["ok"])
            self.assertTrue(any("attested" in p for p in rep["checks"]["attestation"]["problems"]))
        attest(self.root, *(f"{CARD}/{r}" for r in ("Cargo.toml", "frozen.rs", "src/lib.rs",
                                                      "src/extra/more.rs")))
        for raw in (self.build(CARD), self.build(CARD, texts=texts)):
            rep = report(raw)
            self.assertTrue(rep["ok"], rep["checks"])
            self.assertEqual(rep["checks"]["attestation"]["cards"], 4)


class AgentSession(FakeHost):
    def setUp(self):
        super().setUp()
        put_tasks(self.root)
        attest(self.root, *(f"{CARD}/{r}" for r in ("Cargo.toml", "frozen.rs", "src/lib.rs",
                                                     "src/extra/more.rs")))
        self.gate_dir = sc.tmpdir("dvl0-agent-gatedir-")
        self.addCleanup(sc.cleanup, self.gate_dir)

    def manifest(self, turns=5):
        return sandbox.build_agent(self.root, CARD, brief="# decoy brief\n",
                                   model="fake-served-model", turns=turns, wall_s=600, gpu_s=300,
                                   mem_gb=0.5, run_id="fvh-decoy-s1")

    def live(self, raw, **kw):
        man = sandbox.validate(raw, self.root)
        run = sandbox.materialize(man, self.root)
        try:
            return sandbox.live_run(man, run, root=self.root, **kw)
        finally:
            sandbox.remove_run(run)

    def test_a_crate_session_gets_its_seeds_and_writes_its_gate_files_where_asked(self):
        self.control(return_text={f"{CARD}/src/lib.rs": "// the agent's delivery\n"})
        code, rec = self.live(self.manifest(), seeds=[11, 12, 13, 14, 15, 16],
                              gate_dir=self.gate_dir)
        self.assertEqual((code, rec["ended_by"]), (0, "done"), rec.get("detail"))
        self.assertEqual(self.gate_cfgs[0]["seeds"], [11, 12, 13, 14, 15, 16])
        self.assertEqual(self.gate_cfgs[0]["caps"], {"calls": 5, "gpu_s": 300.0})
        self.assertEqual(rec["seeds"], [11, 12, 13, 14, 15, 16])
        self.assertTrue((self.gate_dir / "gate-counts.json").is_file())
        self.assertEqual(sorted(rec["gate"]["files"]), ["gate-counts.json", "gate.log"])
        self.assertNotIn("gate.log", rec["gate"])                 # no text inline
        self.assertEqual(rec["return"]["returned"], [f"{CARD}/src/lib.rs"])
        self.assertEqual(rec["_returned"].returned[f"{CARD}/src/lib.rs"],
                         b"// the agent's delivery\n")
        # the agent is pointed at the brief, and the companions are read-only binds
        argv = json.loads((self.state / "agent-argv.json").read_text())
        self.assertIn("/work/TASK.md", argv[-1])
        run_line = [c for c in self.calls() if c[:2] == ["run", "--detach"]][0]
        binds = [run_line[i + 1] for i, a in enumerate(run_line) if a == "--mount"]
        self.assertTrue(any(f"destination=/work/{CARD}/Cargo.toml,readonly" in b for b in binds))
        self.assertTrue(any(f"destination=/work/{CARD}/src," in b and "tmpfs" in b for b in binds))
        with tarfile.open(self.state / "dvl-fvh-decoy-s1.in.tar") as tf:
            self.assertEqual(sorted(tf.getnames()), [f"{CARD}/src/extra/more.rs",
                                                     f"{CARD}/src/lib.rs"])

    def test_seeds_are_an_agent_runs_and_one_per_turn(self):
        with self.assertRaisesRegex(sandbox.SandboxError, "one seed per turn"):
            self.live(self.manifest(turns=5), seeds=[1, 2, 3])
        with self.assertRaisesRegex(sandbox.SandboxError, "integers"):
            self.live(self.manifest(), seeds=[1, 2, "x", 4, 5])
        self.assertEqual(self.calls(), [])

    def test_a_caller_that_holds_the_calendar_lock_runs_and_another_holder_defers(self):
        lock = self.xdg / sandbox.GPU_LOCK
        fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
        self.addCleanup(os.close, fd)
        fcntl.flock(fd, fcntl.LOCK_EX)
        self.assertTrue(sandbox.calendar_held_by(fd))
        code, _ = self.live(self.manifest(), seeds=list(range(1, 6)), gate_dir=self.gate_dir,
                            calendar_held=True)
        self.assertEqual(code, 0)
        with self.assertRaisesRegex(sandbox.Deferred, "GPU calendar"):
            self.live(self.manifest(), seeds=list(range(1, 6)))
        # an open file on the lock that does not hold it, or on another file, holds nothing
        other = os.open(lock, os.O_RDWR)
        self.addCleanup(os.close, other)
        self.assertFalse(sandbox.calendar_held_by(other))
        stray = os.open(self.gate_dir / "x.lock", os.O_RDWR | os.O_CREAT, 0o600)
        self.addCleanup(os.close, stray)
        self.assertFalse(sandbox.calendar_held_by(stray))


class Cli(unittest.TestCase):
    """mksandbox-run's two agent-session forms: the manifest, and the usage rules."""

    def setUp(self):
        self.root = sc.make_root()
        self.addCleanup(sc.cleanup, self.root)
        put_tasks(self.root)
        from test_agent_run import APPARATUS
        sc.write(self.root, "sandbox/apparatus.toml", APPARATUS.format(sha="0" * 64))
        self.tmp = sc.tmpdir("dvl0-agent-cli-")
        self.addCleanup(sc.cleanup, self.tmp)
        env = mock.patch.dict(os.environ)               # the root's own apparatus file, not
        env.start()                                     # CI's sterile FVH_APPARATUS
        self.addCleanup(env.stop)
        os.environ.pop("FVH_APPARATUS", None)
        os.environ["DVL_MODEL"] = "fake-served-model"   # the model, named: no server asked
        os.environ["DVL_MODEL_URL"] = "http://127.0.0.1:9/v1"

    def test_build_agent_prints_a_manifest_that_validates(self):
        brief = sc.write(self.tmp, "TASK.md", "# decoy brief\n")
        texts = sc.write(self.tmp, "texts.json", json.dumps(
            {f"{CARD}/src/lib.rs": "// w\n", f"{CARD}/src/extra/more.rs": "// m\n"}))
        p = sc.run_mk(["--root", str(self.root), "--build-agent", "--task", CARD, "--brief",
                       str(brief), "--turns", "6", "--wall-s", "600", "--gpu-s", "120",
                       "--mem-gb", "16", "--run-id", "fvh-cli-s2", "--texts", str(texts)],
                      runtime=self.tmp)
        self.assertEqual(p.returncode, 0, p.stderr)
        raw = json.loads(p.stdout)
        self.assertEqual((raw["agent"]["turns"], raw["agent"]["gpu_s"], raw["run_id"],
                          raw["agent"]["model"]), (6, 120, "fvh-cli-s2", "fake-served-model"))
        self.assertEqual({f["dst"]: f.get("text") for f in raw["file"]
                          if f["role"] == "editable"},
                         {f"{CARD}/src/lib.rs": "// w\n", f"{CARD}/src/extra/more.rs": "// m\n"})
        sandbox.validate(raw, self.root)

    def test_the_forms_and_their_options_go_together(self):
        brief = sc.write(self.tmp, "TASK.md", "# decoy brief\n")
        for args in (["--seeds", "s.json", "m.json"], ["--calendar-fd", "9", "m.json"],
                     ["--task", CARD, "m.json"], ["--agent-session", "m.json"],
                     ["--build-agent", "--task", CARD]):
            p = sc.run_mk(["--root", str(self.root), *args], runtime=self.tmp)
            self.assertEqual(p.returncode, 2, (args, p.stderr))
        p = sc.run_mk(["--root", str(self.root), "--build-agent", "--task", "dafny/x.dfy",
                       "--brief", str(brief), "--turns", "3"], runtime=self.tmp)
        self.assertEqual(p.returncode, 3)
        self.assertIn("benchmark task", p.stderr)


if __name__ == "__main__":
    unittest.main()
