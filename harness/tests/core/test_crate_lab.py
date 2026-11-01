"""The frozen core's own tests: Lab 3's pieces (QPLAN §28.5, §28.6, §30 Q64; the DV5c
gaps lane): fvh.statements (the statements pin and the unseal of a sealed stratum),
crate tasks in fvh.batch (a crate's sources editable, its companions read-only and
staged with every verification), and the gated arm (acceptance = "gate": Lab 3's arm G,
whose run ends only when the plan's gate passes the work copy; on a Verus crate or, Δ421, a
one-file Dafny task's root file). On throwaway git roots
holding an invented module Q98, invented crates and an invented gate; the transports are
scripted fakes, the verification runner an isolated fake and the age binary a fake that
passes a plain tar through, so no model, no container and no key is used. One test reads
the course's own expected/Q18.statements and the shipped statement files it pins."""

import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import uuid
from pathlib import Path

import pytest

from fvh import apparatus, backends, batch, budget, executor, protocol, report, runlog, statements, tools
from fvh.tools import runners as R

COURSE = Path(__file__).resolve().parents[3]
GOOD_RS = "// good\nfn lab_smoke_ok() {}\n"
STUB_RS = "// stub\nfn lab_smoke_ok() { unimplemented!() }\n"
CARGO = '[package]\nname = "lab_smoke_c1"\nversion = "0.1.0"\n'
FROZEN = "// frozen statements\n"
CRATE = "bench/local/q/lab9/{t}/tasks"
REGISTRY = """[[module]]
id = "Q98"
status = "authoring"
agentic = []
budget = { claude_calls = 30, claude_runs = 10, qwen_calls = 100, qwen_runs = 20, gpu_hours = 1 }
"""
APP = """schema = 1
[defaults]
calls = 40
turns = 40
wall_s = 2700
gpu_s = 3600
[window]
allowed_overage = ["rejected"]
five_hour_max = 0.8
seven_day_max = 0.6
[backend.claude]
version = "0.0.0-fake"
binary = "~/no/claude"
sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
model = "fake-model"
effort = "low"
max_turns = 2
"""
ARMS_SRC = '''
class StopFirst:
    """Asks to stop first, then edits the target from one model call and verifies."""

    def __init__(self, ask, seeds):
        self.ask, self.seeds = ask, list(seeds)

    def propose(self, state, ctx, budget):
        from fvh import protocol as P
        if state.step == 0:
            return [P.Stop("done", "early")]
        if state.step == 1:
            text = self.ask(f"target={ctx.target} round", self.seeds[0])
            return [P.Edit(ctx.target, "", text), P.Verify("gate")]
        return [P.Stop("done", "")]
'''
GATE_SRC = '''
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Pins:
    min_verified: int
    symbols: tuple


@dataclass(frozen=True)
class CrateTarget:
    id: str
    lang: str
    target: str
    files: tuple
    pins: Pins


@dataclass(frozen=True)
class Verdict:
    word: str
    unknown: tuple
    reasons: tuple


@dataclass(frozen=True)
class Result:
    id: str
    verdict: Verdict


def render(v):
    return v.word if v.word != "PASS" else "PASS · UNKNOWN: X07"


SEEN = []          # (lang, target, files) of every target the gate ran on


def gate_crate(target, *, run=None):
    SEEN.append((target.lang, target.target, target.files))
    g = run("vcheck --gate", target.target)
    a = run("vaudit", target.target)
    files_ok = all(Path(f).is_file() for f in target.files)
    ok = (g.document.get("verdict") == "verified" and a.exit_code == 0 and files_ok
          and g.document.get("verified_count", 0) >= target.pins.min_verified)
    return Result(target.id, Verdict("PASS" if ok else "FAIL", ("X07",) if ok else (),
                                     () if ok else ("vcheck --gate: not a complete pass",)))
'''


class CrateGate(R.Runner):
    """An isolated fake verification runner over a crate directory: a crate whose
    src/lib.rs is GOOD_RS, with its Cargo.toml and frozen.rs beside it, verifies."""

    name = "replay"
    isolated = True
    seen = []

    def execute(self, instrument, target, *, timeout_s=None):
        t = Path(target)
        lib = (t / "src" / "lib.rs").read_text() if (t / "src" / "lib.rs").is_file() else ""
        ok = lib == GOOD_RS and (t / "Cargo.toml").read_text() == CARGO \
            and (t / "frozen.rs").read_text() == FROZEN
        CrateGate.seen.append((instrument, ok))
        doc = {"verdict": "verified" if ok else "failed", "holes": [],
               "verified_count": 1 if ok else 0, "exit_code": 0 if ok else 1, "stage": "verify",
               "diagnostics": [] if ok else [{"severity": "error", "line": 1}]}
        return tools.ToolResult(instrument, str(target), doc, 0 if ok else 1, None, "replay",
                                "agent", hashlib.sha256(lib.encode()).hexdigest())


GOOD_DFY = "// good\nlemma Good() ensures true {}\n"
STUB_DFY = "// stub\nlemma Good() ensures true\n"
DFY = "bench/local/q/lab9/{t}/tasks/{t}.dfy"


class EitherGate(CrateGate):
    """CrateGate, and over a one-file Dafny task: the file verifies when it is GOOD_DFY."""

    def execute(self, instrument, target, *, timeout_s=None):
        t = Path(target)
        if t.is_dir():
            return super().execute(instrument, target, timeout_s=timeout_s)
        text = t.read_text() if t.is_file() else ""
        ok = t.suffix == ".dfy" and text == GOOD_DFY
        CrateGate.seen.append((instrument, ok))
        doc = {"verdict": "verified" if ok else "failed", "holes": [],
               "verified_count": 1 if ok else 0, "exit_code": 0 if ok else 1, "stage": "verify",
               "diagnostics": [] if ok else [{"severity": "error", "line": 1}]}
        return tools.ToolResult(instrument, str(target), doc, 0 if ok else 1, None, "replay",
                                "agent", hashlib.sha256(text.encode()).hexdigest())


