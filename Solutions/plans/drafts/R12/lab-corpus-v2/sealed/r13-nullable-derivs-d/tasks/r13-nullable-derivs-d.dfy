// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["NullableCorrect"]},{"name":"c2","kind":"calls","callees":["NullableDerivsR13","DerivCorrect"]},{"name":"h1"}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.NullableDerivsR13","start":131,"end":141}]
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

  // Provided definition (R13_Repairs.Derivs, given), copied verbatim.
  // Given: the derivative by every character of u, in order.
  function Derivs(r: Re, u: seq<char>): Re
    decreases |u|
  {
    if u == [] then r else Derivs(Deriv(r, u[0]), u[1..])
  }

  // The task (R13.H3 NullableDerivsR13): a word matches exactly when its derivatives end in a nullable regex.
  lemma {:induction false} NullableDerivsR13(r: Re, u: seq<char>)
    ensures Nullable(Derivs(r, u)) <==> Matches(r, u)
    decreases |u|
  {
    if u == [] {
      /*R12_CALLS:c1*/
    } else {
      /*R12_CALLS:c2*/
      assert /*R12_HINT:h1*/ true;
    }
  }
}
