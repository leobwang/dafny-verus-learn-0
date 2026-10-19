/*!
# R02 — Datatypes and recursion (Reference Solution)

Standalone R track. Import only the frozen A1 definitions; no earlier learner
file or later A1b fact is needed. The paired exercise is verus/r/r02_datatypes/src/lib.rs.

Before reading the worked examples, attempt T1 closed book. Fill the five
predictions in slots/R02.slots, specimens/R02/P1d.dfy.specimen,
specimens/R02/P2v.rs.specimen and dafny/checks/R02_checks.dfy. Record the first
attempt using scripts/firsttry.sh R02 --check before running their scenarios.
Five typed holes ship in this language, ten across the pair. T1 starts empty
and has a commented use-site check: it is a separate code test-out.

File order: the test-out, the prediction block, the worked examples (W1, W2),
the cards (C1 to C5), the given VoidSpec, the holes (H1 to H5) and H5's given
client, then the final divergence card (C7). Each hole comes after the cards
its `uses:` line names; chapter §2 teaches the witness extraction H4v needs.

Done: every unit gates with zero tool-counted holes, vaudit is clean,
specfreeze --check R02 passes, and firsttry's strict report is OK. Preserve
given contracts and implementations. /tutor R02 is available after an attempt.
*/
module R02_Datatypes {
  import opened RG_A1_Re

  // item: R02.T1d
  // uses: datatype-match, decreases
  // pair: R02.T1v
  /** Closed book: define function ChrCount(r: Re): nat, counting Chr leaves
      structurally. Empty and Eps have none; a Star retains its body's leaves.
      Write it here, uncomment its check, then record the first attempt. */
  // reference-only: completed closed-book definition
  function ChrCount(r: Re): nat
    decreases r
  {
    match r
    case Chr(_) => 1
    case Alt(a, b) => ChrCount(a) + ChrCount(b)
    case Cat(a, b) => ChrCount(a) + ChrCount(b)
    case Star(a) => ChrCount(a)
    case _ => 0
  }
  // Reference checks (enabled):
  // reference-only: enabled shipped check
  lemma ChrCountCheck() ensures ChrCount(Cat(Chr('a'), Star(Alt(Chr('b'), Eps)))) == 2 {}

  // Prediction block: do not run the scenarios until these slots are recorded.
  // item: R02.P3dv verdict
  /** Change A1 Matches' Star split bound from 0 < i to 0 <= i, leaving the
      recursive calls and decreases unchanged. Predict verification in each
      language. Answer form: D:<v> V:<v>, v is ok, fail, timeout or err:<stage>. */
  // CHECK P3dv
  // item: R02.P4dv verdict
  /** Change only Matches' measure from decreases r, |s| (s.len() in Verus)
      to decreases r. Predict verification. Same answer form as P3dv. */
  // CHECK P4dv

  // ===========================================================================
  // Worked examples
  // ===========================================================================

  // item: R02.W1d
  /** Name the split of a concrete concatenation rather than hoping a solver
      invents the witness. The slice facts connect that witness to the goal. */
  lemma MatchesAB()
    ensures Matches(Cat(Chr('a'), Chr('b')), ['a', 'b'])
  {
    assert ['a', 'b'][..1] == ['a'];
    assert ['a', 'b'][1..] == ['b'];
    assert Matches(Chr('a'), ['a', 'b'][..1]);
    assert Matches(Chr('b'), ['a', 'b'][1..]);
    assert exists i | 0 <= i <= 2 :: Matches(Chr('a'), ['a', 'b'][..i]) && Matches(Chr('b'), ['a', 'b'][i..]);
  }

  // item: R02.W2d
  /** A recursive method over the datatype, tied to its spec function by its
      postcondition. Each recursive call returns a value with the same
      contract for a child; the branch combines the two. */
  function StarCountSpec(r: Re): nat
    decreases r
  {
    match r
    case Alt(a, b) => StarCountSpec(a) + StarCountSpec(b)
    case Cat(a, b) => StarCountSpec(a) + StarCountSpec(b)
    case Star(a) => 1 + StarCountSpec(a)
    case _ => 0
  }

