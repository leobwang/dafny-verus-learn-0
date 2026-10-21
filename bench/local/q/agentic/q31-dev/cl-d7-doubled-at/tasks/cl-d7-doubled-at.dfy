// Topic (e) course-local task cl-d7-doubled-at (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `DoubledSeqAt` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
module Q31dev_d7_double_at {
  function DoubledSeq(s: seq<int>): seq<int>
    decreases |s|
  {
    if |s| == 0 then [] else [2 * s[0]] + DoubledSeq(s[1..])
  }

  lemma DoubledSeqLength(s: seq<int>)
    ensures |DoubledSeq(s)| == |s|
    decreases |s|
  {
    if |s| > 0 {
      DoubledSeqLength(s[1..]);
    }
  }

  // Doubling doubles every element, position by position.
  lemma {:induction false} DoubledSeqAt(s: seq<int>, i: int)
    requires 0 <= i < |s|
    ensures |DoubledSeq(s)| == |s| && DoubledSeq(s)[i] == 2 * s[i]
    decreases |s|
  {
  }
}
