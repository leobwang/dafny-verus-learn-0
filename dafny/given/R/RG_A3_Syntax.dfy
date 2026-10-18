/*! A3 syntax model (PROVIDED, frozen). R09–R16.
Do not open this file before R03 and R06 are done: it imports A2, which re-supplies
their answers, and its class lowering reads classes through R03's API. R09 is its
first module.
Surface syntax and nested scalar spans; finite single-character bounds.
Definitions and parser predicates only: no parser or lowering-correctness proof.
Classes follow the printed below-0xD800 grammar; other literals are scalars.
Class ranges are A2's u32 code-point ranges, read through A2's accessor ClassRanges.
*/
module RG_A3_Syntax {
  import opened RG_A1_Re
  import opened RG_A1b_Facts
  import opened RG_A2_Deriv

  // ---------------------------------------------------------------------------
  // Counted repetition
  // ---------------------------------------------------------------------------

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

  // ---------------------------------------------------------------------------
  // Classes as regexes (code points below the surrogate block)
  // ---------------------------------------------------------------------------

  // Classes lower only below 0xD800, where every code is a char.
  const ClassMax: int := 0xD800

  // A range listing that lowers: every range non-empty and below ClassMax.
  predicate RangesLowered(rs: seq<CRange>)
  {
    forall i | 0 <= i < |rs| :: rs[i].lo <= rs[i].hi && (rs[i].hi as int) < ClassMax
  }

  // A class lowers when its listing (read through A2's accessor) does.
  predicate ClassLowered(cc: CharClass)
  {
    RangesLowered(ClassRanges(cc))
  }

  // The one place a code becomes a char: lo < ClassMax, so lo is a char's code.
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

  function ClassToRe(cc: CharClass): Re
    requires ClassLowered(cc)
  {
    RangesToRe(ClassRanges(cc))
  }

  // ---------------------------------------------------------------------------
  // Concrete syntax with positions
  // ---------------------------------------------------------------------------

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

  // ---------------------------------------------------------------------------
  // The parser's specification
  // ---------------------------------------------------------------------------

  // A result, or an error at a position of the input.
  datatype Res<T> = Ok(value: T) | Err(pos: nat, msg: string)
  {
    predicate IsFailure() { Err? }
    function PropagateFailure<U>(): Res<U>
      requires Err?
    {
      Err(pos, msg)
    }
    function Extract(): T
      requires Ok?
    {
      value
    }
  }

  datatype PR = PR(t: Syn, j: nat)

  predicate Special(c: char)
  {
    c == '(' || c == ')' || c == '|' || c == '*' || c == '+' || c == '?' || c == '{' || c == '}'
    || c == '[' || c == ']' || c == '\\'
  }

  // No special character from i on.
  predicate NoSpecialFrom(s: seq<char>, i: nat)
  {
    forall k | i <= k < |s| :: !Special(s[k])
  }

  predicate Stop(s: seq<char>, j: nat)
    requires j <= |s|
  {
    j == |s| || s[j] == ')' || s[j] == '|'
  }

  // A repetition bound: one character '0'..'9', and its value.
  predicate BoundChar(c: char) { '0' <= c <= '9' }

  function BoundVal(c: char): nat
    requires BoundChar(c)
  {
    c as int - '0' as int
  }

  // s[j..k] spells the counted repetition {n} or {n,m}, n <= m.
  predicate CountedAt(s: seq<char>, j: nat, n: nat, m: nat, k: nat)
  {
    j < |s| && s[j] == '{' && k <= |s| &&
    ((k == j + 3 && BoundChar(s[j + 1]) && s[j + 2] == '}'
      && n == BoundVal(s[j + 1]) && m == n) ||
     (k == j + 5 && BoundChar(s[j + 1]) && s[j + 2] == ',' && BoundChar(s[j + 3]) && s[j + 4] == '}'
      && n == BoundVal(s[j + 1]) && m == BoundVal(s[j + 3]) && n <= m))
  }

  // s[i..k] is a class body of single characters (no ']', '\\' or '-', each below ClassMax),
  // closed by the ']' at k.
  predicate SimpleClassBody(s: seq<char>, i: nat, k: nat)
  {
    i <= k < |s| && s[k] == ']' &&
    forall q | i <= q < k :: s[q] != ']' && s[q] != '\\' && s[q] != '-' && (s[q] as int) < ClassMax
  }
}
