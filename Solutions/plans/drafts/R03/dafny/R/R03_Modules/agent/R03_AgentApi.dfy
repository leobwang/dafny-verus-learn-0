/* CONTRACT
goal: implement ClassIntersect and ClassDiff on every valid input, preserving the stated membership semantics and validity
allowed-files:
  - dafny/R/R03_Modules/agent/R03_AgentApi.dfy
acceptance:
  - scripts/vcheck --gate dafny/R/R03_Modules/agent/R03_AgentApi.dfy exits0, zero counted holes
  - scripts/specfreeze --against <snapshot> dafny/R/R03_Modules/agent/R03_AgentApi.dfy reports all supplied statements unchanged
  - scripts/vaudit dafny/R/R03_Modules/agent/R03_AgentApi.dfy reports zero findings
  - preserve given code, representation and contracts; no new requires, weakened ensures, assumptions or escape hatches
  - only this file may change; private implementation helpers may be added
*/
/*! R03 API implementer, R-v0. Save the original file outside the delivery as
<snapshot> before /contract R03; record its hash and the exact allowed file.
A green verification loop with the two API holes is unfinished. The gate must
have zero holes. Review empty/equal inputs and Unicode character boundaries.
*/
module R03_AgentApi {
    datatype CRange = CRange(lo: char, hi: char)
    datatype CharClass = CharClass(ranges: seq<CRange>)
    type RangeSeq = seq<CRange>

predicate InRange(g: CRange, c: char) { g.lo <= c <= g.hi }

ghost predicate RangesContain(cc: RangeSeq, c: char)
  {
    exists i | 0 <= i < |cc| :: InRange(cc[i], c)
  }

predicate RangesValid(cc: RangeSeq)
  {
    (forall i | 0 <= i < |cc| :: cc[i].lo <= cc[i].hi) &&
    (forall i, j | 0 <= i < j < |cc| :: cc[i].hi < cc[j].lo)
  }

function MinC(a: char, b: char): char { if a <= b then a else b }

function MaxC(a: char, b: char): char { if a <= b then b else a }

function InsertRanges(cc: RangeSeq, g: CRange): (res: RangeSeq)
    requires RangesValid(cc) && g.lo <= g.hi
    ensures RangesValid(res)
    ensures forall c :: RangesContain(res, c) <==> RangesContain(cc, c) || InRange(g, c)
    ensures forall k | 0 <= k < |res| :: res[k].lo >= (if cc == [] then g.lo else MinC(g.lo, cc[0].lo))
    decreases |cc|
  {
    if cc == [] then
      assert forall c :: RangesContain([g], c) <==> InRange(g, c) by {
        forall c ensures RangesContain([g], c) <==> InRange(g, c) {
          if InRange(g, c) { assert InRange([g][0], c); }
        }
      }
      [g]
    else
      var h := cc[0];
      var t := cc[1..];
      if g.hi < h.lo then
        var res := [g] + cc;
        assert forall c :: RangesContain(res, c) <==> InRange(g, c) || RangesContain(cc, c) by {
          forall c ensures RangesContain(res, c) <==> InRange(g, c) || RangesContain(cc, c) {
            if RangesContain(res, c) {
              var i :| 0 <= i < |res| && InRange(res[i], c);
              if i > 0 { assert InRange(cc[i - 1], c); }
            }
            if RangesContain(cc, c) {
              var i :| 0 <= i < |cc| && InRange(cc[i], c);
              assert InRange(res[i + 1], c);
            }
            if InRange(g, c) { assert InRange(res[0], c); }
          }
        }
        res
      else if h.hi < g.lo then
        var r2 := InsertRanges(t, g);
        var res := [h] + r2;
        assert forall c :: RangesContain(res, c) <==> InRange(h, c) || RangesContain(r2, c) by {
          forall c ensures RangesContain(res, c) <==> InRange(h, c) || RangesContain(r2, c) {
            if RangesContain(res, c) {
              var i :| 0 <= i < |res| && InRange(res[i], c);
              if i > 0 { assert InRange(r2[i - 1], c); }
            }
            if RangesContain(r2, c) {
              var i :| 0 <= i < |r2| && InRange(r2[i], c);
              assert InRange(res[i + 1], c);
            }
            if InRange(h, c) { assert InRange(res[0], c); }
          }
        }
        res
      else
        var g2 := CRange(MinC(g.lo, h.lo), MaxC(g.hi, h.hi));
        var res := InsertRanges(t, g2);
        res
  }

