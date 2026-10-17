// DVR0 reference, layer A4 (author-only). Ships as dafny/given/R/RG_A4_Norm.dfy, declared by
// R10 (PLAN §2.2, §2.5 step 6): NormRe and the smart-constructor definitions, the congruence
// facts CatCongRight, CatCong and StarOfEps (given: their empty bodies verify under every
// induction setting), and the Derivation trees. The marked regions are R10's and R11's
// references.
module RG_A4_Norm {
  import opened RG_A1_Re
  import opened RG_A1b_Facts
  import opened RG_A2_Deriv
  import opened RG_A3_Syntax

  // ---------------------------------------------------------------------------
  // Normal forms and smart constructors (R10)
  // ---------------------------------------------------------------------------

  predicate Normal(r: Re)
    decreases r
  {
    match r
    case Empty => true
    case Eps => true
    case Chr(_) => true
    case Alt(a, b) => a != Empty && b != Empty && a != b && Normal(a) && Normal(b)
    case Cat(a, b) => a != Empty && b != Empty && a != Eps && b != Eps && Normal(a) && Normal(b)
    case Star(a) => a != Empty && a != Eps && !a.Star? && Normal(a)
  }

  type NormRe = r: Re | Normal(r) witness Empty

  function MkAlt(a: NormRe, b: NormRe): NormRe
  {
    if a == Empty then b else if b == Empty then a else if a == b then a else Alt(a, b)
  }

  function MkCat(a: NormRe, b: NormRe): NormRe
  {
    if a == Empty || b == Empty then Empty
    else if a == Eps then b
    else if b == Eps then a
    else Cat(a, b)
  }

  function MkStar(a: NormRe): NormRe
  {
    if a == Empty || a == Eps then Eps else if a.Star? then a else Star(a)
  }

  // Star of a regex that matches at most the empty string.
  lemma StarOfEps(a: Re, s: seq<char>)
    requires forall t :: Matches(a, t) ==> t == []
    ensures Matches(Star(a), s) <==> s == []
  {
    if s != [] && Matches(Star(a), s) {
      var i :| 0 < i <= |s| && Matches(a, s[..i]) && Matches(Star(a), s[i..]);
      assert s[..i] != [] by { assert |s[..i]| == i; }
    }
  }

  lemma StarStar(a: Re, s: seq<char>)
    ensures Matches(Star(Star(a)), s) <==> Matches(Star(a), s)
    decreases |s|
  {
    // @hole-begin A4.StarStar
    if Matches(Star(Star(a)), s) && s != [] {
      var i :| 0 < i <= |s| && Matches(Star(a), s[..i]) && Matches(Star(Star(a)), s[i..]);
      StarStar(a, s[i..]);
      StarConcat(a, s[..i], s[i..]);
      assert s[..i] + s[i..] == s;
    }
    if Matches(Star(a), s) && s != [] {
      StarOne(Star(a), s);
    }
    // @hole-end A4.StarStar
  }

  lemma MkAltCorrect(a: NormRe, b: NormRe, s: seq<char>)
    ensures Matches(MkAlt(a, b), s) <==> Matches(Alt(a, b), s)
  {
  }

  lemma MkCatCorrect(a: NormRe, b: NormRe, s: seq<char>)
    ensures Matches(MkCat(a, b), s) <==> Matches(Cat(a, b), s)
  {
    // @hole-begin A4.MkCatCorrect
    if a == Empty || b == Empty {
    } else if a == Eps {
      CatEpsLeft(b, s);
    } else if b == Eps {
      CatEpsRight(a, s);
    }
    // @hole-end A4.MkCatCorrect
  }

  lemma MkStarCorrect(a: NormRe, s: seq<char>)
    ensures Matches(MkStar(a), s) <==> Matches(Star(a), s)
  {
    // @hole-begin A4.MkStarCorrect
    if a == Empty || a == Eps {
      StarOfEps(a, s);
    } else if a.Star? {
      StarStar(a.r, s);
    }
    // @hole-end A4.MkStarCorrect
  }

