// Wrapper fixture (tests/wrappers): base.dfy with each statement changed.
module Fx_Hash {
  function Twice(x: nat): nat { 2 * x }

  lemma TwiceGrows(x: nat)
    requires x > 1
    ensures Twice(x) > x
  {
  }

  method Halve(x: nat) returns (y: nat)
    ensures 2 * y <= x + 1
  {
    y := x / 2;
  }
}
