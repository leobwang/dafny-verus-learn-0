// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"h1"},{"name":"h2"},{"name":"h3"},{"name":"h4"}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.CatAssoc","start":23,"end":48}]
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
  lemma {:induction false} CatAssoc(a: Re, b: Re, c: Re, s: seq<char>)
    ensures Matches(Cat(Cat(a, b), c), s) <==> Matches(Cat(a, Cat(b, c)), s)
  {
    if Matches(Cat(Cat(a, b), c), s) {
      var i :| 0 <= i <= |s| && Matches(Cat(a, b), s[..i]) && Matches(c, s[i..]);
      var u := s[..i];
      var k :| 0 <= k <= |u| && Matches(a, u[..k]) && Matches(b, u[k..]);
      var v := s[k..];
      assert /*R12_HINT:h1*/ true;
      assert /*R12_HINT:h2*/ true;
      assert v[..i - k] == s[k..i];
      assert v[i - k..] == s[i..];
      assert Matches(Cat(b, c), v);
    }
    if Matches(Cat(a, Cat(b, c)), s) {
      var k :| 0 <= k <= |s| && Matches(a, s[..k]) && Matches(Cat(b, c), s[k..]);
      var v := s[k..];
      var j :| 0 <= j <= |v| && Matches(b, v[..j]) && Matches(c, v[j..]);
      var u := s[..k + j];
      assert /*R12_HINT:h3*/ true;
      assert /*R12_HINT:h4*/ true;
      assert v[..j] == s[k..k + j];
      assert v[j..] == s[k + j..];
      assert Matches(Cat(a, b), u);
    }
  }
}
