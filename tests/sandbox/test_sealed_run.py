"""The sealed run and par-run (QPLAN §31.3, §32.5; DELTAS Δ419; the user's D68, D102, D103):
no Docker, no key, no solver, no model, and nothing of any real sealed or held-out part. A
throwaway git root with an invented challenge record (Q31, solo), a SYNTHETIC sealed
stratum of part "probe" (two invented Dafny cards) with its single-use record, its
unsealed copy outside the root, an invented par-agent pin over random bytes, a fake
opencode (the backend tests' fake, which opens no connection) and a stub vcheck:

  - build_sealed: the learner's arm and par's run as agent containers on the model network
    with no agent CLI, the unsealed part inline at its stratum's paths after its check,
    the committed work as role graded, the spec staged without the host's path; the
    manifest rules around them (the one truth run in an agent container is par-run on the
    par-agent part; the batch runner never in a truth run; no editable file, no return
    path, a call cap only there); the docker lines (the grader tmpfs, the gate's
    read-only counts, the return of /work/grader/runs);
  - the return stream's parser: regular files under runs/ only, within the caps;
  - D103 on the return path: a par run directory holding a transcript, a call log, the
    proposals, the gate log and a run.json with the prompt hashes and the policy's name
    comes back as run.json's counts, the inputs and the verified files, and no byte of
    the prompt;
  - the container's batch in-process (fvh.sealed.inside, the image's opencode replaced
    by the fake): every call carries the attempt's pre-registered seed, the records say
    which transport ran them; the census of Δ412 drops a task it closes;
  - `fvh run --sealed` end to end with a stand-in launch that runs that batch: the ledger
    opened, settled by the returned records over two chunks, closed; resume refused;
  - `fvh par` end to end with truthcheck par-run in-process (its child a real
    subprocess): par's calls reserved in the ledger, its runs back counts only, the
    verdict counts only, fvh.report re-deriving them;
  - the gate's seed pool (test_model_gate.py) and a study session's guard on the new
    command lines (rule 1c)."""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "harness"))

from dvl import sandbox  # noqa: E402
from fvh import batch, budget, report, runlog, sealed, statements  # noqa: E402

GIT = ["git", "-c", "user.name=sandbox-tests", "-c", "user.email=sandbox-tests@example.invalid",
       "-c", "init.defaultBranch=main"]
STRATUM = "bench/local/q/agentic/q31-probe"
PAR_ARCHIVE = "Hidden/Agentic/Q31/par-agent.tar.age"
LEARNER_CANARY = "DVLCANARY-sealed-learner-5c2d"   # invented tokens: no real canary's hash
PAR_CANARY = "DVLCANARY-sealed-par-8e41"
TASK = "method M(x: int) returns (y: int)\n  ensures y == x\n{\n  y := x;\n}\n"

REGISTRY = """schema = 1

[[module]]
id = "Q31"
track = "Q"
status = "authoring"
tier = "challenge"
title = "Invented challenge module"
layer = ""
units = []
exercises = []
exits = []
agentic = []
harness = ["agents/q31_gate_bench/baselines.py"]
engines = ["policy"]
solo = true
budget = { claude_calls = 0, claude_runs = 0, qwen_calls = 40, qwen_runs = 20, gpu_hours = 1 }
"""

LEARNER_POLICY = f'''"""The learner's invented one-shot renderer."""

def one_shot_render(state, ctx, budget):
    return "learner prompt {LEARNER_CANARY} for " + ctx.task_id
'''

PAR_POLICY = f'''"""Par's invented renderer (a stand-in for the sealed one)."""

def render(state, ctx, budget):
    return "par prompt {PAR_CANARY} for " + ctx.task_id
'''

STUB_VCHECK = '''import json, sys
t = sys.argv[-1]
body = open(t).read() if not t.startswith("-") else ""
ok = "FAILME" not in body
print(json.dumps({"verdict": "verified" if ok else "failed", "holes": [], "lines": [],
                  "verified_count": 1 if ok else 0, "diagnostics": []}))
sys.exit(0 if ok else 1)
'''

PLAN = f'''seed = 31
tasks = ["c1", "c2"]
[task.c1]
path = "{STRATUM}/c1/tasks/c1.dfy"
[task.c2]
path = "{STRATUM}/c2/tasks/c2.dfy"
[[arm]]
name = "oneshot"
family = "qwen"
rounds = 2
construct = "model"
policy = "q31_gate_bench.baselines:one_shot_render"
'''

PAR_FRAGMENT = '''# an invented par fragment (labs/Q31/par/PLAN.toml)
system = "par system"
[arm]
construct = "model"
policy = "par_q31.policy:render"
[census]
construct = "model"
policy = "par_q31.policy:render"
'''


def git(root, *args):
    return subprocess.run(GIT + ["-C", str(root), *args], check=True, capture_output=True,
                          text=True).stdout


