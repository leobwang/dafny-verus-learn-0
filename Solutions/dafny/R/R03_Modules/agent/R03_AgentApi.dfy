/* CONTRACT
goal: implement ClassIntersect and ClassDiff on every valid input, preserving the stated membership semantics and validity
allowed-files:
  - dafny/R/R03_Modules/agent/R03_AgentApi.dfy
acceptance:
  - scripts/vcheck --gate dafny/R/R03_Modules/agent/R03_AgentApi.dfy exits 0, zero counted holes
  - scripts/specfreeze --against <snapshot> dafny/R/R03_Modules/agent/R03_AgentApi.dfy reports all supplied statements unchanged
  - scripts/vaudit dafny/R/R03_Modules/agent/R03_AgentApi.dfy reports zero findings
  - preserve given code, representation and contracts; no new requires, weakened ensures, assumptions or escape hatches
  - only this file may change; private implementation helpers may be added
*/
/*! Do not open this file before R03's hand holes are done (H1–H5, and in Verus
H6v and H7v): it copies the given class code, including the definitions H6v
and H7v ask you to write. R03 API implementer, R-v0. Save the original file outside the delivery as
<snapshot> before /contract R03; record its hash and the exact allowed file.
A green verification loop with the two API holes is unfinished. The gate must
have zero holes. Review empty and equal inputs and the code boundaries (0, the largest u32,
adjacent ranges, a range across the surrogate block).
*/
module R03_AgentApi {
  // PROVIDED: a copy of the given class code (R03.W2d), u32 code-point ranges (D48).
  // A code point: any u32 value (D48). Codes that are not chars (the surrogate
  // block, everything above 0x10FFFF) may lie inside a range; they add no char.
  newtype Cp = x: int | 0 <= x < 0x1_0000_0000

  datatype CRange = CRange(lo: Cp, hi: Cp)
  datatype CharClass = CharClass(ranges: seq<CRange>)
  type RangeSeq = seq<CRange>

  // The only conversion: a char to its code.
  function Code(c: char): Cp
  {
    c as int as Cp
  }

  predicate InRange(g: CRange, c: char)
  {
    g.lo <= Code(c) <= g.hi
  }

  ghost predicate RangesContain(rs: RangeSeq, c: char)
  {
    exists i | 0 <= i < |rs| :: InRange(rs[i], c)
  }

  // Non-empty ranges, sorted and separated by at least one code.
  predicate RangesValid(rs: RangeSeq)
  {
    (forall i | 0 <= i < |rs| :: rs[i].lo <= rs[i].hi) &&
    (forall i, j | 0 <= i < j < |rs| :: rs[i].hi as int + 1 < rs[j].lo as int)
  }

  function MinCp(a: Cp, b: Cp): Cp
  {
    if a <= b then a else b
  }

  function MaxCp(a: Cp, b: Cp): Cp
  {
    if a <= b then b else a
  }

