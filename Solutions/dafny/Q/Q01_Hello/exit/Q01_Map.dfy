/*!
# Q01 — the map, Dafny half (Reference Solution)

Hole-free reference for `dafny/Q/Q01_Hello/exit/Q01_Map.dfy`: every code block filled,
every check live. Verdict answers are in `Solutions/slots/Q01.slots`. Silent:
`scripts/vcheck --ref` on this file prints only its summary line.
*/
module Q01_Map {
  import opened QG_L1_BigNat

  // item: Q01.X2d S2
  // uses: ensures
  // need: method Swap(a: nat, b: nat) returns (x: nat, y: nat)
  // need: var p, q := Swap(1, 2); assert p == 2 && q == 1;
  // ### X2d · S2 — Write `Swap`, which returns its two arguments in the other order, with
  //     a postcondition that lets the check below verify; then uncomment the check.
  // reference-only: the learner writes this declaration
  method Swap(a: nat, b: nat) returns (x: nat, y: nat)
    ensures x == b && y == a
  {
    x, y := b, a;
  }
  // reference-only: the shipped check, uncommented
  method SwapCheck() { var p, q := Swap(1, 2); assert p == 2 && q == 1; }

  // item: Q01.X4d S4
  // uses: assert, lemma-call
  // need: lemma {:induction false} ZerosToNat(n: nat)
  // need: ensures ToNat(seq(n, i => 0)) == 0
  /** ### X4d · S4 — Prove it by recursion on `n`.
      Why this proof: dropping the low limb of `n` zeros leaves `n - 1` zeros (the assert
      states the slice equality, so the verifier can use the recursive call's
      statement), and the low limb itself is 0. */
  lemma {:induction false} ZerosToNat(n: nat)
    ensures ToNat(seq(n, i => 0)) == 0
    decreases n
  {
    if n > 0 {
      assert seq(n, i => 0)[1..] == seq(n - 1, i => 0);
      ZerosToNat(n - 1);
    }
  }

  // item: Q01.X5dv S5 verdict
  /** ### X5dv · S5 — Suppose this file imported the layer with `import QG_L1_BigNat` (no
      `opened`), and `verus/q/q01_hello/src/exit.rs` had no `use qg_bignat_l1::*;` line.
      How would each file then have to write the layer's value function applied to `s`?
      Answer form: one letter.

      a) `ToNat(s)` and `seq_to_nat(s)`, as the files write it now
      b) `QG_L1_BigNat::ToNat(s)` and `qg_bignat_l1.seq_to_nat(s)`
      c) `QG_L1_BigNat.ToNat(s)` and `qg_bignat_l1.seq_to_nat(s)`
      d) `QG_L1_BigNat.ToNat(s)` and `qg_bignat_l1::seq_to_nat(s)` */
  // CHECK X5dv

  // item: Q01.X6d S6 verdict
  /** ### X6d · S6 — Which single line, added to the header of this method, makes it
      verify? Answer form: one letter.

          method ZeroFirst(a: array<nat>)
            ensures a.Length > 0 ==> a[0] == 0
          {
            if a.Length > 0 { a[0] := 0; }
          }

      a) requires a.Length > 0
      b) modifies a
      c) reads a
      d) ensures a.Length >= 0 */
  // CHECK X6d

  // item: Q01.X8dv S8 verdict
  /** ### X8dv · S8 — The program is `x := x + 1` and the postcondition is `x > 5`. Which
      is the weakest precondition? Answer form: one letter.

      a) x > 5
      b) x > 4
      c) x > 6
      d) x + 5 > 1 */
  // CHECK X8dv

  // item: Q01.X9dv S9 verdict
  /** ### X9dv · S9 — The `scripts/vcheck` flag that runs the done gate, and the exit code
      that means verified. Answer form: `<flag> <code>`, the flag with its leading
      dashes. */
  // CHECK X9dv

  // item: Q01.X10dv S10 verdict
  /** ### X10dv · S10 — A Dafny run reports `verified` with no warning. Which of these does
      that result NOT ask you to trust? Answer form: one letter.

      a) Z3
      b) the Dafny-to-Boogie translation
      c) the body of a lemma it verified
      d) the Python compiler, if you run the code */
  // CHECK X10dv

  // item: Q01.X11dv S11 verdict
  /** ### X11dv · S11 — The course pins a resource limit instead of a time limit. What does
      that buy? Answer form: one letter.

      a) faster runs
      b) the same verdict on every run and machine
      c) more proofs succeed
      d) no out-of-resource results */
  // CHECK X11dv

  // item: Q01.X12d S12 verdict
  /** ### X12d · S12 — How many tool-counted holes does one bodyless lemma with two
      `ensures` clauses produce? Answer form: numeral. */
  // CHECK X12d
}
