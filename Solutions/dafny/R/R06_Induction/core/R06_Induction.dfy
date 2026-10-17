/*! R06 — Induction and loops (Reference Solution).
Standalone R, A1/A1b only. The given Deriv and deriv_exec are complete;
no A2 or earlier learner proof is imported. Five holes in each hand file
(T1 and H1-H4); two code test-outs, six predictions and four unseen exits.
T1 is closed book before the worked examples. Record all prediction/test-out
first tries with scripts/firsttry.sh R06 --check before enabling switches.
H1 needs your measure. H2 retains its loop, decreasing measure and proof call;
supply invariants and connecting facts. H4 opens only its requires clause:
repair with the weakest hypothesis, not an arbitrary sufficient restriction.
Done: complete zero-hole native gates, audit, freeze, strict report, checkpoint,
written work, decomposer review, fifth bench card, viva and calibration.
*/
module R06_Induction {
  import opened RG_A1_Re
  import opened RG_A1b_Facts

  // GIVEN: one-character derivative, not a learner hole.
  function Deriv(r: Re, c: char): Re
    decreases r
  {
    match r
    case Empty => Empty
    case Eps => Empty
    case Chr(d) => if c == d then Eps else Empty
    case Alt(a, b) => Alt(Deriv(a, c), Deriv(b, c))
    case Cat(a, b) =>
      if Nullable(a) then Alt(Cat(Deriv(a, c), b), Deriv(b, c)) else Cat(Deriv(a, c), b)
    case Star(a) => Cat(Deriv(a, c), Star(a))
  }

  // item: R06.T1d
  // pair: R06.T1v
  // uses: invariant
  // Closed book before reading; implement with a while loop.
  method AllNullable(rs: seq<Re>) returns (b: bool)
    ensures b <==> forall i :: 0 <= i < |rs| ==> Nullable(rs[i])
  {
    // @impl-begin R06.T1d
    b := true; var i := 0;
    while i < |rs|
      invariant 0 <= i <= |rs|
      invariant b <==> forall j :: 0 <= j < i ==> Nullable(rs[j])
      decreases |rs|-i
    {
      b := b && Nullable(rs[i]);
      i := i+1;
    }
    // @impl-end R06.T1d
  }

  // item: R06.P3dv verdict
  // StarRepeat calls itself on s[1..] with r unchanged, naming the split.
  // Compare [x] decreases r and [y] decreases |s|. D:<x>,<y> V:<x>,<y>.
  // CHECK P3dv
  // item: R06.P6dv verdict
  // StarShortcut claims Matches(Star(a),[c]+s) <==> Matches(Star(Deriv(a,c)),s),
  // calling derivative correctness on the prefixes needed. D:<v> V:<v>.
  // CHECK P6dv
  // item: R06.W1d
  lemma DerivBase(r: Re,c: char,s: seq<char>)
    requires r.Empty? || r.Eps? || r.Chr?
    ensures Matches(Deriv(r,c),s) <==> Matches(r,[c]+s)
  {
    if r.Chr? {
      var w := [c]+s;
      if w == [r.c] { assert w[1..] == s; assert w[0] == c; }
      if s == [] { assert w == [c]; }
    }
  }
  // item: R06.W2d
  method AllSame(s: seq<char>,c: char) returns (b: bool)
    ensures b <==> forall j :: 0 <= j < |s| ==> s[j] == c
  {
    b := true; var i := 0;
    while i < |s|
      invariant 0 <= i <= |s|
      invariant b <==> forall j :: 0 <= j < i ==> s[j] == c
      decreases |s|-i
    { b := b && s[i] == c; i := i+1; }
  }
  // item: R06.C1d write:calc
  // A calc chain names expressions and justifies each relation's bridge.
  // item: R06.C2d write:invariant
  // The invariant is the loop-counter induction hypothesis.
  // item: R06.C3d write:lemma-decreases
  // A recursive lemma's measure decreases on every recursive call.
  // item: R06.C4d write:induction-false
  // {:induction false} makes calls explicit; R06's unit also pins manual induction.
  // item: R06.C5d recognise:induction-auto
  // Dafny can propose automatic induction under its default setting; it is off here.

