/*!
# Q18 — Practice III-C (Reference Solution)

Hole-free reference for `dafny/Q/Q18_PracticeIIIC/std/Q18_PracticeIIIC.dfy`
(author-only; never learner-visible). Same module, imports, names,
statements, item markers and order as the exercise file. The hole is filled:
H1's repair is stable on seeds 1-3 under both bundled solvers and needs no
lemma of its own. The `cfree:` line is the delivered proof the item quotes (its
verdicts move with the file around it, Q18-code-notes §11; never `stable`).

The file is silent: `scripts/vcheck --ref` on its unit prints only the
summary line.
*/
module Q18_PracticeIIIC {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat
  import opened QG_L6_BigNat
  import opened QG_L7_BigNat
  import DivMod = Std.Arithmetic.DivMod
  import Mul = Std.Arithmetic.Mul

  // ===========================================================================
  // Given
  // ===========================================================================

  // The sum of the limbs, each read as a plain number.
  function DigitSum(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else s[0] + DigitSum(s[1..])
  }

  // ===========================================================================
  // Holes
  // ===========================================================================

  // HELPERS (Q18.H1d): lemmas of your own, here.

  // item: Q18.H1d S11
  // uses: proof-split, lemma-call
  // pair: Q18.H1v
  // form: stable
  // cfree: { if |s| > 0 { CastOut(s[1..]); var t := ToNat(s[1..]); assert BASE * t == t + (BASE - 1) * t; } }
  /** **H1.** A repair that must hold under a solver swap and a seed
      sweep. Casting out (BASE - 1)s: the value of a limb sequence and the
      sum of its limbs leave the same remainder modulo BASE - 1. A
      contractor delivered this proof for the lemma below and reported it
      verified:

          {
            if |s| > 0 {
              CastOut(s[1..]);
              var t := ToNat(s[1..]);
              assert BASE * t == t + (BASE - 1) * t;
            }
          }

      Paste it as the body and run `scripts/vcheck --brittleness --solvers
      dafny/Q/Q18_PracticeIIIC/std`; fill the BRITTLENESS table below from
      what the sweep prints. The contractor's green run was on another file,
      and a verdict moves with the text around a proof: pasted here, the
      delivered proof may fail in some rows or in all of them. Then repair
      it: a proof of the same statement that verifies in every row of the
      same sweep and carries no resource attribute (no `{:rlimit}`,
      `{:resource_limit}`, `{:timeLimit}` or `@ResourceLimit`). Which facts does the delivered proof leave the
      solver to find on its own, and which library lemmas state them? */
  lemma CastOut(s: seq<nat>)
    ensures ToNat(s) % (BASE - 1) == DigitSum(s) % (BASE - 1)
    decreases |s|
  {
    if |s| > 0 {
      var d, t, l, m := s[0], ToNat(s[1..]), DigitSum(s[1..]), BASE - 1;
      CastOut(s[1..]);
      assert t % m == l % m;
      Mul.LemmaMulIsDistributiveAddOtherWay(t, m, 1);
      Mul.LemmaMulBasics(t);
      assert BASE * t == m * t + t;
      DivMod.LemmaModMultiplesVanish(t, d + t, m);
      assert ToNat(s) % m == (d + t) % m;
      DivMod.LemmaAddModNoopRight(d, t, m);
      DivMod.LemmaAddModNoopRight(d, l, m);
      assert (d + t) % m == (d + l) % m;
    }
  }

  // BRITTLENESS (learner-owned): the delivered proof, then yours, from the sweep.
  //   row (solver, seed)   delivered: verdict, resource count   yours: verdict, resource count
  //   4.12.1 seed 1
  //   4.12.1 seed 2
  //   4.12.1 seed 3
  //   4.14.1 seed 1
  //   4.14.1 seed 2
  //   4.14.1 seed 3
}

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line.
  brief 10 · H1 brittleness repair 40 (H1d 25, H1v 15) · H2 the capstone
  round 110 (blueprint 25, statements 25, reviewer run 10, co-developer run
  20, adversarial plant 15, CLI and retrospective 15) · H3 gate v2 and the
  adversarial round 85 (gate 60, specimens 10, the adversarial gate run 15) ·
  Lab 3: case study 150 (pre-registration 30, /grade-paper 10, run setup 20,
  analysis 50, report 40) · FP rate 20 · TRUST.md and contract v2 30 ·
  proposal 60 · /review-code 20 · --post 10 · cards 30 · ledger and
  calibration 10 · total 575 (+ tier viva 30)
Then run `scripts/firsttry.sh Q18 --record`.
*/
