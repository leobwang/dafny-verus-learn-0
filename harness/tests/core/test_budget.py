"""The frozen core's own tests: fvh.budget (DV4-PLAN §4, §9; Δ148, Δ149, Δ176):
caps and the meter, the overage checks on fake events, the window file and the
sentinel rule, the attempt plan against a registry budget, the hash-chained
ledger and its state rules, the anchors (a deleted, truncated or replaced
ledger refused; an open anchor blocking a new batch), and the resume rules as
properties. Throwaway roots only; no model."""

import json
import random
import subprocess

import pytest

from fvh import budget as B


# --- caps and the meter ----------------------------------------------------------------


def test_the_meter_counts_and_names_the_first_cap():
    t = [0.0]
    m = B.Meter(B.Caps(calls=2, tokens=100, wall_s=10), clock=lambda: t[0])
    assert m.cause() is None and not m.snapshot().exhausted
    m.charge(tokens_in=30, tokens_out=20)
    assert m.snapshot().calls_left == 1 and m.snapshot().tokens_left == 50
    m.before_call()
    m.charge(tokens_in=1)
    assert m.cause() == "call-cap" and m.snapshot().exhausted
    with pytest.raises(B.CapReached) as e:
        m.before_call()
    assert e.value.cause == "call-cap"
    t[0] = 11.0
    assert m.cause() == "call-cap"                      # units in order: calls first
    m2 = B.Meter(B.Caps(wall_s=10), clock=lambda: t[0])
    t[0] = 25.0
    assert m2.cause() == "wall-clock"


def test_caps_from_a_table():
    assert B.Caps.from_mapping({"calls": 40, "gpu_s": 3600}).gpu_s == 3600
    with pytest.raises(ValueError):
        B.Caps.from_mapping({"dollars": 1})
    with pytest.raises(ValueError):
        B.Caps(calls=-1)


# --- overage and windows ----------------------------------------------------------------

ALLOWED = {"status": "allowed", "overageStatus": "rejected", "isUsingOverage": False,
           "unifiedWindows": {"five_hour": {"utilization": 0.1}, "seven_day": {"utilization": 0.2}}}
RULE = B.WindowRule()


def test_an_allowed_event_passes():
    assert B.check_event(ALLOWED, RULE)[0] == "ok"


@pytest.mark.parametrize("change, verdict", [
    ({"isUsingOverage": True}, "stop"),
    ({"isUsingOverage": None}, "stop"),
    ({"overageStatus": "allowed"}, "stop"),
    ({"status": "rejected"}, "defer"),
    ({"unifiedWindows": {"five_hour": {"utilization": 0.85}}}, "defer"),
    ({"unifiedWindows": {"seven_day": {"utilization": 0.6}}}, "defer"),
])
def test_overage_and_window_checks(change, verdict):
    assert B.check_event({**ALLOWED, **change}, RULE)[0] == verdict


def test_a_missing_event_stops_on_every_call_never_inherited():
    """DV5c fix round: a call without its own rate_limit_event is never judged on
    an earlier call's event."""
    w = B.OverageWatch(RULE)
    assert w.observe(None)[0] == "stop"
    w = B.OverageWatch(RULE)
    assert w.observe(ALLOWED)[0] == "ok"
    v, why, judged = w.observe(None)
    assert v == "stop" and judged is None and "no rate_limit_event" in why
    assert w.observe({**ALLOWED, "isUsingOverage": True})[0] == "stop"


