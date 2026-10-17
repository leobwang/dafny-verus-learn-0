/*!
# Q06 — The machine and the verifier loop (Reference Solution)

Hole-free reference for `dafny/Q/Q06_Machine/std/Q06_Machine.dfy`
(author-only; never learner-visible). Same module, imports, names,
statements, item markers and order as the exercise file. Every hole is
filled, every check is live (H4's property suite included), and every
verdict switch is enabled; the verdict answers are in
`Solutions/slots/Q06.slots`, their hashes in `expected/Q06.pins`.

The file is silent: `scripts/vcheck --ref` on its unit prints only the
summary line. Every output the module quotes is pinned: the count pins in
`expected/Q06.counts`, the statement freeze in `expected/Q06.freeze`, the
WRITE-card failure demos by their in-file `// EXPECT` lines, and the
divergence demos by their sealed sidecars under `expected/specimens/Q06/`.
No declaration carries a resource attribute (H3 is a budget item).
*/
module Q06_Machine {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import Power = Std.Arithmetic.Power
  import Mul = Std.Arithmetic.Mul

  // ===========================================================================
  // The prediction block.
  // ===========================================================================

  // item: Q06.P1dv S9 verdict
  /** **P1.** Skipping verification. Each file below is run directly (not
      through the course wrappers), on its own, in a scratch directory.

        Dafny, file p1.dfy, run as `dafny test --no-verify --target py p1.dfy`:
          module P1 {
            lemma Wrong(x: nat)
              ensures x + 1 == x
            {
            }

            @Test
            method Passes() {
              expect 1 + 1 == 2;
            }
          }

        Verus, file p1.rs, run as
        `verus p1.rs --crate-type=lib --no-verify --output-json`:
          use vstd::prelude::*;

          verus! {

          proof fn wrong(x: nat)
              ensures
                  x + 1 == x,
          {
          }

          } // verus!

      What is the exit code of each command, and what is the value of the
      `success` field in the JSON document that Verus prints?
      Answer form: `D:<exit> V:<exit> <true|false>`, each <exit> a numeral. */
  // CHECK P1dv

  // item: Q06.P2dv S9 verdict
  /** **P2.** Out of budget. A lemma whose proof runs out of the pinned
      resource limit (the limit the course wrappers pass to each verifier) is
      checked with `scripts/vcheck --json`, once in each language. What is
      the exit code of `scripts/vcheck` itself, and the value of the
      `verdict` field of the JSON document it prints?
      Answer form: `D:<exit> <verdict> V:<exit> <verdict>`, each <exit> a
      numeral and each <verdict> one of the words that field takes:
      `verified`, `failed`, `inconclusive`, `refused`, `killed(memory)`,
      `error`. */
  // CHECK P2dv

  // item: Q06.P5dv S11 verdict
  /** **P5.** A reveal in a narrow scope. What does `scripts/vcheck` say about
      each of these, verified on its own?

        Dafny:
          opaque function F(x: nat): nat
          {
            x + 1
          }

          lemma FAbove(x: nat)
            ensures F(x) > x
          {
            assert true by { reveal F(); }
          }

        Verus:
          #[verifier::opaque]
          pub open spec fn f(x: nat) -> nat {
              x + 1
          }

          pub proof fn lemma_f_above(x: nat)
              ensures
                  f(x) > x,
          {
              assert(true) by { reveal(f); }
          }

      Answer form: `D:<v> V:<v>`, each v one of `ok` (verifies), `fail` (a
      verification error), `timeout` (out of resource or time),
      `err:<stage>` (refused before verification; the stage as
      `scripts/vcheck` prints it: `parse` or `resolve`). */
  // CHECK P5dv

  // item: Q06.P6dv S12 verdict
  /** **P6.** Resource attributes. Three files, each holding one small lemma
      that verifies:

        [a] Dafny:
          lemma {:rlimit 1000} Small(x: nat)
            ensures x + 0 == x
          {
          }

        [b] Verus:
          #[verifier::rlimit(1)]
          pub proof fn lemma_small(x: nat)
              ensures
                  x + 0 == x,
          {
          }

        [c] Verus: the same as [b], with `#[verifier::rlimit(4)]`.

      For which of the three files does `scripts/vaudit` report a finding?
      Answer form: the labels in label order, separated by single spaces, or
      `none`. */
  // CHECK P6dv

  // item: Q06.P8dv S10 verdict
  /** **P8.** The libraries' own trusted parts. Dafny's bundled standard
      library and Verus's `vstd` each hold declarations that are trusted
      rather than proved.
      Dafny: when `scripts/vaudit` audits a unit that uses the standard
      library (this file's unit does), does its report list any finding
      located inside the standard library?
      Verus: when `scripts/vcheck` verifies a crate that uses `vstd` (every
      run carries `--no-cheating`), does it report the trusted sites inside
      `vstd`?
      Answer form: `D:<yes|no> V:<yes|no>`. */
  // CHECK P8dv

