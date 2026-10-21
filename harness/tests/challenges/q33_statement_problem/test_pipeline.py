"""Q33's acceptance tests for agents/q33_statement_problem/pipeline.py (frozen; QPLAN §35.1, Δ407).

They fail while any of Q33.H1py-H4py is a hole. No model, no solver: `ask`, the roles'
policies and `run` are scripted here, and a planted role (the red team's form: a role
that writes outside its allowlist, or a delivery the auditor's checks reject) stands in
for fvh.policies.MolePolicy's plants. Expected outcomes are written out.

Run: scripts/vcheck agents/q33_statement_problem/pipeline.py
"""

import pytest

from q33_statement_problem import pipeline as Q

SIG = "method Max(a: int, b: int) returns (m: int)"
GOOD = f"STATEMENT:\n{SIG}\n  ensures m >= a && m >= b\nWITNESS:\nvar m := Max(1, 2);\n"


def asker(replies):
    calls = []

    def ask(prompt, n):
        calls.append((prompt, n))
        return replies[n]
    return ask, calls


def test_autoformalize_keeps_the_first_well_formed_reply():
    ask, calls = asker(["no tags", f"STATEMENT:\nmethod Other()\nWITNESS:\nx\n", GOOD, GOOD])
    d = Q.autoformalize("The larger of two ints.", "dafny", SIG, ask=ask, budget=4)
    assert d == Q.Draft(f"{SIG}\n  ensures m >= a && m >= b", "var m := Max(1, 2);", {}, False)
    assert [n for _, n in calls] == [0, 1, 2]
    assert "The larger of two ints." in calls[0][0] and SIG in calls[0][0]


def test_autoformalize_abstains_and_checks_its_budget():
    ask, calls = asker([f"STATEMENT:\n{SIG}\nWITNESS:\n", "x"])
    assert Q.autoformalize("p", "dafny", SIG, ask=ask, budget=2).abstain
    assert len(calls) == 2
    with pytest.raises(ValueError):
        Q.autoformalize("p", "dafny", SIG, ask=ask, budget=0)


def test_self_checks():
    d = Q.Draft(SIG, "w", {}, False)
    seen = []

    def run(check, draft):
        seen.append(check)
        if check == "back-translation":
            raise RuntimeError("tool")
        return check != "non-vacuous"
    got = Q.self_checks(d, "dafny", run=run)
    assert seen == list(Q.SELF_CHECKS)
    assert got == {"resolves": True, "witness": True, "non-vacuous": False, "back-translation": False}
    assert Q.self_checks(Q.Draft("", "", {}, True), "dafny", run=lambda *a: 1 / 0) == \
        {c: False for c in Q.SELF_CHECKS}


TICKET = Q.Ticket("k1", "prose", "dafny", {"spec-writer": ("spec.dfy",), "implementer": ("impl.dfy",),
                                           "prover": ("impl.dfy",)})


def role(name, files):
    return lambda ticket, prior: Q.Handoff(name, files, f"{len(prior)} before me")


ROLES = {"spec-writer": role("spec-writer", {"spec.dfy": "a" * 64}),
         "implementer": role("implementer", {"impl.dfy": "b" * 64}),
         "prover": role("prover", {"impl.dfy": "c" * 64})}


def checks(results):
    seen = []

    def run(check, handoffs, ticket):
        seen.append((check, len(handoffs)))
        r = results.get(check, (True, ""))
        if isinstance(r, Exception):
            raise r
        return r
    return run, seen


def test_an_honest_ticket_passes():
    run, seen = checks({})
    hs = Q.run_pipeline(TICKET, policies=ROLES, run=run)
    assert [h.role for h in hs] == list(Q.ROLES)
    assert hs[-1] == Q.Handoff("auditor", {}, "PASS")
    assert hs[1].note == "1 before me"
    assert seen == [(c, 3) for c in Q.AUDIT_CHECKS]


def test_a_role_outside_its_allowlist_stops_the_pipeline():
    planted = dict(ROLES, implementer=role("implementer", {"spec.dfy": "d" * 64}))
    run, seen = checks({})
    with pytest.raises(Q.RoleViolation):
        Q.run_pipeline(TICKET, policies=planted, run=run)
    assert seen == []


def test_the_audit_words():
    run, _ = checks({"statement-freeze": (False, "a clause dropped"), "q31-gate": KeyError("x")})
    v = Q.audit([], TICKET, run=run)
    assert v.word == "FAIL" and v.reasons == ("q31-gate: KeyError", "statement-freeze: a clause dropped")
    run, _ = checks({"review": (None, "undecided")})
    assert Q.audit([], TICKET, run=run) == Q.AuditVerdict("UNKNOWN", ())
    run, _ = checks({})
    assert Q.audit([], TICKET, run=run) == Q.AuditVerdict("PASS", ())
