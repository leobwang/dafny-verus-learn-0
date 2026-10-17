/*!
# Q12 — Practice I-C + Lab 1: the practice block (Exercises)

Imports: the given BigNat spine, layers L1-L4 (`QG_L1_BigNat` …
`QG_L4_BigNat`), nothing else: no earlier exercise file. The layers are
frozen and complete; read them, never edit them. This module's import list
is part of what it states: keep it as shipped. This module keeps nonlinear
arithmetic on.

How to work this file (the practice block of Q12; the order is the
module's):
1. Predictions first: the six stage specimens specimens/Q12/P1d.dfy.specimen
   … P6v.rs.specimen (their headers say how; the answers go in
   slots/Q12.slots). Record the first tries with
   `scripts/firsttry.sh Q12 --check` before you run anything they are about.
2. The retry client (H1, H2 in harness/q/fvh_q/retry.py), then H3 below and
   H3 in verus/q/q12_practice_ic/src/lib.rs.
3. Done = `scripts/vcheck --gate dafny/Q/Q12_PracticeIC/std` prints only the
   summary line and exits 0, `scripts/vaudit dafny/Q/Q12_PracticeIC/std`
   reports no finding, AND `scripts/firsttry.sh Q12 --report --strict` exits
   0. The unit's gate covers this file and
   dafny/Q/Q12_PracticeIC/std/Q12_Lab1Hand.dfy (the Lab 1 hand part) together.
4. Stuck for 20 minutes? /tutor Q12.

This file ships with exactly 1 hole: H3, counted by `scripts/vcheck`; its
unit also holds Q12_Lab1Hand.dfy, which ships with 4 holes (H4-H7). Q12 as a
whole ships 18 holes in its exercise and harness files (Dafny 5: H3 here and
H4-H7 in Q12_Lab1Hand.dfy; Verus 5: H3 in verus/q/q12_practice_ic/src/lib.rs
and H4-H7 in src/lab1_hand.rs; Python 8: H1, H2 in
harness/q/fvh_q/retry.py, H8-H11 in harness/q/fvh_q/policies.py, H12, H13 in
harness/q/fvh_q/report.py); 6 predictions (the stage specimens); and 2 exit
items (the exit files ship 1 + 1 holes). Commit every prediction BEFORE you
run anything it is about, open later files, or read CI, the registry or the
plan: their checks and headers give some predictions away.

Item kinds: P prediction (a slot) · H one-hole item · X exit item (the exit
files) · A agent run (tools/Q12/holecount.py) and the Lab 1 runs. Slots: a
specimen's verdict switch `// SLOT: CHECK <item>` takes its answer in
slots/Q12.slots (`P1d = ???` → `P1d = "<answer>"`). Fill a slot, record the
first try, and only then enable it: `// SLOT: CHECK P1d` becomes
`// CHECK P1d`.

Exit (closed book): dafny/Q/Q12_PracticeIC/exit/Q12_Exit.dfy and
verus/q/q12_practice_ic/src/exit.rs, scored once by
`scripts/firsttry.sh Q12 --exit` (threshold 1 of the 2).

The intro-practice tier viva (/viva Q12) examines Q10, Q11 and Q12.
*/
module Q12_PracticeIC {
  // specfreeze: frozen-imports
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  // ===========================================================================
  // The prediction block. Q12's six predictions are the stage specimens
  // specimens/Q12/P1d.dfy.specimen … P6v.rs.specimen; commit every one of them
  // before you read past this block, and record the first tries:
  //     scripts/firsttry.sh Q12 --check
  // ===========================================================================

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: Q12.H3d S11
  // uses: fuel
  /** **H3.** A literal, normalized. `Normalize` (layer L2) strips the most
      significant zero limbs, one call per limb. Prove the instance below
      from the definitions: unfold just enough of it. */
  lemma NormalizeLiteral()
    ensures Normalize([5, 0, 0, 0]) == [5]
  // Hint: each unfolding of `Normalize` asks for a shorter prefix of the
  //    literal; the verifier must see that prefix as a literal too.
}
