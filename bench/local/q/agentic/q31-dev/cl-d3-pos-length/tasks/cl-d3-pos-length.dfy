// Topic (e) course-local task cl-d3-pos-length (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `PosLength` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
module Q31dev_d3_pos_length {
  function CountPos(s: seq<int>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else (if s[0] > 0 then 1 else 0) + CountPos(s[1..])
  }

  function Pos(s: seq<int>): seq<int>
    decreases |s|
  {
    if |s| == 0 then [] else (if s[0] > 0 then [s[0]] else []) + Pos(s[1..])
  }

  // Keeping the positive elements keeps as many elements as there are positive ones.
  lemma {:induction false} PosLength(s: seq<int>)
    ensures |Pos(s)| == CountPos(s)
    decreases |s|
  {
  }
}
