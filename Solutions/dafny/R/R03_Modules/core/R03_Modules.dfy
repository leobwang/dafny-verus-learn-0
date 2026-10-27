/*! R03 — Modules and APIs (Reference Solution).
Class ranges are u32 code-point pairs (D48); a range's view is the set of chars whose
code lies in it, and the only conversion is a char to its code.
Standalone R; its generated unit includes only A1. The class API is local here;
the later A2 layer is not imported. No earlier learner file is needed.
Four predictions: P1d/P2v in specimens/R03 and P3dv/P4dv in slots/R03.slots.
Commit and record all four before scenarios, demos, plans, expected output or CI.
Five holes in this file; seven hole items in Verus (11 counted holes there as
shipped, with four GATED attributes). A green loop with holes is unfinished.
Done: both native gates have zero counted holes, audits and specfreeze are clean,
firsttry's strict report is OK, and the API/agent/written/card work is reviewed.
Preserve the given contracts, code and export boundary. Add provides entries
for the API definitions you complete; do not reveal the representation.
*/
module R03_Modules {
  // specfreeze: frozen-imports
  // item: R03.P3dv verdict
  /** A separate API exports ClassSingle and InClass with provides only.
      ClassSingle promises only that its result is valid. An external client
      asserts InClass(ClassSingle('b'), 'b'). Predict D:<v> V:<v>.
      v is ok, fail, timeout or err:<stage>. Commit before running its scenario. */
  // CHECK P3dv
  // item: R03.P4dv verdict
  /** The same scenario reveals the Dafny ClassSingle/InClass definitions;
      Verus opens the view/helpers but keeps the executable constructor's
      validity-only postcondition. Predict D:<v> V:<v> before running it. */
  // CHECK P4dv

  module CharClasses {
    // specfreeze: frozen-exports
    export provides CharClass, ClassValid, InClass, ClassEmpty, ClassInsert, ClassRank, ClassMember, ClassRange, ClassUnion
           reveals Cp, CRange, Code, InRange

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
    function {:isolate_assertions} InsertRanges(rs: RangeSeq, g: CRange): (res: RangeSeq)
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

    // item: R03.W2d
    /** PROVIDED: total insertion. A reversed input range contributes no member.
        The private merge above keeps the ranges sorted and separated. */
    opaque function ClassInsert(cc: CharClass, g: CRange): (res: CharClass)
      requires ClassValid(cc)
      ensures ClassValid(res) && (forall c :: InClass(res, c) <==> InClass(cc, c) || InRange(g, c))
    {
      if g.lo > g.hi then cc else CharClass(InsertRanges(cc.ranges, g))
    }

    // item: R03.H1d
    // uses: export
    // pair: R03.H1v
    // cfree: { false }
    /** **H1.** Membership: is `c` in one of the class's ranges?

        Reference: recursion on the list of ranges. The empty list holds
        nothing; otherwise `c` is in the first range or in the rest, and the
        recursive call on `CharClass(cc.ranges[1..])` answers the rest. The
        measure is `ClassRank`, the number of ranges. */
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

    // item: R03.H2d
    // uses: export
    // pair: R03.H2v
    // cfree: { ClassEmpty() }
    /** **H2.** The class of one inclusive char interval, as at most one range:
        total, no `requires`, and `hi < lo` gives the empty class.

        Reference: build the representation directly, `CharClass([CRange(Code(lo),
        Code(hi))])` when `lo <= hi` and `CharClass([])` otherwise. `ClassInsert` is
        opaque and promises nothing about the number of ranges. Membership needs
        the witness range 0 for each char of the interval (the char order is the
        code order). Add `ClassRange` to the export's `provides`. */
    function ClassRange(lo: char, hi: char): (r: CharClass)
      ensures ClassValid(r) && ClassRank(r) <= 1 && (forall c :: InClass(r, c) <==> lo <= c <= hi)
    {
      if lo <= hi then
        var r := CharClass([CRange(Code(lo), Code(hi))]);
        assert forall c :: InClass(r, c) <==> lo <= c <= hi by {
          forall c
            ensures InClass(r, c) <==> lo <= c <= hi
          {
            if lo <= c <= hi {
              assert InRange(r.ranges[0], c);
            }
          }
        }
        r
      else
        CharClass([])
    }

    // item: R03.H3d
    // uses: export
    // pair: R03.H3v
    // cfree: { a }
    // cfree: { ClassEmpty() }
    /** **H3.** The union of two valid classes, built only from `ClassInsert`.

        Reference: recursion on `b`'s ranges. Insert `b`'s first range into
        `a`, then take the union with the rest of `b`. `ClassInsert`'s
        contract keeps the result valid and adds exactly that range's chars.
        The measure is `ClassRank(b)`. */
    function ClassUnion(a: CharClass, b: CharClass): (u: CharClass)
      requires ClassValid(a) && ClassValid(b)
      ensures ClassValid(u) && (forall c :: InClass(u, c) <==> InClass(a, c) || InClass(b, c))
      decreases ClassRank(b)
    {
      if b.ranges == [] then
        a
      else
        var a2 := ClassInsert(a, b.ranges[0]);
        var b2 := CharClass(b.ranges[1..]);
        ClassUnion(a2, b2)
    }
  }

  module Client {
    import opened CharClasses

