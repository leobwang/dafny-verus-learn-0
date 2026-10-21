//! # R11 — Theory (exercises)
//!
//! Standalone R track. Import only the frozen layers A1 to A4; no earlier learner
//! file is needed. The paired exercise is dafny/R/R11_Theory/std/R11_Theory.dfy;
//! the closed-book checkpoint is src/exit.rs.
//!
//! Before reading the chapter, attempt T1 closed book (the first item below).
//! Record the five predictions first (scripts/firsttry.sh R11 --check). Ten typed
//! holes ship in this crate.
//!
//! File order: the test-out (T1), the certificate kernel (W1 the slice split,
//! W2 the tracked evidence, then H1 the checker, H2 soundness on tracked evidence,
//! H3 direct completeness into tracked evidence), complete search (H5 with H6 and
//! H7), the streaming matcher (W3 the residual step, then H4) and the Vec-backed
//! arena (H8, H9). Certificates are ordinary data; their meaning is A4's
//! `valid`/`valid_word_r10`, with splits relative to the word a node owns.
//!
//! Done: the crate gates with zero tool-counted holes, vaudit is clean,
//! specfreeze --check R11 passes and firsttry's strict report is OK. Preserve the
//! given contracts and implementations. /tutor R11 is available after an attempt.
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a4::*;

// =============================================================================
// Test-out (closed book)
// =============================================================================

verus! {

// item: R11.T1v
// pair: R11.T1d
/// **T1.** Closed book: the one-step index update of a scanning loop. Remove
/// `external_body` and write the body. Which precondition makes both
/// postconditions hold, and why can the addition not overflow?
#[verifier::external_body]
fn wp_index_step_r11(i: usize, len: usize) -> (next: usize)
    requires
        i < len,
    ensures
        next == i + 1,
        next <= len,
{
    unimplemented!()
}
// Hint(1): substitute i + 1 for next in the postcondition; what is left must follow from i < len.
// Hint(2): i < len <= usize::MAX, so i + 1 is representable.
// Uncomment as you go:
// fn wp_index_step_check() {
//     let next = wp_index_step_r11(3, 4);
//     assert(next == 4);
// }

} // verus!

// =============================================================================
// The certificate kernel
// =============================================================================

verus! {

// item: R11.W1v
/// The relative split: the first k scalars of a slice are the slice from lo to
/// lo + k of the whole vector, and the rest is the slice from lo + k.
proof fn slice_split_r11(s: Seq<char>, lo: int, hi: int, k: int)
    requires
        0 <= lo <= hi <= s.len(),
        0 <= k <= hi - lo,
    ensures
        s.subrange(lo, hi).take(k) == s.subrange(lo, lo + k),
        s.subrange(lo, hi).skip(k) == s.subrange(lo + k, hi),
{
    assert(s.subrange(lo, hi).take(k) =~= s.subrange(lo, lo + k));
    assert(s.subrange(lo, hi).skip(k) =~= s.subrange(lo + k, hi));
}

// item: R11.W2v
/// Tracked evidence: a proof-mode object packing a tree, a pattern and a word.
/// It states nothing by itself; a `requires` on its consumer says what it proves.
pub tracked struct CertificateEvidenceR11 {
    pub ghost tree: Derivation,
    pub ghost pattern: Re,
    pub ghost word: Seq<char>,
}

// item: R11.H1v
// pair: R11.H1d
/// **H1.** The executable checker over a slice `s[lo..hi]`: return exactly
/// `valid(*d, *r, s@, lo, hi)`, by recursion on the derivation. Remove
/// `external_body` and write the body. Which bounds must be checked before the
/// slice means anything, and how does a node's relative split become absolute?
#[verifier::external_body]
fn check_certificate_r11(d: &Derivation, r: &Re, s: &Vec<char>, lo: usize, hi: usize) -> (ok: bool)
    ensures
        ok == valid(*d, *r, s@, lo as int, hi as int),
    decreases d,
{
    unimplemented!()
}
// Hint(1): A4's `valid` is `valid_word_r10` on `s@.subrange(lo, hi)`; check the bounds first, then match (d, r) pairwise.
// Hint(2): W1's `slice_split_r11` turns a node's relative k into the absolute middle `lo + k`.

// item: R11.H2v
// pair: R11.H2d
// uses: tracked
/// **H2.** Soundness, consuming tracked evidence: a valid tree proves the match.
/// Write your own helper above it (an induction on the tree over plain ghost
/// values) and call it here. What does the consumer's `requires` give you, and
/// how do you reach the evidence's ghost fields?
proof fn consume_sound_r11(tracked evidence: CertificateEvidenceR11)
    requires
        valid_word_r10(evidence.tree, evidence.pattern, evidence.word),
    ensures
        matches(evidence.pattern, evidence.word),
{
    #[verifier::proof_note("R11.H2v")] assume(false);
}
// Hint(1): the proof is an induction on the derivation, like Dafny's H2; put it in a helper over plain ghost values.
// Hint(2): `take(k)` and `skip(k)` are the children's words; state them as `subrange`s with `=~=` for `matches`.

// item: R11.H3v
// pair: R11.H3d
// uses: tracked
/// **H3.** Direct completeness into tracked evidence: from a match, overwrite
/// `out` with evidence whose tree is valid. Which bound on the word does the
/// certificate's `usize` split force, and where does `choose` take the tree from?
proof fn direct_evidence_r11(r: Re, s: Seq<char>, tracked out: &mut CertificateEvidenceR11)
    requires
        s.len() <= usize::MAX,
        matches(r, s),
    ensures
        final(out).pattern == r,
        final(out).word == s,
        valid_word_r10(final(out).tree, r, s),
{
    #[verifier::proof_note("R11.H3v")] assume(false);
}
// Hint(1): prove `exists|d| valid_word_r10(d, r, s)` by induction on (r, s.len()) in a helper, then choose the tree.
// Hint(2): a split k must fit a usize: the `s.len() <= usize::MAX` precondition is what makes `i as usize` exact.

} // verus!

