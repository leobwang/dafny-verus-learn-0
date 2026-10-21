// R12_HINT_SITES: [{"name":"c1","identifiers":["c","n"],"kind":"calls","callees":["StarPowV"]},{"name":"h1","identifiers":["s","c","PowerWord","n"]},{"name":"h2","identifiers":["MatchesV","Chr","c","s"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.StarPowV","start":65,"end":74}]
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

  // The task (R14 H2 StarPowV): every power of c matches Star(Chr(c)).
  lemma {:induction false} StarPowV(c: char, n: nat)
    ensures MatchesV(Star(Chr(c)), PowerWord(c, n))
  {
    if n > 0 {
      /*R12_CALLS:c1*/
      var s := PowerWord(c, n);
      assert /*R12_HINT:h1*/ true;
      assert /*R12_HINT:h2*/ true;
    }
  }
}
