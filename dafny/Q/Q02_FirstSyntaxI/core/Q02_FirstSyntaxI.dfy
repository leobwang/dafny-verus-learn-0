/*!
# Q02 — First syntax I (Exercises)

Imports: the given spine layers QG_L1_BigNat and QG_L2_BigNat (dafny/given/Q/), which
this unit's dfyconfig.toml includes. No earlier exercise file is imported: finish Q01
first, but nothing here depends on your Q01 answers.

How to work this file:
1. Test-out first, closed book, before you read the chapter: T1d below and T1v at the
   top of verus/q/q02_first_syntax_i/src/lib.rs. Write each, then record its first try
   with `scripts/firsttry.sh Q02 --check` BEFORE you uncomment its check.
2. Predictions next: the prediction block below, the specimens specimens/Q02/P1d,
   P2v, P5d and P6v, and the value slot of dafny/checks/Q02_checks.dfy (P9d). Record them
   with `scripts/firsttry.sh Q02 --check` before you run anything they are about.
3. Then read the chapter (docs/Q02_FirstSyntaxI.md), the worked example W1d and the
   cards. A card's failure demo is a specimen: open it only after step 2.
4. Replace each hole; its statement is its check. The test-out block T1d ships a
   commented check: uncomment it once its first try is recorded (step 1). Read Hint(1)
   only when stuck, Hint(2) only when still stuck.
5. Done = `scripts/vcheck --gate dafny/Q/Q02_FirstSyntaxI/core/Q02_FirstSyntaxI.dfy`
   prints only the summary line and exits 0, `scripts/vaudit
   dafny/Q/Q02_FirstSyntaxI/core` reports no finding, AND
   `scripts/firsttry.sh Q02 --report --strict` exits 0.
6. Stuck for 20 minutes? /tutor Q02.

This file ships with exactly 6 holes: H1d, H2d, H3d, H4d, H5d and H6d (the tool counts
them: `scripts/vcheck dafny/Q/Q02_FirstSyntaxI/core` lists one per item). Module Q02
ships 12 holes (6 here, 6 in verus/q/q02_first_syntax_i/src/lib.rs), 2 test-out items
(T1d, T1v), 10 predictions (5 verdicts in the prediction block below, 4 obligation
specimens, 1 value slot) and 6 exit items (in the exit files, not here).
Commit every prediction BEFORE you run anything it is about, open later files, or read
CI, the registry or the plan: their checks and headers give some predictions away.

Item kinds: T test-out · P prediction · W worked example · C card (write, recognise,
diverge) · H hole · X exit item (exit files) · A agent run (agent files).
Slots: a verdict's answer goes into slots/Q02.slots (`P3dv = "<answer>"` in place of
`???`); an obligation specimen's into its `// SLOT: FAILS ???` line; a value slot's
`???` takes a literal. Fill a slot, record it with `scripts/firsttry.sh Q02 --check`,
and only then enable it: delete `SLOT: ` from its line (a verdict: from its
`// SLOT: CHECK …` line), so the check runs.

The agentic exercise (implementer vs checks,
dafny/Q/Q02_FirstSyntaxI/agent/Q02_AgentImplement.dfy) is at the bottom.
*/
module Q02_FirstSyntaxI {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat

  // ===========================================================================
  // Test-out (closed book, before the chapter)
  // ===========================================================================

  // item: Q02.T1d S4
  // uses: decreases
  // pair: Q02.T1v
  // ### T1d · S4 — Write `function PadZeros(s: seq<nat>, k: nat): seq<nat>`, which appends
  //    zero limbs to `s` until its length is at least `k`, by recursion. Closed book: no
  //    chapter, no hints, no tutor. Then run `scripts/firsttry.sh Q02 --check`: it records
  //    your first try (it runs the check below in a scratch copy). Only then uncomment the
  //    check.

  // Uncomment as you go:
  // lemma PadZerosCheck()
  //   ensures PadZeros([7], 3) == [7, 0, 0]
  // {
  // }

  // ===========================================================================
  // Prediction block
  // ===========================================================================
  // Commit every prediction of Q02 before you read past this block: the five
  // verdicts below (answers in slots/Q02.slots), the specimens under specimens/Q02/
  // (P1d, P2v, P5d, P6v) and the value slot in dafny/checks/Q02_checks.dfy (P9d).
  // Record them with `scripts/firsttry.sh Q02 --check` before you run anything they
  // are about.
  //
  // A verdict `v` is one of these tokens: `ok` (scripts/vcheck reports verified),
  // `fail` (it reports a verification failure), `timeout` (it reports a resource or
  // time limit), `err:<stage>` (it stops at a stage before verification and prints
  // that stage: `err:parse` or `err:resolve`).

