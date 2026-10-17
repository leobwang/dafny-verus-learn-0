/*!
# Q09 — Internals III: the trigger test-out (Exercises)

First: commit every prediction of Q09 and record the first tries
(`scripts/firsttry.sh Q09 --check`) BEFORE you read the rest of this file.
The module's prediction block is in
dafny/Q/Q09_InternalsIII/std/Q09_InternalsIII.dfy, and one of its
predictions is about a proof of the lemma below.

Imports: the given BigNat spine, layers L1-L4 (`QG_L1_BigNat` …
`QG_L4_BigNat`), nothing else. The layers are frozen and complete; read
them, never edit them. This module turns nonlinear arithmetic off for
itself.

How to work this file:
1. Test-out, closed book: T1 below, after every prediction of the module is
   recorded and before any reading, without its hints.
   `scripts/firsttry.sh Q09 --check` records its first try, and refuses to
   while any prediction of the module is unrecorded. If T1 here and T1 in
   the Verus file (verus/q/q09_internals_iii/src/lib.rs) both pass on that
   first try, you may skip the chapter section on matching loops.
2. Done = `scripts/vcheck --gate dafny/Q/Q09_InternalsIII/std` prints only
   the summary line and exits 0, `scripts/vaudit dafny/Q/Q09_InternalsIII/std`
   reports no finding, `scripts/vcheck --brittleness --solvers
   dafny/Q/Q09_InternalsIII/std` ends with `stable`, AND
   `scripts/firsttry.sh Q09 --report --strict` exits 0. T1 counts only with
   an explicit trigger on its quantified step and no resource attribute.
3. Stuck for 20 minutes? /tutor Q09.

This file ships with exactly 1 hole: T1 (test-out), counted by
`scripts/vcheck`. Item kinds and the slot protocol are in the main Dafny
file's header (dafny/Q/Q09_InternalsIII/std/Q09_InternalsIII.dfy).
*/
module {:disableNonlinearArithmetic} Q09_Triggers {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  // item: Q09.T1d S11
  // uses: trigger-rewrite
  // pair: Q09.T1v
  // form: trigger, stable
  /** **T1.** (test-out) Each power of BASE is at least BASE times every
      smaller one. Prove it with a quantified step (a `forall` statement)
      whose trigger you choose and write explicitly; the proof must be
      stable under `scripts/vcheck --brittleness --solvers` and carry no
      resource attribute. */
  lemma PowGrowsByBase(m: nat, n: nat)
    requires m < n
    ensures Pow(m) * BASE <= Pow(n)
    decreases n - m
  // Hint(1): recurse from m + 1 to n; the quantified step covers the first
  //    comparison.
  // Hint(2): an instance of the step mentions two powers; a trigger on one of
  //    them makes the step fire again on its own output.
}
