"""The frozen core's sealed run (fvh.sealed; QPLAN §31.3; DELTAS Δ419, the user's D102 and
D103) and the core pieces it adds: the unsealed part's check against its single-use
record, the `par` ledger lines that reserve par's calls, the Qwen transport on the
agent image's own binary, the plan's tasks read from an unsealed copy, the host's refusal
to run a sealed part's task, par's counts-only record (no prompt or transcript field
survives it) and its re-derivation by fvh.report. Invented module ids and throwaway
roots; no model, no container, nothing sealed."""

import hashlib
import json
import sys
from pathlib import Path

import pytest

import importlib

from fvh import apparatus, backends, batch, budget, report, runlog, sealed, statements

QW = importlib.import_module(backends.FAMILY_MODULES[budget.QWEN])   # the Qwen transport

FAKES = Path(__file__).resolve().parent / "fakes"
CANARY = "DVLCANARY-sealed-core-3f9a"          # an invented token: no real canary's hash
DIGEST = "dvl-agent@sha256:" + "a" * 64
TASK = "method M() ensures true\n{\n}\n"
STRATUM = "bench/local/q/agentic/q98-probe"


def _ledger_line(prev, entry):
    line = statements._canon(entry)
    return line, hashlib.sha256(line.encode()).hexdigest()


def part_root(tmp_path, *, files_sha=True, extra_entry=None):
    """A root with a sealed stratum of part "probe" (cards c1, c2) and its single-use
    record, and the unsealed copy outside it. Returns (root, into)."""
    root = tmp_path / "course"
    (root / STRATUM).mkdir(parents=True)
    (root / STRATUM / "STRATUM.toml").write_text(
        'schema = 1\nmodule = "Q98"\nlab = "Q98"\nstratum = "q98-probe"\npart = "probe"\n'
        'sealed = true\narchive = "Hidden/Agentic/Q98/probe.tar.age"\n'
        f'archive_sha256 = "{"b" * 64}"\n'
        '[[card]]\nid = "c1"\nlang = "dafny"\n[[card]]\nid = "c2"\nlang = "dafny"\n')
    into = tmp_path / "unsealed"
    files = {"c1/tasks/c1.dfy": TASK.encode(), "c2/tasks/c2.dfy": TASK.replace("M", "N").encode()}
    for rel, data in files.items():
        (into / rel).parent.mkdir(parents=True, exist_ok=True)
        (into / rel).write_bytes(data)
    entry = {"seq": 1, "prev": statements.GENESIS, "date": "2026-10-31T00:00:00+00:00",
             "module": "Q98", "part": "probe", "stratum": f"{STRATUM}/STRATUM.toml",
             "archive_sha256": "b" * 64, "manifest_sha256": "c" * 64, "files": 2,
             "statements": {}, **(extra_entry or {})}
    if files_sha:
        entry["files_sha256"] = statements.tree_sha256(files)
    line, _ = _ledger_line(statements.GENESIS, entry)
    (root / "research").mkdir()
    (root / statements.LEDGER).write_text(line + "\n")
    return root, into


# --- the unsealed part -------------------------------------------------------------------

def test_the_unsealed_copy_is_checked_against_its_single_use_record(tmp_path):
    root, into = part_root(tmp_path)
    up = sealed.unsealed_part(root, "Q98", "probe", into)
    assert up.stratum == STRATUM and up.cards == ("c1", "c2")
    assert sorted(up.files) == [f"{STRATUM}/c1/tasks/c1.dfy", f"{STRATUM}/c2/tasks/c2.dfy"]
    assert sealed.part_tasks(up) == {"c1": f"{STRATUM}/c1/tasks/c1.dfy",
                                     "c2": f"{STRATUM}/c2/tasks/c2.dfy"}
    (into / "c1/tasks/c1.dfy").write_text(TASK + "// changed\n")
    with pytest.raises(sealed.SealedRefused, match="exactly as it was unsealed"):
        sealed.unsealed_part(root, "Q98", "probe", into)
    (into / "c1/tasks/c1.dfy").write_text(TASK)
    (into / "c1/tasks/extra.dfy").write_text(TASK)
    with pytest.raises(sealed.SealedRefused, match="exactly as it was unsealed"):
        sealed.unsealed_part(root, "Q98", "probe", into)
    (into / "c1/tasks/extra.dfy").unlink()
    (into / "c9").mkdir()
    (into / "c9/x").write_text("x")
    with pytest.raises(sealed.SealedRefused, match="not a task file of a card"):
        sealed.unsealed_part(root, "Q98", "probe", into)


