// Wrapper fixture (tests/wrappers): an invented refinement chain, an abstract
// middle module and a concrete leaf (static lint tests only).
abstract module Fx_CTop {
  function F(x: int): int
  function G(x: int): int

  lemma FG(x: int)
    ensures F(x) <= G(x)
}

abstract module Fx_CMid refines Fx_CTop {
  function F(x: int): int { x }
}

module Fx_CLeaf refines Fx_CMid {
  function G(x: int): int { x + 1 }

  lemma FG ...
  {
  }
}
