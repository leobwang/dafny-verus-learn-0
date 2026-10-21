// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["CheckSoundR11"]},{"name":"c2","kind":"calls","callees":["CheckSoundR11"]},{"name":"c3","kind":"calls","callees":["CheckSoundR11"]},{"name":"c4","kind":"calls","callees":["CheckSoundR11"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.CheckSoundR11","start":49,"end":66}]
module R12_LabCase {
  // Provided definitions: RG_A1_Re (layer A1), copied verbatim.
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

  // The task (R11.H2 CheckSoundR11): an accepted certificate proves the match.
  lemma {:induction false} CheckSoundR11(r: Re, s: seq<char>, d: Derivation)
    requires CheckDeriv(r, s, d)
    ensures Matches(r, s)
    decreases d
  {
    match d
    case DEps =>
    case DChr =>
    case DAltL(d1) =>
      /*R12_CALLS:c1*/
    case DAltR(d1) =>
      /*R12_CALLS:c2*/
    case DCat(k, d1, d2) =>
      /*R12_CALLS:c3*/
    case DStarNil =>
    case DStarCons(k, d1, d2) =>
      /*R12_CALLS:c4*/
  }
}
