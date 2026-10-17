/*!
# Q12 — exit, Dafny half (closed book)

Closed book: keep the chapter, the exercise files, later modules' files,
search tools and /tutor closed. At most the given spine (dafny/given/Q/)
may be open.

This file ships with exactly 1 hole (X1); the Verus half
(verus/q/q12_practice_ic/src/exit.rs) ships with 1 hole. Score both halves
in one sitting with

    scripts/firsttry.sh Q12 --exit

Threshold: at least 1 of the 2 exit items. The first full run (every block
attempted) is the score; repair every block afterwards, after which the
strict gate covers this file too. This file is in no build: work it with
`scripts/vcheck dafny/Q/Q12_PracticeIC/exit/Q12_Exit.dfy`.
*/
module Q12_Exit {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  // item: Q12.X1d S11
  // need: lemma AddSmall()
  // need: ensures Add([3, 1], [4]) == [7, 1]
  /** **X1.** A small sum, computed by the definitions. Layer L4's `Add`
      is `AddC` with carry 0. Prove the instance below. */
  lemma AddSmall()
    ensures Add([3, 1], [4]) == [7, 1]
}
