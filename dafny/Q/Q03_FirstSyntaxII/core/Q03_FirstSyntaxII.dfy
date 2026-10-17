/*!
# Q03 — First syntax II: modes, logic, tooling, trust (Exercises)

Imports: the given BigNat spine, layers L1 (`QG_L1_BigNat`) and L2
(`QG_L2_BigNat`), and nothing else: no earlier exercise file. The layers are
frozen and complete; read them, never edit them.

How to work this file:
1. Test-out first, closed book: T1 (below) before any reading, without its
   hints. Then run `scripts/firsttry.sh Q03 --check`, which records your first
   try (it runs T1's commented checks in a scratch copy), and only then
   uncomment those checks. If both files' T1 pass on that first try, you may
   skip the chapter section on ghost variables.
2. Predictions next: fill every slot of the prediction block (the verdict
   answers go in slots/Q03.slots), of specimens/Q03/P*.specimen and of
   dafny/checks/Q03_checks.dfy, then record the first tries with
   `scripts/firsttry.sh Q03 --check`, before you run anything they are about.
3. Replace each hole, then uncomment the checks beneath it.
4. Done = `scripts/vcheck --gate dafny/Q/Q03_FirstSyntaxII/core` prints only
   the summary line and exits 0, `scripts/vaudit dafny/Q/Q03_FirstSyntaxII/core`
   reports no finding, AND `scripts/firsttry.sh Q03 --report --strict` exits 0.
5. Stuck for 20 minutes? /tutor Q03.

This file ships with exactly 5 holes: T1 (test-out) and H1–H4, each counted by
`scripts/vcheck`. Q03 as a whole ships 10 holes (5 here, 5 in the Verus file
verus/q/q03_first_syntax_ii/src/lib.rs), of which 2 are test-out items (T1 in
each file); 14 predictions (10, plus the 4 fake-green diagnoses P11–P14); and
6 exit items (the exit files ship 2 + 3 holes).
Commit every prediction BEFORE you run anything it is about, open later files,
or read CI, the registry or the plan: their checks and headers give some
predictions away.

Item kinds: T test-out (closed book, first) · P prediction (a slot) · W worked
example (given, finished) · C card (WRITE: a success here and a failure demo in
specimens/Q03/; RECOGNISE; divergence, in the final section) · H one-hole item
· X exit item (the exit files). Slots: a verdict switch `// SLOT: CHECK <item>`
here takes its answer in slots/Q03.slots (`P1dv = ???` → `P1dv = "<answer>"`);
a value or obligation slot is the `// SLOT:` line itself. Fill a slot, record
the first try, and only then enable it: `// SLOT: CHECK P1dv` becomes
`// CHECK P1dv`, `// SLOT: FAILS …` becomes `// FAILS …`, and a value slot
`// SLOT: <check>` becomes the live check.

Exit (closed book): dafny/Q/Q03_FirstSyntaxII/exit/Q03_Exit.dfy and
verus/q/q03_first_syntax_ii/src/exit.rs, scored once by
`scripts/firsttry.sh Q03 --exit` (threshold 5 of 6).

Contract v0 (agent rung 3): no agent file. You write contract v0 by hand into
CLAUDE.md, below the learner-owned marker; `/contract Q03` refuses by design.
*/
module Q03_FirstSyntaxII {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat

  // ===========================================================================
  // Given in this file (not items): the option type and the limb subset type.
  // ===========================================================================

  // An optional value.
  datatype Opt<T> = None | Some(value: T)

  // One limb: a natural number below BASE.
  type Limb = x: nat | x < BASE

  // ===========================================================================
  // Test-out (closed book, before any reading)
  // ===========================================================================

