/*!
# Q15 — exit, Dafny half (closed book, timed)

Closed book: keep the chapter, the exercise files, later modules' files,
search tools and /tutor closed. At most the given spine (dafny/given/Q/)
may be open.

This file ships with exactly 1 hole (X1, 20 minutes); the Verus exit file
(verus/q/q15_practice_iic/src/exit.rs) ships with none. Score it with

    scripts/firsttry.sh Q15 --exit

Threshold: the 1 exit item must pass. The first full run (the block
attempted) is the score; repair the block afterwards, after which the strict
gate covers this file too. This file is in no build: work it with
`scripts/vcheck dafny/Q/Q15_PracticeIIC/exit/Q15_Exit.dfy`.
*/
module Q15_Exit {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat

  // item: Q15.X1d S11
  // need: lemma NoCarryValid(a: seq<nat>, b: seq<nat>)
  // need: ensures Valid(a) && Valid(b)
  // form: trigger
  /** **X1.** No carry, so both are digits. The hypothesis is a quantified
      fact whose trigger, as given, never fires on the terms the conclusion
      holds. Prove the lemma with a quantified step of your own that carries
      an explicit trigger. */
  lemma NoCarryValid(a: seq<nat>, b: seq<nat>)
    requires |a| == |b|
    requires forall i {:trigger a[i], b[i]} | 0 <= i < |a| :: a[i] + b[i] < BASE
    ensures Valid(a) && Valid(b)
  // HOLE: this lemma has no body; write `{ … }` below the ensures line.
}
