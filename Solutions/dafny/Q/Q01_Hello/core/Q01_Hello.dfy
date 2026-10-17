/*!
# Q01 — Hello, Dafny and Verus: the whole map (Reference Solution)

Hole-free reference for `dafny/Q/Q01_Hello/core/Q01_Hello.dfy`. Same module, item
markers, declarations and order as the learner file; every hole is filled, every
check is live, and every slot switch is enabled. Verdict answers live in
`Solutions/slots/Q01.slots` (their hashes in `expected/Q01.pins`); the evidence for
each answer is in `Solutions/plans/Q01-Q03-author-notes.md` §2 and in the DV2a Q01
lane report.

Every output the course quotes for this file is pinned: the unit's count pin
(`expected/Q01.counts`), the WRITE-card demos' in-file EXPECT lines, the
false-friends sidecars. The file is silent: `scripts/vcheck --ref` on its unit prints
only the summary line.
*/
module Q01_Hello {
  import opened QG_L1_BigNat

  // =====================================================================================
  // Prediction block (Q01's verdict items; the other predictions are P3d, P4v and P6v in
  // specimens/Q01/ and P5d in dafny/checks/Q01_checks.dfy)
  // =====================================================================================

  // item: Q01.P1dv S1 verdict
  /** **P1dv.** Subtraction of naturals in executable code. What does `scripts/vcheck`
      say about each of these, verified on its own?

      Dafny:
          method Sub(x: nat, y: nat) returns (d: nat)
          {
            d := x - y;
          }

      Verus:
          fn sub(x: u64, y: u64) -> (d: u64)
          {
              x - y
          }

      Answer form: `D:<v> V:<v>`, each v one of `ok` (verifies), `fail` (a verification
      error), `timeout` (out of resource or time), `err:<stage>` (refused before
      verification; the stage as `scripts/vcheck` prints it: `parse` or `resolve`).
      Reference: the subset constraint of `nat` fails in Dafny; the `u64` underflow
      obligation fails in Verus. */
  // CHECK P1dv

  // item: Q01.P2dv S2 verdict
  /** **P2dv.** The same subtraction in specification code.

      Dafny:
          function Sub(x: nat, y: nat): nat
          {
            x - y
          }

      Verus:
          spec fn sub(x: nat, y: nat) -> nat
          {
              x - y
          }

      Answer form: as P1dv. Reference: Dafny checks the `nat` subset constraint of the
      result (a verification error); a Verus `nat - nat` is an `int`, and returning it as
      `nat` is a type error at stage resolve. */
  // CHECK P2dv

  // item: Q01.P7dv S4 verdict
  /** **P7dv.** The worked lemma of layer L1, with its `decreases` line removed.

      Dafny (in a copy of dafny/given/Q/QG_L1_BigNat.dfy):
          lemma ToNatAppendZero(s: seq<nat>)
            ensures ToNat(s + [0]) == ToNat(s)
          {
            if |s| == 0 {
              assert s + [0] == [0];
            } else {
              assert (s + [0])[1..] == s[1..] + [0];
              ToNatAppendZero(s[1..]);
            }
          }

      Verus (in a copy of verus/given/qg_bignat_l1/src/lib.rs):
          pub proof fn lemma_seq_to_nat_push_zero(s: Seq<u64>)
              ensures
                  seq_to_nat(s.push(0)) == seq_to_nat(s),
          {
              if s.len() == 0 {
                  assert(s.push(0).drop_first() =~= Seq::<u64>::empty());
                  assert(seq_to_nat(Seq::<u64>::empty()) == 0);
              } else {
                  assert(s.push(0).drop_first() =~= s.drop_first().push(0));
                  lemma_seq_to_nat_push_zero(s.drop_first());
              }
          }

      Answer form: as P1dv. Reference: Dafny supplies a default measure for the
      recursive lemma and verifies it; Verus refuses a recursive fn without a
      `decreases` clause at stage resolve. */
  // CHECK P7dv

  // item: Q01.P8dv S9 verdict
  /** **P8dv.** Exit codes. Each file's only problem is one false assertion, and each is
      run directly by its tool with no other option (not through `scripts/vcheck`):
      `dafny verify p8.dfy` and `verus p8.rs --crate-type=lib`.

      p8.dfy:
          module P8 {
            method Check(x: nat)
            {
              assert x + 1 > x + 2;
            }
          }

      p8.rs:
          use vstd::prelude::*;
          verus! {
          fn check(x: u64) {
              assert(x < x);
          }
          } // verus!

      Answer form: `D:<exit> V:<exit>`, each a numeral. Reference: Dafny reports a
      verification error with exit 4; Verus exits 1 on any error. `scripts/vcheck`
      maps both to its own exit 1. */
  // CHECK P8dv

