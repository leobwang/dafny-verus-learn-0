// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["RangesClassLaw"]},{"name":"h1"},{"name":"h2"}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.RangesClassLaw","start":298,"end":314}]
// Provided layer: the class half of RG_A2_Deriv (layer A2), copied verbatim as its own
// module with the layer's export (the representation stays hidden from the task).
module R12_A2 {
  export
    reveals Cp, CRange, Code, InRange, RangesValid, RangesContain, ClassBelow
    provides CharClass, ClassValid, InClass, ClassRank
    provides ClassEmpty, ClassInsert, ClassMember, ClassUnion, ClassRange, ClassOfString
    provides ClassRanges, ClassRangesFacts
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

module R12_LabCase {

  import A2 = R12_A2

  // Provided definitions (R08_RangeStarEngine, given), copied verbatim.
  // Given: c lies in one of the ranges.
  ghost predicate InSomeRange(rs: seq<(char, char)>, c: char)
  {
    exists j | 0 <= j < |rs| :: rs[j].0 <= c <= rs[j].1
  }

  // Given: the class of all the ranges, built with A2's class API.
  function RangesClass(rs: seq<(char, char)>): (cls: A2.CharClass)
    ensures A2.ClassValid(cls)
  {
    if rs == [] then A2.ClassEmpty() else A2.ClassUnion(A2.ClassRange(rs[0].0, rs[0].1), RangesClass(rs[1..]))
  }

  // The task (R08.H1 RangesClassLaw): the class the engine builds holds exactly the characters of the pattern's ranges.
  lemma {:induction false} RangesClassLaw(rs: seq<(char, char)>, c: char)
    ensures A2.InClass(RangesClass(rs), c) <==> InSomeRange(rs, c)
  {
    if rs != [] {
      /*R12_CALLS:c1*/
      if InSomeRange(rs[1..], c) {
        var j :| 0 <= j < |rs[1..]| && rs[1..][j].0 <= c <= rs[1..][j].1;
        assert /*R12_HINT:h1*/ true;
      }
      if InSomeRange(rs, c) {
        var j :| 0 <= j < |rs| && rs[j].0 <= c <= rs[j].1;
        if j > 0 {
          assert /*R12_HINT:h2*/ true;
        }
      }
    }
  }
}
