// Topic (e) course-local task cl-d24-sorted-check (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `SortedCheck`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
module Q32dev_d24_sorted_check {
  method SortedCheck(a: seq<int>) returns (b: bool)
    ensures b <==> forall k | 0 <= k && k + 1 < |a| :: a[k] <= a[k + 1]
  {
    b := true;
    var i := 0;
    while i + 1 < |a|
      invariant 0 <= i && (i == 0 || i + 1 <= |a|)
      invariant b <==> forall k | 0 <= k < i && k + 1 < |a| :: a[k] <= a[k + 1]
    {
      if a[i] > a[i + 1] {
        b := false;
      }
      i := i + 1;
    }
  }
}
