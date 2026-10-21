// Reference Solution.
/*! R10 flagship: human statement design, then contractor proof bodies.
Before actor work, write original-domain contracts for all three constructors,
record nonvacuous input/output examples, and snapshot those statements.
The provided output type promises normal shape. Design and justify the
additional language promise yourself. The actor may edit only bodies and
reference-only helpers in its delivery; it must preserve your snapshot.
*/
module R10_AgentFlagship {
  import opened RG_A1_Re
  import opened RG_A1b_Facts
  import opened RG_A4_Norm

  // Your statements: add requires and ensures clauses to each constructor
  // below, and snapshot the file under research/R10/ before any contractor edit.
  // The contractor may add private proof helpers here and write the bodies.

  // reference-only
  lemma StarStar(a: Re, s: seq<char>)
    ensures Matches(Star(Star(a)), s) <==> Matches(Star(a), s)
    decreases |s|
  {
    if Matches(Star(Star(a)), s) && s != [] {
      var i :| 0 < i <= |s| && Matches(Star(a), s[..i]) && Matches(Star(Star(a)), s[i..]);
      StarStar(a, s[i..]);
      StarConcat(a, s[..i], s[i..]);
      assert s[..i] + s[i..] == s;
    }
    if Matches(Star(a), s) && s != [] {
      StarOne(Star(a), s);
    }
  }

  // reference-only
  lemma MkAltCorrect(a: NormRe, b: NormRe, s: seq<char>)
    ensures Matches(MkAlt(a, b), s) <==> Matches(Alt(a, b), s)
  {
  }

  // reference-only
  lemma MkCatCorrect(a: NormRe, b: NormRe, s: seq<char>)
    ensures Matches(MkCat(a, b), s) <==> Matches(Cat(a, b), s)
  {
    if a == Empty || b == Empty {
    } else if a == Eps {
      CatEpsLeft(b, s);
    } else if b == Eps {
      CatEpsRight(a, s);
    }
  }

  // reference-only
  lemma MkStarCorrect(a: NormRe, s: seq<char>)
    ensures Matches(MkStar(a), s) <==> Matches(Star(a), s)
  {
    if a == Empty || a == Eps {
      StarOfEps(a, s);
    } else if a.Star? {
      StarStar(a.r, s);
    }
  }

  // item: R10.A1d
  method BuildAltR10(a: NormRe, b: NormRe) returns (out: NormRe)
    ensures EquivalentReR10(out, Alt(a, b))
  {
    out := MkAlt(a, b);
    forall s: seq<char>
      ensures Matches(out, s) <==> Matches(Alt(a, b), s)
    {
      MkAltCorrect(a, b, s);
    }
  }

  method BuildCatR10(a: NormRe, b: NormRe) returns (out: NormRe)
    ensures EquivalentReR10(out, Cat(a, b))
  {
    out := MkCat(a, b);
    forall s: seq<char>
      ensures Matches(out, s) <==> Matches(Cat(a, b), s)
    {
      MkCatCorrect(a, b, s);
    }
  }

  method BuildStarR10(a: NormRe) returns (out: NormRe)
    ensures EquivalentReR10(out, Star(a))
  {
    out := MkStar(a);
    forall s: seq<char>
      ensures Matches(out, s) <==> Matches(Star(a), s)
    {
      MkStarCorrect(a, s);
    }
  }
}