  // Insert one non-empty range, merging the ranges it overlaps or touches.
  function InsertRanges(rs: RangeSeq, g: CRange): (res: RangeSeq)
    requires RangesValid(rs) && g.lo <= g.hi
    ensures RangesValid(res)
    ensures forall c :: RangesContain(res, c) <==> RangesContain(rs, c) || InRange(g, c)
    ensures forall k | 0 <= k < |res| :: res[k].lo >= (if rs == [] then g.lo else MinCp(g.lo, rs[0].lo))
    decreases |rs|
  {
    if rs == [] then
      assert forall c :: RangesContain([g], c) <==> InRange(g, c) by {
        forall c
          ensures RangesContain([g], c) <==> InRange(g, c)
        {
          if InRange(g, c) {
            assert InRange([g][0], c);
          }
        }
      }
      [g]
    else
      var h := rs[0];
      var t := rs[1..];
      if g.hi as int + 1 < h.lo as int then
        var res := [g] + rs;
        assert forall c :: RangesContain(res, c) <==> InRange(g, c) || RangesContain(rs, c) by {
          forall c
            ensures RangesContain(res, c) <==> InRange(g, c) || RangesContain(rs, c)
          {
            if RangesContain(res, c) {
              var i :| 0 <= i < |res| && InRange(res[i], c);
              if i > 0 {
                assert InRange(rs[i - 1], c);
              }
            }
            if RangesContain(rs, c) {
              var i :| 0 <= i < |rs| && InRange(rs[i], c);
              assert InRange(res[i + 1], c);
            }
            if InRange(g, c) {
              assert InRange(res[0], c);
            }
          }
        }
        res
      else if h.hi as int + 1 < g.lo as int then
        var r2 := InsertRanges(t, g);
        var res := [h] + r2;
        assert forall c :: RangesContain(res, c) <==> InRange(h, c) || RangesContain(r2, c) by {
          forall c
            ensures RangesContain(res, c) <==> InRange(h, c) || RangesContain(r2, c)
          {
            if RangesContain(res, c) {
              var i :| 0 <= i < |res| && InRange(res[i], c);
              if i > 0 {
                assert InRange(r2[i - 1], c);
              }
            }
            if RangesContain(r2, c) {
              var i :| 0 <= i < |r2| && InRange(r2[i], c);
              assert InRange(res[i + 1], c);
            }
            if InRange(h, c) {
              assert InRange(res[0], c);
            }
          }
        }
        res
      else
        // g and h overlap or touch: their union is one range.
        var g2 := CRange(MinCp(g.lo, h.lo), MaxCp(g.hi, h.hi));
        InsertRanges(t, g2)
  }

  predicate ClassValid(cc: CharClass)
  {
    RangesValid(cc.ranges)
  }

  ghost function ClassRank(cc: CharClass): nat
  {
    |cc.ranges|
  }

  ghost predicate InClass(cc: CharClass, c: char)
  {
    RangesContain(cc.ranges, c)
  }

  function ClassEmpty(): (r: CharClass)
    ensures ClassValid(r) && (forall c :: !InClass(r, c))
  {
    CharClass([])
  }

  function ClassInsert(cc: CharClass, g: CRange): (res: CharClass)
    requires ClassValid(cc)
    ensures ClassValid(res) && (forall c :: InClass(res, c) <==> InClass(cc, c) || InRange(g, c))
  {
    if g.lo > g.hi then cc else CharClass(InsertRanges(cc.ranges, g))
  }

  // PROVIDED: the range-sequence decomposition fact, the one insertion uses.
  lemma RangesHead(rs: RangeSeq, c: char)
    requires |rs| > 0
    ensures RangesContain(rs, c) <==> InRange(rs[0], c) || RangesContain(rs[1..], c)
  {
    if RangesContain(rs, c) {
      var i :| 0 <= i < |rs| && InRange(rs[i], c);
      if i > 0 {
        assert InRange(rs[1..][i - 1], c);
      }
    }
    if RangesContain(rs[1..], c) {
      var i :| 0 <= i < |rs[1..]| && InRange(rs[1..][i], c);
      assert InRange(rs[i + 1], c);
    }
  }

  // item: R03.A1d
  method ClassIntersect(a: CharClass, b: CharClass) returns (r: CharClass)
    requires ClassValid(a) && ClassValid(b)
    ensures ClassValid(r) && (forall c :: InClass(r, c) <==> InClass(a, c) && InClass(b, c))
  {
    r := InterAll(a.ranges, b.ranges);
  }

  method ClassDiff(a: CharClass, b: CharClass) returns (r: CharClass)
    requires ClassValid(a) && ClassValid(b)
    ensures ClassValid(r) && (forall c :: InClass(r, c) <==> InClass(a, c) && !InClass(b, c))
  {
    r := DiffAll(a, b.ranges);
  }