  // item: Q03.T1d S7
  // uses: ghost, witness
  // pair: Q03.T1v
  /** **T1.** (test-out) The largest limb of a non-empty sequence.
      Method clause: keep the index of the current maximum in a `ghost var`.
      Which index proves the `exists` half of the postcondition, and how does
      the loop keep track of it? */
  method MaxLimb(s: seq<nat>) returns (m: nat)
    requires |s| > 0
    ensures (forall i | 0 <= i < |s| :: s[i] <= m) && (exists i | 0 <= i < |s| :: s[i] == m)
  {
    assume false;
  }
  // Hint(1): a loop over the indices from 1, with one invariant per half of
  //    the postcondition (the second over the prefix read so far).
  // Hint(2): the ghost index `w` satisfies `0 <= w < |s| && s[w] == m`.

  method MaxLimbCheck() {
    // Uncomment as you go:
    // var m := MaxLimb([7]);
    // assert m == 7;
    // var k := MaxLimb([0, 0]);
    // assert k == 0;
  }

  // ===========================================================================
  // The prediction block. Commit every prediction of this module before you
  // read past this block, and record the first tries:
  //     scripts/firsttry.sh Q03 --check
  // Verdict answers go in slots/Q03.slots; the other predictions live in
  // specimens/Q03/ (P3, P10, P11–P14) and dafny/checks/Q03_checks.dfy (P9).
  // The Verus file's prediction block holds P4.
  // Verdict vocabulary for `D:<v> V:<v>` answers: `ok` (verifies), `fail` (a
  // verification error), `timeout` (out of resource or time), `err:<stage>`
  // (refused before verification; <stage> as scripts/vcheck prints it:
  // `parse` or `resolve`).
  // ===========================================================================

  // item: Q03.P1dv S10 verdict
  /** **P1.** Compiled code. Each file holds a method (Dafny) or an exec fn
      (Verus) specified to return 7, whose body first assumes `false` and then
      returns 8, and a test that calls it:

        Dafny:
          method Seven() returns (r: int)
            ensures r == 7
          {
            assume false;
            r := 8;
          }

          @Test
          method SevenTest() {
            var r := Seven();
            expect r == 7;
          }

        Verus:
          pub fn seven() -> (r: u64)
              ensures r == 7,
          {
              assume(false);
              8
          }

          #[test]
          fn seven_test() {
              assert_eq!(seven(), 7);
          }

      Both are compiled and the tests run (Dafny `dafny test --allow-warnings`,
      Verus `verus --compile --test`). What value does each call of `Seven` /
      `seven` return when it runs?
      Answer form: `D:<numeral> V:<numeral>` (one space between the halves). */
  // SLOT: CHECK P1dv

  // item: Q03.P2dv S13 verdict
  /** **P2.** Contradictory assumptions. Each of these sits alone in a file of
      its own and is checked with `scripts/vcheck --gate`:

        Dafny:
          lemma Contra(x: nat)
            requires x > 5 && x < 3
            ensures false
          {
          }

        Verus:
          pub proof fn lemma_contra(x: nat)
              requires
                  x > 5,
                  x < 3,
              ensures
                  false,
          {
          }

      What does each check report?
      Answer form: `D:<v> V:<v>` with the verdict vocabulary above. */
  // SLOT: CHECK P2dv

  // item: Q03.P5dv S9 verdict
  /** **P5.** Signals a naive grader trusts.
      Dafny half: `dafny audit` run directly (not through scripts/vaudit) on a
      file whose audit report lists one finding. What is its exit code?
      Verus half: `verus <file> --crate-type=lib` run directly (no other
      option, so no `--no-cheating`; not through scripts/vcheck) on a file
      that holds `use vstd::prelude::*;` and, inside `verus! { }`, these
      three proof fns:

          pub proof fn lemma_a(x: int)
              ensures
                  x + x == 2 * x,
          {
          }

          pub proof fn lemma_b(x: int)
              ensures
                  x + 2 > x,
          {
              assume(false);
          }

          #[verifier::external_body]
          pub proof fn lemma_c(x: int)
              ensures
                  x + 1 > x,
          {
          }

      Its last line has the form `verification results:: <N> verified, <E>
      errors`. What is N?
      Answer form: `D:<exit code> V:<N>`, both numerals. */
  // SLOT: CHECK P5dv

