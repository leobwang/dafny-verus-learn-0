# Reference Solution.
"""R15 — Lab β: the roundtrip oracle (Exercises, Python)

Lab β's second oracle asks whether a specification survives a round trip
through English. A policy describes the specification in plain English;
the same policy, shown only the signature and that description, writes a
specification back; the verifier then checks the two implications between
the original and the returned specification. Both proved: the description
carried the whole specification. One failed: it lost (or added) something,
and which one failed says what.

Imports: the Python standard library, the frozen core `fvh` (fvh.tools) and
this package's spectest.py (its given card types, `outcome_r15`,
`render_lemma_r15` and `write_target_r15`), nothing else. Every generated
file is verified through `fvh.tools.run`, never a subprocess, and each run
is judged by `outcome_r15` alone, as in spectest.py.

`ask` is a policy callable: one prompt (a string) in, one reply (a string)
out. In a lab run it is the pinned Qwen model behind fvh's model backend,
and its calls count against R15's Qwen budget (PLAN §4.3: 2 calls per
specification); Claude never judges in it. CI never calls a model: the
acceptance tests pass scripted replies.

How to work this file (Lab β's oracles; PLAN §4.3):
1. Replace the hole, H3py. A Python hole is a function whose body, after its
   docstring, is the one statement `raise NotImplementedError("<item id>")`;
   the tools count holes on the syntax tree, never by searching the text.
2. Run the acceptance tests (harness/tests/r/r15_cases/test_roundtrip.py,
   frozen): `scripts/vcheck harness/r/fvh_r/roundtrip.py`. No solver and no
   model runs in them: they use synthetic cards, scripted replies and a
   stand-in for the instrument runner.
3. Done = `scripts/vcheck --gate harness/r/fvh_r/roundtrip.py` exits 0 (zero
   holes and every acceptance test passing), AND
   `scripts/firsttry.sh R15 --report --strict` exits 0.
4. Stuck for 20 minutes? /tutor R15.

This file ships with exactly 1 hole: H3py, counted from the syntax tree.

Validity (PLAN §4.3: β's hidden truth stays out of every loop). The round
trip reads the specification under test, its card and verifier results;
the hidden verdicts (Hidden/labs/R15/) never enter it, and its results meet
them only after the batch, in the grader container. Redaction: the second
prompt holds the signature and the description, never a clause of the
original specification, so the returned specification cannot be a copy.
"""

import re
from dataclasses import dataclass

from fvh import tools
from fvh_r.spectest import (GATE_R15, CardR15, SpecR15, outcome_r15, render_lemma_r15,
                            write_target_r15)

# =============================================================================
# Given (frozen statements). Read them, never change them.
# =============================================================================

ROUNDTRIP_VERDICTS_R15 = ("equivalent", "weaker", "stronger", "incomparable", "unknown",
                          "unparsed")


@dataclass(frozen=True)
class RoundtripReportR15:
    """roundtrip_r15's account.

    description  the policy's English description (the first reply)
    spec2        the specification parsed from the second reply, or None
    forward      the outcome (spectest's OUTCOMES_R15) of the lemma spec ⟹
                 spec2, or None when it did not run
    backward     the outcome of the lemma spec2 ⟹ spec, or None
    verdict      one of ROUNDTRIP_VERDICTS_R15, read as what spec2 says
                 against spec: "weaker" (it says less), "stronger" (it says
                 more), "equivalent", "incomparable", "unknown" (the verifier
                 settled neither way), "unparsed" (no specification came back)
    calls        the policy calls made
    """

    description: str
    spec2: SpecR15 | None
    forward: str | None
    backward: str | None
    verdict: str
    calls: int


def _signature_r15(card: CardR15) -> str:
    sig = ", ".join(f"{n}: {t}" for n, t in card.params)
    res = ", ".join(f"{n}: {t}" for n, t in card.results)
    if card.lang == "dafny":
        return f"method {card.name}({sig}) returns ({res})"
    return f"fn {card.name}({sig}) -> ({res})"


def _language_r15(card: CardR15) -> str:
    return "Dafny" if card.lang == "dafny" else "Verus"


def describe_prompt_r15(spec: SpecR15) -> str:
    """The first prompt: the declaration's signature and the specification's
    clauses, asking for a plain-English description. It holds nothing of the
    card's header or footer (the clauses name the definitions they use) and
    no implementation (a card has none)."""
    card = spec.card
    lines = [f"Here is a formal specification written in {_language_r15(card)}.", "",
             "Signature:", f"  {_signature_r15(card)}", "", "Requires:"]
    lines += [f"  - {c}" for c in spec.requires] or ["  (none)"]
    lines += ["", "Ensures:"]
    lines += [f"  - {c}" for c in spec.ensures] or ["  (none)"]
    lines += ["", "Describe in plain English, in a few sentences, what this specification "
              "requires of the inputs and what it promises about the results. Name every "
              "parameter and result. Do not write code, formulas or formal notation."]
    return "\n".join(lines) + "\n"


def formalize_prompt_r15(card: CardR15, description: str) -> str:
    """The second prompt: the declaration's signature and the description
    only, asking for one fenced block of `requires:` / `ensures:` lines.
    Raises TypeError when the description is not a string."""
    if not isinstance(description, str):
        raise TypeError("the description is a string (the policy's reply)")
    lang = _language_r15(card)
    lines = [f"Write a formal specification in {lang} for the declaration below.", "",
             "Signature:", f"  {_signature_r15(card)}", "",
             "What it must do, in English:", description.strip(), "",
             "Answer with one fenced code block holding one clause per line: "
             "`requires: <expression>` for each precondition and `ensures: <expression>` for "
             f"each postcondition, each a boolean {lang} expression over the parameters and "
             "results above. Put nothing else in the block."]
    return "\n".join(lines) + "\n"


