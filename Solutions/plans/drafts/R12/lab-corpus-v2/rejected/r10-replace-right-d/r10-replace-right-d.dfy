// R12_HINT_SITES: [{"name":"h1","identifiers":["Matches","b2","s","i"]},{"name":"h2","identifiers":["Matches","b1","s","i"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.ReplaceRightR10","start":21,"end":33}]
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

  // The task (R10.W3 ReplaceRightR10): replace an equivalent right factor. The reference calls
  // RG_A4_Norm.CatCongRight, whose statement is this one; its proof is the skeleton here.
  lemma ReplaceRightR10(a:Re,b1:Re,b2:Re,s:seq<char>)
    requires forall t :: Matches(b1,t)<==>Matches(b2,t)
    ensures Matches(Cat(a,b1),s)<==>Matches(Cat(a,b2),s)
  {
    if Matches(Cat(a, b1), s) {
      var i :| 0 <= i <= |s| && Matches(a, s[..i]) && Matches(b1, s[i..]);
      assert /*R12_HINT:h1*/ true;
    }
    if Matches(Cat(a, b2), s) {
      var i :| 0 <= i <= |s| && Matches(a, s[..i]) && Matches(b2, s[i..]);
      assert /*R12_HINT:h2*/ true;
    }
  }
}