  // item: Q03.P6dv S10 verdict
  /** **P6.** Stages. Each file holds one type error and one false assertion:

        Dafny:
          method M() {
            var b: bool := 1;
            assert 1 + 1 == 3;
          }

        Verus:
          fn m() {
              let b: bool = 1;
              assert(1 + 1 == 3);
          }

      How many errors does `scripts/vcheck` report on each file, and at which
      stage does it stop?
      Answer form: `D:<n> <stage> V:<n> <stage>`, <n> a numeral and <stage>
      one of `parse`, `resolve`, `verify` (as scripts/vcheck prints it). */
  // SLOT: CHECK P6dv

  // item: Q03.P7dv S11 verdict
  /** **P7.** Failure messages. In this unit (this file's dfyconfig.toml, and
      for Verus this module's crate), two empty-bodied lemmas about a counting
      function, one true and one false:

        Dafny:
          function Count(n: nat): nat
            decreases n
          {
            if n == 0 then 0 else 1 + Count(n - 1)
          }

          lemma CountIsN(n: nat)
            ensures Count(n) == n
          {
          }

          lemma CountIsNPlusOne(n: nat)
            ensures Count(n) == n + 1
          {
          }

        Verus:
          pub open spec fn count(n: nat) -> nat
              decreases n,
          {
              if n == 0 { 0 } else { 1 + count((n - 1) as nat) }
          }

          pub proof fn lemma_count_is_n(n: nat)
              ensures count(n) == n,
          {
          }

          pub proof fn lemma_count_is_n_plus_one(n: nat)
              ensures count(n) == n + 1,
          {
          }

      Does each tool print the same message for the true lemma as for the
      false one (ignoring the line numbers)?
      Answer form: `D:<same|different> V:<same|different>`. */
  // SLOT: CHECK P7dv

  // item: Q03.P8dv S8 verdict
  /** **P8.** Weakest precondition (the wp lab is on paper). For the program

          x := x * 2;
          y := x + 1;

      over integers `x` and `y`, and the postcondition `y > 7`, which option is
      equivalent to the weakest precondition?
          a) x > 3     b) x > 7     c) x + 1 > 7     d) x > 6
      Answer form: one letter, `a`, `b`, `c` or `d`. */
  // SLOT: CHECK P8dv

  // ===========================================================================
  // Worked example
  // ===========================================================================

  // item: Q03.W1d S7
  /** **W1.** A subset type that 0 does not inhabit, a function over it, and a
      ghost helper. A subset type must be inhabited; Dafny tries 0 by default,
      so a predicate that rejects 0 needs an explicit `witness`. */
  type NZDigit = x: nat | 1 <= x <= 9 witness 1

  // A function over the subset type: the argument's constraint is a fact.
  function DigitPred(d: NZDigit): nat
    ensures DigitPred(d) < 9
  {
    d - 1
  }

  // A ghost helper: specification only, erased from compiled code.
  ghost predicate AllDigits(s: seq<nat>)
  {
    forall i | 0 <= i < |s| :: 1 <= s[i] <= 9
  }

  method DigitDemo() {
    var d: NZDigit := 7;
    assert DigitPred(d) == 6;     // the body of DigitPred unfolds once
    ghost var s: seq<nat> := [d, 1];
    assert AllDigits(s);          // both elements are digits
  }

  // ===========================================================================
  // WRITE cards (each: a success here, a pinned failure demo in specimens/Q03/)
  // ===========================================================================

  // item: Q03.C1d S7 write:ghost
  /** ### C1 — card: ghost variables (`ghost var`).
      Jurisdiction: values the proof needs and the program never uses; they
      are checked, then erased. Success: `CountZeroLimbs` keeps the limbs it
      has read in a ghost sequence. Failure: specimens/Q03/card-c1d.dfy.specimen
      (a ghost value used by compiled code). */
  ghost function ZeroCount(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else ZeroCount(s[..|s| - 1]) + (if s[|s| - 1] == 0 then 1 else 0)
  }

