// Topic (e) course-local task cl-d14-find-first (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `FindFirst`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
module Q32dev_d14_find_first {
  method FindFirst(a: seq<int>, x: int) returns (k: int)
    ensures 0 <= k <= |a|
    ensures k < |a| ==> a[k] == x
    ensures forall j | 0 <= j < k :: a[j] != x
  {
    k := 0;
    while k < |a| && a[k] != x
      invariant 0 <= k <= |a|
      invariant forall j | 0 <= j < k :: a[j] != x
    {
      k := k + 1;
    }
  }
}
