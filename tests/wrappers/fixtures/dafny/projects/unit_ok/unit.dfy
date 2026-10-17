// Wrapper fixture (tests/wrappers): the one source of a project fixture.
module Fx_Unit {
  function Double(x: nat): nat { 2 * x }

  lemma DoubleGrows(x: nat)
    ensures Double(x) >= x
  {
  }
}