  method CountZeroLimbs(s: seq<nat>) returns (n: nat)
    ensures n == ZeroCount(s)
  {
    n := 0;
    ghost var seen: seq<nat> := [];
    var i := 0;
    while i < |s|
      invariant 0 <= i <= |s|
      invariant seen == s[..i]
      invariant n == ZeroCount(seen)
      decreases |s| - i
    {
      assert (seen + [s[i]])[..|seen|] == seen;
      seen := seen + [s[i]];
      if s[i] == 0 {
        n := n + 1;
      }
      i := i + 1;
    }
    assert seen == s;
  }

  // item: Q03.C2d S7 write:exec-check
  /** ### C2 — card: a runtime check that hands the verifier a fact.
      Jurisdiction: a precondition the caller cannot promise; test it in code
      and return the answer in an option. Success: `SafeDiv`. Failure:
      specimens/Q03/card-c2d.dfy.specimen (the unchecked division). */
  method SafeDiv(a: nat, b: nat) returns (r: Opt<nat>)
    ensures (r.Some? <==> b != 0) && (r.Some? ==> r.value == a / b)
  {
    if b != 0 {
      r := Some(a / b);
    } else {
      r := None;
    }
  }

  // item: Q03.C3d S13 write:witness
  /** ### C3 — card: witnesses.
      Jurisdiction: an `exists` goal is proved by naming a term that works.
      Success: `ExistsSquareFour` names 2. Failure:
      specimens/Q03/card-c3d.dfy.specimen (the same lemma, empty body). */
  ghost function Square(i: nat): nat
  {
    i * i
  }

  lemma ExistsSquareFour()
    ensures exists i: nat :: Square(i) == 4
  {
    assert Square(2) == 4;
  }

  // item: Q03.C4d S7 write:subset-type
  /** ### C4 — card: subset types.
      Jurisdiction: a base type plus a predicate every value carries; the
      verifier checks the predicate where a value enters the type and assumes
      it where a value is used. Success: `Small` and `Twice`. Failure:
      specimens/Q03/card-c4d.dfy.specimen (a type declared with a bad
      witness). */
  type Small = x: nat | x < 10

  function Twice(x: Small): nat
    ensures Twice(x) < 20
  {
    2 * x
  }

  // ===========================================================================
  // RECOGNISE cards (Rosetta: Dafny column here, Verus column in lib.rs)
  // ===========================================================================

  // item: Q03.C9dv S11 recognise:trigger
  /** ### C9 — Rosetta card: quantifier triggers (recognise).
      Dafny `{:trigger s[i]}` · Verus `#[trigger] s[i]`: the term whose
      appearance lets the solver use a `forall` fact. Both columns verify;
      the Verus column is `trigger_rosetta` in the Verus file. */
  lemma TriggerRosetta(s: seq<nat>, k: nat)
    requires forall i {:trigger s[i]} | 0 <= i < |s| :: s[i] < 100
    requires k < |s|
    ensures s[k] < 100
  {
  }

  // item: Q03.C10dv S12 recognise:audit
  /** ### C10 — Rosetta card: the assumption audit (recognise).
      Dafny: `scripts/vaudit <file>` runs `dafny audit` over every root plus
      the course lint. Verus: `scripts/vcheck` runs Verus with
      `--no-cheating`, and `scripts/vaudit <crate>` adds the course lint.
      Each finding line starts with its location and its kind:
          <path>:<line>: <kind>
      An empty report is a clean audit. */

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: Q03.H1d S7
  // uses: lemma-call
  // pair: Q03.H1v
  /** **H1.** Adding one limb adds its value: for valid limbs `s` and a limb
      `d`, `ToNat(AddLimb(s, d)) == ToNat(s) + d`. Prove it by induction on
      `s`. Which case of `AddLimb` needs the induction hypothesis, and with
      which limb? */
  lemma AddLimbToNat(s: seq<nat>, d: nat)
    requires Valid(s) && d < BASE
    ensures ToNat(AddLimb(s, d)) == ToNat(s) + d
    decreases |s|
  // Hint(1): one case per branch of `AddLimb`; the L2 helpers `ToNatSingleton`,
  //    `ToNatCons` and `ValidTail` each close one step.
  // Hint(2): in the carry case, the recursive call is `AddLimbToNat(s[1..], 1)`.

