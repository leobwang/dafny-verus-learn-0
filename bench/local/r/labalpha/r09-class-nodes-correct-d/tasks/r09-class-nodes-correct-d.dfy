// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["RangeNodesCorrectR09","ClassNodesCorrectR09"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.ClassNodesCorrectR09","start":75,"end":83}]
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

  // Provided definitions: RG_A2_Deriv (layer A2), code points and ranges, copied verbatim.
  newtype Cp = x: int | 0 <= x < 0x1_0000_0000

  datatype CRange = CRange(lo: Cp, hi: Cp)

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

  // The task (R09 ClassNodesCorrectR09): the node count of a lowered range listing.
  lemma ClassNodesCorrectR09(xs: seq<CRange>)
    requires RangesLowered(xs)
    ensures NodeCount(RangesToRe(xs)) == ClassNodesR09(xs)
    decreases xs
  {
    if xs != [] {
      /*R12_CALLS:c1*/
    }
  }
}