  // item: Q02.P3dv S4 verdict
  /* **P3dv.** A recursive count and a lemma with an EMPTY body about it, each verified
     on its own with `scripts/vcheck`, in this module's unit or crate.

       Dafny (this unit, dafny/Q/Q02_FirstSyntaxI/core):
         function Count(n: nat): nat
           decreases n
         {
           if n == 0 then 0 else 1 + Count(n - 1)
         }
         lemma CountId(n: nat)
           ensures Count(n) == n
         {
         }

       D-off: the same, with the lemma declared `lemma {:induction false} CountId(n: nat)`.

       Verus (this crate, verus/q/q02_first_syntax_i):
         pub open spec fn count(n: nat) -> nat
             decreases n,
         {
             if n == 0 { 0 } else { 1 + count((n - 1) as nat) }
         }
         pub proof fn count_id(n: nat)
             ensures count(n) == n,
         {
         }

     What does each run report?
     Answer form: `D:<v> D-off:<v> V:<v>`, each `v` a verdict token (above). */
  // SLOT: CHECK P3dv

  // item: Q02.P4dv S4 verdict
  /* **P4dv.** A counting `while` loop written with NO `decreases` clause, verified with
     `scripts/vcheck` in this module's unit or crate.

       Dafny:
         method CountUp(n: nat) returns (i: nat)
           ensures i == n
         {
           i := 0;
           while i < n
             invariant i <= n
           {
             i := i + 1;
           }
         }

       Verus:
         pub fn count_up(n: u64) -> (i: u64)
             ensures i == n,
         {
             let mut i: u64 = 0;
             while i < n
                 invariant i <= n,
             {
                 i = i + 1;
             }
             i
         }

     What does each run report?
     Answer form: `D:<v> V:<v>`, each `v` a verdict token (above). */
  // SLOT: CHECK P4dv

  // item: Q02.P7dv S6 verdict
  /* **P7dv.** Mutation without permission. Both programs below are rejected.

       Dafny (a method that writes an array element and has no `modifies` clause):
         method SetFirst(a: array<nat>)
           requires a.Length > 0
         {
           a[0] := 1;
         }

       Verus (a function that writes through a shared reference):
         pub fn set_first(v: &Vec<u64>)
             requires v.len() > 0,
         {
             v.set(0, 1);
         }

     At which stage is each rejected, as `scripts/vcheck` reports it?
     Answer form: `D:<stage> V:<stage>`, each `stage` one of `parse`, `resolve`, `verify`:
     `verify` when the verifier reports an obligation it could not prove and
     `scripts/vcheck` prints no stage; otherwise the stage `scripts/vcheck` prints. */
  // SLOT: CHECK P7dv

  // item: Q02.P8dv S3 verdict
  /* **P8dv.** A fact proved with `assert … by`, then a second `assert` of the LEMMA's own
     postcondition (not the fact the `by` block proved).

       Dafny (ToNatBound is QG_L2_BigNat's: requires Valid(s), ensures ToNat(s) < Pow(|s|)):
         lemma Scoped(s: seq<nat>)
           requires Valid(s)
         {
           assert ToNat(s) >= 0 by { ToNatBound(s); }
           assert ToNat(s) < Pow(|s|);
         }

       Verus (lemma_seq_to_nat_push_zero is qg_bignat_l1's:
       ensures seq_to_nat(s.push(0)) == seq_to_nat(s)):
         pub proof fn scoped(s: Seq<u64>) {
             assert(seq_to_nat(s.push(0)) >= 0) by { lemma_seq_to_nat_push_zero(s); }
             assert(seq_to_nat(s.push(0)) == seq_to_nat(s));
         }

     What does `scripts/vcheck` report for each?
     Answer form: `D:<v> V:<v>`, each `v` a verdict token (above). */
  // SLOT: CHECK P8dv

