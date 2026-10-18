// R12_HINT_SITES: [{"name":"h1","identifiers":["w","s"]},{"name":"h2","identifiers":["w","c"]},{"name":"h3","identifiers":["w","c"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.DerivBase","start":46,"end":60}]
module R12_LabCase {
  // Provided definitions: RG_A1_Re (layer A1) (Re, Matches, Nullable) and R06's given Deriv, copied verbatim.
  datatype Re = Empty | Eps | Chr(c: char) | Alt(a: Re, b: Re) | Cat(a: Re, b: Re) | Star(r: Re)

  ghost predicate Matches(r: Re, s: seq<char>)
    decreases r, |s|
  {
    match r
    case Empty => false
    case Eps => s == []
    case Chr(c) => s == [c]
    case Alt(a, b) => Matches(a, s) || Matches(b, s)
    case Cat(a, b) => exists i | 0 <= i <= |s| :: Matches(a, s[..i]) && Matches(b, s[i..])
    case Star(a) => s == [] || exists i | 0 < i <= |s| :: Matches(a, s[..i]) && Matches(Star(a), s[i..])
  }

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

  // R06's given one-character derivative (not a task).
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

  // The task.
  lemma DerivBase(r: Re,c: char,s: seq<char>)
    requires r.Empty? || r.Eps? || r.Chr?
    ensures Matches(Deriv(r,c),s) <==> Matches(r,[c]+s)
  {
    if r.Chr? {
      var w := [c]+s;
      if w == [r.c] {
        assert /*R12_HINT:h1*/ true;
        assert /*R12_HINT:h2*/ true;
      }
      if s == [] {
        assert /*R12_HINT:h3*/ true;
      }
    }
  }
}
