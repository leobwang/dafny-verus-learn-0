/*!
# Q05 — Frames, ownership, modes, wp→VC (Exercises)

Imports: the given BigNat spine, layers L1 (`QG_L1_BigNat`), L2
(`QG_L2_BigNat`) and L3 (`QG_L3_BigNat`), and `Std.Wrappers` from the
standard library (this unit's dfyconfig.toml includes the layers and turns
the standard library on). No earlier exercise file is imported. The layers
are frozen and complete; read them, never edit them.

How to work this file (the order is the module's, for both files):
1. Predictions first: fill every slot of the prediction block below (the
   verdict answers go in slots/Q05.slots), of specimens/Q05/P*.specimen and of
   dafny/checks/Q05_checks.dfy, then record the first tries with
   `scripts/firsttry.sh Q05 --check`, before you run anything they are about.
2. Test-out next, closed book: T1d (below the prediction block) and T1v (in
   verus/q/q05_frames/src/lib.rs) before any reading, without hints. Run
   `scripts/firsttry.sh Q05 --check` again, which records your first try (it
   runs T1's commented check in a scratch copy, and it refuses while a
   prediction of Q05 is unrecorded), and only then uncomment the check. If
   both files' T1 pass on that first try, you may skip the chapter section on
   lexicographic measures.
3. Then read the chapter (docs/Q05_Frames.md), the cards and the worked
   example. A card's failure demo is a specimen: open it only after step 1.
4. Replace each hole, then uncomment the checks beneath it. Read Hint(1) only
   when stuck, Hint(2) only when still stuck.
5. Done = `scripts/vcheck --gate dafny/Q/Q05_Frames/std` prints only the
   summary line and exits 0, `scripts/vaudit dafny/Q/Q05_Frames/std` reports
   no finding, AND `scripts/firsttry.sh Q05 --report --strict` exits 0.
6. Stuck for 20 minutes? /tutor Q05.

This file ships with exactly 5 holes: H1d–H5d, each counted by
`scripts/vcheck`, and one test-out block (T1d: empty, with one commented
check). Q05 as a whole ships 9 holes (5 here, 4 in the Verus file
verus/q/q05_frames/src/lib.rs), 2 test-out items (T1d and T1v: blocks with a
commented check, no hole), 8 predictions (the 4 verdicts below, 3 obligation
specimens and 1 value slot) and 4 exit items (the exit files ship 2 + 2
holes). Commit every prediction BEFORE you run anything it is about, open
later files, or read CI, the registry or the plan: their checks and headers
give some predictions away.

Item kinds: P prediction (a slot) · T test-out (closed book) · C card (WRITE:
a success here and a failure demo in specimens/Q05/; divergence, in the final
section) · W worked example (given, finished) · H one-hole item · X exit item
(the exit files) · A agent run (the agent files). Slots: a verdict switch
`// SLOT: CHECK <item>` here takes its answer in slots/Q05.slots
(`P1dv = ???` → `P1dv = "<answer>"`); an obligation specimen's answer goes in
its `// SLOT: FAILS ???` line; a value slot's `???` takes a literal. Fill a
slot, record the first try, and only then enable it: `// SLOT: CHECK P1dv`
becomes `// CHECK P1dv`, `// SLOT: FAILS …` becomes `// FAILS …`, and a
value slot `// SLOT: <check>` becomes the live check.

Exit (closed book): dafny/Q/Q05_Frames/exit/Q05_Exit.dfy and
verus/q/q05_frames/src/exit.rs, scored once by
`scripts/firsttry.sh Q05 --exit` (threshold 3 of 4, with at least 1 of the 2
in each language).

The agentic exercise (infra debugger, agent/Q05_AgentInfra.dfy and
verus/q/q05_frames/src/agent.rs) and the CALIBRATION block are at the bottom.
*/
module Q05_Frames {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened Std.Wrappers

