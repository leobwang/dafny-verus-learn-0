// DVR0 reference (author-only): R09's references over layer A3 (PLAN §3 R09, §2.5 step 5):
// the lowering's correctness lemmas and their helpers, and the recursive-descent parser with
// positions. Counted repetition takes single-character bounds; ClassItems and Counted carry
// completeness clauses, so a parser that always fails does not meet their contracts.
module RX_R09_Syntax {
  import opened RG_A1_Re
  import opened RG_A1b_Facts
  import opened RG_A2_Deriv
  import opened RG_A3_Syntax

  // ---------------------------------------------------------------------------
  // The lowering's correctness (counted repetition, classes)
  // ---------------------------------------------------------------------------

  lemma CopiesSplit(r: Re, a: nat, b: nat, s: seq<char>)
    ensures Matches(Copies(r, a + b), s) <==> Matches(Cat(Copies(r, a), Copies(r, b)), s)
    decreases a
  {
    // @hole-begin R09.CopiesSplit
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
    // @hole-end R09.CopiesSplit
  }

  // Replacing the right operand by a language-equal one (a helper; A4 gives the same fact
  // from R10 on, and its empty body verifies under every induction setting).
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

  lemma CopiesUpToCorrect(r: Re, j: nat, s: seq<char>)
    ensures Matches(CopiesUpTo(r, j), s) <==> exists k | 0 <= k <= j :: Matches(Copies(r, k), s)
    decreases j
  {
    // @hole-begin R09.CopiesUpToCorrect
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
    // @hole-end R09.CopiesUpToCorrect
  }

  lemma RepRangeCorrect(r: Re, n: nat, m: nat, s: seq<char>)
    requires n <= m
    ensures Matches(RepRange(r, n, m), s) <==> exists k | n <= k <= m :: Matches(Copies(r, k), s)
  {
    // @hole-begin R09.RepRangeCorrect
    if Matches(RepRange(r, n, m), s) {
      var i :| 0 <= i <= |s| && Matches(Copies(r, n), s[..i]) && Matches(CopiesUpTo(r, m - n), s[i..]);
      CopiesUpToCorrect(r, m - n, s[i..]);
      var k :| 0 <= k <= m - n && Matches(Copies(r, k), s[i..]);
      CopiesSplit(r, n, k, s);
      assert Matches(Copies(r, n + k), s);
    }
    if exists k | n <= k <= m :: Matches(Copies(r, k), s) {
      var k :| n <= k <= m && Matches(Copies(r, k), s);
      CopiesSplit(r, n, k - n, s);
      var i :| 0 <= i <= |s| && Matches(Copies(r, n), s[..i]) && Matches(Copies(r, k - n), s[i..]);
      CopiesUpToCorrect(r, m - n, s[i..]);
      assert Matches(CopiesUpTo(r, m - n), s[i..]);
    }
    // @hole-end R09.RepRangeCorrect
  }

  lemma RangeReCorrect(lo: char, hi: char, s: seq<char>)
    requires lo <= hi && (hi as int) < ClassMax
    ensures Matches(RangeRe(lo, hi), s) <==> |s| == 1 && lo <= s[0] <= hi
    decreases hi as int - lo as int
  {
    // @hole-begin R09.RangeReCorrect
    if lo != hi {
      var lo2 := (lo as int + 1) as char;
      RangeReCorrect(lo2, hi, s);
      if |s| == 1 && lo <= s[0] <= hi && s[0] != lo {
        assert lo2 <= s[0];
      }
      if |s| == 1 && s[0] == lo {
        assert s == [lo];
      }
    } else {
      if |s| == 1 && lo <= s[0] <= hi {
        assert s == [lo];
      }
    }
    // @hole-end R09.RangeReCorrect
  }

