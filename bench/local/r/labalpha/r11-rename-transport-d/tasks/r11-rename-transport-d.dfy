// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"h1","identifiers":["RenameWordR11","RenameCharR11","r","c","s","from","to"]},{"name":"c1","identifiers":["r","a","s","child","from","to"],"kind":"calls","callees":["RenameTransportR11"]},{"name":"c2","identifiers":["r","b","s","child","from","to"],"kind":"calls","callees":["RenameTransportR11"]},{"name":"c3","identifiers":["r","a","b","s","k","left","right","from","to"],"kind":"calls","callees":["RenameSplitR11","RenameTransportR11"]},{"name":"c4","identifiers":["r","s","k","left","right","from","to"],"kind":"calls","callees":["RenameSplitR11","RenameTransportR11"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.RenameTransportR11","start":66,"end":84}]
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

  // Provided definitions (R11 agent file), copied verbatim; qualified layer names read locally.
  ghost function RenameCharR11(c:char,from:char,to:char):char {if c==from then to else c}
  ghost function RenameWordR11(s:seq<char>,from:char,to:char):seq<char> {seq(|s|,i requires 0<=i<|s| =>RenameCharR11(s[i],from,to))}
  ghost function RenamePatternR11(r:Re,from:char,to:char):Re
   decreases r
  {
   match r
   case Empty=>Empty
   case Eps=>Eps
   case Chr(c)=>Chr(RenameCharR11(c,from,to))
   case Alt(a,b)=>Alt(RenamePatternR11(a,from,to),RenamePatternR11(b,from,to))
   case Cat(a,b)=>Cat(RenamePatternR11(a,from,to),RenamePatternR11(b,from,to))
   case Star(a)=>Star(RenamePatternR11(a,from,to))
  }
  ghost predicate RulesR11(r:Re,s:seq<char>,d:Derivation) {
   CheckDeriv(r,s,d)
  }

  // Provided fact (R11 agent RenameSplitR11), complete.
  lemma RenameSplitR11(s:seq<char>,k:nat,from:char,to:char)
   requires k<=|s|
   ensures |RenameWordR11(s,from,to)|==|s|
   ensures RenameWordR11(s,from,to)[..k]==RenameWordR11(s[..k],from,to)
   ensures RenameWordR11(s,from,to)[k..]==RenameWordR11(s[k..],from,to)
  {
   assert RenameWordR11(s,from,to)[..k]==RenameWordR11(s[..k],from,to);
   assert RenameWordR11(s,from,to)[k..]==RenameWordR11(s[k..],from,to);
  }

  // The task (R11.A1 RenameTransportR11): renaming a character transports a certificate.
  lemma {:induction false} RenameTransportR11(r:Re,s:seq<char>,d:Derivation,from:char,to:char)
   requires RulesR11(r,s,d)
   ensures RulesR11(RenamePatternR11(r,from,to),RenameWordR11(s,from,to),d)
   decreases d
  {
   match d
   case DEps=>
   case DChr=>
     assert /*R12_HINT:h1*/ true;
   case DAltL(child)=>
     /*R12_CALLS:c1*/
   case DAltR(child)=>
     /*R12_CALLS:c2*/
   case DCat(k,left,right)=>
     /*R12_CALLS:c3*/
   case DStarNil=>
   case DStarCons(k,left,right)=>
     /*R12_CALLS:c4*/
  }
}
