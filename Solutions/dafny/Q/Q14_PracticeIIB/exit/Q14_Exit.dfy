/*!
# Q14 — exit, Dafny half (Reference Solution)

Hole-free reference for `dafny/Q/Q14_PracticeIIB/exit/Q14_Exit.dfy`
(author-only; never learner-visible). Same module, names, statements, item
markers and order as the exit file; the hole is proved. Silent under
`scripts/vcheck --ref`.
*/
module Q14_Exit {

  // Given (not an item): b's limbs pushed onto the end of a, one at a time.
  function PushAll(b: seq<nat>, a: seq<nat>): seq<nat>
  {
    if |b| == 0 then a else PushAll(b[1..], a + [b[0]])
  }

  // item: Q14.X1d S7
  // need: lemma PushAllConcat(a: seq<nat>, b: seq<nat>)
  /** **X1.** Pushing every limb of `b` onto `a` gives `a + b`.

      Reference: the recursion of `PushAll`, by hand, with the measure
      `|b|`: the default one (the parameters in order) does not decrease,
      because the first argument grows. One sequence identity regroups the
      concatenation. */
  lemma PushAllConcat(a: seq<nat>, b: seq<nat>)
    ensures PushAll(b, a) == a + b
    decreases |b|
  {
    if |b| > 0 {
      PushAllConcat(a + [b[0]], b[1..]);
      assert a + [b[0]] + b[1..] == a + b;
    }
  }
}
