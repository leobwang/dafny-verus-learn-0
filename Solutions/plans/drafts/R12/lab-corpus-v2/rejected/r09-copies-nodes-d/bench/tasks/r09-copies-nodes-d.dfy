// R12_HINT_SITES: [{"name":"c1","identifiers":["r","k"],"kind":"calls","callees":["CopiesNodesR09"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.CopiesNodesR09","start":34,"end":41}]
module R12_LabCase {
  // Provided definitions: RG_A1_Re (layer A1), copied verbatim.
  datatype Re = Empty | Eps | Chr(c: char) | Alt(a: Re, b: Re) | Cat(a: Re, b: Re) | Star(r: Re)

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

  // Provided definitions: RG_A3_Syntax (layer A3), counted repetition, copied verbatim.
  function Copies(r: Re, k: nat): Re
    decreases r, k
  {
    if k == 0 then Eps else Cat(r, Copies(r, k - 1))
  }

  // Zero to j more copies.
  function CopiesUpTo(r: Re, j: nat): Re
    decreases r, j
  {
    if j == 0 then Eps else Alt(Eps, Cat(r, CopiesUpTo(r, j - 1)))
  }

  // The task (R09 CopiesNodesR09): the node count of Copies(r, k).
  lemma CopiesNodesR09(r: Re, k: nat)
    ensures NodeCount(Copies(r, k)) == 1 + k * (NodeCount(r) + 1)
    decreases k
  {
    if k > 0 {
      /*R12_CALLS:c1*/
    }
  }
}
