//! # Q07 — the port, `src/port.rs` (Exercises)
//!
//! The module `port` of the crate `q07_internals_i` (the crate root, src/lib.rs, declares it
//! with `mod port;`). Imports: the vstd prelude, vstd's division lemmas
//! (`vstd::arithmetic::div_mod`) and the given BigNat spine (`use qg_bignat_l4::*;`).
//!
//! The D→V port: layer L2's `FromNat` (Dafny), with the contract layer L3's `FromNatCorrect`
//! states, carried over to Verus for the inputs below 2^128. Its Dafny side is the Dafny
//! file's W2 and the check unit dafny/checks/Q07_checks.dfy.
//!
//! How to work this file (after every hole of src/lib.rs and of the Dafny file):
//! 1. H7, the port: its contract and its body. Then uncomment the use-site check below it
//!    and the differential suite at the end of this file, and run both columns of the
//!    sample: `scripts/vcheck --test dafny/checks/Q07_checks.dfy` and `scripts/vcheck --test
//!    verus/q/q07_internals_i`.
//! 2. The mutants (MUTANTS, at the end): for each, does each contract reject it? Fill the
//!    FIDELITY block's rows.
//! 3. H8, the mirror, then H9; then the FIDELITY block's last lines.
//! 4. Done = the crate's done gate (src/lib.rs's header): `scripts/vcheck --gate
//!    verus/q/q07_internals_i`, `scripts/vaudit verus/q/q07_internals_i`, `scripts/vcheck
//!    --test verus/q/q07_internals_i`, `scripts/firsttry.sh Q07 --report --strict`. H7
//!    counts only with no `*`, `/` or `%` in its code (its `form:` line).
//! 5. Stuck for 20 minutes? /tutor Q07.
//!
//! This file ships with exactly 3 holes, H7, H8 and H9, each counted by `scripts/vcheck` on
//! the crate. Item kinds and the slot protocol: the header of
//! dafny/Q/Q07_InternalsI/std/Q07_InternalsI.dfy.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l4::*;

verus! {

// item: Q07.H7v S1
// uses: bit-vector, property-test
// form: bv-exec
/// **H7.** The port. Carry layer L2's `FromNat` and the contract layer L3's
/// `FromNatCorrect` states over to Verus, for the inputs below 2^128, in Verus's terms
/// (`BigNat`, layer L1): write `from_u128`'s `ensures` and its body, splitting `x` by shifts
/// and casts, with no `*`, `/` or `%` in the code (the form). Which of `BigNat`'s spec fns
/// carry `Valid` and `ToNat` over, and what does each say?
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn from_u128(x: u128) -> (r: BigNat)
{
    unimplemented!()
}
// Hint(1): split `x` as H6 splits a double word; the solver needs a `bit_vector` fact for
//    each operation the code uses.
// Hint(2): push only the limbs the contract allows; `seq_to_nat` must unfold once per
//    limb pushed, and once more.

/// H7's use-site check: concrete calls whose results the contract must determine.
fn from_u128_check() {
    // Uncomment as you go:
    // let r = from_u128(0x2_0000_0000_0000_0005u128);
    // assert(r.wf() && r.to_nat() == 0x2_0000_0000_0000_0005);
    // let z = from_u128(0u128);
    // assert(z.wf() && z.to_nat() == 0);
    // let m = from_u128(u128::MAX);
    // assert(m.wf() && m.to_nat() == 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF);
}

// item: Q07.H8v S2
/// **H8.** The mirror. Transcribe layer L2's `FromNat` (Dafny) into this Verus spec fn,
/// from its definition and independently of your code for H7: the same recursion, in
/// Verus's terms. Replace `uninterp` by `open` and the final `;` by a body (the measure
/// ships).
pub uninterp spec fn from_nat_mirror(n: nat) -> Seq<u64>
    decreases n,
;
// Hint(1): `FromNat`'s definition is one line of L2.
// Hint(2): Verus's `%` and `/` on `nat`, and a cast to `u64` for the limb.

// item: Q07.H9v S4
// uses: fuel
/// **H9.** The mirror meets the port's contract, relative to the mirror: for every `x`
/// below 2^128, the mirror's output is canonical and has the value `x`. How many limbs can
/// that output have, and how do you show it?
pub proof fn lemma_mirror_meets_port(x: u128)
    ensures
        seq_wf(from_nat_mirror(x as nat)),
        seq_to_nat(from_nat_mirror(x as nat)) == x as nat,
{
    #[verifier::proof_note("Q07.H9v")] assume(false);  // HOLE: replace this line
}
// Hint(1): first show that `x / BASE` is below `BASE`, so that the recursion stops after
//    two limbs.
// Hint(2): unfold both spec fns far enough, then take each length of the output in turn.

} // verus!

// H7's differential suite: the check unit's sample run (dafny/checks/Q07_checks.dfy), row
// for row, against your port compiled by Verus. Uncomment it once from_u128 verifies.
// Uncomment as you go:
// #[cfg(test)]
// mod port_tests {
//     use super::*;
//
//     #[test]
//     fn sample() {
//         assert_eq!(from_u128(0).limbs, Vec::<u64>::new());
//         assert_eq!(from_u128(5).limbs, vec![5u64]);
//         assert_eq!(from_u128(0xFFFF_FFFF_FFFF_FFFF).limbs, vec![u64::MAX]);
//         assert_eq!(from_u128(0x1_0000_0000_0000_0007).limbs, vec![7u64, 1]);
//         assert_eq!(from_u128(0x3_0000_0000_0000_0002).limbs, vec![2u64, 3]);
//         assert_eq!(from_u128(u128::MAX).limbs, vec![u64::MAX, u64::MAX]);
//     }
// }

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
