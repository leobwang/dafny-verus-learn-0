// Wrapper fixture (tests/wrappers): refines spec_only.dfy's abstract module.
module Fx_XImpl refines Fx_XSpec {
  function Id(x: int): int { x }

  lemma IdFixed ...
  {
  }
}
