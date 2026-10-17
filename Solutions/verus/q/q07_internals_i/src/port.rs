//! # Q07 — the port, `src/port.rs` (Reference Solution)
//!
//! Hole-free reference for `verus/q/q07_internals_i/src/port.rs` (author-only; never
//! learner-visible), the module `port` of the crate `q07_internals_i`. Same imports, names,
//! item markers and order as the exercise file; the statements are the exercise file's,
//! with H7's contract written (an open statement: `from_u128` is under `open_specs` in
//! `expected/Q07.freeze`) and H8's definition given. Every check is live: H7's use-site
//! check, the differential suite (`scripts/vcheck --test` on the crate, run on a root that
//! holds this twin at the learner path), and the mutants as reference-only tests.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l4::*;

verus! {

// item: Q07.H7v S1
// uses: bit-vector, property-test
// form: bv-exec
// triv: { BigNat { limbs: Vec::new() } }
// cfree: { let mut v: Vec<u64> = Vec::new();
// cfree:   if x / 0x1_0000_0000_0000_0000u128 != 0 { v.push((x % 0x1_0000_0000_0000_0000u128) as u64);
// cfree:     v.push((x / 0x1_0000_0000_0000_0000u128) as u64);
// cfree:     proof { assert(v@.drop_first().drop_first() =~= Seq::<u64>::empty()); reveal_with_fuel(seq_to_nat, 3); } }
// cfree:   else if x != 0 { v.push(x as u64);
// cfree:     proof { assert(v@.drop_first() =~= Seq::<u64>::empty()); reveal_with_fuel(seq_to_nat, 2); } }
// cfree:   BigNat { limbs: v } }
/// **H7.** The port of `FromNat` to inputs below 2^128.
///
/// Reference: the contract is `FromNatCorrect`'s carried over, `r.wf()` and
/// `r.to_nat() == x`; Verus's `wf` is canonical (no most significant zero limb), which is
/// stronger than Dafny's `Valid` (every limb below `BASE`, high zeros allowed): for `u64`
/// limbs `Valid` holds by typing, and `FromNat` itself never makes a high zero, so the
/// stronger contract is the faithful one (the mirror, H8 and H9, shows it relative to the
/// definition). The body splits `x` by a cast and a shift (two `bit_vector` facts relate
/// them to the remainder and the division), then pushes the limbs a canonical `BigNat`
/// keeps: both when the high limb is not 0, the low one alone when only it is not 0,
/// nothing for 0. `seq_to_nat` unfolds once per pushed limb plus once for the empty tail.
pub fn from_u128(x: u128) -> (r: BigNat)
    ensures
        r.wf(),
        r.to_nat() == x,
{
    let lo = x as u64;
    let hi = (x >> 64u128) as u64;
    proof {
        assert(x as u64 == x % 0x1_0000_0000_0000_0000u128) by (bit_vector);  // did: the cast as a remainder
        assert((x >> 64u128) == x / 0x1_0000_0000_0000_0000u128) by (bit_vector);  // did: the shift as a division
    }
    let mut v: Vec<u64> = Vec::new();
    if hi != 0 {
        v.push(lo);
        v.push(hi);
        proof {
            assert(v@.drop_first().drop_first() =~= Seq::<u64>::empty());
            reveal_with_fuel(seq_to_nat, 3);  // did: three unfoldings of seq_to_nat
        }
    } else if lo != 0 {
        v.push(lo);
        proof {
            assert(v@.drop_first() =~= Seq::<u64>::empty());
            reveal_with_fuel(seq_to_nat, 2);  // did: two unfoldings of seq_to_nat
        }
    }
    BigNat { limbs: v }
}

/// H7's use-site check: concrete calls whose results the contract must determine.
fn from_u128_check() {
    let r = from_u128(0x2_0000_0000_0000_0005u128);
    assert(r.wf() && r.to_nat() == 0x2_0000_0000_0000_0005);
    let z = from_u128(0u128);
    assert(z.wf() && z.to_nat() == 0);
    let m = from_u128(u128::MAX);
    assert(m.wf() && m.to_nat() == 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF);
}

// item: Q07.H8v S2
/// **H8.** The mirror: `FromNat`'s definition, transcribed.
///
/// Reference: L2's `FromNat(n)` is `if n == 0 then [] else [n % BASE] + FromNat(n / BASE)`;
/// in Verus the limb is `(n % BASE) as u64` (a `nat` below `BASE`, so the cast keeps it);
/// the measure `decreases n` ships with the statement.
pub open spec fn from_nat_mirror(n: nat) -> Seq<u64>
    decreases n,
{
    if n == 0 {
        Seq::empty()
    } else {
        seq![(n % BASE) as u64] + from_nat_mirror(n / BASE)
    }
}

// item: Q07.H9v S4
// uses: fuel
/// **H9.** The mirror meets the port's contract, relative to the mirror.
///
/// Reference: below 2^128 the quotient `n / BASE` is a limb (one scoped `nonlinear_arith`
/// step), so the quotient of the quotient is 0 and the mirror unfolds to at most two limbs:
/// three cases (`n == 0`, one limb, two limbs). In each, `reveal_with_fuel` unfolds both
/// spec fns, `=~=` names the literal and its tails, and the two-limb case recombines `n`
/// with vstd's `lemma_fundamental_div_mod`.
pub proof fn lemma_mirror_meets_port(x: u128)
    ensures
        seq_wf(from_nat_mirror(x as nat)),
        seq_to_nat(from_nat_mirror(x as nat)) == x as nat,
{
    let n = x as nat;
    let q = n / BASE;
    assert(q < BASE) by {
        assert(x as nat / 0x1_0000_0000_0000_0000nat < 0x1_0000_0000_0000_0000nat) by (nonlinear_arith)  // did: a quotient below 2^128 / 2^64
            requires
                x <= 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFFu128,
        ;
    }
    assert(q / BASE == 0);
    reveal_with_fuel(from_nat_mirror, 3);  // did: three unfoldings of the mirror
    reveal_with_fuel(seq_to_nat, 3);  // did: three unfoldings of seq_to_nat
    if n == 0 {
    } else if q == 0 {
        assert(from_nat_mirror(n) =~= seq![(n % BASE) as u64]);
        assert(seq![(n % BASE) as u64].drop_first() =~= Seq::<u64>::empty());
    } else {
        assert(from_nat_mirror(q) =~= seq![(q % BASE) as u64]);
        assert(from_nat_mirror(n) =~= seq![(n % BASE) as u64, (q % BASE) as u64]);
        assert(seq![(n % BASE) as u64, (q % BASE) as u64].drop_first() =~= seq![(q % BASE) as u64]);
        assert(seq![(q % BASE) as u64].drop_first() =~= Seq::<u64>::empty());
        lemma_fundamental_div_mod(n as int, BASE as int);
    }
}

} // verus!

