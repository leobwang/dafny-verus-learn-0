/*!
# Q33 — The statement problem: the dev prose items, Dafny half (Exercises)

Six prose tasks (QPLAN §35.1: part A's hand calibration). Each ships a method's signature
and its implementation, and no specification: you write its `requires` and `ensures` from
the prose. Its code is given; you may add proof lines to its body (invariants, assertions,
lemma calls), never change its code. Then uncomment the use-site check in its client, write
a non-vacuity witness (one call whose `requires` hold) in its witness method, and delete
the client's assume. The statements you write by hand calibrate your pipeline's self-checks.

What grades a specification: the use-site check (an adequate one verifies it), your witness,
/review-code, and, in the grader container, a hidden two-way check against the author's
specification. The frozen parts of this file (every declaration but the six prose methods)
are pinned by Q33_StatementProblemStatement.dfy (`[[against]]` in Q33_Statement.toml).

This file ships with exactly 6 holes (H5d-H10d), each counted by `scripts/vcheck`: one
labelled assume per client.
*/
module Q33_StatementProblem {
  // item: Q33.H5d S12
  // uses: ensures, witness
  // prose: InsertPoint
  /** **H5.** Prose task. *The index at which x goes into the ascending sequence s to keep it ascending, after every element equal to x: every element before the index is at most x, every element from it on exceeds x.* Write `InsertPoint`'s specification. */
  method InsertPoint(s: seq<int>, x: int) returns (i: nat)
    requires forall p, q | 0 <= p < q < |s| :: s[p] <= s[q]
    ensures i <= |s|
    ensures forall k | 0 <= k < i :: s[k] <= x
    ensures forall k | i <= k < |s| :: s[k] > x
  {
    if |s| == 0 || s[0] > x {
      i := 0;
    } else {
      var j := InsertPoint(s[1..], x);
      i := j + 1;
    }
  }

  method InsertPointUse()
  {
    var s := [1, 3, 5];
    var i := InsertPoint(s, 4);
    assert s[1] == 3 && s[2] == 5;
    assert i == 2;
  }

  /** Your non-vacuity witness for `InsertPoint`: one call whose `requires` hold. */
  method InsertPointWitness()
  {
    var i := InsertPoint([2, 4], 3);
  }

  // item: Q33.H6d S12
  // uses: ensures, witness
  // prose: DropLeadingZeros
  /** **H6.** Prose task. *A digit sequence d (most significant digit first) without its leading zero digits: the longest suffix of d that does not start with 0.* Write `DropLeadingZeros`'s specification. */
  method DropLeadingZeros(d: seq<nat>) returns (r: seq<nat>)
    ensures |r| <= |d|
    ensures r == d[|d| - |r|..]
    ensures |r| == 0 || r[0] != 0
    ensures forall k | 0 <= k < |d| - |r| :: d[k] == 0
  {
    if |d| > 0 && d[0] == 0 {
      r := DropLeadingZeros(d[1..]);
    } else {
      r := d;
    }
  }

  method DropLeadingZerosUse()
  {
    var d := [0, 5];
    var r := DropLeadingZeros(d);
    assert d[0] == 0 && d[1] == 5;
    assert |r| == 1;
    assert r == d[1..];
    assert r == [5];
  }

  /** Your non-vacuity witness for `DropLeadingZeros`: one call whose `requires` hold. */
  method DropLeadingZerosWitness()
  {
    var r := DropLeadingZeros([0, 1]);
  }

  // item: Q33.H7d S12
  // uses: ensures, witness
  // prose: ClauseHolds
  /** **H7.** Prose task. *Whether a clause (a disjunction of literals) is true under an assignment: some literal of it holds. A literal (v, true) is variable v and (v, false) its negation; every variable of the clause is an index into assign.* Write `ClauseHolds`'s specification. */
  method ClauseHolds(clause: seq<(nat, bool)>, assign: seq<bool>) returns (b: bool)
    requires forall k | 0 <= k < |clause| :: clause[k].0 < |assign|
    ensures b <==> exists k | 0 <= k < |clause| :: assign[clause[k].0] == clause[k].1
  {
    if |clause| == 0 {
      b := false;
    } else if clause[0].0 < |assign| && assign[clause[0].0] == clause[0].1 {
      b := true;
    } else {
      b := ClauseHolds(clause[1..], assign);
    }
  }