def test_an_unrecorded_part_a_copy_in_the_tree_and_an_old_record_are_refused(tmp_path):
    root, into = part_root(tmp_path)
    with pytest.raises(sealed.SealedRefused, match="never unsealed"):
        sealed.unsealed_part(root, "Q98", "other", into)
    inside = root / "copy"
    inside.mkdir()
    with pytest.raises(sealed.SealedRefused, match="inside the course tree"):
        sealed.unsealed_part(root, "Q98", "probe", inside)
    root2, into2 = part_root(tmp_path / "old", files_sha=False)
    with pytest.raises(sealed.SealedRefused, match="no files_sha256"):
        sealed.unsealed_part(root2, "Q98", "probe", into2)


def test_a_plan_reads_its_tasks_from_the_unsealed_copy_and_the_host_refuses_them(tmp_path):
    root, into = part_root(tmp_path)
    plan = tmp_path / "plan.toml"
    plan.write_text(f'seed = 7\ntasks = ["c1"]\n[task.c1]\npath = "{STRATUM}/c1/tasks/c1.dfy"\n'
                    '[[arm]]\nname = "a"\nfamily = "qwen"\nrounds = 2\nconstruct = "model"\n'
                    'policy = "fvh:smoke"\n')
    with pytest.raises(batch.BatchError, match="unreadable"):
        batch.load_plan(plan, root)               # not in the tree
    p = batch.load_plan(plan, root, tasks_at={STRATUM: into})
    assert p.tasks == {"c1": (f"{STRATUM}/c1/tasks/c1.dfy", "dafny")}
    assert batch.sealed_part_of(root, f"{STRATUM}/c1/tasks/c1.dfy") == (STRATUM, "probe")
    app = apparatus.load(FAKES / "apparatus.toml")
    b = batch.Batch(root, "Q98", p, transports=lambda *a: None, app=app)
    with pytest.raises(batch.BatchError, match="run only in a sealed run"):
        b.open()


# --- par's reservation -------------------------------------------------------------------

def test_par_lines_reserve_the_modules_budget(tmp_path):
    led = budget.Ledger(tmp_path / "ledger.jsonl")
    led.par("planned", calls=12, runs=6, part="T1", archive_sha256="d" * 64)
    assert led.used()[budget.QWEN] == {"calls": 12, "runs": 6}
    led.par("done", part="T1", runs=6, solved=2, calls=9)
    assert led.used()[budget.QWEN] == {"calls": 12, "runs": 6}     # reserved, not re-counted
    assert [r["event"] for r in led.par_lines("T1")] == ["planned", "done"]
    assert led.par_lines("T2") == []
    with pytest.raises(budget.LedgerError):
        led.par("started")
    text = led.path.read_text().splitlines()
    bad = json.loads(text[-1])
    bad["event"] = "other"
    led.path.write_text("\n".join(text[:-1] + [budget._canon(bad)]) + "\n")
    with pytest.raises(budget.LedgerError, match="event"):
        led.read()


# --- the transport on the image's binary (D102) -------------------------------------------

def test_the_image_binary_is_named_by_its_digest_and_recorded(tmp_path, monkeypatch):
    monkeypatch.delenv(backends.NO_MODEL_ENV, raising=False)
    exe = tmp_path / "img" / "cli"
    exe.parent.mkdir()
    exe.write_text(f"#!{sys.executable}\n" + (FAKES / "fake_opencode.py").read_text())
    exe.chmod(0o755)
    state = tmp_path / "state"
    state.mkdir()
    table = {"version": "1.18.25", "provider_npm": "@ai-sdk/openai-compatible"}
    with pytest.raises(ValueError, match="image digest"):
        QW.Transport(table, gate_url="http://127.0.0.1:8000/v1", model="m", binary=str(exe))
    with pytest.raises(ValueError, match="absolute"):
        QW.Transport(table, gate_url="http://127.0.0.1:8000/v1", model="m",
                     binary="cli", pinned_by=DIGEST)
    t = QW.Transport(table, gate_url="http://127.0.0.1:8000/v1", model="m", state_base=state,
                     cwd_base=str(tmp_path), binary=str(exe), pinned_by=DIGEST)
    c = t.complete("hello", seed=5)
    assert c.apparatus["binary"] == str(exe) and c.apparatus["pinned_by"] == DIGEST
    assert c.apparatus["sha256"] is None              # no second transport pin (D102)
    runs = [json.loads(x) for x in (exe.parent / "calls.jsonl").read_text().splitlines()]
    assert [r["argv"][0] for r in runs] == ["debug", "debug", "run"]
    conf = json.loads(Path(runs[-1]["env"]["OPENCODE_CONFIG"]).read_text()) \
        if Path(runs[-1]["env"]["OPENCODE_CONFIG"]).exists() else None
    assert conf is None                               # the call's state is removed after it
    exe.unlink()
    with pytest.raises(backends.ApparatusMismatch, match="missing"):
        t.complete("hello", seed=6)