  lemma ClassToReCorrect(cc: CharClass, s: seq<char>)
    requires ClassLowered(cc)
    ensures Matches(ClassToRe(cc), s) <==> |s| == 1 && InClass(cc, s[0])
  {
    // @hole-begin R09.ClassToReCorrect
    if cc != [] {
      RangeReCorrect(cc[0].lo, cc[0].hi, s);
      ClassToReCorrect(cc[1..], s);
      if |s| == 1 {
        var c := s[0];
        if InClass(cc, c) && !InRange(cc[0], c) {
          var i :| 0 <= i < |cc| && InRange(cc[i], c);
          assert InRange(cc[1..][i - 1], c);
        }
        if InClass(cc[1..], c) {
          var i :| 0 <= i < |cc[1..]| && InRange(cc[1..][i], c);
          assert InRange(cc[i + 1], c);
        }
        if InRange(cc[0], c) {
          assert InClass(cc, c);
        }
      }
    }
    // @hole-end R09.ClassToReCorrect
  }

  // ---------------------------------------------------------------------------
  // The parser
  // ---------------------------------------------------------------------------

  function ClassItems(s: seq<char>, i: nat, acc: CharClass): (res: Res<(CharClass, nat)>)
    requires i <= |s| && ClassValid(acc) && ClassLowered(acc)
    ensures res.Ok? ==> i < res.value.1 <= |s| && ClassValid(res.value.0) && ClassLowered(res.value.0)
    ensures res.Err? ==> res.pos <= |s|
    ensures forall k: nat :: SimpleClassBody(s, i, k) ==> res.Ok? && res.value.1 == k + 1
    decreases |s| - i
  {
    // @impl-begin R09.ClassItems trivial=Err(i, "")
    if i >= |s| then Err(i, "unclosed class")
    else if s[i] == ']' then Ok((acc, i + 1))
    else
      var c := if s[i] == '\\' && i + 1 < |s| then s[i + 1] else s[i];
      var k := if s[i] == '\\' && i + 1 < |s| then i + 2 else i + 1;
      if k + 1 < |s| && s[k] == '-' && s[k + 1] != ']' then
        var d := s[k + 1];
        if d < c then Err(k + 1, "empty range")
        else if (d as int) >= ClassMax then Err(k + 1, "class character out of range")
        else
          var acc2 := ClassInsert(acc, CRange(c, d));
          // @hole-begin R09.ClassItems
          assert ClassLowered(acc2) by {
            forall q | 0 <= q < |acc2| ensures acc2[q].lo <= acc2[q].hi && (acc2[q].hi as int) < ClassMax {
              assert InClass(acc2, acc2[q].hi) by { assert InRange(acc2[q], acc2[q].hi); }
              if !InRange(CRange(c, d), acc2[q].hi) {
                var p :| 0 <= p < |acc| && InRange(acc[p], acc2[q].hi);
              }
            }
          }
          // @hole-end R09.ClassItems
          ClassItems(s, k + 2, acc2)
      else if (c as int) >= ClassMax then Err(i, "class character out of range")
      else
        var acc2 := ClassInsert(acc, CRange(c, c));
        // @hole-begin R09.ClassItems
        assert ClassLowered(acc2) by {
          forall q | 0 <= q < |acc2| ensures acc2[q].lo <= acc2[q].hi && (acc2[q].hi as int) < ClassMax {
            assert InClass(acc2, acc2[q].hi) by { assert InRange(acc2[q], acc2[q].hi); }
            if !InRange(CRange(c, c), acc2[q].hi) {
              var p :| 0 <= p < |acc| && InRange(acc[p], acc2[q].hi);
            }
          }
        }
        // @hole-end R09.ClassItems
        // @hole-begin R09.ClassItems
        assert forall k0: nat :: SimpleClassBody(s, i, k0) ==> SimpleClassBody(s, k, k0);
        // @hole-end R09.ClassItems
        ClassItems(s, k, acc2)
    // @impl-end R09.ClassItems
  }