  method ClauseHoldsUse()
  {
    var b := ClauseHolds([(0, false), (1, false)], [true, true]);
    assert !b;
  }

  /** Your non-vacuity witness for `ClauseHolds`: one call whose `requires` hold. */
  method ClauseHoldsWitness()
  {
    var b := ClauseHolds([(0, true)], [true]);
  }

  // item: Q33.H8d S12
  // uses: ensures, witness
  // prose: FirstRunLength
  /** **H8.** Prose task. *How many elements at the front of the non-empty sequence s equal its first element: the length of its first run.* Write `FirstRunLength`'s specification. */
  method FirstRunLength(s: seq<int>) returns (n: nat)
    requires |s| > 0
    ensures 1 <= n <= |s|
    ensures forall k | 0 <= k < n :: s[k] == s[0]
    ensures n < |s| ==> s[n] != s[0]
  {
    if |s| == 0 {
      n := 0;
    } else {
      n := 1;
      while n < |s| && s[n] == s[0]
        invariant 1 <= n <= |s|
        invariant forall k | 0 <= k < n :: s[k] == s[0]
      {
        n := n + 1;
      }
    }
  }

  method FirstRunLengthUse()
  {
    var s := [4, 4, 1];
    var n := FirstRunLength(s);
    assert s[1] == 4 && s[2] == 1;
    assert n == 2;
  }

  /** Your non-vacuity witness for `FirstRunLength`: one call whose `requires` hold. */
  method FirstRunLengthWitness()
  {
    var n := FirstRunLength([1]);
  }

  // item: Q33.H9d S12
  // uses: ensures, witness
  // prose: MergeFromA
  /** **H9.** Prose task. *Which list the next element of the merge of two ascending lists a and b (not both empty) comes from: true for a when a is not empty and its head is at most b's (or b is empty), false for b otherwise.* Write `MergeFromA`'s specification. */
  method MergeFromA(a: seq<int>, b: seq<int>) returns (fromA: bool)
    requires |a| + |b| > 0
    ensures fromA ==> |a| > 0 && (|b| == 0 || a[0] <= b[0])
    ensures !fromA ==> |b| > 0 && (|a| == 0 || b[0] < a[0])
  {
    if |a| == 0 {
      fromA := false;
    } else if |b| == 0 {
      fromA := true;
    } else {
      fromA := a[0] <= b[0];
    }
  }

  method MergeFromAUse()
  {
    var f := MergeFromA([2], [2]);
    assert f;
  }

  /** Your non-vacuity witness for `MergeFromA`: one call whose `requires` hold. */
  method MergeFromAWitness()
  {
    var f := MergeFromA([], [1]);
  }

  // item: Q33.H10d S12
  // uses: ensures, witness
  // prose: SortedPrefix
  /** **H10.** Prose task. *Whether the first k elements of s (k at most |s|) are in ascending order: each is no greater than the next.* Write `SortedPrefix`'s specification. */
  method SortedPrefix(s: seq<int>, k: nat) returns (b: bool)
    requires k <= |s|
    ensures b <==> forall p | 0 < p < k :: s[p - 1] <= s[p]
  {
    b := true;
    var i := 1;
    while i < k && i < |s|
      invariant 1 <= i
      invariant i <= k || i == 1
      invariant b <==> forall p | 0 < p < i && p < k :: s[p - 1] <= s[p]
    {
      if s[i - 1] > s[i] {
        b := false;
      }
      i := i + 1;
    }
  }

  method SortedPrefixUse()
  {
    var b := SortedPrefix([1, 3, 2], 2);
    assert b;
  }

  /** Your non-vacuity witness for `SortedPrefix`: one call whose `requires` hold. */
  method SortedPrefixWitness()
  {
    var b := SortedPrefix([1, 2], 2);
  }
}
