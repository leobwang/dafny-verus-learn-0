// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","identifiers":["a","b","w"],"kind":"calls","callees":["PartsLaw"]},{"name":"h1","identifiers":["pa","pb","i"]},{"name":"h2","identifiers":["pa","pb","i"]},{"name":"h3","identifiers":["Matches","pa","i","w"]},{"name":"h4","identifiers":["Matches","pb","pa","i","w"]},{"name":"h5","identifiers":["Parts","r"]},{"name":"h6","identifiers":["Matches","Parts","r","w"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.PartsLaw","start":52,"end":81}]
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


  // Provided definitions (R08_AltSetEngine, given), copied verbatim.
  // Given: split the top-level Alt nodes, drop the literal Empty parts.
  function Parts(r: Re): seq<Re>
  {
    match r
    case Empty => []
    case Alt(a, b) => Parts(a) + Parts(b)
    case _ => [r]
  }

  // Given: some alternative of the list matches w.
  ghost predicate AnyMatches(st: seq<Re>, w: seq<char>)
  {
    exists i | 0 <= i < |st| :: Matches(st[i], w)
  }

  // The task (R08.H2 PartsLaw): splitting a pattern into its parts keeps its language.
  lemma {:induction false} PartsLaw(r: Re, w: seq<char>)
    ensures AnyMatches(Parts(r), w) <==> Matches(r, w)
  {
    match r
    case Empty =>
    case Alt(a, b) =>
      /*R12_CALLS:c1*/
      var pa, pb := Parts(a), Parts(b);
      if Matches(a, w) {
        var i :| 0 <= i < |pa| && Matches(pa[i], w);
        assert /*R12_HINT:h1*/ true;
      }
      if Matches(b, w) {
        var i :| 0 <= i < |pb| && Matches(pb[i], w);
        assert /*R12_HINT:h2*/ true;
      }
      if AnyMatches(pa + pb, w) {
        var i :| 0 <= i < |pa + pb| && Matches((pa + pb)[i], w);
        if i < |pa| {
          assert /*R12_HINT:h3*/ true;
        } else {
          assert /*R12_HINT:h4*/ true;
        }
      }
    case _ =>
      assert /*R12_HINT:h5*/ true;
      if Matches(r, w) {
        assert /*R12_HINT:h6*/ true;
      }
  }
}
