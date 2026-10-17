// Wrapper fixture (tests/wrappers): an {:axiom} child is silent in verify (Δ44).
module Fx_Impl refines Fx_Spec {
  lemma {:axiom} RevRev ...

  lemma RevLength ...
  {
  }
}