def canon(entry):
    return json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def make_root(tmp, tasks=None):
    """The git root (module docstring) and the unsealed copy outside it."""
    root = tmp / "course"
    for rel in ("scripts", "dafny/options", "sandbox/images.lock", "sandbox/apparatus.toml",
                "harness/fvh"):
        src, dst = ROOT / rel, root / rel
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    (root / "MODULES.toml").write_text(REGISTRY)
    tasks = tasks or {"c1": TASK, "c2": TASK.replace("M(", "N(")}
    cards = "".join(f'[[card]]\nid = "{c}"\nlang = "dafny"\nsource = "course-local"\n'
                    for c in tasks)
    files = {
        "agents/q31_gate_bench/__init__.py": "",
        "agents/q31_gate_bench/baselines.py": LEARNER_POLICY,
        "harness/q/fvh_q/__init__.py": "",
        "research/plans/sealed.toml": PLAN,
        f"{STRATUM}/STRATUM.toml":
            'schema = 1\nmodule = "Q31"\nlab = "Q31"\nstratum = "q31-probe"\npart = "probe"\n'
            'role = "held-out"\nsealed = true\narchive = "Hidden/Agentic/Q31/probe.tar.age"\n'
            f'archive_sha256 = "{"b" * 64}"\n' + cards,
    }
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    into = tmp / "unsealed" / "Q31" / "probe"
    written = {}
    for c, text in tasks.items():
        rel = f"{c}/tasks/{c}.dfy"
        (into / rel).parent.mkdir(parents=True, exist_ok=True)
        (into / rel).write_text(text)
        written[rel] = text.encode()
    entry = {"seq": 1, "prev": statements.GENESIS, "date": "2026-10-31T00:00:00+00:00",
             "module": "Q31", "part": "probe", "stratum": f"{STRATUM}/STRATUM.toml",
             "archive_sha256": "b" * 64, "manifest_sha256": "c" * 64, "files": len(written),
             "files_sha256": statements.tree_sha256(written), "statements": {}}
    (root / statements.LEDGER).write_text(canon(entry) + "\n")
    arc = root / PAR_ARCHIVE
    arc.parent.mkdir(parents=True, exist_ok=True)
    data = b"age-encryption.org/v1\n" + os.urandom(96)
    arc.write_bytes(data)
    (root / "sandbox" / "truth.toml").write_text(
        'schema = 1\n[[lab]]\nid = "Q31"\npart = "par-agent"\n'
        f'archive = "{PAR_ARCHIVE}"\nrecipient = "age1invented"\n'
        'identity = "~/.keys/invented.agekey"\n'
        f'sha256 = "{hashlib.sha256(data).hexdigest()}"\nfiles = 3\n')
    (root / ".gitignore").write_text("__pycache__/\n")
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "fixture")
    return root, into


def found():
    return {"base_url": "http://127.0.0.1:9/v1", "model": "probe-model", "max_model_len": 4096,
            "served": ["probe-model"], "version": None}


def app_of(root):
    from fvh import apparatus
    return apparatus.load(root / "sandbox" / "apparatus.toml")


def fake_opencode(tmp, reply=None):
    exe = tmp / "img" / "opencode"
    exe.parent.mkdir(parents=True, exist_ok=True)
    exe.write_text(f"#!{sys.executable}\n"
                   + (ROOT / "harness/tests/core/fakes/fake_opencode.py").read_text())
    exe.chmod(0o755)
    (exe.parent / "fake-control.json").write_text(json.dumps(
        {"reply": reply or json.dumps({"actions": [{"type": "stop", "reason": "done"}]})}))
    return exe


def calls_of(exe):
    p = exe.parent / "calls.jsonl"
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


def work_from(root, raw, work, exe):
    """What a sealed run's container holds at /work (each staged file at its dst), the
    stub vcheck over the tool copy, the fake in place of the image's opencode."""
    for f in raw["file"]:
        e = sandbox.Entry(f.get("src"), f["dst"], f["role"], f["sha256"], f.get("rev"),
                          f.get("text"))
        data = sandbox.read_source(root, e)
        p = work / f["dst"]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    (work / "scripts" / "vcheck").write_text(STUB_VCHECK)
    spec = json.loads((work / sealed.SPEC).read_text())
    spec["opencode"] = str(exe)
    (work / sealed.SPEC).write_text(json.dumps(spec))
    (work / sealed.GRADER).mkdir(exist_ok=True)
    return spec


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dvl0-sealed-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root, self.into = make_root(self.tmp)
        self.env = mock.patch.dict(os.environ, {"DVL_SCRATCH": str(self.tmp / "scratch")})
        self.env.start()
        self.addCleanup(self.env.stop)
        os.environ.pop("FVH_NO_MODEL", None)
        self.mods = dict(sys.modules)
        self.path = list(sys.path)

    def tearDown(self):
        for k in [k for k in sys.modules if k not in self.mods]:
            del sys.modules[k]
        sys.path[:] = self.path

    def plan(self):
        return batch.load_plan(self.root / "research/plans/sealed.toml", self.root,
                               tasks_at={STRATUM: self.into})

    def learner_spec(self, ids=None):
        plan = self.plan()
        ids = ids or [p.id for p in plan.items()]
        up = sealed.unsealed_part(self.root, "Q31", "probe", self.into)
        spec = sealed._spec_base(self.root, "Q31", "sealed-run", up, app_of(self.root), found(),
                                 ids=ids, seed_pool=[s for a in ids for s in plan.seeds(a)],
                                 calls=2 * len(ids), prereg="", stmts={},
                                 plan_sha256=plan.sha256)
        spec.update(plan_text=PLAN, unsealed=str(self.into))
        return spec