  // ===========================================================================
  // The prediction block. Commit every prediction of this module before you
  // read past this block (the test-out below included), and record the first
  // tries:
  //     scripts/firsttry.sh Q05 --check
  // Verdict answers go in slots/Q05.slots; the other predictions live in
  // specimens/Q05/ (P4d, P5v, P6d) and dafny/checks/Q05_checks.dfy (P8d).
  // Verdict vocabulary for `D:<v> V:<v>` answers: `ok` (verifies), `fail` (a
  // verification error), `timeout` (out of resource or time), `err:<stage>`
  // (refused before verification; <stage> as scripts/vcheck prints it:
  // `parse` or `resolve`).
  // ===========================================================================

  // item: Q05.P1dv S6 verdict
  /** **P1dv.** Reading state without declaring it. Each file holds a type
      with one field and a function that reads the field, with no `reads`
      clause:

        Dafny:
          class Counter {
            var n: nat

            function Size(): nat
            {
              n
            }
          }

        Verus:
          pub struct Counter {
              pub n: u64,
          }

          impl Counter {
              pub open spec fn size(&self) -> nat {
                  self.n as nat
              }
          }

      What does `scripts/vcheck` say about each file?
      Answer form: `D:<v> V:<v>` with the verdict vocabulary above. */
  // SLOT: CHECK P1dv

  // item: Q05.P2dv S7 verdict
  /** **P2dv.** A two-argument recursion. `G(m, n)` returns `n` when `m == 0`,
      calls `G(m - 1, 7)` when `n == 0`, and `G(m, n - 1)` otherwise:

        Dafny, with no `decreases` clause:
          function G(m: nat, n: nat): nat
          {
            if m == 0 then n else if n == 0 then G(m - 1, 7) else G(m, n - 1)
          }

        Verus, with the clause `decreases m`:
          pub open spec fn g(m: nat, n: nat) -> nat
              decreases m,
          {
              if m == 0 {
                  n
              } else if n == 0 {
                  g((m - 1) as nat, 7)
              } else {
                  g(m, (n - 1) as nat)
              }
          }

      What does `scripts/vcheck` say about each file?
      Answer form: `D:<v> V:<v>` with the verdict vocabulary above. */
  // SLOT: CHECK P2dv

  // item: Q05.P3dv S7 verdict
  /** **P3dv.** Ghost state in the running program.

      Dafny: this file, built to Python with `dafny build --target py` in a
      scratch directory (the build writes the generated code to a directory
      `<stem>-py/` beside the source):

          class Tagged {
            var x: nat
            ghost var Shadow: seq<nat>

            constructor ()
            {
              x := 0;
              Shadow := [];
            }
          }

          method Main() {
            var t := new Tagged();
            print t.x, "\n";
          }

      Does the generated Python mention `Shadow` anywhere?

      Verus: this type, compiled with a test (`verus --compile --test`):

          pub struct Tagged {
              pub x: u64,
              pub shadow: Ghost<Seq<u64>>,
          }

      What does `core::mem::size_of::<Tagged>()` return when the test runs?
      Answer form: `D:<yes|no> V:<numeral>`. */
  // SLOT: CHECK P3dv

  // item: Q05.P9dv S8 verdict
  /** **P9dv.** The verification condition of a call (the wp→VC lab is on
      paper). A callee and its caller:

          method Bump(a: array<nat>, i: nat)
            requires i < a.Length
            modifies a
            ensures a[i] == old(a[i]) + 1
            ensures forall j | 0 <= j < a.Length && j != i :: a[j] == old(a[j])

          method Caller(a: array<nat>)
            requires a.Length == 2
            modifies a
          {
            Bump(a, 0);
            assert a[0] >= 1 && a[1] == old(a[1]);
          }

      Write `a` for the array's contents before the call and `a1` for its
      contents after it. Which formula is the condition the verifier must
      prove for the call and the assertion, given `a.Length == 2`? (Verus
      checks the same condition for the same call over a `&mut` vector.)

          a) 0 < a.Length
          b) 0 < a.Length && forall a1 :: (a1[0] == a[0] + 1 &&
               forall j | 0 <= j < 2 && j != 0 :: a1[j] == a[j])
               ==> (a1[0] >= 1 && a1[1] == a[1])
          c) 0 < a.Length ==> a[0] + 1 >= 1 && a[1] == a[1]
          d) forall a1 :: a1[0] == a[0] + 1 ==> a1[0] >= 1 && a1[1] == a[1]

      Answer form: one letter, `a`, `b`, `c` or `d`. */
  // SLOT: CHECK P9dv

