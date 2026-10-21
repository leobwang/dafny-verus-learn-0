// Topic (e) course-local task cl-d11-uniform-ends (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `UniformFirstLast` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
module Q31dev_d11_uniform_ends {
  predicate Uniform(s: seq<int>)
    decreases |s|
  {
    |s| <= 1 || (s[0] == s[1] && Uniform(s[1..]))
  }

  // In a uniform sequence the first and last elements agree.
  lemma {:induction false} UniformFirstLast(s: seq<int>)
    requires |s| > 0 && Uniform(s)
    ensures s[0] == s[|s| - 1]
    decreases |s|
  {
    if |s| > 1 {
      UniformFirstLast(s[1..]);
      assert s[1..][|s[1..]| - 1] == s[|s| - 1];
    }
  }
}
