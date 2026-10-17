// Lab 1 local task da2-cmp-zeros-empty (Q12, course-authored; QPLAN §22.6).
// Write the body of `CmpZerosEmpty` so that `scripts/vcheck --gate` verifies this file. Keep
// every other line of the file as it is: the definitions above it, its statement and
// its attributes.
module Lab1_da2_cmp_zeros_empty {
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

  // An all-zero sequence compares equal to the empty one.
  lemma {:induction false} CmpZerosEmpty(a: seq<nat>)
    requires forall i | 0 <= i < |a| :: a[i] == 0
    ensures Cmp(a, []) == 0
    decreases |a|
  {
  }
}
