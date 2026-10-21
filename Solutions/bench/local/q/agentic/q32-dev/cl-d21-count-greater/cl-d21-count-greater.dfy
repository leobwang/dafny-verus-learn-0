// Topic (e) course-local task cl-d21-count-greater (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `CountGreater`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
module Q32dev_d21_count_greater {
  method CountGreater(a: seq<int>, t: int) returns (c: nat)
    ensures c <= |a|
  {
    c := 0;
    var i := 0;
    while i < |a|
      invariant 0 <= i <= |a|
      invariant c <= i
    {
      if a[i] > t {
        c := c + 1;
      }
      i := i + 1;
    }
  }
}