  // item: Q02.P10dv S5 verdict
  /* **P10dv.** Library staging. Add one line to this module's files, and nothing else:

       Dafny: `import opened Std.Wrappers` as the first line inside `module Q02_FirstSyntaxI`
       in this file (unit dafny/Q/Q02_FirstSyntaxI/core).
       Verus: `use vstd::seq_lib::*;` under `use vstd::prelude::*;` in
       verus/q/q02_first_syntax_i/src/lib.rs.

     What does `scripts/vcheck` (the learner loop, on the unit or the crate as shipped, holes
     and all) report for each? The course's import-tier checker is a separate question.
     Answer form: `D:<v> V:<v>`, each `v` a verdict token (above). */
  // SLOT: CHECK P10dv

  // ===========================================================================
  // Worked example
  // ===========================================================================

  // item: Q02.W1d S4
  /** **W1d (worked).** The index of the first zero limb of `s`, or `|s|` when there is
      none. A loop with its invariants and an explicit `decreases`; the `assert`s after
      the loop state what the verifier knows there: the invariants, and the guard false. */
  method FirstZero(s: seq<nat>) returns (i: nat)
    ensures i <= |s|
    ensures forall j | 0 <= j < i :: s[j] != 0
    ensures i < |s| ==> s[i] == 0
  {
    i := 0;
    while i < |s| && s[i] != 0
      invariant i <= |s|
      invariant forall j | 0 <= j < i :: s[j] != 0
      decreases |s| - i
    {
      i := i + 1;
    }
    // At loop exit: both invariants hold, and the guard is false.
    assert i <= |s| && forall j | 0 <= j < i :: s[j] != 0;
    assert !(i < |s| && s[i] != 0);
    assert i == |s| || s[i] == 0;
  }

  // ===========================================================================
  // WRITE cards. Each failure demo is a specimen under specimens/Q02/: open it only
  // after your predictions are committed.
  // ===========================================================================

  // item: Q02.C1d S3 write:assert-by
  /* ### C1d — card: `assert … by`
     Jurisdiction: a fact that needs its own proof steps (here one lemma call), written
     next to the fact it proves. Success: CardAssertBy below. Failure:
     specimens/Q02/card-c1d.dfy.specimen. */
  lemma CardAssertBy(s: seq<nat>)
    requires Valid(s)
    ensures ToNat(s) < BASE * Pow(|s|)
  {
    assert ToNat(s) < Pow(|s|) by {
      ToNatBound(s);
    }
  }

  // item: Q02.C2d S4 write:invariant
  /* ### C2d — card: loop invariants
     Jurisdiction: what a loop keeps true from one pass to the next, written as `invariant`
     clauses between the guard and the body; it must hold before the first pass and after
     every pass. Success: CardInvariant below. Failure: specimens/Q02/card-c2d.dfy.specimen. */
  method CardInvariant(s: seq<nat>) returns (i: nat)
    ensures i == |s|
  {
    i := 0;
    while i < |s|
      invariant i <= |s|
      decreases |s| - i
    {
      i := i + 1;
    }
  }

  // item: Q02.C3d S4 write:decreases
  /* ### C3d — card: termination measures (`decreases`)
     Jurisdiction: why a recursion or a loop stops: a measure that every recursive call (or
     every pass) makes smaller and that cannot fall below zero. The course states it
     explicitly. Success: CardEvens below (the limbs at even positions). Failure:
     specimens/Q02/card-c3d.dfy.specimen. */
  function CardEvens(s: seq<nat>): seq<nat>
    decreases |s|
  {
    if |s| < 2 then s else [s[0]] + CardEvens(s[2..])
  }

  // item: Q02.C4d S2 write:quantified-ensures
  /* ### C4d — card: a `forall` postcondition
     Jurisdiction: a property of every element of a result, stated once for all indices.
     Success: CardIndices below (the sequence 0, 1, …, n - 1). Failure:
     specimens/Q02/card-c4d.dfy.specimen. */
  method CardIndices(n: nat) returns (s: seq<nat>)
    ensures |s| == n && forall i | 0 <= i < n :: s[i] == i
  {
    s := [];
    var k := 0;
    while k < n
      invariant k <= n && |s| == k
      invariant forall i | 0 <= i < k :: s[i] == i
      decreases n - k
    {
      s := s + [k];
      k := k + 1;
    }
  }

