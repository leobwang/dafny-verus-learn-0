//! # Q07 — exit, Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q07_internals_i/src/exit.rs` (author-only; never
//! learner-visible). Same imports, names, statements, item markers, `need:` and `form:`
//! lines as the exit file; both blocks are proved. Silent under `scripts/vcheck --ref`.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l4::*;

verus! {

// item: Q07.X1v S1
// uses: bit-vector
// need: pub fn join_word(hi: u64, lo: u64) -> (r: u128)
// need: r as nat == hi as nat * BASE + lo as nat
// form: bv-exec
// triv: { 0u128 }
// cfree: { (hi as u128) * 0x1_0000_0000_0000_0000u128 + (lo as u128) }
// cfree: { ((hi as u128) << 64u128) | (lo as u128) }
/// **X1.** Join two words into a double word.
///
/// Reference: the code is a shift and an `or`; one `bit_vector` fact says that they equal
/// the product and the sum the postcondition speaks of, and the solver's integer arithmetic
/// takes it from there. Without the fact the shift and the `or` do not verify, and the code
/// may not multiply (the form).
pub fn join_word(hi: u64, lo: u64) -> (r: u128)
    ensures
        r as nat == hi as nat * BASE + lo as nat,
{
    proof {
        assert(((hi as u128) << 64u128) | (lo as u128) == (hi as u128) * 0x1_0000_0000_0000_0000u128 + (lo as u128)) by (bit_vector);  // did: the shift and the or as a product and a sum
    }
    ((hi as u128) << 64u128) | (lo as u128)
}

// item: Q07.X2v S5
// uses: arithmetic-library
// need: pub proof fn lemma_weight_quotient(k: nat, n: nat)
// need: k <= n
// need: weight(n) / weight(k) == weight((n - k) as nat)
// form: no-nl
// cfree: { lemma_weight_add(k, (n - k) as nat); lemma_weight_zero(); lemma_weight_mono(0, k); assert(weight(n) / weight(k) == weight((n - k) as nat)) by (nonlinear_arith) requires weight(n) == weight(k) * weight((n - k) as nat), weight(k) > 0; }
/// **X2.** A quotient of weights is a weight.
///
/// Reference: L4's `lemma_weight_add(k, n - k)` splits `weight(n)` into
/// `weight(k) * weight(n - k)`; `weight(k)` is positive (L3's first equation and
/// monotonicity); one commutativity call orders the product as vstd's
/// `lemma_div_multiples_vanish` states it, and that lemma cancels the factor.
pub proof fn lemma_weight_quotient(k: nat, n: nat)
    requires
        k <= n,
    ensures
        weight(n) / weight(k) == weight((n - k) as nat),
{
    lemma_weight_add(k, (n - k) as nat);
    lemma_weight_zero();
    lemma_weight_mono(0, k);
    lemma_mul_is_commutative(weight(k) as int, weight((n - k) as nat) as int);
    lemma_div_multiples_vanish(weight((n - k) as nat) as int, weight(k) as int);
}

} // verus!