class Fake:
    """A scripted Claude-family transport: each call's reply is one edit of the target."""

    def __init__(self, replies):
        self.replies = list(replies)

    def complete(self, message, *, system="", seed=None):
        r = self.replies.pop(0) if self.replies else GOOD_RS
        target = message.split("target=", 1)[1].split()[0]
        obj = {"actions": [{"type": "edit", "path": target, "old": "", "new": r}]}
        return backends.Completion(text="", structured=obj,
                                   usage={"input_tokens": 3, "output_tokens": 2}, turns=1,
                                   rate_limit=None, window=("ok", ""),
                                   apparatus={"family": "claude"}, raw=json.dumps(obj) + "\n")


def git(root, *args, check=True):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@example.invalid", GIT_CONFIG_GLOBAL=os.devnull)
    return subprocess.run(["git", "-C", str(root), *args], check=check, env=env,
                          capture_output=True, text=True).stdout.strip()


def sha(b):
    return hashlib.sha256(b).hexdigest()


class Root(type(Path())):
    pass


@pytest.fixture
def root(tmp_path, monkeypatch):
    r = Root(tmp_path / "course")
    r.mkdir()
    git(r, "init", "-q")
    (r / "MODULES.toml").write_text(REGISTRY)
    (r / "research").mkdir()
    (r / "research" / "q98_statements.dfy").write_text("// shipped form\n")
    (r / "expected").mkdir()
    (r / "expected" / "Q98.statements").write_text(
        "# pin\n" + f"{sha(b'// shipped form' + bytes([10]))}  research/q98_statements.dfy\n")
    mod = f"fvhtest_arms_{uuid.uuid4().hex[:8]}"
    gmod = f"fvhtest_gate_{uuid.uuid4().hex[:8]}"
    (r / "harness" / "q").mkdir(parents=True)
    (r / "harness" / "q" / f"{mod}.py").write_text(ARMS_SRC)
    (r / "harness" / "q" / f"{gmod}.py").write_text(GATE_SRC)
    (r / "app.toml").write_text(APP)
    git(r, "add", ".")
    git(r, "commit", "-qm", "course")
    monkeypatch.setenv(apparatus.ENV, str(r / "app.toml"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "run"))
    (tmp_path / "run").mkdir()
    r.mod, r.gmod = mod, gmod
    CrateGate.seen = []
    return r


def put_crate(root, t="c1"):
    d = root / CRATE.format(t=t)
    (d / "src").mkdir(parents=True)
    (d / "Cargo.toml").write_text(CARGO)
    (d / "frozen.rs").write_text(FROZEN)
    (d / "src" / "lib.rs").write_text(STUB_RS)
    return d


def commit_statements(root, text="// my statements\n"):
    (root / "research" / "q98_statements.dfy").write_text(text)
    git(root, "add", "research")
    git(root, "commit", "-qm", "statements")


def write_plan(root, *, arms, tasks=("c1",), extra="", lab="", paths=None):
    lines = [f'lab = "{lab}"' if lab else "", "seed = 91", f"tasks = {json.dumps(list(tasks))}",
             'system = "sys"', 'instructions = "edit"', extra]
    for t in tasks:
        lines += [f"[task.{t}]", f'path = "{(paths or {}).get(t) or CRATE.format(t=t)}"']
    for name, acceptance in arms:
        lines += ["[[arm]]", f'name = "{name}"', 'family = "claude"', "rounds = 2",
                  f'policy = "{root.mod}:StopFirst"', 'construct = "seeded"',
                  f'acceptance = "{acceptance}"']
    p = root / "plan.toml"
    p.write_text("\n".join(lines) + "\n")
    return p


def make(root, plan_path, replies=(GOOD_RS,)):
    plan = batch.load_plan(plan_path, root)
    b = batch.Batch(root, "Q98", plan, transports=lambda *a: Fake(list(replies)),
                    runners=lambda task, lang: CrateGate(), log=lambda m: None,
                    app=apparatus.load(root / "app.toml"))
    b._window_ok = lambda ids: True                # the window check is test_batch.py's
    return b


def runs(root):
    out = {}
    for p in sorted((root / "research" / "runs" / "Q98").glob("*/run.json")):
        m = runlog.load_meta(p.parent)
        out[m.arm] = (m, p.parent)
    return out


# --- the statements pin --------------------------------------------------------------

def test_check_refuses_until_the_statements_are_committed_and_changed(root):
    with pytest.raises(statements.StatementsRefused, match="still the shipped form"):
        statements.check(root, "Q98")
    (root / "research" / "q98_statements.dfy").write_text("// mine\n")
    with pytest.raises(statements.StatementsRefused, match="not committed"):
        statements.check(root, "Q98")
    commit_statements(root, "// mine\n")
    got = statements.check(root, "Q98")
    assert got == {"research/q98_statements.dfy": sha(b"// mine\n")}
    with pytest.raises(statements.StatementsRefused, match="no statements pin"):
        statements.check(root, "Q97")


def test_an_untracked_statement_file_is_refused(root):
    git(root, "rm", "-q", "--cached", "research/q98_statements.dfy")
    git(root, "commit", "-qm", "untrack")
    (root / "research" / "q98_statements.dfy").write_text("// mine\n")
    with pytest.raises(statements.StatementsRefused, match="not tracked"):
        statements.check(root, "Q98")


