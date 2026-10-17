/* CONTRACT
goal: implement and prove every statement of the STATEMENTS section of this file, changing no statement
allowed-files:
  - verus/q/q08_internals_ii/src/agent.rs
acceptance:
  - re-verify after every edit with `scripts/vcheck verus/q/q08_internals_ii/src/agent.rs`; never stack unverified edits
  - `scripts/vcheck --gate verus/q/q08_internals_ii/src/agent.rs` exits 0 and prints only the summary line
  - zero tool-counted holes in the allowed file
  - `scripts/specfreeze --against research/q08_statements.rs verus/q/q08_internals_ii/src/agent.rs` reports no change: no statement changed
  - `scripts/vaudit verus/q/q08_internals_ii/src/agent.rs` reports no finding
  - `git diff` against the committed statements changes only the bodies of the STATEMENTS functions (each `#[verifier::external_body]` line removed with its `unimplemented!()` body) and the HELPERS section
  - every WITNESSES check is unchanged and verifies
  - new helper functions and proof fns go only under HELPERS
*/
//! # Q08 Flagship, Verus half — spec-to-proof (Reference Solution)
//!
//! Hole-free reference for `verus/q/q08_internals_ii/src/agent.rs` (author-only): the proof
//! that the contract is satisfiable as stated. The three sections are empty, as shipped;
//! the closing reference section holds a reference set of statements (each fn's header is
//! what a learner commits in STATEMENTS, as an `external_body` stub), witnesses for them,
//! and the reference delivery: the bodies and the helpers a contractor puts under HELPERS.
//! Silent under `scripts/vcheck --ref`; `scripts/vaudit --ref` reports no finding.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l4::*;