  function ParseAlt(s: seq<char>, i: nat): (res: Res<PR>)
    requires i <= |s|
    ensures res.Ok? ==> i <= res.value.j <= |s| && WF(res.value.t, |s|)
                        && res.value.t.lo == i && res.value.t.hi == res.value.j
    ensures res.Err? ==> res.pos <= |s|
    ensures NoSpecialFrom(s, i) ==> res.Ok? && res.value.j == |s|
    decreases |s| - i, 6
  {
    // @impl-begin R09.ParseAlt trivial=Err(i, "")
    var p :- ParseCat(s, i);
    AltRest(s, p.t, p.j)
    // @impl-end R09.ParseAlt
  }

  function AltRest(s: seq<char>, left: Syn, j: nat): (res: Res<PR>)
    requires j <= |s| && WF(left, |s|) && left.hi == j
    ensures res.Ok? ==> j <= res.value.j <= |s| && WF(res.value.t, |s|)
                        && res.value.t.lo == left.lo && res.value.t.hi == res.value.j
    ensures res.Err? ==> res.pos <= |s|
    ensures NoSpecialFrom(s, j) && j == |s| ==> res.Ok? && res.value.j == |s|
    decreases |s| - j, 5
  {
    // @impl-begin R09.AltRest trivial=Err(j, "")
    if j < |s| && s[j] == '|' then
      var q :- ParseCat(s, j + 1);
      AltRest(s, SAlt(left, q.t, left.lo, q.j), q.j)
    else Ok(PR(left, j))
    // @impl-end R09.AltRest
  }

  function ParseCat(s: seq<char>, i: nat): (res: Res<PR>)
    requires i <= |s|
    ensures res.Ok? ==> i <= res.value.j <= |s| && WF(res.value.t, |s|)
                        && res.value.t.lo == i && res.value.t.hi == res.value.j
    ensures res.Err? ==> res.pos <= |s|
    ensures NoSpecialFrom(s, i) ==> res.Ok? && res.value.j == |s|
    decreases |s| - i, 4
  {
    // @impl-begin R09.ParseCat trivial=Err(i, "")
    if Stop(s, i) then Ok(PR(SEps(i, i), i))
    else
      var p :- ParsePost(s, i);
      CatRest(s, p.t, p.j)
    // @impl-end R09.ParseCat
  }

  function CatRest(s: seq<char>, left: Syn, j: nat): (res: Res<PR>)
    requires j <= |s| && WF(left, |s|) && left.hi == j
    ensures res.Ok? ==> j <= res.value.j <= |s| && WF(res.value.t, |s|)
                        && res.value.t.lo == left.lo && res.value.t.hi == res.value.j
    ensures res.Err? ==> res.pos <= |s|
    ensures NoSpecialFrom(s, j) ==> res.Ok? && res.value.j == |s|
    decreases |s| - j, 3
  {
    // @impl-begin R09.CatRest trivial=Err(j, "")
    if Stop(s, j) then Ok(PR(left, j))
    else
      var q :- ParsePost(s, j);
      CatRest(s, SCat(left, q.t, left.lo, q.j), q.j)
    // @impl-end R09.CatRest
  }

  function ParsePost(s: seq<char>, i: nat): (res: Res<PR>)
    requires i < |s|
    ensures res.Ok? ==> i < res.value.j <= |s| && WF(res.value.t, |s|)
                        && res.value.t.lo == i && res.value.t.hi == res.value.j
    ensures res.Err? ==> res.pos <= |s|
    ensures NoSpecialFrom(s, i) ==> res.Ok? && res.value == PR(SChr(s[i], i, i + 1), i + 1)
    decreases |s| - i, 2
  {
    // @impl-begin R09.ParsePost trivial=Err(i, "")
    var p :- ParseAtom(s, i);
    PostRest(s, p.t, p.j)
    // @impl-end R09.ParsePost
  }

