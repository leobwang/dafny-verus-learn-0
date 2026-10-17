// Wrapper fixture (tests/wrappers): the empty-body gate (Δ45). Three holes:
// one auto-induction closes unless its lever stays, one that fails even at
// maximal automation, one that is not a hole at all.
module Fx_Eb {
  function Sum(n: nat): nat {
    if n == 0 then 0 else n + Sum(n - 1)
  }

  function Rev(s: seq<int>): seq<int> {
    if |s| == 0 then [] else Rev(s[1..]) + [s[0]]
  }

  // item: Q09.H1d S3
  lemma {:induction false} SumClosed(n: nat)
    ensures 2 * Sum(n) == n * (n + 1)

  // item: Q09.H2d S3
  lemma RevRev(s: seq<int>)
    ensures Rev(Rev(s)) == s

  // item: Q09.H3d S3
  lemma SumNonNegative(n: nat)
    ensures Sum(n) >= 0
}