  // ===========================================================================
  // Test-out (closed book)
  // ===========================================================================

  // item: Q06.T1d S11
  // uses: trigger
  // pair: Q06.T1v
  /** **T1.** (test-out) A fact about every limb, used for limb 1.

      Reference: the hypothesis's trigger is `Head(Drop(s, k))`, so the
      solver instantiates it only for a term of that shape. `s[1]` is not
      one; the assertion names `Head(Drop(s, 1))`, which fires the
      hypothesis at `k = 1`, and `Head(Drop(s, 1))` unfolds to `s[1]`
      because `1 < |s|`. */
  lemma SecondLimb(s: seq<nat>)
    requires |s| > 1
    requires forall k {:trigger Head(Drop(s, k))} | 0 <= k < |s| :: Head(Drop(s, k)) < 100
    ensures s[1] < 100
  {
    assert Head(Drop(s, 1)) < 100;
  }

  // ===========================================================================
  // Worked example
  // ===========================================================================

  // item: Q06.W1d S11
  /** **W1.** An opaque function and a scoped `reveal`. Outside a `reveal`,
      the verifier knows `Twice` by its signature only. `reveal Twice();`
      inside an `assert … by { … }` unfolds it for that assertion alone: the
      asserted fact is what the rest of the proof can see, never the
      definition. */
  opaque function Twice(x: nat): nat
  {
    2 * x
  }

  lemma TwiceEven(x: nat)
    ensures Twice(x) % 2 == 0
  {
    assert Twice(x) == 2 * x by { reveal Twice(); }
    // Here the equation is known and the body of Twice is not: the
    // postcondition follows from the equation.
  }

  // ===========================================================================
  // WRITE cards (each: a success here, a pinned failure demo in specimens/Q06/)
  // ===========================================================================

  // item: Q06.C1d S11 write:trigger
  /** ### C1 — card: triggers (`{:trigger …}`).
      Jurisdiction: a quantified fact is used only for the terms that match
      its trigger, so a proof switches it on by mentioning such a term.
      Success: `OddBound` asserts a fact about `Odd(3)`, which fires the
      hypothesis at `i = 3`. Failure: specimens/Q06/card-c1d.dfy.specimen
      (the same lemma; no term of the trigger's shape appears). */
  function Odd(i: nat): nat
  {
    2 * i + 1
  }

  lemma OddBound(s: seq<nat>)
    requires |s| > 3
    requires forall i {:trigger Odd(i)} | 0 <= i < |s| :: s[i] < Odd(i)
    ensures s[3] < 7
  {
    assert s[3] < Odd(3);
  }

  // item: Q06.C2d S11 write:opaque-reveal
  /** ### C2 — card: `opaque` and a scoped `reveal`.
      Jurisdiction: an opaque definition stays folded until a `reveal`
      unfolds it, inside that reveal's scope only, so the solver sees the
      body exactly where a proof asks for it. Success: `MidBetween` reveals
      `Mid` for its whole body. Failure: specimens/Q06/card-c2d.dfy.specimen
      (the reveal is confined to an `assert … by` and the body is needed
      after it). */
  opaque function Mid(a: nat, b: nat): nat
  {
    (a + b) / 2
  }

  lemma MidBetween(a: nat, b: nat)
    requires a <= b
    ensures a <= Mid(a, b) <= b
  {
    reveal Mid();
  }

  // item: Q06.C3d S11 write:rlimit
  /** ### C3 — card: proofs that fit the resource limit.
      Jurisdiction: every unit verifies under one pinned resource limit; a
      proof that exhausts it gets an out-of-resource verdict, which says
      nothing about whether the goal is true or nearly proved. Make the
      proof fit by giving the solver the steps it does not find, never by
      raising the limit. Success: `FourthPowerMono` with four library facts
      about products. Failure: specimens/Q06/card-c3d.dfy.specimen (the same
      lemma with an empty body). */
  lemma FourthPowerMono(x: nat, y: nat)
    requires x <= y
    ensures x * x * x * x <= y * y * y * y
  {
    Mul.LemmaMulInequality(x, y, x);      // x * x <= y * x
    Mul.LemmaMulInequality(x, y, y);      // x * y <= y * y
    var a, b := x * x, y * y;
    Mul.LemmaMulInequality(a, b, a);      // a * a <= b * a
    Mul.LemmaMulInequality(a, b, b);      // a * b <= b * b
  }

