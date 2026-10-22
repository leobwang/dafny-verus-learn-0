// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["ClassNodesCorrectR09"]},{"name":"c2","kind":"calls","callees":["LoweringNodesCorrectR09"]},{"name":"c3","kind":"calls","callees":["LoweringNodesCorrectR09"]},{"name":"c4","kind":"calls","callees":["LoweringNodesCorrectR09"]},{"name":"c5","kind":"calls","callees":["LoweringNodesCorrectR09"]},{"name":"c6","kind":"calls","callees":["LoweringNodesCorrectR09"]},{"name":"c7","kind":"calls","callees":["LoweringNodesCorrectR09"]},{"name":"c8","kind":"calls","callees":["LoweringNodesCorrectR09","CopiesNodesR09","OptionalNodesR09"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.LoweringNodesCorrectR09","start":224,"end":248}]
module R12_LabCase {
  // Provided definitions: RG_A1_Re (layer A1), copied verbatim.
  datatype Re = Empty | Eps | Chr(c: char) | Alt(a: Re, b: Re) | Cat(a: Re, b: Re) | Star(r: Re)

  function NodeCount(r: Re): nat
    decreases r
  {
    match r
    case Empty => 1
    case Eps => 1
    case Chr(_) => 1
    case Alt(a, b) => 1 + NodeCount(a) + NodeCount(b)
    case Cat(a, b) => 1 + NodeCount(a) + NodeCount(b)
    case Star(a) => 1 + NodeCount(a)
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

  // Provided definitions: RG_A2_Deriv (layer A2), code points and ranges, copied verbatim.
  newtype Cp = x: int | 0 <= x < 0x1_0000_0000

  datatype CRange = CRange(lo: Cp, hi: Cp)

  // Every range is non-empty; ranges are sorted and separated by at least one code.
  predicate RangesValid(rs: seq<CRange>)
  {
    (forall i | 0 <= i < |rs| :: rs[i].lo <= rs[i].hi) &&
    (forall i, j | 0 <= i < j < |rs| :: rs[i].hi as int + 1 < rs[j].lo as int)
  }

  datatype CharClass = CharClass(ranges: seq<CRange>)

  predicate ClassValid(cc: CharClass)
  {
    RangesValid(cc.ranges)
  }

  // The read-only range accessor (for A3's lowering and size accounting).
  function ClassRanges(cc: CharClass): seq<CRange>
  {
    cc.ranges
  }

  // Provided definitions: RG_A3_Syntax (layer A3), classes as regexes, copied verbatim.
  const ClassMax: int := 0xD800

  predicate RangesLowered(rs: seq<CRange>)
  {
    forall i | 0 <= i < |rs| :: rs[i].lo <= rs[i].hi && (rs[i].hi as int) < ClassMax
  }

  function RangeRe(lo: Cp, hi: Cp): Re
    requires lo <= hi && (hi as int) < ClassMax
    decreases hi as int - lo as int
  {
    if lo == hi then Chr(lo as int as char) else Alt(Chr(lo as int as char), RangeRe(lo + 1, hi))
  }

  function RangesToRe(rs: seq<CRange>): Re
    requires RangesLowered(rs)
    decreases rs
  {
    if rs == [] then Empty else Alt(RangeRe(rs[0].lo, rs[0].hi), RangesToRe(rs[1..]))
  }

  // A class lowers when its listing (read through A2's accessor) does.
  predicate ClassLowered(cc: CharClass)
  {
    RangesLowered(ClassRanges(cc))
  }

  function ClassToRe(cc: CharClass): Re
    requires ClassLowered(cc)
  {
    RangesToRe(ClassRanges(cc))
  }

  // Bounds of a counted repetition are single characters '0'..'9'.
  const MaxBound: nat := 9

  // Every node carries its source span [lo, hi).
  datatype Syn =
    | SEps(lo: nat, hi: nat)
    | SChr(c: char, lo: nat, hi: nat)
    | SClass(cc: CharClass, lo: nat, hi: nat)
    | SAlt(a: Syn, b: Syn, lo: nat, hi: nat)
    | SCat(a: Syn, b: Syn, lo: nat, hi: nat)
    | SStar(a: Syn, lo: nat, hi: nat)
    | SPlus(a: Syn, lo: nat, hi: nat)
    | SOpt(a: Syn, lo: nat, hi: nat)
    | SRep(a: Syn, n: nat, m: nat, lo: nat, hi: nat)
    | SGroup(a: Syn, lo: nat, hi: nat)

  // Spans nest: children lie inside the parent, in source order.
  predicate WF(t: Syn, len: nat)
    decreases t, len
  {
    t.lo <= t.hi <= len &&
    match t
    case SEps(lo, hi) => lo == hi
    case SChr(_, lo, hi) => lo < hi
    case SClass(cc, lo, hi) => lo < hi && ClassValid(cc) && ClassLowered(cc)
    case SAlt(a, b, lo, hi) => WF(a, len) && WF(b, len) && a.lo == lo && a.hi < b.lo && b.hi == hi
    case SCat(a, b, lo, hi) => WF(a, len) && WF(b, len) && a.lo == lo && a.hi == b.lo && b.hi == hi
    case SStar(a, lo, hi) => WF(a, len) && a.lo == lo && a.hi < hi
    case SPlus(a, lo, hi) => WF(a, len) && a.lo == lo && a.hi < hi
    case SOpt(a, lo, hi) => WF(a, len) && a.lo == lo && a.hi < hi
    case SRep(a, n, m, lo, hi) => WF(a, len) && a.lo == lo && a.hi < hi && n <= m <= MaxBound
    case SGroup(a, lo, hi) => WF(a, len) && lo < a.lo && a.hi < hi
  }

  function Lower(t: Syn, len: nat): Re
    requires WF(t, len)
    decreases t, len
  {
    match t
    case SEps(_, _) => Eps
    case SChr(c, _, _) => Chr(c)
    case SClass(cc, _, _) => ClassToRe(cc)
    case SAlt(a, b, _, _) => Alt(Lower(a, len), Lower(b, len))
    case SCat(a, b, _, _) => Cat(Lower(a, len), Lower(b, len))
    case SStar(a, _, _) => Star(Lower(a, len))
    case SPlus(a, _, _) => Cat(Lower(a, len), Star(Lower(a, len)))
    case SOpt(a, _, _) => Alt(Eps, Lower(a, len))
    case SRep(a, n, m, _, _) => RepRange(Lower(a, len), n, m)
    case SGroup(a, _, _) => Lower(a, len)
  }

  // Provided definitions: R09's size model (R09_Size), copied verbatim.
  ghost function RangeNodesR09(lo: Cp, hi: Cp): nat
    requires lo <= hi && (hi as int) < ClassMax
  {
    2 * ((hi as int) - (lo as int)) + 1
  }

  ghost function ClassNodesR09(xs: seq<CRange>): nat
    requires RangesLowered(xs)
    decreases xs
  {
    if xs == [] then 1 else 1 + RangeNodesR09(xs[0].lo, xs[0].hi) + ClassNodesR09(xs[1..])
  }

  ghost function LoweringNodesR09(t:Syn,len:nat):nat
    requires WF(t,len)
    decreases t
  {
    match t
    case SEps(_,_) => 1
    case SChr(_,_,_) => 1
    case SClass(cc,_,_) => ClassNodesR09(ClassRanges(cc))
    case SAlt(a,b,_,_) => 1+LoweringNodesR09(a,len)+LoweringNodesR09(b,len)
    case SCat(a,b,_,_) => 1+LoweringNodesR09(a,len)+LoweringNodesR09(b,len)
    case SStar(a,_,_) => 1+LoweringNodesR09(a,len)
    case SPlus(a,_,_) => 2+2*LoweringNodesR09(a,len)
    case SOpt(a,_,_) => 2+LoweringNodesR09(a,len)
    case SGroup(a,_,_) => LoweringNodesR09(a,len)
    case SRep(a,n,m,_,_) => RepNodesR09(LoweringNodesR09(a,len),n,m)
  }

  // The logical size of a counted repetition whose child has c nodes.
  ghost function RepNodesR09(c: nat, n: nat, m: nat): nat
    requires n <= m
  {
    3 + n * (c + 1) + (m - n) * (c + 3)
  }

  // Provided fact (R09 reference RangeNodesCorrectR09), complete.
  lemma RangeNodesCorrectR09(lo: Cp, hi: Cp)
    requires lo <= hi && (hi as int) < ClassMax
    ensures NodeCount(RangeRe(lo, hi)) == RangeNodesR09(lo, hi)
    decreases hi as int - lo as int
  {
    if lo < hi {
      RangeNodesCorrectR09(lo + 1, hi);
    }
  }

  // Provided facts (R09 reference CopiesNodesR09, OptionalNodesR09, ClassNodesCorrectR09), complete.
  lemma CopiesNodesR09(r:Re,k:nat)
    ensures NodeCount(Copies(r,k))==1+k*(NodeCount(r)+1)
    decreases k
  {if k>0 {CopiesNodesR09(r,k-1);}}

  lemma OptionalNodesR09(r:Re,k:nat)
    ensures NodeCount(CopiesUpTo(r,k))==1+k*(NodeCount(r)+3)
    decreases k
  {if k>0 {OptionalNodesR09(r,k-1);}}

  lemma ClassNodesCorrectR09(xs: seq<CRange>)
    requires RangesLowered(xs)
    ensures NodeCount(RangesToRe(xs)) == ClassNodesR09(xs)
    decreases xs
  {
    if xs != [] {
      RangeNodesCorrectR09(xs[0].lo, xs[0].hi);
      ClassNodesCorrectR09(xs[1..]);
    }
  }

  // The task (R09 LoweringNodesCorrectR09): the logical size model counts the lowered regex.
  lemma LoweringNodesCorrectR09(t: Syn, len: nat)
    requires WF(t, len)
    ensures NodeCount(Lower(t, len)) == LoweringNodesR09(t, len)
    decreases t
  {
    match t
    case SEps(_,_) =>
    case SChr(_,_,_) =>
    case SClass(cc,_,_) =>
      /*R12_CALLS:c1*/
    case SAlt(a,b,_,_) =>
      /*R12_CALLS:c2*/
    case SCat(a,b,_,_) =>
      /*R12_CALLS:c3*/
    case SStar(a,_,_) =>
      /*R12_CALLS:c4*/
    case SPlus(a,_,_) =>
      /*R12_CALLS:c5*/
    case SOpt(a,_,_) =>
      /*R12_CALLS:c6*/
    case SGroup(a,_,_) =>
      /*R12_CALLS:c7*/
    case SRep(a,n,m,_,_) =>
      /*R12_CALLS:c8*/
  }
}
