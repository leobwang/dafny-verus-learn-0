// Wrapper fixture (tests/wrappers): an invented abstract spec whose concrete
// refiner leaves one statement without a body (static lint tests only).
abstract module Fx_PSpec {
  function Twice(x: int): int

  lemma TwiceEven(x: int)
    ensures Twice(x) % 2 == 0

  lemma TwiceGrows(x: nat)
    ensures Twice(x) >= x
}

module Fx_PImpl refines Fx_PSpec {
  function Twice(x: int): int { 2 * x }

  lemma TwiceEven ...
  {
  }
}
