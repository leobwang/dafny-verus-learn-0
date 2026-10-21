// Topic (e) course-local task cl-d22-clamp-all (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `ClampAll`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
module Q32dev_d22_clamp_all {
  method ClampAll(a: seq<int>, lo: int, hi: int) returns (r: seq<int>)
    requires lo <= hi
    ensures |r| == |a|
    ensures forall j | 0 <= j < |r| :: lo <= r[j] <= hi
  {
    r := [];
    var i := 0;
    while i < |a|
      invariant 0 <= i <= |a|
      invariant |r| == i
      invariant forall j | 0 <= j < |r| :: lo <= r[j] <= hi
    {
      var x := if a[i] < lo then lo else if a[i] > hi then hi else a[i];
      r := r + [x];
      i := i + 1;
    }
  }
}