def _seal(root, cards, *, extra=None, man_files=None):
    """A fake sealed stratum: the 'archive' is a plain tar the fake age passes through."""
    files = {}
    for c in cards:
        files[f"{c}/tasks/Cargo.toml"] = CARGO.encode()
        files[f"{c}/tasks/frozen.rs"] = FROZEN.encode()
        files[f"{c}/tasks/src/lib.rs"] = STUB_RS.encode()
    files.update(extra or {})
    listed = man_files if man_files is not None else files
    man = "".join(f"{sha(v)}  {k}\n" for k, v in sorted(listed.items())).encode()
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        for name, data in sorted({**files, "MANIFEST.sha256": man}.items()):
            ti = tarfile.TarInfo(f"labs/Q98/{name}")
            ti.size = len(data)
            tf.addfile(ti, io.BytesIO(data))
    d = root / "bench" / "local" / "q" / "lab9"
    d.mkdir(parents=True, exist_ok=True)
    arc = d / "tasks.tar.age"
    arc.write_bytes(buf.getvalue())
    cards_toml = "".join(f'\n[[card]]\nid = "{c}"\nlang = "verus"\nkind = "possible"\n'
                         for c in cards)
    (d / "STRATUM.toml").write_text(
        f'schema = 1\nlab = "Q98"\nmodule = "Q98"\narchive = "bench/local/q/lab9/tasks.tar.age"\n'
        f'archive_sha256 = "{sha(arc.read_bytes())}"\nrecipient = "age1fake"\n'
        f"files = {len(listed)}\nmanifest_sha256 = \"{sha(man)}\"\n" + cards_toml)
    fake = root.parent / "fake-age"
    fake.write_text(f"#!{sys.executable}\nimport sys\nsys.stdout.buffer.write(open(sys.argv[-1], "
                    "'rb').read())\n")
    fake.chmod(0o755)
    key = root.parent / "key.txt"
    key.write_text("AGE-SECRET-KEY-FAKE\n")
    return (str(fake), sha(fake.read_bytes())), str(key)


def test_unseal_writes_the_cards_only_after_the_check(root):
    age, key = _seal(root, ["c1", "c2"])
    with pytest.raises(statements.StatementsRefused, match="shipped form"):
        statements.unseal(root, "Q98", age=age, identity=key)
    assert not (root / CRATE.format(t="c1")).exists()
    commit_statements(root)
    got = statements.unseal(root, "Q98", age=age, identity=key, dry_run=True)
    assert got["strata"][0]["written"] == 6 and not (root / CRATE.format(t="c1")).exists()
    got = statements.unseal(root, "Q98", age=age, identity=key)
    assert got["strata"][0]["written"] == 6
    assert (root / CRATE.format(t="c2") / "src" / "lib.rs").read_text() == STUB_RS
    rec = (root / "bench" / "local" / "q" / "lab9" / "UNSEALED.toml").read_text()
    assert sha(b"// my statements\n") in rec
    again = statements.unseal(root, "Q98", age=age, identity=key)
    assert again["strata"][0]["written"] == 0 and again["strata"][0]["kept"] == 6
    (root / CRATE.format(t="c1") / "src" / "lib.rs").write_text("// my delivery\n")
    with pytest.raises(statements.StatementsRefused, match="nothing is overwritten"):
        statements.unseal(root, "Q98", age=age, identity=key)


def test_unseal_refuses_an_archive_that_is_not_its_pin(root):
    commit_statements(root)
    age, key = _seal(root, ["c1"])
    arc = root / "bench" / "local" / "q" / "lab9" / "tasks.tar.age"
    arc.write_bytes(arc.read_bytes() + b"\0")
    with pytest.raises(statements.StatementsRefused, match="archive_sha256"):
        statements.unseal(root, "Q98", age=age, identity=key)
    age, key = _seal(root, ["c1"], extra={"stray.txt": b"x"})
    with pytest.raises(statements.StatementsRefused, match="not a listed card"):
        statements.unseal(root, "Q98", age=age, identity=key)
    age, key = _seal(root, ["c1"], man_files={})
    with pytest.raises(statements.StatementsRefused, match="differ from its manifest"):
        statements.unseal(root, "Q98", age=age, identity=key)
    age, key = _seal(root, ["c1"])
    with pytest.raises(statements.StatementsRefused, match="not the pinned age"):
        statements.unseal(root, "Q98", age=(age[0], "0" * 64), identity=key)
    assert not (root / CRATE.format(t="c1")).exists()


def _seal_public(root, cards):
    """A fake sealed stratum of one-file Dafny cards: (id, task or None, role, spare_order)."""
    files = {}
    for cid, task, role, order in cards:
        src = f"// Source: dafnybench {task} (Apache-2.0); unchanged.\n" if task else ""
        files[f"{cid}/tasks/{cid}.dfy"] = (f"// task {cid}\n{src}lemma L() {{}}\n").encode()
    man = "".join(f"{sha(v)}  {k}\n" for k, v in sorted(files.items())).encode()
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        for name, data in sorted({**files, "MANIFEST.sha256": man}.items()):
            ti = tarfile.TarInfo(f"labs/Q98/{name}")
            ti.size = len(data)
            tf.addfile(ti, io.BytesIO(data))
    d = root / "bench" / "local" / "q" / "lab9"
    d.mkdir(parents=True, exist_ok=True)
    arc = d / "tasks.tar.age"
    arc.write_bytes(buf.getvalue())
    toml = ""
    for cid, task, role, order in cards:
        toml += f'\n[[card]]\nid = "{cid}"\nlang = "dafny"\n'
        toml += (f'source = "public"\nrole = "{role}"\n' + (f"spare_order = {order}\n" if order else "")
                 if task else 'source = "course-local"\n')
    (d / "STRATUM.toml").write_text(
        f'schema = 1\nlab = "Q98"\nmodule = "Q98"\narchive = "bench/local/q/lab9/tasks.tar.age"\n'
        f'archive_sha256 = "{sha(arc.read_bytes())}"\nrecipient = "age1fake"\n'
        f'files = {len(files)}\nmanifest_sha256 = "{sha(man)}"\n' + toml)
    fake = root.parent / "fake-age"
    fake.write_text(f"#!{sys.executable}\nimport sys\nsys.stdout.buffer.write(open(sys.argv[-1], "
                    "'rb').read())\n")
    fake.chmod(0o755)
    key = root.parent / "key.txt"
    key.write_text("AGE-SECRET-KEY-FAKE\n")
    return (str(fake), sha(fake.read_bytes())), str(key)


