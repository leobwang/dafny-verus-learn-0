// Topic (e) course-local task cl-d18-reverse-copy (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `ReverseCopy`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
module Q32dev_d18_reverse_copy {
  method ReverseCopy(a: seq<int>) returns (r: seq<int>)
    ensures |r| == |a|
    ensures forall j | 0 <= j < |a| :: r[j] == a[|a| - 1 - j]
  {
    r := [];
    var i := 0;
    while i < |a|
    {
      r := [a[i]] + r;
      i := i + 1;
    }
  }
}
