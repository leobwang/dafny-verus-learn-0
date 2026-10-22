// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["CatEpsLeft"]},{"name":"h1"},{"name":"h2"},{"name":"c2","kind":"calls","callees":["CatAssoc"]},{"name":"c3","kind":"calls","callees":["CopiesSplit"]},{"name":"c4","kind":"calls","callees":["CatCongRight"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.CopiesSplit","start":89,"end":105}]
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

  // Provided definitions: RG_A3_Syntax (layer A3), counted repetition, copied verbatim.
  function Copies(r: Re, k: nat): Re
    decreases r, k
  {
    if k == 0 then Eps else Cat(r, Copies(r, k - 1))
  }

  // Zero to j more copies.
  function CopiesUpTo(r: Re, j: nat): Re
    decreases r, j
  {
    if j == 0 then Eps else Alt(Eps, Cat(r, CopiesUpTo(r, j - 1)))
  }

  // Provided fact (RG_A1b_Facts.CatEpsLeft), complete.
  lemma CatEpsLeft(r: Re, s: seq<char>)
    ensures Matches(Cat(Eps, r), s) <==> Matches(r, s)
  {
    if Matches(r, s) {
      assert s[..0] == [] && s[0..] == s;
    }
  }

  // Provided fact (RG_A1b_Facts.CatAssoc), complete.
  lemma {:induction false} CatAssoc(a: Re, b: Re, c: Re, s: seq<char>)
    ensures Matches(Cat(Cat(a, b), c), s) <==> Matches(Cat(a, Cat(b, c)), s)
  {
    if Matches(Cat(Cat(a, b), c), s) {
      var i :| 0 <= i <= |s| && Matches(Cat(a, b), s[..i]) && Matches(c, s[i..]);
      var u := s[..i];
      var k :| 0 <= k <= |u| && Matches(a, u[..k]) && Matches(b, u[k..]);
      var v := s[k..];
      assert u[..k] == s[..k];
      assert u[k..] == s[k..i];
      assert v[..i - k] == s[k..i];
      assert v[i - k..] == s[i..];
      assert Matches(Cat(b, c), v);
    }
    if Matches(Cat(a, Cat(b, c)), s) {
      var k :| 0 <= k <= |s| && Matches(a, s[..k]) && Matches(Cat(b, c), s[k..]);
      var v := s[k..];
      var j :| 0 <= j <= |v| && Matches(b, v[..j]) && Matches(c, v[j..]);
      var u := s[..k + j];
      assert u[..k] == s[..k];
      assert u[k..] == s[k..k + j];
      assert v[..j] == s[k..k + j];
      assert v[j..] == s[k + j..];
      assert Matches(Cat(a, b), u);
    }
  }

  // Provided fact (R09 reference helper CatCongRight), complete.
  lemma CatCongRight(a: Re, b1: Re, b2: Re, s: seq<char>)
    requires forall t :: Matches(b1, t) <==> Matches(b2, t)
    ensures Matches(Cat(a, b1), s) <==> Matches(Cat(a, b2), s)
  {
    if Matches(Cat(a, b1), s) {
      var i :| 0 <= i <= |s| && Matches(a, s[..i]) && Matches(b1, s[i..]);
      assert Matches(b2, s[i..]);
    }
    if Matches(Cat(a, b2), s) {
      var i :| 0 <= i <= |s| && Matches(a, s[..i]) && Matches(b2, s[i..]);
      assert Matches(b1, s[i..]);
    }
  }

  // The task (R09.W4 CopiesSplit): a + b copies split into a then b copies.
  lemma CopiesSplit(r: Re, a: nat, b: nat, s: seq<char>)
    ensures Matches(Copies(r, a + b), s) <==> Matches(Cat(Copies(r, a), Copies(r, b)), s)
    decreases a
  {
    if a == 0 {
      /*R12_CALLS:c1*/
    } else {
      assert /*R12_HINT:h1*/ true;
      assert /*R12_HINT:h2*/ true;
      /*R12_CALLS:c2*/
      var x, y := Copies(r, a - 1 + b), Cat(Copies(r, a - 1), Copies(r, b));
      forall t ensures Matches(x, t) <==> Matches(y, t) {
        /*R12_CALLS:c3*/
      }
      /*R12_CALLS:c4*/
    }
  }
}
