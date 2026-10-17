// Wrapper fixture (tests/wrappers): restates RevRev with a weaker ensures and
// proves only that; the parent's ensures still binds (Δ44).
module Fx_Impl refines Fx_Spec {
  lemma RevRev(s: seq<int>)
    ensures |s| >= 0
  {
  }

  lemma RevLength ...
  {
  }
}
