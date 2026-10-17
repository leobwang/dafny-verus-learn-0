// Lab 1 local task da6-fromnat-last (Q12, course-authored; QPLAN §22.6).
// Write the body of `FromNatLast` so that `scripts/vcheck --gate` verifies this file. Keep
// every other line of the file as it is: the definitions above it, its statement and
// its attributes.
module Lab1_da6_fromnat_last {
  const BASE: nat := 18446744073709551616

  function FromNat(n: nat): seq<nat>
    decreases n
  {
    if n == 0 then [] else [n % BASE] + FromNat(n / BASE)
  }

  // The digits of a positive number end with a non-zero digit.
  lemma {:induction false} FromNatLast(n: nat)
    requires n > 0
    ensures |FromNat(n)| > 0 && FromNat(n)[|FromNat(n)| - 1] != 0
    decreases n
  {
  }
}