  // item: Q06.C4d S12 write:property-test
  /** ### C4 — card: bounded property tests.
      Jurisdiction: before a proof, check a property of a candidate's outputs
      on chosen samples. The checker is a verified method whose postcondition
      is two-sided (`ok` exactly when every sample has the property), so no
      constant answer verifies; `@Test` methods run it with `expect` on a
      correct candidate (it must pass) and on a planted one (it must be
      rejected): `scripts/vcheck --test` on the unit. The verifier checks the
      checker; the test run checks the candidates. Success: `AllBelow` and
      the two tests below it. Failure: specimens/Q06/card-c4d.dfy.specimen (a
      one-sided checker, which a constant answer satisfies). */
  method AllBelow(f: nat -> nat, samples: seq<nat>, bound: nat) returns (ok: bool)
    ensures ok <==> forall k | 0 <= k < |samples| :: f(samples[k]) < bound
  {
    ok := true;
    var k := 0;
    while k < |samples|
      invariant 0 <= k <= |samples|
      invariant ok <==> forall j | 0 <= j < k :: f(samples[j]) < bound
      decreases |samples| - k
    {
      ok := ok && f(samples[k]) < bound;
      k := k + 1;
    }
  }

  // A candidate that clips to the limit 1000, and a planted one that lets
  // 1000 itself through.
  function Clip(x: nat): nat
  {
    if x < 1000 then x else 999
  }

  function ClipPlanted(x: nat): nat
  {
    if x <= 1000 then x else 999
  }

  @Test
  method ClipPasses() {
    var ok := AllBelow(Clip, [0, 999, 1000, 1001, BASE], 1000);
    expect ok;
  }

  @Test
  method ClipPlantedRejected() {
    var ok := AllBelow(ClipPlanted, [0, 999, 1000, 1001, BASE], 1000);
    expect !ok;
  }

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: Q06.H1d S11
  // uses: trigger
  // pair: Q06.H1v
  /** **H1.** The first prefix is below one limb's weight.

      Reference: the hypothesis fires only on a `Pow(k)` term. Asserting
      `Pow(1) == BASE` puts `Pow(1)` in front of the solver, which
      instantiates the hypothesis at `k = 1` (`ToNat(s[..1]) < Pow(1)`); the
      equation itself is one unfolding of `Pow`. */
  lemma FirstPrefix(s: seq<nat>)
    requires |s| >= 1
    requires forall k {:trigger Pow(k)} | 0 <= k <= |s| :: ToNat(s[..k]) < Pow(k)
    ensures ToNat(s[..1]) < BASE
  {
    assert Pow(1) == BASE;
  }

  // Given (not an item): two limbs packed into one number. Opaque: its body
  // is hidden from every proof that does not reveal it.
  opaque function Pack(lo: nat, hi: nat): nat
  {
    lo + BASE * hi
  }

  // item: Q06.H2d S11
  // uses: opaque-reveal
  // pair: Q06.H2v
  /** **H2.** Packing two limbs gives the value of the two-limb sequence.

      Reference: `reveal Pack();` unfolds `Pack` for the whole body. The
      value side unfolds one limb at a time: `ToNatCons(lo, [hi])` gives
      `ToNat([lo] + [hi]) == lo + BASE * ToNat([hi])`, `ToNatSingleton(hi)`
      gives `ToNat([hi]) == hi`, and the last assertion tells the solver
      that `[lo] + [hi]` is the sequence `[lo, hi]` of the statement. */
  lemma PackToNat(lo: nat, hi: nat)
    ensures Pack(lo, hi) == ToNat([lo, hi])
  {
    reveal Pack();  // did: unfolds Pack's body for this proof
    ToNatCons(lo, [hi]);
    ToNatSingleton(hi);
    assert [lo] + [hi] == [lo, hi];
  }

