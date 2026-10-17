/*!
# Q03 — exit, Dafny half (closed book)

Closed book: keep the chapter, the exercise files, later modules' files,
search tools and /tutor closed. At most the given spine (dafny/given/Q/) may
be open.

This file ships with exactly 2 holes (X1, X3) and one empty block (X2); the
Verus half (verus/q/q03_first_syntax_ii/src/exit.rs) ships with 3 holes. Score
both halves in one sitting with

    scripts/firsttry.sh Q03 --exit

Threshold: 5 of the 6 exit items. The first full run (every block attempted)
is the score; repair every block afterwards, after which the strict gate
covers this file too. This file is in no build: work it with
`scripts/vcheck dafny/Q/Q03_FirstSyntaxII/exit/Q03_Exit.dfy`.
*/
module Q03_Exit {

  // Given (not an item): the option type of X3.
  datatype Opt<T> = None | Some(value: T)

  // item: Q03.X1d S7
  // uses: ghost, witness
  // need: method FindAtLeast(s: seq<nat>, b: nat) returns (found: bool, ghost w: nat)
  // need: ensures found ==> w < |s| && s[w] >= b
  // need: ensures !found ==> forall j | 0 <= j < |s| :: s[j] < b
  // pair: Q03.X1v
  /** **X1.** Search `s` for a limb at least `b`. Return whether there is one,
      and, as a ghost out-parameter, the index of one when there is. */
  method FindAtLeast(s: seq<nat>, b: nat) returns (found: bool, ghost w: nat)
    ensures found ==> w < |s| && s[w] >= b
    ensures !found ==> forall j | 0 <= j < |s| :: s[j] < b
  {
    assume false;
  }

  // item: Q03.X2d S7
  // uses: subset-type, witness
  // need: type Odd
  // need: method OddCheck(o: Odd) { assert o % 2 == 1; }
  // ### X2 · S7 — Declare the subset type `Odd` of the odd naturals, with whatever Dafny needs to accept it; then uncomment the check below.
  // Uncomment as you go:
  // method OddCheck(o: Odd) { assert o % 2 == 1; }

  // item: Q03.X3d S7
  // uses: exec-check
  // need: method CheckedSub(a: nat, b: nat) returns (r: Opt<nat>)
  // need: ensures (r.Some? <==> b <= a) && (r.Some? ==> r.value + b == a)
  // pair: Q03.X3v
  /** **X3.** Checked subtraction on naturals: `Some(a - b)` when `b <= a`,
      `None` otherwise. */
  method CheckedSub(a: nat, b: nat) returns (r: Opt<nat>)
    ensures (r.Some? <==> b <= a) && (r.Some? ==> r.value + b == a)
  {
    assume false;
  }
}
