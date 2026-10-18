// R12_HINT_SITES: [{"name":"h1","identifiers":["u","v"]},{"name":"h2","identifiers":["u","v"]},{"name":"c1","identifiers":["Deriv","r","u","v"],"kind":"calls","callees":["DerivsAppend"]},{"name":"h3","identifiers":["u","v"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.DerivsAppend","start":39,"end":50}]
module R12_LabCase {
  // Provided definitions: RG_A1_Re (layer A1) (Re, Nullable) and R06's given Deriv, Derivs, copied verbatim.
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

  // R06's given word derivative (R06 checkpoint, not a task).
  function Derivs(r: Re,s: seq<char>): Re
    decreases |s|
  { if |s| == 0 then r else Derivs(Deriv(r,s[0]),s[1..]) }

  // The task.
  lemma {:induction false} DerivsAppend(r: Re,u: seq<char>,v: seq<char>)
    ensures Derivs(r,u+v) == Derivs(Derivs(r,u),v)
    decreases |u|
  {
    if |u| > 0 {
      assert /*R12_HINT:h1*/ true;
      assert /*R12_HINT:h2*/ true;
      /*R12_CALLS:c1*/
    } else {
      assert /*R12_HINT:h3*/ true;
    }
  }
}
