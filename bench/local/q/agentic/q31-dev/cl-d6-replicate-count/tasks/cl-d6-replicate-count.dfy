// Topic (e) course-local task cl-d6-replicate-count (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `ReplicateCount` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
module Q31dev_d6_replicate_count {
  function Replicate(x: int, n: nat): seq<int>
    decreases n
  {
    if n == 0 then [] else [x] + Replicate(x, n - 1)
  }

  function Occ(s: seq<int>, x: int): nat
    decreases |s|
  {
    if |s| == 0 then 0 else (if s[0] == x then 1 else 0) + Occ(s[1..], x)
  }

  // n copies of x hold x exactly n times.
  lemma {:induction false} ReplicateCount(x: int, n: nat)
    ensures Occ(Replicate(x, n), x) == n
    decreases n
  {
  }
}
