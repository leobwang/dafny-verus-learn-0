// Wrapper fixture (tests/wrappers): an invented abstract module that only an
// abstract module refines (nothing concrete), and a trait (static lint tests only).
abstract module Fx_USpec {
  const Limit: int
  function Clamp(x: int): int

  lemma ClampBelow(x: int)
    ensures Clamp(x) <= Limit
}

abstract module Fx_UMid refines Fx_USpec {
  function Clamp(x: int): int { if x <= Limit then x else Limit }
}

trait Fx_UShape {
  function Area(): nat
}