    // item: R03.H4d
    // pair: R03.H4v
    /** **H4.** A client of the exported API only: the union of a sequence of
        classes.

        Reference: recursion on `cs`. The empty sequence gives `ClassEmpty()`;
        otherwise take the union of `cs[0]` with the union of `cs[1..]`. Each
        direction of the membership then picks a witness: a class of `cs[1..]`
        for a char that is not in `cs[0]`, and the class `cs[i]` itself. */
    method UnionOfClasses(cs: seq<CharClass>) returns (u: CharClass)
      requires forall i | 0 <= i < |cs| :: ClassValid(cs[i])
      ensures ClassValid(u) && (forall x :: InClass(u, x) <==> exists i | 0 <= i < |cs| :: InClass(cs[i], x))
      decreases |cs|
    {
      // @hole-begin R03.H4d
      if |cs| == 0 {
        u := ClassEmpty();
      } else {
        var rest := UnionOfClasses(cs[1..]);
        u := ClassUnion(cs[0], rest);
        forall x | InClass(u, x)
          ensures exists i | 0 <= i < |cs| :: InClass(cs[i], x)
        {
          if !InClass(cs[0], x) {
            var j :| 0 <= j < |cs[1..]| && InClass(cs[1..][j], x);
          }
        }
        forall x | exists i | 0 <= i < |cs| :: InClass(cs[i], x)
          ensures InClass(u, x)
        {
          var i :| 0 <= i < |cs| && InClass(cs[i], x);
        }
      }
      // @hole-end R03.H4d
    }

    // item: R03.H5d
    // pair: R03.H5v
    // cfree: { ClassEmpty() }
    /** **H5.** The class of the characters of a string.

        Reference: recursion on the string. The empty string gives the empty
        class; otherwise insert the one-char range `CRange(Code(s[0]),
        Code(s[0]))` into the class of `s[1..]`. That `Code` is injective is
        what makes the one-char range hold exactly `s[0]`. */
    function ClassOfString(s: seq<char>): (r: CharClass)
      ensures ClassValid(r) && (forall c :: InClass(r, c) <==> c in s)
      decreases |s|
    {
      if |s| == 0 then
        ClassEmpty()
      else
        var tail := ClassOfString(s[1..]);
        ClassInsert(tail, CRange(Code(s[0]), Code(s[0])))
    }

    // The client checks: the API's contracts at concrete classes. The second
    // is the abstraction square: two representations (a split pair of ranges
    // and one range across the surrogate block, which is valid and adds no
    // char) with one view; a client can rely only on the view.
    // Reference checks (enabled):
    // reference-only: enabled shipped check
    method InterfaceChecks()
    {
      var a := ClassRange('a', 'c');
      assert ClassMember(a, 'b');
      var b := ClassOfString(['d']);
      var u := ClassUnion(a, b);
      assert ClassMember(u, 'd');
    }

    // reference-only: enabled shipped check
    method SurrogateSpanCheck()
    {
      var split := ClassInsert(ClassInsert(ClassEmpty(), CRange(0xD7FF, 0xD7FF)), CRange(0xE000, 0xE000));
      var span := ClassInsert(ClassEmpty(), CRange(0xD7FF, 0xE000));
      assert ClassMember(split, '\U{E000}');
      assert ClassMember(span, '\U{E000}');
      assert !ClassMember(span, 'a');
    }
    // end reference checks
  }

  // item: R03.W1d
  module SpanAPI {
    export provides SpanBox, SpanValid, SpanModel, MakeSpan, SpanHas
    datatype SpanBox = SpanBox(lo: char, hi: char)
    function SpanModel(s: SpanBox): (char, char)
    {
      (s.lo, s.hi)
    }
    predicate SpanValid(s: SpanBox)
    {
      s.lo <= s.hi
    }
    function MakeSpan(lo: char, hi: char): (s: SpanBox)
      requires lo <= hi
      ensures SpanValid(s) && SpanModel(s) == (lo, hi)
    {
      SpanBox(lo, hi)
    }
    function SpanHas(s: SpanBox, c: char): (b: bool)
      ensures b == (SpanModel(s).0 <= c <= SpanModel(s).1)
    {
      s.lo <= c <= s.hi
    }
  }
  module SpanClient {
    import opened SpanAPI
    lemma SpanContractExample() {
      var s := MakeSpan('a', 'd');
      assert SpanValid(s);
      assert SpanHas(s, 'c');
    }
  }

  // item: R03.C1d write:export
  // SpanAPI's provides exports names and contracts while keeping bodies hidden.
  // EXPECT: card-c1d.dfy.specimen fails in the client. Inspect its declared stage.
  // item: R03.C2d recognise:import
  // Client imports CharClasses opened; SpanClient imports the independent mini-API.
  // item: R03.C6d recognise:opaque
  opaque function SpanCode(c: char): int
  {
    c as int
  }

  /* API REVIEW — learner-owned, 15 minutes.
     Total on every valid input? Any hidden non-emptiness or unequal-input restriction?
     Enough information for clients? What remains hidden by provides and the view?
     Point to the actual contract, client and gate/audit evidence: ...
     CALIBRATION — estimate / actual / correction and its observation: ...
  */

  // item: R03.C8dv diverge:r03-c8
  // FINAL CARD — names, contracts, bodies and fields cross module boundaries differently.
  // Inspect the paired sealed divergence demos only after both predictions are recorded.
}
