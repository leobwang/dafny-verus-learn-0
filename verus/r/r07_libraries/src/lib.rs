/*! R07 — Libraries: what they cost (Exercises).
Standalone R, frozen A1/A1b/A2 only; no earlier learner file is imported.
Six holes in this Verus file: closed-book T1 and H1-H5. Five predictions precede
reading and all worked material. Record first tries before enabling switches.
Search then name: retain exact qualified symbols, instantiated arguments and
found-by notes. Read preconditions; scope a broadcast only after named calls.
Use the pinned wrapper and std/all tiers; no local solver or tool overrides.
Done: full zero-hole gates, clean audits, freeze, strict report, written card,
trust/mismatch activities, synthetic pass@k, learner-written EVAL R-v0,
retriever-race review, sixth bench card and viva. Deferred live runs are debt.
*/
use vstd::prelude::*;
use vstd::seq_lib::*;
use rg_re_a2::char_class::CharClass;
verus! {
  // item: R07.T1v
  // pair: R07.T1d
  // uses: library-call
proof fn lemma_observed_alphabet_bound(xs: Seq<char>)
 ensures xs.to_set().len() <= xs.len(),
{ #[verifier::proof_note("R07.T1v")] assume(false); }
// item: R07.W1v
proof fn lemma_observed_alphabet_empty(xs: Seq<char>)
    ensures xs.to_set().len() == 0 <==> xs.len() == 0,
{ xs.lemma_cardinality_of_empty_set_is_0(); } // found-by: source

// item: R07.W2v
fn class_lookup_from_api(cc: &CharClass,c: char) -> (b: bool)
    ensures b == cc@.contains(c),
{ cc.class_member(c) }
// item: R07.W3v
proof fn filter_map_origin_named(xs: Seq<char>,f: spec_fn(char)->Option<char>,out:char)
 requires xs.filter_map(f).contains(out),
 ensures exists|c:char| xs.contains(c) && f(c) == Some(out),
{ xs.lemma_filter_map_contains(f,out); }
// item: R07.W4v
proof fn filter_map_step_named(xs: Seq<char>,f:spec_fn(char)->Option<char>,i:int)
 requires 0 <= i < xs.len(),
 ensures xs[..i+1].filter_map(f) == xs[..i].filter_map(f)+(match f(xs[i]) { Some(c)=>seq![c],None=>Seq::empty() }),
{ xs.lemma_filter_map_take_succ(f,i); }
  // item: R07.H1v
  // pair: R07.H1d
  // uses: library-call
proof fn lemma_filtered_sample_prefix(cc: &CharClass,xs: Seq<char>,ys: Seq<char>)
 requires xs.is_prefix_of(ys),
 ensures xs.filter(|c: char| cc@.contains(c)).is_prefix_of(ys.filter(|c: char| cc@.contains(c))),
 { #[verifier::proof_note("R07.H1v")] assume(false); }
  // item: R07.H2v
  // pair: R07.H2d
  // uses: library-call
proof fn lemma_filtered_alphabet_exact(cc: &CharClass,xs: Seq<char>)
 ensures xs.filter(|c: char| cc@.contains(c)).no_duplicates() == (xs.filter(|c: char| cc@.contains(c)).to_set().len() == xs.filter(|c: char| cc@.contains(c)).len()),
{ #[verifier::proof_note("R07.H2v")] assume(false); }
  // item: R07.H3v
  // pair: R07.H3d
  // uses: library-call
proof fn lemma_sample_batch_bound(blocks: Seq<Seq<char>>,limit: nat)
 requires forall|i:int| 0 <= i < blocks.len() ==> (#[trigger] blocks[i]).len() <= limit,
 ensures blocks.flatten().len() <= blocks.len()*limit,
{ #[verifier::proof_note("R07.H3v")] assume(false); }
// item: R07.H4v
// uses: broadcast-use
proof fn filter_map_origin_scoped(xs: Seq<char>,f: spec_fn(char)->Option<char>,out:char)
 requires xs.filter_map(f).contains(out),
 ensures exists|c:char| xs.contains(c) && f(c) == Some(out),
{ #[verifier::proof_note("R07.H4v")] assume(false); }
// item: R07.H5v
// uses: broadcast-use
proof fn filter_map_step_scoped(xs: Seq<char>,f:spec_fn(char)->Option<char>,i:int)
 requires 0 <= i < xs.len(),
 ensures xs[..i+1].filter_map(f) == xs[..i].filter_map(f)+(match f(xs[i]) { Some(c)=>seq![c],None=>Seq::empty() }),
{ #[verifier::proof_note("R07.H5v")] assume(false); }
}