  // item: Q01.P9dv S11 verdict
  /** **P9dv.** A nonlinear inequality over three variables, the lemma body empty, through
      `scripts/vcheck` at the course limits.

      Dafny:
          lemma ProductOrder(a: int, b: int, c: int)
            requires 0 < a < b && 1 < c
            ensures a * a * c < b * b * c
          {
          }

      Verus:
          proof fn product_order(a: int, b: int, c: int)
              requires
                  0 < a < b,
                  1 < c,
              ensures
                  a * a * c < b * b * c,
          {
          }

      Answer form: as P1dv. Reference: Dafny's solver searches nonlinear arithmetic
      and exhausts the pinned resource limit (out of resource, all three seeds); Verus
      leaves nonlinear arithmetic off by default and reports the postcondition
      unproved. */
  // CHECK P9dv

  // item: Q01.P10dv S12 verdict
  /** **P10dv.** Hole visibility. Each file holds one open proof hole and nothing else
      wrong; each is run directly by the two commands of P8dv.

      p10.dfy:
          module P10 {
            lemma Open(x: nat)
              ensures x + 0 == x
          }

      p10.rs:
          use vstd::prelude::*;
          verus! {
          proof fn open(x: nat)
              ensures
                  x + 0 == x,
          {
              assume(false);
          }
          } // verus!

      Answer form: `D:<exit> <yes|no> V:<exit> <yes|no>`: each tool's exit code, and
      whether its output mentions the hole. Reference: Dafny warns about the bodyless
      lemma and, without --allow-warnings, exits 2; Verus verifies the file silently,
      exit 0 (only `--no-cheating` reports an `assume`). */
  // CHECK P10dv

  // item: Q01.P11dv S13 verdict
  /** **P11dv.** A "maximum" with a weak postcondition and a wrong body.

      Dafny:
          method WeakMax(a: nat, b: nat) returns (m: nat)
            ensures m >= a && m >= b
          {
            m := a + b;
          }

      Verus:
          fn weak_max(a: u64, b: u64) -> (m: u64)
              requires
                  a <= 1000,
                  b <= 1000,
              ensures
                  m >= a && m >= b,
          {
              a + b
          }

      Answer form: as P1dv. Reference: both verify; the postcondition does not say that
      `m` is one of the arguments, so `a + b` meets it (H1d's third conjunct is the
      repair). */
  // CHECK P11dv

  // =====================================================================================
  // Worked examples
  // =====================================================================================

  // item: Q01.W1d S3
  /** **W1d.** The L1 worked lemma, proved again with an `assert` after each step that
      states what the verifier knows at that point. */
  lemma ToNatAppendZeroStepwise(s: seq<nat>)
    ensures ToNat(s + [0]) == ToNat(s)
    decreases |s|
  {
    if |s| == 0 {
      assert s + [0] == [0];
    } else {
      // Dropping the low limb of `s + [0]` leaves the rest of `s`, then the zero.
      assert (s + [0])[1..] == s[1..] + [0];
      // The definition of ToNat, read on `s + [0]`.
      assert ToNat(s + [0]) == s[0] + BASE * ToNat(s[1..] + [0]);
      // The same fact for the shorter sequence (the recursive call).
      ToNatAppendZeroStepwise(s[1..]);
      assert ToNat(s[1..] + [0]) == ToNat(s[1..]);
      // The definition of ToNat, read on `s`: both sides now agree.
      assert ToNat(s) == s[0] + BASE * ToNat(s[1..]);
    }
  }

  // item: Q01.W2d S1
  /** **W2d.** A first verified method: the low limb of a non-empty limb sequence. */
  method LowLimb(s: seq<nat>) returns (d: nat)
    requires |s| > 0
    ensures d == s[0]
  {
    d := s[0];
  }

  // =====================================================================================
  // WRITE cards: one success here, one pinned failure in specimens/Q01/card-*.specimen
  // =====================================================================================

  // item: Q01.C1d S2 write:ensures
  /* ### C1d — card: `ensures` (WRITE)
     Jurisdiction: what a method promises its callers about its results; the body must
     establish it on every return path. Success: `Inc` below. Failure:
     specimens/Q01/card-c1d.dfy.specimen (its EXPECT line pins the message). */
  method Inc(x: nat) returns (y: nat)
    ensures y == x + 1
  {
    y := x + 1;
  }

