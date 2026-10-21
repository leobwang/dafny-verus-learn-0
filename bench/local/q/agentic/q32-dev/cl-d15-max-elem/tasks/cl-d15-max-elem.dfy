// Topic (e) course-local task cl-d15-max-elem (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `MaxElem`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
module Q32dev_d15_max_elem {
  method MaxElem(a: seq<int>) returns (m: int)
    requires |a| > 0
    ensures forall j | 0 <= j < |a| :: a[j] <= m
    ensures m in a
  {
    m := a[0];
    var i := 1;
    while i < |a|
    {
      if a[i] > m {
        m := a[i];
      }
      i := i + 1;
    }
  }
}