  // ===========================================================================
  // Test-out (closed book, after the prediction block is committed and
  // before any reading)
  // ===========================================================================

  // item: Q05.T1d S7
  // uses: lexicographic-decreases
  // pair: Q05.T1v
  // ### T1d · S7 — Write `function Odometer(lo: nat, hi: nat): nat`, the number of steps
  //    an odometer with the digits `hi lo` takes to reach `0 0` when each step decrements
  //    `lo` or, at `lo == 0`, decrements `hi` and resets `lo` to 9. Write it by recursion,
  //    with whatever Dafny needs to accept it. Closed book: no chapter, no hints, no
  //    tutor, and only once every prediction of Q05 is recorded. Then run
  //    `scripts/firsttry.sh Q05 --check`: it records your first try (it runs the check
  //    below in a scratch copy). Only then uncomment the check.

  // Uncomment as you go:
  // lemma OdometerCheck()
  //   ensures Odometer(2, 1) == 12
  // {
  // }

  // ===========================================================================
  // WRITE cards (each: a success here, a pinned failure demo in specimens/Q05/)
  // ===========================================================================

  // item: Q05.C1d S6 write:dynamic-frames
  /** ### C1 — card: dynamic frames (`Repr`, `Valid()`, `modifies Repr`,
      `fresh(Repr - old(Repr))`).
      Jurisdiction: an object whose state spans several heap objects. A ghost
      set `Repr` names them, `Valid()` reads exactly them, a method that
      changes the object says `modifies Repr`, and `fresh(Repr - old(Repr))`
      tells a caller that anything new in `Repr` was allocated by the call,
      so it is disjoint from every object the caller already holds.
      Success: `Meter`. Failure: specimens/Q05/card-c1d.dfy.specimen (a field
      read in a function). */
  class Meter {
    var count: nat
    var log: array<nat>
    ghost var Repr: set<object>

    ghost predicate Valid()
      reads this, Repr
    {
      this in Repr && log in Repr && log.Length > 0
    }

    constructor ()
      ensures Valid() && fresh(Repr) && count == 0
    {
      count := 0;
      log := new nat[1];
      Repr := {this, log};
    }

    method Tick()
      requires Valid()
      modifies Repr
      ensures Valid() && count == old(count) + 1 && fresh(Repr - old(Repr))
    {
      count := count + 1;
      log[0] := count;
    }
  }

  // item: Q05.C2d S7 write:by-method
  /** ### C2 — card: `function … by method`.
      Jurisdiction: one name with two bodies. The function body is the
      specification the verifier reasons with; the method body is what the
      compiled program runs, and the verifier proves that it returns the
      function's value. Success: `Triangle`, computed by an upward loop.
      Failure: specimens/Q05/card-c2d.dfy.specimen (the same loop without its
      second invariant). */
  function Triangle(n: nat): nat
    decreases n
  {
    if n == 0 then 0 else n + Triangle(n - 1)
  } by method {
    var t := 0;
    var k := 0;
    while k < n
      invariant 0 <= k <= n
      invariant t == Triangle(k)
      decreases n - k
    {
      k := k + 1;
      t := t + k;
    }
    return t;
  }

  // item: Q05.C3d S6 write:error-propagation
  /** ### C3 — card: `:-` over a failure-compatible type.
      Jurisdiction: a call that may fail. `var x :- M();` binds the value of a
      success and otherwise returns the failure at once, as the caller's own
      result (here `Result` from `Std.Wrappers`). Success: `FirstIsZero`.
      Failure: specimens/Q05/card-c3d.dfy.specimen (a postcondition the early
      return breaks). */
  method FirstLimb(s: seq<nat>) returns (r: Result<nat, string>)
    ensures r.Success? <==> |s| > 0
    ensures r.Success? ==> r.value == s[0]
  {
    if |s| == 0 {
      return Failure("no limb");
    }
    return Success(s[0]);
  }