  // Language equality is a congruence for Star.
  lemma StarCong(a: Re, b: Re, s: seq<char>)
    requires forall t :: Matches(a, t) <==> Matches(b, t)
    ensures Matches(Star(a), s) <==> Matches(Star(b), s)
    decreases |s|
  {
    // @hole-begin A4.StarCong
    if s != [] {
      if Matches(Star(a), s) {
        var i :| 0 < i <= |s| && Matches(a, s[..i]) && Matches(Star(a), s[i..]);
        StarCong(a, b, s[i..]);
        assert Matches(b, s[..i]);
      }
      if Matches(Star(b), s) {
        var i :| 0 < i <= |s| && Matches(b, s[..i]) && Matches(Star(b), s[i..]);
        StarCong(a, b, s[i..]);
        assert Matches(a, s[..i]);
      }
    }
    // @hole-end A4.StarCong
  }

  // Replacing the right operand of a Cat by a language-equal one.
  lemma CatCongRight(a: Re, b1: Re, b2: Re, s: seq<char>)
    requires forall t :: Matches(b1, t) <==> Matches(b2, t)
    ensures Matches(Cat(a, b1), s) <==> Matches(Cat(a, b2), s)
  {
    if Matches(Cat(a, b1), s) {
      var i :| 0 <= i <= |s| && Matches(a, s[..i]) && Matches(b1, s[i..]);
      assert Matches(b2, s[i..]);
    }
    if Matches(Cat(a, b2), s) {
      var i :| 0 <= i <= |s| && Matches(a, s[..i]) && Matches(b2, s[i..]);
      assert Matches(b1, s[i..]);
    }
  }

  lemma CatCong(a1: Re, a2: Re, b1: Re, b2: Re, s: seq<char>)
    requires forall t :: Matches(a1, t) <==> Matches(a2, t)
    requires forall t :: Matches(b1, t) <==> Matches(b2, t)
    ensures Matches(Cat(a1, b1), s) <==> Matches(Cat(a2, b2), s)
  {
    if Matches(Cat(a1, b1), s) {
      var i :| 0 <= i <= |s| && Matches(a1, s[..i]) && Matches(b1, s[i..]);
      assert Matches(a2, s[..i]) && Matches(b2, s[i..]);
    }
    if Matches(Cat(a2, b2), s) {
      var i :| 0 <= i <= |s| && Matches(a2, s[..i]) && Matches(b2, s[i..]);
      assert Matches(a1, s[..i]) && Matches(b1, s[i..]);
    }
  }

  function Norm(r: Re): NormRe
    decreases r
  {
    match r
    case Empty => Empty
    case Eps => Eps
    case Chr(c) => Chr(c)
    case Alt(a, b) => MkAlt(Norm(a), Norm(b))
    case Cat(a, b) => MkCat(Norm(a), Norm(b))
    case Star(a) => MkStar(Norm(a))
  }

  lemma NormCorrect(r: Re, s: seq<char>)
    ensures Matches(Norm(r), s) <==> Matches(r, s)
    decreases r
  {
    // @hole-begin A4.NormCorrect
    match r
    case Empty =>
    case Eps =>
    case Chr(_) =>
    case Alt(a, b) =>
      MkAltCorrect(Norm(a), Norm(b), s);
      NormCorrect(a, s);
      NormCorrect(b, s);
    case Cat(a, b) =>
      MkCatCorrect(Norm(a), Norm(b), s);
      forall t ensures Matches(Norm(a), t) <==> Matches(a, t) { NormCorrect(a, t); }
      forall t ensures Matches(Norm(b), t) <==> Matches(b, t) { NormCorrect(b, t); }
      CatCong(Norm(a), a, Norm(b), b, s);
    case Star(a) =>
      MkStarCorrect(Norm(a), s);
      forall t ensures Matches(Norm(a), t) <==> Matches(a, t) { NormCorrect(a, t); }
      StarCong(Norm(a), a, s);
    // @hole-end A4.NormCorrect
  }

  // The derivative built from smart constructors stays normal.
  function NDeriv(r: NormRe, c: char): NormRe
    decreases r
  {
    match r
    case Empty => Empty
    case Eps => Empty
    case Chr(d) => if c == d then Eps else Empty
    case Alt(a, b) => MkAlt(NDeriv(a, c), NDeriv(b, c))
    case Cat(a, b) =>
      if Nullable(a) then MkAlt(MkCat(NDeriv(a, c), b), NDeriv(b, c)) else MkCat(NDeriv(a, c), b)
    case Star(a) => MkCat(NDeriv(a, c), r)
  }

