// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["NormalFixedR10"]},{"name":"c2","kind":"calls","callees":["NormalFixedR10"]},{"name":"c3","kind":"calls","callees":["NormalFixedR10"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.NormalFixedR10","start":55,"end":67}]
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

  // The task (R10.H3 NormalFixedR10): a normal regex is a fixed point of Norm.
  lemma {:induction false} NormalFixedR10(r: NormRe)
    ensures Norm(r) == r
    decreases r
  {
    match r
    case Alt(a, b) =>
      /*R12_CALLS:c1*/
    case Cat(a, b) =>
      /*R12_CALLS:c2*/
    case Star(a) =>
      /*R12_CALLS:c3*/
    case _ =>
  }
}
