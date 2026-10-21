// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["CertificateLengthR11"]},{"name":"c2","kind":"calls","callees":["CertificateLengthR11"]},{"name":"c3","kind":"calls","callees":["CertificateLengthR11"]},{"name":"c4","kind":"calls","callees":["CertificateLengthR11"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.CertificateLengthR11","start":49,"end":64}]
module R12_LabCase {
  // Provided definitions: RG_A1_Re (layer A1), copied verbatim.
  datatype Re = Empty | Eps | Chr(c: char) | Alt(a: Re, b: Re) | Cat(a: Re, b: Re) | Star(r: Re)

  // Provided definitions: RG_A4_Norm (layer A4), copied verbatim.
  datatype Derivation =
    | DEps
    | DChr
    | DAltL(d: Derivation)
    | DAltR(d: Derivation)
    | DCat(k: nat, d1: Derivation, d2: Derivation)
    | DStarNil
    | DStarCons(k: nat, d1: Derivation, d2: Derivation)

  // The executable checker: does d derive s from r?
  ghost predicate CheckDeriv(r: Re, s: seq<char>, d: Derivation)
    decreases d
  {
    match d
    case DEps => r == Eps && s == []
    case DChr => r.Chr? && s == [r.c]
    case DAltL(d1) => r.Alt? && CheckDeriv(r.a, s, d1)
    case DAltR(d1) => r.Alt? && CheckDeriv(r.b, s, d1)
    case DCat(k, d1, d2) =>
      r.Cat? && k <= |s| && CheckDeriv(r.a, s[..k], d1) && CheckDeriv(r.b, s[k..], d2)
    case DStarNil => r.Star? && s == []
    case DStarCons(k, d1, d2) =>
      r.Star? && 0 < k <= |s| && CheckDeriv(r.r, s[..k], d1) && CheckDeriv(r, s[k..], d2)
  }

  // Provided definition (R11 checkpoint), copied verbatim.
  function CharacterLeavesR11(d:Derivation):nat decreases d {
   match d
   case DEps=>0
   case DChr=>1
   case DAltL(child)=>CharacterLeavesR11(child)
   case DAltR(child)=>CharacterLeavesR11(child)
   case DCat(_,left,right)=>CharacterLeavesR11(left)+CharacterLeavesR11(right)
   case DStarNil=>0
   case DStarCons(_,left,right)=>CharacterLeavesR11(left)+CharacterLeavesR11(right)
  }

  // The task (R11.X1 CertificateLengthR11): a certificate has one leaf per character.
  lemma {:induction false} CertificateLengthR11(r:Re,s:seq<char>,d:Derivation)
    requires CheckDeriv(r,s,d)
    ensures |s|==CharacterLeavesR11(d)
    decreases d
  {
    match d
    case DAltL(child)=>
      /*R12_CALLS:c1*/
    case DAltR(child)=>
      /*R12_CALLS:c2*/
    case DCat(k,left,right)=>
      /*R12_CALLS:c3*/
    case DStarCons(k,left,right)=>
      /*R12_CALLS:c4*/
    case _=>
  }
}
