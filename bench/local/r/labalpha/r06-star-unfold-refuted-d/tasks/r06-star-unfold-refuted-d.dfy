// R12_HINT_SITES: [{"name":"h1","identifiers":["Matches","Star","a","s"]},{"name":"h2","identifiers":["Matches","Cat","Star","a","s"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.StarUnfoldRefuted","start":20,"end":26}]
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

  // The task.
  lemma StarUnfoldRefuted()
    ensures exists a: Re,s: seq<char> :: Matches(Star(a),s) && !Matches(Cat(a,Star(a)),s)
  {
    var a := Chr('x'); var s: seq<char> := [];
    assert /*R12_HINT:h1*/ true;
    assert /*R12_HINT:h2*/ true;
  }
}