  method FirstIsZero(s: seq<nat>) returns (r: Result<bool, string>)
    ensures r.Success? <==> |s| > 0
    ensures r.Success? ==> (r.value <==> s[0] == 0)
  {
    var x :- FirstLimb(s);
    return Success(x == 0);
  }

  // item: Q05.C4d S7 write:lexicographic-decreases
  /** ### C4 — card: lexicographic `decreases`.
      Jurisdiction: a recursion or a loop in which no single quantity goes
      down at every step, but a tuple does, compared left to right:
      `decreases a, b` holds at a step when `a` goes down (whatever `b` does),
      or `a` stays and `b` goes down. Success: `Ack` (a recursion) and
      `WalkPairs` (a loop). Failure: specimens/Q05/card-c4d.dfy.specimen. */
  function Ack(m: nat, n: nat): nat
    decreases m, n
  {
    if m == 0 then n + 1
    else if n == 0 then Ack(m - 1, 1)
    else Ack(m - 1, Ack(m, n - 1))
  }

  // Walk the pairs (i, j) with j < i, from i = n down: one pair per pass, j
  // counting up from 0 below i.
  method WalkPairs(n: nat) returns (i: nat, j: nat)
    ensures i == 0
  {
    i, j := n, 0;
    while i > 0
      invariant j <= i
      decreases i, i - j
    {
      if j + 1 < i {
        j := j + 1;
      } else {
        i := i - 1;
        j := 0;
      }
    }
  }

  // ===========================================================================
  // Worked example: the given stack (and two holes inside it)
  // ===========================================================================

  // item: Q05.W1d S6
  /** **W1.** A growable stack of limbs with dynamic frames. `Repr` is the set
      of heap objects the stack is made of (itself and its array), `Valid()`
      reads exactly `this` and `Repr`, and the constructor promises
      `fresh(Repr)`: a new stack shares no object with anything that existed
      before. `Size()` only reads, so it declares `reads` and no `modifies`.
      `Contents` is the ghost view of the stack: the first `n` slots of `a`.
      H1d and H2d are this class's last two methods. */
  class LimbStack {
    var a: array<nat>
    var n: nat
    ghost var Contents: seq<nat>
    ghost var Repr: set<object>

    ghost predicate Valid()
      reads this, Repr
    {
      this in Repr && a in Repr && n <= a.Length && Contents == a[..n]
    }

    constructor (cap: nat)
      requires cap > 0
      ensures Valid() && fresh(Repr) && Contents == []
    {
      a := new nat[cap];
      n := 0;
      Contents := [];
      Repr := {this, a};
    }

    function Size(): nat
      reads this, Repr
      requires Valid()
      ensures Size() == |Contents|
    {
      n
    }

    // item: Q05.H1d S6
    // uses: dynamic-frames
    /** **H1d.** Push one limb. The code is given: when the array is full, it
        allocates a larger one, copies the limbs with a loop, and adds the new
        array to `Repr`. Write the copy loop's invariants and the frame the
        loop needs. Which objects does the loop write, and what does the
        verifier know about `a` after the loop if the loop does not say so? */
    method Push(x: nat)
      requires Valid()
      modifies Repr
      ensures Valid() && Contents == old(Contents) + [x] && fresh(Repr - old(Repr))
    {
      assume false;  // HOLE: delete this line, then write the copy loop's invariants and its frame
      if n == a.Length {
        var b := new nat[2 * a.Length + 1];
        var i := 0;
        while i < n
          decreases n - i
        {
          b[i] := a[i];
          i := i + 1;
        }
        a := b;
        Repr := Repr + {b};
      }
      a[n] := x;
      n := n + 1;
      Contents := Contents + [x];
    }
    // Hint(1): two invariants: one keeps the indices and the two lengths in
    //    range, one says what the part of `b` copied so far holds.
    // Hint(2): the loop writes `b` only. Can the verifier tell that from the
    //    loop's own annotations?

