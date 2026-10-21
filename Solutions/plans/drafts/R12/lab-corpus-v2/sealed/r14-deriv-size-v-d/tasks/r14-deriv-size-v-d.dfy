// R12_HINT_SITES: [{"name":"c1","identifiers":["a","b","c","NodeCount"],"kind":"calls","callees":["DerivSizeV","SquareGrowth"]},{"name":"c2","identifiers":["a","b","c","NodeCount"],"kind":"calls","callees":["DerivSizeV","SquareGrowth"]},{"name":"c3","identifiers":["a","c","NodeCount"],"kind":"calls","callees":["DerivSizeV","SquareGrowth"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.DerivSizeV","start":75,"end":88}]
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

  // Provided fact (R14's SquareGrowth, the product inequality every case needs), complete.
  lemma SquareGrowth(x: nat, y: nat)
    ensures 2 + 2 * x * x + y + 2 * y * y <= 2 * (1 + x + y) * (1 + x + y)
    ensures 2 + 2 * x * x + x <= 2 * (1 + x) * (1 + x)
  {
    assert 2 * (1 + x + y) * (1 + x + y) == 2 + 4 * x + 4 * y + 2 * x * x + 4 * x * y + 2 * y * y;
    assert 2 * (1 + x) * (1 + x) == 2 + 4 * x + 2 * x * x;
    assert x * y >= 0;
  }

  // The task (R14 H3 DerivSizeV): a derivative is at most twice the square of its regex's size.
  lemma {:induction false} DerivSizeV(r: Re, c: char)
    ensures NodeCount(Deriv(r, c)) <= 2 * NodeCount(r) * NodeCount(r)
  {
    match r
    case Empty =>
    case Eps =>
    case Chr(d) =>
    case Alt(a, b) =>
      /*R12_CALLS:c1*/
    case Cat(a, b) =>
      /*R12_CALLS:c2*/
    case Star(a) =>
      /*R12_CALLS:c3*/
  }
}
