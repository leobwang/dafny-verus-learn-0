//! # R10 — Invariants in types (exercises)
//!
//! Standalone R track. Import only the frozen layers A1 to A4; no earlier learner
//! file is needed. The paired exercise is
//! dafny/R/R10_TypeInvariants/std/R10_TypeInvariants.dfy.
//!
//! Record the five predictions first (scripts/firsttry.sh R10 --check). Four
//! typed holes ship in this crate, eight across the pair.
//!
//! File order: the worked examples (W1 the packet with its type invariant, W2
//! the runtime check, W3 a language fact the shape does not give), the holes H1
//! to H4 with the given idempotence corollary after H3, then the given compiled
//! use-site test outside `verus!`. Shape (`is_norm`), exact normalization
//! (`norm`) and language preservation (`equiv`) are three different promises.
//!
//! Done: the crate gates with zero tool-counted holes, vaudit is clean,
//! specfreeze --check R10 passes and firsttry's strict report is OK. Preserve the
//! given contracts and implementations. /tutor R10 is available after an attempt.
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a4::*;

verus! {

// =============================================================================
// Worked examples
// =============================================================================

// item: R10.W1v
/// A packet: A4's `NormRe` and a ghost node count, with tracked evidence that
/// names the packed pattern. The type invariant `coherent` holds of every
/// value of the type; a constructor expression must establish it, and
/// `use_type_invariant` makes it available inside the impl.
pub tracked struct NormalEvidenceR10 {
    pub ghost pattern: Re,
}

pub struct NormPacketR10 {
    repr: NormRe,
    weight: Ghost<nat>,
    evidence: Tracked<NormalEvidenceR10>,
}

impl NormPacketR10 {
    #[verifier::type_invariant]
    spec fn coherent(&self) -> bool {
        is_norm(self.repr.re()) && self.weight@ == node_count(self.repr.re()) && self.evidence@.pattern == self.repr.re()
    }

    pub closed spec fn re(self) -> Re {
        self.repr.re()
    }

    pub fn pattern_ref_r10(&self) -> (out: &Re)
        ensures
            *out == self.re(),
            is_norm(*out),
    {
        proof {
            use_type_invariant(self);
        }
        self.repr.pattern_ref_r10()
    }

    pub fn into_pattern_r10(self) -> (out: Re)
        ensures
            out == self.re(),
            is_norm(out),
    {
        proof {
            use_type_invariant(&self);
        }
        self.repr.into_pattern_r10()
    }
}

// item: R10.W2v
/// The runtime end of the enforcement spectrum: A4's compiled `is_normal_exec_r10`
/// decides the shape of a raw regex.
fn runtime_shape_r10(r: &Re) -> (out: bool)
    ensures
        out == is_norm(*r),
{
    is_normal_exec_r10(r)
}

// item: R10.W3v
/// A language fact the shape does not give: replacing the right operand of a
/// Cat by a language-equal one keeps the language (A4's `lemma_cat_cong`).
proof fn replace_right_r10(a: Re, b1: Re, b2: Re, s: Seq<char>)
    requires
        equiv(b1, b2),
    ensures
        matches(Re::Cat(Box::new(a), Box::new(b1)), s) == matches(Re::Cat(Box::new(a), Box::new(b2)), s),
{
    lemma_cat_cong(a, a, b1, b2, s);
}

// =============================================================================
// Holes
// =============================================================================

// item: R10.H1v
// pair: R10.H1d
// uses: type-invariant, ghost, tracked
/// **H1.** Accept exactly the normal inputs, each in a packet whose ghost weight
/// is its node count and whose tracked evidence names it; reject the rest.
/// Remove `external_body` and write the body. What must hold when the struct
/// expression builds a `NormPacketR10`, and which of its fields exist at run time?
#[verifier::external_body]
fn try_packet_r10(r: Re) -> (res: Option<NormPacketR10>)
    ensures
        match res {
            Some(p) => p.re() == r && is_norm(r),
            None => !is_norm(r),
        },
{
    unimplemented!()
}
// Hint(1): `is_normal_exec_r10` decides the shape at run time; the weight is a `Ghost` and the evidence `Tracked`.
// Hint(2): `NormRe::from_normal_r10` needs `is_norm(r)`; the type invariant is checked at the struct expression.

// item: R10.H2v
// pair: R10.H2d
// uses: type-invariant, ghost, tracked
/// **H2.** Build the packet of `mk_cat(a.re(), b.re())`, with its ghost weight
/// rebuilt from the two packets' weights rather than by traversing the result.
/// Remove `external_body` and write the body. In which cases of `mk_cat` is the
/// result one of the operands, and what do the operands' invariants tell you then?
#[verifier::external_body]
fn cat_packet_r10(a: NormPacketR10, b: NormPacketR10) -> (out: NormPacketR10)
    ensures
        out.re() == mk_cat(a.re(), b.re()),
{
    unimplemented!()
}
// Hint(1): `use_type_invariant` on each operand gives its weight's meaning; `mk_cat`'s four branches pick the weight.
// Hint(2): A4's `lemma_cat_shape_r10` gives `is_norm` of the result; `mk_cat_exec` computes it from the moved patterns.

// item: R10.H3v
// pair: R10.H3d
/// **H3.** Normalizing a regex that is already normal returns it unchanged.
/// Prove it by structural induction (Verus never inducts for you). For which
/// constructors does `norm` call a smart constructor on normalized children,
/// and why does each return its plain node when the children are normal?
proof fn normal_fixed_r10(r: Re)
    requires
        is_norm(r),
    ensures
        norm(r) == r,
    decreases r,
{
    #[verifier::proof_note("R10.H3v")] assume(false);
}
// Hint(1): the leaves are their own normal form; each recursive constructor needs its children's hypotheses.
// Hint(2): `norm` is recursive, so its definition unfolds one level per mention; `is_norm(Alt(a, b))` excludes `a == b`.

// Given: idempotence follows from H3, because `norm`'s result is normal.
proof fn norm_idempotent_r10(r: Re)
    ensures
        norm(norm(r)) == norm(r),
{
    lemma_norm_shape_r10(r);
    normal_fixed_r10(norm(r));
}

// item: R10.H4v
// pair: R10.H4d
// uses: type-invariant, ghost
/// **H4.** The compiled structural normalizer: a packet whose pattern equals the
/// spec model `norm(*r)`. Reuse H1 and H2 where they fit. Remove `external_body`
/// and write the body. `norm` is a spec fn, so the body cannot call it: which
/// exec operations compute each case, and which shape lemma does each need?
#[verifier::external_body]
fn normalize_packet_r10(r: &Re) -> (out: NormPacketR10)
    ensures
        out.re() == norm(*r),
    decreases r,
{
    unimplemented!()
}
// Hint(1): `mk_alt_exec`, `mk_cat_exec`, `mk_star_exec` and `copy_re` are A4's and A1's exec operations.
// Hint(2): `try_packet_r10` packs a raw normal regex once `is_norm` of it is known; the shape lemmas supply that.

} // verus!

// Given (not an item): the compiled use-site check of H1, H2 and H4. It runs
// your bodies; `scripts/vcheck --test` executes it once they are done.
#[test]
fn packet_sample_test() {
    let ab = Re::Cat(Box::new(Re::Chr('a')), Box::new(Re::Chr('b')));
    let accepted = try_packet_r10(ab);
    assert!(accepted.is_some());
    let rejected = try_packet_r10(Re::Alt(Box::new(Re::Empty), Box::new(Re::Chr('a'))));
    assert!(rejected.is_none());
    let left = try_packet_r10(Re::Chr('a')).unwrap();
    let right = try_packet_r10(Re::Chr('b')).unwrap();
    let joined = cat_packet_r10(left, right);
    assert!(is_normal_exec_r10(joined.pattern_ref_r10()));
    let raw = Re::Star(Box::new(Re::Star(Box::new(Re::Alt(Box::new(Re::Chr('c')), Box::new(Re::Empty))))));
    let normal = normalize_packet_r10(&raw);
    let expected = Re::Star(Box::new(Re::Chr('c')));
    assert!(eq_re(normal.pattern_ref_r10(), &expected));
}