PUBLIC = [("cl-d1-x", None, None, None), ("pd-d1-x", "A1.dfy", "card", None),
          ("pd-d2-x", "B.dfy", "card", None), ("pd-d3-x", "S.dfy", "spare", 1),
          ("pd-d4-x", "T.dfy", "spare", 2)]


def _written(root):
    d = root / "bench" / "local" / "q" / "lab9"
    return sorted(p.parent.parent.name for p in d.glob("*/tasks/*.dfy"))


def test_unseal_writes_public_cards_and_no_spare(root):
    commit_statements(root)
    age, key = _seal_public(root, PUBLIC)
    got = statements.unseal(root, "Q98", age=age, identity=key)
    assert _written(root) == ["cl-d1-x", "pd-d1-x", "pd-d2-x"]
    assert "public_replaced" not in got["strata"][0]


def test_unseal_replaces_a_card_the_learner_met_with_the_next_free_spare(root):
    commit_statements(root)
    lab1 = root / "bench" / "local" / "q" / "lab1"
    lab1.mkdir(parents=True)
    # B.dfy was in the learner's Lab 1; so was the first spare: the second one replaces it
    (lab1 / "STRATUM.toml").write_text('task = "bench/public/dafnybench/tasks/B.dfy"\nalso = "S.dfy"\n')
    age, key = _seal_public(root, PUBLIC)
    got = statements.unseal(root, "Q98", age=age, identity=key)
    assert _written(root) == ["cl-d1-x", "pd-d1-x", "pd-d4-x"]
    assert got["strata"][0]["public_replaced"] == [["pd-d2-x", "pd-d4-x"]]
    assert statements.learner_seen(root) >= {"B.dfy", "S.dfy"}


def test_the_pools_count_as_met_only_through_their_draw_records(root):
    pools = root / "bench" / "public"
    pools.mkdir(parents=True)
    (pools / "POOLS.toml").write_text('[[pool]]\nset = "dafnybench"\ntasks = ["A1.dfy", "B.dfy"]\n\n'
                                      '[[draw]]\nlab = "Q12"\ndrawn = ["B.dfy"]\n')
    assert statements.learner_seen(root) == {"B.dfy"}


def test_unseal_refuses_a_part_whose_spares_run_out(root):
    commit_statements(root)
    alpha = root / "bench" / "local" / "r" / "labalpha"
    alpha.mkdir(parents=True)
    (alpha / "STRATUM.toml").write_text('a = "A1.dfy"\nb = "B.dfy"\nc = "T.dfy"\n')
    age, key = _seal_public(root, PUBLIC)
    with pytest.raises(statements.StatementsRefused, match="spares have run out"):
        statements.unseal(root, "Q98", age=age, identity=key)
    assert _written(root) == []


def test_the_course_pins_the_shipped_statement_files():
    """expected/Q18.statements names Lab 3's statement files with the sha256 of their
    shipped form: the blob of the commit that added each file, or the working copy
    while it is not committed yet (the authoring tree)."""
    pins = statements.read_pins(COURSE, "Q18")
    assert sorted(p for p, _ in pins) == ["research/q18_statements.dfy",
                                         "research/q18_statements.rs"]
    for rel, want in pins:
        first = git(COURSE, "log", "--diff-filter=A", "--format=%H", "--", rel, check=False)
        if first:
            blob = subprocess.run(["git", "-C", str(COURSE), "show",
                                   f"{first.splitlines()[-1]}:{rel}"], capture_output=True).stdout
        else:
            blob = (COURSE / rel).read_bytes()
        assert sha(blob) == want, rel


# --- crate tasks and the gated arm ----------------------------------------------------

def test_a_crate_task_stages_its_companions_read_only(root):
    put_crate(root)
    git(root, "add", ".")
    git(root, "commit", "-qm", "crate")
    plan = batch.load_plan(write_plan(root, arms=[("p", "verify")]), root)
    assert plan.is_crate(root, "c1")
    ed, co = batch.crate_files(root, CRATE.format(t="c1"))
    assert ed == (f"{CRATE.format(t='c1')}/src/lib.rs",)
    assert sorted(co) == [f"{CRATE.format(t='c1')}/Cargo.toml",
                          f"{CRATE.format(t='c1')}/frozen.rs"]
    (root / "bench/local/q/lab9/c9/tasks").mkdir(parents=True)
    (root / "bench/local/q/lab9/c9/tasks/README").write_text("x")
    p = write_plan(root, arms=[("p", "verify")], tasks=("c9",))
    p.write_text(p.read_text().replace("c9/tasks", "c9/tasks"))
    with pytest.raises(batch.BatchError, match="Cargo.toml and src/lib.rs"):
        batch.load_plan(p, root)


