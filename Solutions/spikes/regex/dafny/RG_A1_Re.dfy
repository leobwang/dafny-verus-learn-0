// DVR0 reference, layer A1 (author-only; Solutions/spikes/regex/dafny).
// Ships as dafny/given/R/RG_A1_Re.dfy (PLAN §2.2, §2.5 step 1): definitions only.
// No lemma lives here: every lemma about these definitions is a module hole
// (RX_R02.dfy, RG_A1b_Facts.dfy) or the R06 decomposer's (RX_R06_Decomp.dfy).
module RG_A1_Re {
  datatype Re = Empty | Eps | Chr(c: char) | Alt(a: Re, b: Re) | Cat(a: Re, b: Re) | Star(r: Re)

  // Whole-string semantics by splits. A Star iteration consumes a non-empty chunk.
  // Ghost, so no exec item can answer itself by calling it.
  ghost predicate Matches(r: Re, s: seq<char>)
    decreases r, |s|
  {
    match r
    case Empty => false
    case Eps => s == []
    case Chr(c) => s == [c]
    case Alt(a, b) => Matches(a, s) || Matches(b, s)
    case Cat(a, b) => exists i | 0 <= i <= |s| :: Matches(a, s[..i]) && Matches(b, s[i..])
    case Star(a) => s == [] || exists i | 0 < i <= |s| :: Matches(a, s[..i]) && Matches(Star(a), s[i..])
  }

  predicate Nullable(r: Re)
    decreases r
  {
    match r
    case Empty => false
    case Eps => true
    case Chr(_) => false
    case Alt(a, b) => Nullable(a) || Nullable(b)
    case Cat(a, b) => Nullable(a) && Nullable(b)
    case Star(_) => true
  }

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

  // The regex read backwards.
  function Backwards(r: Re): Re
    decreases r
  {
    match r
    case Empty => Empty
    case Eps => Eps
    case Chr(c) => Chr(c)
    case Alt(a, b) => Alt(Backwards(a), Backwards(b))
    case Cat(a, b) => Cat(Backwards(b), Backwards(a))
    case Star(a) => Star(Backwards(a))
  }

  // The string read backwards.
  function BackwardsStr(s: seq<char>): seq<char>
    decreases |s|
  {
    if s == [] then [] else BackwardsStr(s[1..]) + [s[0]]
  }
}