// =============================================================================
// Complete search
// =============================================================================

verus! {

// item: R11.H5v
// pair: R11.H5d
/// **H5.** Complete search over `s[lo..hi]`: a valid certificate, or `None` only
/// when the slice does not match. Remove `external_body` and write the body; Cat
/// and Star hand their splits to H6 and H7. Which clause rules out an
/// always-`None` search, and what is the recursion's measure?
#[verifier::external_body]
fn search_r11(r: &Re, s: &Vec<char>, lo: usize, hi: usize) -> (out: Option<Derivation>)
    requires
        lo <= hi <= s.len(),
    ensures
        match out {
            Some(d) => valid(d, *r, s@, lo as int, hi as int),
            None => !matches(*r, s@.subrange(lo as int, hi as int)),
        },
    decreases node_count(*r), hi - lo, 1nat,
{
    unimplemented!()
}
// Hint(1): the measure (node_count(*r), hi - lo, 1) lets H6 and H7 call back on children and on shorter slices.
// Hint(2): each leaf decides both clauses by itself; `Empty` is always `None`.

// item: R11.H6v
// pair: R11.H6d
/// **H6.** The split loop of a concatenation over a slice: try each split k,
/// return the first certificate found, and on reaching the end prove that no
/// split works. Remove `external_body` and write the body. What must the loop
/// invariant say about the splits already tried?
#[verifier::loop_isolation(false)]
#[verifier::external_body]
fn search_cat_r11(a: &Re, b: &Re, s: &Vec<char>, lo: usize, hi: usize) -> (out: Option<Derivation>)
    requires
        lo <= hi <= s.len(),
    ensures
        match out {
            Some(d) => valid(d, Re::Cat(Box::new(*a), Box::new(*b)), s@, lo as int, hi as int),
            None => !matches(Re::Cat(Box::new(*a), Box::new(*b)), s@.subrange(lo as int, hi as int)),
        },
    decreases node_count(Re::Cat(Box::new(*a), Box::new(*b))), hi - lo, 0nat,
{
    unimplemented!()
}
// Hint(1): the invariant is the exclusion of every split below k; extend it to k after a failed try, with `assert forall`.
// Hint(2): at k == n a split chosen out of `matches` would lie in the excluded range: that is the `None` proof.

// item: R11.H7v
// pair: R11.H7d
/// **H7.** The first-chunk loop of a star: H6 with chunks of length at least 1
/// and the same star on the rest. Remove `external_body` and write the body.
/// Which loop bound differs from H6, and how do you recurse on the star itself?
#[verifier::loop_isolation(false)]
#[verifier::external_body]
fn search_star_r11(a: &Re, s: &Vec<char>, lo: usize, hi: usize) -> (out: Option<Derivation>)
    requires
        lo < hi <= s.len(),
    ensures
        match out {
            Some(d) => valid(d, Re::Star(Box::new(*a)), s@, lo as int, hi as int),
            None => !matches(Re::Star(Box::new(*a)), s@.subrange(lo as int, hi as int)),
        },
    decreases node_count(Re::Star(Box::new(*a))), hi - lo, 0nat,
{
    unimplemented!()
}
// Hint(1): k starts at 1 (a first chunk is non-empty) and the recursion on the rest uses the same star.
// Hint(2): build the star once with `copy_re` and keep `parent == Re::Star(Box::new(*a))` in the invariant.

} // verus!

