/*!
# R02 — Datatypes and recursion (exercises)

Standalone R track. Import only the frozen A1 definitions; no earlier learner
file or later A1b fact is needed. The paired exercise is verus/r/r02_datatypes/src/lib.rs.

Before reading the worked examples, attempt T1 closed book. Fill the five
predictions in slots/R02.slots, specimens/R02/P1d.dfy.specimen,
specimens/R02/P2v.rs.specimen and dafny/checks/R02_checks.dfy. Record the first
attempt using scripts/firsttry.sh R02 --check before running their scenarios.
Five typed holes ship in this language, ten across the pair. T1 starts empty
and has a commented use-site check: it is a separate code test-out.

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
  // TESTOUT_DEFINITION
  // Uncomment as you go:
  // lemma ChrCountCheck() ensures ChrCount(Cat(Chr('a'), Star(Alt(Chr('b'), Eps)))) == 2 {}

  // Prediction block: do not run the scenarios until these slots are recorded.
  // item: R02.P3dv verdict
  /** Change A1 Matches' Star split bound from 0 < i to 0 <= i, leaving the
      recursive calls and decreases unchanged. Predict verification in each
      language. Answer form: D:<v> V:<v>, v is ok, fail, timeout or err:<stage>. */
  // SLOT: CHECK P3dv
  // item: R02.P4dv verdict
  /** Change only Matches' measure from decreases r, |s| (s.len() in Verus)
      to decreases r. Predict verification. Same answer form as P3dv. */
  // SLOT: CHECK P4dv

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
    case Alt(a, b) => var x := StarCount(a); var y := StarCount(b); n := x + y;
    case Cat(a, b) => var x := StarCount(a); var y := StarCount(b); n := x + y;
    case Star(a) => var x := StarCount(a); n := 1 + x;
    case _ => n := 0;
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

// item: R02.H1d
// uses: datatype-match, exists-witness
// pair: R02.H1v
lemma NullableCorrect(r: Re)
    ensures Nullable(r) <==> Matches(r, [])
    decreases r


// item: R02.H2d
// uses: datatype-match
// pair: R02.H2v
lemma {:induction false} NodeCountBackwards(r: Re)
    ensures NodeCount(r) >= 1 && NodeCount(Backwards(r)) == NodeCount(r)
    decreases r


// item: R02.H3d
// uses: datatype-match
// pair: R02.H3v
lemma {:induction false} NullableBackwards(r: Re)
    ensures Nullable(Backwards(r)) == Nullable(r)
    decreases r


// item: R02.H4d
// uses: exists-witness
// pair: R02.H4v
lemma CatEpsLeft(r: Re, s: seq<char>)
    ensures Matches(Cat(Eps, r), s) <==> Matches(r, s)


// item: R02.H5d
// uses: datatype-match, decreases
// pair: R02.H5v
method IsVoid(r: Re) returns (b: bool)
    ensures b == VoidSpec(r)
    decreases r
  { assume false; }

  // item: R02.C1d write:datatype-match
  // EXPECT: card-c1d.dfy.specimen is rejected: its match omits constructors.
  function RegexOuterTag(r: Re): nat {
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
  { match r case Star(a) => 1 + OuterStars(a) case _ => 0 }

  // item: R02.C3d write:exists-witness
  // EXPECT: card-c3d.dfy.specimen fails: its precondition promises no '#'.
  lemma MarkedPosition(s: seq<char>, i: int)
    requires 0 <= i < |s| && s[i] == '#'
    ensures exists k :: 0 <= k < |s| && s[k] == '#'
  { assert 0 <= i < |s| && s[i] == '#'; }

  // item: R02.C4dv recognise:test
  // Dafny @Test methods are verified; Rust #[test] functions outside verus!
  // are native tests. A finite sample and a universal contract are different evidence.
  @Test method RegexSampleTest() { expect !Nullable(Chr('z')); }

  // item: R02.C5dv recognise:ghost
  // VoidSpec above is a ghost predicate; the paired void_spec is a spec fn.
  // Keep specification evaluation separate from a compiled executable.

  // item: R02.C7dv diverge:r02-c7
  // FINAL CARD: match on a value vs a borrowed tree containing Box values.
  // EXPECT: card-c7dv-d.dfy.specimen fails its equality; card-c7dv-v.rs.specimen
  // is rejected for its type mismatch. Read the returned stage in each column.

}
