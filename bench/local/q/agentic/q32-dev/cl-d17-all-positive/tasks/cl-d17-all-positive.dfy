// Topic (e) course-local task cl-d17-all-positive (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `AllPositive`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
module Q32dev_d17_all_positive {
  method AllPositive(a: seq<int>) returns (b: bool)
    ensures b <==> forall j | 0 <= j < |a| :: a[j] > 0
  {
    b := true;
    var i := 0;
    while i < |a|
    {
      if a[i] <= 0 {
        b := false;
      }
      i := i + 1;
    }
  }
}
