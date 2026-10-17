/*!
# Q07 — exit, Dafny half (closed book)

Closed book: keep the chapter, the exercise files, later modules' files,
search tools and /tutor closed. At most the given spine (dafny/given/Q/) and
the pinned standard library's own source may be open: X1 asks for library
lemmas by name.

This file ships with exactly 2 holes (X1, X2); the Verus half
(verus/q/q07_internals_i/src/exit.rs) ships with 2 holes. Score both halves in
one sitting with

    scripts/firsttry.sh Q07 --exit

Threshold: 3 of the 4 exit items, with at least 1 of the 2 in each language.
The first full run (every block attempted) is the score; repair every block
afterwards, after which the strict gate covers this file too. Then fill the
EXPLAIN-BACK block at the end of this file. Nonlinear arithmetic is off in
this module, as in the exercise file. This file is in no build: work it with
`scripts/vcheck dafny/Q/Q07_InternalsI/exit/Q07_Exit.dfy`.
*/
module {:disableNonlinearArithmetic} Q07_Exit {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened Std.Arithmetic.Mul
  import opened Std.Arithmetic.DivMod

  // item: Q07.X1d S5
  // uses: arithmetic-library
  // need: lemma ProductOfPowSuccModBase(x: nat, k: nat)
  // need: ensures (x * Pow(k + 1)) % BASE == 0
  /** **X1.** A product with a positive power of `BASE` leaves no remainder
      modulo `BASE`. Prove it with the standard library (nonlinear arithmetic
      is off in this module). */
  lemma ProductOfPowSuccModBase(x: nat, k: nat)
    ensures (x * Pow(k + 1)) % BASE == 0

  // item: Q07.X2d S4
  // uses: fuel
  // need: lemma DivBaseOfTwoLimbs(a: nat, b: nat)
  // need: requires a < BASE
  // need: ensures ToNat([a, b]) / BASE == b
  /** **X2.** The quotient of a two-limb literal by `BASE` is its high limb.
      Prove it. */
  lemma DivBaseOfTwoLimbs(a: nat, b: nat)
    requires a < BASE
    ensures ToNat([a, b]) / BASE == b
}

/*
EXPLAIN-BACK (learner-owned; advisory: no script reads it). After the exit is
scored, choose one VERUS exit item that passed (X1 or X2 of
verus/q/q07_internals_i/src/exit.rs) and write, in at most 120 words, what
the verifier needed and why each step of your proof is there.
  item:
  explanation:
*/
