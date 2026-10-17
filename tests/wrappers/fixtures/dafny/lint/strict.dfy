// Wrapper fixture (tests/wrappers): agent- and reference-mode lint cases (a
// finished file has no hole of any kind). Expect comments mark the agent-mode
// findings; the suite adds the reference-only ones itself.
module Fx_Strict {
  lemma Hole(x: nat)  // expect: bodyless
    ensures x >= 0

  method Assumes(x: nat) returns (y: nat)
    ensures y == x
  {
    y := x;
    assume y == x;  // expect: assume
  }

  lemma Done(x: nat)
    ensures x >= 0
  {
  }

  // item: Q04.X1d S4
  // need: lemma Target(n: nat)
  lemma Other(n: nat)
    ensures n >= 0
  {
  }

  // item: Q04.X2d S4
  // need: lemma Done2(n: nat)
  // need: ensures n + 0 == n
  lemma Done2(n: nat)
    ensures n + 0 == n
  {
  }
  // SLOT: FAILS ???
}
