/*!
# Q05 — Frames, ownership, modes, wp→VC (Reference Solution)

Hole-free reference for `dafny/Q/Q05_Frames/std/Q05_Frames.dfy` (author-only;
never learner-visible). Same module, imports, names, statements, item markers
and order as the exercise file. Every hole is filled, every check is live,
and every verdict switch is enabled; the verdict answers are in
`Solutions/slots/Q05.slots`, their hashes in `expected/Q05.pins`. The
learner's regions of the annotation and code holes (H1d–H5d) are marked
`@hole-begin <id>` … `@hole-end <id>` for the empty-body gate's region mode
and the statement freeze (H2d's header clauses are its open frame).

The file is silent: `scripts/vcheck --ref` on its unit prints only the
summary line. Every output the module quotes is pinned: the count pins in
`expected/Q05.counts`, the statement freeze in `expected/Q05.freeze`, the
WRITE-card failure demos by their in-file `// EXPECT` lines, and the
divergence demos by their sidecars under `expected/specimens/Q05/`.
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
  // CHECK P1dv

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
  // CHECK P2dv

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
  // CHECK P3dv

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
  // CHECK P9dv

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
  // (Reference) Neither argument alone goes down at every step: a reset raises `lo` back
  // to 9. The pair does, compared left to right, so the measure is `hi, lo`. Dafny's
  // default measure is the parameters in the order they are declared, `lo, hi`, which the
  // reset breaks: it must be written out.
  // reference-only: the learner writes this function (a prompt-as-heading block)
  function Odometer(lo: nat, hi: nat): nat
    decreases hi, lo
  {
    if lo > 0 then 1 + Odometer(lo - 1, hi)
    else if hi > 0 then 1 + Odometer(9, hi - 1)
    else 0
  }

  // reference-only: the learner uncomments this check
  lemma OdometerCheck()
    ensures Odometer(2, 1) == 12
  {
  }

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
        array to `Repr`.

        Reference: the copy loop writes only `b`, the fresh array, so its frame
        is `modifies b`. Without it a loop inside a method may modify every
        object of the method's own frame, `Repr`, which holds `a`, so after
        the loop the verifier no longer knows what `a` holds. The invariants
        keep the indices in range and say that the copied prefix agrees:
        `b[..i] == a[..i]`, which at the end gives `b[..n] == a[..n] ==
        Contents`. */
    method Push(x: nat)
      requires Valid()
      modifies Repr
      ensures Valid() && Contents == old(Contents) + [x] && fresh(Repr - old(Repr))
    {
      if n == a.Length {
        var b := new nat[2 * a.Length + 1];
        var i := 0;
        while i < n
          // @hole-begin Q05.H1d
          invariant 0 <= i <= n <= a.Length < b.Length
          invariant b[..i] == a[..i]
          modifies b
          // @hole-end Q05.H1d
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

    // item: Q05.H2d S6
    // uses: dynamic-frames
    /** **H2d.** Pop the top limb. The body and the functional postcondition
        are given.

        Reference: the body writes the fields of `this` only, so `modifies
        this` is its frame. A client holding another stack needs two more
        facts: that this stack is still valid, and that its representation is
        the same set as before (`Repr == old(Repr)`), so that `s.Repr !!
        t.Repr` still holds and `t`, untouched because `this` is not in
        `t.Repr`, keeps its contents and validity. Any frame clauses from which
        `PopCheck` follows are as good. */
    method Pop() returns (x: nat)
      requires Valid() && |Contents| > 0
      // @hole-begin Q05.H2d
      modifies this
      ensures Valid() && Repr == old(Repr)
      // @hole-end Q05.H2d
      ensures x == old(Contents)[|old(Contents)| - 1] && Contents == old(Contents)[..|old(Contents)| - 1]
    {
      n := n - 1;
      x := a[n];
      Contents := Contents[..n];
    }
  }

  // H1d's check: two pushes onto a stack of capacity 1 (the second one grows
  // the array).
  method PushCheck() {
    var s := new LimbStack(1);
    s.Push(7);
    s.Push(8);
    assert s.Contents == [7, 8];
  }

  // H2d's check: two stacks with disjoint representations; after a pop from
  // `s`, the other stack `t` is valid and holds what it held, and the two
  // representations are still disjoint.
  // reference-only: the learner uncomments this check
  method PopCheck(s: LimbStack, t: LimbStack)
    requires s.Valid() && t.Valid() && s.Repr !! t.Repr && |s.Contents| > 0
    modifies s.Repr
  {
    var tc := t.Contents;
    var x := s.Pop();
    assert t.Valid() && t.Contents == tc && s.Repr !! t.Repr;
  }

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: Q05.H3d S7
  // uses: by-method
  /** **H3d.** A fast comparison. `CmpFast` is `Cmp` (layer L3); its method
      body scans the limbs once, from the most significant position down.

      Reference: the loop keeps `r` equal to the comparison of the suffixes
      from position `i`, `r == Cmp(Drop(a, i), Drop(b, i))`. Before the loop
      both suffixes are empty, so `r == 0` is right (the assertion shows the
      verifier the empty suffixes). One step down, L2's `DropStep` relates
      the suffixes from `i` to the head and tail of the suffixes from `i - 1`
      (a missing limb reads as 0), which is exactly how `Cmp` recurses: a
      difference found higher up wins, so `r` changes only while it is 0. At
      the end the suffixes from 0 are the numerals themselves. */
  function CmpFast(a: seq<nat>, b: seq<nat>): int
  {
    Cmp(a, b)
  } by method {
    var i := if |a| < |b| then |b| else |a|;
    var r := 0;
    // @hole-begin Q05.H3d
    assert Drop(a, i) == [] && Drop(b, i) == [];
    // @hole-end Q05.H3d
    while i > 0
      // @hole-begin Q05.H3d
      invariant 0 <= i <= (if |a| < |b| then |b| else |a|)
      invariant r == Cmp(Drop(a, i), Drop(b, i))
      // @hole-end Q05.H3d
      decreases i
    {
      i := i - 1;
      var x := if i < |a| then a[i] else 0;
      var y := if i < |b| then b[i] else 0;
      // @hole-begin Q05.H3d
      DropStep(a, i);
      DropStep(b, i);
      // @hole-end Q05.H3d
      if r == 0 {
        r := if x < y then -1 else if x > y then 1 else 0;
      }
    }
    // @hole-begin Q05.H3d
    assert Drop(a, 0) == a && Drop(b, 0) == b;
    // @hole-end Q05.H3d
    return r;
  }

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
  /** **H4d.** Count the one bits of every limb, in one loop: each pass either
      takes one bit off the current limb `x` or moves to the next limb.

      Reference: the count so far, the bits still in `x` and the bits of the
      limbs not yet loaded add up to the total:
      `c + BitCount(x) + Ones(s[i..]) == Ones(s)`. Neither `|s| - i` nor `x`
      goes down at every pass (loading a limb raises `x`), but the pair does,
      left to right: `decreases |s| - i, x`. */
  method CountOnes(s: seq<nat>) returns (c: nat)
    ensures c == Ones(s)
  {
    var i := 0;
    var x := 0;
    c := 0;
    while x > 0 || i < |s|
      // @hole-begin Q05.H4d
      invariant 0 <= i <= |s|
      invariant c + BitCount(x) + Ones(s[i..]) == Ones(s)
      decreases |s| - i, x
      // @hole-end Q05.H4d
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

  method CountOnesCheck() {
    var c := CountOnes([3, 4]);
    assert c == 3;
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
  /** **H5d.** Parse a decimal numeral. The loop header with its invariants and
      the lines after the loop are given.

      Reference: the empty string is the one failure the loop cannot find, so
      it is the case before the loop. In the body, `:-` returns `Digit`'s
      failure at once on a non-digit, which the postcondition allows because
      then not every character is a digit; otherwise it binds the digit. The
      assertion shows the verifier that the prefix one longer ends in the new
      digit, so `DecValue` of it unfolds once to `v * 10 + d`. */
  method ParseDecimal(s: string) returns (r: Result<nat, string>)
    ensures r.Success? <==> (|s| > 0 && AllDigits(s))
    ensures r.Success? ==> AllDigits(s) && r.value == DecValue(s)
  {
    // @hole-begin Q05.H5d
    if |s| == 0 {
      return Failure("empty");
    }
    // @hole-end Q05.H5d
    var v := 0;
    var i := 0;
    while i < |s|
      invariant 0 <= i <= |s|
      invariant AllDigits(s[..i])
      invariant v == DecValue(s[..i])
    {
      // @hole-begin Q05.H5d
      var d :- Digit(s[i]);
      assert s[..i + 1][..i] == s[..i];
      v := v * 10 + d;
      i := i + 1;
      // @hole-end Q05.H5d
    }
    assert s[..|s|] == s;
    return Success(v);
  }

  method ParseDecimalCheck() {
    var r := ParseDecimal("");
    assert r.Failure?;
    var q := ParseDecimal("7x");
    assert !AllDigits("7x") by {
      assert "7x"[1] == 'x';
    }
    assert q.Failure?;
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
// — clearly marked: everything below answers the agentic file —
// =============================================================================
// The reference delivery of dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy (and of
// its Verus twin) is that file's own twin, Solutions/dafny/Q/Q05_Frames/agent/
// Q05_AgentInfra.dfy (Solutions/verus/q/q05_frames/src/agent.rs): the repaired
// wiring, the receipts as captured, the diagnosis and the author's note on the
// soft spots, in a closing section under this same heading. They live there,
// beside the file they answer, so one copy is verified and kept.

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line.
  setup 5 · test-out 10 · read 45 · worked 32 · cards 8 · predicts 22 ·
  holes 54 · wp→VC on paper 20 · agent 15 · paper 15 · exit 22 · calib 5 ·
  total 253
*/