def test_the_ledger_counts_calls_spent_by_re_issued_attempts(tmp_path):
    """DV5c fix round: an infra-failed or deferred attempt's recorded calls are spent
    on top of the plan; an overage stop holds until a cleared note."""
    led = B.Ledger(tmp_path / "ledger.jsonl")
    led.plan([B.PlannedAttempt("a/t1/1/1", B.CLAUDE, 2), B.PlannedAttempt("a/t2/1/1", B.CLAUDE, 2)])
    assert led.used()[B.CLAUDE]["calls"] == 4
    led.move("a/t1/1/1", "running")
    led.move("a/t1/1/1", "infra-failed", calls=1)
    led.move("a/t2/1/1", "running")
    led.move("a/t2/1/1", "scored", calls=2)
    assert led.used()[B.CLAUDE] == {"calls": 5, "runs": 2}
    assert led.overage_stop() is None
    led.append({"kind": "note", "note": "overage-stop", "reason": "r"})
    assert led.overage_stop()["reason"] == "r"
    led.append({"kind": "note", "note": "overage-cleared"})
    assert led.overage_stop() is None


def test_a_batch_starts_only_from_a_fresh_allowed_event(tmp_path):
    f = tmp_path / "claude-window.json"
    assert not B.batch_may_start(f, RULE, now=1000.0)[0]
    B.write_window(f, ALLOWED, now=1000.0)
    assert B.batch_may_start(f, RULE, now=1000.0 + 60)[0]
    assert not B.batch_may_start(f, RULE, now=1000.0 + B.FIVE_HOURS)[0]
    B.write_window(f, {**ALLOWED, "status": "rejected"}, now=1000.0)
    assert not B.batch_may_start(f, RULE, now=1001.0)[0]


# --- the plan --------------------------------------------------------------------------


def arms():
    return [B.Arm("A1", B.QWEN, 8), B.Arm("A2", B.QWEN, 8), B.Arm("C", B.CLAUDE, 5)]


def test_the_plan_enumerates_every_id_in_order():
    items = B.enumerate_plan(arms()[:2], ["t1", "t2"], repeats=3)
    assert len(items) == 12 and items[0].id == "A1/t1/1/1" and items[-1].id == "A2/t2/3/1"
    tot = B.plan_totals(items)
    assert tot[B.QWEN] == {"calls": 96, "runs": 12} and tot[B.CLAUDE]["runs"] == 0
    with pytest.raises(ValueError):
        B.attempt_id("A/1", "t", 1, 1)


def test_interleaved_groups_run_first_in_adjacent_runs():
    items = B.enumerate_plan(arms(), ["t1", "t2"], repeats=2, interleave=[["A2", "A1"]])
    ids = [p.id for p in items]
    assert ids[:4] == ["A2/t1/1/1", "A1/t1/1/1", "A2/t1/2/1", "A1/t1/2/1"]
    assert ids[8:] == ["C/t1/1/1", "C/t1/2/1", "C/t2/1/1", "C/t2/2/1"]
    assert sorted(ids) == sorted(p.id for p in B.enumerate_plan(arms(), ["t1", "t2"], repeats=2))
    for bad in ([["A1", "A1"]], [["A1"], ["A1"]], [["Z"]], [[]]):
        with pytest.raises(B.BudgetError):
            B.enumerate_plan(arms(), ["t1"], interleave=bad)


def test_a_plan_over_the_registry_budget_is_refused():
    items = B.enumerate_plan(arms(), ["t1", "t2"], repeats=2)
    ok = {"qwen_calls": 64, "qwen_runs": 8, "claude_calls": 20, "claude_runs": 4}
    assert B.check_plan(items, ok) == []
    assert B.check_plan(items, {**ok, "claude_calls": 19})
    assert B.check_plan(items, ok, used={B.QWEN: {"calls": 1, "runs": 0}})
    assert B.check_plan(items, {**ok, "qwen_runs": 7})


def test_the_registry_budget_is_read_from_the_registry(tmp_path):
    (tmp_path / "MODULES.toml").write_text(
        '[[module]]\nid = "Q98"\nbudget = { claude_calls = 3, claude_runs = 1, qwen_calls = 0, '
        'qwen_runs = 0, gpu_hours = 0 }\n')
    assert B.registry_budget(tmp_path, "Q98")["claude_calls"] == 3
    with pytest.raises(B.BudgetError):
        B.registry_budget(tmp_path, "Q97")