# --- the manifests ----------------------------------------------------------------------

class Manifests(Base):
    def test_the_learners_arm_is_an_agent_run_with_no_cli_and_its_part_inline(self):
        raw = sandbox.build_sealed(self.root, self.learner_spec(), mem_gb=8)
        m = sandbox.validate(raw, self.root, check_image=False)
        self.assertEqual((m.kind, m.network, m.agent["cli"], m.agent["calls"]),
                         ("agent", "model", "none", 4))
        self.assertEqual(sandbox.sealed_mode(m), "sealed-run")
        self.assertEqual(m.commands, ((sandbox.BATCHRUN, "Q31", "probe"),))
        roles = {e.dst: e.role for e in m.files}
        self.assertEqual(roles[f"{STRATUM}/c1/tasks/c1.dfy"], "task")
        self.assertEqual(roles["agents/q31_gate_bench/baselines.py"], "graded")
        self.assertEqual(roles["harness/fvh/sealed.py"], "given")
        self.assertNotIn("editable", roles.values())
        self.assertEqual(m.returns, ())
        self.assertIsNone(m.truth)
        spec = json.loads(next(e.text for e in m.files if e.dst == sealed.SPEC))
        self.assertNotIn("unsealed", spec)
        self.assertNotIn("plan_text", spec)
        self.assertNotIn(str(self.into), json.dumps(spec))
        self.assertTrue(spec["image"].startswith("dvl-agent@sha256:"))
        self.assertEqual(next(e.text for e in m.files if e.dst == sealed.PLAN), PLAN)
        lines = sandbox.docker_argv(m, "/RUN")
        run = " ".join(lines[0])
        self.assertIn(f"destination={sandbox.WORK}/{sandbox.GRADER_DIR},", run)
        self.assertIn(f"source=/RUN/gate-view,destination={sandbox.GATE_VIEW_DIR},readonly", run)
        self.assertIn("--network dvl-int-", run)
        self.assertEqual(lines[-2][-5:], ["--directory", "/work/grader", "--file", "-", "runs"])
        self.assertEqual(lines[3][-3:], [sandbox.BATCHRUN, "Q31", "probe"])

    def test_par_is_the_one_truth_run_in_an_agent_container(self):
        spec = self.learner_spec()
        spec.update(kind="par-run", par={"seed": 31}, plan_sha256="")
        spec.pop("plan_text")
        raw = sandbox.build_sealed(self.root, spec, archive=PAR_ARCHIVE)
        m = sandbox.validate(raw, self.root, check_image=False)
        self.assertEqual(m.truth["part"], "par-agent")
        self.assertEqual(m.commands, ((sandbox.TRUTHCHECK, "par-run", "Q31", "probe"),))
        self.assertEqual(sandbox.sealed_mode(m), "par-run")
        self.assertIn(f"source=/RUN/truth,destination={sandbox.TRUTH_DIR},readonly",
                      " ".join(sandbox.docker_argv(m, "/RUN")[0]))
        with self.assertRaisesRegex(sandbox.ManifestError, "par-agent archive"):
            sandbox.build_sealed(self.root, spec)
        with self.assertRaisesRegex(sandbox.ManifestError, "build_sealed"):
            sandbox.build_truth(self.root, "Q31", "par-run", part="par-agent")

    def test_the_manifest_rules_around_the_sealed_forms(self):
        spec = self.learner_spec()
        good = sandbox.build_sealed(self.root, spec)

        def problems(raw):
            try:
                sandbox.validate(raw, self.root, check_image=False)
            except sandbox.ManifestError as e:
                return " ".join(e.problems)
            return ""
        pin = sandbox.truth_pins(self.root)["Q31:par-agent"]
        truth = {"lab": "Q31", "part": "par-agent", "archive": pin["archive"],
                 "sha256": pin["sha256"]}
        # a truth table on an agent container for any mode but par-run
        bad = dict(good, truth=truth, command=[{"argv": [sandbox.TRUTHCHECK, "manifest", "Q31"]}])
        self.assertIn("only a verification container", problems(bad))
        # the batch runner never in a truth run
        bad = dict(good, truth=truth)
        self.assertIn("are the grader's (/opt/dvl/bin/truthcheck) and nothing else", problems(bad))
        # par-run in a verification container
        v = dict(good, kind="verify", network="none", agent=None, truth=truth,
                 command=[{"argv": [sandbox.TRUTHCHECK, "par-run", "Q31", "probe"]}])
        v.pop("agent")
        self.assertIn("par-run unseals", problems(v))
        # an editable file, a return path, an inline task elsewhere, no call cap
        ed = dict(good, file=good["file"] + [{"dst": f"{STRATUM}/c9/tasks/c9.dfy",
                                              "role": "editable", "text": TASK,
                                              "sha256": sandbox.sha256_bytes(TASK.encode())}])
        self.assertIn("stages no editable file", problems(ed))
        stray = dict(good, file=good["file"] + [{"dst": "notes/x.txt", "role": "task",
                                                 "text": "x",
                                                 "sha256": sandbox.sha256_bytes(b"x")}])
        self.assertIn("a sealed run's inline task", problems(stray))
        nocap = dict(good, agent={k: v for k, v in good["agent"].items() if k != "calls"})
        self.assertIn("names its call cap", problems(nocap))
        # a call cap outside a sealed run
        probe = dict(good, command=[{"argv": ["scripts/vcheck", "--gate", f"{STRATUM}/c1/tasks/c1.dfy"]}])
        self.assertIn("only a sealed run's", problems(probe))
        self.assertEqual(problems(good), "")

    def test_the_part_and_the_work_are_checked_before_anything_is_staged(self):
        spec = self.learner_spec()
        (self.into / "c1/tasks/c1.dfy").write_text(TASK + "// edited after the unseal\n")
        with self.assertRaisesRegex(sandbox.ManifestError, "exactly as it was unsealed"):
            sandbox.build_sealed(self.root, spec)
        (self.into / "c1/tasks/c1.dfy").write_text(TASK)
        (self.root / "agents/q31_gate_bench/baselines.py").write_text(LEARNER_POLICY + "# x\n")
        with self.assertRaisesRegex(sandbox.ManifestError, "commit it first"):
            sandbox.build_sealed(self.root, spec)


