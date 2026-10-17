// Wrapper fixture (tests/wrappers): symbols whose names share a prefix (Δ11 filters).
module Fx_Sym {
  function Inc(x: nat): nat { x + 1 }

  lemma Good(x: nat)
    ensures Inc(x) > x
  {
  }

  lemma GoodLonger(x: nat)
    ensures Inc(x) > 0
  {
  }

  lemma Bad(x: nat)
    ensures Inc(x) == x
  {
  }
}