def test_gated_and_prompt_only_arms_on_a_crate(root):
    put_crate(root)
    git(root, "add", ".")
    git(root, "commit", "-qm", "crate")
    gate = f"harness/q/{root.gmod}.py"
    extra = f'gate = "{gate}"\ngate_sha256 = "{sha((root / gate).read_bytes())}"'
    b = make(root, write_plan(root, arms=[("G", "gate"), ("P", "verify")], extra=extra))
    b.open()
    assert b.run() == 0
    got = runs(root)
    mg, dg = got["G"]
    mp, dp = got["P"]
    # arm G: the early Stop is refused, the gate passes the edited crate, the run ends there
    assert (mg.outcome, mg.ended_by) == ("verified", "gate-pass")
    obs = [json.loads(x) for x in (dg / "observations.jsonl").read_text().splitlines()]
    assert obs[0]["observations"][0]["kind"] == "refused"
    acc = [o["verdict"]["acceptance"] for r in obs for o in r["observations"]
           if o["kind"] == "verify"]
    assert acc and acc[-1]["passed"] and acc[-1]["verdict"].startswith("PASS")
    assert mg.apparatus["acceptance"] == "gate" and mg.apparatus["gate_sha256"] == \
        sha((root / gate).read_bytes())
    # arm P: the early Stop ends the run; the final verification of the stub fails
    assert (mp.outcome, mp.ended_by) == ("failed", "stop")
    # the companions reached every verification; only the source was returned
    assert ("vaudit", True) in CrateGate.seen
    ret = sorted(p.relative_to(dg / "returned").as_posix()
                 for p in (dg / "returned").rglob("*") if p.is_file())
    assert ret == [f"{CRATE.format(t='c1')}/src/lib.rs"]
    staged = runlog.read_inputs(dg)
    assert len(staged) == 3
    # fvh report re-derives both outcomes from the logs
    for m, d in (got["G"], got["P"]):
        chk = report.rederive(d, m)
        assert chk.ok, chk


def test_a_gate_that_is_not_the_pre_registered_one_refuses(root):
    put_crate(root)
    gate = f"harness/q/{root.gmod}.py"
    git(root, "add", ".")
    git(root, "commit", "-qm", "crate")
    p = write_plan(root, arms=[("G", "gate")], extra=f'gate = "{gate}"\ngate_sha256 = "{"0" * 64}"')
    with pytest.raises(batch.BatchError, match="not the pre-registered one"):
        make(root, p).open()
    with pytest.raises(batch.BatchError, match="gate names the acceptance tool"):
        batch.load_plan(write_plan(root, arms=[("G", "gate")]), root)


# --- a challenge's gated arm on the learner's committed agents/ gate (Q32's, Q33's) ---------

Q31_GATE = "agents/q31_gate_bench/gate.py"
CHALLENGE_REGISTRY = """
[[module]]
id = "Q32"
status = "authoring"
agentic = []
budget = { claude_calls = 30, claude_runs = 10, qwen_calls = 100, qwen_runs = 20, gpu_hours = 1 }

[[module]]
id = "Q31"
status = "authoring"
agentic = []
budget = { claude_calls = 30, claude_runs = 10, qwen_calls = 100, qwen_runs = 20, gpu_hours = 1 }
"""


@pytest.fixture
def agents_root(root, monkeypatch):
    """The root with Q31 and Q32 records, the learner's Q31 gate (the fake crate gate) at
    its real course path and a learner fvh_q package, all committed; the real
    q31_gate_bench (pytest's ../agents path) is kept out of sys.modules meanwhile."""
    monkeypatch.setattr(sys, "path", list(sys.path))
    for name in [m for m in sys.modules if m == "q31_gate_bench" or m.startswith("q31_gate_bench.")]:
        monkeypatch.delitem(sys.modules, name)
    with open(root / "MODULES.toml", "a") as fh:
        fh.write(CHALLENGE_REGISTRY)
    g = root / Q31_GATE
    g.parent.mkdir(parents=True)
    (g.parent / "__init__.py").write_text("")
    g.write_text(GATE_SRC)
    (root / "harness" / "q" / "fvh_q").mkdir()
    (root / "harness" / "q" / "fvh_q" / "__init__.py").write_text("")
    put_crate(root)
    git(root, "add", ".")
    git(root, "commit", "-qm", "the learner's Q31 gate")
    yield root
    for name in [m for m in sys.modules if m == "q31_gate_bench" or m.startswith("q31_gate_bench.")]:
        del sys.modules[name]


def gate_line(root, rel=Q31_GATE, digest=None):
    return f'gate = "{rel}"\ngate_sha256 = "{digest or sha((root / rel).read_bytes())}"'


class FakeEither(Fake):
    """Fake, replying GOOD_DFY for a .dfy target and GOOD_RS otherwise."""

    def complete(self, message, *, system="", seed=None):
        target = message.split("target=", 1)[1].split()[0]
        self.replies = [GOOD_DFY if target.endswith(".dfy") else GOOD_RS]
        return super().complete(message, system=system, seed=seed)


def make_for(root, plan_path, module):
    plan = batch.load_plan(plan_path, root)
    b = batch.Batch(root, module, plan, transports=lambda *a: FakeEither([]),
                    runners=lambda task, lang: EitherGate(), log=lambda m: None,
                    app=apparatus.load(root / "app.toml"))
    b._window_ok = lambda ids: True
    return b


