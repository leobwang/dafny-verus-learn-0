/*!
# Q12 — exit, Dafny half (Reference Solution)

Hole-free reference for `dafny/Q/Q12_PracticeIC/exit/Q12_Exit.dfy`
(author-only; never learner-visible). Same module, imports, item markers,
`need:` lines and order as the exit file; the exit hole is filled. The file
is silent: `scripts/vcheck --ref` on it prints only the summary line. No
declaration carries a resource attribute.
*/
module Q12_Exit {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  // item: Q12.X1d S11
  // need: lemma AddSmall()
  // need: ensures Add([3, 1], [4]) == [7, 1]
  /** **X1.** A small sum, computed by the definitions. Layer L4's `Add`
      is `AddC` with carry 0. Prove the instance below. */
  lemma AddSmall()
    ensures Add([3, 1], [4]) == [7, 1]
  {
    reveal AddC();  // did: unfolds the opaque AddC for this proof only
    assert Tail([3, 1]) == [1] && Tail([4]) == [] && Tail([1]) == [];
    assert AddC([1], [], 0) == [1];
  }
}
