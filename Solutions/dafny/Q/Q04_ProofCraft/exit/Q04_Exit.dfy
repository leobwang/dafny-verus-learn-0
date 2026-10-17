/*!
# Q04 — exit, Dafny half (Reference Solution)

Hole-free reference for `dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy`
(author-only; never learner-visible). Same module, imports, names, statements,
item markers and order as the exit file; every hole is filled. Silent under
`scripts/vcheck --ref`.
*/
module Q04_Exit {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import Power = Std.Arithmetic.Power

  // item: Q04.X1d S4
  // uses: calc, lemma-recursion
  // need: lemma ToNatAppend(a: seq<nat>, b: seq<nat>)
  // need: ensures ToNat(a + b) == ToNat(a) + Pow(|a|) * ToNat(b)
  /** **X1.** The value of an append.

      Reference: recursion on `a`. Empty `a`: `a + b == b` and `Pow(0) == 1`.
      Otherwise the chain unfolds `ToNat(a + b)` once (the tail of `a + b`
      is `a[1..] + b`), uses the call on `a[1..]`, and refolds: `BASE` times
      `Pow(|a| - 1)` is `Pow(|a|)`. */
  lemma ToNatAppend(a: seq<nat>, b: seq<nat>)
    ensures ToNat(a + b) == ToNat(a) + Pow(|a|) * ToNat(b)
    decreases |a|
  {
    if |a| == 0 {
      assert a + b == b;
    } else {
      calc {
        ToNat(a + b);
      == { assert (a + b)[1..] == a[1..] + b; }
        a[0] + BASE * ToNat(a[1..] + b);
      == { ToNatAppend(a[1..], b); }
        a[0] + BASE * (ToNat(a[1..]) + Pow(|a| - 1) * ToNat(b));
      ==
        ToNat(a) + Pow(|a|) * ToNat(b);
      }
    }
  }

  // item: Q04.X2d S5
  // uses: forall, library-call
  // need: lemma PowsBelow(n: nat)
  // need: ensures forall k | 0 <= k < n :: Pow(k) < Pow(n)
  /** **X2.** Every smaller power is smaller.

      Reference: one `forall` statement; for each `k < n` the two bridges
      move both powers to `Power.Pow(BASE, …)`, and
      `Power.LemmaPowStrictlyIncreases(BASE, k, n)` orders them (`BASE > 1`).
      The empty body does not verify in this file, whose options leave lemma
      induction to the author of the proof. */
  lemma PowsBelow(n: nat)
    ensures forall k | 0 <= k < n :: Pow(k) < Pow(n)
  {
    forall k | 0 <= k < n
      ensures Pow(k) < Pow(n)
    {
      PowIsStdPow(k);
      PowIsStdPow(n);
      Power.LemmaPowStrictlyIncreases(BASE, k, n);
    }
  }
}
