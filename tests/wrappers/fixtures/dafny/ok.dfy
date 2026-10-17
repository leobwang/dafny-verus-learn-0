// Wrapper fixture (tests/wrappers): an invented hole-free program.
module Fx_Ok {
  function Double(x: nat): nat { 2 * x }

  lemma DoubleGrows(x: nat)
    ensures Double(x) >= x
  {
  }
}
