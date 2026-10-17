// Wrapper fixture (tests/wrappers): one of each tool-counted hole kind (Δ1, Δ5).
module Fx_Holes {
  function Inc(x: nat): nat { x + 1 }

  method HoleAssume(x: nat) returns (y: nat)
    ensures y == x
  {
    y := x;
    assume y == x;
  }

  lemma IncGrows(x: nat)
    ensures Inc(x) > x
  {
  }

  // item: Q04.H1d S3
  lemma HoleLemma(x: nat)
    ensures Inc(x) == x + 1

  // item: Q04.H2d S3
  lemma HoleTwoEnsures(x: nat)
    ensures Inc(x) >= 1
    ensures Inc(x) >= 0

  // item: Q04.H3d S3
  function HoleFunction(x: nat): nat
    ensures HoleFunction(x) >= x
}
