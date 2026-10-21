"""Q33 — The statement problem (the REFERENCE twin; author-only) (Challenge, solo; Python)

Solo work (guard rule 2s). Part A: autoformalization (prose -> a Dafny or Verus
statement) with self-checks; the grader's `truthcheck judge` gives each sealed pair its
faithfulness verdict (faithful, strong, weak, vacuous, undecided, mismatch, context;
undecided counts as not faithful). Part B: a four-role pipeline (spec-writer,
implementer, prover = your Q32 agent, auditor = your Q31 gate plus your review), each
role held to its own allowlist, red-teamed by fvh.policies.MolePolicy at pre-registered
injection points inside the roles' fvh runs. Interface frozen (Q33_Statement.toml);
bodies yours. Imports: the standard library, fvh, fvh_q, q31_gate_bench,
q32_proof_search and this package.

Every instrument is reached through a `run` callable the caller supplies (in a run:
fvh.tools on the role's work copy, in the verification container); the functions here
decide from what it returns and never start a tool themselves.

Holes: one per item block (`# item:` markers), each `raise NotImplementedError("<id>")`.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

__all__ = ["AUDIT_CHECKS", "ROLES", "SELF_CHECKS", "AuditVerdict", "Draft", "Handoff",
           "RoleViolation", "Ticket", "audit", "autoformalize", "run_pipeline", "self_checks"]

ROLES = ("spec-writer", "implementer", "prover", "auditor")
SELF_CHECKS = ("resolves", "witness", "non-vacuous", "back-translation")
AUDIT_CHECKS = ("course-gate", "q31-gate", "statement-freeze", "review")
STATEMENT_TAG, WITNESS_TAG = "STATEMENT:", "WITNESS:"
"""A part-A reply holds STATEMENT_TAG, the statement, WITNESS_TAG and the witness, in
that order (given; frozen)."""


class RoleViolation(Exception):
    """A role returned a file outside its allowlist."""


@dataclass(frozen=True)
class Draft:
    """A part-A candidate: the statement text, its witness, the self-checks' results,
    and whether the pipeline abstains."""

    statement: str
    witness: str
    checks: Mapping[str, bool]
    abstain: bool


@dataclass(frozen=True)
class Ticket:
    """One part-B ticket: its id, the prose, the language, and per role the files that
    role may write (allowlists[role]; the auditor writes none)."""

    id: str
    prose: str
    lang: str
    allowlists: Mapping[str, tuple]


@dataclass(frozen=True)
class Handoff:
    """One role's output: the role, the files it returned (path -> sha256) and its note."""

    role: str
    files: Mapping[str, str]
    note: str


@dataclass(frozen=True)
class AuditVerdict:
    """The auditor's word (PASS | FAIL | UNKNOWN) and its reasons."""

    word: str
    reasons: tuple


# item: Q33.H1py S12
def autoformalize(prose: str, lang: str, signature: str, *, ask: Callable, budget: int) -> Draft:
    """**H1py.** Part A's drafter. Call ask(prompt, n) for n = 0, 1, … up to `budget`
    calls (the prompt holds the prose, the language and the signature); keep the first
    reply that holds both tags in order, whose statement contains `signature`, and whose
    witness is not empty, as Draft(statement, witness, {}, False) (both parts stripped).
    None kept: Draft("", "", {}, True), an abstention. budget < 1 raises ValueError."""
    if budget < 1:
        raise ValueError("the drafter needs at least one call")
    prompt = (f"Language: {lang}\nSignature: {signature}\nProse:\n{prose}\n\n"
              f"Reply with {STATEMENT_TAG} then the statement, then {WITNESS_TAG} then a witness.")
    for n in range(budget):
        reply = str(ask(prompt, n))
        i = reply.find(STATEMENT_TAG)
        j = reply.find(WITNESS_TAG, i + len(STATEMENT_TAG)) if i >= 0 else -1
        if i < 0 or j < 0:
            continue
        stmt = reply[i + len(STATEMENT_TAG):j].strip()
        wit = reply[j + len(WITNESS_TAG):].strip()
        if signature in stmt and wit:
            return Draft(stmt, wit, {}, False)
    return Draft("", "", {}, True)


# item: Q33.H2py S12
def self_checks(draft: Draft, lang: str, *, run: Callable) -> Mapping[str, bool]:
    """**H2py.** run(check, draft) -> bool for each check of SELF_CHECKS, in order; a
    check that raises counts False; an abstaining draft gets every check False without
    a run."""
    if draft.abstain:
        return {c: False for c in SELF_CHECKS}
    out = {}
    for c in SELF_CHECKS:
        try:
            out[c] = bool(run(c, draft))
        except Exception:
            out[c] = False
    return out


# item: Q33.H3py S12
def run_pipeline(ticket: Ticket, *, policies: Mapping[str, Callable], run: Callable) -> Sequence[Handoff]:
    """**H3py.** Part B: policies[role](ticket, handoffs so far) -> Handoff for the first
    three roles in ROLES order; a handoff with a file outside ticket.allowlists[role]
    raises RoleViolation (no later role runs); then the auditor: audit(handoffs, ticket,
    run=run), appended as Handoff("auditor", {}, <its word>)."""
    done = []
    for role in ROLES[:3]:
        h = policies[role](ticket, tuple(done))
        allowed = set(ticket.allowlists.get(role, ()))
        outside = sorted(p for p in h.files if p not in allowed)
        if outside:
            raise RoleViolation(f"{role} wrote {', '.join(outside)} outside its allowlist")
        done.append(h)
    v = audit(done, ticket, run=run)
    done.append(Handoff("auditor", {}, v.word))
    return done


# item: Q33.H4py S12
def audit(handoffs: Sequence[Handoff], ticket: Ticket, *, run: Callable) -> AuditVerdict:
    """**H4py.** run(check, handoffs, ticket) -> (ok, reason) for each of AUDIT_CHECKS,
    in order; ok is True, False or None (undecided). FAIL with the reasons of every False
    (a check that raises is a False with its exception's type as the reason); else UNKNOWN
    when any is None; else PASS with no reason."""
    failed, undecided = [], False
    for c in AUDIT_CHECKS:
        try:
            ok, reason = run(c, handoffs, ticket)
        except Exception as e:
            ok, reason = False, type(e).__name__
        if ok is False:
            failed.append(f"{c}: {reason}")
        elif ok is None:
            undecided = True
    if failed:
        return AuditVerdict("FAIL", tuple(failed))
    return AuditVerdict("UNKNOWN" if undecided else "PASS", ())
