"""The frozen core's own tests: fvh.backends (DV4-PLAN §3.4, §9; Δ63, Δ64, Δ147,
Δ148): both transports against fake CLI executables (harness/tests/core/fakes/),
named by throwaway apparatus pins under a throwaway HOME. The fakes print
recorded-shape streams with neutral content and record their argv and
environment; nothing calls a model or opens a connection. Checked: the argv,
the environment built from nothing, the credentials snapshot, the init,
overage and result assertions, the parsing (a malformed reply included), an
apparatus mismatch, the FVH_NO_MODEL tripwire, and a backend built from the
CI's fake apparatus file failing closed."""

import hashlib
import importlib
import json
import shutil
import stat
import sys
import time
from pathlib import Path

import pytest

from fvh import apparatus, backends, budget, executor, protocol as P
from fvh.backends import claude as CL

QW = importlib.import_module(backends.FAMILY_MODULES[budget.QWEN])
FAKES = Path(__file__).resolve().parent / "fakes"
GATE = "http://127.0.0.1:9/v1"           # a run parameter; nothing listens, nothing connects


def install(tmp_path, monkeypatch, fake, name):
    """Copy a fake into HOME/bin, pin it, and return (pins, control path, calls path)."""
    home = tmp_path / "home"
    (home / "bin").mkdir(parents=True)
    dst = home / "bin" / name
    dst.write_text(f"#!{sys.executable}\n" + (FAKES / fake).read_text())
    dst.chmod(0o755)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv(backends.NO_MODEL_ENV, raising=False)
    sha = hashlib.sha256(dst.read_bytes()).hexdigest()
    return {"binary": f"~/bin/{name}", "sha256": sha}, home / "bin" / "fake-control.json", \
        home / "bin" / "calls.jsonl"


def control(path, **kw):
    path.write_text(json.dumps(kw))


def calls(path):
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


# =====================================================================================
# The Claude transport
# =====================================================================================

def cl_setup(tmp_path, monkeypatch, *, expires_in_s=8 * 3600):
    pins, ctl, log = install(tmp_path, monkeypatch, "fake_claude.py", "0.0.0-fake")
    table = {**pins, "version": "0.0.0-fake", "model": "fake-model", "effort": "low",
             "max_turns": 2}
    cred = tmp_path / "home" / ".claude" / ".credentials.json"
    cred.parent.mkdir(parents=True)
    cred.write_text(json.dumps({"claudeAiOauth": {
        "accessToken": "fake-access-token", "refreshToken": "fake-refresh-token",
        "expiresAt": int((time.time() + expires_in_s) * 1000),
        "refreshTokenExpiresAt": int((time.time() + 86400) * 1000),
        "scopes": ["fake:scope"], "subscriptionType": "fake"},
        "trustedDeviceToken": "fake-device-token"}))
    state = tmp_path / "state"
    state.mkdir()
    t = CL.Transport(table, state_base=state, cwd_base=str(tmp_path))
    return t, table, ctl, log


def test_claude_argv_environment_and_parse(tmp_path, monkeypatch):
    monkeypatch.setenv("FVH_PARENT_ONLY", "must-not-leak")
    t, table, ctl, log = cl_setup(tmp_path, monkeypatch)
    proposal = {"actions": [{"type": "verify", "mode": "gate"}]}
    control(ctl, proposal=proposal)
    c = t.complete("the message", system="the system prompt")
    assert c.structured == proposal and c.turns == 2 and c.window[0] == "ok"
    assert c.tokens() == (13, 7)
    assert c.apparatus["prompt"] == CL.PROMPT_NOTE and c.apparatus["init_assertions"] == "passed"
    (call,) = calls(log)
    a = call["argv"]
    assert a[:5] == ["-p", "--safe-mode", "--tools", "", "--strict-mcp-config"]
    sent = json.loads(a[a.index("--json-schema") + 1])
    assert "$schema" not in sent and sent == {k: v for k, v in P.ACTION_SCHEMA.items()
                                              if k != "$schema"}
    assert a[a.index("--model") + 1] == "fake-model" and a[a.index("--max-turns") + 1] == "2"
    assert a[a.index("--system-prompt") + 1] == "the system prompt" and a[-1] == "the message"
    assert "--bare" not in a and "--mcp-config" not in a
    env = call["env"]
    assert set(env) - {"PWD", "SHLVL", "_", "LC_CTYPE"} == {
        "PATH", "HOME", "CLAUDE_CONFIG_DIR", "LANG", "TERM", *CL.ENV_SWITCHES}
    assert env["PATH"] == "/usr/bin:/bin" and "FVH_PARENT_ONLY" not in env
    assert not any(k.startswith("ANTHROPIC") for k in env)
    assert call["cwd_entries"] == [] and Path(call["cwd"]).parent == tmp_path
    assert not Path(call["cwd"]).exists() and list((tmp_path / "state").iterdir()) == []


