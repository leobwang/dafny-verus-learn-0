/*!
# Q09 — Internals III: brittleness, forensics, gate core (Reference Solution)

Hole-free reference for `dafny/Q/Q09_InternalsIII/std/Q09_InternalsIII.dfy`
(author-only; never learner-visible). Same module, imports, names,
statements, item markers and order as the exercise file. Every hole is
filled and every verdict switch is enabled; the verdict answers are in
`Solutions/slots/Q09.slots`, their hashes in `expected/Q09.pins`. The
BRITTLENESS table of H1 is filled from the module lane's own runs
(`Solutions/plans/Q09-code-notes.md` §2).

The file is silent: `scripts/vcheck --ref` on its unit prints only the
summary line. Every output the module quotes is pinned: the count pins in
`expected/Q09.counts`, the statement freeze in `expected/Q09.freeze` and the
WRITE-card failure demos by their in-file `// EXPECT` lines. No declaration
carries a resource attribute (H1 carries the `stable` form).
*/
module Q09_InternalsIII {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import Mul = Std.Arithmetic.Mul

  // ===========================================================================
  // The prediction block.
  // ===========================================================================

  // item: Q09.P1d S11 verdict
  /** **P1.** A solver swap. In this module's options (nonlinear arithmetic
      on), this attempt:

          lemma ProductBelowSquare(x: nat, y: nat, n: nat)
            requires x < Pow(n) && y < Pow(n)
            ensures x * y < Pow(n) * Pow(n)
          {
            var p := Pow(n);
            assert x * y <= x * p;
          }

      is verified at the pinned resource limit with the pinned Z3 (4.12.1),
      and again with the other Z3 bundled with Dafny (4.14.1:
      `scripts/vcheck --solver 4.14.1`). What does each run give?
      Answer form: `D:<v> <v>` (the pinned solver first, then the other),
      each v one of `ok` (verifies), `fail` (a verification error),
      `timeout` (an inconclusive or out-of-resource run) or `err:<stage>`
      (refused before verification; the stage as `scripts/vcheck` prints
      it). */
  // CHECK P1d

  // item: Q09.P2dv S11 verdict
  /** **P2.** Seeds. Two attempts, each with a quantified step whose trigger
      is the plain power term.

        Dafny, run in the module options of
        dafny/Q/Q09_InternalsIII/std/Q09_Triggers.dfy (`module
        {:disableNonlinearArithmetic} Q09_Triggers`, the same imports):
          lemma PowGrowsByBase(m: nat, n: nat)
            requires m < n
            ensures Pow(m) * BASE <= Pow(n)
            decreases n - m
          {
            forall k: nat {:trigger Pow(k)} ensures Pow(k) * BASE <= Pow(k + 1) {
              PowAdd(k, 1);
            }
            if m + 1 < n {
              PowGrowsByBase(m + 1, n);
            }
          }

        Verus, run in this module's crate:
          pub proof fn lemma_weight_strict_mono(m: nat, n: nat)
              requires
                  m < n,
              ensures
                  weight(m) < weight(n),
              decreases n - m,
          {
              assert forall|k: nat| #[trigger] weight(k) < weight(k + 1) by {
                  lemma_weight_succ(k);
                  lemma_weight_mono(0, k);
                  lemma_weight_zero();
              }
              if m + 1 < n {
                  lemma_weight_strict_mono(m + 1, n);
              }
          }

      Each is run through `scripts/vcheck --brittleness` (seeds 1, 2 and 3).
      What is its verdict under each seed, and does the command's first line
      end with `stable` (write `stable`) or `NOT stable` (write `unstable`)?
      Answer form: `D:<v>,<v>,<v>,<s> V:<v>,<v>,<v>,<s>`, each v as in P1
      (`ok`, `fail`, `timeout` for an inconclusive or out-of-resource run,
      `err:<stage>`) and each s `stable` or `unstable`. */
  // CHECK P2dv

