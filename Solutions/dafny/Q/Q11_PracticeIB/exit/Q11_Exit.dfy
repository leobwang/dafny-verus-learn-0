/*!
# Q11 — exit, Dafny half (Reference Solution)

Hole-free reference for `dafny/Q/Q11_PracticeIB/exit/Q11_Exit.dfy`
(author-only; never learner-visible). Same module, names, statements, item
markers and order as the exit file; the hole is proved. Silent under
`scripts/vcheck --ref`.
*/
module Q11_Exit {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat

  // Given (not an item): the number of base-2^64 digits of n.
  function Digits(n: nat): nat
    decreases n
  {
    if n == 0 then 0 else 1 + Digits(n / BASE)
  }

  // item: Q11.X1d S7
  // need: lemma DigitsLength(n: nat)
  /** **X1.** `Digits(n)` is the length of L2's `FromNat(n)`.

      Reference: the recursion of both definitions, by hand (the unit turns
      automatic induction off): for `n > 0`, the lemma itself at `n / BASE`;
      both sides then unfold once. Its measure is the default one, `n`. */
  lemma DigitsLength(n: nat)
    ensures Digits(n) == |FromNat(n)|
  {
    if n > 0 {
      DigitsLength(n / BASE);
    }
  }
}
