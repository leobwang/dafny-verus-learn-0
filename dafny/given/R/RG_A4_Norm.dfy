/*! A4 normal-form definitions (PROVIDED, frozen). R10–R15. Do not open this file before
R02, R03, R05 and R06 are done: it imports A1b and A2, which re-supply their answers.
Shape is distinct from language preservation; no semantic smart-constructor, normalizer
or certificate-correctness answer is supplied. Certificate splits are word-relative.
*/
module RG_A4_Norm {
 import opened RG_A1_Re
 import opened RG_A1b_Facts
 import opened RG_A2_Deriv
 import opened RG_A3_Syntax
 ghost predicate EquivalentReR10(a:Re,b:Re) {forall s:seq<char> :: Matches(a,s) <==> Matches(b,s)}
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
  lemma StarOfEps(a: Re, s: seq<char>)
    requires forall t :: Matches(a, t) ==> t == []
    ensures Matches(Star(a), s) <==> s == []
  {
    if s != [] && Matches(Star(a), s) {
      var i :| 0 < i <= |s| && Matches(a, s[..i]) && Matches(Star(a), s[i..]);
      assert s[..i] != [] by { assert |s[..i]| == i; }
    }
  }
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
  ghost function Norm(r: Re): NormRe
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
  ghost function NDeriv(r: NormRe, c: char): NormRe
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
  datatype Derivation =
    | DEps
    | DChr
    | DAltL(d: Derivation)
    | DAltR(d: Derivation)
    | DCat(k: nat, d1: Derivation, d2: Derivation)
    | DStarNil
    | DStarCons(k: nat, d1: Derivation, d2: Derivation)

  // The executable checker: does d derive s from r?
  ghost predicate CheckDeriv(r: Re, s: seq<char>, d: Derivation)
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
}
