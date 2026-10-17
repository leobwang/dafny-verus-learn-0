/*!
# Q02 — First syntax I (Reference Solution)

Hole-free reference for `dafny/Q/Q02_FirstSyntaxI/core/Q02_FirstSyntaxI.dfy`
(author-only; never learner-visible). Same module name, same items in the same
order, same statements; the hole bodies are complete, the test-out block and
its check are written out, and the verdict switches are live (the answers are
in Solutions/slots/Q02.slots, their hashes in expected/Q02.pins).

Every output the course quotes about this file is pinned: the unit's count pin
(expected/Q02.counts), the verdict hashes (expected/Q02.pins), the card demo
pins (in-file EXPECT lines and the expected/specimens/Q02/ sidecars). The file
is silent: `scripts/vcheck --ref` on it prints only its summary line.

Imports: the given spine layers QG_L1_BigNat and QG_L2_BigNat (re-supply: no
exercise file is imported). The prediction answers and their evidence are in
Solutions/plans/Q02-author-notes.md.
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
  // (Reference) Each call adds one limb, so `k - |s|` shrinks by one per call and the guard
  // stops the recursion before it goes below zero. Dafny's default measure (the parameters
  // in order) would not work: `s` grows.
  // reference-only: the learner writes this function (a prompt-as-heading block)
  function PadZeros(s: seq<nat>, k: nat): seq<nat>
    decreases k - |s|
  {
    if |s| >= k then s else PadZeros(s + [0], k)
  }

  // reference-only: the learner uncomments this check
  lemma PadZerosCheck()
    ensures PadZeros([7], 3) == [7, 0, 0]
  {
  }

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
  // CHECK P3dv

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
  // CHECK P4dv

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
  // CHECK P7dv

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
  // CHECK P8dv

  // item: Q02.P10dv S5 verdict
  /* **P10dv.** Library staging. Add one line to this module's files, and nothing else:

       Dafny: `import opened Std.Wrappers` as the first line inside `module Q02_FirstSyntaxI`
       in this file (unit dafny/Q/Q02_FirstSyntaxI/core).
       Verus: `use vstd::seq_lib::*;` under `use vstd::prelude::*;` in
       verus/q/q02_first_syntax_i/src/lib.rs.

     What does `scripts/vcheck` (the learner loop, on the unit or the crate as shipped, holes
     and all) report for each? The course's import-tier checker is a separate question.
     Answer form: `D:<v> V:<v>`, each `v` a verdict token (above). */
  // CHECK P10dv

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
      (Reference) `s` is `p + [0]` for the prefix `p := s[..|s| - 1]`. L1's worked lemma
      gives the value of `p + [0]`, proved inside one `assert … by`; the sequence equality
      `p + [0] == s` then lets the verifier rewrite that fact into the goal. Without the
      equality the solver never connects `ToNat(p + [0])` with `ToNat(s)`. */
  lemma ToNatDropLastZero(s: seq<nat>)
    requires |s| > 0 && s[|s| - 1] == 0
    ensures ToNat(s[..|s| - 1]) == ToNat(s)
  {
    var p := s[..|s| - 1];
    assert ToNat(p + [0]) == ToNat(p) by {
      ToNatAppendZero(p);
    }
    assert p + [0] == s;
  }

  // item: Q02.H2d S4
  // uses: invariant, assert
  // pair: Q02.H2v
  /** **H2d.** The loop form of `Normalize`: strip the most significant zero limbs.
      (Reference) The invariant `Normalize(s[..n]) == Normalize(s)` says the prefix still to
      be stripped normalizes like the whole; it holds on entry once the verifier knows
      `s[..|s|] == s`, and each pass keeps it because, when `s[n - 1] == 0`, `Normalize`'s
      own definition steps from `s[..n]` to `s[..n][..n - 1]`, which the in-body `assert`
      equates with `s[..n - 1]`. At exit the guard is false, so `Normalize(s[..n])` is
      `s[..n]` itself. The bound invariant keeps every index in range. */
  method NormalizeLoop(s: seq<nat>) returns (r: seq<nat>)
    ensures r == Normalize(s)
  {
    var n := |s|;
    // @hole-begin Q02.H2d
    assert s[..n] == s;
    // @hole-end Q02.H2d
    while n > 0 && s[n - 1] == 0
      // @hole-begin Q02.H2d
      invariant 0 <= n <= |s|
      invariant Normalize(s[..n]) == Normalize(s)
      // @hole-end Q02.H2d
      decreases n
    {
      // @hole-begin Q02.H2d
      assert s[..n][..n - 1] == s[..n - 1];
      // @hole-end Q02.H2d
      n := n - 1;
    }
    r := s[..n];
  }

  // item: Q02.H3d S4
  // uses: lemma-call
  /** **H3d.** Normalizing keeps the value.
      (Reference) By recursion on `|s|`, following `Normalize`'s own cases: when the top limb
      is zero, `s == p + [0]`, L1's worked lemma removes that limb from the value, and the
      recursive call handles `Normalize(p)`, which is `Normalize(s)` by definition. */
  lemma NormalizeToNat(s: seq<nat>)
    ensures ToNat(Normalize(s)) == ToNat(s)
    decreases |s|
  {
    if |s| > 0 && s[|s| - 1] == 0 {
      var p := s[..|s| - 1];
      assert s == p + [0];
      ToNatAppendZero(p);
      NormalizeToNat(p);
    }
  }

  // item: Q02.H4d S2
  // uses: lemma-call
  /** **H4d.** Normalizing a valid limb sequence gives a canonical one.
      (Reference) With induction off, the recursion is written by hand: in the zero-top case
      `Normalize(s)` is `Normalize(s[..|s| - 1])`, and the recursive call (whose `Valid`
      precondition holds for a prefix of a valid sequence) gives its canonical form; in the
      other cases `Normalize(s)` is `s` or `[]`, canonical by definition. */
  lemma {:induction false} NormalizeCanonical(s: seq<nat>)
    requires Valid(s)
    ensures Canonical(Normalize(s))
    decreases |s|
  {
    if |s| > 0 && s[|s| - 1] == 0 {
      NormalizeCanonical(s[..|s| - 1]);
    }
  }

  // item: Q02.H5d S2
  // uses: quantified-ensures, invariant, decreases
  // pair: Q02.H5v
  /** **H5d.** `n` zero limbs, built by a `while` loop with an explicit `decreases`.
      (Reference) The invariant carries both halves of the postcondition for the prefix
      built so far; the measure `n - |s|` shrinks by one per pass. */
  method Zeros(n: nat) returns (s: seq<nat>)
    ensures |s| == n && forall i | 0 <= i < n :: s[i] == 0
  {
    s := [];
    while |s| < n
      invariant |s| <= n
      invariant forall i | 0 <= i < |s| :: s[i] == 0
      decreases n - |s|
    {
      s := s + [0];
    }
  }

  // item: Q02.H6d S6
  // uses: frame, quantified-ensures, invariant, decreases
  // pair: Q02.H6v
  /** **H6d.** Clear every limb of `a` from position `k` on, in place, by a `while` loop
      with an explicit `decreases`.
      (Reference) The invariant describes the whole array at every pass: positions below
      `k` and from `j` on still hold their old values, positions in `[k, j)` are zero. The
      write `a[j] := 0` is allowed by `modifies a`. */
  method ClearFrom(a: array<nat>, k: nat)
    modifies a
    ensures forall i | 0 <= i < a.Length :: a[i] == (if i < k then old(a[i]) else 0)
  {
    var j := k;
    while j < a.Length
      invariant k <= j
      invariant forall i | 0 <= i < a.Length :: a[i] == (if i < k || i >= j then old(a[i]) else 0)
      decreases a.Length - j
    {
      a[j] := 0;
      j := j + 1;
    }
  }

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
// — clearly marked: everything below answers the agentic file —
// =============================================================================
// The reference delivery of dafny/Q/Q02_FirstSyntaxI/agent/Q02_AgentImplement.dfy (and of
// its Verus twin) is that file's own twin, Solutions/dafny/Q/Q02_FirstSyntaxI/agent/
// Q02_AgentImplement.dfy (Solutions/verus/q/q02_first_syntax_i/src/agent.rs): its
// definitions, the shipped suite verbatim, the adversarial checks and the author's note on
// the planted soft spots, in a closing section under this same heading. They live there,
// beside the statements they answer, so one copy is verified and kept.
