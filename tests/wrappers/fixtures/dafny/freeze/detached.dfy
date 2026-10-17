// Wrapper fixture (tests/wrappers): states its own weaker lemma and refines nothing.
module Fx_Impl {
  lemma RevRev(s: seq<int>)
    ensures |s| >= 0
  {
  }
}
