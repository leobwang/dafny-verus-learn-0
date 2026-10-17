// Wrapper fixture (tests/wrappers): a resolution error.
module Fx_Resolve {
  lemma UsesUndefined()
    ensures Undefined(3)
  {
  }
}
