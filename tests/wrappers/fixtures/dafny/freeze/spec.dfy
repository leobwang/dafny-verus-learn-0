// Wrapper fixture (tests/wrappers): a frozen statement module (Δ44), invented.
abstract module Fx_Spec {
  function Rev(s: seq<int>): seq<int> {
    if |s| == 0 then [] else Rev(s[1..]) + [s[0]]
  }

  lemma RevRev(s: seq<int>)
    ensures Rev(Rev(s)) == s

  lemma RevLength(s: seq<int>)
    requires |s| > 0
    ensures |Rev(s)| == |s|
}
