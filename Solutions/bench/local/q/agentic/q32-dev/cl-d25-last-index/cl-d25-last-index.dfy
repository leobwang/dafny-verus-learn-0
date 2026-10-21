// Topic (e) course-local task cl-d25-last-index (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `LastIndex`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
module Q32dev_d25_last_index {
  method LastIndex(a: seq<int>, x: int) returns (k: int)
    ensures -1 <= k < |a|
    ensures k >= 0 ==> a[k] == x
    ensures forall j | k < j < |a| :: a[j] != x
  {
    k := |a| - 1;
    while k >= 0 && a[k] != x
      invariant -1 <= k < |a|
      invariant forall j | k < j < |a| :: a[j] != x
      decreases k + 1
    {
      k := k - 1;
    }
  }
}
