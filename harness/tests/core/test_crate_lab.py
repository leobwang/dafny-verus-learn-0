"""The frozen core's own tests: Lab 3's pieces (QPLAN §28.5, §28.6, §30 Q64; the DV5c
gaps lane): fvh.statements (the statements pin and the unseal of a sealed stratum),
crate tasks in fvh.batch (a crate's sources editable, its companions read-only and
staged with every verification), and the gated arm (acceptance = "gate": Lab 3's arm G,
whose run ends only when the plan's gate passes the work copy). On throwaway git roots
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


def gate_crate(target, *, run=None):
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


def write_plan(root, *, arms, tasks=("c1",), extra="", lab=""):
    lines = [f'lab = "{lab}"' if lab else "", "seed = 91", f"tasks = {json.dumps(list(tasks))}",
             'system = "sys"', 'instructions = "edit"', extra]
    for t in tasks:
        lines += [f"[task.{t}]", f'path = "{CRATE.format(t=t)}"']
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
