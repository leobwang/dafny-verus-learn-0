// Topic (e) course-local task cl-d2-max-in (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `SeqMaxIsElement` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
module Q31dev_d2_max_in {
  function SeqMax(s: seq<int>): int
    requires |s| > 0
    decreases |s|
  {
    if |s| == 1 then s[0] else (var m := SeqMax(s[1..]); if s[0] >= m then s[0] else m)
  }

  // The maximum of a non-empty sequence is one of its elements.
  lemma {:induction false} SeqMaxIsElement(s: seq<int>)
    requires |s| > 0
    ensures SeqMax(s) in s
    decreases |s|
  {
  }
}
