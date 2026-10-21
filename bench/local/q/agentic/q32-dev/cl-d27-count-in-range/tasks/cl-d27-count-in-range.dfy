// Topic (e) course-local task cl-d27-count-in-range (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `CountInRange`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
module Q32dev_d27_count_in_range {
  method CountInRange(a: seq<int>, lo: int, hi: int) returns (c: nat)
    ensures c <= |a|
    ensures lo > hi ==> c == 0
  {
    c := 0;
    var i := 0;
    while i < |a|
    {
      if lo <= a[i] <= hi {
        c := c + 1;
      }
      i := i + 1;
    }
  }
}
