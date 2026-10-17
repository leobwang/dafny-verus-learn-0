/*!
# Q10 — exit, Dafny half (closed book, timed)

Closed book: keep the chapter, the exercise files, later modules' files,
search tools and /tutor closed. At most the given spine (dafny/given/Q/) may
be open.

This file ships with exactly 1 hole (X1, 10 minutes); the Verus half
(verus/q/q10_practice_ia/src/exit.rs) ships with 1 hole (X1, 10 minutes).
Score both halves in one sitting with

    scripts/firsttry.sh Q10 --exit

Threshold: 1 of the 2 exit items. The first full run (both blocks
attempted) is the score; repair both blocks afterwards, after which the
strict gate covers this file too. This file is in no build: work it with
`scripts/vcheck dafny/Q/Q10_PracticeIA/exit/Q10_Exit.dfy`.
*/
module Q10_Exit {
  import opened QG_L1_BigNat

  /** The sum of the limbs, head first (given). It is ghost: compiled code
      cannot call it. */
  ghost function Sum(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else s[0] + Sum(s[1..])
  }

  // item: Q10.X1d S4
  // uses: invariant
  // need: method SumLimbs(s: seq<nat>) returns (t: nat)
  // need: ensures t == Sum(s)
  /** **X1.** Sum the limbs with a loop from the top limb down: the loop
      starts at `|s|` and steps the index down to 0. Write the loop and its
      invariant, and whatever the verifier needs for each step. */
  method SumLimbs(s: seq<nat>) returns (t: nat)
    ensures t == Sum(s)
  {
    assume false;  // HOLE: replace this line with the loop and its proof
  }
}
