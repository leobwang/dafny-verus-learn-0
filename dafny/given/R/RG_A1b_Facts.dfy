/*!
# RG_A1b — regex spine, layer A1b (PROVIDED, complete)

Do not open this file before R02 and R05 are done: it re-supplies R02's `NullableCorrect`,
`CatEpsLeft` (R02's H4 in Verus; its Dafny H4 is `CatTwoChrs`, D60) and R05's band-1 facts
(`CatAssoc`, `StarOne`, `StarConcat`), proved. Finish their holes and record first tries
(`scripts/firsttry.sh R02 --check`, `scripts/firsttry.sh R05 --check`) first.

Frozen infrastructure, not an exercise. Imported by R06–R16: band-1 facts re-supplied after their original exercises.
Use only the layer chain declared by your module. No earlier learner file is imported.
PLAN.md §2.2 and §2.4 define this layer boundary.
*/
module RG_A1b_Facts {
  import opened RG_A1_Re

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

  lemma CatEpsLeft(r: Re, s: seq<char>)
    ensures Matches(Cat(Eps, r), s) <==> Matches(r, s)
  {
    if Matches(r, s) {
      assert s[..0] == [] && s[0..] == s;
    }
  }

  lemma CatEpsRight(r: Re, s: seq<char>)
    ensures Matches(Cat(r, Eps), s) <==> Matches(r, s)
  {
    if Matches(r, s) {
      assert s[..|s|] == s && s[|s|..] == [];
    }
    if Matches(Cat(r, Eps), s) {
      var i :| 0 <= i <= |s| && Matches(r, s[..i]) && Matches(Eps, s[i..]);
      assert i == |s|;
      assert s[..i] == s;
    }
  }

  // Concatenation is associative on languages (both directions; R05 poses each one).
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

  lemma StarOne(a: Re, u: seq<char>)
    requires Matches(a, u)
    ensures Matches(Star(a), u)
  {
    if u != [] {
      assert u[..|u|] == u && u[|u|..] == [];
    }
  }

  lemma StarConcat(a: Re, u: seq<char>, v: seq<char>)
    requires Matches(Star(a), u) && Matches(Star(a), v)
    ensures Matches(Star(a), u + v)
    decreases |u|
  {
    if u == [] {
      assert u + v == v;
    } else {
      var i :| 0 < i <= |u| && Matches(a, u[..i]) && Matches(Star(a), u[i..]);
      StarConcat(a, u[i..], v);
      assert (u + v)[..i] == u[..i];
      assert (u + v)[i..] == u[i..] + v;
    }
  }
}
