// Wrapper fixture (tests/wrappers): a loud non-hole warning ({:verify false}, W-D15).
module Fx_Loud {
  lemma {:verify false} Skipped(x: nat)
    ensures x > 100
  {
  }
}
