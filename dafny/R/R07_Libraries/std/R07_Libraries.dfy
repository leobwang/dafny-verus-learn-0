/*! R07 — Libraries: what they cost (Exercises).
Standalone R, frozen A1/A1b/A2 only; no earlier learner file is imported.
Four holes in this Dafny file: closed-book T1 and H1-H3. Five predictions precede
reading and all worked material. Record first tries before enabling switches.
Search then name: retain exact qualified symbols, instantiated arguments and
found-by notes. Read preconditions; scope a broadcast only after named calls.
Use the pinned wrapper and std/all tiers; no local solver or tool overrides.
Done: full zero-hole gates, clean audits, freeze, strict report, written card,
trust/mismatch activities, synthetic pass@k, learner-written EVAL R-v0,
retriever-race review, sixth bench card and viva. Deferred live runs are debt.
*/
module R07_Libraries {
  import opened RG_A2_Deriv
  import S = Std.Collections.Seq

  // item: R07.T1d
  // pair: R07.T1v
  // uses: library-call
  // gate: named-calls
  /** **T1.** Closed book, before reading: the observed alphabet of a sample
      is no larger than the sample. Name the `Std.Collections.Seq` lemma that
      bounds the cardinality of `S.ToSet(xs)`. Which of the library's
      cardinality lemmas is about `ToSet` and length? */
  lemma {:induction false} ObservedAlphabetBound(xs: seq<char>)
    ensures |S.ToSet(xs)| <= |xs|

  // item: R07.C5dv recognise:toolchain-mismatch
  // Read the pinned tool identity before interpreting a verifier result.
  // item: R07.P3dv verdict
  // Compare the two printed observed-alphabet contracts. D:<x>,<y> V:<x>,<y>.
  // SLOT: CHECK P3dv
  // item: R07.P5dv verdict
  // The specimen prints the complete per-sample hypothesis. D:<v> V:<v>.
  // SLOT: CHECK P5dv

  // ===========================================================================
  // Worked examples
  // ===========================================================================

  // item: R07.W1d
  /** A library lemma called by its qualified name, with a found-by note
      saying how it was found. */
  lemma ObservedAlphabetEmpty(xs: seq<char>)
    ensures |S.ToSet(xs)| == 0 <==> |xs| == 0
  {
    S.LemmaCardinalityOfEmptySetIs0(xs); // found-by: source
  }

  // item: R07.W2d
  /** A2's class API used through its interface: `ClassMember` decides
      `InClass`. */
  method ClassLookupFromAPI(cc: CharClass, c: char) returns (b: bool)
    ensures b <==> InClass(cc, c)
  {
    b := ClassMember(cc, c);
  }

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: R07.H1d
  // pair: R07.H1v
  // uses: library-call
  // gate: named-calls
  /** **H1.** Filtering keeps prefixes: if `xs` is a prefix of `ys`, the
      class-filtered `xs` is a prefix of the class-filtered `ys`. Which library
      lemma relates the filter of a concatenation to the filters of its parts,
      and how do you first write `ys` as a concatenation with `xs` in front? */
  lemma {:induction false} FilteredSamplePrefix(cc: CharClass, xs: seq<char>, ys: seq<char>)
    requires |xs| <= |ys| && xs == ys[..|xs|]
    ensures |S.Filter(c => InClass(cc, c), xs)| <= |S.Filter(c => InClass(cc, c), ys)| &&
      S.Filter(c => InClass(cc, c), xs) == S.Filter(c => InClass(cc, c), ys)[..|S.Filter(c => InClass(cc, c), xs)|]
  // Hint(1): search `Std.Collections.Seq` for lemmas whose names mention both
  //    `Filter` and `Concat`; read the precondition and the argument order.
  // Hint(2): the library speaks about `a + b`; state that `ys` is
  //    `xs + ys[|xs|..]` before the call, so its conclusion is about `ys`.

  // item: R07.H2d
  // pair: R07.H2v
  // uses: library-call
  // gate: named-calls
  /** **H2.** A filtered sample has no duplicates exactly when its set is as
      large as the sequence. The library proves each direction separately.
      Which two lemmas, and under which hypothesis is each one called? */
  lemma {:induction false} FilteredAlphabetExact(cc: CharClass, xs: seq<char>)
    ensures S.HasNoDuplicates(S.Filter(c => InClass(cc, c), xs)) <==> |S.ToSet(S.Filter(c => InClass(cc, c), xs))| == |S.Filter(c => InClass(cc, c), xs)|
  // Hint(1): a `<==>` is two implications; each library lemma has the left
  //    side of one of them as its `requires`.
  // Hint(2): search the library for `NoDuplicates` together with
  //    `Cardinality`; call each lemma only where its precondition holds.

  // item: R07.H3d
  // pair: R07.H3v
  // uses: library-call
  // gate: named-calls
  /** **H3.** A batch of samples, each at most `limit` long, flattens to at most
      `|blocks| * limit` characters. The library's bound is stated for a
      different flattening function. Which lemma gives the bound, and which
      one says the two flattenings agree? */
  lemma {:induction false} SampleBatchBound(blocks: seq<seq<char>>, limit: nat)
    requires forall i :: 0 <= i < |blocks| ==> |blocks[i]| <= limit
    ensures |S.Flatten(blocks)| <= |blocks| * limit
  // Hint(1): read the bound lemma's `ensures`: which flattening does it
  //    mention, `Flatten` or `FlattenReverse`?
  // Hint(2): the library also relates the two flattenings; call that lemma
  //    too, so the bound reaches `S.Flatten(blocks)`.
}
