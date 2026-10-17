/*! # Q04 exit — synthetic tools fixture (Reference Solution): the twin of
    dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy. */
module Q04_Exit {
  import opened QG_L1_BigNat

  function Double(n: nat): nat { n + n }

  // item: Q04.X1d S4
  // need: lemma DoubleIsTwice(n: nat)
  lemma DoubleIsTwice(n: nat)
    ensures Double(n) == 2 * n
  {
  }

  // item: Q04.X2d S5
  // uses: lemma-call
  // need: lemma DoubleMono(a: nat, b: nat)
  lemma DoubleMono(a: nat, b: nat)
    requires a <= b
    ensures Double(a) <= Double(b)
  {
    DoubleIsTwice(a);
    DoubleIsTwice(b);
  }
}
