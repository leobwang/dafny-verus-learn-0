// Topic (e) course-local task cl-d13-twice-sum (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `TwiceSumTo`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
module Q32dev_d13_twice_sum {
  method TwiceSumTo(n: nat) returns (s: nat)
    ensures 2 * s == n * (n + 1)
  {
    s := 0;
    var i := 0;
    while i < n
      invariant 0 <= i <= n
      invariant 2 * s == i * (i + 1)
    {
      i := i + 1;
      s := s + i;
    }
  }
}