  // item: Q02.C5d S6 write:frame
  /* ### C5d — card: frames on arrays (`modifies`, `old`)
     Jurisdiction: which heap locations a method may change (`modifies`), and how its
     postcondition names their values at the call (`old`). Success: CardSwapLimbs below.
     Failure: specimens/Q02/card-c5d.dfy.specimen (a caller of the same method). */
  method CardSwapLimbs(a: array<nat>, i: nat, j: nat)
    requires i < a.Length && j < a.Length
    modifies a
    ensures a[i] == old(a[j]) && a[j] == old(a[i])
  {
    a[i], a[j] := a[j], a[i];
  }

  // ===========================================================================
  // RECOGNISE cards (Rosetta: the Dafny column here, the Verus column in
  // verus/q/q02_first_syntax_i/src/lib.rs)
  // ===========================================================================

  // item: Q02.C8dv S6 recognise:old
  /* ### C8dv — Rosetta card: `old`
     Dafny: `old(e)` is `e` evaluated in the heap as the method started; it appears in the
     `ensures` (and loop invariants) of a method that `modifies` something.
     Verus: a `&mut` parameter `v` has two values in a specification, `old(v)` at the call
     and `final(v)` at the return; a bare `v` in an `ensures` is refused.
     Dafny column: CardOld below. Verus column: `card_old` in the Verus crate. */
  method CardOld(a: array<nat>)
    requires a.Length > 0
    modifies a
    ensures a[0] == old(a[0]) + 1
  {
    a[0] := a[0] + 1;
  }

  // item: Q02.C9dv S2 recognise:exists
  /* ### C9dv — Rosetta card: existential quantifiers
     Dafny: `exists i :: P(i)`; Verus: `exists|i: int| P(i)`. A proof names a witness: a term
     for which `P` holds, stated so the verifier sees it.
     Dafny column: CardExists below. Verus column: `card_exists` in the Verus crate. */
  lemma CardExists(s: seq<nat>)
    requires |s| > 0 && s[|s| - 1] != 0
    ensures exists i :: 0 <= i < |s| && s[i] != 0
  {
    var w := |s| - 1;
    assert 0 <= w < |s| && s[w] != 0;
  }

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: Q02.H1d S3
  // uses: assert-by, lemma-call
  // pair: Q02.H1v
  /** **H1d.** Dropping a most significant zero limb keeps the value.
      Method clause: the proof uses one `assert … by`. Which given lemma talks about a zero
      limb on top of a sequence, and how is `s` such a sequence? */
  lemma ToNatDropLastZero(s: seq<nat>)
    requires |s| > 0 && s[|s| - 1] == 0
    ensures ToNat(s[..|s| - 1]) == ToNat(s)
  // HOLE: give this lemma a body.
  // Hint(1): name the prefix, `var p := s[..|s| - 1];`. Then `s` is `p` with one limb more.
  // Hint(2): L1's worked lemma speaks about `p + [0]`, the goal about `s`. Which equation
  //    between the two does the verifier need to be told?

  // item: Q02.H2d S4
  // uses: invariant, assert
  // pair: Q02.H2v
  /** **H2d.** The loop form of `Normalize`: strip the most significant zero limbs.
      The code and its `decreases` are given. Write the loop invariants, and the assertions
      they need to hold on entry and to be kept by each pass. What does the loop keep true
      about the prefix `s[..n]` that is still to be stripped? */
  method NormalizeLoop(s: seq<nat>) returns (r: seq<nat>)
    ensures r == Normalize(s)
  {
    assume false;  // HOLE: delete this line, then write the invariants and the assertions
    var n := |s|;
    while n > 0 && s[n - 1] == 0
      decreases n
    {
      n := n - 1;
    }
    r := s[..n];
  }
  // Hint(1): at loop exit `s[n - 1]` is not a zero limb (or `n` is 0). What is
  //    `Normalize(s[..n])` then?
  // Hint(2): two invariants: `n` stays in range, and `Normalize` of the prefix stays
  //    `Normalize(s)`. If one fails on entry or is not kept, ask which equality between
  //    slices of `s` the verifier was never told.

  // item: Q02.H3d S4
  // uses: lemma-call
  /** **H3d.** Normalizing keeps the value. Which cases does `Normalize` itself
      distinguish, and which one changes the sequence? */
  lemma NormalizeToNat(s: seq<nat>)
    ensures ToNat(Normalize(s)) == ToNat(s)
    decreases |s|
  // HOLE: give this lemma a body.
  // Hint(1): follow `Normalize`'s cases; only the zero-top case needs work.
  // Hint(2): in that case `s` is `p + [0]` for `p := s[..|s| - 1]`: one given lemma and one
  //    recursive call.