class GraderReturn(unittest.TestCase):
    def stream(self, members):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tf:
            for name, kind, data in members:
                ti = tarfile.TarInfo(name)
                if kind == "file":
                    ti.size = len(data)
                    tf.addfile(ti, io.BytesIO(data))
                elif kind == "link":
                    ti.type, ti.linkname = tarfile.SYMTYPE, "/etc/passwd"
                    tf.addfile(ti)
                else:
                    ti.type = tarfile.DIRTYPE
                    tf.addfile(ti)
        buf.seek(0)
        return buf

    def test_only_regular_files_under_runs_within_the_caps(self):
        got = sandbox.parse_grader_return(self.stream([
            ("runs", "dir", b""), ("runs/r1", "dir", b""), ("runs/r1/run.json", "file", b"{}"),
            ("runs/r1/big", "file", b"x" * 64), ("runs/r1/link", "link", b""),
            ("other/x", "file", b"x"), ("runs/../x", "file", b"x")]), file_cap=32)
        self.assertEqual(list(got["files"]), ["runs/r1/run.json"])
        why = {r["name"]: r["why"] for r in got["rejected"]}
        self.assertIn("per-file cap", why["runs/r1/big"])
        self.assertIn("not a regular file", why["runs/r1/link"])
        self.assertIn("outside runs/", why["other/x"])
        self.assertIn("outside runs/", why["runs/../x"])
        got = sandbox.parse_grader_return(self.stream([
            ("runs/a", "file", b"x" * 20), ("runs/b", "file", b"x" * 20)]), cap=30)
        self.assertEqual(list(got["files"]), ["runs/a"])


# --- D103: par's return path ---------------------------------------------------------------

