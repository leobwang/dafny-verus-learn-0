// DVR0 reference, layer A2 (author-only). Ships as dafny/given/R/RG_A2_Deriv.dfy, declared
// by R07 (PLAN §2.2, §2.5 step 4): re-supplies R03's character-class API and R06's Deriv
// family. NullableCorrect, StarOne and StarConcat come from A1b. The marked regions are the
// references of the R03 and R06 holes.
module RG_A2_Deriv {
  import opened RG_A1_Re
  import opened RG_A1b_Facts

  // ---------------------------------------------------------------------------
  // CharClass: sorted, disjoint inclusive ranges (R03's total API)
  // ---------------------------------------------------------------------------

  datatype CRange = CRange(lo: char, hi: char)
  type CharClass = seq<CRange>

  predicate InRange(g: CRange, c: char) { g.lo <= c <= g.hi }

  // Spec membership.
  ghost predicate InClass(cc: CharClass, c: char)
  {
    exists i | 0 <= i < |cc| :: InRange(cc[i], c)
  }

  predicate ClassValid(cc: CharClass)
  {
    (forall i | 0 <= i < |cc| :: cc[i].lo <= cc[i].hi) &&
    (forall i, j | 0 <= i < j < |cc| :: cc[i].hi < cc[j].lo)
  }

  function MinC(a: char, b: char): char { if a <= b then a else b }
  function MaxC(a: char, b: char): char { if a <= b then b else a }

  // Executable membership.
  function ClassMember(cc: CharClass, c: char): bool
    ensures ClassMember(cc, c) <==> InClass(cc, c)
    decreases |cc|
  {
    // @impl-begin A2.ClassMember trivial=false
    if cc == [] then false
    else
      var rest := ClassMember(cc[1..], c);
      InRange(cc[0], c) || rest
    // @impl-end A2.ClassMember
  }

  // Insert one range into a valid class, merging overlaps.
  function ClassInsert(cc: CharClass, g: CRange): (res: CharClass)
    requires ClassValid(cc) && g.lo <= g.hi
    ensures ClassValid(res)
    ensures forall c :: InClass(res, c) <==> InClass(cc, c) || InRange(g, c)
    ensures forall k | 0 <= k < |res| :: res[k].lo >= (if cc == [] then g.lo else MinC(g.lo, cc[0].lo))
    decreases |cc|
  {
    // @impl-begin A2.ClassInsert trivial=cc
    if cc == [] then
      // @hole-begin A2.ClassInsert
      assert forall c :: InClass([g], c) <==> InRange(g, c) by {
        forall c ensures InClass([g], c) <==> InRange(g, c) {
          if InRange(g, c) { assert InRange([g][0], c); }
        }
      }
      // @hole-end A2.ClassInsert
      [g]
    else
      var h := cc[0];
      var t := cc[1..];
      if g.hi < h.lo then
        var res := [g] + cc;
        // @hole-begin A2.ClassInsert
        assert forall c :: InClass(res, c) <==> InRange(g, c) || InClass(cc, c) by {
          forall c ensures InClass(res, c) <==> InRange(g, c) || InClass(cc, c) {
            if InClass(res, c) {
              var i :| 0 <= i < |res| && InRange(res[i], c);
              if i > 0 { assert InRange(cc[i - 1], c); }
            }
            if InClass(cc, c) {
              var i :| 0 <= i < |cc| && InRange(cc[i], c);
              assert InRange(res[i + 1], c);
            }
            if InRange(g, c) { assert InRange(res[0], c); }
          }
        }
        // @hole-end A2.ClassInsert
        res
      else if h.hi < g.lo then
        var r2 := ClassInsert(t, g);
        var res := [h] + r2;
        // @hole-begin A2.ClassInsert
        assert forall c :: InClass(res, c) <==> InRange(h, c) || InClass(r2, c) by {
          forall c ensures InClass(res, c) <==> InRange(h, c) || InClass(r2, c) {
            if InClass(res, c) {
              var i :| 0 <= i < |res| && InRange(res[i], c);
              if i > 0 { assert InRange(r2[i - 1], c); }
            }
            if InClass(r2, c) {
              var i :| 0 <= i < |r2| && InRange(r2[i], c);
              assert InRange(res[i + 1], c);
            }
            if InRange(h, c) { assert InRange(res[0], c); }
          }
        }
        // @hole-end A2.ClassInsert
        res
      else
        var g2 := CRange(MinC(g.lo, h.lo), MaxC(g.hi, h.hi));
        var res := ClassInsert(t, g2);
        res
    // @impl-end A2.ClassInsert
  }

  function ClassUnion(a: CharClass, b: CharClass): (res: CharClass)
    requires ClassValid(a) && ClassValid(b)
    ensures ClassValid(res)
    ensures forall c :: InClass(res, c) <==> InClass(a, c) || InClass(b, c)
    decreases |b|
  {
    // @impl-begin A2.ClassUnion trivial=a
    if b == [] then a
    else
      var a2 := ClassInsert(a, b[0]);
      var b2 := b[1..];
      ClassUnion(a2, b2)
    // @impl-end A2.ClassUnion
  }

  // ---------------------------------------------------------------------------
  // Brzozowski derivative
  // ---------------------------------------------------------------------------

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

  lemma DerivCorrect(r: Re, c: char, s: seq<char>)
    ensures Matches(Deriv(r, c), s) <==> Matches(r, [c] + s)
    decreases r
  {
    // @hole-begin A2.DerivCorrect
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
    // @hole-end A2.DerivCorrect
  }

  // The derivative matcher: one derivative per character, then Nullable.
  method DerivMatch(r: Re, s: seq<char>) returns (b: bool)
    ensures b == Matches(r, s)
  {
    var cur := r;
    var i := 0;
    while i < |s|
      // @hole-begin A2.DerivMatch
      invariant 0 <= i <= |s|
      invariant Matches(cur, s[i..]) <==> Matches(r, s)
      // @hole-end A2.DerivMatch
    {
      // @hole-begin A2.DerivMatch
      DerivCorrect(cur, s[i], s[i + 1..]);
      assert [s[i]] + s[i + 1..] == s[i..];
      // @hole-end A2.DerivMatch
      cur := Deriv(cur, s[i]);
      i := i + 1;
    }
    // @hole-begin A2.DerivMatch
    NullableCorrect(cur);
    assert s[i..] == [];
    // @hole-end A2.DerivMatch
    b := Nullable(cur);
  }
}