def test_q32s_gated_arm_accepts_through_the_learners_committed_q31_gate(agents_root):
    root = agents_root
    plan = batch.load_plan(write_plan(root, arms=[("G", "gate")], extra=gate_line(root)), root)
    assert plan.gate == Q31_GATE
    b = make_for(root, write_plan(root, arms=[("G", "gate")], extra=gate_line(root)), "Q32")
    b.open()
    assert b._gate_mod.__file__ == str(root / Q31_GATE)
    assert b.run() == 0
    (m, d), = [(m, d) for p in sorted((root / "research/runs/Q32").glob("*/run.json"))
               for m, d in [(runlog.load_meta(p.parent), p.parent)]]
    assert (m.outcome, m.ended_by) == ("verified", "gate-pass")
    assert m.apparatus["gate"] == Q31_GATE
    assert m.apparatus["gate_sha256"] == sha((root / Q31_GATE).read_bytes())


def test_q32s_gated_arm_runs_a_one_file_dafny_task_and_a_verus_crate(agents_root):
    """QPLAN §34.1: every Q32 candidate goes through the learner's Q31 gate, and Q32's
    tasks are half Dafny (§34.4): the gate's target is the work copy's root .dfy file
    (lang "dafny") for a one-file Dafny task, the crate (lang "verus") for a crate task
    (Δ421)."""
    root = agents_root
    d = root / DFY.format(t="d1")
    d.parent.mkdir(parents=True)
    d.write_text(STUB_DFY)
    git(root, "add", ".")
    git(root, "commit", "-qm", "a Dafny task")
    p = write_plan(root, arms=[("G", "gate")], tasks=("d1", "c1"), extra=gate_line(root),
                   paths={"d1": DFY.format(t="d1")})
    plan = batch.load_plan(p, root)
    assert plan.tasks["d1"] == (DFY.format(t="d1"), "dafny")
    assert plan.tasks["c1"] == (CRATE.format(t="c1"), "verus")
    b = make_for(root, p, "Q32")
    b.open()
    gate_mod = b._gate_mod
    gate_mod.SEEN.clear()
    assert b.run() == 0
    got = {}
    for f in sorted((root / "research/runs/Q32").glob("*/run.json")):
        m = runlog.load_meta(f.parent)
        got[m.task_id] = (m, f.parent)
    assert sorted(got) == ["c1", "d1"]
    for t, lang in (("d1", "dafny"), ("c1", "verus")):
        m, rd = got[t]
        assert (m.outcome, m.ended_by, m.lang) == ("verified", "gate-pass", lang), t
        assert m.apparatus["gate"] == Q31_GATE and m.apparatus["acceptance"] == "gate"
        assert report.rederive(rd, m).ok
    assert "crate" not in got["d1"][0].apparatus and got["c1"][0].apparatus["crate"]
    seen = {lang: (tgt, files) for lang, tgt, files in gate_mod.SEEN}
    tgt, files = seen["dafny"]
    assert tgt.endswith("/" + DFY.format(t="d1")) and files == (tgt,)
    assert Path(seen["verus"][0]).name == "tasks"
    ret = sorted(x.relative_to(got["d1"][1] / "returned").as_posix()
                 for x in (got["d1"][1] / "returned").rglob("*") if x.is_file())
    assert ret == [DFY.format(t="d1")]


def test_a_gated_arm_refuses_a_one_file_verus_task(agents_root):
    """The instruments take a Verus crate, not a one-file Verus task (fvh.tools.command's
    specfreeze and reach rows), so a gated plan refuses one at load (Δ421)."""
    root = agents_root
    rs = root / "bench/local/q/lab9/v1/tasks/v1.rs"
    rs.parent.mkdir(parents=True)
    rs.write_text(STUB_RS)
    p = write_plan(root, arms=[("G", "gate")], tasks=("v1",), extra=gate_line(root),
                   paths={"v1": "bench/local/q/lab9/v1/tasks/v1.rs"})
    with pytest.raises(batch.BatchError, match="task.s. v1 are one-file Verus tasks"):
        batch.load_plan(p, root)
    p = write_plan(root, arms=[("P", "verify")], tasks=("v1",),
                   paths={"v1": "bench/local/q/lab9/v1/tasks/v1.rs"})
    assert batch.load_plan(p, root).tasks["v1"][1] == "verus"     # an ungated arm runs it


def test_an_agents_gate_serves_the_plans_of_the_modules_that_use_it_only(agents_root):
    root = agents_root
    assert batch.agent_gate_users(Q31_GATE) == ("Q32", "Q33")
    for module in ("Q31", "Q98"):
        with pytest.raises(batch.BatchError, match="Q32 and Q33's plans only"):
            make_for(root, write_plan(root, arms=[("G", "gate")], extra=gate_line(root)),
                     module).open()
    # another agents/ file is no gate a plan may name, even of the topic
    other = root / "agents" / "q32_proof_search" / "gate.py"
    other.parent.mkdir(parents=True)
    other.write_text(GATE_SRC)
    with pytest.raises(batch.BatchError, match="gate names the acceptance tool"):
        batch.load_plan(write_plan(root, arms=[("G", "gate")],
                                   extra=gate_line(root, "agents/q32_proof_search/gate.py")), root)