  // item: Q02.H4d S2
  // uses: lemma-call
  /** **H4d.** Normalizing a valid limb sequence gives a canonical one. Which case of
      `Normalize` calls itself, and what does a recursive call of this lemma need there? */
  lemma {:induction false} NormalizeCanonical(s: seq<nat>)
    requires Valid(s)
    ensures Canonical(Normalize(s))
    decreases |s|
  // HOLE: give this lemma a body.
  // Hint(1): which case of `Normalize` calls itself?
  // Hint(2): follow `Normalize`'s recursion with this lemma's own.

  // item: Q02.H5d S2
  // uses: quantified-ensures, invariant, decreases
  // pair: Q02.H5v
  /** **H5d.** `n` zero limbs.
      Method clause: build `s` with a `while` loop that states its `decreases`. */
  method Zeros(n: nat) returns (s: seq<nat>)
    ensures |s| == n && forall i | 0 <= i < n :: s[i] == 0
  {
    assume false;  // HOLE: replace this line with the loop
  }
  // Hint(1): start from `[]` and append one limb per pass.
  // Hint(2): the invariant states the postcondition for the part built so far.

  // item: Q02.H6d S6
  // uses: frame, quantified-ensures, invariant, decreases
  // pair: Q02.H6v
  /** **H6d.** Clear every limb of `a` from position `k` on, in place.
      Method clause: a `while` loop that states its `decreases`. */
  method ClearFrom(a: array<nat>, k: nat)
    modifies a
    ensures forall i | 0 <= i < a.Length :: a[i] == (if i < k then old(a[i]) else 0)
  {
    assume false;  // HOLE: replace this line with the loop
  }
  // Hint(1): start the index at `k`. What must the invariant say about the positions the
  //    loop has not reached yet?
  // Hint(2): the invariant describes the whole array at every pass, not only the part
  //    already cleared.

  // ===========================================================================
  // Final section: divergence card. Record every Q02 prediction before you read on.
  // ===========================================================================

  // item: Q02.C7dv S4 diverge:q02-c7
  /* ### C7dv — divergence card: empty-bodied lemmas about a recursive definition
     The same statement, an empty proof, in each language. Demos:
     specimens/Q02/card-c7dv-d.dfy.specimen and specimens/Q02/card-c7dv-v.rs.specimen; run
     each with `scripts/vcheck` and compare. The chapter explains the difference. */
}

// =============================================================================
// ## Exercise (AGENTIC) — implementer vs checks (`/contract Q02`)
// =============================================================================
// Files: dafny/Q/Q02_FirstSyntaxI/agent/Q02_AgentImplement.dfy and
// verus/q/q02_first_syntax_i/src/agent.rs. Shipped state: RED by design. Each states three
// definitions by a prose contract and a partial formal one, with a hole for each body
// (Verus: also a bound-lemma hole per definition), and a live suite of six checks that
// fail over the holes. Check command (the file's own header gives the exact shipped
// output):
//
//     scripts/vcheck dafny/Q/Q02_FirstSyntaxI/agent/Q02_AgentImplement.dfy
//
// Steps (after this file is done):
// 1. Before the run: read the three prose contracts and run the check command.
// 2. In a FRESH session, run /contract Q02 (one file per run: the Dafny file, then the
//    Verus file).
// 3. Tally the transcript: only the fast channel per edit? exactly one full gate, last?
//    Fill the LATENCY LOG block of the agent file from the transcript.
// 4. Check the artifact yourself: the gate output, `git diff` (bodies only), `scripts/vaudit`.
// 5. Write ADVERSARIAL CHECKS in the agent file's trailing block: cases the shipped suite
//    never exercised, judged against the prose contract, not the formal one.
// The lesson: a delivery that passes every shipped check has met the checks, not
// necessarily the contract.

// =============================================================================
// CALIBRATION (learner-owned; no script reads it)
// =============================================================================
// Minutes, planned / actual (the test-out first tries are recorded by
// `scripts/firsttry.sh Q02 --check`, not here):
//   setup 5 /       test-out 10 /     read 45 /      worked 32 /     cards 10 /
//   predicts 24 /   holes 48 /        agent 15 /     paper 15 /      exit 25 /
//   calib 5 /       total 234 /
// Then run `scripts/firsttry.sh Q02 --record`.
