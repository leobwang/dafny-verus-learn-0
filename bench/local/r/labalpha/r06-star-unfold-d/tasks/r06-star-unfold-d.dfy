// R12_HINT_SITES: [{"name":"c1","identifiers":["a"],"kind":"calls","callees":["NullableFact"]},{"name":"h1","identifiers":["s"]},{"name":"h2","identifiers":["Matches","Cat","Star","a","s","i"]},{"name":"h3","identifiers":["s","i"]},{"name":"h4","identifiers":["Matches","Star","a","s","i"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.StarUnfold","start":52,"end":69}]
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

  // Provided fact (RG_A1b_Facts.NullableCorrect), complete.
  lemma NullableFact(r: Re)
    ensures Nullable(r) <==> Matches(r, [])
    decreases r
  {
    match r
    case Empty =>
    case Eps =>
    case Chr(_) =>
    case Alt(a, b) =>
      NullableFact(a);
      NullableFact(b);
    case Cat(a, b) =>
      NullableFact(a);
      NullableFact(b);
      var e: seq<char> := [];
      assert e[..0] == e && e[0..] == e;
    case Star(_) =>
  }

  // The task (R06.H4 StarUnfold): unfold a star once.
  lemma StarUnfold(a: Re, s: seq<char>)
    requires s != [] || Nullable(a)
    ensures Matches(Star(a), s) <==> Matches(Cat(a, Star(a)), s)
  {
    if s == [] {
      /*R12_CALLS:c1*/
      assert /*R12_HINT:h1*/ true;
    }
    if Matches(Star(a), s) && s != [] {
      var i :| 0 < i <= |s| && Matches(a, s[..i]) && Matches(Star(a), s[i..]);
      assert /*R12_HINT:h2*/ true;
    }
    if Matches(Cat(a, Star(a)), s) {
      var i :| 0 <= i <= |s| && Matches(a, s[..i]) && Matches(Star(a), s[i..]);
      if i == 0 { assert /*R12_HINT:h3*/ true; }
      else { assert /*R12_HINT:h4*/ true; }
    }
  }
}