def test_claude_credentials_snapshot_has_no_refresh_token(tmp_path, monkeypatch):
    t, _, ctl, log = cl_setup(tmp_path, monkeypatch)
    t.complete("m")
    cred = calls(log)[0]["credentials"]
    assert cred["mode"] == 0o600
    inner = cred["data"]["claudeAiOauth"]
    assert inner["accessToken"] == "fake-access-token"
    assert not any("refresh" in k.lower() for k in inner)
    assert set(cred["data"]) == {"claudeAiOauth"} and set(inner) <= set(CL.SNAPSHOT_KEYS)


def test_claude_pinned_builtins_pass_the_init_assertions(tmp_path, monkeypatch):
    t, table, ctl, log = cl_setup(tmp_path, monkeypatch)
    t.table.update(builtin_plugins=["bp"], builtin_skills=["bs1", "bs2"])
    control(ctl, init={"plugins": [{"name": "bp", "path": "builtin", "source": "bp@builtin"}],
                       "skills": ["bs1"]})
    assert t.complete("m").apparatus["init_assertions"] == "passed"
    for init, match in (({"plugins": [{"name": "bp", "path": "/home/x/plugins/bp"}]},
                         "init plugins"), ({"skills": ["bs1", "user-skill"]}, "init skills")):
        control(ctl, init=init)
        with pytest.raises(backends.ApparatusMismatch, match=match):
            t.complete("m")


def test_claude_turn_cap_is_a_malformed_reply_that_counts(tmp_path, monkeypatch):
    t, _, ctl, log = cl_setup(tmp_path, monkeypatch)
    control(ctl, result={"subtype": "error_max_turns", "is_error": True, "num_turns": 3,
                         "structured_output": None, "terminal_reason": "max_turns",
                         "errors": ["Reached maximum number of turns (2)"]})
    c = t.complete("m")
    assert c.structured is None and c.text == "" and c.apparatus["ended"] == "max-turns"
    meter = budget.Meter()
    policy = backends.ModelPolicy(t, backends.smoke_render, meter=meter)
    ctx = P.Context(task_id="T", lang="dafny", statement="s", editable=("w.dfy",), readable=(),
                    target="w.dfy")
    with pytest.raises(P.Malformed):
        policy.propose(P.State("T", 0, {}), ctx, meter.snapshot())
    assert meter.calls == 1 and meter.outputs == 1


def test_claude_not_logged_in_is_auth_before_output(tmp_path, monkeypatch):
    t, _, ctl, log = cl_setup(tmp_path, monkeypatch)
    control(ctl, synthetic="Not logged in \u00b7 Please run /login",
            result={"is_error": True, "result": "Not logged in \u00b7 Please run /login",
                    "structured_output": None})
    with pytest.raises(backends.TransportError) as e:
        t.complete("m")
    assert e.value.cause == "auth" and not e.value.had_output


def test_claude_defers_when_the_token_is_too_close_to_expiry(tmp_path, monkeypatch):
    t, _, ctl, log = cl_setup(tmp_path, monkeypatch, expires_in_s=60)
    with pytest.raises(backends.Deferred):
        t.complete("m")
    assert calls(log) == []


def test_claude_without_credentials_is_an_auth_failure_before_output(tmp_path, monkeypatch):
    t, _, ctl, log = cl_setup(tmp_path, monkeypatch)
    (tmp_path / "home" / ".claude" / ".credentials.json").unlink()
    with pytest.raises(backends.TransportError) as e:
        t.complete("m")
    assert e.value.cause == "auth" and not e.value.had_output and calls(log) == []