    // item: Q05.H2d S6
    // uses: dynamic-frames
    /** **H2d.** Pop the top limb. The body and the functional postcondition
        are given. Write the `modifies` clause and the frame postcondition a
        client needs, so that the check `PopCheck` below verifies once it is
        uncommented. What does the body write, and what must a client that
        holds another stack know after the call? */
    method Pop() returns (x: nat)
      requires Valid() && |Contents| > 0
      ensures x == old(Contents)[|old(Contents)| - 1] && Contents == old(Contents)[..|old(Contents)| - 1]
    {
      assume false;  // HOLE: delete this line, then write the frame clauses in the header above
      n := n - 1;
      x := a[n];
      Contents := Contents[..n];
    }
    // Hint(1): which object's fields does the body assign?
    // Hint(2): `PopCheck` asserts `s.Repr !! t.Repr` after the call: what must
    //    the postcondition say about `Repr`?
  }

  // H1d's check: two pushes onto a stack of capacity 1 (the second one grows
  // the array).
  method PushCheck() {
    // Uncomment as you go:
    // var s := new LimbStack(1);
    // s.Push(7);
    // s.Push(8);
    // assert s.Contents == [7, 8];
  }

  // H2d's check: two stacks with disjoint representations; after a pop from
  // `s`, the other stack `t` is valid and holds what it held, and the two
  // representations are still disjoint.
  // Uncomment as you go:
  // method PopCheck(s: LimbStack, t: LimbStack)
  //   requires s.Valid() && t.Valid() && s.Repr !! t.Repr && |s.Contents| > 0
  //   modifies s.Repr
  // {
  //   var tc := t.Contents;
  //   var x := s.Pop();
  //   assert t.Valid() && t.Contents == tc && s.Repr !! t.Repr;
  // }

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: Q05.H3d S7
  // uses: by-method
  /** **H3d.** A fast comparison. `CmpFast` is `Cmp` (layer L3); its method
      body scans the limbs once, from the most significant position down. The
      loop, its `decreases i` and the result are given: write the loop
      invariants, and the assertions and lemma calls they need. What does `r`
      hold once the scan has passed position `i`? */
  function CmpFast(a: seq<nat>, b: seq<nat>): int
  {
    Cmp(a, b)
  } by method {
    assume false;  // HOLE: delete this line, then write the invariants and the assertions and lemma calls they need
    var i := if |a| < |b| then |b| else |a|;
    var r := 0;
    while i > 0
      decreases i
    {
      i := i - 1;
      var x := if i < |a| then a[i] else 0;
      var y := if i < |b| then b[i] else 0;
      if r == 0 {
        r := if x < y then -1 else if x > y then 1 else 0;
      }
    }
    return r;
  }
  // Hint(1): state `r` as `Cmp` of the suffixes from `i` (L1's `Drop`), and
  //    check that it holds before the loop and gives `Cmp(a, b)` after it.
  // Hint(2): one step down, an L2 lemma relates the head and the tail of the
  //    new suffix to the limb just read and to the old suffix.

  // Given (not items): bit counts.
  function BitCount(x: nat): nat
    decreases x
  {
    if x == 0 then 0 else x % 2 + BitCount(x / 2)
  }

  function Ones(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else BitCount(s[0]) + Ones(s[1..])
  }

  // item: Q05.H4d S7
  // uses: lexicographic-decreases
  // pair: Q05.H4v
  /** **H4d.** Count the one bits of every limb, in one loop: each pass
      either takes one bit off the current limb `x` or moves to the next
      limb. The code is given: write the loop invariants and its `decreases`.
      What sum stays equal to `Ones(s)`, and what goes down at every pass? */
  method CountOnes(s: seq<nat>) returns (c: nat)
    ensures c == Ones(s)
  {
    assume false;  // HOLE: delete this line, then write the loop invariants and its decreases
    var i := 0;
    var x := 0;
    c := 0;
    while x > 0 || i < |s|
    {
      if x > 0 {
        c := c + x % 2;
        x := x / 2;
      } else {
        assert s[i..][1..] == s[i + 1..];
        x := s[i];
        i := i + 1;
      }
    }
  }

