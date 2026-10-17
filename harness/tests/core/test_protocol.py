"""The frozen core's own tests: fvh.protocol (DV4-PLAN §3.2, §9): the actions, the
run's state, context and budget, the observation clip, the action schema and its
validator, and the JSON round trip. No model, no container."""

import dataclasses
import json

import pytest

from fvh import protocol as P


def ctx(**kw):
    base = dict(task_id="T1", lang="dafny", statement="s", editable=("a.dfy",),
                readable=("b.dfy",), target="a.dfy", material={"text": "x"})
    base.update(kw)
    return P.Context(**base)


def test_actions_are_keyword_built_value_objects():
    assert P.Edit(path="p", old="a", new="b") == P.Edit("p", "a", "b")
    assert P.Verify() == P.Verify(mode="gate")
    assert P.Stop(reason="done") == P.Stop(reason="done", note="")
    assert P.Read(path="p") == P.Read("p", None, None)
    assert {P.Stop("done"), P.Stop("done")} == {P.Stop("done")}
    with pytest.raises(dataclasses.FrozenInstanceError):
        P.Edit("p", "a", "b").new = "c"
    assert type(P.Edit("p", "", "x")).__name__ == "Edit"


@pytest.mark.parametrize("make", [
    lambda: P.Read(path=""),
    lambda: P.Read(path="p", start=0),
    lambda: P.Read(path="p", start=3, end=2),
    lambda: P.Read(path="p", start=True),
    lambda: P.Edit(path="p", old=1, new="x"),
    lambda: P.Edit(path="p", old="", new="x" * (P.NEW_LIMIT + 1)),
    lambda: P.Verify(mode="fast"),
    lambda: P.Stop(reason="maybe"),
    lambda: P.Stop(reason="done", note="n" * (P.NOTE_LIMIT + 1)),
])
def test_actions_validate(make):
    with pytest.raises((TypeError, ValueError)):
        make()


def test_context_freezes_and_checks():
    c = ctx()
    assert c.max_actions == P.MAX_ACTIONS and c.read_limit == P.READ_LIMIT
    with pytest.raises(TypeError):
        c.material["text"] = "y"
    assert c.may_read("a.dfy") and c.may_read("b.dfy") and not c.may_read("c.dfy")
    with pytest.raises(ValueError):
        ctx(target="b.dfy")
    with pytest.raises(TypeError):
        ctx(editable="a.dfy")
    with pytest.raises(ValueError):
        ctx(max_actions=0)


def test_state_and_budget():
    s = P.State("T1", 0, {"a.dfy": "0" * 64})
    assert s.last_verify is None and s.history == ()
    with pytest.raises(ValueError):
        P.State("T1", -1, {})
    assert not P.Budget().exhausted
    assert not P.Budget(calls_left=1, tokens_left=None).exhausted
    assert P.Budget(calls_left=0).exhausted and P.Budget(wall_s_left=-0.5).exhausted
    with pytest.raises(TypeError):
        P.Budget(calls_left="1")


def test_clip_states_the_cut():
    text, cut = P.clip("abcdef", 10)
    assert (text, cut) == ("abcdef", 0)
    text, cut = P.clip("é" * 10, 5)                # 20 bytes; cut on a character boundary
    assert text.startswith("éé") and "16 bytes cut" in text and cut == 16
    o = P.Observation("read", True, text, cut=cut)
    assert P.observation_from_json(P.observation_to_json(o)) == o


ALL = [P.Read("a", 1, 3), P.Read("a"), P.Edit("a", "x", "y"), P.Edit("a", "", "whole"),
       P.Verify("loop"), P.Verify(), P.Stop("give-up", "why")]


def test_round_trip_through_json():
    doc = P.proposal_to_json(ALL[:P.MAX_ACTIONS])
    text = json.dumps(doc)
    assert P.parse_proposal(text) == ALL[:P.MAX_ACTIONS]
    assert P.action_to_json(P.Read("a")) == {"type": "read", "path": "a"}


@pytest.mark.parametrize("bad", [
    "not json",
    [],
    {"actions": []},
    {"actions": "x"},
    {"actions": [{"type": "stop", "reason": "done"}], "extra": 1},
    {"actions": [{"type": "jump"}]},
    {"actions": [{"type": "edit", "path": "a", "old": "x"}]},
    {"actions": [{"type": "verify", "mode": "gate", "extra": 1}]},
    {"actions": [{"type": "read", "path": "a", "start": 0}]},
    {"actions": [{"type": "stop", "reason": "done"}] * (P.MAX_ACTIONS + 1)},
])
def test_malformed_proposals(bad):
    with pytest.raises(P.Malformed):
        P.parse_proposal(bad)


def test_max_actions_of_the_context_is_honoured():
    two = {"actions": [{"type": "verify", "mode": "gate"}] * 2}
    assert len(P.parse_proposal(two, max_actions=2)) == 2
    with pytest.raises(P.Malformed):
        P.parse_proposal(two, max_actions=1)


def _check(schema, value):
    """A small JSON-schema checker for the keywords ACTION_SCHEMA uses."""
    t = schema.get("type")
    types = t if isinstance(t, list) else [t] if t else []
    kinds = {"object": dict, "array": list, "string": str, "integer": int, "null": type(None)}
    if types and not any(isinstance(value, kinds[k]) and not (k == "integer" and
                                                              isinstance(value, bool))
                         for k in types):
        return False
    if "const" in schema and value != schema["const"]:
        return False
    if "enum" in schema and value not in schema["enum"]:
        return False
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", 10**9):
            return False
    if isinstance(value, int) and not isinstance(value, bool) and "minimum" in schema:
        if value < schema["minimum"]:
            return False
    if isinstance(value, dict):
        if not set(schema.get("required", [])) <= set(value):
            return False
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False and not set(value) <= set(props):
            return False
        if not all(_check(props[k], v) for k, v in value.items() if k in props):
            return False
    if isinstance(value, list):
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", 10**9):
            return False
        if "items" in schema and not all(_check(schema["items"], v) for v in value):
            return False
    if "oneOf" in schema and sum(_check(s, value) for s in schema["oneOf"]) != 1:
        return False
    return True


CASES = [
    P.proposal_to_json(ALL[:3]),
    P.proposal_to_json([P.Stop("done")]),
    {"actions": []},
    {"actions": [{"type": "stop", "reason": "done"}], "x": 1},
    {"actions": [{"type": "edit", "path": "a", "old": "x"}]},
    {"actions": [{"type": "edit", "path": "", "old": "x", "new": "y"}]},
    {"actions": [{"type": "read", "path": "a", "start": None, "end": 2}]},
    {"actions": [{"type": "read", "path": "a", "end": 0}]},
    {"actions": [{"type": "verify", "mode": "fast"}]},
    {"actions": [{"type": "stop", "reason": "done", "note": "n" * (P.NOTE_LIMIT + 1)}]},
    {"actions": [{"type": "stop", "reason": "done"}] * (P.MAX_ACTIONS + 1)},
]


@pytest.mark.parametrize("case", CASES)
def test_the_schema_and_the_validator_agree(case):
    by_schema = _check(P.ACTION_SCHEMA, case)
    try:
        P.parse_proposal(case)
        by_code = True
    except P.Malformed:
        by_code = False
    assert by_schema == by_code


def test_the_schema_is_json_and_names_every_action():
    s = json.loads(json.dumps(P.ACTION_SCHEMA))
    consts = {b["properties"]["type"]["const"] for b in s["properties"]["actions"]["items"]["oneOf"]}
    assert consts == set(P.ACTION_TYPES)
