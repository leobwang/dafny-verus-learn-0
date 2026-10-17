// Wrapper fixture (tests/wrappers): an invented abstract spec whose refiner
// lives in impl_only.dfy (the lint's program context; static tests only).
abstract module Fx_XSpec {
  function Id(x: int): int

  lemma IdFixed(x: int)
    ensures Id(x) == x
}