  lemma NDerivCorrect(r: NormRe, c: char, s: seq<char>)
    ensures Matches(NDeriv(r, c), s) <==> Matches(Deriv(r, c), s)
    decreases r
  {
    // @hole-begin A4.NDerivCorrect
    match r
    case Empty =>
    case Eps =>
    case Chr(_) =>
    case Alt(a, b) =>
      MkAltCorrect(NDeriv(a, c), NDeriv(b, c), s);
      NDerivCorrect(a, c, s);
      NDerivCorrect(b, c, s);
    case Cat(a, b) =>
      forall t ensures Matches(NDeriv(a, c), t) <==> Matches(Deriv(a, c), t) { NDerivCorrect(a, c, t); }
      forall t ensures Matches(NDeriv(b, c), t) <==> Matches(Deriv(b, c), t) { NDerivCorrect(b, c, t); }
      MkCatCorrect(NDeriv(a, c), b, s);
      CatCong(NDeriv(a, c), Deriv(a, c), b, b, s);
      if Nullable(a) {
        MkAltCorrect(MkCat(NDeriv(a, c), b), NDeriv(b, c), s);
      }
    case Star(a) =>
      forall t ensures Matches(NDeriv(a, c), t) <==> Matches(Deriv(a, c), t) { NDerivCorrect(a, c, t); }
      MkCatCorrect(NDeriv(a, c), r, s);
      CatCong(NDeriv(a, c), Deriv(a, c), r, r, s);
    // @hole-end A4.NDerivCorrect
  }

  // ---------------------------------------------------------------------------
  // Derivations and the certifying matcher (R11)
  // ---------------------------------------------------------------------------

  datatype Derivation =
    | DEps
    | DChr
    | DAltL(d: Derivation)
    | DAltR(d: Derivation)
    | DCat(k: nat, d1: Derivation, d2: Derivation)
    | DStarNil
    | DStarCons(k: nat, d1: Derivation, d2: Derivation)

  // The executable checker: does d derive s from r?
  predicate CheckDeriv(r: Re, s: seq<char>, d: Derivation)
    decreases d
  {
    match d
    case DEps => r == Eps && s == []
    case DChr => r.Chr? && s == [r.c]
    case DAltL(d1) => r.Alt? && CheckDeriv(r.a, s, d1)
    case DAltR(d1) => r.Alt? && CheckDeriv(r.b, s, d1)
    case DCat(k, d1, d2) =>
      r.Cat? && k <= |s| && CheckDeriv(r.a, s[..k], d1) && CheckDeriv(r.b, s[k..], d2)
    case DStarNil => r.Star? && s == []
    case DStarCons(k, d1, d2) =>
      r.Star? && 0 < k <= |s| && CheckDeriv(r.r, s[..k], d1) && CheckDeriv(r, s[k..], d2)
  }

  lemma CheckSound(r: Re, s: seq<char>, d: Derivation)
    requires CheckDeriv(r, s, d)
    ensures Matches(r, s)
    decreases d
  {
    // @hole-begin A4.CheckSound
    match d
    case DEps =>
    case DChr =>
    case DAltL(d1) =>
      CheckSound(r.a, s, d1);
    case DAltR(d1) =>
      CheckSound(r.b, s, d1);
    case DCat(k, d1, d2) =>
      CheckSound(r.a, s[..k], d1);
      CheckSound(r.b, s[k..], d2);
    case DStarNil =>
    case DStarCons(k, d1, d2) =>
      CheckSound(r.r, s[..k], d1);
      CheckSound(r, s[k..], d2);
    // @hole-end A4.CheckSound
  }

  datatype Option<T> = None | Some(value: T)

  // An exhaustive search that returns a derivation (the untrusted producer).
  function FindDeriv(r: Re, s: seq<char>): (res: Option<Derivation>)
    ensures res.Some? ==> CheckDeriv(r, s, res.value)
    ensures res.None? ==> !Matches(r, s)
    decreases r, |s|
  {
    // @impl-begin A4.FindDeriv trivial=None
    match r
    case Empty => None
    case Eps => if s == [] then Some(DEps) else None
    case Chr(c) => if s == [c] then Some(DChr) else None
    case Alt(a, b) =>
      var x := FindDeriv(a, s);
      if x.Some? then Some(DAltL(x.value))
      else
        var y := FindDeriv(b, s);
        if y.Some? then Some(DAltR(y.value)) else None
    case Cat(a, b) => FindCat(a, b, s, 0)
    case Star(a) => if s == [] then Some(DStarNil) else FindStar(a, s, 1)
    // @impl-end A4.FindDeriv
  }

