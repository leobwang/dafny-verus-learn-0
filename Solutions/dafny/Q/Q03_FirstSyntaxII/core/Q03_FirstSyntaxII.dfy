/*!
# Q03 — First syntax II: modes, logic, tooling, trust (Reference Solution)

Hole-free reference for `dafny/Q/Q03_FirstSyntaxII/core/Q03_FirstSyntaxII.dfy`
(author-only; never learner-visible). Same module, imports, names,
statements, item markers and order as the exercise file. Every hole is
filled, every check is live, and every verdict switch is enabled; the verdict
answers are in `Solutions/slots/Q03.slots`, their hashes in
`expected/Q03.pins`.

The file is silent: `scripts/vcheck --ref` on its unit prints only the
summary line. Every output the module quotes is pinned: the count pins in
`expected/Q03.counts`, the statement freeze in `expected/Q03.freeze`, the
WRITE-card failure demos by their in-file `// EXPECT` lines, and the
divergence demos by their sidecars under `expected/specimens/Q03/`.
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

      Reference: the ghost index `w` is the witness of the `exists` half of
      the postcondition. The invariant `s[w] == m` keeps it pointing at the
      current maximum, so at the end `exists i :: s[i] == m` has the term
      `s[w]` to instantiate. It costs nothing at run time: `w` is erased. */
  method MaxLimb(s: seq<nat>) returns (m: nat)
    requires |s| > 0
    ensures (forall i | 0 <= i < |s| :: s[i] <= m) && (exists i | 0 <= i < |s| :: s[i] == m)
  {
    m := s[0];
    ghost var w := 0;
    var i := 1;
    while i < |s|
      invariant 1 <= i <= |s|
      invariant 0 <= w < |s| && s[w] == m
      invariant forall j | 0 <= j < i :: s[j] <= m
      decreases |s| - i
    {
      if s[i] > m {
        m := s[i];
        w := i;
      }
      i := i + 1;
    }
  }

  method MaxLimbCheck() {
    var m := MaxLimb([7]);
    assert m == 7;
    var k := MaxLimb([0, 0]);
    assert k == 0;
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
  // CHECK P1dv

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
  // CHECK P2dv

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
  // CHECK P5dv

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
  // CHECK P6dv

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
  // CHECK P7dv

  // item: Q03.P8dv S8 verdict
  /** **P8.** Weakest precondition (the wp lab is on paper). For the program

          x := x * 2;
          y := x + 1;

      over integers `x` and `y`, and the postcondition `y > 7`, which option is
      equivalent to the weakest precondition?
          a) x > 3     b) x > 7     c) x + 1 > 7     d) x > 6
      Answer form: one letter, `a`, `b`, `c` or `d`. */
  // CHECK P8dv

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
  /** **H1.** Adding one limb adds its value.

      Reference: induction on `s`, following the three cases of `AddLimb`.
      Empty: the result is `[d]` or `[]` (`ToNatSingleton`). No carry: one
      Horner step (`ToNatCons`) with the tail unchanged. Carry: the tail is
      valid (`ValidTail`), the induction hypothesis adds the carry 1 to it,
      and one Horner step puts the low limb `s[0] + d - BASE` back:
      `s[0] + d - BASE + BASE * (ToNat(s[1..]) + 1) == s[0] + d + BASE * ToNat(s[1..])`. */
  lemma AddLimbToNat(s: seq<nat>, d: nat)
    requires Valid(s) && d < BASE
    ensures ToNat(AddLimb(s, d)) == ToNat(s) + d
    decreases |s|
  {
    if |s| == 0 {
      ToNatSingleton(d);
    } else if s[0] + d < BASE {
      ToNatCons(s[0] + d, s[1..]);
    } else {
      ValidTail(s);
      AddLimbToNat(s[1..], 1);
      ToNatCons(s[0] + d - BASE, AddLimb(s[1..], 1));
    }
  }

  lemma AddLimbToNatCheck() {
    AddLimbToNat([], 0);
    assert ToNat(AddLimb([], 0)) == 0;
    AddLimbToNat([BASE - 1], 1);
    assert ToNat(AddLimb([BASE - 1], 1)) == ToNat([BASE - 1]) + 1;
  }

  // item: Q03.H2d S7
  // uses: lemma-call
  // pair: Q03.H2v
  /** **H2.** `FromNat` is correct: valid limbs, and the value it started from.

      Reference: induction on `n` along `FromNat`'s own recursion (`n / BASE`).
      For `n > 0`, `FromNat(n) == [n % BASE] + FromNat(n / BASE)`; the
      induction hypothesis gives the tail, `ToNatCons` gives the value
      `n % BASE + BASE * (n / BASE) == n`, and `ValidCons` the validity
      (`n % BASE < BASE`). */
  lemma FromNatCorrect(n: nat)
    ensures Valid(FromNat(n)) && ToNat(FromNat(n)) == n
    decreases n
  {
    if n > 0 {
      FromNatCorrect(n / BASE);
      ToNatCons(n % BASE, FromNat(n / BASE));
      ValidCons(n % BASE, FromNat(n / BASE));
    }
  }

  lemma FromNatCorrectCheck() {
    FromNatCorrect(BASE + 3);
    assert ToNat(FromNat(BASE + 3)) == BASE + 3;
  }

  // item: Q03.H3d S13
  // uses: witness, assert
  // pair: Q03.H3v
  /** **H3.** Some canonical limb sequence has the value 5.

      Reference: the witness is `[5]`. `ToNatSingleton(5)` gives its value;
      the `assert` puts the term `[5]` in front of the solver, which then
      instantiates the `exists` with it (`Canonical([5])` holds by
      definition: `5 < BASE` and the top limb is not 0). */
  lemma ExistsCanonicalFive()
    ensures exists s: seq<nat> :: Canonical(s) && ToNat(s) == 5
  {
    ToNatSingleton(5);
    assert Canonical([5]) && ToNat([5]) == 5;
  }

  // item: Q03.H4d S7
  // uses: exec-check, subset-type
  // pair: Q03.H4v
  /** **H4.** A checked conversion from `nat` to `Limb`.

      Reference: the runtime test `x < BASE` is exactly the fact the subset
      type `Limb` demands, so inside the `then` branch `Some(x)` is an
      `Opt<Limb>`; the other branch returns `None`. */
  method TryLimb(x: nat) returns (r: Opt<Limb>)
    ensures (r.Some? <==> x < BASE) && (r.Some? ==> r.value == x)
  {
    if x < BASE {
      r := Some(x);
    } else {
      r := None;
    }
  }

  method TryLimbCheck() {
    var r := TryLimb(5);
    assert r.Some? && r.value == 5;
    var q := TryLimb(BASE);
    assert q.None?;
    var e := TryLimb(BASE - 1);
    assert e.Some? && e.value == BASE - 1;
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
