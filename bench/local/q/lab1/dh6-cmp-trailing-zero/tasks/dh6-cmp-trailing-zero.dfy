// Lab 1 local task dh6-cmp-trailing-zero (Q12, course-authored; QPLAN §22.6).
// Write the body of `CmpTrailingZero` so that `scripts/vcheck --gate` verifies this file. Keep
// every other line of the file as it is: the definitions above it, its statement and
// its attributes.
module Lab1_dh6_cmp_trailing_zero {
  function Head(s: seq<nat>): nat
  {
    if |s| == 0 then 0 else s[0]
  }

  function Tail(s: seq<nat>): seq<nat>
  {
    if |s| == 0 then [] else s[1..]
  }

  function Cmp(a: seq<nat>, b: seq<nat>): int
    decreases |a| + |b|
  {
    if |a| == 0 && |b| == 0 then 0
    else
      var c := Cmp(Tail(a), Tail(b));
      if c != 0 then c
      else if Head(a) < Head(b) then -1
      else if Head(a) > Head(b) then 1
      else 0
  }

  // A trailing zero limb does not change the comparison.
  lemma {:induction false} CmpTrailingZero(a: seq<nat>)
    ensures Cmp(a, a + [0]) == 0
    decreases |a|
  {
  }
}
