// Wrapper fixture (tests/wrappers): statements for the normalized spec hash.
module Fx_Hash {
  function Twice(x: nat): nat { x + x }

  lemma TwiceGrows(x: nat)
    requires x > 0
    ensures Twice(x) > x
  {
  }

  method Halve(x: nat) returns (y: nat)
    ensures 2 * y <= x
  {
    y := x / 2;
  }
}
