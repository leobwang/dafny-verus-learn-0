/*! R06 checkpoint (Exercises) — CLOSED BOOK,22min.
Four items, two per language: pass at least3/4 with at least1 per language.
Open only for the checkpoint. Keep given definitions and statements fixed.
Record scripts/firsttry.sh R06 --exit; a later observed pass does not replace
the first exit record. No earlier learner file or hand-exercise proof imported.
*/
module R06_Checkpoint {
  import opened RG_A1_Re
  // GIVEN definitions, complete.
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
  function Derivs(r: Re, s: seq<char>): Re
    decreases |s|
  { if |s| == 0 then r else Derivs(Deriv(r, s[0]), s[1..]) }

  function SumNC(rs: seq<Re>): nat
    decreases |rs|
  { if |rs| == 0 then 0 else SumNC(rs[..|rs| - 1]) + NodeCount(rs[|rs| - 1]) }

  // item: R06.X1d
  // uses: lemma-decreases, induction-false
  /** **X1.** Budget 5.5 minutes. Prove the exact general statement, and
      write the measure its recursion needs. */
  lemma {:induction false} DerivsAppend(r: Re, u: seq<char>, v: seq<char>)
    ensures Derivs(r, u + v) == Derivs(Derivs(r, u), v)

  // item: R06.X2d
  // uses: invariant
  /** **X2.** Budget 5.5 minutes. Keep the given loop; supply its invariants
      and the facts that connect them. */
  method SumNodeCounts(rs: seq<Re>) returns (n: nat)
    ensures n == SumNC(rs)
  {
    assume false;

    n := 0;
    var i := 0;
    while i < |rs|
      decreases |rs| - i
    {
      n := n + NodeCount(rs[i]);
      i := i + 1;
    }
  }
}
