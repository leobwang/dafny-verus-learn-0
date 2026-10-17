// DVR0 reference, layer A1b (author-only). Ships as dafny/given/R/RG_A1b_Facts.dfy,
// declared by R06 and imported by R06-R16 (PLAN §2.2, §2.4, §2.5 step 3): the band-1
// facts, re-supplied (R02's NullableCorrect and CatEpsLeft, R05's CatAssoc, StarOne and
// StarConcat) plus CatEpsRight. The marked regions are also the references of the R02
// and R05 holes, so the gate blanks them.
module RG_A1b_Facts {
  import opened RG_A1_Re

  lemma NullableCorrect(r: Re)
    ensures Nullable(r) <==> Matches(r, [])
    decreases r
  {
    // @hole-begin A1b.NullableCorrect
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
    // @hole-end A1b.NullableCorrect
  }

  lemma CatEpsLeft(r: Re, s: seq<char>)
    ensures Matches(Cat(Eps, r), s) <==> Matches(r, s)
  {
    // @hole-begin A1b.CatEpsLeft
    if Matches(r, s) {
      assert s[..0] == [] && s[0..] == s;
    }
    // @hole-end A1b.CatEpsLeft
  }

  lemma CatEpsRight(r: Re, s: seq<char>)
    ensures Matches(Cat(r, Eps), s) <==> Matches(r, s)
  {
    // @hole-begin A1b.CatEpsRight
    if Matches(r, s) {
      assert s[..|s|] == s && s[|s|..] == [];
    }
    if Matches(Cat(r, Eps), s) {
      var i :| 0 <= i <= |s| && Matches(r, s[..i]) && Matches(Eps, s[i..]);
      assert i == |s|;
      assert s[..i] == s;
    }
    // @hole-end A1b.CatEpsRight
  }

  // Concatenation is associative on languages (both directions; R05 poses each one).
  lemma {:induction false} CatAssoc(a: Re, b: Re, c: Re, s: seq<char>)
    ensures Matches(Cat(Cat(a, b), c), s) <==> Matches(Cat(a, Cat(b, c)), s)
  {
    // @hole-begin A1b.CatAssoc
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
    // @hole-end A1b.CatAssoc
  }

  lemma StarOne(a: Re, u: seq<char>)
    requires Matches(a, u)
    ensures Matches(Star(a), u)
  {
    // @hole-begin A1b.StarOne
    if u != [] {
      assert u[..|u|] == u && u[|u|..] == [];
    }
    // @hole-end A1b.StarOne
  }

  lemma StarConcat(a: Re, u: seq<char>, v: seq<char>)
    requires Matches(Star(a), u) && Matches(Star(a), v)
    ensures Matches(Star(a), u + v)
    decreases |u|
  {
    // @hole-begin A1b.StarConcat
    if u == [] {
      assert u + v == v;
    } else {
      var i :| 0 < i <= |u| && Matches(a, u[..i]) && Matches(Star(a), u[i..]);
      StarConcat(a, u[i..], v);
      assert (u + v)[..i] == u[..i];
      assert (u + v)[i..] == u[i..] + v;
    }
    // @hole-end A1b.StarConcat
  }
}
