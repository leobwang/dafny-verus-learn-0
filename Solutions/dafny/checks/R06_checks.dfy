/*! R06 — Reference Solution. Given-only value prediction enabled. */
module R06_Checks {
  import opened RG_A1_Re
  import opened RG_A1b_Facts
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
  // item: R06.P1d value
  // Answer form: constructors (A1 term, no spaces).
  @Test method DerivShapeR06() {
    var pattern := Cat(Star(Chr('a')),Chr('b'));
    expect Deriv(pattern,'a') == Alt(Cat(Cat(Eps,Star(Chr('a'))),Chr('b')),Empty);
  }
}
