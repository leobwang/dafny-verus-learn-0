/*!
# Q07 — Internals I: proof engineering, translation (Exercises)

Imports: the given BigNat spine, layers L1 (`QG_L1_BigNat`) to L4
(`QG_L4_BigNat`), and two modules of Dafny's standard library,
`Std.Arithmetic.Mul` and `Std.Arithmetic.DivMod`, all opened; nothing else:
no earlier exercise file. The layers are frozen and complete; read them,
never edit them. Nonlinear arithmetic is off in this module (the attribute on
its `module` line).

How to work this file:
1. Predictions first: fill every slot of the prediction block below (the
   verdict answers go in slots/Q07.slots) and of the Verus file's prediction
   block (verus/q/q07_internals_i/src/lib.rs), then record the first tries
   with `scripts/firsttry.sh Q07 --check`, before you run anything they are
   about.
2. Test-out next, closed book: T1 (below the prediction block) before any
   reading, without its hints. `scripts/firsttry.sh Q07 --check` records its
   first try, and refuses to while any prediction of the module is
   unrecorded: record the predictions first. If both files' T1 pass on that
   first try, you may skip the chapter section on unfolding and fuel.
3. Replace each hole.
4. Done = `scripts/vcheck --gate dafny/Q/Q07_InternalsI/std` prints only the
   summary line and exits 0, `scripts/vaudit dafny/Q/Q07_InternalsI/std`
   reports no finding, AND `scripts/firsttry.sh Q07 --report --strict` exits
   0.
5. Stuck for 20 minutes? /tutor Q07.

This file ships with exactly 4 holes: T1 (test-out), H1, H2 and H3, each
counted by `scripts/vcheck`. Q07 as a whole ships 11 holes (4 here, 4 in the
Verus crate root verus/q/q07_internals_i/src/lib.rs and 3 in its port module
verus/q/q07_internals_i/src/port.rs), of which 2 are test-out items (T1 in
each language); 7 predictions (all verdicts); and 4 exit items (the exit
files ship 2 + 2 holes). Commit every prediction BEFORE you run anything it
is about, open later files, or read CI, the registry or the plan: their
checks and headers give some predictions away.

Item kinds: P prediction (a slot) · T test-out (closed book, after the
predictions) · W worked example (given, finished) · C card (WRITE: a success
here and a failure demo in specimens/Q07/; RECOGNISE: a reading card with a
demo; divergence, in the final section) · H one-hole item · X exit item (the
exit files) · A agent run (the agent files). Slots: a verdict switch
`// SLOT: CHECK <item>` here takes its answer in slots/Q07.slots
(`P1dv = ???` → `P1dv = "<answer>"`). Fill a slot, record the first try, and
only then enable it: `// SLOT: CHECK P1dv` becomes `// CHECK P1dv`.

The port (H7, H8 and H9, in the Verus file src/port.rs) and its fidelity
audit come after every other hole of the module; W2 below and the check unit
dafny/checks/Q07_checks.dfy are its Dafny side.

Exit (closed book): dafny/Q/Q07_InternalsI/exit/Q07_Exit.dfy and
verus/q/q07_internals_i/src/exit.rs, scored once by
`scripts/firsttry.sh Q07 --exit` (threshold 3 of 4, with at least 1 of the 2
in each language). After it is scored, fill the EXPLAIN-BACK block at the
end of the Dafny exit file.

The agentic exercise (refactorer under harness,
dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy and
verus/q/q07_internals_i/src/agent.rs) is at the bottom.
*/
module {:disableNonlinearArithmetic} Q07_InternalsI {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened Std.Arithmetic.Mul
  import opened Std.Arithmetic.DivMod

  // ===========================================================================
  // The prediction block. Commit every prediction of this module before you
  // read past this block (the test-out T1 included), and record the first
  // tries:
  //     scripts/firsttry.sh Q07 --check
  // Verdict answers go in slots/Q07.slots. The Verus file's prediction block
  // (verus/q/q07_internals_i/src/lib.rs) holds P3 and P6.
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
  // SLOT: CHECK P1dv

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
  // SLOT: CHECK P2dv

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
  // SLOT: CHECK P4d

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
  // SLOT: CHECK P5dv

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
  // SLOT: CHECK P7d

  // ===========================================================================
  // Test-out (closed book: after every prediction of this module is recorded,
  // before any reading; `scripts/firsttry.sh Q07 --check` refuses T1's first
  // try until then)
  // ===========================================================================

  // item: Q07.T1d S4
  // uses: fuel
  // pair: Q07.T1v
  /** **T1.** (test-out) The value of a three-limb literal: `ToNat` peels
      one limb at a time, least significant first. What must the solver know
      about the literal's tails before the three limbs add up? */
  lemma ThreeLimbs(a: nat, b: nat, c: nat)
    ensures ToNat([a, b, c]) == a + BASE * (b + BASE * c)
  // Hint(1): the solver unfolds a recursive definition only a limited number
  //    of times on its own, and this literal needs one unfolding per limb.
  // Hint(2): state each step yourself (the slice `[a, b, c][1..]` and the
  //    values of the shorter literals), or raise `ToNat`'s fuel for this
  //    lemma alone.

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
  /** **H1.** Carrying twice. Adding 1 to the two-limb number whose limbs
      are both `BASE - 1` carries out of both limbs. Layer L4's `AddC`, which
      `Add` calls, is opaque. What must the solver be allowed to see, and how
      many calls of `AddC` does the evaluation make? */
  lemma AddCarriesTwice()
    ensures Add([BASE - 1, BASE - 1], [1]) == [0, 0, 1]
  // Hint(1): an opaque function's body is visible only after a `reveal`.
  // Hint(2): count the calls of `AddC` the evaluation makes; C1's attribute
  //    gives a function that many unfoldings inside one lemma.

  // item: Q07.H2d S5
  // uses: arithmetic-library
  /** **H2.** A quotient by one limb is a limb: if `v < BASE * d`, then
      `v / d < BASE`. Nonlinear arithmetic is off in this module: which
      library fact turns a bound on a product into a bound on a quotient? */
  lemma DivLimbBound(v: nat, d: nat)
    requires 0 < d < BASE && v < BASE * d
    ensures v / d < BASE
  // Hint(1): `Std.Arithmetic.DivMod` (opened) states bounds on quotients;
  //    look for one whose `requires` is a bound by a product.
  // Hint(2): one call, with `v`, `d` and `BASE` as its arguments.

  // item: Q07.H3d S5
  // uses: arithmetic-library
  /** **H3.** One step of division by a limb: with a remainder `r < d` and a
      next limb `x`, the next quotient digit `(r * BASE + x) / d` is a limb.
      Which bound on `r * BASE + x` does H2's library fact need, and which
      named steps give it with nonlinear arithmetic off? */
  lemma DivLimbStep(r: nat, x: nat, d: nat)
    requires 0 < d < BASE && r < d && x < BASE
    ensures (r * BASE + x) / d < BASE
  // Hint(1): from `r + 1 <= d`, scale both sides by `BASE` (a library fact
  //    about `<=` and a product), then distribute `(r + 1) * BASE` (another).
  // Hint(2): then H2's library fact, on `r * BASE + x`.

  // ===========================================================================
  // Final section: divergence card. Record every prediction of this module
  // (scripts/firsttry.sh Q07 --check) before you read on or open its demos.
  // ===========================================================================

  // item: Q07.C7dv S1 diverge:q07-c7
  /** ### C7 — divergence card. Demos: specimens/Q07/card-c7dv-d.dfy.specimen
      and specimens/Q07/card-c7dv-v.rs.specimen. */
}

// =============================================================================
// ## Exercise (AGENTIC) — refactorer under harness (`/contract Q07`)
// =============================================================================
// Files: dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy and
// verus/q/q07_internals_i/src/agent.rs. Shipped state: green, with no hole:
// verified but monolithic proofs in a FROZEN and an API section, and an
// empty HELPERS section. Check command (each file's own header gives the
// steps in full):
//
//     scripts/vcheck dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy
//
// Steps (after this file is done):
// 1. Before the runs: copy each file's FROZEN section to research/q07_frozen.dfy
//    and research/q07_frozen.rs, and commit them with the agent files as
//    shipped.
// 2. In a FRESH session, run /contract Q07 (one run per file).
// 3. Review each diff and fill the REVIEW blocks.
// 4. The local Qwen replay of the Dafny contract (scripts/contract_local.sh;
//    the pinned replay is recorded in chapter section 10), then COMPARISON.
// The lesson: a refactor can pass every machine-checked line and still
// weaken a statement that no line pins; reading the diff is the check.

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line.
  setup 5 · test-out 10 · read 45 · worked 30 · cards 6 · predicts 20 ·
  holes 56 · port + fidelity 35 · agent 15 · paper 15 ·
  exit + explain-back 28 · calib 5 · total 270
*/
