// Wrapper fixture (tests/wrappers): base.dfy with layout, comments, an attribute
// and the proofs changed; every statement is the same.
module Fx_Hash {
  function Twice(x: nat): nat {
    x + x   // the definition is part of the statement
  }

  lemma {:induction false} TwiceGrows(x: nat) requires x > 0 ensures Twice(x) > x
  {
    assert Twice(x) == x + x;
  }

  /* a block comment */ method Halve(x: nat)
    returns (y: nat)
    ensures 2*y <= x
  {
    y := 0;
  }
}