// The differential suite: the check unit's sample run (dafny/checks/Q07_checks.dfy), row for
// row, against the port compiled by Verus.
#[cfg(test)]
mod port_tests {
    use super::*;

    #[test]
    fn sample() {
        assert_eq!(from_u128(0).limbs, Vec::<u64>::new());
        assert_eq!(from_u128(5).limbs, vec![5u64]);
        assert_eq!(from_u128(0xFFFF_FFFF_FFFF_FFFF).limbs, vec![u64::MAX]);
        assert_eq!(from_u128(0x1_0000_0000_0000_0007).limbs, vec![7u64, 1]);
        assert_eq!(from_u128(0x3_0000_0000_0000_0002).limbs, vec![2u64, 3]);
        assert_eq!(from_u128(u128::MAX).limbs, vec![u64::MAX, u64::MAX]);
    }
}

// reference-only: the three mutants of the exercise file's MUTANTS block as plain Rust
// (outside `verus!`, so never verified), and the sample rows on which each breaks the Verus
// contract (`wf`: no zero most significant limb; the value). M1 breaks only `wf`, on every
// row below 2^64: the Dafny contract (`Valid` and the value) accepts it, which is the
// fidelity finding. M2 and M3 break the value, so both contracts reject them.
#[cfg(test)]
mod port_mutants {
    // reference-only
    fn value(v: &[u64]) -> u128 {
        let mut r: u128 = 0;
        for (i, &d) in v.iter().enumerate() {
            r |= (d as u128) << (64 * i);
        }
        r
    }

    // reference-only
    fn wf(v: &[u64]) -> bool {
        v.is_empty() || *v.last().unwrap() != 0
    }

    // reference-only
    fn m1(x: u128) -> Vec<u64> {
        vec![x as u64, (x >> 64) as u64]
    }

    // reference-only
    fn m2(x: u128) -> Vec<u64> {
        let (lo, hi) = (x as u64, (x >> 64) as u64);
        if hi != 0 { vec![hi, lo] } else if lo != 0 { vec![lo] } else { vec![] }
    }

    // reference-only
    fn m3(x: u128) -> Vec<u64> {
        let (lo, hi) = (x as u64, (x >> 63) as u64);
        if hi != 0 { vec![lo, hi] } else if lo != 0 { vec![lo] } else { vec![] }
    }

    #[test]
    fn m1_breaks_wf_only() {
        for x in [0u128, 5, 0xFFFF_FFFF_FFFF_FFFF] {
            assert_eq!(value(&m1(x)), x);
            assert!(!wf(&m1(x)));
        }
    }

    #[test]
    fn m2_breaks_the_value() {
        assert_ne!(value(&m2(0x1_0000_0000_0000_0007)), 0x1_0000_0000_0000_0007);
        assert_ne!(value(&m2(0x3_0000_0000_0000_0002)), 0x3_0000_0000_0000_0002);
    }

    #[test]
    fn m3_breaks_the_value() {
        assert_ne!(value(&m3(0xFFFF_FFFF_FFFF_FFFF)), 0xFFFF_FFFF_FFFF_FFFF);
        assert_ne!(value(&m3(0x1_0000_0000_0000_0007)), 0x1_0000_0000_0000_0007);
    }
}

// MUTANTS (open them only after H7 verifies). Each is one change to the code of your
// from_u128 (keep your proof lines):
//   M1: push both limbs, whatever their values.
//   M2: push the high limb first, then the low limb.
//   M3: take the high limb as `(x >> 63u128) as u64`.
// For each: in a scratch copy of the crate, does `scripts/vcheck` still verify your
// contract? And does the Dafny contract accept the matching Dafny output (the check unit's
// `MutantEvaluation` prints `Valid` and `ToNat` for each mutant on the sample; its header
// says where the printed lines are)? If your
// proof breaks, ask whether any proof could succeed: look for a sample row whose output
// breaks the contract.

/*
FIDELITY (learner-owned; advisory: no script reads it). Fill it after H7's suite runs and
after H9.
  mutant | the Verus contract (scripts/vcheck)  | the Dafny contract (the check unit's lines)
  M1     |                                       |
  M2     |                                       |
  M3     |                                       |
  the mirror (H8, H9), "relative to the mirror":
  What does the port promise that the source does not, or the reverse?
*/
