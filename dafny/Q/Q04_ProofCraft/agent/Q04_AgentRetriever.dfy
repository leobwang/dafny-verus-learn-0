/* CONTRACT
goal: close the goals ScaleStrict, HighLimbOfShift and ProductMod, each with standard-library lemma calls only
allowed-files:
  - dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy
acceptance:
  - `scripts/vcheck --gate dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy` exits 0 and prints only the summary line
  - zero tool-counted holes in the allowed file
  - `git diff` shows only the three goals' bodies: each bodyless goal gains a `{ … }` body, and no other line changes (no signature, `requires`, `ensures`, attribute, doc comment or import, no declaration added or removed)
  - each body holds only standard-library lemma calls with their arguments, each call on its own line followed by `// found-by: <rung>`, where `<rung>` is one of `ide`, `grep`, `docs`, `llm`, `memory`: no lemma of your own, no `assert`, `calc` or other statement
  - re-verify after every edit with `scripts/vcheck dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy`; never stack unverified edits
  - `scripts/vaudit --compare expected/Q04_AgentRetriever.audit dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy` reports no difference (an empty report: no finding)
*/
/*!
# Q04 Retriever race — retriever (`/contract Q04`)

What this file ships: three goals, each a lemma about products, quotients or
remainders whose proof is a short chain of standard-library lemma calls. The
module turns off nonlinear arithmetic, so no goal falls to the solver's own
arithmetic. It is green with holes: the three bodyless lemmas are 3
tool-counted holes, and nothing else is reported. Check command:

    scripts/vcheck dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy

Its audit dashboard shows one row per open goal (3 rows as shipped, none once
every goal is closed):

    scripts/vaudit dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy

The file is outside every build: no unit includes it.

Learner follow-up (before and after the contractor delivers; THIS is the
exercise):
1. Before the run: take each goal through your own search ladder, in order
   (IDE hover and go-to-definition, a scoped grep of the pinned library
   source, the library's documentation, a model, memory), timing it, and fill
   the SEARCH LOG block at the end of this file (goal, lemma, rung, minutes).
   Do not edit the goals: the contractor proves them.
2. In a FRESH session, run /contract Q04 on this file: the first live run of
   your contract v0 (CLAUDE.md, below the learner-owned marker).
3. Check the artifact yourself: the gate output, `git diff` (the three bodies
   only), the `// found-by:` lines and `scripts/vaudit`.
4. Fill the COMPARISON block: did each `found-by:` rung match where the lemma
   lives? Did the transcript show a lemma name that does not exist (a
   resolution error), a step that is not a library call, or a statement edit?
   Which of your v0 rules did the run test?
*/
module {:disableNonlinearArithmetic} Q04_AgentRetriever {
  import opened QG_L1_BigNat
  import opened QG_L3_BigNat
  import Mul = Std.Arithmetic.Mul
  import DivMod = Std.Arithmetic.DivMod
  import Power = Std.Arithmetic.Power

  // item: Q04.A1d S5

  // ### The goals. Each proof is a short chain of standard-library lemma calls.

  /** Scaling both sides of a strict inequality by the same positive factor
      keeps it strict. */
  lemma ScaleStrict(x: nat, y: nat, z: nat)
    requires x < y && z > 0
    ensures x * z < y * z

  /** The high part of `a * c + b`, for `b` below `c`, is `a`. */
  lemma HighLimbOfShift(a: nat, b: nat, c: nat)
    requires b < c
    ensures (a * c + b) / c == a

  /** The product of two remainders modulo `m` has the remainder of the
      product. */
  lemma ProductMod(x: nat, y: nat, m: nat)
    requires m > 0
    ensures (x % m) * (y % m) % m == x * y % m
}

// SEARCH LOG (learner-owned; before the contract run)
//   goal | lemma found | rung (ide, grep, docs, llm, memory) | minutes
//   ScaleStrict:
//   HighLimbOfShift:
//   ProductMod:

// COMPARISON (learner-owned; after the contract run)
//   each `found-by:` rung against where the lemma lives:
//   a lemma name that does not exist (a resolution error) in the transcript?
//   a step that is not a library call, or a statement edit?
//   which rules of your contract v0 did the run test?