@pytest.mark.parametrize("ctl_kw, match", [
    ({"init": {"tools": ["Bash", "StructuredOutput"]}}, "init tools"),
    ({"init": {"mcp_servers": [{"name": "x"}]}}, "init mcp_servers"),
    ({"init": {"plugins": [{"name": "p"}]}}, "init plugins"),
    ({"init": {"skills": ["s"]}}, "init skills"),
    ({"init": {"apiKeySource": "ANTHROPIC_API_KEY"}}, "apiKeySource"),
    ({"version": "9.9.9"}, "claude_code_version"),
    ({"init": {"model": "other"}}, "init model"),
    ({"touch": True}, "left 1 entries"),
    ({"rate_limit": {"status": "allowed", "overageStatus": "rejected",
                     "isUsingOverage": True}}, "isUsingOverage"),
    ({"rate_limit": {"status": "allowed", "overageStatus": "allowed",
                     "isUsingOverage": False}}, "overageStatus"),
    ({"rate_limit": None}, "the call carried no rate_limit_event"),
    ({"result": {"num_turns": 5}}, "num_turns"),
])
def test_claude_assertions_stop_the_batch(tmp_path, monkeypatch, ctl_kw, match):
    t, _, ctl, log = cl_setup(tmp_path, monkeypatch)
    control(ctl, **ctl_kw)
    with pytest.raises(backends.ApparatusMismatch, match=match):
        t.complete("m")


def test_claude_a_later_call_without_an_event_stops_too(tmp_path, monkeypatch):
    """DV5c fix round: a call is judged on its own event only; one without an event
    stops, and the stop carries what the batch needs (the call ran)."""
    t, _, ctl, log = cl_setup(tmp_path, monkeypatch)
    t.complete("m")
    control(ctl, rate_limit=None)
    with pytest.raises(apparatus.ApparatusMismatch, match="no rate_limit_event") as e:
        t.complete("m")
    assert e.value.ran and e.value.overage and e.value.rate_limit is None


def test_claude_an_overage_stop_carries_its_event(tmp_path, monkeypatch):
    t, _, ctl, log = cl_setup(tmp_path, monkeypatch)
    bad = {"status": "allowed", "overageStatus": "allowed", "isUsingOverage": True}
    control(ctl, rate_limit=bad)
    with pytest.raises(apparatus.ApparatusMismatch, match="overage check") as e:
        t.complete("m")
    assert e.value.ran and e.value.overage and e.value.rate_limit == bad


def test_claude_a_reached_window_defers(tmp_path, monkeypatch):
    t, _, ctl, log = cl_setup(tmp_path, monkeypatch)
    control(ctl, rate_limit={"status": "allowed", "overageStatus": "rejected",
                             "isUsingOverage": False,
                             "unifiedWindows": {"five_hour": {"utilization": 0.95}}})
    assert t.complete("m").window[0] == "defer"


@pytest.mark.parametrize("ctl_kw, cause, had", [
    ({"result": {"is_error": True, "api_error_status": 429}}, "rate-limit", True),
    ({"result": {"is_error": True, "api_error_status": 401}}, "auth", True),
    ({"result": {"is_error": True, "api_error_status": 500}}, "cli-crash", True),
    ({"no_result": True, "exit": 1}, "cli-crash", True),
])
def test_claude_errors_name_their_cause(tmp_path, monkeypatch, ctl_kw, cause, had):
    t, _, ctl, log = cl_setup(tmp_path, monkeypatch)
    control(ctl, **ctl_kw)
    with pytest.raises(backends.TransportError) as e:
        t.complete("m")
    assert e.value.cause == cause and e.value.had_output == had


def test_claude_a_changed_binary_is_refused_before_it_runs(tmp_path, monkeypatch):
    t, table, ctl, log = cl_setup(tmp_path, monkeypatch)
    p = tmp_path / "home" / "bin" / "0.0.0-fake"
    p.write_text(p.read_text() + "\n# changed\n")
    with pytest.raises(backends.ApparatusMismatch, match="sha256"):
        t.complete("m")
    assert calls(log) == []


def test_claude_model_policy_through_the_executor(tmp_path, monkeypatch):
    t, _, ctl, log = cl_setup(tmp_path, monkeypatch)
    control(ctl, proposal={"actions": [{"type": "edit", "path": "w.dfy", "old": "",
                                        "new": "ok"}, {"type": "stop", "reason": "done"}]})
    meter = budget.Meter(budget.Caps(calls=3))
    policy = backends.ModelPolicy(t, backends.smoke_render, meter=meter, system="sys")
    ctx = P.Context(task_id="T", lang="dafny", statement="s", editable=("w.dfy",), readable=(),
                    target="w.dfy")

    class R(executor.LogRunner):
        def __init__(self):
            self.results, self.used = [], 0

        def execute(self, instrument, target, *, timeout_s=None):
            from fvh import tools
            return tools.ToolResult(instrument, str(target), {"verdict": "verified", "holes": [],
                                                              "verified_count": 1}, 0, None,
                                    "replay", "agent", "0" * 64)
    res = executor.Executor(ctx, {"w.dfy": "x"}, runner=R(), meter=meter).run(policy)
    assert (res.outcome, res.ended_by) == ("verified", "stop")
    assert meter.calls == 1 and meter.outputs == 1 and meter.tokens_out == 7
    assert json.loads(calls(log)[0]["argv"][-1])["task"] == "T"       # the smoke renderer