def test_an_agents_gate_is_read_as_committed_as_the_graded_role_reads_it(agents_root):
    root = agents_root
    g = root / Q31_GATE
    # a changed gate, pre-registered at its working copy's sha256: commit it first
    g.write_text(GATE_SRC + "\n# mine, not committed\n")
    with pytest.raises(batch.BatchError, match="commit it first"):
        make_for(root, write_plan(root, arms=[("G", "gate")], extra=gate_line(root)), "Q32").open()
    git(root, "commit", "-qam", "gate v3, committed")
    make_for(root, write_plan(root, arms=[("G", "gate")], extra=gate_line(root)), "Q32").open()
    # an untracked file beside the learner's gate v2 refuses as well (the gate composes it)
    (root / "harness" / "q" / "fvh_q" / "extra.py").write_text("X = 1\n")
    with pytest.raises(batch.BatchError, match="first: harness/q/fvh_q/extra.py"):
        batch.check_agent_gate(root, "Q32", Q31_GATE, sha(g.read_bytes()))
    (root / "harness" / "q" / "fvh_q" / "extra.py").unlink()
    # bytecode caches are no frozen work (graded_ok skips them too)
    (g.parent / "__pycache__").mkdir(exist_ok=True)
    (g.parent / "__pycache__" / "gate.cpython-312.pyc").write_bytes(b"\0")
    assert batch.check_agent_gate(root, "Q32", Q31_GATE, sha(g.read_bytes())) == sha(g.read_bytes())
    # the committed blob must be the pre-registered one
    with pytest.raises(batch.BatchError, match="not the pre-registered one"):
        batch.check_agent_gate(root, "Q32", Q31_GATE, "0" * 64)


def test_a_gate_ignored_by_git_or_outside_a_checkout_is_not_committed(agents_root, tmp_path):
    root = agents_root
    (root / ".gitignore").write_text("agents/q31_gate_bench/gate.py\n")
    git(root, "add", ".gitignore")
    git(root, "rm", "-q", "--cached", Q31_GATE)
    git(root, "commit", "-qm", "ignore the gate")
    with pytest.raises(batch.BatchError, match="is not committed"):
        batch.check_agent_gate(root, "Q32", Q31_GATE)
    bare = tmp_path / "bare"
    (bare / "agents" / "q31_gate_bench").mkdir(parents=True)
    with pytest.raises(batch.BatchError, match="at a commit"):
        batch.check_agent_gate(bare, "Q32", Q31_GATE)
    # the sealed run's container: the module rule only (the graded role staged the commit)
    assert batch.check_agent_gate(bare, "Q32", Q31_GATE, committed=False) is None
    with pytest.raises(batch.BatchError, match="plans only"):
        batch.check_agent_gate(bare, "Q31", Q31_GATE, committed=False)


def test_a_sealed_parts_crate_task_is_found_in_the_unsealed_copy(agents_root, tmp_path):
    root = agents_root
    stratum = "bench/local/q/agentic/q32-t9"
    into = tmp_path / "unsealed"
    src = root / CRATE.format(t="c1")
    dst = into / "c1" / "tasks"
    for f in src.rglob("*"):
        if f.is_file():
            (dst / f.relative_to(src)).parent.mkdir(parents=True, exist_ok=True)
            (dst / f.relative_to(src)).write_bytes(f.read_bytes())
    p = write_plan(root, arms=[("G", "gate")], extra=gate_line(root))
    p.write_text(p.read_text().replace(CRATE.format(t="c1"), f"{stratum}/c1/tasks"))
    with pytest.raises(batch.BatchError):
        batch.load_plan(p, root)                       # not in the course tree
    plan = batch.load_plan(p, root, tasks_at={stratum: into})
    assert plan.tasks["c1"] == (f"{stratum}/c1/tasks", "verus") and plan.gate == Q31_GATE


def test_a_task_in_a_sealed_stratum_needs_the_statements_pin(root):
    age, key = _seal(root, ["c1"])
    commit_statements(root)
    statements.unseal(root, "Q98", age=age, identity=key)
    git(root, "add", ".")
    git(root, "commit", "-qm", "unsealed")
    with pytest.raises(batch.BatchError, match="sealed stratum"):
        batch.load_plan(write_plan(root, arms=[("P", "verify")]), root)
    p = write_plan(root, arms=[("P", "verify")],
                   extra='statements = ["research/q98_statements.dfy"]')
    b = make(root, p)
    b.open()
    note = batch.batch_note(budget.Ledger(budget.ledger_path(root, "Q98")))
    assert note["statements_sha256"] == {"research/q98_statements.dfy":
                                         sha(b"// my statements\n")}
    assert b.run() == 0
    (m, _), = runs(root).values()
    assert m.apparatus["statements_sha256"] == note["statements_sha256"]


def test_a_plan_whose_statements_are_not_the_pin_refuses(root):
    put_crate(root)
    commit_statements(root)
    p = write_plan(root, arms=[("P", "verify")], extra='statements = ["research/other.dfy"]')
    with pytest.raises(batch.BatchError, match="are not the files"):
        make(root, p).open()


def test_the_executor_refuses_a_stop_until_the_acceptance_passes(tmp_path):
    ctx = protocol.Context(task_id="c1", lang="verus", statement="", editable=("c/src/lib.rs",),
                           readable=("c/Cargo.toml",), target="c/src/lib.rs")
    calls = []

    def accept(work, paths):
        calls.append(sorted(paths))
        lib = (Path(work) / "c" / "src" / "lib.rs").read_text()
        r = CrateGate().execute("vcheck --gate", Path(work) / "c")
        return {"passed": lib == "ok", "verdict": "PASS" if lib == "ok" else "FAIL",
                "reasons": [] if lib == "ok" else ["no"], "results": [r]}

    class Pol:
        def __init__(self):
            self.n = 0

        def propose(self, state, ctx, budget):
            self.n += 1
            if self.n == 1:
                return [protocol.Stop("done", "")]
            if self.n == 2:
                return [protocol.Verify("gate")]
            if self.n == 3:
                return [protocol.Edit("c/src/lib.rs", "", "ok"), protocol.Verify("gate"),
                        protocol.Stop("done", "never reached")]
            raise AssertionError("the run should have ended at the passing gate")

    ex = executor.Executor(ctx, {"c/src/lib.rs": "stub"}, runner=CrateGate(),
                           meter=budget.Meter(budget.Caps(turns=10)),
                           support_files={"c/Cargo.toml": CARGO}, acceptance=accept,
                           verify_target="c")
    res = ex.run(Pol())
    assert res.ended_by == "gate-pass"
    assert calls == [["c/Cargo.toml", "c/src/lib.rs"]] * 2
    assert ex.history[0].observations[0].kind == "refused"
    assert "c/Cargo.toml" not in res.files


