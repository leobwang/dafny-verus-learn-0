// R12_HINT_SITES: [{"name":"c1","identifiers":["r","m","n","s","i"],"kind":"calls","callees":["CopiesUpToCorrect"]},{"name":"c2","identifiers":["r","n","k","s"],"kind":"calls","callees":["CopiesSplit"]},{"name":"h1","identifiers":["Matches","Copies","r","n","k","s"]},{"name":"c3","identifiers":["r","n","k","s"],"kind":"calls","callees":["CopiesSplit"]},{"name":"c4","identifiers":["r","m","n","s","i"],"kind":"calls","callees":["CopiesUpToCorrect"]},{"name":"h2","identifiers":["Matches","CopiesUpTo","r","m","n","s","i"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.RepRangeCorrect","start":156,"end":174}]
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

  function RepRange(r: Re, n: nat, m: nat): Re
    requires n <= m
  {
    Cat(Copies(r, n), CopiesUpTo(r, m - n))
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

  // Provided fact (R09 reference CopiesSplit), complete.
  lemma CopiesSplit(r: Re, a: nat, b: nat, s: seq<char>)
    ensures Matches(Copies(r, a + b), s) <==> Matches(Cat(Copies(r, a), Copies(r, b)), s)
    decreases a
  {
    if a == 0 {
      CatEpsLeft(Copies(r, b), s);
    } else {
      assert Copies(r, a + b) == Cat(r, Copies(r, a - 1 + b));
      assert Copies(r, a) == Cat(r, Copies(r, a - 1));
      CatAssoc(r, Copies(r, a - 1), Copies(r, b), s);
      var x, y := Copies(r, a - 1 + b), Cat(Copies(r, a - 1), Copies(r, b));
      forall t ensures Matches(x, t) <==> Matches(y, t) {
        CopiesSplit(r, a - 1, b, t);
      }
      CatCongRight(r, x, y, s);
    }
  }

  // Provided fact (R09 reference CopiesUpToCorrect), complete.
  lemma CopiesUpToCorrect(r: Re, j: nat, s: seq<char>)
    ensures Matches(CopiesUpTo(r, j), s) <==> exists k | 0 <= k <= j :: Matches(Copies(r, k), s)
    decreases j
  {
    if j > 0 {
      var u := CopiesUpTo(r, j - 1);
      assert CopiesUpTo(r, j) == Alt(Eps, Cat(r, u));
      if Matches(CopiesUpTo(r, j), s) {
        if s != [] {
          assert !Matches(Eps, s);
          assert Matches(Cat(r, u), s);
          var i :| 0 <= i <= |s| && Matches(r, s[..i]) && Matches(u, s[i..]);
          CopiesUpToCorrect(r, j - 1, s[i..]);
          var k :| 0 <= k <= j - 1 && Matches(Copies(r, k), s[i..]);
          assert Copies(r, k + 1) == Cat(r, Copies(r, k));
          assert Matches(Copies(r, k + 1), s);
        } else {
          assert Matches(Copies(r, 0), s);
        }
      }
      if exists k | 0 <= k <= j :: Matches(Copies(r, k), s) {
        var k :| 0 <= k <= j && Matches(Copies(r, k), s);
        if k > 0 {
          assert Copies(r, k) == Cat(r, Copies(r, k - 1));
          var i :| 0 <= i <= |s| && Matches(r, s[..i]) && Matches(Copies(r, k - 1), s[i..]);
          CopiesUpToCorrect(r, j - 1, s[i..]);
          assert exists k' | 0 <= k' <= j - 1 :: Matches(Copies(r, k'), s[i..]);
          assert Matches(Cat(r, u), s);
        } else {
          assert Copies(r, 0) == Eps;
        }
        assert Matches(CopiesUpTo(r, j), s);
        assert exists k | 0 <= k <= j :: Matches(Copies(r, k), s);
      }
    } else {
      assert Copies(r, 0) == Eps;
      if exists k | 0 <= k <= j :: Matches(Copies(r, k), s) {
        var k :| 0 <= k <= j && Matches(Copies(r, k), s);
        assert k == 0;
        assert exists k | 0 <= k <= j :: Matches(Copies(r, k), s);
      }
    }
  }

  // The task (R09.H4 RepRangeCorrect): RepRange(r, n, m) matches exactly n..m copies.
  lemma {:induction false} RepRangeCorrect(r: Re, n: nat, m: nat, s: seq<char>)
    requires n <= m
    ensures Matches(RepRange(r, n, m), s) <==> exists k | n <= k <= m :: Matches(Copies(r, k), s)
  {
    if Matches(RepRange(r, n, m), s) {
      var i :| 0 <= i <= |s| && Matches(Copies(r, n), s[..i]) && Matches(CopiesUpTo(r, m - n), s[i..]);
      /*R12_CALLS:c1*/
      var k :| 0 <= k <= m - n && Matches(Copies(r, k), s[i..]);
      /*R12_CALLS:c2*/
      assert /*R12_HINT:h1*/ true;
    }
    if exists k | n <= k <= m :: Matches(Copies(r, k), s) {
      var k :| n <= k <= m && Matches(Copies(r, k), s);
      /*R12_CALLS:c3*/
      var i :| 0 <= i <= |s| && Matches(Copies(r, n), s[..i]) && Matches(Copies(r, k - n), s[i..]);
      /*R12_CALLS:c4*/
      assert /*R12_HINT:h2*/ true;
    }
  }
}