def test_claude_malformed_structured_output(tmp_path, monkeypatch):
    t, _, ctl, log = cl_setup(tmp_path, monkeypatch)
    control(ctl, proposal={"actions": [{"type": "launch"}]})
    meter = budget.Meter()
    policy = backends.ModelPolicy(t, backends.smoke_render, meter=meter)
    ctx = P.Context(task_id="T", lang="dafny", statement="s", editable=("w.dfy",), readable=(),
                    target="w.dfy")
    with pytest.raises(P.Malformed):
        policy.propose(P.State("T", 0, {}), ctx, meter.snapshot())
    assert meter.calls == 1                         # a malformed reply counts as a call


# =====================================================================================
# The Qwen transport
# =====================================================================================

def qw_setup(tmp_path, monkeypatch, **extra):
    pins, ctl, log = install(tmp_path, monkeypatch, "fake_opencode.py", "qcli")
    table = {**pins, "version": "0.0.0-fake", "model": "fake:latest", "num_ctx": 32768,
             "num_predict": 512, **extra}
    state = tmp_path / "state"
    state.mkdir()
    return QW.Transport(table, gate_url=GATE, state_base=state, cwd_base=str(tmp_path)), ctl, log


def test_qwen_config_environment_argv_and_precheck(tmp_path, monkeypatch):
    t, ctl, log = qw_setup(tmp_path, monkeypatch)
    c = t.complete("the message", system="sys", seed=41)
    assert P.parse_proposal(backends.one_json_value(c.text))[0] == P.Stop("give-up")
    assert c.usage == {"input_tokens": 11, "output_tokens": 5}
    agent, conf, run = calls(log)
    assert agent["argv"] == ["debug", "agent", "build", "--pure"]
    assert conf["argv"] == ["debug", "config", "--pure"]
    assert run["argv"][:6] == ["run", "--pure", "--format", "json", "-m",
                               f"{QW.PROVIDER}/fake:latest"]
    assert run["argv"][-1] == "sys\n\nthe message"
    env = run["env"]
    assert all(env[k] == "1" for k in QW.DISABLE) and len(QW.DISABLE) == 8
    assert all(env[k].startswith(env["HOME"]) for k in QW.XDG)
    assert env["HOME"].startswith(str(tmp_path / "state"))         # the call's own state
    conf_obj = QW.config(t.table, gate_url=GATE, seed=41)
    assert conf_obj["permission"] == {"*": "deny"} and conf_obj["tools"] == {"*": False}
    assert conf_obj["mcp"] == {} and conf_obj["share"] == "disabled"
    # one call, one gated request: no title request, no compaction request (step 3c)
    assert conf_obj["agent"] == {"title": {"disable": True}}
    assert conf_obj["compaction"] == {"auto": False}
    model = conf_obj["provider"][QW.PROVIDER]["models"]["fake:latest"]
    assert model["limit"]["context"] == 32768 and model["options"] == {"seed": 41}
    assert conf_obj["provider"][QW.PROVIDER]["options"]["baseURL"] == GATE
    assert list((tmp_path / "state").iterdir()) == []


@pytest.mark.parametrize("ctl_kw, match", [
    ({"tools_on": ["bash"]}, "tools not disabled: bash"),
    ({"allow_external": "/tmp/elsewhere/*"}, "external_directory"),
    ({"extra_url": "http://127.0.0.1:11/v1"}, "provider URLs"),
])
def test_qwen_precheck_refuses(tmp_path, monkeypatch, ctl_kw, match):
    t, ctl, log = qw_setup(tmp_path, monkeypatch)
    control(ctl, **ctl_kw)
    with pytest.raises(backends.ApparatusMismatch, match=match):
        t.complete("m")
    assert [c["argv"][0] for c in calls(log)] == ["debug", "debug"]      # no run