// =============================================================================
// The streaming matcher
// =============================================================================

use rg_re_a1b::*;
use rg_re_a2::*;

verus! {

// The loop's relation: after reading prefix, current matches exactly the tails
// that complete prefix to a word of r. Opaque: revealed where it is used.
#[verifier::opaque]
pub open spec fn residual_r11(r: Re, current: Re, prefix: Seq<char>) -> bool {
    forall|tail: Seq<char>| #[trigger] matches(current, tail) == matches(r, prefix + tail)
}

proof fn residual_start_r11(r: Re)
    ensures
        residual_r11(r, r, Seq::empty()),
{
    // did: unfold the fixed model for this constructor obligation.
    reveal(residual_r11);
    assert forall|tail: Seq<char>| #[trigger] matches(r, tail) == matches(r, Seq::empty() + tail) by {
        assert(Seq::<char>::empty() + tail =~= tail);
    }
}

// item: R11.W3v
/// The relation is kept by one derivative step (A2's `lemma_deriv_correct`).
proof fn residual_step_r11(r: Re, current: Re, prefix: Seq<char>, c: char)
    requires
        residual_r11(r, current, prefix),
    ensures
        residual_r11(r, deriv(current, c), prefix + seq![c]),
{
    // did: unfold the fixed model for this constructor obligation.
    reveal(residual_r11);
    assert forall|tail: Seq<char>| #[trigger] matches(deriv(current, c), tail) == matches(r, (prefix + seq![c]) + tail) by {
        lemma_deriv_correct(current, c, tail);
        assert(prefix + (seq![c] + tail) =~= (prefix + seq![c]) + tail);
    }
}

proof fn residual_observe_r11(r: Re, current: Re, prefix: Seq<char>)
    requires
        residual_r11(r, current, prefix),
    ensures
        nullable(current) == matches(r, prefix),
{
    // did: unfold the fixed model for this constructor obligation.
    reveal(residual_r11);
    lemma_nullable_correct(current);
    assert(prefix + Seq::<char>::empty() =~= prefix);
}

pub struct PrefixReportR11 {
    pub accepted: bool,
    pub trace: Vec<bool>,
}

// item: R11.H4v
// pair: R11.H4d
/// **H4.** The streaming matcher: read s with derivatives, record for every
/// nonempty prefix whether it matches, and report whether s does. Remove
/// `external_body` and write the body. What must the invariant say about
/// `current`, `trace` and the prefix read so far?
#[verifier::external_body]
fn prefix_matches_r11(r: &Re, s: &Vec<char>) -> (out: PrefixReportR11)
    ensures
        out.accepted == matches(*r, s@),
        out.trace@.len() == s@.len(),
        forall|j: int| 0 <= j < s@.len() ==> out.trace@[j] == matches(*r, s@.take(j + 1)),
{
    unimplemented!()
}
// Hint(1): the invariant has three parts: bounds and the trace's length, the residual relation on `s@.take(i)`, and the trace facts.
// Hint(2): `residual_start_r11` before the loop, `residual_step_r11` and `residual_observe_r11` in the body.

} // verus!

// =============================================================================
// The Vec-backed arena (the gated PointsTo arena's admitted fallback)
// =============================================================================

