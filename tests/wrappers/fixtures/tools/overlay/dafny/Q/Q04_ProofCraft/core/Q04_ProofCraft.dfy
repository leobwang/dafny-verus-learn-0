/*! # Q04 — synthetic tools fixture (tests/wrappers/fixtures/tools). Not course content. */
module Q04_ProofCraft {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat

  // item: Q04.W1d S1
  const Example := 1

  // item: Q04.P1dv S1 verdict
  // **P1.** Run `scripts/vcheck` on this unit. Answer form: "<verdict> <hole count>"
  // SLOT: CHECK P1dv

  // item: Q04.C1dv S3 write:calc
  const CardNote := 0

  // item: Q04.H1d S3
  // uses: calc, lemma-call
  // pair: Q04.H1v
  lemma H1(x: nat)
    ensures x + 0 == x

  function Sum(n: nat): nat
  {
    if n == 0 then 0 else n + Sum(n - 1)
  }

  // item: Q04.H3d S3
  // uses: calc
  lemma SumFormula(n: nat)
    ensures 2 * Sum(n) == n * (n + 1)

  method {:test} CheckSum() {
    // Uncomment as you go:
    // expect Sum(3) == 6;
  }
}