  method StarCount(r: Re) returns (n: nat)
    ensures n == StarCountSpec(r)
    decreases r
  {
    match r
    case Alt(a, b) =>
      var x := StarCount(a);
      var y := StarCount(b);
      n := x + y;
    case Cat(a, b) =>
      var x := StarCount(a);
      var y := StarCount(b);
      n := x + y;
    case Star(a) =>
      var x := StarCount(a);
      n := 1 + x;
    case _ =>
      n := 0;
  }

  // ===========================================================================
  // Cards
  // ===========================================================================

  // item: R02.C1d write:datatype-match
  // EXPECT: card-c1d.dfy.specimen is rejected: its match omits constructors.
  function RegexOuterTag(r: Re): nat
  {
    match r
    case Empty => 0
    case Eps => 1
    case Chr(_) => 2
    case Alt(_, _) => 3
    case Cat(_, _) => 4
    case Star(_) => 5
  }

  // item: R02.C2d write:decreases
  // EXPECT: card-c2d.dfy.specimen fails to establish a strict decrease.
  function OuterStars(r: Re): nat
    decreases r
  {
    match r
    case Star(a) => 1 + OuterStars(a)
    case _ => 0
  }

  // item: R02.C3d write:exists-witness
  // EXPECT: card-c3d.dfy.specimen fails: its precondition promises no '#'.
  lemma MarkedPosition(s: seq<char>, i: int)
    requires 0 <= i < |s| && s[i] == '#'
    ensures exists k :: 0 <= k < |s| && s[k] == '#'
  {
    assert 0 <= i < |s| && s[i] == '#';
  }

  // item: R02.C4dv recognise:test
  // Dafny @Test methods are verified; Rust #[test] functions outside verus!
  // are native tests. A finite sample and a universal contract are different evidence.
  @Test
  method RegexSampleTest()
  {
    expect !Nullable(Chr('z'));
  }

  // Given structural specification for H5. It means no string is matched.
  ghost predicate VoidSpec(r: Re)
    decreases r
  {
    match r
    case Empty => true
    case Eps => false
    case Chr(_) => false
    case Alt(a, b) => VoidSpec(a) && VoidSpec(b)
    case Cat(a, b) => VoidSpec(a) || VoidSpec(b)
    case Star(_) => false
  }

  // item: R02.C5dv recognise:ghost
  // VoidSpec above is a ghost predicate; the paired void_spec is a spec fn.
  // Keep specification evaluation separate from a compiled executable.

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: R02.H1d
  // uses: datatype-match, exists-witness
  // pair: R02.H1v
  /** **H1.** The structural test `Nullable` agrees with the semantics on the
      empty string. Prove it by structural induction: a call of this lemma on
      a child is that child's hypothesis (the lever `{:induction false}` keeps
      Dafny from finding the calls for you). Which constructors need their
      children's hypotheses, and which split of the empty string does `Cat`
      need? */
  lemma {:induction false} NullableCorrect(r: Re)
    ensures Nullable(r) <==> Matches(r, [])
    decreases r
  {
    // @hole-begin R02.H1d
    match r
    case Empty =>
    case Eps =>
    case Chr(_) =>
    case Alt(a, b) =>
      NullableCorrect(a);
      NullableCorrect(b);
    case Cat(a, b) =>
      NullableCorrect(a);
      NullableCorrect(b);
      var e: seq<char> := [];
      assert e[..0] == e;
      assert e[0..] == e;
    case Star(_) =>
    // @hole-end R02.H1d
  }
  // Hint(1): match on r; the leaves and Star follow from the two definitions alone.
  // Hint(2): the empty string has exactly one split; name its two slices as
  //    sequences, the way W1 names the split of ['a', 'b'].

