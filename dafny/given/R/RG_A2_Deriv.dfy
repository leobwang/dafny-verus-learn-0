/*!
# RG_A2 — regex spine, layer A2 (PROVIDED, complete; provisional until R03 and R06 pass)

Do not open this file before R03 and R06 are done: it re-supplies, complete and proved,
R03's character-class API and R06's derivative proofs (`DerivCorrect`, `DerivMatch`).
Finish their holes and record their first tries (`scripts/firsttry.sh R03 --check`,
`scripts/firsttry.sh R06 --check`) first.

Frozen infrastructure, not an exercise. Imported by R07–R16: the character-class API and
derivative matcher re-supplied after band 1. Use only the layer chain declared by your
module. No earlier learner file is imported. PLAN.md §2.2 and §2.4 define this layer
boundary. Provisional: the class half is final once R03 and R06 pass on it.
*/
module RG_A2_Deriv {
  // The class representation is hidden: clients build classes only through the API,
  // and read a class's ranges only through the accessor ClassRanges.
  export
    reveals Cp, CRange, Code, InRange, RangesValid, RangesContain, ClassBelow, Deriv
    provides RG_A1_Re, RG_A1b_Facts
    provides CharClass, ClassValid, InClass, ClassRank
    provides ClassEmpty, ClassInsert, ClassMember, ClassUnion, ClassRange, ClassOfString
    provides ClassRanges, ClassRangesFacts
    provides DerivCorrect, DerivMatch

  import opened RG_A1_Re
  import opened RG_A1b_Facts

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

  // The derivative matcher: one derivative per character, then Nullable.
  method DerivMatch(r: Re, s: seq<char>) returns (b: bool)
    ensures b == Matches(r, s)
  {
    var cur := r;
    var i := 0;
    while i < |s|
      invariant 0 <= i <= |s|
      invariant Matches(cur, s[i..]) <==> Matches(r, s)
    {
      DerivCorrect(cur, s[i], s[i + 1..]);
      assert [s[i]] + s[i + 1..] == s[i..];
      cur := Deriv(cur, s[i]);
      i := i + 1;
    }
    NullableCorrect(cur);
    assert s[i..] == [];
    b := Nullable(cur);
  }

  // ---------------------------------------------------------------------------
  // Code points and ranges (u32 code-point pairs)
  // ---------------------------------------------------------------------------

  // A code point: any u32 value. A range may hold codes that are not chars
  // (the surrogate block 0xD800..0xDFFF, everything above 0x10FFFF); they add no char.
  newtype Cp = x: int | 0 <= x < 0x1_0000_0000

  datatype CRange = CRange(lo: Cp, hi: Cp)

  // The only conversion: a char to its code. Nothing builds a char from a code here.
  function Code(c: char): Cp
  {
    c as int as Cp
  }

  predicate InRange(g: CRange, c: char)
  {
    g.lo <= Code(c) <= g.hi
  }

  // Every range is non-empty; ranges are sorted and separated by at least one code.
  predicate RangesValid(rs: seq<CRange>)
  {
    (forall i | 0 <= i < |rs| :: rs[i].lo <= rs[i].hi) &&
    (forall i, j | 0 <= i < j < |rs| :: rs[i].hi as int + 1 < rs[j].lo as int)
  }

  ghost predicate RangesContain(rs: seq<CRange>, c: char)
  {
    exists i | 0 <= i < |rs| :: InRange(rs[i], c)
  }

  function MinCp(a: Cp, b: Cp): Cp
  {
    if a <= b then a else b
  }

  function MaxCp(a: Cp, b: Cp): Cp
  {
    if a <= b then b else a
  }

  // ---------------------------------------------------------------------------
  // CharClass: R03's total API, re-supplied (representation hidden)
  // ---------------------------------------------------------------------------

  datatype CharClass = CharClass(ranges: seq<CRange>)

  predicate ClassValid(cc: CharClass)
  {
    RangesValid(cc.ranges)
  }

