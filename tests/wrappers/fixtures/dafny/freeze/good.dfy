// Wrapper fixture (tests/wrappers): refines the frozen module, with proofs.
module Fx_Impl refines Fx_Spec {
  lemma RevAppend(a: seq<int>, b: seq<int>)
    ensures Rev(a + b) == Rev(b) + Rev(a)
  {
    if |a| == 0 {
      assert a + b == b;
    } else {
      assert (a + b)[1..] == a[1..] + b;
      RevAppend(a[1..], b);
    }
  }

  lemma RevRev ...
  {
    if |s| > 0 {
      RevAppend(Rev(s[1..]), [s[0]]);
      RevRev(s[1..]);
    }
  }

  lemma RevLength ...
  {
  }
}
