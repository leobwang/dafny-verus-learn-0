/*! # Q04 — synthetic test fixture (tests/course_map). Not course content. */
module Q04_ProofCraft {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat

  // item: Q04.W1d S1
  const Example := 1

  // item: Q04.P1dv S1 verdict
  // SLOT: CHECK P1dv

  // item: Q04.C1dv S3 write:calc
  const CardNote := 0

  // item: Q04.H1d S3
  // uses: calc, lemma-call
  // pair: Q04.H1v
  lemma H1(x: nat)
    ensures x + 0 == x
}
