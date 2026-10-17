/*!
# Q07 — Internals I: proof engineering, translation (Reference Solution)

Hole-free reference for `dafny/Q/Q07_InternalsI/std/Q07_InternalsI.dfy`
(author-only; never learner-visible). Same module, imports, names,
statements, item markers and order as the exercise file. Every hole is
filled, and every verdict switch is enabled; the verdict answers are in
`Solutions/slots/Q07.slots`, their hashes in `expected/Q07.pins`.

The file is silent: `scripts/vcheck --ref` on its unit prints only the
summary line. Every output the module quotes is pinned: the count pins in
`expected/Q07.counts`, the statement freeze in `expected/Q07.freeze`, the
WRITE-card failure demos by their in-file `// EXPECT` lines, and the
RECOGNISE and divergence demos by their sealed sidecars under
`expected/specimens/Q07/`. Nonlinear arithmetic is off in this module, as in
the exercise file.
*/
module {:disableNonlinearArithmetic} Q07_InternalsI {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened Std.Arithmetic.Mul
  import opened Std.Arithmetic.DivMod

  // ===========================================================================
  // The prediction block.
  // ===========================================================================

  // item: Q07.P1dv S4 verdict
  /** **P1.** Unfolding depth. Two Dafny lemmas, each in a module of this
      file's options (`std` unit, nonlinear arithmetic off), each with an
      empty body:

          lemma TwoLimbs(a: nat, b: nat)
            ensures ToNat([a, b]) == a + BASE * b
          {
          }

          lemma TwoLimbsThen(a: nat, b: nat, s: seq<nat>)
            ensures ToNat([a, b] + s) == a + BASE * (b + BASE * ToNat(s))
          {
          }

      and the same two statements in Verus, in a crate of this module's
      dependencies (`use qg_bignat_l4::*;`), each with an empty body:

          proof fn two_limbs(a: u64, b: u64)
              ensures
                  seq_to_nat(seq![a, b]) == a + BASE * b,
          {
          }

          proof fn two_limbs_then(a: u64, b: u64, s: Seq<u64>)
              ensures
                  seq_to_nat(seq![a, b] + s) == a + BASE * (b + BASE * seq_to_nat(s)),
          {
          }

      What does `scripts/vcheck` say about each?
      Answer form: `D:<v> <v> V:<v> <v>` (in each language the literal
      first, then the one with the tail `s`), each v one of `ok` (verifies),
      `fail` (a verification error), `timeout` (out of resource or time),
      `err:<stage>` (refused before verification; the stage as
      `scripts/vcheck` prints it: `parse` or `resolve`). */
  // CHECK P1dv

  // item: Q07.P2dv S1 verdict
  /** **P2.** A port of halving. Dafny, in this module's options:

          method Half(x: int) returns (r: int)
            ensures r == x / 2
          {
            r := x / 2;
          }

      Verus, in a crate of its own:

          fn half(x: i64) -> (r: i64)
              ensures
                  r == x / 2,
          {
              x / 2
          }

      What does `scripts/vcheck` say about each?
      Answer form: `D:<v> V:<v>`, each v as in P1. */
  // CHECK P2dv

  // item: Q07.P4d S1 verdict
  /** **P4.** Machine words in Dafny. In this module's options:

          method SplitWide(x: bv128) returns (hi: bv64, lo: bv64)
            ensures (hi as nat) * BASE + (lo as nat) == x as nat
          {
            hi := (x >> 64) as bv64;
            lo := (x & 0xFFFF_FFFF_FFFF_FFFF) as bv64;
          }

      What does `scripts/vcheck` say about it?
      Answer form: `D:<v>`, v as in P1. */
  // CHECK P4d

  // item: Q07.P5dv S5 verdict
  /** **P5.** Arithmetic without the nonlinear solver. Dafny, in this
      module's options (nonlinear arithmetic off), each with an empty body:

          lemma Comm(x: nat, y: nat)
            ensures x * y == y * x
          {
          }

          lemma Dist(x: nat, y: nat, z: nat)
            ensures x * (y + z) == x * y + x * z
          {
          }

      Verus, in a crate of its own with a crate's default settings, each
      with an empty body:

          proof fn comm(x: int, y: int)
              ensures
                  x * y == y * x,
          {
          }

          proof fn dist(x: int, y: int, z: int)
              ensures
                  x * (y + z) == x * y + x * z,
          {
          }

      What does `scripts/vcheck` say about each?
      Answer form: `D:<v> <v> V:<v> <v>` (commutativity, then
      distributivity, in each language), each v as in P1. */
  // CHECK P5dv

  // item: Q07.P7d S3 verdict
  /** **P7.** Assertion batches. Three lemmas in this module's options, each
      with the same body:

          lemma Plain(x: nat)
            ensures true
          {
            assert x == 1;
            assert x == 2;
            assert x == 3;
          }

      [a] as written; [b] the same lemma with `{:isolate_assertions}` on the
      lemma; [c] the same lemma with `{:isolate}` on the second assertion
      only (`assert {:isolate} x == 2;`). How many errors does
      `scripts/vcheck` report for each?
      Answer form: `D:<n> <n> <n>`, each n a numeral ([a], [b], [c]). */
  // CHECK P7d

  // ===========================================================================
  // Test-out (closed book)
  // ===========================================================================

  // item: Q07.T1d S4
  // uses: fuel
  // pair: Q07.T1v
  /** **T1.** (test-out) The value of a three-limb literal.

      Reference: the solver unfolds `ToNat` once for each `ToNat` term it
      sees, and the literal needs three unfoldings, one per limb (the empty
      tail is the base case). `{:fuel ToNat, 4}` on the lemma lets it unfold
      `ToNat` far enough inside this lemma alone; the by-hand alternative
      asserts the two slices `[a, b, c][1..] == [b, c]` and
      `[b, c][1..] == [c]` together with the values of the shorter
      literals. */
  lemma {:fuel ToNat, 4} ThreeLimbs(a: nat, b: nat, c: nat)
    ensures ToNat([a, b, c]) == a + BASE * (b + BASE * c)
  {
  }

  // ===========================================================================
  // Worked examples
  // ===========================================================================

  // item: Q07.W1d S5
  /** **W1.** The arithmetic library with nonlinear arithmetic off. This
      module turns the solver's nonlinear reasoning off, so a bound on a
      product of two variables comes from a named lemma of
      `Std.Arithmetic.Mul` (opened above), one call per fact. Two nonzero
      limbs: their product is positive (one fact) and at most
      `(BASE - 1) * (BASE - 1)` (another). Each lemma holds for any integers
      its `requires` admits, so the call names the bounds. */
  lemma NonzeroLimbProduct(x: nat, y: nat)
    requires 0 < x < BASE && 0 < y < BASE
    ensures 0 < x * y <= (BASE - 1) * (BASE - 1)
  {
    LemmaMulStrictlyPositive(x, y);              // 0 < x * y
    LemmaMulStrictUpperBound(x, BASE, y, BASE);  // x * y <= (BASE - 1) * (BASE - 1)
  }

  // item: Q07.W2d S1
  /** **W2.** The port's source. Layer L2's `FromNat` (the base-2^64 digits
      of `n`, least significant first) and layer L3's `FromNatCorrect` (its
      result is `Valid` and has the value `n`) are the Dafny side of the
      port in the Verus crate (`src/port.rs`, H7–H9). Read them, and read
      `Valid` (layer L1), as the specification a port must carry over: the
      port takes the inputs below 2^128, and `FromNatSource` states the
      source's contract on exactly those inputs. The check unit
      `dafny/checks/Q07_checks.dfy` runs `FromNat` on the port's sample
      (`scripts/vcheck --test dafny/checks/Q07_checks.dfy`). */
  lemma FromNatSource(n: nat)
    requires n < BASE * BASE
    ensures Valid(FromNat(n)) && ToNat(FromNat(n)) == n
  {
    FromNatCorrect(n);
  }

  // ===========================================================================
  // WRITE cards (each: a success here, a pinned failure demo in specimens/Q07/)
  // ===========================================================================

  // item: Q07.C1d S4 write:fuel
  /** ### C1 — card: unfolding and fuel (`{:fuel F, k}`).
      Jurisdiction: the solver unfolds a recursive function's definition a
      limited number of times on its own. A proof can unfold it by hand
      (assert the unfolded pieces) or raise the function's fuel for one
      lemma with `{:fuel F, k}`. Success: `TwoLimbsByHand` states the slice
      and the shorter literal's value; `TwoLimbsByFuel` gives `ToNat` more
      fuel instead. Failure: specimens/Q07/card-c1d.dfy.specimen (the same
      statement, an empty body). */
  lemma TwoLimbsByHand(a: nat, b: nat)
    ensures ToNat([a, b]) == a + BASE * b
  {
    assert [a, b][1..] == [b];
    assert ToNat([b]) == b;
  }

  lemma {:fuel ToNat, 3} TwoLimbsByFuel(a: nat, b: nat)
    ensures ToNat([a, b]) == a + BASE * b
  {
  }

  // item: Q07.C2d S5 write:arithmetic-library
  /** ### C2 — card: the arithmetic library (`Std.Arithmetic.Mul`,
      `Std.Arithmetic.DivMod`).
      Jurisdiction: with nonlinear arithmetic off, a fact about a product of
      two variables comes from a named library lemma, called with arguments
      that meet its `requires`. Success: `LimbProductBelow`, one call of
      `LemmaMulUpperBound`. Failure: specimens/Q07/card-c2d.dfy.specimen
      (the same lemma with no call). */
  lemma LimbProductBelow(x: nat, y: nat)
    requires x < BASE && y < BASE
    ensures x * y < BASE * BASE
  {
    LemmaMulUpperBound(x, BASE - 1, y, BASE - 1);
  }

  // ===========================================================================
  // RECOGNISE cards
  // ===========================================================================

  // item: Q07.C4d S3 recognise:isolate
  /** ### C4 — card: assertion batches (recognise).
      `{:isolate_assertions}` on a lemma or method verifies each of its
      assertions as a separate solver task; `assert {:isolate} P;` splits one
      assertion off; `scripts/vcheck --isolate <file>` does the first for a
      whole run. Each changes how the work is batched (and so which task
      runs out of resource), never what an assertion may assume. Demo:
      specimens/Q07/card-c4d.dfy.specimen. */

  // item: Q07.C5d S1 recognise:bv-types
  /** ### C5 — card: Dafny's bit-vector types (recognise).
      `bv64`, `bv128`: fixed-width words with `&`, `|`, `<<`, `>>` and
      wrapping arithmetic, and conversions `as nat` / `as bv64`. A fact
      stated wholly on one side (all bit-vectors, or all integers) is the
      solver's home ground; a statement that crosses between them makes the
      solver relate two theories. You will read them in other code; this
      course writes machine words in Verus. Demo:
      specimens/Q07/card-c5d.dfy.specimen. */

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: Q07.H1d S4
  // uses: fuel
  /** **H1.** Carrying twice.

      Reference: `AddC` is opaque, so `reveal AddC();` first; the reveal
      alone fails, because the evaluation of `Add([BASE - 1, BASE - 1], [1])`
      makes three calls of `AddC` (two limbs with a carry each, then the
      final carry) and the solver unfolds fewer on its own.
      `{:fuel AddC, 3}` on the lemma lets it unfold all three inside this
      lemma alone (the fuel attribute without the reveal fails too). */
  lemma {:fuel AddC, 3} AddCarriesTwice()
    ensures Add([BASE - 1, BASE - 1], [1]) == [0, 0, 1]
  {
    reveal AddC();  // did: AddC's body visible, three unfoldings by the fuel attribute
  }

  // item: Q07.H2d S5
  // uses: arithmetic-library
  /** **H2.** A quotient by one limb is a limb.

      Reference: `LemmaMultiplyDivideLt(v, d, BASE)` (`Std.Arithmetic.DivMod`)
      turns `v < d * BASE` into `v / d < BASE`; Dafny's encoding knows that
      multiplication commutes, so `v < BASE * d` meets its `requires`. */
  lemma DivLimbBound(v: nat, d: nat)
    requires 0 < d < BASE && v < BASE * d
    ensures v / d < BASE
  {
    LemmaMultiplyDivideLt(v, d, BASE);
  }

  // item: Q07.H3d S5
  // uses: arithmetic-library
  /** **H3.** One step of division by a limb.

      Reference: from `r + 1 <= d`, `LemmaMulInequality(r + 1, d, BASE)` gives
      `(r + 1) * BASE <= d * BASE`; distributing, `r * BASE + BASE`, so
      `r * BASE + x < r * BASE + BASE <= d * BASE`. Then H2's library lemma,
      `LemmaMultiplyDivideLt(r * BASE + x, d, BASE)`. The distributivity is a
      named step (nonlinear arithmetic is off); the commutativity is free. */
  lemma DivLimbStep(r: nat, x: nat, d: nat)
    requires 0 < d < BASE && r < d && x < BASE
    ensures (r * BASE + x) / d < BASE
  {
    LemmaMulInequality(r + 1, d, BASE);
    LemmaMulIsDistributiveAddOtherWay(BASE, r, 1);
    LemmaMultiplyDivideLt(r * BASE + x, d, BASE);
  }

  // ===========================================================================
  // Final section: divergence card.
  // ===========================================================================

  // item: Q07.C7dv S1 diverge:q07-c7
  /** ### C7 — divergence card. Demos: specimens/Q07/card-c7dv-d.dfy.specimen
      and specimens/Q07/card-c7dv-v.rs.specimen. */
}

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line.
  setup 5 · test-out 10 · read 45 · worked 30 · cards 6 · predicts 20 ·
  holes 56 · port + fidelity 35 · agent 15 · paper 15 ·
  exit + explain-back 28 · calib 5 · total 270
*/
