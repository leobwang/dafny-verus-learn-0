/*!
# Q18 — Practice III-C (Exercises)

Imports: the given BigNat spine, layers L1 (`QG_L1_BigNat`) to L7
(`QG_L7_BigNat`), all opened, and Dafny's `Std.Arithmetic.DivMod` and
`Std.Arithmetic.Mul` (as `DivMod` and `Mul`, not opened); nothing else: no
earlier exercise file. The layers are frozen and complete; read them, never
edit them. Nonlinear arithmetic is on in this module.

How to work this file (the hard practice tier):
1. Predictions first: Q18's predictions are the four build-tool deliveries
   of specimens/Q18/ (P1-P4, two per language); fill their slots (the
   answers go in slots/Q18.slots) and record the first tries with
   `scripts/firsttry.sh Q18 --check` before you run anything they are about.
2. The item ships its statement and a delivered proof (in its docstring),
   nothing else. Lemmas of your own go in the item's `HELPERS` area, above
   the item, each with a statement of your own and its proof.
3. Done = `scripts/vcheck --gate dafny/Q/Q18_PracticeIIIC/std` prints only the
   summary line and exits 0, `scripts/vaudit dafny/Q/Q18_PracticeIIIC/std`
   reports no finding, `scripts/vcheck --brittleness --solvers
   dafny/Q/Q18_PracticeIIIC/std` ends with `stable`, AND
   `scripts/firsttry.sh Q18 --report --strict` exits 0.
4. Stuck for 20 minutes? /tutor Q18.

This file ships with exactly 1 hole (H1), counted by `scripts/vcheck`. Q18 as
a whole ships 7 holes (1 here, 1 in the Verus crate
verus/q/q18_practice_iiic/src/lib.rs, and 5 Python holes in the gate
harness/q/fvh_q/gate/gate_v2.py); 4 predictions (the specimens); and no exit
file (the hard tier's exit is the verifier part plus the reviews). The
capstone's statements are yours to write, in research/q18_statements.dfy and
research/q18_statements.rs; the agent files are the capstone's proof work.
Commit every prediction BEFORE you run anything it is about, open later
files, or read CI, the registry or the plan: their checks and headers give
some predictions away.

Item kinds: P prediction (a slot, in a specimen) · H one-hole item · A agent
item (the agent files and Lab 3's runs). Slots: a verdict switch
`// SLOT: CHECK <item>` in a specimen takes its answer in slots/Q18.slots
(`P1d = ???` → `P1d = "<answer>"`). Fill the slot, record the first try, and
only then enable it: `// SLOT: CHECK P1d` becomes `// CHECK P1d`.
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
  // HOLE: this lemma has no body; write `{ … }` below the decreases line.
  // Hint: one step of the induction is a remainder of a sum with a multiple
  //    of the modulus in it; DivMod has a lemma for each half of that step.

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
