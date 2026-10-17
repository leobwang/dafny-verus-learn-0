// Wrapper fixture (tests/wrappers): leaves RevRev unrefined, so it stays a hole.
module Fx_Impl refines Fx_Spec {
  lemma RevLength ...
  {
  }
}