verus! {

pub struct ArenaNodeR11 {
    pub label: char,
    pub first: Option<usize>,
    pub second: Option<usize>,
}

pub struct ArenaR11 {
    pub nodes: Vec<ArenaNodeR11>,
}

pub open spec fn targets_valid_r11(node: ArenaNodeR11, len: int) -> bool {
    (match node.first {
        Some(k) => k < len,
        None => true,
    }) && (match node.second {
        Some(k) => k < len,
        None => true,
    })
}

pub open spec fn arena_valid_r11(arena: ArenaR11) -> bool {
    forall|i: int| 0 <= i < arena.nodes@.len() ==> targets_valid_r11(#[trigger] arena.nodes@[i], arena.nodes@.len() as int)
}

proof fn targets_monotone_r11(node: ArenaNodeR11, old_len: int, new_len: int)
    requires
        targets_valid_r11(node, old_len),
        old_len <= new_len,
    ensures
        targets_valid_r11(node, new_len),
{
}

fn empty_arena_r11() -> (out: ArenaR11)
    ensures
        arena_valid_r11(out),
        out.nodes@.len() == 0,
{
    ArenaR11 { nodes: Vec::new() }
}

// item: R11.H8v
/// **H8.** Append a node with no edges and return its index, keeping every
/// target in range. Remove `external_body` and write the body. Why do the old
/// nodes' targets stay valid when the arena grows?
#[verifier::external_body]
fn append_node_r11(arena: &mut ArenaR11, label: char) -> (index: usize)
    requires
        arena_valid_r11(*old(arena)),
        old(arena).nodes.len() < usize::MAX,
    ensures
        arena_valid_r11(*final(arena)),
        final(arena).nodes@.len() == old(arena).nodes@.len() + 1,
        final(arena).nodes@.take(old(arena).nodes@.len() as int) == old(arena).nodes@,
        index == old(arena).nodes@.len(),
        final(arena).nodes@[index as int].label == label,
        final(arena).nodes@[index as int].first is None,
        final(arena).nodes@[index as int].second is None,
{
    unimplemented!()
}
// Hint(1): keep the old view in a ghost, push, then prove the validity forall index by index.
// Hint(2): `targets_monotone_r11` moves an old node's targets to the longer arena; the new node has none.

// item: R11.H9v
/// **H9.** Point a node's first edge at a target, changing nothing else. Remove
/// `external_body` and write the body. Which nodes does `set` leave unchanged,
/// and how does the validity forall treat the one it changes?
#[verifier::external_body]
fn link_first_r11(arena: &mut ArenaR11, index: usize, target: usize)
    requires
        arena_valid_r11(*old(arena)),
        index < old(arena).nodes.len(),
        target < old(arena).nodes.len(),
    ensures
        arena_valid_r11(*final(arena)),
        final(arena).nodes@.len() == old(arena).nodes@.len(),
        final(arena).nodes@[index as int].label == old(arena).nodes@[index as int].label,
        final(arena).nodes@[index as int].first == Some(target),
        final(arena).nodes@[index as int].second == old(arena).nodes@[index as int].second,
        forall|j: int| 0 <= j < old(arena).nodes@.len() && j != index ==> final(arena).nodes@[j] == old(arena).nodes@[j],
{
    unimplemented!()
}
// Hint(1): read the node's label and second edge before the write; the new node is the old one with first replaced.
// Hint(2): the changed node's target is in range by the precondition; every other node is `before[j]`.

} // verus!

// Given (not an item): the compiled use-site check of T1, H1, H4, H5 to H7, H8 and H9.
// It runs your bodies; `scripts/vcheck --test` executes it once they are done.
#[test]
fn certificate_sample_test() {
    assert_eq!(wp_index_step_r11(2, 5), 3);
    let ab = Re::Cat(Box::new(Re::Chr('a')), Box::new(Re::Star(Box::new(Re::Chr('b')))));
    let word: Vec<char> = vec!['a', 'b'];
    let good = Derivation::DCat(1, Box::new(Derivation::DChr), Box::new(Derivation::DStarCons(1, Box::new(Derivation::DChr), Box::new(Derivation::DStarNil))));
    assert!(check_certificate_r11(&good, &ab, &word, 0, 2));
    let bad = Derivation::DCat(2, Box::new(Derivation::DChr), Box::new(Derivation::DStarNil));
    assert!(!check_certificate_r11(&bad, &ab, &word, 0, 2));
    let aba: Vec<char> = vec!['a', 'b', 'a'];
    let report = prefix_matches_r11(&ab, &aba);
    assert!(!report.accepted);
    assert_eq!(report.trace, vec![true, true, false]);
    let pattern = Re::Cat(Box::new(Re::Star(Box::new(Re::Chr('a')))), Box::new(Re::Chr('b')));
    let aab: Vec<char> = vec!['a', 'a', 'b'];
    let found = search_r11(&pattern, &aab, 0, 3);
    assert!(found.is_some());
    assert!(check_certificate_r11(&found.unwrap(), &pattern, &aab, 0, 3));
    let aa: Vec<char> = vec!['a', 'a'];
    assert!(search_r11(&pattern, &aa, 0, 2).is_none());
    let mut arena = empty_arena_r11();
    let first = append_node_r11(&mut arena, 'x');
    let second = append_node_r11(&mut arena, 'y');
    link_first_r11(&mut arena, second, first);
    assert_eq!(arena.nodes.len(), 2);
    assert_eq!(arena.nodes[1].first, Some(0));
    assert_eq!(arena.nodes[1].label, 'y');
    assert_eq!(arena.nodes[0].first, None);
}
