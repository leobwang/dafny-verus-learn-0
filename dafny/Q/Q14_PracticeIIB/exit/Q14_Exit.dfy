/*!
# Q14 — exit, Dafny half (closed book, timed)

Closed book: keep the chapter, the exercise files, later modules' files,
search tools and /tutor closed. At most the given spine (dafny/given/) may be
open.

This file ships with exactly 1 hole (X1, 20 minutes); the Verus exit file
(verus/q/q14_practice_iib/src/exit.rs) ships with none. Score it with

    scripts/firsttry.sh Q14 --exit

Threshold: the 1 exit item must pass. The first full run (the block
attempted) is the score; repair the block afterwards, after which the strict
gate covers this file too. Work it with `scripts/vcheck
dafny/Q/Q14_PracticeIIB/exit/Q14_Exit.dfy`. The unit's options apply:
automatic induction for lemmas is off.
*/
module Q14_Exit {

  // Given (not an item): b's limbs pushed onto the end of a, one at a time.
  function PushAll(b: seq<nat>, a: seq<nat>): seq<nat>
  {
    if |b| == 0 then a else PushAll(b[1..], a + [b[0]])
  }

  // item: Q14.X1d S7
  // need: lemma PushAllConcat(a: seq<nat>, b: seq<nat>)
  /** **X1.** Pushing every limb of `b` onto `a` gives `a + b`. Prove it:
      no skeleton; the lemma's measure is yours. */
  lemma PushAllConcat(a: seq<nat>, b: seq<nat>)
    ensures PushAll(b, a) == a + b
  // HOLE: this lemma has no body; write its measure and `{ … }` below the
  //    ensures line.
}