# --- the exact-value secret scan (DV4-PLAN §5.7) -----------------------------------------

def test_the_scan_withholds_a_file_holding_the_exact_token(tmp_path):
    tok = "opaque-" + uuid.uuid4().hex + uuid.uuid4().hex   # no credential format matches it
    (tmp_path / "calls.jsonl").write_text(f'{{"echo": "{tok}"}}\n')
    (tmp_path / "clean.txt").write_text("nothing here\n")
    assert batch.scan_run_dir(tmp_path)["withheld"] == []
    got = batch.scan_run_dir(tmp_path, exact=(tok,))
    assert got["withheld"] == ["calls.jsonl"] and got["hits"] == ["exact-token"]
    assert not (tmp_path / "calls.jsonl").exists() and (tmp_path / "clean.txt").exists()
    assert tok not in json.dumps(got)

    class T:
        def secret_values(self):
            return (tok,)

    class W:
        inner = T()
    assert batch._secret_values(W()) == (tok,) and batch._secret_values(object()) == ()


def test_the_claude_transport_remembers_its_snapshot_tokens(tmp_path):
    from fvh.backends import claude as CL
    src = tmp_path / "src.json"
    tok = "tok-" + uuid.uuid4().hex
    src.write_text(json.dumps({CL.OAUTH: {"accessToken": tok, "expiresAt": 9e15,
                                          "refreshToken": "never-copied"}}))
    dst = CL.derive_credentials(src, tmp_path / "cfg", now=0.0, min_life_s=10)
    tr = CL.Transport.__new__(CL.Transport)
    tr._tokens = set()
    tr._remember_token(dst)
    assert tr.secret_values() == (tok,)


# --- single use (the challenge tier: QPLAN §31.3, D-6, Δ402) ------------------------------

def _part(root, part):
    sp = root / "bench" / "local" / "q" / "lab9" / "STRATUM.toml"
    sp.write_text(sp.read_text().replace('schema = 1\n', f'schema = 1\npart = "{part}"\n', 1))


def test_a_single_use_part_is_unsealed_once_outside_the_tree(root, tmp_path):
    age, key = _seal(root, ["c1"])
    _part(root, "T1")
    commit_statements(root)
    with pytest.raises(statements.StatementsRefused, match="--part, --into"):
        statements.unseal(root, "Q98", age=age, identity=key, part="T1", once=True)
    with pytest.raises(statements.StatementsRefused, match="outside the course tree"):
        statements.unseal(root, "Q98", age=age, identity=key, part="T1", once=True,
                          into=root / "scratch")
    with pytest.raises(statements.StatementsRefused, match='part = "T2"'):
        statements.unseal(root, "Q98", age=age, identity=key, part="T2", once=True,
                          into=tmp_path / "out")
    out = tmp_path / "out"
    got = statements.unseal(root, "Q98", age=age, identity=key, part="T1", once=True, into=out)
    assert got["strata"][0]["written"] == 3
    assert (out / "c1" / "tasks" / "src" / "lib.rs").read_text() == STUB_RS
    assert not (root / CRATE.format(t="c1")).exists()          # nothing in the tree
    assert not (root / "bench" / "local" / "q" / "lab9" / "UNSEALED.toml").exists()
    led = statements.unseal_ledger(root)
    assert [(e["seq"], e["module"], e["part"], e["files"]) for e in led] == [(1, "Q98", "T1", 3)]
    assert led[0]["prev"] == statements.GENESIS
    written = {f.relative_to(out).as_posix(): f.read_bytes() for f in out.rglob("*") if f.is_file()}
    assert len(written) == 3                     # the sealed run checks the copy by this (Δ419)
    assert led[0]["files_sha256"] == statements.tree_sha256(written)
    with pytest.raises(statements.StatementsRefused, match="unsealed once already"):
        statements.unseal(root, "Q98", age=age, identity=key, part="T1", once=True,
                          into=tmp_path / "again")
    assert not (tmp_path / "again").exists()


def test_the_single_use_ledger_is_chained(root, tmp_path):
    age, key = _seal(root, ["c1"])
    _part(root, "T1")
    commit_statements(root)
    statements.unseal(root, "Q98", age=age, identity=key, part="T1", once=True,
                      into=tmp_path / "o1")
    age, key = _seal(root, ["c2"])                           # a new seal: a new archive sha
    _part(root, "T1")
    statements.unseal(root, "Q98", age=age, identity=key, part="T1", once=True,
                      into=tmp_path / "o2")
    led = statements.unseal_ledger(root)
    assert [e["seq"] for e in led] == [1, 2]
    lp = root / statements.LEDGER
    lines = lp.read_text().splitlines()
    lp.write_text(lines[0].replace('"files":3', '"files":4') + "\n" + lines[1] + "\n")
    with pytest.raises(statements.StatementsRefused, match="chain is broken"):
        statements.unseal_ledger(root)


def test_a_topic_e_stratum_under_agentic_is_found(root):
    d = root / "bench" / "local" / "q" / "agentic" / "q31-heldout"
    d.mkdir(parents=True)
    (d / "STRATUM.toml").write_text('schema = 1\nmodule = "Q98"\narchive = "Hidden/x.tar.age"\n')
    assert d / "STRATUM.toml" in statements.sealed_strata(root, "Q98")
