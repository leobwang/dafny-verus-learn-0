// Wrapper fixture (tests/wrappers): an invented frozen abstract spec that a
// concrete module of the same file refines in full (the given-role lint, Δ44).
abstract module Fx_GSpec {
  type Bag
  const Cap: nat
  ghost function Size(b: Bag): nat
  ghost predicate Fits(b: Bag)
  function Empty(): Bag

  lemma EmptyFits()
    ensures Fits(Empty())

  lemma CapPositive()
    ensures Cap > 0
}

module Fx_GImpl refines Fx_GSpec {
  type Bag = seq<int>
  const Cap: nat := 4
  ghost function Size(b: Bag): nat { |b| }
  ghost predicate Fits(b: Bag) { Size(b) <= Cap }
  function Empty(): Bag { [] }

  lemma EmptyFits ...
  {
  }

  lemma CapPositive ...
  {
  }
}
