/*!
# Q07 — exit, Dafny half (Reference Solution)

Hole-free reference for `dafny/Q/Q07_InternalsI/exit/Q07_Exit.dfy`
(author-only; never learner-visible). Same module, imports, names,
statements, item markers and `need:` lines as the exit file; both blocks are
proved. Silent under `scripts/vcheck --ref`. Nonlinear arithmetic is off in
the module, as in the exit file.
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
      modulo `BASE`.

      Reference: one unfolding of `Pow` gives `Pow(k + 1) == BASE * Pow(k)`;
      associativity and commutativity (named: nonlinear arithmetic is off)
      regroup `x * (BASE * Pow(k))` as `(x * Pow(k)) * BASE`, and
      `LemmaModMultiplesBasic` says a multiple of `BASE` leaves remainder 0. */
  lemma ProductOfPowSuccModBase(x: nat, k: nat)
    ensures (x * Pow(k + 1)) % BASE == 0
  {
    assert Pow(k + 1) == BASE * Pow(k);
    LemmaMulIsAssociative(x, BASE, Pow(k));
    LemmaMulIsCommutative(x, BASE);
    LemmaMulIsAssociative(BASE, x, Pow(k));
    LemmaMulIsCommutative(BASE, x * Pow(k));
    LemmaModMultiplesBasic(x * Pow(k), BASE);
  }

  // item: Q07.X2d S4
  // uses: fuel
  // need: lemma DivBaseOfTwoLimbs(a: nat, b: nat)
  // need: requires a < BASE
  // need: ensures ToNat([a, b]) / BASE == b
  /** **X2.** The quotient of a two-limb literal by `BASE` is its high limb.

      Reference: unfold the literal's value (`ToNatCons` and
      `ToNatSingleton`, L2) to `a + BASE * b`, then
      `LemmaFundamentalDivModConverse` with quotient `b` and remainder `a`
      (`a < BASE`); its `x == q * d + r` needs the product in the other
      order, one commutativity call. */
  lemma DivBaseOfTwoLimbs(a: nat, b: nat)
    requires a < BASE
    ensures ToNat([a, b]) / BASE == b
  {
    ToNatCons(a, [b]);
    ToNatSingleton(b);
    assert ToNat([a, b]) == a + BASE * b;
    LemmaMulIsCommutative(BASE, b);
    LemmaFundamentalDivModConverse(ToNat([a, b]), BASE, b, a);
  }
}

/*
EXPLAIN-BACK (learner-owned; advisory: no script reads it). After the exit is
scored, choose one VERUS exit item that passed (X1 or X2 of
verus/q/q07_internals_i/src/exit.rs) and write, in at most 120 words, what
the verifier needed and why each step of your proof is there.
  item:
  explanation:
*/
