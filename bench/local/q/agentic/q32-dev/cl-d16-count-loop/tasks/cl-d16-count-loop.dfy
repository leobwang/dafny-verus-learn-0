// Topic (e) course-local task cl-d16-count-loop (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `CountLoop`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
module Q32dev_d16_count_loop {
  function Occurrences(s: seq<int>, x: int): nat
    decreases |s|
  {
    if |s| == 0 then 0 else Occurrences(s[..|s| - 1], x) + (if s[|s| - 1] == x then 1 else 0)
  }

  method CountLoop(s: seq<int>, x: int) returns (c: nat)
    ensures c == Occurrences(s, x)
  {
    c := 0;
    var i := 0;
    while i < |s|
    {
      if s[i] == x {
        c := c + 1;
      }
      i := i + 1;
    }
  }
}
