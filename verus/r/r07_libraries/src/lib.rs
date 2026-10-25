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
// gate: named-calls
/// **T1.** Closed book, before reading: the observed alphabet of a sample is
/// no larger than the sample. Name the `vstd` method that bounds the length of
/// `xs.to_set()`. Which of `Seq`'s cardinality lemmas is about `to_set` and
/// `len`?
proof fn lemma_observed_alphabet_bound(xs: Seq<char>)
    ensures
        xs.to_set().len() <= xs.len(),
{
    #[verifier::proof_note("R07.T1v")] assume(false);  // HOLE
}

// ===========================================================================
// Worked examples
// ===========================================================================

// item: R07.W1v
/// A library lemma called by name on its receiver, with a found-by note.
proof fn lemma_observed_alphabet_empty(xs: Seq<char>)
    ensures
        xs.to_set().len() == 0 <==> xs.len() == 0,
{
    xs.lemma_cardinality_of_empty_set_is_0();  // found-by: source
}

// item: R07.W2v
/// A2's class API used through its interface: `class_member` decides the view.
fn class_lookup_from_api(cc: &CharClass, c: char) -> (b: bool)
    ensures
        b == cc@.contains(c),
{
    cc.class_member(c)
}

// item: R07.W3v
/// A named call: a member of a `filter_map` comes from some input element.
proof fn filter_map_origin_named(xs: Seq<char>, f: spec_fn(char) -> Option<char>, out: char)
    requires
        xs.filter_map(f).contains(out),
    ensures
        exists|c: char| xs.contains(c) && f(c) == Some(out),
{
    xs.lemma_filter_map_contains(f, out);
}

// item: R07.W4v
/// A named call: one more input element extends the `filter_map` by at most one.
proof fn filter_map_step_named(xs: Seq<char>, f: spec_fn(char) -> Option<char>, i: int)
    requires
        0 <= i < xs.len(),
    ensures
        xs[..i + 1].filter_map(f) == xs[..i].filter_map(f) + (match f(xs[i]) {
            Some(c) => seq![c],
            None => Seq::empty(),
        }),
{
    xs.lemma_filter_map_take_succ(f, i);
}

// ===========================================================================
// Holes
// ===========================================================================

// item: R07.H1v
// pair: R07.H1d
// uses: library-call
// gate: named-calls
/// **H1.** Filtering keeps prefixes: if `xs` is a prefix of `ys`, the
/// class-filtered `xs` is a prefix of the class-filtered `ys`. Which `Seq`
/// lemma says that filtering is monotone under `is_prefix_of`, and on which
/// receiver and arguments is it called?
proof fn lemma_filtered_sample_prefix(cc: &CharClass, xs: Seq<char>, ys: Seq<char>)
    requires
        xs.is_prefix_of(ys),
    ensures
        xs.filter(|c: char| cc@.contains(c)).is_prefix_of(ys.filter(|c: char| cc@.contains(c))),
{
    #[verifier::proof_note("R07.H1v")] assume(false);  // HOLE
}
// Hint(1): search `vstd::seq_lib` for lemmas whose names mention `filter`;
//    read which sequence is the receiver.
// Hint(2): the predicate passed must be the same closure as in the `ensures`.

// item: R07.H2v
// pair: R07.H2d
// uses: library-call
// gate: named-calls
/// **H2.** A filtered sample has no duplicates exactly when its set is as large
/// as the sequence. `vstd` proves each direction separately. Which two methods,
/// and under which hypothesis is each one called?
proof fn lemma_filtered_alphabet_exact(cc: &CharClass, xs: Seq<char>)
    ensures
        xs.filter(|c: char| cc@.contains(c)).no_duplicates() == (xs.filter(|c: char| cc@.contains(c)).to_set().len() == xs.filter(|c: char| cc@.contains(c)).len()),
{
    #[verifier::proof_note("R07.H2v")] assume(false);  // HOLE
}
// Hint(1): an equality of Booleans is two implications; each lemma has the
//    left side of one of them as its `requires`.
// Hint(2): search `vstd::seq_lib` for `no_dup` and for `to_set`; call each
//    method only where its precondition holds.

// item: R07.H3v
// pair: R07.H3d
// uses: library-call
// gate: named-calls
/// **H3.** A batch of samples, each at most `limit` long, flattens to at most
/// `blocks.len() * limit` characters. The library's bound is stated for a
/// different flattening. Which method gives the bound, and which one says the
/// two flattenings agree?
proof fn lemma_sample_batch_bound(blocks: Seq<Seq<char>>, limit: nat)
    requires
        forall|i: int| 0 <= i < blocks.len() ==> (#[trigger] blocks[i]).len() <= limit,
    ensures
        blocks.flatten().len() <= blocks.len() * limit,
{
    #[verifier::proof_note("R07.H3v")] assume(false);  // HOLE
}
// Hint(1): read the bound method's `ensures`: does it mention `flatten` or
//    `flatten_alt`?
// Hint(2): `vstd` also relates the two flattenings; call that method too.

// item: R07.H4v
// uses: broadcast-use
// gate: named-calls
/// **H4.** Scope the automation: W3's fact for every output at once. Every
/// element of a `filter_map` comes from some input element. A named call
/// proves one output; which scoped `broadcast use` covers every output the
/// goal mentions, and why is it shorter than an `assert forall` of calls?
proof fn filter_map_origins_scoped(xs: Seq<char>, f: spec_fn(char) -> Option<char>)
    ensures
        forall|out: char| xs.filter_map(f).contains(out) ==> exists|c: char| xs.contains(c) && f(c) == Some(out),
{
    #[verifier::proof_note("R07.H4v")] assume(false);  // HOLE
}
// Hint(1): a `broadcast use` names a `broadcast proof fn` by its full path;
//    W3 found the lemma by name.
// Hint(2): inside a proof body the broadcast is scoped to that body; it lets
//    the solver use the lemma at every `out` the goal mentions.

// item: R07.H5v
// uses: broadcast-use
// gate: named-calls
/// **H5.** The same for W4's fact, at every index: each one-element extension
/// of the input extends the `filter_map` by the optional mapped element.
/// Which lemma does the scoped broadcast make available, and at which terms
/// can the solver use it?
proof fn filter_map_steps_scoped(xs: Seq<char>, f: spec_fn(char) -> Option<char>)
    ensures
        forall|i: int| 0 <= i < xs.len() ==> #[trigger] xs[..i + 1].filter_map(f) == xs[..i].filter_map(f) + (match f(xs[i]) {
            Some(c) => seq![c],
            None => Seq::empty(),
        }),
{
    #[verifier::proof_note("R07.H5v")] assume(false);  // HOLE
}
// Hint(1): as H4: the full path of the `broadcast proof fn` W4 calls by name.
// Hint(2): the trigger of the goal's quantifier is the term the lemma's own
//    conclusion talks about.

} // verus!