# --- par's counts-only record (D103) -------------------------------------------------------

FORBIDDEN_KEYS = {"prompt_hashes", "arm_policy", "policy_source_sha256", "plan_sha256", "calls_log",
                  "message", "message_sha256", "system", "transcript", "prompt", "request",
                  "response", "feedback_sources_sha256", "apparatus_file"}


def par_meta(**over):
    app = {"prompt_hashes": ["e" * 64], "arm_policy": "par_q98.policy:render",
           "arm_construct": "model", "policy_source_sha256": "f" * 64, "plan_sha256": "1" * 64,
           "calls": [{"model": "m", "seed": 3, "prompt": CANARY}], "seeds": [3, 4],
           "lab_task": f"{STRATUM}/c1/tasks/c1.dfy", "instrument": "vcheck --gate",
           "backend": {"qwen": {"binary": "~/.local/bin/qwen-cli"}},
           "apparatus_file": "/home/x/sandbox/apparatus.toml",
           "transport": {"binary": "/opt/dvl/agent/cli", "pinned_by": DIGEST},
           "model_server_found": {"model": "m"}}
    m = runlog.RunMeta(run_id="20261031T000000Z-par-c1-1-1", module="Q98", arm="par",
                       task_id="c1", lang="dafny", attempt=1, repeat=1, mode="harness-executed",
                       backend="qwen", outcome="verified", ended_by="stop",
                       verify={"verdict": "verified", "holes": [], "verified_count": 1},
                       usage={"calls": 2, "gpu_s": 1.5, "note": CANARY}, apparatus=app,
                       findings=("ctx-saturated:1", f"free text {CANARY}"),
                       return_summary={"files_sha256": {"x": "2" * 64}}, **over)
    return m.to_dict()


def _keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _keys(v)


def test_a_par_record_carries_no_prompt_or_transcript_field():
    rec = sealed.counts_only(par_meta(), part="probe", archive_sha256="9" * 64)
    assert not set(_keys(rec)) & FORBIDDEN_KEYS
    assert "backend" not in rec["apparatus"] and "calls" not in rec["apparatus"]
    assert CANARY not in json.dumps(rec)
    assert rec["apparatus"]["counts_only"] is True
    assert rec["apparatus"]["par"] == {"part": "probe", "archive_sha256": "9" * 64}
    assert rec["usage"] == {"calls": 2, "gpu_s": 1.5}
    assert rec["findings"] == ["ctx-saturated:1"]
    assert rec["apparatus"]["transport"]["pinned_by"] == DIGEST
    runlog.RunMeta(**rec)                              # still a run record


def test_report_rederives_a_counts_only_run_without_proposals(tmp_path):
    rd = tmp_path / "par-probe-r1"
    rd.mkdir()
    runlog.write_inputs(rd, {f"{STRATUM}/c1/tasks/c1.dfy": TASK.encode()})
    (rd / "returned" / STRATUM / "c1" / "tasks").mkdir(parents=True)
    (rd / "returned" / STRATUM / "c1" / "tasks" / "c1.dfy").write_text(TASK)
    rec = sealed.counts_only(par_meta(), part="probe", archive_sha256="9" * 64)
    meta = runlog.RunMeta(**rec)
    chk = report.rederive(rd, meta)
    assert chk.ok and chk.derived == "verified" and "counts-only" in chk.detail
    (rd / "returned" / "stray.dfy").write_text(TASK)
    assert not report.rederive(rd, meta).ok
    (rd / "returned" / "stray.dfy").unlink()
    bad = runlog.RunMeta(**{**rec, "outcome": "failed"})
    assert not report.rederive(rd, bad).ok


def test_the_command_line_names_the_sealed_route_for_a_sealed_part(tmp_path, capsys):
    from fvh import __main__ as cli
    root, into = part_root(tmp_path)
    (root / "MODULES.toml").write_text('[[module]]\nid = "Q98"\nstatus = "authoring"\nsolo = true\n'
                                       'budget = { qwen_calls = 9, qwen_runs = 9 }\n')
    plan = tmp_path / "plan.toml"
    plan.write_text(f'seed = 7\ntasks = ["c1"]\n[task.c1]\npath = "{STRATUM}/c1/tasks/c1.dfy"\n'
                    '[[arm]]\nname = "a"\nfamily = "qwen"\nrounds = 2\nconstruct = "model"\n'
                    'policy = "fvh:smoke"\n')
    assert cli.main(["--root", str(root), "run", "Q98", "--plan", str(plan), "--dry-run"]) == 3
    assert "--sealed probe --unsealed DIR" in capsys.readouterr().err
    assert cli.main(["--root", str(root), "run", "Q98", "--plan", str(plan), "--sealed",
                     "probe"]) == 3
    assert "go together" in capsys.readouterr().err