  lemma AddLimbToNatCheck() {
    // Uncomment as you go:
    // AddLimbToNat([], 0);
    // assert ToNat(AddLimb([], 0)) == 0;
  }

  // item: Q03.H2d S7
  // uses: lemma-call
  // pair: Q03.H2v
  /** **H2.** `FromNat` is correct: its limbs are valid and their value is the
      number it started from. Prove it by induction on `n`. Along which
      measure does `FromNat` recurse, and so on which argument do you call
      the lemma again? */
  lemma FromNatCorrect(n: nat)
    ensures Valid(FromNat(n)) && ToNat(FromNat(n)) == n
    decreases n
  // Hint(1): for `n > 0`, `FromNat(n)` is one limb consed onto
  //    `FromNat(n / BASE)`.
  // Hint(2): `ToNatCons` gives the value, `ValidCons` the validity.

  lemma FromNatCorrectCheck() {
    // Uncomment as you go:
    // FromNatCorrect(BASE + 3);
    // assert ToNat(FromNat(BASE + 3)) == BASE + 3;
  }

  // item: Q03.H3d S13
  // uses: witness, assert
  // pair: Q03.H3v
  /** **H3.** Some canonical limb sequence has the value 5. Which sequence is
      the witness, and what must the solver know about it before it can use
      it for the `exists`? */
  lemma ExistsCanonicalFive()
    ensures exists s: seq<nat> :: Canonical(s) && ToNat(s) == 5
  // Hint(1): name the witness in an `assert` that states both conjuncts for it.
  // Hint(2): an L2 helper gives the value of a one-limb sequence.

  // item: Q03.H4d S7
  // uses: exec-check, subset-type
  // pair: Q03.H4v
  /** **H4.** A checked conversion from `nat` to `Limb`: `Some(x)` exactly when
      `x` fits in a limb, `None` otherwise. Where does the fact that makes
      `Some(x)` an `Opt<Limb>` come from? */
  method TryLimb(x: nat) returns (r: Opt<Limb>)
    ensures (r.Some? <==> x < BASE) && (r.Some? ==> r.value == x)
  {
    assume false;
  }
  // Hint: one `if` on the limb bound.

  method TryLimbCheck() {
    // Uncomment as you go:
    // var r := TryLimb(5);
    // assert r.Some? && r.value == 5;
    // var q := TryLimb(BASE);
    // assert q.None?;
  }

  // ===========================================================================
  // Final section: divergence cards. Record every prediction of this module
  // (scripts/firsttry.sh Q03 --check) before you read on or open their demos.
  // ===========================================================================

  // item: Q03.C6dv S10 diverge:q03-c6
  /** ### C6 — divergence card. Demos: specimens/Q03/card-c6dv-d.dfy.specimen
      and specimens/Q03/card-c6dv-v.rs.specimen. */

  // item: Q03.C7dv S13 diverge:q03-c7
  /** ### C7 — divergence card. Demos: specimens/Q03/card-c7dv-d.dfy.specimen
      and specimens/Q03/card-c7dv-v.rs.specimen. */

  // item: Q03.C8dv S12 diverge:q03-c8
  /** ### C8 — divergence card. Demos: specimens/Q03/card-c8dv-d.dfy.specimen
      and specimens/Q03/card-c8dv-v.rs.specimen. */
}

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line.
  setup 5 · test-out 10 · read 45 · worked 26 · cards 12 · predicts 24 ·
  holes 32 · wp on paper 20 · fake-green specimens 12 · contract v0 20 ·
  paper 15 · exit 25 · calib 5 · total 251 (+ tier viva 30)
*/
