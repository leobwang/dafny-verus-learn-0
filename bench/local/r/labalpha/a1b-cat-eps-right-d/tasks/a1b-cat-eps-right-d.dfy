// R12_HINT_SITES: [{"name":"h1","identifiers":["s"]},{"name":"h2","identifiers":["s","i"]},{"name":"h3","identifiers":["s","i"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.CatEpsRight","start":20,"end":31}]
module R12_LabCase {
  // Provided definitions: RG_A1_Re (layer A1: Re, Matches), copied verbatim.
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

  // The task.
  lemma CatEpsRight(r: Re, s: seq<char>)
    ensures Matches(Cat(r, Eps), s) <==> Matches(r, s)
  {
    if Matches(r, s) {
      assert /*R12_HINT:h1*/ true;
    }
    if Matches(Cat(r, Eps), s) {
      var i :| 0 <= i <= |s| && Matches(r, s[..i]) && Matches(Eps, s[i..]);
      assert /*R12_HINT:h2*/ true;
      assert /*R12_HINT:h3*/ true;
    }
  }
}
