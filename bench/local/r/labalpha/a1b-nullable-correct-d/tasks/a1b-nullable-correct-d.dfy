// R12_HINT_SITES: [{"name":"c1","identifiers":["a","b"],"kind":"calls","callees":["NullableCorrect"]},{"name":"c2","identifiers":["a","b"],"kind":"calls","callees":["NullableCorrect"]},{"name":"h1","identifiers":["e"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.NullableCorrect","start":32,"end":47}]
module R12_LabCase {
  // Provided definitions: RG_A1_Re (layer A1: Re, Matches, Nullable), copied verbatim.
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

  // The task.
  lemma NullableCorrect(r: Re)
    ensures Nullable(r) <==> Matches(r, [])
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
      var e: seq<char> := [];
      assert /*R12_HINT:h1*/ true;
    case Star(_) =>
  }
}
