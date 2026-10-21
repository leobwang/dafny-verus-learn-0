// R12_HINT_SITES: [{"name":"c1","identifiers":["r","u","v","Star"],"kind":"calls","callees":["CatIntroV"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.BatteryCellR14","start":75,"end":81}]
module R12_LabCase {
  // Provided definitions: RG_A1_Re (layer A1: Re, Nullable, NodeCount) and RG_A2_Deriv (Deriv),
  // copied verbatim; MatchesV and PowerWord are R14's own (R14_Mechanics), verbatim.
  datatype Re = Empty | Eps | Chr(c: char) | Alt(a: Re, b: Re) | Cat(a: Re, b: Re) | Star(r: Re)

  predicate Nullable(r: Re)
    decreases r
  {
    match r
    case Empty => false
    case Eps => true
    case Chr(_) => false
    case Alt(a, b) => Nullable(a) || Nullable(b)
    case Cat(a, b) => Nullable(a) && Nullable(b)
    case Star(_) => true
  }

  function NodeCount(r: Re): nat
    decreases r
  {
    match r
    case Empty => 1
    case Eps => 1
    case Chr(_) => 1
    case Alt(a, b) => 1 + NodeCount(a) + NodeCount(b)
    case Cat(a, b) => 1 + NodeCount(a) + NodeCount(b)
    case Star(a) => 1 + NodeCount(a)
  }

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

  ghost predicate MatchesV(r: Re, s: seq<char>)
    decreases r, |s|
  {
    match r
    case Empty => false
    case Eps => s == []
    case Chr(c) => s == [c]
    case Alt(a, b) => MatchesV(a, s) || MatchesV(b, s)
    case Cat(a, b) =>
      exists i {:trigger MatchesV(a, s[..i])} | 0 <= i <= |s| :: MatchesV(a, s[..i]) && MatchesV(b, s[i..])
    case Star(a) =>
      s == [] || exists i {:trigger MatchesV(a, s[..i])} | 0 < i <= |s| :: MatchesV(a, s[..i]) && MatchesV(Star(a), s[i..])
  }

  function PowerWord(c: char, n: nat): seq<char>
  {
    if n == 0 then [] else [c] + PowerWord(c, n - 1)
  }

  // Provided fact (R14 H1 CatIntroV), complete.
  lemma CatIntroV(a: Re, b: Re, u: seq<char>, v: seq<char>)
    requires MatchesV(a, u) && MatchesV(b, v)
    ensures MatchesV(Cat(a, b), u + v)
  {
    var s := u + v;
    assert s[..|u|] == u;
    assert s[|u|..] == v;
  }

  // The task (R14 battery cell loop-d): a matching-loop hypothesis is in context.
  lemma BatteryCellR14(r: Re, u: seq<char>, v: seq<char>)
    requires u != [] && MatchesV(r, u) && MatchesV(Star(r), v)
    requires forall s {:trigger MatchesV(Star(r), s)} :: MatchesV(Star(r), s) ==> MatchesV(Star(r), s + s)
    ensures MatchesV(Cat(r, Star(r)), u + v)
  {
    /*R12_CALLS:c1*/
  }
}