  // item: R02.H2d
  // uses: datatype-match
  // pair: R02.H2v
  /** **H2.** Reading a regex backwards keeps its node count, and every regex
      has at least one node. Which cases of `Backwards` rebuild a node with
      recursive children, and what must be known about those children before
      the counts can be compared? */
  lemma {:induction false} NodeCountBackwards(r: Re)
    ensures NodeCount(r) >= 1 && NodeCount(Backwards(r)) == NodeCount(r)
    decreases r
  {
    // @hole-begin R02.H2d
    match r
    case Empty =>
    case Eps =>
    case Chr(_) =>
    case Alt(a, b) =>
      NodeCountBackwards(a);
      NodeCountBackwards(b);
    case Cat(a, b) =>
      NodeCountBackwards(a);
      NodeCountBackwards(b);
    case Star(a) =>
      NodeCountBackwards(a);
    // @hole-end R02.H2d
  }
  // Hint(1): one case per constructor; a leaf is its own backwards form.
  // Hint(2): `Cat` swaps its children under `Backwards`; a sum does not care
  //    about the order once each child's fact is in scope.

  // item: R02.H3d
  // uses: datatype-match
  // pair: R02.H3v
  /** **H3.** Reading a regex backwards keeps its nullability. In which case
      does `Backwards` reorder the children, and why does `Nullable` not
      notice the order? */
  lemma {:induction false} NullableBackwards(r: Re)
    ensures Nullable(Backwards(r)) == Nullable(r)
    decreases r
  {
    // @hole-begin R02.H3d
    match r
    case Empty =>
    case Eps =>
    case Chr(_) =>
    case Alt(a, b) =>
      NullableBackwards(a);
      NullableBackwards(b);
    case Cat(a, b) =>
      NullableBackwards(a);
      NullableBackwards(b);
    case Star(_) =>
    // @hole-end R02.H3d
  }
  // Hint(1): the skeleton of H2 works here too.
  // Hint(2): `Nullable` of a `Cat` is a conjunction of the children's values.

  // item: R02.H4d
  // uses: exists-witness
  // pair: R02.H4v
  /** **H4.** Putting `Eps` in front changes no language. Each direction is
      about the existential over split points in `Matches`' `Cat` case: which
      split proves `Matches(Cat(Eps, r), s)` from `Matches(r, s)`, and what
      does `Eps` force about any split of a match of `Cat(Eps, r)`? */
  lemma CatEpsLeft(r: Re, s: seq<char>)
    ensures Matches(Cat(Eps, r), s) <==> Matches(r, s)
  {
    // @hole-begin R02.H4d
    if Matches(r, s) {
      assert s[..0] == [];
      assert s[0..] == s;
    }
    // @hole-end R02.H4d
  }
  // Hint(1): `Eps` matches one string only, so it can take only one prefix.
  // Hint(2): name that split by its slices, as W1 does; one of them is the empty sequence.

  // item: R02.H5d
  // uses: datatype-match, decreases
  // pair: R02.H5v
  /** **H5.** Implement `IsVoid`, an executable emptiness test: it returns
      `VoidSpec(r)`, computed by recursion over the tree (`VoidSpec` is ghost,
      so the method cannot call it). Which constructors are void on their own,
      and how do `Alt` and `Cat` combine their children's answers? */
  method IsVoid(r: Re) returns (b: bool)
    ensures b == VoidSpec(r)
    decreases r
  {
    // @impl-begin R02.H5d
    match r
    case Empty =>
      b := true;
    case Eps =>
      b := false;
    case Chr(_) =>
      b := false;
    case Alt(a, c) =>
      var x := IsVoid(a);
      var y := IsVoid(c);
      b := x && y;
    case Cat(a, c) =>
      var x := IsVoid(a);
      var y := IsVoid(c);
      b := x || y;
    case Star(_) =>
      b := false;
    // @impl-end R02.H5d
  }
  // Hint(1): W2's `StarCount` has the shape: one recursive call per child, each bound to a local.
  // Hint(2): the given `VoidSpec` is the table to implement, one constructor at a time.

  // Given (not an item): H5's use-site check. It verifies against IsVoid's
  // contract now and must keep verifying once your body replaces the hole.
  method IsVoidClient()
  {
    var dead := IsVoid(Cat(Chr('a'), Empty));
    assert dead;
    var live := IsVoid(Star(Empty));
    assert !live;
  }

  // item: R02.C7dv diverge:r02-c7
  // FINAL CARD: match on a value vs a borrowed tree containing Box values.
  // EXPECT: card-c7dv-d.dfy.specimen fails its equality; card-c7dv-v.rs.specimen
  // is rejected for its type mismatch. Read the returned stage in each column.

}
