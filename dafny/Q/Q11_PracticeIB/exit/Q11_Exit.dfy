/*!
# Q11 — exit, Dafny half (closed book)

Closed book: keep the chapter, the exercise files, later modules' files,
search tools and /tutor closed. At most the given spine (dafny/given/Q/) may
be open.

This file ships with exactly 1 hole (X1); the Verus half
(verus/q/q11_practice_ib/src/exit.rs) ships with 1 hole. Each is timed:
10 minutes. Score both halves in one sitting with

    scripts/firsttry.sh Q11 --exit

Threshold: 1 of the 2 exit items. The first full run (every block attempted)
is the score; repair every block afterwards, after which the strict gate
covers this file too. This file is in no build: work it with
`scripts/vcheck dafny/Q/Q11_PracticeIB/exit/Q11_Exit.dfy`.
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
  /** **X1.** `Digits(n)` is the length of L2's `FromNat(n)`. */
  lemma DigitsLength(n: nat)
    ensures Digits(n) == |FromNat(n)|
  // HOLE: this lemma has no body; write `{ … }` below the ensures line.
}