  // Try the splits k, k+1, ..., |s| of a Cat.
  function FindCat(a: Re, b: Re, s: seq<char>, k: nat): (res: Option<Derivation>)
    requires k <= |s| + 1
    requires forall i | 0 <= i < k && i <= |s| :: !(Matches(a, s[..i]) && Matches(b, s[i..]))
    ensures res.Some? ==> CheckDeriv(Cat(a, b), s, res.value)
    ensures res.None? ==> !Matches(Cat(a, b), s)
    decreases Cat(a, b), |s|, |s| + 1 - k
  {
    // @impl-begin A4.FindCat trivial=None
    if k > |s| then None
    else
      var x := FindDeriv(a, s[..k]);
      var y := if x.Some? then FindDeriv(b, s[k..]) else None;
      if x.Some? && y.Some? then Some(DCat(k, x.value, y.value))
      else FindCat(a, b, s, k + 1)
    // @impl-end A4.FindCat
  }

  // Try the first-chunk lengths k, k+1, ..., |s| of a Star.
  function FindStar(a: Re, s: seq<char>, k: nat): (res: Option<Derivation>)
    requires 1 <= k <= |s| + 1
    requires forall i | 0 < i < k && i <= |s| :: !(Matches(a, s[..i]) && Matches(Star(a), s[i..]))
    ensures res.Some? ==> CheckDeriv(Star(a), s, res.value)
    ensures res.None? ==> !Matches(Star(a), s) || s == []
    decreases Star(a), |s|, |s| + 1 - k
  {
    // @impl-begin A4.FindStar trivial=None
    if k > |s| then None
    else
      var x := FindDeriv(a, s[..k]);
      var y := if x.Some? then FindDeriv(Star(a), s[k..]) else None;
      if x.Some? && y.Some? then Some(DStarCons(k, x.value, y.value))
      else FindStar(a, s, k + 1)
    // @impl-end A4.FindStar
  }

  // Completeness of derivations: every match has one.
  lemma CheckComplete(r: Re, s: seq<char>)
    requires Matches(r, s)
    ensures exists d :: CheckDeriv(r, s, d)
  {
    // @hole-begin A4.CheckComplete
    var x := FindDeriv(r, s);
    assert CheckDeriv(r, s, x.value);
    // @hole-end A4.CheckComplete
  }

  // Completeness without the search: a derivation built by induction.
  lemma CheckCompleteDirect(r: Re, s: seq<char>) returns (d: Derivation)
    requires Matches(r, s)
    ensures CheckDeriv(r, s, d)
    decreases r, |s|
  {
    // @hole-begin A4.CheckCompleteDirect
    match r
    case Eps =>
      d := DEps;
    case Chr(_) =>
      d := DChr;
    case Alt(a, b) =>
      if Matches(a, s) {
        var d1 := CheckCompleteDirect(a, s);
        d := DAltL(d1);
      } else {
        var d1 := CheckCompleteDirect(b, s);
        d := DAltR(d1);
      }
    case Cat(a, b) =>
      var k :| 0 <= k <= |s| && Matches(a, s[..k]) && Matches(b, s[k..]);
      var d1 := CheckCompleteDirect(a, s[..k]);
      var d2 := CheckCompleteDirect(b, s[k..]);
      d := DCat(k, d1, d2);
    case Star(a) =>
      if s == [] {
        d := DStarNil;
      } else {
        var k :| 0 < k <= |s| && Matches(a, s[..k]) && Matches(Star(a), s[k..]);
        var d1 := CheckCompleteDirect(a, s[..k]);
        var d2 := CheckCompleteDirect(r, s[k..]);
        d := DStarCons(k, d1, d2);
      }
    // @hole-end A4.CheckCompleteDirect
  }

  // The certifying matcher: the derivative matcher decides, the search
  // produces a witness, and only the verified checker is trusted.
  method CertMatch(r: Re, s: seq<char>) returns (b: bool, w: Option<Derivation>)
    ensures b == Matches(r, s)
    ensures b ==> w.Some? && CheckDeriv(r, s, w.value)
  {
    b := DerivMatch(r, s);
    if b {
      w := FindDeriv(r, s);
    } else {
      w := None;
    }
  }
}