  /* ADVERSARIAL REVIEW — learner-owned, 30 minutes after the delivery.
     Check totality on valid inputs, including empty and equal classes; identify
     what the public postconditions let an independent client prove. Inspect
     the code boundaries (0, the largest u32), adjacent ranges, a range across
     the surrogate block, and every strict comparison before a `- 1` or `+ 1`.
     Do not replace a proof with passing examples. Record diff, snapshot/freeze,
     gate, audit and transcript.

     AGENT DASHBOARD — learner-owned:
     goal / changed files / remaining obligations / gate summary / audit and
     freeze result / transcript / adversarial review / correction: ...
  */

  // The clearly marked reference implementation below answers the agentic file.

  // The chars of `acc`, plus those of `g` that lie in some range of `b`.
  function InterRow(g: CRange, b: RangeSeq, acc: CharClass): (r: CharClass)
    requires RangesValid(b) && ClassValid(acc)
    ensures ClassValid(r) && (forall c :: InClass(r, c) <==> InClass(acc, c) || (InRange(g, c) && RangesContain(b, c)))
    decreases |b|
  {
    if b == [] then
      acc
    else
      var h := b[0];
      var small := CRange(MaxCp(g.lo, h.lo), MinCp(g.hi, h.hi));
      var step := ClassInsert(acc, small);
      var r := InterRow(g, b[1..], step);
      assert forall c :: InClass(r, c) <==> InClass(acc, c) || (InRange(g, c) && RangesContain(b, c)) by {
        forall c
          ensures InClass(r, c) <==> InClass(acc, c) || (InRange(g, c) && RangesContain(b, c))
        {
          RangesHead(b, c);
        }
      }
      r
  }

  function InterAll(a: RangeSeq, b: RangeSeq): (r: CharClass)
    requires RangesValid(a) && RangesValid(b)
    ensures ClassValid(r) && (forall c :: InClass(r, c) <==> RangesContain(a, c) && RangesContain(b, c))
    decreases |a|
  {
    if a == [] then
      ClassEmpty()
    else
      var tail := InterAll(a[1..], b);
      var r := InterRow(a[0], b, tail);
      assert forall c :: InClass(r, c) <==> RangesContain(a, c) && RangesContain(b, c) by {
        forall c
          ensures InClass(r, c) <==> RangesContain(a, c) && RangesContain(b, c)
        {
          RangesHead(a, c);
        }
      }
      r
  }

  // The chars of `a` outside `g`: each range of `a` that meets `g` keeps its
  // part below `g.lo` and its part above `g.hi`, in codes (no char is built).
  function DiffOne(a: RangeSeq, g: CRange): (r: CharClass)
    requires RangesValid(a)
    ensures ClassValid(r) && (forall c :: InClass(r, c) <==> RangesContain(a, c) && !InRange(g, c))
    decreases |a|
  {
    if a == [] then
      ClassEmpty()
    else
      var tail := DiffOne(a[1..], g);
      var h := a[0];
      var r :=
        if g.lo > g.hi || h.hi < g.lo || g.hi < h.lo then
          ClassInsert(tail, h)
        else
          var left := if h.lo < g.lo then ClassInsert(tail, CRange(h.lo, g.lo - 1)) else tail;
          if g.hi < h.hi then ClassInsert(left, CRange(g.hi + 1, h.hi)) else left;
      assert forall c :: InClass(r, c) <==> RangesContain(a, c) && !InRange(g, c) by {
        forall c
          ensures InClass(r, c) <==> RangesContain(a, c) && !InRange(g, c)
        {
          RangesHead(a, c);
        }
      }
      r
  }

  function DiffAll(a: CharClass, b: RangeSeq): (r: CharClass)
    requires ClassValid(a) && RangesValid(b)
    ensures ClassValid(r) && (forall c :: InClass(r, c) <==> InClass(a, c) && !RangesContain(b, c))
    decreases |b|
  {
    if b == [] then
      a
    else
      var step := DiffOne(a.ranges, b[0]);
      var r := DiffAll(step, b[1..]);
      assert forall c :: InClass(r, c) <==> InClass(a, c) && !RangesContain(b, c) by {
        forall c
          ensures InClass(r, c) <==> InClass(a, c) && !RangesContain(b, c)
        {
          RangesHead(b, c);
        }
      }
      r
  }
}
