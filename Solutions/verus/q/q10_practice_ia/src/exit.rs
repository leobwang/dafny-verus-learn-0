//! # Q10 — exit, Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q10_practice_ia/src/exit.rs` (author-only; never
//! learner-visible). Same imports, names, statements, item markers and `need:` lines as
//! the exit file; the block is implemented, with its trivial body and its near miss in
//! `// triv:` and `// cfree:` lines. Silent under `scripts/vcheck --ref`.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l5::*;

verus! {

// item: Q10.X1v S1
// uses: exec-check
// need: pub fn halve_words(lo: u64, hi: u64) -> (r: (u64, u64))
// need: r.0 as nat + r.1 as nat * BASE == (lo as nat + hi as nat * BASE) / 2
// triv: { (0, 0) }
// cfree: { (lo / 2, hi / 2) }
/// **X1.** Halve a two-word number.
///
/// Reference: one line of code: the low bit of `hi` moves to the top bit of the low word.
/// The solver's linear integer arithmetic closes the postcondition (`hi % 2` is 0 or 1, and
/// `lo / 2 + 2^63 < 2^64`, so the sum cannot overflow). The near miss loses that bit.
pub fn halve_words(lo: u64, hi: u64) -> (r: (u64, u64))
    ensures
        r.0 as nat + r.1 as nat * BASE == (lo as nat + hi as nat * BASE) / 2,
{
    (lo / 2 + (hi % 2) * 0x8000_0000_0000_0000u64, hi / 2)
}

} // verus!