  ghost function ClassRank(cc: CharClass): nat
  {
    |cc.ranges|
  }

  // Spec membership.
  ghost predicate InClass(cc: CharClass, c: char)
  {
    RangesContain(cc.ranges, c)
  }

  // The read-only range accessor (for A3's lowering and size accounting).
  function ClassRanges(cc: CharClass): seq<CRange>
  {
    cc.ranges
  }

  lemma ClassRangesFacts(cc: CharClass)
    ensures ClassValid(cc) <==> RangesValid(ClassRanges(cc))
    ensures forall c :: InClass(cc, c) <==> RangesContain(ClassRanges(cc), c)
  {
  }

  // Every range of the listing ends below code b.
  predicate ClassBelow(cc: CharClass, b: int)
  {
    forall i | 0 <= i < |ClassRanges(cc)| :: ClassRanges(cc)[i].hi as int < b
  }

  function ClassEmpty(): (r: CharClass)
    ensures ClassValid(r)
    ensures forall c :: !InClass(r, c)
    ensures ClassRanges(r) == []
  {
    CharClass([])
  }

  // Membership in a listing with one range in front.
  lemma ContainsCons(x: CRange, rs: seq<CRange>)
    ensures forall c :: RangesContain([x] + rs, c) <==> InRange(x, c) || RangesContain(rs, c)
  {
    var t := [x] + rs;
    forall c
      ensures RangesContain(t, c) <==> InRange(x, c) || RangesContain(rs, c)
    {
      if RangesContain(t, c) {
        var i :| 0 <= i < |t| && InRange(t[i], c);
        if i > 0 {
          assert InRange(rs[i - 1], c);
        }
      }
      if RangesContain(rs, c) {
        var i :| 0 <= i < |rs| && InRange(rs[i], c);
        assert InRange(t[i + 1], c);
      }
      if InRange(x, c) {
        assert InRange(t[0], c);
      }
    }
  }

  // Validity of a listing with one range in front.
  lemma ValidCons(x: CRange, rs: seq<CRange>)
    requires RangesValid(rs) && x.lo <= x.hi
    requires forall k | 0 <= k < |rs| :: x.hi as int + 1 < rs[k].lo as int
    ensures RangesValid([x] + rs)
  {
    var t := [x] + rs;
    forall i, j | 0 <= i < j < |t|
      ensures t[i].hi as int + 1 < t[j].lo as int
    {
      if i > 0 {
        assert t[i] == rs[i - 1] && t[j] == rs[j - 1];
      } else {
        assert t[j] == rs[j - 1];
      }
    }
  }

  // Insert one non-empty range into valid ranges, merging overlapping and adjacent ones.
  function InsertRanges(rs: seq<CRange>, g: CRange): (res: seq<CRange>)
    requires RangesValid(rs) && g.lo <= g.hi
    ensures RangesValid(res)
    ensures forall c :: RangesContain(res, c) <==> RangesContain(rs, c) || InRange(g, c)
    ensures forall k | 0 <= k < |res| :: res[k].lo >= (if rs == [] then g.lo else MinCp(g.lo, rs[0].lo))
    decreases |rs|
  {
    if rs == [] then
      ContainsCons(g, []);
      ValidCons(g, []);
      assert [g] + [] == [g];
      [g]
    else
      var h := rs[0];
      var t := rs[1..];
      assert rs == [h] + t;
      ContainsCons(h, t);
      if g.hi as int + 1 < h.lo as int then
        ContainsCons(g, rs);
        ValidCons(g, rs);
        [g] + rs
      else if h.hi as int + 1 < g.lo as int then
        var r2 := InsertRanges(t, g);
        ContainsCons(h, r2);
        ValidCons(h, r2);
        [h] + r2
      else
        // g and h overlap or touch: their union is one range.
        var g2 := CRange(MinCp(g.lo, h.lo), MaxCp(g.hi, h.hi));
        InsertRanges(t, g2)
  }