  function PostRest(s: seq<char>, a: Syn, j: nat): (res: Res<PR>)
    requires j <= |s| && WF(a, |s|) && a.hi == j && a.lo < j
    ensures res.Ok? ==> j <= res.value.j <= |s| && WF(res.value.t, |s|)
                        && res.value.t.lo == a.lo && res.value.t.hi == res.value.j
    ensures res.Err? ==> res.pos <= |s|
    ensures NoSpecialFrom(s, j) ==> res == Ok(PR(a, j))
    decreases |s| - j, 1
  {
    // @impl-begin R09.PostRest trivial=Err(j, "")
    if j == |s| then Ok(PR(a, j))
    else if s[j] == '*' then PostRest(s, SStar(a, a.lo, j + 1), j + 1)
    else if s[j] == '+' then PostRest(s, SPlus(a, a.lo, j + 1), j + 1)
    else if s[j] == '?' then PostRest(s, SOpt(a, a.lo, j + 1), j + 1)
    else if s[j] == '{' then
      var (t, k) :- Counted(s, a, j);
      PostRest(s, t, k)
    else Ok(PR(a, j))
    // @impl-end R09.PostRest
  }

  // A counted repetition {n} or {n,m} at s[j] == '{'.
  // A counted repetition {n} or {n,m} at s[j] == '{'; each bound is one character '0'..'9'.
  function Counted(s: seq<char>, a: Syn, j: nat): (res: Res<(Syn, nat)>)
    requires j < |s| && s[j] == '{' && WF(a, |s|) && a.hi == j && a.lo < j
    ensures res.Ok? ==> j < res.value.1 <= |s| && WF(res.value.0, |s|)
                        && res.value.0.lo == a.lo && res.value.0.hi == res.value.1
    ensures res.Err? ==> res.pos <= |s|
    ensures forall n: nat, m: nat, k: nat :: CountedAt(s, j, n, m, k) ==> res == Ok((SRep(a, n, m, a.lo, k), k))
  {
    // @impl-begin R09.Counted trivial=Err(j, "")
    if j + 1 >= |s| then Err(j + 1, "expected a bound")
    else if !BoundChar(s[j + 1]) then Err(j + 1, "expected a bound '0'..'9'")
    else if j + 2 >= |s| then Err(j + 2, "expected '}' or ','")
    else if s[j + 2] == '}' then
      var n := BoundVal(s[j + 1]);
      Ok((SRep(a, n, n, a.lo, j + 3), j + 3))
    else if s[j + 2] != ',' then Err(j + 2, "expected '}' or ','")
    else if j + 3 >= |s| || !BoundChar(s[j + 3]) then Err(j + 3, "expected a bound '0'..'9'")
    else if j + 4 >= |s| || s[j + 4] != '}' then Err(j + 4, "expected '}'")
    else
      var n := BoundVal(s[j + 1]);
      var m := BoundVal(s[j + 3]);
      if m < n then Err(j + 3, "upper bound below lower bound")
      else Ok((SRep(a, n, m, a.lo, j + 5), j + 5))
    // @impl-end R09.Counted
  }

  function ParseAtom(s: seq<char>, i: nat): (res: Res<PR>)
    requires i < |s|
    ensures res.Ok? ==> i < res.value.j <= |s| && WF(res.value.t, |s|)
                        && res.value.t.lo == i && res.value.t.hi == res.value.j
    ensures res.Err? ==> res.pos <= |s|
    ensures NoSpecialFrom(s, i) ==> res == Ok(PR(SChr(s[i], i, i + 1), i + 1))
    decreases |s| - i, 0
  {
    // @impl-begin R09.ParseAtom trivial=Err(i, "")
    var c := s[i];
    if c == '(' then
      var p :- ParseAlt(s, i + 1);
      if p.j < |s| && s[p.j] == ')' then Ok(PR(SGroup(p.t, i, p.j + 1), p.j + 1))
      else Err(p.j, "expected ')'")
    else if c == '[' then
      var (cc, j) :- ClassItems(s, i + 1, []);
      Ok(PR(SClass(cc, i, j), j))
    else if c == '\\' then
      if i + 1 < |s| then Ok(PR(SChr(s[i + 1], i, i + 2), i + 2))
      else Err(i + 1, "dangling escape")
    else if Special(c) then Err(i, "unexpected special character")
    else Ok(PR(SChr(c, i, i + 1), i + 1))
    // @impl-end R09.ParseAtom
  }

