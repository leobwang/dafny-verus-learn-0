/*!
# Q04 — exit, Dafny half (closed book)

Closed book: keep the chapter, the exercise files, later modules' files,
search tools and /tutor closed. At most the given spine (dafny/given/Q/) and
the pinned standard library's own source may be open.

This file ships with exactly 2 holes (X1, X2); the Verus half
(verus/q/q04_proof_craft/src/exit.rs) ships with 2 holes. Score both halves
in one sitting with

    scripts/firsttry.sh Q04 --exit

Threshold: 3 of the 4 exit items, at least 1 in each language. The first full
run (every block attempted) is the score; repair every block afterwards, after
which the strict gate covers this file too. This file is in no build: work it
with `scripts/vcheck dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy`.
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
  /** **X1.** The value of an append: the limbs of `a` followed by the limbs
      of `b`. Prove it by recursion on `a` (`decreases |a|` ships), with a
      `calc` chain in the recursive case. */
  lemma ToNatAppend(a: seq<nat>, b: seq<nat>)
    ensures ToNat(a + b) == ToNat(a) + Pow(|a|) * ToNat(b)
    decreases |a|

  // item: Q04.X2d S5
  // uses: forall, library-call
  // need: lemma PowsBelow(n: nat)
  // need: ensures forall k | 0 <= k < n :: Pow(k) < Pow(n)
  /** **X2.** Every smaller power is smaller. Prove it with one `forall`
      statement and the standard library (L3's bridge `PowIsStdPow` is open
      to you). */
  lemma PowsBelow(n: nat)
    ensures forall k | 0 <= k < n :: Pow(k) < Pow(n)
}