  // item: Q09.P3dv S9 verdict
  /** **P3.** Machine records. Each file below holds one proved lemma and
      one open hole, and is run as `scripts/vcheck --json <file>`.

        Dafny, p3.dfy:
          module P3 {
            lemma Proved(x: nat)
              ensures x + 0 == x
            {
            }

            lemma Open(x: nat)
              ensures x * 1 == x
          }

        Verus, p3.rs:
          use vstd::prelude::*;

          verus! {

          proof fn proved(x: nat)
              ensures
                  x + 0 == x,
          {
          }

          proof fn open_one(x: nat)
              ensures
                  x * 1 == x,
          {
              #[verifier::proof_note("P3")] assume(false);
          }

          } // verus!

      What is the `verdict` field of each JSON document, and is its
      `verified_count` a number or `null`?
      Answer form: `D:<verdict> <number|null> V:<verdict> <number|null>`,
      each <verdict> one of the words that field takes: `verified`,
      `failed`, `inconclusive`, `refused`, `killed(memory)`, `error`. */
  // CHECK P3dv

  // ===========================================================================
  // Worked example
  // ===========================================================================

  // item: Q09.W1d S11
  // **W1.** Measuring a given proof: layer L4's `AddCCorrect`. A proof is
  // stable when it verifies under seeds 1-3 and, in Dafny, under both Z3
  // binaries bundled with the pinned Dafny. The sweep, then the same sweep
  // with JSON for the counts:
  //     scripts/vcheck --brittleness --solvers dafny/given/Q/QG_L4_BigNat.dfy
  //     scripts/vcheck --brittleness --solvers --json dafny/given/Q/QG_L4_BigNat.dfy
  // The first prints one verdict per row (`4.12.1 seed 1: verified · …`)
  // and ends with `stable`; the JSON's `spread` gives, per symbol and per
  // solver, the smallest and the largest resource count of its rows. The
  // filled BRITTLENESS table of `QG_L4_BigNat.AddCCorrect` (captured
  // 2026-10-06 at the pins; your counts are those of your runs):
  //     solver   seed 1     seed 2     seed 3     resource counts
  //     4.12.1   verified   verified   verified   101,608..109,776 (CV 3.2%)
  //     4.14.1   verified   verified   verified   158,253..160,400 (CV 0.6%)
  // Read it row by row: the verdicts agree in every row, so the proof is
  // stable; the counts move between seeds, and the two solvers' counts are
  // not comparable (they measure two programs). A spread above 20% would be
  // flagged, never gated.

  // ===========================================================================
  // WRITE cards (each: a success here, a pinned failure demo in specimens/Q09/)
  // ===========================================================================

  // item: Q09.C1d S11 write:proof-split
  /** ### C1 — card: splitting a proof into small steps.
      Jurisdiction: a nonlinear goal the solver must find on its own is the
      kind of step whose cost moves with the seed and the solver; split it
      into named library facts, each small, and the cost becomes small and
      steady. Success: `ThreeLimbProduct`, four facts from
      `Std.Arithmetic.Mul`, each about one product. Failure:
      specimens/Q09/card-c1d.dfy.specimen (the same lemma, the whole product
      left to the solver in one step). Measure both with
      `scripts/vcheck --json` and compare their resource counts. */
  lemma ThreeLimbProduct(x: nat, y: nat, z: nat)
    requires x < BASE && y < BASE && z < BASE
    ensures x * y * z < BASE * BASE * BASE
  {
    Mul.LemmaMulInequality(x, BASE, y);            // x * y <= BASE * y
    Mul.LemmaMulLeftInequality(BASE, y, BASE);     // BASE * y < BASE * BASE
    Mul.LemmaMulInequality(x * y, BASE * BASE, z); // x * y * z <= BASE * BASE * z
    Mul.LemmaMulLeftInequality(BASE * BASE, z, BASE);
  }

  // item: Q09.C2d S11 write:trigger-rewrite
  /** ### C2 — card: moving a trigger.
      Jurisdiction: a quantified fact is used only at the terms that match
      its trigger. If each instance creates a new term of the trigger's
      shape, the instances feed themselves, upward, and never reach the one
      the proof needs; moved to a term that no instance creates, the trigger
      matches only the terms the proof already holds. Success:
      `ZerosNonEmpty` triggers its step on `Zeros(k + 1)`. Failure:
      specimens/Q09/card-c2d.dfy.specimen (the same step triggered on
      `Zeros(k)`). */
  opaque function Zeros(n: nat): seq<nat>
  {
    if n == 0 then [] else [0] + Zeros(n - 1)
  }

