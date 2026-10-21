// Topic (e) course-local task cl-d10-zip-length (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `ZipPairsLength` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
module Q31dev_d10_zip_length {
  function ZipPairs(a: seq<int>, b: seq<int>): seq<(int, int)>
    requires |a| == |b|
    decreases |a|
  {
    if |a| == 0 then [] else [(a[0], b[0])] + ZipPairs(a[1..], b[1..])
  }

  // Zipping two equally long sequences keeps their length.
  lemma {:induction false} ZipPairsLength(a: seq<int>, b: seq<int>)
    requires |a| == |b|
    ensures |ZipPairs(a, b)| == |a|
    decreases |a|
  {
  }
}
