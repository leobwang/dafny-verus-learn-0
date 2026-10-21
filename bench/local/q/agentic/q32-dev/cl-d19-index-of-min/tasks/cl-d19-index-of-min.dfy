// Topic (e) course-local task cl-d19-index-of-min (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `IndexOfMin`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
module Q32dev_d19_index_of_min {
  method IndexOfMin(a: seq<int>) returns (k: int)
    requires |a| > 0
    ensures 0 <= k < |a|
    ensures forall j | 0 <= j < |a| :: a[k] <= a[j]
  {
    k := 0;
    var i := 1;
    while i < |a|
    {
      if a[i] < a[k] {
        k := i;
      }
      i := i + 1;
    }
  }
}