# --- the ledger -------------------------------------------------------------------------


def ledger(tmp_path):
    n = [0]

    def clock():
        n[0] += 1
        return f"2026-10-11T00:00:{n[0]:02d}Z"
    return B.Ledger(tmp_path / "research" / "runs" / "Q98" / "ledger.jsonl", clock=clock)


def test_the_ledger_chains_its_lines(tmp_path):
    lg = ledger(tmp_path)
    lg.plan(B.enumerate_plan(arms()[:1], ["t1"], repeats=2))
    lg.move("A1/t1/1/1", "running")
    lg.move("A1/t1/1/1", "scored", outcome="failed")
    lg.sentinel(calls=1)
    recs = lg.read()
    assert [r["seq"] for r in recs] == [1, 2, 3, 4, 5]
    assert recs[0]["prev"] == B.GENESIS
    assert lg.attempts()["A1/t1/1/1"].outcome == "failed"
    assert lg.used()[B.QWEN] == {"calls": 16, "runs": 2}
    assert lg.used()[B.CLAUDE]["calls"] == 1
    text = lg.path.read_text().splitlines()
    text[2] = text[2].replace("running", "deferred")
    lg.path.write_text("\n".join(text) + "\n")
    with pytest.raises(B.LedgerError, match=":4: the chain breaks"):
        lg.read()


def test_scored_is_written_once_and_ids_are_never_added_twice(tmp_path):
    lg = ledger(tmp_path)
    items = B.enumerate_plan(arms()[:1], ["t1"])
    lg.plan(items)
    with pytest.raises(B.BudgetError):
        lg.plan(items)
    lg.move("A1/t1/1/1", "running")
    lg.move("A1/t1/1/1", "scored", outcome="verified")
    for st in B.STATES:
        with pytest.raises(B.LedgerError):
            lg.move("A1/t1/1/1", st)
    with pytest.raises(B.LedgerError):
        lg.move("A9/t1/1/1", "running")


def test_infra_failed_is_reissued_a_bounded_number_of_times(tmp_path):
    lg = ledger(tmp_path)
    lg.plan(B.enumerate_plan(arms()[:1], ["t1"]))
    aid = "A1/t1/1/1"
    for _ in range(3):                                  # the first run, then two re-issues
        lg.move(aid, "running")
        lg.move(aid, "infra-failed")
    assert lg.attempts()[aid].reissues == 2
    assert B.resume_order(lg, max_reissue=2) == []
    assert B.resume_order(lg, max_reissue=3) == [aid]
    with pytest.raises(B.LedgerError, match="re-issued"):
        lg.move(aid, "running", max_reissue=2)


def test_resume_rules_as_properties(tmp_path):
    rng = random.Random(7)
    for trial in range(30):
        lg = B.Ledger(tmp_path / f"l{trial}.jsonl")
        items = B.enumerate_plan(arms()[:2], ["t1", "t2", "t3"])
        lg.plan(items)
        for p in items:
            for _ in range(rng.randrange(4)):
                st = lg.attempts()[p.id].state
                nxt = [s for s in B.TRANSITIONS[st]
                       if not (st == "infra-failed" and lg.attempts()[p.id].reissues >= 3)]
                if not nxt:
                    break
                lg.move(p.id, rng.choice(nxt))
        att = lg.attempts()
        order = B.resume_order(lg)
        assert all(att[i].state != "scored" and att[i].state != "running" for i in order)
        assert order == [p.id for p in items if p.id in order]          # plan order
        for p in items:
            a = att[p.id]
            if a.state in ("planned", "deferred") or (a.state == "infra-failed"
                                                      and a.reissues < 3):
                assert p.id in order


# --- the anchors -------------------------------------------------------------------------