def par_run_dir(base, *, canary=PAR_CANARY):
    """A par run directory as fvh.batch writes one in the container, every file of it."""
    rd = base / "20261031T000000Z-par-c1-1-1"
    rd.mkdir(parents=True)
    runlog.write_inputs(rd, {f"{STRATUM}/c1/tasks/c1.dfy": TASK.encode()})
    (rd / "returned" / STRATUM / "c1" / "tasks").mkdir(parents=True)
    (rd / "returned" / STRATUM / "c1" / "tasks" / "c1.dfy").write_text(TASK)
    for name in ("actions.jsonl", "observations.jsonl", "calls.jsonl", "feedback.jsonl",
                 "acceptance.jsonl", "patch.diff", "verify.json", "gate-counts.json"):
        (rd / name).write_text(json.dumps({"prompt": f"par prompt {canary}"}) + "\n")
    import gzip
    for name in ("transcript.jsonl.gz", "gate.log.gz"):
        (rd / name).write_bytes(gzip.compress(f"par prompt {canary}".encode()))
    meta = runlog.RunMeta(
        run_id=rd.name, module="Q31", arm="par", task_id="c1", lang="dafny", attempt=1,
        repeat=1, mode="harness-executed", backend="qwen", outcome="verified", ended_by="stop",
        verify={"verdict": "verified", "holes": [], "verified_count": 1},
        usage={"calls": 1, "gpu_s": 0.5},
        apparatus={"prompt_hashes": ["e" * 64], "arm_policy": "par_q31.policy:render",
                   "policy_source_sha256": "f" * 64, "plan_sha256": "1" * 64,
                   "calls": [{"prompt": canary}], "seeds": [7],
                   "lab_task": f"{STRATUM}/c1/tasks/c1.dfy"},
        findings=(f"note {canary}",))
    runlog.write_meta(rd, meta)
    return rd


def all_bytes(top):
    out = b""
    for p in Path(top).rglob("*"):
        if p.is_file():
            data = p.read_bytes()
            if p.suffix == ".gz":
                import gzip
                data = gzip.decompress(data)
            out += data
    return out


class CountsOnly(Base):
    def assert_counts_only(self, d):
        names = sorted(p.relative_to(d).as_posix() for p in d.rglob("*") if p.is_file())
        self.assertEqual(names, ["inputs.sha256", "inputs.tar.gz",
                                 f"returned/{STRATUM}/c1/tasks/c1.dfy", "run.json"])
        self.assertNotIn(PAR_CANARY.encode(), all_bytes(d))
        meta = runlog.load_meta(d)
        for k in ("prompt_hashes", "arm_policy", "policy_source_sha256", "plan_sha256", "calls"):
            self.assertNotIn(k, meta.apparatus)
        self.assertTrue(meta.apparatus["counts_only"])
        self.assertTrue(report.rederive(d, meta).ok)

    def test_a_par_record_comes_back_as_counts_only_on_the_host(self):
        rd = par_run_dir(self.tmp / "returned")
        dest = sealed.import_par(self.root, "Q31", rd, part="probe", archive_sha256="9" * 64)
        self.assertEqual(dest.name, f"par-probe-{rd.name}")
        self.assert_counts_only(dest)

    def test_and_in_the_container_before_the_return(self):
        work = self.tmp / "work"
        rd = par_run_dir(work / "grader" / "runs")
        (work / "grader" / "runs" / "ledger.jsonl").write_text("{}\n")
        (work / "grader" / "runs" / "stray.txt").write_text(PAR_CANARY)
        self.assertEqual(sealed.strip_counts_only(work, part="probe", archive_sha256="9" * 64), 1)
        self.assertEqual(sorted(p.name for p in (work / "grader" / "runs").iterdir()), [rd.name])
        self.assert_counts_only(rd)


# --- the container's batch, in-process ------------------------------------------------------

class Inside(Base):
    def test_every_call_carries_its_seed_and_the_records_name_the_transport(self):
        exe = fake_opencode(self.tmp)
        raw = sandbox.build_sealed(self.root, self.learner_spec())
        work = self.tmp / "work"
        spec = work_from(self.root, raw, work, exe)
        view = self.tmp / "view.json"
        view.write_text(json.dumps({"calls": 0, "gpu_s": 0.0}))
        res = sealed.inside(work, view=view)
        plan = self.plan()
        ids = [p.id for p in plan.items()]
        self.assertEqual((res["ran"], res["left"]), (ids, []))
        self.assertEqual(set(res["states"].values()), {"scored"})
        runs = [d for d in (work / "grader" / "runs").iterdir() if d.is_dir()]
        self.assertEqual(len(runs), len(ids))
        sent = [json.loads(Path(c["env"]["OPENCODE_CONFIG"]).read_text())
                if Path(c["env"]["OPENCODE_CONFIG"]).exists() else None
                for c in calls_of(exe) if c["argv"][0] == "run"]
        self.assertEqual(len(sent), len(ids))       # one model call each: the stop
        for d in runs:
            m = runlog.load_meta(d)
            self.assertEqual(m.outcome, "verified")
            aid = budget.attempt_id(m.arm, m.task_id, m.repeat, m.attempt)
            seeds = [json.loads(x)["seed"] for x in (d / "calls.jsonl").read_text().splitlines()]
            self.assertEqual(seeds, plan.seeds(aid)[:1])
            tr = m.apparatus["transport"]
            self.assertEqual((tr["binary"], tr["pinned_by"]), (str(exe), spec["image"]))
            self.assertEqual(m.apparatus["model_server_found"]["model"], "probe-model")
            self.assertTrue(m.apparatus["prompt_hashes"])       # the learner's records are whole
            self.assertTrue((d / "transcript.jsonl.gz").is_file())
        self.assertNotIn("grader", tempfile.gettempdir())       # restored after the batch

    def test_the_census_drops_a_task_its_first_sample_closes(self):
        root, into = make_root(self.tmp / "census", tasks={"c1": TASK, "c2": TASK + "// FAILME\n"})
        exe = fake_opencode(self.tmp / "census")
        up = sealed.unsealed_part(root, "Q31", "probe", into)
        tasks = sealed.part_tasks(up)
        cen, par = sealed._par_ids(sorted(tasks), 1, 1, 1, True)
        text = sealed.par_plan_text(__import__("tomllib").loads(PAR_FRAGMENT), seed=31,
                                    tasks=tasks, rounds=1, repeats=1, attempts=1, lab="",
                                    lever_check=False, census=True)
        ids = cen + par
        spec = sealed._spec_base(root, "Q31", "par-run", up, app_of(root), found(), ids=ids,
                                 seed_pool=[1], calls=4, prereg="", stmts={}, plan_sha256="")
        spec.update(par={"seed": 31, "dropped": []}, unsealed=str(into))
        raw = sandbox.build_sealed(root, spec, archive=PAR_ARCHIVE)
        work = self.tmp / "census-work"
        work_from(root, raw, work, exe)
        pkg = self.tmp / "census-pkg" / "par_q31"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("")
        (pkg / "policy.py").write_text(PAR_POLICY)
        sys.path.insert(0, str(pkg.parent))
        (work / "plan.toml").write_text(text)
        res = sealed.inside(work, plan_path=work / "plan.toml")
        self.assertEqual(res["closed"], ["c1"])
        self.assertEqual(res["ran"], ["census/c1/1/1", "census/c2/1/1", "par/c2/1/1"])
        self.assertEqual(res["left"], [])


