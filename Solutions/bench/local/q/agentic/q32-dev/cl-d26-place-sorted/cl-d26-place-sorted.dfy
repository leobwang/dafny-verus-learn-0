// Topic (e) course-local task cl-d26-place-sorted (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `PlaceKeepsSorted`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
module Q32dev_d26_place_sorted {
  predicate SortedSeq(s: seq<int>)
  {
    forall i, j | 0 <= i < j < |s| :: s[i] <= s[j]
  }

  function Place(x: int, s: seq<int>): seq<int>
    decreases |s|
  {
    if |s| == 0 || x <= s[0] then [x] + s else [s[0]] + Place(x, s[1..])
  }

  // Placing x in a sorted sequence keeps it sorted.
  lemma {:induction false} PlaceKeepsSorted(x: int, s: seq<int>)
    requires SortedSeq(s)
    ensures SortedSeq(Place(x, s))
    decreases |s|
  {
    if |s| == 0 || x <= s[0] {
      var r := [x] + s;
      forall i, j | 0 <= i < j < |r|
        ensures r[i] <= r[j]
      {
        if i == 0 {
          assert s[0] <= s[j - 1];
        }
      }
    } else {
      PlaceKeepsSorted(x, s[1..]);
      PlaceElements(x, s[1..]);
      var t := Place(x, s[1..]);
      var r := [s[0]] + t;
      forall i, j | 0 <= i < j < |r|
        ensures r[i] <= r[j]
      {
        if i == 0 {
          var y := t[j - 1];
          assert y in t;
          if y != x {
            assert y in s[1..];
            var k :| 0 <= k < |s[1..]| && s[1..][k] == y;
            assert s[k + 1] == y;
          }
        }
      }
      assert Place(x, s) == r;
    }
  }

  lemma PlaceElements(x: int, s: seq<int>)
    ensures forall y | y in Place(x, s) :: y == x || y in s
    decreases |s|
  {
    if |s| > 0 && x > s[0] {
      PlaceElements(x, s[1..]);
    }
  }
}
