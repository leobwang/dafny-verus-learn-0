/*!
# Q10 — exit, Dafny half (Reference Solution)

Hole-free reference for `dafny/Q/Q10_PracticeIA/exit/Q10_Exit.dfy`
(author-only; never learner-visible). Same module, imports, names,
statements, item markers and `need:` lines as the exit file; the block is
proved. Silent under `scripts/vcheck --ref`.
*/
module Q10_Exit {
  import opened QG_L1_BigNat

  /** The sum of the limbs, head first (given). It is ghost: compiled code
      cannot call it. */
  ghost function Sum(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else s[0] + Sum(s[1..])
  }

  // item: Q10.X1d S4
  // uses: invariant
  // need: method SumLimbs(s: seq<nat>) returns (t: nat)
  // need: ensures t == Sum(s)
  /** **X1.** Sum the limbs with a loop from the top limb down.

      Reference: the loop keeps `t == Sum(s[i..])`, the sum of the suffix
      already added; one step takes limb `i - 1`, and the sequence identity
      `s[i..][1..] == s[i + 1..]` lets `Sum`'s unfolding on the new suffix
      meet the invariant on the old one; at the exit `s[0..] == s`. */
  method SumLimbs(s: seq<nat>) returns (t: nat)
    ensures t == Sum(s)
  {
    t := 0;
    var i := |s|;
    while i > 0
      invariant 0 <= i <= |s| && t == Sum(s[i..])
      decreases i
    {
      i := i - 1;
      assert s[i..][1..] == s[i + 1..];
      t := t + s[i];
    }
    assert s[0..] == s;
  }
}
