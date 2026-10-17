// Wrapper fixture (tests/wrappers): @VerifyOnly warns twice at one position (W-D16,
// Δ5) and silently skips the wrong lemma below it.
module Fx_Only {
  @VerifyOnly
  lemma Focus(x: nat)
    ensures x >= 0
  {
  }

  lemma Wrong(x: nat)
    ensures x > 5
  {
  }
}
