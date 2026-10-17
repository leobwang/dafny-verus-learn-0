// Wrapper fixture (tests/wrappers): adds a requires to a refined lemma (W-D19).
module Fx_Impl refines Fx_Spec {
  lemma RevRev(s: seq<int>)
    requires |s| == 0
  {
  }

  lemma RevLength ...
  {
  }
}
