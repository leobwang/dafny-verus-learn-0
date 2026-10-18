// R12_HINT_SITES: [{"name":"c1","identifiers":["Norm","r"],"kind":"calls","callees":["NormalFixedR10"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.NormIdempotentR10","start":64,"end":68}]
module R12_LabCase {
  // Provided definitions: RG_A1_Re (layer A1) and RG_A4_Norm (layer A4), copied verbatim.
  datatype Re = Empty | Eps | Chr(c: char) | Alt(a: Re, b: Re) | Cat(a: Re, b: Re) | Star(r: Re)

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

  // Provided fact (R10.H3 NormalFixedR10, reference proof), complete.
  lemma {:induction false} NormalFixedR10(r: NormRe)
    ensures Norm(r) == r
    decreases r
  {
    match r
    case Alt(a, b) => NormalFixedR10(a); NormalFixedR10(b);
    case Cat(a, b) => NormalFixedR10(a); NormalFixedR10(b);
    case Star(a) => NormalFixedR10(a);
    case _ =>
  }

  // The task (R10 NormIdempotentR10): normalization is idempotent.
  lemma {:induction false} NormIdempotentR10(r: Re)
    ensures Norm(Norm(r)) == Norm(r)
  {
    /*R12_CALLS:c1*/
  }
}