_FENCE_R15 = re.compile(r"```[^\n]*\n(.*?)```", re.S)
_CLAUSE_R15 = re.compile(r"(requires|ensures)\s*:\s*(\S.*)")


def parse_spec_reply_r15(card: CardR15, text: str) -> SpecR15 | None:
    """The specification in a reply to formalize_prompt_r15: the first fenced
    block (``` with an optional language tag), each non-blank line of it
    `requires: <expression>` or `ensures: <expression>` (surrounding blanks
    stripped), in order. None when the reply is not a string, holds no
    fenced block, a non-blank line of the block is neither form, or the
    block holds no clause."""
    if not isinstance(text, str):
        return None
    m = _FENCE_R15.search(text)
    if m is None:
        return None
    req, ens = [], []
    for line in m.group(1).splitlines():
        s = line.strip()
        if not s:
            continue
        c = _CLAUSE_R15.fullmatch(s)
        if c is None:
            return None
        (req if c.group(1) == "requires" else ens).append(c.group(2).strip())
    if not req and not ens:
        return None
    return SpecR15(card, tuple(req), tuple(ens))


def render_implication_r15(card: CardR15, name: str, hyp_spec: SpecR15,
                           concl_spec: SpecR15) -> str:
    """The whole file of the lemma `hyp_spec ⟹ concl_spec` (render_lemma_r15)
    over the card's parameters followed by its results: requires the
    hypothesis's requires clauses, then its ensures clauses; ensures the
    conclusion's requires clauses, then its ensures clauses. Raises
    ValueError when a specification is of another card."""
    if hyp_spec.card != card or concl_spec.card != card:
        raise ValueError("a specification is of another card")
    over = tuple(card.params) + tuple(card.results)
    return render_lemma_r15(card, name, over,
                            tuple(hyp_spec.requires) + tuple(hyp_spec.ensures),
                            tuple(concl_spec.requires) + tuple(concl_spec.ensures))

# =============================================================================
# Hole
# =============================================================================

# item: R15.H3py
def roundtrip_r15(spec: SpecR15, ask, *, run=None, workdir=None) -> RoundtripReportR15:
    """**H3.** The round trip of one specification (card = spec.card).

    1. description = ask(describe_prompt_r15(spec)).
    2. Build the second prompt, formalize_prompt_r15(card, description).
       Redaction: raise ValueError, before asking, when it contains the text
       of any non-blank requires or ensures clause of `spec` (the
       description quoted the original).
    3. spec2 = parse_spec_reply_r15(card, ask(<the second prompt>)). When it
       is None, the verdict is "unparsed" and nothing runs.
    4. Otherwise write and run two lemmas with render_implication_r15,
       write_target_r15 (into `workdir` when given) and `run("vcheck --gate",
       <path>)`, where `run` is the argument when given, else `fvh.tools.run`
       looked up at the time of the call; forward first:
         forward   spec ⟹ spec2, named `<card name>_Forward` (Dafny) or
                   `<card name>_forward` (Verus);
         backward  spec2 ⟹ spec, named `<card name>_Backward` or
                   `<card name>_backward`;
       each judged by outcome_r15.
    5. The verdict: both proved "equivalent"; forward proved and backward
       failed "weaker" (spec2 says less); backward proved and forward failed
       "stronger" (spec2 says more); both failed "incomparable"; any other
       pair (an outcome unknown) "unknown".
    Returns the RoundtripReportR15 (above), calls = 2 (the two policy
    calls), forward and backward None when nothing ran.
    """
    card = spec.card
    description = ask(describe_prompt_r15(spec))
    prompt = formalize_prompt_r15(card, description)
    for c in tuple(spec.requires) + tuple(spec.ensures):
        if c.strip() and c in prompt:
            raise ValueError(f"redaction: the second prompt quotes the clause {c!r}")
    spec2 = parse_spec_reply_r15(card, ask(prompt))
    if spec2 is None:
        return RoundtripReportR15(description, None, None, None, "unparsed", 2)
    go = run if run is not None else tools.run
    if card.lang == "dafny":
        n1, n2 = f"{card.name}_Forward", f"{card.name}_Backward"
    else:
        n1, n2 = f"{card.name}_forward", f"{card.name}_backward"
    f1 = render_implication_r15(card, n1, spec, spec2)
    f2 = render_implication_r15(card, n2, spec2, spec)
    fwd = outcome_r15(go(GATE_R15, write_target_r15(f1, card.lang, workdir)))
    bwd = outcome_r15(go(GATE_R15, write_target_r15(f2, card.lang, workdir)))
    if fwd == "proved" and bwd == "proved":
        verdict = "equivalent"
    elif fwd == "proved" and bwd == "failed":
        verdict = "weaker"
    elif fwd == "failed" and bwd == "proved":
        verdict = "stronger"
    elif fwd == "failed" and bwd == "failed":
        verdict = "incomparable"
    else:
        verdict = "unknown"
    return RoundtripReportR15(description, spec2, fwd, bwd, verdict, 2)
# triv: return RoundtripReportR15("", spec, "proved", "proved", "equivalent", 2)