verus! {

// item: Q08.A1v S6

// ### STATEMENTS (learner-owned: your statements, each an `external_body` stub). Two
//    operations on canonical BigNats (L1's `BigNat`, `wf`, `to_nat`):
//    - the shift left by `k` limbs;
//    - the limbs above the low `k` (the part above a split at `k` limbs).

// ### WITNESSES (learner-owned: your checks that the statements can be met and say
//    something).

// ### HELPERS (the contractor's: helper fns and proof fns, if any).

// =========================================================================================
// — clearly marked: everything below answers the agentic file —
// =========================================================================================
// A reference set of statements: `shift_limbs` (canonical, worth the value times
// `weight(k)`) and `high_limbs` (canonical, worth the value divided by `weight(k)`), each
// an `external_body` stub when committed as research/q08_statements.rs (2 holes, the
// witnesses verifying against them). A low split would need normalization (its top limbs
// may be 0), so the Verus statements are the shift and the high part only. The delivery
// below passes every acceptance line: `vcheck --gate` with 0 holes, `specfreeze --against`
// the statements with no finding, `vaudit` with no finding, the witnesses unchanged
// (Solutions/plans/Q08-code-notes.md).
//
// The high part's proof is split into two proof fns (`lemma_div_by_low`,
// `lemma_div_short`): written inline, as the plan's first delivery had it, it verified on
// seeds 1-3 but spent up to 4.85M of the 6M rlimit on one seed (CV 81.7%); split, every
// symbol stays below a CV of 10% (the code notes give the runs).
//
// Statement pitfalls the learner's audit and the rubric look for: forgetting `r.wf()` in an
// `ensures` (any limbs with the right value); a shift that turns zero into `k` zero limbs
// (not canonical: the empty BigNat must stay empty); a low split stated as a canonical
// BigNat with no normalization; witnesses that call only the empty BigNat. Soft spots a
// contract run shows: a `requires` added to a statement or a helper that a caller cannot
// meet; an `assume` or `#[verifier::rlimit]` in a helper (`vaudit` reports it); an
// `ensures` weakened to `>=` (the freeze check catches it).

pub open spec fn zeros(k: nat) -> Seq<u64>
    decreases k,
{
    if k == 0 {
        Seq::empty()
    } else {
        zeros((k - 1) as nat).push(0u64)
    }
}

proof fn lemma_zeros(k: nat)
    ensures
        zeros(k).len() == k,
        seq_to_nat(zeros(k)) == 0,
    decreases k,
{
    if k > 0 {
        lemma_zeros((k - 1) as nat);
        lemma_seq_to_nat_push_zero(zeros((k - 1) as nat));
    }
}

proof fn lemma_weight_pos(k: nat)
    ensures
        weight(k) > 0,
{
    lemma_weight_zero();
    lemma_weight_mono(0, k);
}

/// Splitting off `lo` divides by its weight.
proof fn lemma_div_by_low(lo: Seq<u64>, hi: Seq<u64>)
    ensures
        seq_to_nat(lo + hi) / weight(lo.len()) == seq_to_nat(hi),
{
    let w = weight(lo.len());
    lemma_weight_pos(lo.len());
    lemma_seq_to_nat_upper(lo);
    lemma_seq_to_nat_append(lo, hi);
    lemma_mul_is_commutative(w as int, seq_to_nat(hi) as int);
    lemma_fundamental_div_mod_converse(
        seq_to_nat(lo + hi) as int,
        w as int,
        seq_to_nat(hi) as int,
        seq_to_nat(lo) as int,
    );
}

/// A value of at most `k` limbs divides by `weight(k)` to 0.
proof fn lemma_div_short(a: Seq<u64>, k: nat)
    requires
        a.len() <= k,
    ensures
        seq_to_nat(a) / weight(k) == 0,
{
    lemma_weight_pos(k);
    lemma_seq_to_nat_upper(a);
    lemma_weight_mono(a.len(), k);
    lemma_basic_div(seq_to_nat(a) as int, weight(k) as int);
}

/// Multiply by `weight(k)`: `k` zero limbs below the value (zero stays empty).
pub fn shift_limbs(a: &BigNat, k: usize) -> (r: BigNat)
    requires
        a.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() * weight(k as nat),
{
    let n = a.limbs.len();
    let mut v: Vec<u64> = Vec::new();
    if n == 0 {
        proof {
            lemma_mul_basics(weight(k as nat) as int);
        }
        return BigNat { limbs: v };
    }
    let mut i: usize = 0;
    while i < k
        invariant
            i <= k,
            v@ =~= zeros(i as nat),
        decreases k - i,
    {
        v.push(0);
        i = i + 1;
    }
    let mut j: usize = 0;
    while j < n
        invariant
            j <= n,
            n == a@.len(),
            v@ =~= zeros(k as nat) + a@.subrange(0, j as int),
        decreases n - j,
    {
        v.push(a.limbs[j]);
        j = j + 1;
        proof {
            assert(v@ =~= zeros(k as nat) + a@.subrange(0, j as int));
        }
    }
    proof {
        assert(a@.subrange(0, n as int) =~= a@);
        lemma_zeros(k as nat);
        lemma_seq_to_nat_append(zeros(k as nat), a@);
        lemma_mul_is_commutative(weight(k as nat) as int, a.to_nat() as int);
    }
    BigNat { limbs: v }
}

/// Divide by `weight(k)`: drop the `k` lowest limbs.
pub fn high_limbs(a: &BigNat, k: usize) -> (r: BigNat)
    requires
        a.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() / weight(k as nat),
{
    let n = a.limbs.len();
    let mut v: Vec<u64> = Vec::new();
    if k >= n {
        proof {
            lemma_div_short(a@, k as nat);
        }
        return BigNat { limbs: v };
    }
    let mut j: usize = k;
    while j < n
        invariant
            k <= j <= n,
            n == a@.len(),
            v@ =~= a@.subrange(k as int, j as int),
        decreases n - j,
    {
        v.push(a.limbs[j]);
        j = j + 1;
    }
    proof {
        let lo = a@.subrange(0, k as int);
        assert(lo + v@ =~= a@);
        lemma_div_by_low(lo, v@);
    }
    BigNat { limbs: v }
}

// The reference witnesses.
fn witnesses() {
    let a = BigNat { limbs: vec![5u64, 1u64] };
    proof {
        reveal_with_fuel(seq_to_nat, 3);  // did: unfolds seq_to_nat on a two-limb literal
        assert(a@.drop_first() =~= seq![1u64]);
        assert(seq![1u64].drop_first() =~= Seq::<u64>::empty());
        assert(a.wf());
    }
    let r = shift_limbs(&a, 2);
    assert(r.to_nat() == a.to_nat() * weight(2));
    let h = high_limbs(&a, 1);
    assert(h.to_nat() == a.to_nat() / weight(1));
}

} // verus!

// AUDIT (learner-owned; after the contract run)
//   the statement that cost the contractor most, and why:
//   each helper's statement (does it assume what it should prove?):