def git_root(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "MODULES.toml").write_text(
        '[[module]]\nid = "Q98"\nbudget = { claude_calls = 50, claude_runs = 10, '
        'qwen_calls = 500, qwen_runs = 50, gpu_hours = 1 }\n')
    return tmp_path


def test_open_and_close_anchor_the_batch(tmp_path):
    root = git_root(tmp_path)
    lg = B.open_batch(root, "Q98", B.enumerate_plan(arms()[:1], ["t1"]), course_commit="c0")
    assert B.last_anchor(root, "Q98")["event"] == "open"
    with pytest.raises(B.AnchorError, match="still open"):
        B.open_batch(root, "Q98", B.enumerate_plan(arms()[1:2], ["t1"]), course_commit="c0")
    lg.move("A1/t1/1/1", "running")
    lg.move("A1/t1/1/1", "scored", outcome="failed")
    rec = B.close_batch(root, "Q98", course_commit="c0")
    assert rec["seq"] == 3 and rec["head"] == lg.head()[1]
    assert B.check_anchors(root, "Q98") == 2
    B.open_batch(root, "Q98", B.enumerate_plan(arms()[1:2], ["t1"]), course_commit="c1")


def test_a_deleted_truncated_or_replaced_ledger_is_refused(tmp_path):
    root = git_root(tmp_path)
    lg = B.open_batch(root, "Q98", B.enumerate_plan(arms()[:1], ["t1", "t2"]),
                      course_commit="c0")
    B.close_batch(root, "Q98", course_commit="c0")
    saved = lg.path.read_text()
    lg.path.unlink()
    with pytest.raises(B.AnchorError, match="missing"):
        B.check_anchors(root, "Q98")
    lg.path.write_text(saved.splitlines()[0] + "\n")
    with pytest.raises(B.AnchorError, match="truncated"):
        B.check_anchors(root, "Q98")
    other = B.Ledger(tmp_path / "other.jsonl", clock=lambda: "2026-01-01T00:00:00Z")
    other.plan(B.enumerate_plan(arms()[:1], ["x1", "x2"]))
    lg.path.write_text(other.path.read_text())
    with pytest.raises(B.AnchorError, match="hashes differently"):
        B.check_anchors(root, "Q98")
    with pytest.raises(B.AnchorError):
        B.open_batch(root, "Q98", B.enumerate_plan(arms()[1:2], ["t9"]), course_commit="c0")


def test_an_ignored_heads_file_or_no_git_is_refused(tmp_path):
    root = git_root(tmp_path / "g")
    (root / ".gitignore").write_text("research/ledger-heads.jsonl\n")
    with pytest.raises(B.AnchorError, match="ignored"):
        B.open_batch(root, "Q98", B.enumerate_plan(arms()[:1], ["t1"]), course_commit="c")
    plain = tmp_path / "plain"
    plain.mkdir()
    (plain / "MODULES.toml").write_text((root / "MODULES.toml").read_text())
    with pytest.raises(B.AnchorError, match="git"):
        B.open_batch(plain, "Q98", B.enumerate_plan(arms()[:1], ["t1"]), course_commit="c",
                     require_git=True)


def test_a_plan_over_budget_writes_nothing(tmp_path):
    root = git_root(tmp_path)
    items = B.enumerate_plan([B.Arm("C", B.CLAUDE, 6)], ["t1", "t2", "t3", "t4", "t5", "t6",
                                                         "t7", "t8", "t9"])
    with pytest.raises(B.BudgetError):
        B.open_batch(root, "Q98", items, course_commit="c")
    assert not B.ledger_path(root, "Q98").exists() and B.read_heads(root) == []


def test_heads_lines_are_validated(tmp_path):
    (tmp_path / "research").mkdir()
    (tmp_path / "research" / "ledger-heads.jsonl").write_text(json.dumps({"module": "Q98"}) + "\n")
    with pytest.raises(B.AnchorError, match=":1: not an anchor"):
        B.read_heads(tmp_path)
