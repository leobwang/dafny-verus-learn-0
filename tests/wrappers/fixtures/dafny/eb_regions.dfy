// Wrapper fixture (tests/wrappers): the empty-body gate on a `function … by
// method` and its region mode (QPLAN §6 Q18). Each item's learner lines sit
// between `@hole-begin`/`@hole-end` markers, as in a reference twin. Invented
// functions; none is a course item.
module Fx_EbRegions {
  function Tri(n: nat): nat {
    if n == 0 then 0 else n + Tri(n - 1)
  }

  // item: Q09.H4d S3
  function TriLoop(n: nat): nat {
    Tri(n)
  } by method {
    var i := 0;
    var r := 0;
    while i < n
      // @hole-begin Q09.H4d
      invariant 0 <= i <= n
      invariant r == Tri(i)
      // @hole-end Q09.H4d
    {
      i := i + 1;
      r := r + i;
    }
    return r;
  }

  // item: Q09.H5d S3
  method Half(n: nat) returns (r: nat)
    // @hole-begin Q09.H5d
    requires n % 2 == 0
    // @hole-end Q09.H5d
    ensures 2 * r == n
  {
    r := n / 2;
  }

  // item: Q09.H6d S3
  method Twice(n: nat) returns (r: nat)
    ensures r == n + n
  {
    // @hole-begin Q09.H6d
    assert n + n == 2 * n;
    // @hole-end Q09.H6d
    r := 2 * n;
  }
}