  // The whole input must be consumed.
  function Parse(s: seq<char>): (res: Res<Syn>)
    ensures res.Ok? ==> WF(res.value, |s|) && res.value.lo == 0 && res.value.hi == |s|
    ensures res.Err? ==> res.pos <= |s|
    ensures NoSpecialFrom(s, 0) ==> res.Ok?
  {
    // @impl-begin R09.Parse trivial=Err(0, "")
    var p :- ParseAlt(s, 0);
    if p.j == |s| then Ok(p.t) else Err(p.j, "unexpected ')'")
    // @impl-end R09.Parse
  }

  // Fidelity on the literal fragment: a string with no special character
  // parses, and its regex matches exactly that string.
  lemma CatChrStep(a: Re, u: seq<char>, c: char)
    requires Matches(a, u)
    ensures Matches(Cat(a, Chr(c)), u + [c])
  {
    // @hole-begin R09.CatChrStep
    var w := u + [c];
    assert w[..|u|] == u && w[|u|..] == [c];
    // @hole-end R09.CatChrStep
  }

  lemma {:isolate_assertions} CatRestLiteral(s: seq<char>, left: Syn, j: nat)
    requires j <= |s| && WF(left, |s|) && left.hi == j && NoSpecialFrom(s, j)
    requires Matches(Lower(left, |s|), s[left.lo..j])
    ensures CatRest(s, left, j).Ok?
    ensures Matches(Lower(CatRest(s, left, j).value.t, |s|), s[left.lo..])
    decreases |s| - j
  {
    // @hole-begin R09.CatRestLiteral
    if j == |s| {
      assert s[left.lo..j] == s[left.lo..];
    } else {
      var q := SChr(s[j], j, j + 1);
      var t := SCat(left, q, left.lo, j + 1);
      assert !Stop(s, j) && ParsePost(s, j) == Ok(PR(q, j + 1));
      assert WF(t, |s|);
      assert CatRest(s, left, j) == CatRest(s, t, j + 1);
      assert s[left.lo..j + 1] == s[left.lo..j] + [s[j]];
      CatChrStep(Lower(left, |s|), s[left.lo..j], s[j]);
      assert Lower(t, |s|) == Cat(Lower(left, |s|), Chr(s[j]));
      CatRestLiteral(s, t, j + 1);
    }
    // @hole-end R09.CatRestLiteral
  }

  lemma LiteralFidelity(s: seq<char>)
    requires NoSpecialFrom(s, 0)
    ensures Parse(s).Ok? && Matches(Lower(Parse(s).value, |s|), s)
  {
    // @hole-begin R09.LiteralFidelity
    if s == [] {
      assert ParseCat(s, 0) == Ok(PR(SEps(0, 0), 0));
      assert AltRest(s, SEps(0, 0), 0) == Ok(PR(SEps(0, 0), 0));
      assert Parse(s) == Ok(SEps(0, 0));
    } else {
      var a := SChr(s[0], 0, 1);
      assert s[0..1] == [s[0]];
      CatRestLiteral(s, a, 1);
      var c := CatRest(s, a, 1);
      assert ParsePost(s, 0) == Ok(PR(a, 1));
      assert ParseCat(s, 0) == c;
      assert c.value.j == |s|;
      assert AltRest(s, c.value.t, c.value.j) == Ok(c.value);
      assert Parse(s) == Ok(c.value.t);
      assert s[0..] == s;
    }
    // @hole-end R09.LiteralFidelity
  }

  function PatternToRe(s: seq<char>): Res<Re>
  {
    var t :- Parse(s);
    Ok(Lower(t, |s|))
  }
}
