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
# Q04 Retriever race — retriever (Reference Solution)

Hole-free reference for `dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy`
(author-only; never learner-visible): the three goals closed by library calls,
each with its receipt, and the reference section under the loud heading at the
end. Silent under `scripts/vcheck --ref`.
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
  {
    Mul.LemmaMulStrictInequality(x, y, z);  // found-by: grep
  }

  /** The high part of `a * c + b`, for `b` below `c`, is `a`. */
  lemma HighLimbOfShift(a: nat, b: nat, c: nat)
    requires b < c
    ensures (a * c + b) / c == a
  {
    DivMod.LemmaFundamentalDivModConverse(a * c + b, c, a, b);  // found-by: grep
  }

  /** The product of two remainders modulo `m` has the remainder of the
      product. */
  lemma ProductMod(x: nat, y: nat, m: nat)
    requires m > 0
    ensures (x % m) * (y % m) % m == x * y % m
  {
    DivMod.LemmaMulModNoop(x, y, m);  // found-by: grep
  }

  // ===========================================================================
  // — clearly marked: everything below answers the agentic file —
  // ===========================================================================
  // The reference delivery is the three bodies above, one library call each:
  // `Mul.LemmaMulStrictInequality` (a strict inequality times a positive
  // factor), `DivMod.LemmaFundamentalDivModConverse` (a value written as
  // `q * d + r` with `r < d` has quotient `q`), `DivMod.LemmaMulModNoop` (the
  // remainder of a product of remainders). The module's
  // `{:disableNonlinearArithmetic}` keeps the solver from closing a goal by
  // its own arithmetic: each empty body fails every shipped seed (ScaleStrict
  // needs the module attribute as its lever; the other two are inconclusive
  // even with every lever stripped; Solutions/plans/Q04-code-notes.md §7).
  //
  // Soft spots a contractor tends to hit, each one the COMPARISON block should
  // catch:
  //   - an invented lemma name (for example `LemmaMulStrictlyIncreases`): a
  //     resolution error in the transcript, then a retry under another name;
  //   - a step that is not a library call: an `assert`, a `calc`, or a
  //     `{:disableNonlinearArithmetic false}` edit, which the gate may accept
  //     and the contract's body rule does not;
  //   - a helper lemma of its own (a declaration the `git diff` shows);
  //   - `// found-by: memory` (or `llm`) on every line, whatever the transcript
  //     shows: check each rung against the transcript's own search commands.
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
