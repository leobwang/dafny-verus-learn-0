// Topic (e) course-local task cl-d8-insert-length (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `InsertOrderedLength` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
module Q31dev_d8_insert_length {
  function InsertOrdered(x: int, s: seq<int>): seq<int>
    decreases |s|
  {
    if |s| == 0 || x <= s[0] then [x] + s else [s[0]] + InsertOrdered(x, s[1..])
  }

  // Inserting adds exactly one element.
  lemma {:induction false} InsertOrderedLength(x: int, s: seq<int>)
    ensures |InsertOrdered(x, s)| == |s| + 1
    decreases |s|
  {
    if |s| > 0 && x > s[0] {
      InsertOrderedLength(x, s[1..]);
    }
  }
}
