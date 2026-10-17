// Wrapper fixture (tests/wrappers): one good lemma, one wrong lemma, one failing assert.
module Fx_Fails {
  function Inc(x: nat): nat { x + 1 }

  lemma Good(x: nat)
    ensures Inc(x) > x
  {
  }

  lemma Bad(x: nat)
    ensures Inc(x) == x
  {
  }

  method BadAssert(x: nat)
  {
    assert x > 0;
  }
}