  // item: Q01.C2d S3 write:assert
  /* ### C2d — card: `assert` (WRITE)
     Jurisdiction: a fact the verifier must prove at this point; afterwards it is known.
     Success: `AssertStep` below. Failure: specimens/Q01/card-c2d.dfy.specimen. */
  method AssertStep(x: nat)
  {
    var y := x + 2;
    assert y > x;
  }

  // item: Q01.C3d S3 write:lemma-call
  /* ### C3d — card: calling a lemma (WRITE)
     Jurisdiction: a call proves the lemma's `requires` at the call site and then knows
     its `ensures` there. Success: `HeadCall` below. Failure:
     specimens/Q01/card-c3d.dfy.specimen. */
  // The card lemma (given): the total head of a non-empty sequence is its first limb.
  lemma HeadOfNonEmpty(s: seq<nat>)
    requires |s| > 0
    ensures Head(s) == s[0]
  {
  }

  method HeadCall(s: seq<nat>)
    requires |s| > 0
  {
    HeadOfNonEmpty(s);
    assert Head(s) == s[0];
  }

  // =====================================================================================
  // RECOGNISE cards (Rosetta): the Dafny column is live here; the Verus column is live in
  // verus/q/q01_hello/src/lib.rs (section "Rosetta columns")
  // =====================================================================================

  // item: Q01.C5dv S2 recognise:requires
  /* ### C5dv — Rosetta: `requires`
     Jurisdiction: what every caller must establish; the body may rely on it.
     Dafny: `requires i < |s|` on the method.   Verus: `requires i < v.len(),` on the fn
     (`get_limb`). */
  method GetLimb(s: seq<nat>, i: nat) returns (d: nat)
    requires i < |s|
    ensures d == s[i]
  {
    d := s[i];
  }

  // item: Q01.C6dv S4 recognise:decreases
  /* ### C6dv — Rosetta: `decreases`
     Jurisdiction: the measure that shrinks on every recursive call, so the recursion
     ends. Dafny: `decreases |s|`.   Verus: `decreases s.len(),` (`reverse_limbs`). */
  function ReverseLimbs(s: seq<nat>): seq<nat>
    decreases |s|
  {
    if |s| == 0 then [] else ReverseLimbs(s[1..]) + [s[0]]
  }

  // item: Q01.C7dv S4 recognise:invariant
  /* ### C7dv — Rosetta: loop `invariant`
     Jurisdiction: a fact true before the loop and kept by every iteration; after the
     loop, it and the negated guard are all the verifier knows. Dafny:
     `invariant i <= n` and `decreases n - i`.   Verus: `invariant i <= n,` and
     `decreases n - i,` (`count_to`). */
  method CountTo(n: nat) returns (i: nat)
    ensures i == n
  {
    i := 0;
    while i < n
      invariant i <= n
      decreases n - i
    {
      i := i + 1;
    }
  }

  // item: Q01.C8dv S2 recognise:forall
  /* ### C8dv — Rosetta: `forall` in a specification
     Jurisdiction: a property of every index in a range. Dafny:
     `forall i | 0 <= i < |s| :: s[i] < b`.   Verus:
     `forall|i: int| 0 <= i < s.len() ==> s[i] < b` (`all_below`). */
  predicate AllBelow(s: seq<nat>, b: nat)
  {
    forall i | 0 <= i < |s| :: s[i] < b
  }

  // item: Q01.C9dv S7 recognise:ghost
  /* ### C9dv — Rosetta: ghost code
     Jurisdiction: values and statements that exist only for the proof. Dafny:
     `ghost var before := x;`.   Verus: `let ghost before = x;` in an exec fn
     (`ghost_demo`); Verus also has whole spec and proof functions. */
  method GhostDemo(x: nat) returns (y: nat)
    ensures y == x + 1
  {
    ghost var before := x;
    y := x + 1;
    assert y == before + 1;
  }

  // item: Q01.C10dv S2 recognise:function
  /* ### C10dv — Rosetta: a specification function
     Jurisdiction: a mathematical definition that specifications and proofs can call.
     Dafny: `function`.   Verus: `spec fn` (`is_zero_limb`). */
  function IsZeroLimb(d: nat): bool
  {
    d == 0
  }

  // =====================================================================================
  // Holes
  // =====================================================================================