  // Inserting a range below b keeps every range below b.
  lemma InsertRangesBelow(rs: seq<CRange>, g: CRange, b: int)
    requires RangesValid(rs) && g.lo <= g.hi
    requires g.hi as int < b
    requires forall k | 0 <= k < |rs| :: rs[k].hi as int < b
    ensures forall k | 0 <= k < |InsertRanges(rs, g)| :: InsertRanges(rs, g)[k].hi as int < b
    decreases |rs|
  {
    if rs != [] {
      var h := rs[0];
      if g.hi as int + 1 < h.lo as int {
      } else if h.hi as int + 1 < g.lo as int {
        InsertRangesBelow(rs[1..], g, b);
      } else {
        InsertRangesBelow(rs[1..], CRange(MinCp(g.lo, h.lo), MaxCp(g.hi, h.hi)), b);
      }
    }
  }

  // Executable membership.
  function ClassMember(cc: CharClass, c: char): (b: bool)
    ensures b == InClass(cc, c)
    decreases ClassRank(cc)
  {
    if cc.ranges == [] then
      false
    else
      var rest := ClassMember(CharClass(cc.ranges[1..]), c);
      InRange(cc.ranges[0], c) || rest
  }

  // Insert the range g (total: an empty range g.lo > g.hi adds nothing).
  function ClassInsert(cc: CharClass, g: CRange): (res: CharClass)
    requires ClassValid(cc)
    ensures ClassValid(res)
    ensures forall c :: InClass(res, c) <==> InClass(cc, c) || InRange(g, c)
    ensures forall b: int :: ClassBelow(cc, b) && g.hi as int < b ==> ClassBelow(res, b)
  {
    if g.hi < g.lo then
      cc
    else
      var res := CharClass(InsertRanges(cc.ranges, g));
      assert forall b: int :: ClassBelow(cc, b) && g.hi as int < b ==> ClassBelow(res, b) by {
        forall b: int | ClassBelow(cc, b) && g.hi as int < b
          ensures ClassBelow(res, b)
        {
          assert ClassRanges(cc) == cc.ranges;
          InsertRangesBelow(cc.ranges, g, b);
        }
      }
      res
  }

  function ClassUnion(a: CharClass, b: CharClass): (u: CharClass)
    requires ClassValid(a) && ClassValid(b)
    ensures ClassValid(u)
    ensures forall c :: InClass(u, c) <==> InClass(a, c) || InClass(b, c)
    ensures forall n: int :: ClassBelow(a, n) && ClassBelow(b, n) ==> ClassBelow(u, n)
    decreases ClassRank(b)
  {
    if b.ranges == [] then
      a
    else
      var a2 := ClassInsert(a, b.ranges[0]);
      var b2 := CharClass(b.ranges[1..]);
      assert forall n: int :: ClassBelow(b, n) ==> b.ranges[0].hi as int < n && ClassBelow(b2, n) by {
        forall n: int | ClassBelow(b, n)
          ensures b.ranges[0].hi as int < n && ClassBelow(b2, n)
        {
          assert ClassRanges(b) == b.ranges;
          assert ClassRanges(b2) == b.ranges[1..];
        }
      }
      ClassUnion(a2, b2)
  }

  // The class of one inclusive char interval (total: lo > hi gives the empty class).
  function ClassRange(lo: char, hi: char): (r: CharClass)
    ensures ClassValid(r)
    ensures forall c :: InClass(r, c) <==> lo <= c <= hi
  {
    ClassInsert(ClassEmpty(), CRange(Code(lo), Code(hi)))
  }

  // The class of the characters of a string.
  function ClassOfString(s: seq<char>): (r: CharClass)
    ensures ClassValid(r)
    ensures forall c :: InClass(r, c) <==> c in s
    decreases |s|
  {
    if |s| == 0 then
      ClassEmpty()
    else
      var tail := ClassOfString(s[1..]);
      ClassInsert(tail, CRange(Code(s[0]), Code(s[0])))
  }

}
