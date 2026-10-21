// Topic (e) course-local task cl-d23-prefix-totals (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `PrefixTotals`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
module Q32dev_d23_prefix_totals {
  method PrefixTotals(a: seq<int>) returns (p: seq<int>)
    ensures |p| == |a| + 1 && p[0] == 0
    ensures forall k | 0 <= k < |a| :: p[k + 1] == p[k] + a[k]
  {
    p := [0];
    var i := 0;
    while i < |a|
    {
      p := p + [p[i] + a[i]];
      i := i + 1;
    }
  }
}