  // item: Q01.H1d S2
  // uses: ensures
  // pair: Q01.H1v
  /** **H1d.** Why this body: the two branches of the `if` each return one of the
      arguments (the third conjunct), and the guard makes that argument the larger one
      (the first two). A weaker postcondition, `m >= a && m >= b` alone, would also
      accept `a + b` (P11dv). */
  method Max2(a: int, b: int) returns (m: int)
    ensures m >= a && m >= b && (m == a || m == b)
  {
    if a >= b {
      m := a;
    } else {
      m := b;
    }
  }
  // reference-only: live in the twin, commented in the learner file
  method Max2Check()
  {
    var m := Max2(3, 7);
    assert m == 7;
  }
  // reference-only: an extra edge check (equal arguments)
  method Max2EqualCheck()
  {
    var m := Max2(4, 4);
    assert m == 4;
  }

  // item: Q01.H2d S3
  // uses: assert, lemma-call
  // pair: Q01.H2v
  /** **H2d.** Why this proof: `s + [0, 0]` is `s + [0]` with one more zero appended (the
      assert states it, so the verifier can match the worked lemma's left-hand side),
      and the worked lemma applied twice, first to `s + [0]`, then to `s`, removes the
      two zeros one at a time. */
  lemma ToNatAppendTwoZeros(s: seq<nat>)
    ensures ToNat(s + [0, 0]) == ToNat(s)
  {
    assert s + [0, 0] == (s + [0]) + [0];
    ToNatAppendZero(s + [0]);
    ToNatAppendZero(s);
  }

  // item: Q01.H3d S4
  // uses: lemma-call
  // pair: Q01.H3v
  /** **H3d.** Why this proof: with `{:induction false}` the verifier does not induct for
      us, so the proof is a recursive call on the tail, whose limbs are also all zero.
      The value of `s` is `s[0] + BASE * ToNat(s[1..])`, and both terms are 0. */
  lemma {:induction false} AllZeroToNat(s: seq<nat>)
    requires forall i | 0 <= i < |s| :: s[i] == 0
    ensures ToNat(s) == 0
    decreases |s|
  {
    if |s| > 0 {
      AllZeroToNat(s[1..]);
    }
  }

  // =====================================================================================
  // Final section: the false-friends card (read it only after Q01's predictions are
  // committed)
  // =====================================================================================

  // item: Q01.C4dv S3 diverge:false-friends
  /* ### C4dv — card: false friends (Dafny and Verus)
     Six constructs that look alike in the two languages and do not behave alike. Each
     row has one demo per language under specimens/Q01/, named by row:
       row 1 `calc`       card-c4dv-1-d.dfy.specimen   card-c4dv-1-v.rs.specimen
       row 2 `assert`     card-c4dv-2-d.dfy.specimen   card-c4dv-2-v.rs.specimen
       row 3 `forall`     card-c4dv-3-d.dfy.specimen   card-c4dv-3-v.rs.specimen
       row 4 `old`        card-c4dv-4-d.dfy.specimen   card-c4dv-4-v.rs.specimen
       row 5 `decreases`  card-c4dv-5-d.dfy.specimen   card-c4dv-5-v.rs.specimen
       row 6 `==>`        card-c4dv-6-d.dfy.specimen   card-c4dv-6-v.rs.specimen
     Run each pair with `scripts/vcheck <demo>` and compare. */

  // =====================================================================================
  // ## Exercise (AGENTIC) — repairer (rung 1) and the three doors
  // =====================================================================================
  // Agent files: dafny/Q/Q01_Hello/agent/Q01_AgentRepair.dfy and
  // verus/q/q01_hello/src/agent.rs. Each ships RED with four planted bugs, one
  // diagnostic per bug. Reference deliveries: Solutions/dafny/Q/Q01_Hello/agent/ and
  // Solutions/verus/q/q01_hello/src/agent.rs (each ends with its clearly marked
  // reference section).
  //
  // ### — clearly marked: everything below answers the agentic file —
  // The repairs (one line each), Dafny: Bug 1 `y := x + 1;` · Bug 2 `d := s[|s| - 1];` ·
  // Bug 3 `Pos(1);` · Bug 4 `assert x * 2 == 6;`. Verus: Bug 1 `x + 1` ·
  // Bug 2 `i = i + 1;` · Bug 3 `pos(1);` · Bug 4 `assert(3 * 2 == 6);`.
  // Planted soft spots for the audit: none beyond the four bugs; the acceptance lines
  // forbid touching any requires/ensures/doc line, and the clean audit pins
  // (expected/Q01_AgentRepair.audit, expected/q01_hello_agent.audit) are empty.

  // CALIBRATION (learner-owned; no script reads it). Planned vs actual minutes:
  //   setup 15 / __ · read 45 / __ · worked 30 / __ · cards 15 / __ · predicts 25 / __
  //   holes 24 / __ · agent + three doors 25 / __ · paper 15 / __ · map exit 25 / __
  //   calib 8 / __ · total 227 / __
}
