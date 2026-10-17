/*!
# Q02 — exit, Dafny half (closed book)

Closed during the exit: the chapter, the exercise files (dafny/Q/Q02_FirstSyntaxI/core,
verus/q/q02_first_syntax_i/src/lib.rs, the specimens), later modules' files, search tools
and /tutor. Open, at most: the given spine (dafny/given/Q/, verus/given/).

This file ships with exactly 1 hole (X3d); X1d and X2d are prompt-as-heading blocks that
ship empty, each with a commented check to uncomment. Its Verus half,
verus/q/q02_first_syntax_i/src/exit.rs, ships with 3 holes (X1v, X2v, X3v). Neither file
is in any build.

Score: `scripts/firsttry.sh Q02 --exit` judges every block of both files, each on its own,
and records the first run on which every block holds an attempt (a guess counts; an empty
block or a hole does not). The threshold is 5 of the 6 blocks. That first run is the score;
repair every block afterwards, and from then on the strict gate covers this file too.
A block passes when it is attempted and has no error, no hole, no commented check, and
every `need:` line of its marker in its code.
*/
module Q02_Exit {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat

  // item: Q02.X1d S4
  // uses: decreases
  // need: function Upto(i: nat, n: nat): seq<nat>
  // need: lemma UptoCheck() ensures Upto(2, 5) == [2, 3, 4]
  // ### X1d · S4 — Write `function Upto(i: nat, n: nat): seq<nat>`, which returns
  //    `[i, i + 1, …, n - 1]` (empty when `i >= n`), by recursion that counts `i` up. Then
  //    uncomment the check.

  // Uncomment as you go:
  // lemma UptoCheck() ensures Upto(2, 5) == [2, 3, 4] {}

  // item: Q02.X2d S6
  // uses: frame, quantified-ensures
  // need: method ZeroAt(a: array<nat>, i: nat)
  // need: ZeroAt(a, 1); assert a[0] == 7 && a[1] == 0 && a[2] == 7;
  // ### X2d · S6 — Write `method ZeroAt(a: array<nat>, i: nat)`, which sets `a[i]` to 0 when
  //    `i < a.Length`, with what Dafny needs to accept the write and a postcondition that
  //    lets the check verify. Then uncomment the check.

  // Uncomment as you go:
  // method ZeroAtCheck() {
  //   var a := new nat[3](_ => 7);
  //   ZeroAt(a, 1);
  //   assert a[0] == 7 && a[1] == 0 && a[2] == 7;
  // }

  // item: Q02.X3d S3
  // uses: assert-by
  // need: lemma ToNatDropTwoZeros(s: seq<nat>)
  // need: ensures ToNat(s[..|s| - 2]) == ToNat(s)
  /** **X3d.** Dropping the two most significant limbs, both zero, keeps the value. Prove
      it with one `assert … by` per dropped limb. */
  lemma ToNatDropTwoZeros(s: seq<nat>)
    requires |s| >= 2 && s[|s| - 1] == 0 && s[|s| - 2] == 0
    ensures ToNat(s[..|s| - 2]) == ToNat(s)
  // HOLE: give this lemma a body.
}
