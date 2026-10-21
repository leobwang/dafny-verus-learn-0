// Topic (e) course-local task cl-d20-zeros-three (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `NullCountThree`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
module Q32dev_d20_zeros_three {
  function NullCount(s: seq<int>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else (if s[0] == 0 then 1 else 0) + NullCount(s[1..])
  }

  // Given: the zeros of a concatenation (proved).
  lemma {:induction false} NullCountAppend(a: seq<int>, b: seq<int>)
    ensures NullCount(a + b) == NullCount(a) + NullCount(b)
    decreases |a|
  {
    if |a| == 0 {
      assert a + b == b;
    } else {
      assert (a + b)[1..] == a[1..] + b;
      NullCountAppend(a[1..], b);
    }
  }

  // The zeros of three pieces.
  lemma {:induction false} NullCountThree(a: seq<int>, b: seq<int>, c: seq<int>)
    ensures NullCount(a + b + c) == NullCount(a) + NullCount(b) + NullCount(c)
  {
  }
}
