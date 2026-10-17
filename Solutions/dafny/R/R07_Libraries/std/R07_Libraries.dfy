/*! R07 — Libraries: what they cost (Reference Solution).
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
 lemma {:induction false} ObservedAlphabetBound(xs: seq<char>)
  ensures |S.ToSet(xs)| <= |xs|
 { S.LemmaCardinalityOfSet(xs); }
  // item: R07.C5dv recognise:toolchain-mismatch
  // Read the pinned tool identity before interpreting a verifier result.
  // item: R07.P3dv verdict
  // Compare the two printed observed-alphabet contracts. D:<x>,<y> V:<x>,<y>.
  // CHECK P3dv
  // item: R07.P5dv verdict
  // The specimen prints the complete per-sample hypothesis. D:<v> V:<v>.
  // CHECK P5dv

  // item: R07.W1d
  lemma ObservedAlphabetEmpty(xs: seq<char>)
    ensures |S.ToSet(xs)| == 0 <==> |xs| == 0
  { S.LemmaCardinalityOfEmptySetIs0(xs); } // found-by: source

  // item: R07.W2d
  method ClassLookupFromAPI(cc: CharClass,c: char) returns (b: bool)
    ensures b <==> InClass(cc,c)
  { b := ClassMember(cc,c); }
  // item: R07.H1d
  // pair: R07.H1v
  // uses: library-call
 lemma {:induction false} FilteredSamplePrefix(cc: CharClass,xs: seq<char>,ys: seq<char>)
  requires |xs| <= |ys| && xs == ys[..|xs|]
  ensures |S.Filter(c => InClass(cc,c),xs)| <= |S.Filter(c => InClass(cc,c),ys)| &&
    S.Filter(c => InClass(cc,c),xs) == S.Filter(c => InClass(cc,c),ys)[..|S.Filter(c => InClass(cc,c),xs)|]
 {
  assert ys == xs + ys[|xs|..];
  S.LemmaFilterDistributesOverConcat(c => InClass(cc,c),xs,ys[|xs|..]);
 }
  // item: R07.H2d
  // pair: R07.H2v
  // uses: library-call
 lemma {:induction false} FilteredAlphabetExact(cc: CharClass,xs: seq<char>)
  ensures S.HasNoDuplicates(S.Filter(c => InClass(cc,c),xs)) <==> |S.ToSet(S.Filter(c => InClass(cc,c),xs))| == |S.Filter(c => InClass(cc,c),xs)|
 {
  var filtered := S.Filter(c => InClass(cc,c),xs);
  if S.HasNoDuplicates(filtered) { S.LemmaCardinalityOfSetNoDuplicates(filtered); }
  if |S.ToSet(filtered)| == |filtered| { S.LemmaNoDuplicatesCardinalityOfSet(filtered); }
 }
  // item: R07.H3d
  // pair: R07.H3v
  // uses: library-call
 lemma {:induction false} SampleBatchBound(blocks: seq<seq<char>>,limit: nat)
  requires forall i :: 0 <= i < |blocks| ==> |blocks[i]| <= limit
  ensures |S.Flatten(blocks)| <= |blocks|*limit
 {
  S.LemmaFlattenLengthLeMul(blocks,limit);
  S.LemmaFlattenAndFlattenReverseAreEquivalent(blocks);
 }
}