  // item: Q06.H3d S11
  // uses: rlimit
  /** **H3.** Two numbers below `Pow(n)` multiply to less than `Pow(2 * n)`.
      This attempt does not verify at the pinned resource limit:

          lemma TwoShifts(x: nat, y: nat, n: nat)
            requires x < Pow(n) && y < Pow(n)
            ensures x * y < Pow(2 * n)
          {
            PowIsStdPow(n);
            PowIsStdPow(2 * n);
            Power.LemmaPowAdds(BASE, n, n);
            Power.LemmaPowPositive(BASE, n);
          }

      Reference: the bridges and `LemmaPowAdds` give
      `Pow(2 * n) == Pow(n) * Pow(n)`; what the solver does not find on its
      own, at any budget, is the bound on the product.
      `Mul.LemmaMulUpperBound(x, p - 1, y, p - 1)` states it
      (`x * y <= (p - 1) * (p - 1)`), and `(p - 1) * (p - 1) < p * p` closes
      the gap. No resource attribute. */
  lemma TwoShifts(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(2 * n)
  {
    var p := Pow(n);
    PowIsStdPow(n);
    PowIsStdPow(2 * n);
    Power.LemmaPowAdds(BASE, n, n);
    Mul.LemmaMulUpperBound(x, p - 1, y, p - 1);
    assert (p - 1) * (p - 1) < p * p;
  }

  // Given (not an item): the reference split of a two-limb sum into its low
  // limb and its carry.
  function RefSplit(a: nat, b: nat): (nat, nat)
  {
    ((a + b) % BASE, (a + b) / BASE)
  }

  // item: Q06.H4d S12
  // uses: property-test
  // pair: Q06.H4v
  /** **H4.** A bounded property check of a limb adder.

      Reference: one pass over the samples that returns `false` at the first
      disagreement. The invariant says that every sample before `k` agrees,
      so the `false` exit has a witness (the sample at `k`) and the `true`
      exit has the whole `forall`. A constant body fails one side of the
      `<==>`. The suite below runs it: `AddCarryA` agrees with `RefSplit` on
      every boundary sample, and `AddCarryB` disagrees at `(1, BASE - 1)`,
      whose sum is exactly `BASE`. */
  method CheckSplit(f: (nat, nat) -> (nat, nat), samples: seq<(nat, nat)>) returns (ok: bool)
    ensures ok <==> forall k | 0 <= k < |samples| :: f(samples[k].0, samples[k].1) == RefSplit(samples[k].0, samples[k].1)
  {
    var k := 0;
    while k < |samples|
      invariant 0 <= k <= |samples|
      invariant forall j | 0 <= j < k :: f(samples[j].0, samples[j].1) == RefSplit(samples[j].0, samples[j].1)
      decreases |samples| - k
    {
      if f(samples[k].0, samples[k].1) != RefSplit(samples[k].0, samples[k].1) {
        return false;
      }
      k := k + 1;
    }
    return true;
  }

  // The samples and the two candidates the suite runs (given): limb pairs at
  // the carry boundary, a correct adder and a planted one.
  function Boundary(): seq<(nat, nat)>
  {
    [(0, 0), (1, BASE - 1), (BASE - 1, 1), (BASE - 1, BASE - 1), (BASE / 2, BASE / 2)]
  }

  function AddCarryA(a: nat, b: nat): (nat, nat)
  {
    if a + b < BASE then (a + b, 0) else (a + b - BASE, 1)
  }

  function AddCarryB(a: nat, b: nat): (nat, nat)
  {
    if a + b <= BASE then (a + b, 0) else (a + b - BASE, 1)
  }

  @Test
  method GoodPasses() {
    var ok := CheckSplit(AddCarryA, Boundary());
    expect ok;
  }

  @Test
  method PlantedRejected() {
    var ok := CheckSplit(AddCarryB, Boundary());
    expect !ok;
  }

  // ===========================================================================
  // Final section: divergence card.
  // ===========================================================================

  // item: Q06.C5dv S9 diverge:q06-c5
  /** ### C5 — divergence card. Demos: specimens/Q06/card-c5dv-d.dfy.specimen
      and specimens/Q06/card-c5dv-v.rs.specimen. */
}

/*
AUDIT ROWS (learner-owned; advisory: no script reads this block and no gate
depends on it). Before the moderate-tier viva (/viva Q06), once
`scripts/firsttry.sh <ID> --report --strict` passes for Q04, Q05 and Q06,
write on each line below the number of findings you expect `scripts/vaudit`
to report for that target and their kinds; then run `scripts/vaudit` on each
target and write whether the line held. The viva opens on any line that did
not hold.
  dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy   expected:        held:
  dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy       expected:        held:
  verus/q/q04_proof_craft                          expected:        held:
  dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy         expected:        held:
  verus/q/q04_proof_craft/src/exit.rs              expected:        held:
  dafny/Q/Q05_Frames/std/Q05_Frames.dfy            expected:        held:
  verus/q/q05_frames                               expected:        held:
  dafny/Q/Q05_Frames/exit/Q05_Exit.dfy             expected:        held:
  verus/q/q05_frames/src/exit.rs                   expected:        held:
  dafny/Q/Q06_Machine/std/Q06_Machine.dfy          expected:        held:
  verus/q/q06_machine                              expected:        held:
  dafny/Q/Q06_Machine/exit/Q06_Exit.dfy            expected:        held:
  verus/q/q06_machine/src/exit.rs                  expected:        held:
*/

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line.
  setup 5 · test-out 10 · read 48 · worked 25 · cards 8 · predicts 22 ·
  holes 36 · property tests 15 · statistics by hand 30 · EVAL.md v0 15 ·
  TRUST.md v0 10 · agent 15 · paper 15 · exit 22 · calib 5 · total 281
  (+ tier viva 30)
*/
