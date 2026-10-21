// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["DerivCorrect"]},{"name":"c2","kind":"calls","callees":["NullableFact","DerivCorrect"]},{"name":"h1"},{"name":"h2"},{"name":"h3"},{"name":"c3","kind":"calls","callees":["DerivCorrect"]},{"name":"h4"},{"name":"c4","kind":"calls","callees":["DerivCorrect"]},{"name":"h5"},{"name":"h6"},{"name":"h7"},{"name":"h8"},{"name":"h9"},{"name":"h10"},{"name":"c5","kind":"calls","callees":["DerivCorrect"]},{"name":"c6","kind":"calls","callees":["DerivCorrect"]},{"name":"h11"},{"name":"h12"}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.DerivCorrect","start":71,"end":123}]
module R12_LabCase {
  // Provided definitions: RG_A1_Re (layer A1) (Re, Matches, Nullable) and R06's given Deriv, copied verbatim.
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

  // R06's given one-character derivative (not a task).
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

  // Provided facts, complete (not tasks).

  // RG_A1b_Facts.NullableCorrect, complete (renamed NullableFact).
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

  // The task.
  lemma {:induction false} DerivCorrect(r: Re,c: char,s: seq<char>)
    ensures Matches(Deriv(r,c),s) <==> Matches(r,[c]+s)
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
      /*R12_CALLS:c1*/
    case Cat(a, b) =>
      /*R12_CALLS:c2*/
      if Matches(r, w) {
        var i :| 0 <= i <= |w| && Matches(a, w[..i]) && Matches(b, w[i..]);
        if i == 0 {
          assert /*R12_HINT:h1*/ true;
        } else {
          assert /*R12_HINT:h2*/ true;
          assert /*R12_HINT:h3*/ true;
          /*R12_CALLS:c3*/
          assert /*R12_HINT:h4*/ true;
        }
      }
      if Matches(Deriv(r, c), s) {
        if Matches(Cat(Deriv(a, c), b), s) {
          var j :| 0 <= j <= |s| && Matches(Deriv(a, c), s[..j]) && Matches(b, s[j..]);
          /*R12_CALLS:c4*/
          assert /*R12_HINT:h5*/ true;
          assert /*R12_HINT:h6*/ true;
        } else {
          assert /*R12_HINT:h7*/ true;
          assert /*R12_HINT:h8*/ true;
        }
      }
    case Star(a) =>
      if Matches(r, w) {
        var i :| 0 < i <= |w| && Matches(a, w[..i]) && Matches(Star(a), w[i..]);
        assert /*R12_HINT:h9*/ true;
        assert /*R12_HINT:h10*/ true;
        /*R12_CALLS:c5*/
      }
      if Matches(Deriv(r, c), s) {
        var j :| 0 <= j <= |s| && Matches(Deriv(a, c), s[..j]) && Matches(Star(a), s[j..]);
        /*R12_CALLS:c6*/
        assert /*R12_HINT:h11*/ true;
        assert /*R12_HINT:h12*/ true;
      }
  }
}