  // item: R06.H1d
  // pair: R06.H1v
  // uses: lemma-decreases, calc, induction-false
  // The measure is yours; prove the full datatype, including nullable Cat and Star.
  lemma {:induction false} DerivCorrect(r: Re,c: char,s: seq<char>)
    ensures Matches(Deriv(r,c),s) <==> Matches(r,[c]+s)
    decreases r
  {
    // @hole-begin R06.H1d
    calc {
      Matches(Deriv(r,c),s);
      == {

    var w := [c] + s;
    match r
    case Empty =>
    case Eps =>
    case Chr(d) =>
      assert w == [d] <==> (c == d && s == []) by {
        if w == [d] { assert w[1..] == s; assert w[0] == c; }
        if s == [] { assert w == [c]; }
      }
    case Alt(a, b) =>
      DerivCorrect(a, c, s);
      DerivCorrect(b, c, s);
    case Cat(a, b) =>
      NullableCorrect(a);
      DerivCorrect(b, c, s);
      if Matches(r, w) {
        var i :| 0 <= i <= |w| && Matches(a, w[..i]) && Matches(b, w[i..]);
        if i == 0 {
          assert w[..0] == [] && w[0..] == w;
        } else {
          assert w[..i] == [c] + s[..i - 1];
          assert w[i..] == s[i - 1..];
          DerivCorrect(a, c, s[..i - 1]);
          assert Matches(Cat(Deriv(a, c), b), s);
        }
      }
      if Matches(Deriv(r, c), s) {
        if Matches(Cat(Deriv(a, c), b), s) {
          var j :| 0 <= j <= |s| && Matches(Deriv(a, c), s[..j]) && Matches(b, s[j..]);
          DerivCorrect(a, c, s[..j]);
          assert w[..j + 1] == [c] + s[..j];
          assert w[j + 1..] == s[j..];
        } else {
          assert Nullable(a) && Matches(b, w);
          assert w[..0] == [] && w[0..] == w;
        }
      }
    case Star(a) =>
      if Matches(r, w) {
        var i :| 0 < i <= |w| && Matches(a, w[..i]) && Matches(Star(a), w[i..]);
        assert w[..i] == [c] + s[..i - 1];
        assert w[i..] == s[i - 1..];
        DerivCorrect(a, c, s[..i - 1]);
      }
      if Matches(Deriv(r, c), s) {
        var j :| 0 <= j <= |s| && Matches(Deriv(a, c), s[..j]) && Matches(Star(a), s[j..]);
        DerivCorrect(a, c, s[..j]);
        assert w[..j + 1] == [c] + s[..j];
        assert w[j + 1..] == s[j..];
      }

      }
      Matches(r,[c]+s);
    }
    // @hole-end R06.H1d
  }

  // item: R06.H2d
  // pair: R06.H2v
  // uses: invariant
  // Keep the loop, measure and correctness call; supply annotations and bridges.
  method DerivMatch(r: Re,s: seq<char>) returns (b: bool)
    ensures b == Matches(r,s)
  {

    var cur := r; var i := 0;
    while i < |s|
      // @hole-begin R06.H2d
      invariant 0 <= i <= |s|
      invariant Matches(cur,s[i..]) <==> Matches(r,s)
      // @hole-end R06.H2d
      decreases |s|-i
    {
      DerivCorrect(cur,s[i],s[i+1..]);
      // @hole-begin R06.H2d
      assert [s[i]]+s[i+1..] == s[i..];
      // @hole-end R06.H2d
      cur := Deriv(cur,s[i]);
      i := i+1;
    }
    // @hole-begin R06.H2d
    NullableCorrect(cur); assert s[i..] == [];
    // @hole-end R06.H2d
    b := Nullable(cur);
  }

  // item: R06.H3d
  // pair: R06.H3v
  lemma StarUnfoldRefuted()
    ensures exists a: Re,s: seq<char> :: Matches(Star(a),s) && !Matches(Cat(a,Star(a)),s)
  {
    // @hole-begin R06.H3d
    var a := Chr('x'); var s: seq<char> := [];
    assert Matches(Star(a),s);
    assert !Matches(Cat(a,Star(a)),s);
    // @hole-end R06.H3d
  }

  // item: R06.H4d
  // pair: R06.H4v
  // uses: calc
  // REPAIR: add the weakest sufficient requires; do not narrow more than needed.
  lemma StarUnfold(a: Re,s: seq<char>)
    requires s != [] || Nullable(a)
    ensures Matches(Star(a),s) <==> Matches(Cat(a,Star(a)),s)
  {
    // @hole-begin R06.H4d

    calc {
      Matches(Star(a),s);
      == {
        if s == [] {
          NullableCorrect(a);
          assert s[..0] == [] && s[0..] == [];
        }
        if Matches(Star(a),s) && s != [] {
          var i :| 0 < i <= |s| && Matches(a,s[..i]) && Matches(Star(a),s[i..]);
          assert Matches(Cat(a,Star(a)),s);
        }
        if Matches(Cat(a,Star(a)),s) {
          var i :| 0 <= i <= |s| && Matches(a,s[..i]) && Matches(Star(a),s[i..]);
          if i == 0 { assert s[i..] == s; }
          else { assert Matches(Star(a),s); }
        }
      }
      Matches(Cat(a,Star(a)),s);
    }
    // @hole-end R06.H4d
  }

  /* CALIBRATION — estimated / actual minutes, first-try confidence,
     mathematical idea / native obstacle / correction: ...
     The flagship's Cat-case paper argument precedes its keyboard proof.
     The repair's weakest-hypothesis requirement has a human review component;
     a stronger sufficient restriction can still pass native verification.
  */
  // item: R06.C6dv diverge:r06-c6
  // FINAL CARD: calc chains and their step hints; record predictions first.
}
