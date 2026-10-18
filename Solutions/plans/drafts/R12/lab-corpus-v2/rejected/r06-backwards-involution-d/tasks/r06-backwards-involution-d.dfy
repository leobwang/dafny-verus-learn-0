// R12_HINT_SITES: [{"name":"c1","identifiers":["a","b"],"kind":"calls","callees":["BackwardsInvolution"]},{"name":"c2","identifiers":["a","b"],"kind":"calls","callees":["BackwardsInvolution"]},{"name":"c3","identifiers":["a"],"kind":"calls","callees":["BackwardsInvolution"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.BackwardsInvolution","start":21,"end":35}]
module R12_LabCase {
  // Provided definitions: RG_A1_Re (layer A1) (Re, Backwards), copied verbatim.
  datatype Re = Empty | Eps | Chr(c: char) | Alt(a: Re, b: Re) | Cat(a: Re, b: Re) | Star(r: Re)

  // The regex read backwards.
  function Backwards(r: Re): Re
    decreases r
  {
    match r
    case Empty => Empty
    case Eps => Eps
    case Chr(c) => Chr(c)
    case Alt(a, b) => Alt(Backwards(a), Backwards(b))
    case Cat(a, b) => Cat(Backwards(b), Backwards(a))
    case Star(a) => Star(Backwards(a))
  }

  // The task.
  lemma BackwardsInvolution(r: Re)
    ensures Backwards(Backwards(r)) == r
    decreases r
  {
    match r
    case Empty =>
    case Eps =>
    case Chr(_) =>
    case Alt(a, b) =>
      /*R12_CALLS:c1*/
    case Cat(a, b) =>
      /*R12_CALLS:c2*/
    case Star(a) =>
      /*R12_CALLS:c3*/
  }
}
