// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["NullableCorrect"]},{"name":"h1"}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.ResidualObserveR11","start":60,"end":67}]
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

  // Provided fact (RG_A1b_Facts.NullableCorrect), complete, copied verbatim.
  lemma NullableCorrect(r: Re)
    ensures Nullable(r) <==> Matches(r, [])
    decreases r
  {
    match r
    case Empty =>
    case Eps =>
    case Chr(_) =>
    case Alt(a, b) =>
      NullableCorrect(a);
      NullableCorrect(b);
    case Cat(a, b) =>
      NullableCorrect(a);
      NullableCorrect(b);
      var e: seq<char> := [];
      assert e[..0] == e && e[0..] == e;
    case Star(_) =>
  }

  // Provided definition (R11_Streaming.ResidualR11), copied verbatim.
  opaque ghost predicate ResidualR11(r:Re,current:Re,prefix:seq<char>) {
   forall tail:seq<char> :: Matches(current,tail)<==>Matches(r,prefix+tail)
  }

  // The task (R11 ResidualObserveR11): the residual's nullability reads acceptance of the prefix.
  lemma ResidualObserveR11(r:Re,current:Re,prefix:seq<char>)
   requires ResidualR11(r,current,prefix)
   ensures Nullable(current)==Matches(r,prefix)
  {
   reveal ResidualR11();
   /*R12_CALLS:c1*/
   assert /*R12_HINT:h1*/ true;
  }
}
