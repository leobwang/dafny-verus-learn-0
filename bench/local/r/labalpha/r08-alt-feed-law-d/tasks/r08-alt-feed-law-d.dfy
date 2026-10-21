// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","identifiers":["st","c","w","Deriv"],"kind":"calls","callees":["AltFeedLaw","PartsLaw","DerivCorrect"]},{"name":"h1","identifiers":["Matches","head","i","w"]},{"name":"h2","identifiers":["Matches","tail","head","i","w"]},{"name":"h3","identifiers":["Matches","st","j","c","w"]},{"name":"h4","identifiers":["head","tail","k"]},{"name":"h5","identifiers":["Matches","st","i","c","w"]},{"name":"h6","identifiers":["head","tail","k"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.AltFeedLaw","start":187,"end":217}]
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

  // Provided definition (RG_A2_Deriv.Deriv), copied verbatim.
  function Deriv(r: Re, c: char): Re
    decreases r
  {
    match r
    case Empty => Empty
    case Eps => Empty
    case Chr(d) => if c == d then Eps else Empty
    case Alt(a, b) => Alt(Deriv(a, c), Deriv(b, c))
    case Cat(a, b) =>
      if Nullable(a) then Alt(Cat(Deriv(a, c), b), Deriv(b, c)) else Cat(Deriv(a, c), b)
    case Star(a) => Cat(Deriv(a, c), Star(a))
  }

  // Provided fact (RG_A2_Deriv.DerivCorrect), complete, copied verbatim.
  lemma DerivCorrect(r: Re, c: char, s: seq<char>)
    ensures Matches(Deriv(r, c), s) <==> Matches(r, [c] + s)
    decreases r
  {
    var w := [c] + s;
    match r
    case Empty =>
    case Eps =>
    case Chr(d) =>
      assert w == [d] <==> (c == d && s == []) by {
        if w == [d] { assert w[1..] == s; assert w[0] == c; }
        if s == [] { assert w == [c]; }
      }
    case Alt(a, b) =>
      DerivCorrect(a, c, s);
      DerivCorrect(b, c, s);
    case Cat(a, b) =>
      NullableCorrect(a);
      DerivCorrect(b, c, s);
      if Matches(r, w) {
        var i :| 0 <= i <= |w| && Matches(a, w[..i]) && Matches(b, w[i..]);
        if i == 0 {
          assert w[..0] == [] && w[0..] == w;
        } else {
          assert w[..i] == [c] + s[..i - 1];
          assert w[i..] == s[i - 1..];
          DerivCorrect(a, c, s[..i - 1]);
          assert Matches(Cat(Deriv(a, c), b), s);
        }
      }
      if Matches(Deriv(r, c), s) {
        if Matches(Cat(Deriv(a, c), b), s) {
          var j :| 0 <= j <= |s| && Matches(Deriv(a, c), s[..j]) && Matches(b, s[j..]);
          DerivCorrect(a, c, s[..j]);
          assert w[..j + 1] == [c] + s[..j];
          assert w[j + 1..] == s[j..];
        } else {
          assert Nullable(a) && Matches(b, w);
          assert w[..0] == [] && w[0..] == w;
        }
      }
    case Star(a) =>
      if Matches(r, w) {
        var i :| 0 < i <= |w| && Matches(a, w[..i]) && Matches(Star(a), w[i..]);
        assert w[..i] == [c] + s[..i - 1];
        assert w[i..] == s[i - 1..];
        DerivCorrect(a, c, s[..i - 1]);
      }
      if Matches(Deriv(r, c), s) {
        var j :| 0 <= j <= |s| && Matches(Deriv(a, c), s[..j]) && Matches(Star(a), s[j..]);
        DerivCorrect(a, c, s[..j]);
        assert w[..j + 1] == [c] + s[..j];
        assert w[j + 1..] == s[j..];
      }
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

  // Given: the derivative of every alternative, split again.
  function FeedAll(st: seq<Re>, c: char): seq<Re>
  {
    if st == [] then [] else Parts(Deriv(st[0], c)) + FeedAll(st[1..], c)
  }

  // The engine's model, opaque: its existential stays out of every proof that does not reveal it.
  opaque ghost predicate AltRes(st: seq<Re>, w: seq<char>)
  {
    AnyMatches(st, w)
  }

  // Provided fact (R08.H2d PartsLaw), complete.
  lemma {:induction false} PartsLaw(r: Re, w: seq<char>)
    ensures AnyMatches(Parts(r), w) <==> Matches(r, w)
  {
    match r
    case Empty =>
    case Alt(a, b) =>
      PartsLaw(a, w);
      PartsLaw(b, w);
      var pa, pb := Parts(a), Parts(b);
      if Matches(a, w) {
        var i :| 0 <= i < |pa| && Matches(pa[i], w);
        assert (pa + pb)[i] == pa[i];
      }
      if Matches(b, w) {
        var i :| 0 <= i < |pb| && Matches(pb[i], w);
        assert (pa + pb)[|pa| + i] == pb[i];
      }
      if AnyMatches(pa + pb, w) {
        var i :| 0 <= i < |pa + pb| && Matches((pa + pb)[i], w);
        if i < |pa| {
          assert Matches(pa[i], w);
        } else {
          assert Matches(pb[i - |pa|], w);
        }
      }
    case _ =>
      assert Parts(r) == [r];
      if Matches(r, w) {
        assert Matches(Parts(r)[0], w);
      }
  }

  // The task (R08.H3 AltFeedLaw): the alternative-set engine's step law.
  lemma {:induction false} AltFeedLaw(st: seq<Re>, c: char, w: seq<char>)
    ensures AltRes(FeedAll(st, c), w) <==> AltRes(st, [c] + w)
    decreases |st|
  {
    reveal AltRes();
    if st != [] {
      var head, tail := Parts(Deriv(st[0], c)), FeedAll(st[1..], c);
      /*R12_CALLS:c1*/
      if AnyMatches(head + tail, w) {
        var i :| 0 <= i < |head + tail| && Matches((head + tail)[i], w);
        if i < |head| {
          assert /*R12_HINT:h1*/ true;
        } else {
          assert /*R12_HINT:h2*/ true;
          var j :| 0 <= j < |st[1..]| && Matches(st[1..][j], [c] + w);
          assert /*R12_HINT:h3*/ true;
        }
      }
      if AnyMatches(st, [c] + w) {
        var i :| 0 <= i < |st| && Matches(st[i], [c] + w);
        if i == 0 {
          var k :| 0 <= k < |head| && Matches(head[k], w);
          assert /*R12_HINT:h4*/ true;
        } else {
          assert /*R12_HINT:h5*/ true;
          var k :| 0 <= k < |tail| && Matches(tail[k], w);
          assert /*R12_HINT:h6*/ true;
        }
      }
    }
  }
}