    predicate ClassValid(cc: CharClass) { RangesValid(cc.ranges) }
    ghost function ClassRank(cc: CharClass): nat { |cc.ranges| }
    ghost predicate InClass(cc: CharClass, c: char) { RangesContain(cc.ranges, c) }

    function ClassEmpty(): (r: CharClass)
      ensures ClassValid(r) && (forall c :: !InClass(r, c))
    { CharClass([]) }

    /** PROVIDED: total insertion. A reversed input range contributes no member.
        The private merge proof above preserves sorted, separated ranges. */
    function ClassInsert(cc: CharClass, g: CRange): (res: CharClass)
      requires ClassValid(cc)
      ensures ClassValid(res) && (forall c :: InClass(res, c) <==> InClass(cc, c) || InRange(g, c))
    { if g.lo > g.hi then cc else CharClass(InsertRanges(cc.ranges, g)) }


  // PROVIDED scalar-neighbour primitives. They skip the Unicode surrogate gap.
  // A caller needs a strict lower/upper bound before requesting a neighbour.
  function CharPrev(c: char): (p: char)
    requires c > '\0'
    ensures p < c && ((p as int) + 1 == (c as int) || (p == '\U{D7FF}' && c == '\U{E000}'))
  {
    var n := c as int;
    if n == 0xE000 then '\U{D7FF}' else (n - 1) as char
  }
  function CharNext(c: char): (p: char)
    requires c < '\U{10FFFF}'
    ensures c < p && ((c as int) + 1 == (p as int) || (c == '\U{D7FF}' && p == '\U{E000}'))
  {
    var n := c as int;
    if n == 0xD7FF then '\U{E000}' else (n + 1) as char
  }
  // PROVIDED range-sequence decomposition fact, the same fact used by insertion.
  lemma RangesHead(rs: RangeSeq, c: char)
    requires |rs| > 0
    ensures RangesContain(rs,c) <==> InRange(rs[0],c) || RangesContain(rs[1..],c)
  {
    if RangesContain(rs,c) {
      var i :| 0 <= i < |rs| && InRange(rs[i],c);
      if i > 0 { assert InRange(rs[1..][i-1],c); }
    }
    if RangesContain(rs[1..],c) {
      var i :| 0 <= i < |rs[1..]| && InRange(rs[1..][i],c);
      assert InRange(rs[i+1],c);
    }
    if InRange(rs[0],c) { assert InRange(rs[0],c); }
  }

  // item: R03.A1d
  method ClassIntersect(a: CharClass, b: CharClass) returns (r: CharClass)
    requires ClassValid(a) && ClassValid(b)
    ensures ClassValid(r) && (forall c :: InClass(r,c) <==> InClass(a,c) && InClass(b,c))
  { assume false; }

  method ClassDiff(a: CharClass, b: CharClass) returns (r: CharClass)
    requires ClassValid(a) && ClassValid(b)
    ensures ClassValid(r) && (forall c :: InClass(r,c) <==> InClass(a,c) && !InClass(b,c))
  { assume false; }

  /* ADVERSARIAL REVIEW — learner-owned, 30 minutes after the delivery.
     Check totality on valid inputs, including empty and equal classes; identify
     what the public postconditions let an independent client prove. Inspect
     the smallest/largest char and the surrogate-gap neighbours, and every
     strict comparison before a neighbour call. Do not replace a proof with
     passing examples. Record diff, snapshot/freeze, gate, audit and transcript.

     AGENT DASHBOARD — learner-owned:
     goal / changed files / remaining obligations / gate summary / audit and
     freeze result / transcript / adversarial review / correction: ...
  */
}