# --- the routes end to end, with a stand-in launch ---------------------------------------------

class Calendar:
    fh = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Routes(Base):
    def launch_learner(self, exe, per_chunk=None):
        """A stand-in for mksandbox-run --sealed-run: the manifest built and the batch run
        in-process on a /work made from it; `per_chunk` attempts at most per chunk."""
        chunks = []

        def launch(spec, recs, fd):
            raw = sandbox.build_sealed(self.root, spec)
            sandbox.validate(raw, self.root, check_image=False)
            work = self.tmp / f"work{len(chunks)}"
            work_from(self.root, raw, work, exe)
            ran = []
            clock = [0.0]

            def tick(aid):
                ran.append(aid)
                if per_chunk and len(ran) >= per_chunk:
                    clock[0] = 1e9
            res = sealed.inside(work, clock=lambda: clock[0], on_attempt=tick)
            chunks.append(res)
            shutil.copytree(work / "grader" / "runs", Path(recs) / "grader" / "runs")
            (Path(recs) / "run.json").write_text(json.dumps(
                {"gate": {"gate.log": "PROMPTS", "gate-counts.json": "{}"}, "ended_by": "done"}))
            return 0 if not res["left"] else 1
        return launch, chunks

    def test_the_learners_sealed_batch_runs_in_chunks_and_closes(self):
        exe = fake_opencode(self.tmp)
        launch, chunks = self.launch_learner(exe, per_chunk=1)
        code = sealed.run_sealed(self.root, "Q31", self.root / "research/plans/sealed.toml",
                                 "probe", self.into, launch=launch, app=app_of(self.root),
                                 found=found(), calendar=Calendar(), log=lambda m: None)
        self.assertEqual(code, 0)
        self.assertEqual([len(c["ran"]) for c in chunks], [1, 1])
        led = budget.Ledger(budget.ledger_path(self.root, "Q31"))
        att = led.attempts()
        self.assertEqual({a.state for a in att.values()}, {"scored"})
        self.assertEqual(len(att), 2)
        self.assertEqual(budget.last_anchor(self.root, "Q31")["event"], "close")
        note = led.notes("sealed-run")[-1]
        self.assertEqual((note["part"], note["stratum"]), ("probe", STRATUM))
        for a in att:
            rid = [r["run_id"] for r in led.read() if r.get("id") == a and r.get("run_id")][-1]
            self.assertTrue((self.root / "research/runs/Q31" / rid / "run.json").is_file())
        recs = sorted((self.root / "research/runs/Q31/sealed").iterdir())
        self.assertEqual(len(recs), 2)
        self.assertNotIn("PROMPTS", recs[0].read_text())
        self.assertTrue(report.build(self.root, "Q31").reproduced)

    def test_a_chunk_that_returns_nothing_leaves_the_batch_open_and_resume_refuses_it(self):
        def nothing(spec, recs, fd):
            return 1
        code = sealed.run_sealed(self.root, "Q31", self.root / "research/plans/sealed.toml",
                                 "probe", self.into, launch=nothing, app=app_of(self.root),
                                 found=found(), calendar=Calendar(), log=lambda m: None)
        self.assertEqual(code, 3)
        self.assertEqual(budget.last_anchor(self.root, "Q31")["event"], "open")
        with self.assertRaisesRegex(batch.BatchError, "sealed run"):
            batch.resume(self.root, "Q31", check_apparatus=False)
        exe = fake_opencode(self.tmp)
        launch, _ = self.launch_learner(exe)
        code = sealed.run_sealed(self.root, "Q31", self.root / "research/plans/sealed.toml",
                                 "probe", self.into, launch=launch, app=app_of(self.root),
                                 found=found(), calendar=Calendar(), log=lambda m: None)
        self.assertEqual(code, 0)                 # the same line continues the open batch

    def test_a_plan_beyond_its_part_or_with_an_agent_arm_is_refused(self):
        p = self.root / "research/plans/agent.toml"
        p.write_text(PLAN.replace('construct = "model"\npolicy = "q31_gate_bench.baselines:'
                                  'one_shot_render"', 'construct = "agent"'))
        with self.assertRaisesRegex(sealed.SealedRefused, "agent-mode arm"):
            sealed.run_sealed(self.root, "Q31", p, "probe", self.into, app=app_of(self.root),
                              found=found(), calendar=Calendar())
        p.write_text(PLAN.replace('name = "oneshot"', 'name = "par"'))
        with self.assertRaisesRegex(sealed.SealedRefused, "par's"):
            sealed.run_sealed(self.root, "Q31", p, "probe", self.into, app=app_of(self.root),
                              found=found(), calendar=Calendar())


