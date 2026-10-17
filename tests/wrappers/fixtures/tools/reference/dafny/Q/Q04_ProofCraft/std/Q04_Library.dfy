/*! # Q04 — synthetic tools fixture (Reference Solution): the twin of
    dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy. */
module Q04_Library {
  import opened QG_L3_BigNat
  import opened Std.Wrappers

  // item: Q04.H2d S4
  // uses: calc
  lemma H2(x: nat)
    ensures x * 1 == x
  {
  }

  // item: Q04.T1dv S5
  const T1 := 0
}