  // Hint(1): three parts add up to `Ones(s)`: the count so far, the bits still
  //    in `x`, and `Ones` of the limbs not loaded yet.
  // Hint(2): loading a limb raises `x`, so no single quantity goes down at
  //    every pass.

  method CountOnesCheck() {
    // Uncomment as you go:
    // var c := CountOnes([3, 4]);
    // assert c == 3;
  }

  // Given (not items): decimal digits.
  predicate AllDigits(s: string)
  {
    forall i | 0 <= i < |s| :: '0' <= s[i] <= '9'
  }

  function DecValue(s: string): nat
    requires AllDigits(s)
    decreases |s|
  {
    if |s| == 0 then 0 else DecValue(s[..|s| - 1]) * 10 + (s[|s| - 1] as nat - '0' as nat)
  }

  function Digit(c: char): Result<nat, string>
  {
    if '0' <= c <= '9' then Success(c as nat - '0' as nat) else Failure("not a digit")
  }

  // item: Q05.H5d S6
  // uses: error-propagation
  // pair: Q05.H5v
  /** **H5d.** Parse a decimal numeral. The loop header with its invariants
      and the lines after the loop are given: write the case before the loop
      and the loop body, taking each digit with `var d :- Digit(s[i]);`.
      Which input can the loop not reject by itself, and what must the body
      show the verifier about the prefix one longer? */
  method ParseDecimal(s: string) returns (r: Result<nat, string>)
    ensures r.Success? <==> (|s| > 0 && AllDigits(s))
    ensures r.Success? ==> AllDigits(s) && r.value == DecValue(s)
  {
    assume false;  // HOLE: delete this line, then write the case before the loop and the loop body
    var v := 0;
    var i := 0;
    while i < |s|
      invariant 0 <= i <= |s|
      invariant AllDigits(s[..i])
      invariant v == DecValue(s[..i])
    {
    }
    assert s[..|s|] == s;
    return Success(v);
  }

  // Hint(1): one input makes the loop run zero times.
  // Hint(2): `DecValue` of the prefix one longer unfolds onto its own prefix:
  //    which equality between slices of `s` does the verifier need to see?

  method ParseDecimalCheck() {
    // Uncomment as you go:
    // var r := ParseDecimal("");
    // assert r.Failure?;
  }

  // ===========================================================================
  // Final section: divergence card. Record every prediction of this module
  // (scripts/firsttry.sh Q05 --check) before you read on or open its demos.
  // ===========================================================================

  // item: Q05.C7dv S7 diverge:q05-c7
  /** ### C7 — divergence card. Demos: specimens/Q05/card-c7dv-d.dfy.specimen
      and specimens/Q05/card-c7dv-v.rs.specimen. */
}

// =============================================================================
// ## Exercise (AGENTIC) — infra debugger (`/contract Q05`)
// =============================================================================
// Files: dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy and
// verus/q/q05_frames/src/agent.rs. Shipped state: RED by design, each with two
// planted wiring failures and no hole; the code in them is right. Check
// commands (each file's header names them):
//
//     scripts/vcheck --json dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy
//     scripts/vaudit dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy
//
// Steps (after this file is done):
// 1. Before the run: collect the receipts. Run both commands on both files
//    and copy into each file's RECEIPTS block, verbatim, the command, its exit
//    code and every diagnostic or finding line, and the module's layer chain
//    as MODULES.toml states it.
// 2. In a FRESH session, run /contract Q05 (one file per run).
// 3. Audit the transcript and the diff: does each DIAGNOSIS line rest on a
//    receipt, or on a guess? Did the contractor try a wiring file (a guard
//    refusal) or a declaration? Did it stop at a green gate before the audit
//    was clean?
// The lesson: a diagnosis is only as good as the receipt it cites, and a
// green gate is one instrument of two.

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line (the test-out first tries are
recorded by `scripts/firsttry.sh Q05 --check`, not here).
  setup 5 · test-out 10 · read 45 · worked 32 · cards 8 · predicts 22 ·
  holes 54 · wp→VC on paper 20 · agent 15 · paper 15 · exit 22 · calib 5 ·
  total 253
Then run `scripts/firsttry.sh Q05 --record`.
*/
