// Topic (e) course-local task cl-d12-evens-le (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `EvensBelowLe` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
module Q31dev_d12_evens_le {
  function EvensBelow(n: nat): nat
    decreases n
  {
    if n == 0 then 0 else EvensBelow(n - 1) + (if (n - 1) % 2 == 0 then 1 else 0)
  }

  // There are at most n even numbers below n.
  lemma {:induction false} EvensBelowLe(n: nat)
    ensures EvensBelow(n) <= n
    decreases n
  {
    if n > 0 {
      EvensBelowLe(n - 1);
    }
  }
}