  lemma ZerosSucc(k: nat)
    ensures |Zeros(k + 1)| == |Zeros(k)| + 1
  {
    reveal Zeros();
  }

  lemma ZerosNonEmpty(m: nat)
    ensures |Zeros(m + 1)| > 0
  {
    forall k: nat {:trigger Zeros(k + 1)} ensures |Zeros(k + 1)| == |Zeros(k)| + 1 {
      ZerosSucc(k);
    }
  }

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: Q09.H1d S11
  // uses: proof-split
  // pair: Q09.H1v
  // form: stable
  /** **H1.** Repair pair, Dafny: a product of two numbers below `Pow(n)` is
      below `Pow(n) * Pow(n)`. P1's attempt (one assertion) times out under
      the pinned solver and verifies under the other, so it is not stable.
      Reference: the same chain made of named facts of `Std.Arithmetic.Mul`,
      one per step: `p * y < p * p` by `LemmaMulLeftInequality(p, y, p)`;
      for `x == 0` the product is 0 (`LemmaMulBasics`) and `p * p` is
      positive (`LemmaMulStrictlyPositive`); otherwise `x * y < x * p`
      (`LemmaMulLeftInequality(x, y, p)`) and `x * p < p * p`
      (`LemmaMulStrictInequality(x, p, p)`). It verifies in all six rows,
      with no resource attribute. */
  lemma ProductBelowSquare(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(n) * Pow(n)
  {
    var p := Pow(n);
    Mul.LemmaMulLeftInequality(p, y, p);
    if x == 0 {
      Mul.LemmaMulBasics(y);
      Mul.LemmaMulStrictlyPositive(p, p);
    } else {
      Mul.LemmaMulLeftInequality(x, y, p);
      Mul.LemmaMulStrictInequality(x, p, p);
    }
  }
  /* BRITTLENESS (reviewed, never gated). P1's attempt as the body, in this
     module, through scripts/vcheck --brittleness --solvers (--json for the
     counts):
       solver   seed 1        seed 2        seed 3        resource counts
       4.12.1   inconclusive  inconclusive  inconclusive  5,006,649..5,006,650
       4.14.1   verified      verified      verified      38,789..38,790
     The repair above, the same sweep:
       4.12.1   verified      verified      verified      11,090..11,091
       4.14.1   verified      verified      verified      11,203..11,204
  */
}

// =============================================================================
// ## Exercise (AGENTIC) — the red-teamed contractor (`/contract Q09`)
// =============================================================================
// Files: dafny/Q/Q09_InternalsIII/agent/Q09_AgentRedTeam.dfy and
// verus/q/q09_internals_iii/src/agent.rs. Shipped state: green, with exactly
// 4 tool-counted holes each (the four lemmas of its BANK) and an empty
// REFUTATIONS section. Check commands:
//
//     scripts/vcheck dafny/Q/Q09_InternalsIII/agent/Q09_AgentRedTeam.dfy
//     scripts/vcheck verus/q/q09_internals_iii/src/agent.rs
//
// Steps (after this file is done):
// 1. Before the run: fill each agent file's DIAGNOSIS block, copy each file
//    to research/q09_bank.dfy and research/q09_bank.rs, and commit them.
// 2. In a FRESH session, run /contract Q09 on each agent file.
// 3. Audit the run: the transcript, `git diff`, the freeze check against the
//    committed bank and `scripts/vaudit`, and fill each file's AUDIT block.
// 4. Then write contract v1 by hand, below the learner marker of CLAUDE.md.
// The lesson: a contractor that is told the truth about its goal can still
// be handed a goal that is false; the gate cannot say which, the contract
// must say what to do then, and only your audit can say whether it did.

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line.
  setup 5 · test-out 10 · read 45 · worked 20 · predicts 20 · repair pair 25 ·
  forensics 40 · gate core 40 · MDE on paper 10 · red-team + contract v1 25 ·
  EVAL.md v1 10 · paper 15 · exit + explain-back 25 · calib 5 · total 295
  (+ tier viva 30)
*/
