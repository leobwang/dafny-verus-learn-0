// R12_HINT_SITES: [{"name":"c1","identifiers":["a","b","c","s"],"kind":"calls","callees":["DerivCorrect"]},{"name":"c2","identifiers":["a","b","c","s"],"kind":"calls","callees":["NullableFact","DerivCorrect"]},{"name":"h1","identifiers":["w"]},{"name":"h2","identifiers":["w","c","s","i"]},{"name":"h3","identifiers":["w","s","i"]},{"name":"c3","identifiers":["a","c","s","i"],"kind":"calls","callees":["DerivCorrect"]},{"name":"h4","identifiers":["Matches","Cat","Deriv","a","b","c","s"]},{"name":"c4","identifiers":["a","c","s","j"],"kind":"calls","callees":["DerivCorrect"]},{"name":"h5","identifiers":["w","c","s","j"]},{"name":"h6","identifiers":["w","s","j"]},{"name":"h7","identifiers":["Nullable","Matches","a","b","w"]},{"name":"h8","identifiers":["w"]},{"name":"h9","identifiers":["w","c","s","i"]},{"name":"h10","identifiers":["w","s","i"]},{"name":"c5","identifiers":["a","c","s","i"],"kind":"calls","callees":["DerivCorrect"]},{"name":"c6","identifiers":["a","c","s","j"],"kind":"calls","callees":["DerivCorrect"]},{"name":"h11","identifiers":["w","c","s","j"]},{"name":"h12","identifiers":["w","s","j"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.DerivCorrect","start":68,"end":120}]
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
