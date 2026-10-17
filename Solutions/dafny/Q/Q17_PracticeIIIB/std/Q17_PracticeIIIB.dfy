/*!
# Q17 — Practice III-B (Reference Solution)

Hole-free reference for `dafny/Q/Q17_PracticeIIIB/std/Q17_PracticeIIIB.dfy`
(author-only; never learner-visible). Same module, names, statements, item
markers and order as the exercise file. Every hole is filled and every check
is live. The learner's own declarations are in the `HELPERS` area (an
ordering predicate and three lemmas) and inside the class (two helper
methods), each marked `// reference-only`
(Solutions/plans/Q17-code-notes.md).

The file is silent: `scripts/vcheck --ref` on its unit prints only the
summary line.
*/
module Q17_PracticeIIIB {

  // ===========================================================================
  // The priority queue (H1)
  // ===========================================================================

  // Given (not an item): a priority queue of naturals, specified on its ghost
  // model `Model` and its ghost frame `Repr`.
  trait PQueue {
    ghost var Model: multiset<nat>
    ghost var Repr: set<object>

    ghost predicate Valid()
      reads this, Repr

    method Insert(x: nat)
      requires Valid()
      modifies Repr
      ensures Valid() && Model == old(Model) + multiset{x} && fresh(Repr - old(Repr))

    method ExtractMin() returns (m: nat)
      requires Valid() && |Model| > 0
      modifies Repr
      ensures Valid() && m in old(Model) && (forall y | y in old(Model) :: m <= y)
      ensures Model == old(Model) - multiset{m} && fresh(Repr - old(Repr))
  }

  // HELPERS (Q17.H1d): your predicates and lemmas, here.
  // reference-only: the learner's ordering predicate
  ghost predicate Desc(s: seq<nat>)
  {
    forall i, j | 0 <= i < j < |s| :: s[i] >= s[j]
  }

  // reference-only: the learner's lemma (the minimum of a sorted prefix)
  lemma DescLastMin(s: seq<nat>)
    requires Desc(s) && |s| > 0
    ensures forall y | y in multiset(s) :: s[|s| - 1] <= y
  {
    forall y | y in multiset(s)
      ensures s[|s| - 1] <= y
    {
      assert y in s;
    }
  }

  // reference-only: the learner's lemma (a sorted insertion: order and multiset)
  lemma DescInsert(s: seq<nat>, i: nat, x: nat)
    requires Desc(s) && i <= |s|
    requires i > 0 ==> x <= s[i - 1]
    requires forall j | i <= j < |s| :: s[j] < x
    ensures Desc(s[..i] + [x] + s[i..]) && multiset(s[..i] + [x] + s[i..]) == multiset(s) + multiset{x}
  {
    assert s == s[..i] + s[i..];
  }

  // reference-only: the learner's lemma (the array after the shift, as a sequence)
  lemma Spliced(t: seq<nat>, s: seq<nat>, i: nat, x: nat)
    requires |t| == |s| + 1 && i <= |s| && t[i] == x
    requires forall j | 0 <= j < i :: t[j] == s[j]
    requires forall j | i < j < |t| :: t[j] == s[j - 1]
    ensures t == s[..i] + [x] + s[i..]
  {
  }

  // item: Q17.H1d S6
  // uses: dynamic-frames, invariant
  /** **H1.** Reference: `Valid` keeps the array and the object in `Repr`, a
      non-empty array, the prefix `a[..n]` in descending order and its
      multiset equal to `Model`. `Insert` grows the array by copy when it is
      full (`MakeRoom`, whose fresh array joins `Repr`), then shifts the
      smaller elements one place up and writes `x` in the gap (`Shift`);
      `ExtractMin` takes the last element of the prefix. The two helpers keep
      each method's proof small enough to be stable on both solvers. */
  class ArrayPQ extends PQueue {
    var a: array<nat>
    var n: nat

    ghost predicate Valid()
      reads this, Repr
    {
      this in Repr && a in Repr && n <= a.Length && 0 < a.Length &&
      Desc(a[..n]) && Model == multiset(a[..n])
    }

    constructor ()
      ensures Valid() && fresh(Repr) && Model == multiset{}
    {
      a := new nat[4];
      n := 0;
      Model := multiset{};
      Repr := {this, a};
    }

    // reference-only: the learner's helper method (growth by copy, when full)
    method MakeRoom()
      requires Valid()
      modifies this
      ensures Valid() && n < a.Length && n == old(n) && a[..n] == old(a[..n])
      ensures Model == old(Model) && fresh(Repr - old(Repr))
    {
      if n < a.Length {
        return;
      }
      var b := new nat[2 * a.Length];
      var k := 0;
      while k < n
        invariant k <= n < b.Length
        invariant b[..k] == a[..k]
        modifies b
      {
        b[k] := a[k];
        k := k + 1;
      }
      assert b[..n] == a[..n];
      a := b;
      Repr := Repr + {b};
    }

    // reference-only: the learner's helper method (the sorted insertion's shift)
    method Shift(x: nat) returns (i: nat)
      requires n < a.Length
      modifies a
      ensures i <= n && (i > 0 ==> x <= old(a[..n])[i - 1])
      ensures forall j | i <= j < n :: old(a[..n])[j] < x
      ensures a[..n + 1] == old(a[..n])[..i] + [x] + old(a[..n])[i..]
    {
      ghost var s := a[..n];
      i := n;
      while 0 < i && a[i - 1] < x
        invariant 0 <= i <= n < a.Length
        invariant forall j | 0 <= j < i :: a[j] == s[j]
        invariant forall j | i < j <= n :: a[j] == s[j - 1]
        invariant forall j | i <= j < n :: s[j] < x
        modifies a
      {
        a[i] := a[i - 1];
        i := i - 1;
      }
      a[i] := x;
      Spliced(a[..n + 1], s, i, x);
    }

    method Insert(x: nat)
      requires Valid()
      modifies Repr
      ensures Valid() && Model == old(Model) + multiset{x} && fresh(Repr - old(Repr))
    {
      MakeRoom();
      ghost var s := a[..n];
      var i := Shift(x);
      DescInsert(s, i, x);
      n := n + 1;
      Model := Model + multiset{x};
    }

    method ExtractMin() returns (m: nat)
      requires Valid() && |Model| > 0
      modifies Repr
      ensures Valid() && m in old(Model) && (forall y | y in old(Model) :: m <= y)
      ensures Model == old(Model) - multiset{m} && fresh(Repr - old(Repr))
    {
      ghost var s := a[..n];
      m := a[n - 1];
      DescLastMin(s);
      assert s == s[..n - 1] + [m];
      n := n - 1;
      assert a[..n] == s[..n];
      Model := Model - multiset{m};
    }

    // reference-only: the given check, uncommented (commented in the exercise file)
    method Peek() returns (m: nat)
      requires Valid() && |Model| > 0
      ensures m in Model && forall y | y in Model :: m <= y
    {
      m := a[n - 1];
    }
  }

  method ArrayPQCheck()
  {
    var q := new ArrayPQ();
    q.Insert(5);
    q.Insert(3);
    q.Insert(8);
    var m := q.ExtractMin();
    assert m == 3 && q.Model == multiset{5, 8};
  }
}