def load_truthcheck():
    spec = importlib.util.spec_from_file_location("truthcheck_sealed_test",
                                                  ROOT / "sandbox" / "image" / "truthcheck.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def par_archive():
    files = {"labs/Q31/MANIFEST.sha256": b"", "labs/Q31/par/PLAN.toml": PAR_FRAGMENT.encode(),
             "labs/Q31/par/agent/par_q31/__init__.py": b"",
             "labs/Q31/par/agent/par_q31/policy.py": PAR_POLICY.encode()}
    return files


class ParRun(Base):
    def launch_par(self, exe, outs):
        def launch(spec, recs, fd):
            raw = sandbox.build_sealed(self.root, spec, archive=PAR_ARCHIVE)
            sandbox.validate(raw, self.root, check_image=False)
            work = self.tmp / f"parwork{len(outs)}"
            work_from(self.root, raw, work, exe)
            tc = load_truthcheck()
            tc.WORK, tc.PYTHON = str(work), sys.executable
            tc.CHILD_TMP, tc.PAR_TMP = str(self.tmp / "child"), str(self.tmp / "par")
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.object(tc, "unseal", lambda lab: (par_archive(), None)), \
                    contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = tc.entry(["par-run", "Q31", "probe"])
            outs.append((code, out.getvalue(), err.getvalue()))
            shutil.copytree(work / "grader" / "runs", Path(recs) / "grader" / "runs")
            (Path(recs) / "run.json").write_text(json.dumps(
                {"gate": {"gate-counts.json": "{}"}, "commands": [{"stdout": out.getvalue()}]}))
            return code
        return launch

    def test_par_runs_beside_the_learner_counts_only(self):
        exe = fake_opencode(self.tmp)
        outs = []
        code = sealed.run_par(self.root, "Q31", PAR_ARCHIVE, "probe", self.into,
                              self.root / "research/plans/sealed.toml",
                              launch=self.launch_par(exe, outs), app=app_of(self.root),
                              found=found(), calendar=Calendar(), log=lambda m: None)
        self.assertEqual(code, 0, outs)
        tc_code, out, err = outs[0]
        self.assertEqual((tc_code, err), (0, ""))
        verdict = json.loads(out)
        self.assertEqual({k: verdict[k] for k in ("mode", "runs", "solved", "left", "agreed")},
                         {"mode": "par-run", "runs": 2, "solved": 2, "left": 0, "agreed": True})
        self.assertNotIn(PAR_CANARY, out)
        # the runs: counts only (D103)
        dirs = sorted(d for d in (self.root / "research/runs/Q31").iterdir()
                      if d.name.startswith("par-probe-"))
        self.assertEqual(len(dirs), 2)
        self.assertNotIn(PAR_CANARY.encode(), all_bytes(self.root / "research"))
        for d in dirs:
            names = sorted(p.relative_to(d).as_posix().split("/")[0] for p in d.rglob("*")
                           if p.is_file())
            self.assertEqual(sorted(set(names)), ["inputs.sha256", "inputs.tar.gz", "returned",
                                                  "run.json"])
            meta = runlog.load_meta(d)
            self.assertEqual((meta.arm, meta.outcome), ("par", "verified"))
            self.assertNotIn("prompt_hashes", meta.apparatus)
            self.assertEqual(meta.apparatus["par"]["part"], "probe")
        plan = self.plan()
        # the ledger: par's calls reserved, then its counts
        led = budget.Ledger(budget.ledger_path(self.root, "Q31"))
        lines = led.par_lines("probe")
        self.assertEqual([r["event"] for r in lines], ["planned", "done"])
        self.assertEqual((lines[0]["calls"], lines[0]["runs"], lines[0]["beside"]),
                         (4, 2, "oneshot"))
        self.assertEqual((lines[1]["runs"], lines[1]["solved"]), (2, 2))
        self.assertEqual(led.used()[budget.QWEN], {"calls": 4, "runs": 2})
        self.assertTrue(report.build(self.root, "Q31").reproduced)
        self.assertEqual(plan.seed, lines[0]["seed"])
        with self.assertRaisesRegex(sealed.SealedRefused, "already"):
            sealed.run_par(self.root, "Q31", PAR_ARCHIVE, "probe", self.into,
                           self.root / "research/plans/sealed.toml", app=app_of(self.root),
                           found=found(), calendar=Calendar())

    def test_par_needs_its_pin_its_budget_and_one_arm_to_run_beside(self):
        with self.assertRaisesRegex(sealed.SealedRefused, "par agent"):
            sealed.run_par(self.root, "Q31", "Hidden/Agentic/Q31/other.tar.age", "probe",
                           self.into, self.root / "research/plans/sealed.toml",
                           app=app_of(self.root), found=found(), calendar=Calendar())
        two = self.root / "research/plans/two.toml"
        two.write_text(PLAN + PLAN[PLAN.index("[[arm]]"):].replace('"oneshot"', '"other"'))
        with self.assertRaisesRegex(sealed.SealedRefused, "--beside"):
            sealed.run_par(self.root, "Q31", PAR_ARCHIVE, "probe", self.into, two,
                           app=app_of(self.root), found=found(), calendar=Calendar())
        reg = self.root / "MODULES.toml"
        reg.write_text(REGISTRY.replace("qwen_calls = 40", "qwen_calls = 3"))
        with self.assertRaisesRegex(sealed.SealedRefused, "registry allows qwen_calls = 3"):
            sealed.run_par(self.root, "Q31", PAR_ARCHIVE, "probe", self.into,
                           self.root / "research/plans/sealed.toml", app=app_of(self.root),
                           found=found(), calendar=Calendar())


class StudySessionGuard(unittest.TestCase):
    """The new command lines name the unsealed part or the sealed archive: rule 1c refuses
    them in a study session."""

    def test_the_sealed_command_lines_are_refused(self):
        tmp = Path(tempfile.mkdtemp(prefix="dvl0-sealedguard-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        root, home = tmp / "study", tmp / "home"
        root.mkdir()
        gen = ROOT / "scripts" / "gen_hook_fixtures.py"
        sid = "11111111-2222-4333-8444-555555555558"
        slug = "".join(c if c.isascii() and c.isalnum() else "-" for c in str(root))
        subprocess.run([sys.executable, str(gen), "--fake-root", str(root)], check=True,
                       capture_output=True)
        subprocess.run([sys.executable, str(gen), "--fake-home", str(home), f"--slug={slug}",
                        f"--sid={sid}"], check=True, capture_output=True)
        for cmd in ("uv run --offline --frozen --directory harness python -m fvh run Q31 --plan "
                    "research/q31-plan.toml --sealed heldout --unsealed ~/x/heldout",
                    "python3 -m fvh par Q31 --truth Hidden/Agentic/Q31/par-agent.tar.age "
                    "--sealed heldout --unsealed ~/x/heldout --plan research/q31-plan.toml",
                    "scripts/mksandbox-run --truth Hidden/Agentic/Q31/par-agent.tar.age "
                    "--truth-check par-run --par /tmp/spec.json --records /tmp/r"):
            inp = {"session_id": sid,
                   "transcript_path": f"{home}/.claude/projects/{slug}/{sid}.jsonl",
                   "tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": str(root)}
            env = {k: v for k, v in os.environ.items()
                   if k not in ("CLAUDE_CODE_SESSION_ID", "CLAUDE_CONFIG_DIR", "TMPDIR",
                                "SPOILER_GUARD_NO_JQ")}
            env.update(HOME=str(home), CLAUDE_PROJECT_DIR=str(root))
            p = subprocess.run(["bash", str(ROOT / ".claude" / "hooks" / "spoiler-guard.sh")],
                               input=json.dumps(inp), capture_output=True, text=True, env=env,
                               timeout=60)
            self.assertEqual(p.returncode, 2, f"{cmd}: {p.stdout} {p.stderr}")
            self.assertIn("rule 1c", p.stderr, cmd)


if __name__ == "__main__":
    unittest.main()
