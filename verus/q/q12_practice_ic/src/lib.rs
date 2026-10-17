//! # Q12 — Practice I-C + Lab 1: the practice block (Exercises)
//!
//! Imports: the given BigNat spine crates `qg_bignat_l1`–`qg_bignat_l5` (`use
//! qg_bignat_l5::*;` brings all five layers' names), the vstd prelude and
//! `core::cmp::Ordering`, nothing else: no earlier exercise crate. The layers are frozen
//! and complete; read them, never edit them. The crate's second file is src/lab1_hand.rs
//! (the module `lab1_hand`, declared below): the Verus half of Lab 1's hand part.
//!
//! How to work this file (the order is the module's; the Dafny file's header,
//! dafny/Q/Q12_PracticeIC/std/Q12_PracticeIC.dfy, has the whole module's steps):
//! 1. Predictions first: the six stage specimens specimens/Q12/P1d.dfy.specimen …
//!    P6v.rs.specimen (their answers go in slots/Q12.slots); record the first tries with
//!    `scripts/firsttry.sh Q12 --check` before you run anything they are about.
//! 2. H3 below, after the Dafny file's H3. Then src/lab1_hand.rs, closed book, as its
//!    header says.
//! 3. Done = `scripts/vcheck --gate verus/q/q12_practice_ic` prints only the summary line
//!    and exits 0, `scripts/vaudit verus/q/q12_practice_ic` reports no finding, AND
//!    `scripts/firsttry.sh Q12 --report --strict` exits 0. The crate's gate covers this
//!    file and src/lab1_hand.rs together.
//! 4. Stuck for 20 minutes? /tutor Q12.
//!
//! This file ships with exactly 1 hole: H3, counted by `scripts/vcheck` (Verus runs with
//! `--no-cheating`, which turns each hole into one counted diagnostic); src/lab1_hand.rs
//! ships 4. Commit every prediction BEFORE you run anything it is about, open later
//! files, or read CI, the registry or the plan: their checks and headers give some
//! predictions away.
//!
//! Item kinds and the slot protocol are in the Dafny file's header. Exit (closed book):
//! src/exit.rs here and the Dafny exit file, scored once by
//! `scripts/firsttry.sh Q12 --exit`; src/exit.rs is never part of this crate's build.
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use qg_bignat_l5::*;

mod lab1_hand;

verus! {

// =========================================================================================
// The prediction block. Q12's six predictions are the stage specimens
// specimens/Q12/P1d.dfy.specimen … P6v.rs.specimen; commit every one of them before you
// read past this block, and record the first tries:
//     scripts/firsttry.sh Q12 --check
// =========================================================================================

// =========================================================================================
// Holes
// =========================================================================================

// item: Q12.H3v S11
// uses: trigger
/// **H3.** A chain of two limb-wise bounds. Each hypothesis is quantified over every
/// position and fires on its own trigger (layer L2's `limb_at`, which reads a missing limb
/// as 0). Prove the conclusion at one position `k` inside `a`: give the verifier the terms
/// its triggers need, and nothing more.
pub proof fn lemma_chain_le(a: Seq<u64>, b: Seq<u64>, c: Seq<u64>, k: int)
    requires
        0 <= k < a.len(),
        forall|j: int| 0 <= j ==> #[trigger] limb_at(a, j) <= limb_at(b, j),
        forall|j: int| 0 <= j ==> #[trigger] limb_at(b, j) <= limb_at(c, j),
    ensures
        a[k] as nat <= limb_at(c, k),
{
    #[verifier::proof_note("Q12.H3v")] assume(false);  // HOLE: replace this line
}
// Hint: which term does each hypothesis wait for at `k`, and which of them does the
//    conclusion already hold?

} // verus!