def test_qwen_tolerated_external_pattern(tmp_path, monkeypatch):
    t, ctl, log = qw_setup(tmp_path, monkeypatch, external_ok=["/tmp/qcli/*"])
    control(ctl, allow_external="/tmp/qcli/*")
    t.complete("m")


def test_qwen_reply_parsing(tmp_path, monkeypatch):
    t, ctl, log = qw_setup(tmp_path, monkeypatch)
    control(ctl, reply="<think>plan</think>```json\n{\"actions\": [{\"type\": \"verify\", "
                       "\"mode\": \"gate\"}]}\n```")
    c = t.complete("m")
    assert P.parse_proposal(backends.one_json_value(c.text)) == [P.Verify()]
    control(ctl, reply='{"actions": [{"type": "verify", "mode": "gate"}]} and more')
    ctx = P.Context(task_id="T", lang="dafny", statement="s", editable=("w",), readable=(),
                    target="w")
    with pytest.raises(P.Malformed, match="after its JSON"):
        backends.default_parse(t.complete("m"), ctx)


def test_qwen_a_failed_run_is_a_crash(tmp_path, monkeypatch):
    t, ctl, log = qw_setup(tmp_path, monkeypatch)
    control(ctl, exit=1)
    with pytest.raises(backends.TransportError) as e:
        t.complete("m")
    assert e.value.cause == "cli-crash" and e.value.had_output


def test_qwen_needs_a_gate_url(tmp_path, monkeypatch):
    monkeypatch.delenv(backends.NO_MODEL_ENV, raising=False)
    with pytest.raises(ValueError):
        QW.Transport({"binary": "~/x", "sha256": "0" * 64}, gate_url="unix:/x")


# =====================================================================================
# The adapters and the tripwire
# =====================================================================================

class Scripted:
    family = "scripted"

    def __init__(self, *replies):
        self.replies, self.n = list(replies), 0

    def complete(self, message, *, system="", seed=None):
        r = self.replies[self.n]
        self.n += 1
        return backends.Completion(text=r, usage={"input_tokens": 2, "output_tokens": 1})


def edit(path, old, new):
    return json.dumps({"actions": [{"type": "edit", "path": path, "old": old, "new": new}]})


def test_candidate_ask_returns_the_whole_file():
    meter = budget.Meter(budget.Caps(calls=2))
    ask = backends.candidate_ask(Scripted(edit("w", "", "TEXT"), edit("w", "", "T2")),
                                 target="w", meter=meter)
    assert ask("p", 1) == "TEXT" and ask("p", 2) == "T2"
    assert meter.calls == 2
    with pytest.raises(budget.CapReached):
        ask("p", 3)


@pytest.mark.parametrize("reply", [
    edit("other", "", "x"),
    edit("w", "a", "b"),
    json.dumps({"actions": [{"type": "stop", "reason": "done"}]}),
    json.dumps({"actions": [json.loads(edit("w", "", "a"))["actions"][0]] * 2}),
    "no json",
])
def test_candidate_ask_refuses_other_replies(reply):
    with pytest.raises(P.Malformed):
        backends.candidate_ask(Scripted(reply), target="w")("p", 1)


def test_strip_think():
    assert backends.strip_think("a<think>x</think>b<think>y") == "ab"


def test_no_model_refuses_before_anything_runs(tmp_path, monkeypatch):
    monkeypatch.setenv(backends.NO_MODEL_ENV, "1")
    app = apparatus.load(FAKES / "apparatus.toml")
    for fam in budget.FAMILIES:
        with pytest.raises(backends.ModelDisabled):
            backends.build(fam, app, gate_url=GATE) if fam == budget.QWEN else \
                backends.build(fam, app)
    with pytest.raises(backends.ModelDisabled):
        CL.Transport({})


def test_a_backend_built_from_the_ci_apparatus_fails_closed(tmp_path, monkeypatch):
    monkeypatch.delenv(backends.NO_MODEL_ENV, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))                 # an empty HOME, as in CI
    monkeypatch.setenv(apparatus.ENV, str(FAKES / "apparatus.toml"))
    t = backends.build(budget.CLAUDE)
    with pytest.raises(backends.ApparatusMismatch, match="missing"):
        t.complete("m")
    q = backends.build(budget.QWEN, gate_url=GATE)
    with pytest.raises(backends.ApparatusMismatch, match="missing"):
        q.complete("m")
