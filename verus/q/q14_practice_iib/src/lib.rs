//! # Q14 — Practice II-B: the Verus half (Exercises)
//!
//! Imports: the given BigNat spine crates `qg_bignat_l1`–`qg_bignat_l6` (`use
//! qg_bignat_l6::*;` brings all six layers' names), the vstd prelude and
//! `vstd::arithmetic::mul`, nothing else: no earlier exercise crate. The layers are frozen
//! and complete; read them, never edit them. The crate's second file is src/perm.rs (the
//! module `perm`, declared below), which also uses vstd's simple pointers.
//!
//! How to work this file (the order is the module's; the Dafny file's header,
//! dafny/Q/Q14_PracticeIIB/std/Q14_PracticeIIB.dfy, gives it in full):
//! 1. Predictions first: the module's prediction is in the Dafny file's prediction block
//!    (its answer goes in slots/Q14.slots); record the first try with
//!    `scripts/firsttry.sh Q14 --check` before you run anything it is about.
//! 2. Each item ships its statement and nothing else: no skeleton. Each item allows at
//!    most one lemma of your own, in its `HELPERS` area above the item. H2 here, then H3;
//!    H5 is in src/perm.rs.
//! 3. Done = `scripts/vcheck --gate verus/q/q14_practice_iib` prints only the summary line
//!    and exits 0, `scripts/vaudit verus/q/q14_practice_iib` reports no finding, AND
//!    `scripts/firsttry.sh Q14 --report --strict` exits 0. The crate's gate covers this
//!    file and src/perm.rs together.
//! 4. Stuck for 20 minutes? /tutor Q14.
//!
//! This file ships with exactly 4 holes: H2's three methods and H3, each counted by
//! `scripts/vcheck` (Verus runs with `--no-cheating`, which turns each hole into one
//! counted diagnostic); src/perm.rs ships 2. Commit every prediction BEFORE you run
//! anything it is about, open later files, or read CI, the registry or the plan: their
//! checks and headers give some predictions away.
//!
//! Item kinds and the slot protocol are in the Dafny file's header. Exit (closed book,
//! timed): the Dafny exit file; src/exit.rs ships with no block and is never part of this
//! crate's build.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l6::*;

mod perm;

verus! {

// =========================================================================================
// A trait with a ghost view
// =========================================================================================

/// Given (not an item): an accumulator seen through its ghost total.
pub trait Accum: Sized {
    spec fn total(&self) -> nat;

    fn add_word(&mut self, x: u64)
        requires
            old(self).total() + x < BASE * BASE,
        ensures
            final(self).total() == old(self).total() + x,
    ;

    fn read(&self) -> (r: BigNat)
        ensures
            r.wf(),
            r.to_nat() == self.total(),
    ;

    fn from_big(a: &BigNat) -> (r: Option<Self>)
        requires
            a.wf(),
        ensures
            r is Some <==> a.to_nat() < BASE * BASE,
            r is Some ==> r->0.total() == a.to_nat(),
    ;
}

/// Given (not an item): a generic client, which sees an accumulator only through `total`.
pub fn add_both<A: Accum>(acc: &mut A, x: u64, y: u64)
    requires
        old(acc).total() + x + y < BASE * BASE,
    ensures
        final(acc).total() == old(acc).total() + x + y,
{
    acc.add_word(x);
    acc.add_word(y);
}

/// Given (not an item): a two-limb accumulator.
pub struct PairAcc {
    pub lo: u64,
    pub hi: u64,
}

// item: Q14.H2v S6
// uses: trait-spec
/// **H2.** Implement `Accum` for `PairAcc`, whose view ships: `total` is `lo + BASE * hi`.
/// Write the three methods and their proofs (three holes, one item). No skeleton: each
/// method's contract is the trait's. Where can `lo + x` overflow, and what does the
/// trait's precondition say about `hi` then? How many limbs can a canonical `BigNat` below
/// `BASE * BASE` have, and which layer lemma rules out the rest?
impl Accum for PairAcc {
    open spec fn total(&self) -> nat {
        self.lo as nat + BASE * self.hi as nat
    }

    #[verifier::external_body]  // HOLE: remove this line and implement
    fn add_word(&mut self, x: u64) {
        unimplemented!()
    }

    #[verifier::external_body]  // HOLE: remove this line and implement
    fn read(&self) -> (r: BigNat) {
        unimplemented!()
    }

    #[verifier::external_body]  // HOLE: remove this line and implement
    fn from_big(a: &BigNat) -> (r: Option<Self>) {
        unimplemented!()
    }
}
// Hint: `seq_to_nat` unfolds from the low limb, one `drop_first` at a time; a canonical
//    `read` result has no top zero limb.

fn pair_acc_check() {
    // Uncomment as you go:
    // let mut acc = PairAcc { lo: u64::MAX, hi: 0 };
    // add_both(&mut acc, 1, 2);
    // let r = acc.read();
    // assert(r.to_nat() == u64::MAX as nat + 3);
    // let b = BigNat { limbs: Vec::new() };
    // let z = PairAcc::from_big(&b);
    // assert(z is Some);
}

// =========================================================================================
// Erasure (H3's Verus half; work it before H3's Dafny half)
// =========================================================================================

/// Given (not an item): the sum of the limbs, defined from the top limb.
pub open spec fn limb_sum(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 { 0 } else { limb_sum(s.drop_last()) + s.last() as nat }
}

// HELPERS (Q14.H3v): at most one proof fn of your own, here.

// item: Q14.H3v S7
// uses: ghost, invariant, lemma-recursion
// pair: Q14.H3d
// form: loop-dir:i:down
/// **H3.** The sum of the limbs as a `u128`. The bound on the limbs is ghost: the code
/// never reads it, and no exec line may (Verus refuses one that does); it is there for the
/// proof that the sum does not overflow. Write the loop **from the top limb down** (`i`
/// counting from `v.len()` to 0, each limb read at an index that counts with `i`) and its
/// proof. No skeleton: the invariant is yours. What does the loop know about the limbs it
/// has added, and which product bounds their sum?
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn sum_limbs(v: &Vec<u64>, Ghost(bound): Ghost<nat>) -> (r: u128)
    requires
        forall|i: int| 0 <= i < v.len() ==> v@[i] <= bound,
        v.len() * bound <= u128::MAX,
    ensures
        r == limb_sum(v@),
{
    unimplemented!()
}
// Hint: `limb_sum` peels the top limb; a loop going down adds the low limb of what is left
//    to it: one lemma of your own relates the two ends. `vstd::arithmetic::mul` has the
//    product inequalities.

fn sum_limbs_check() {
    // Uncomment as you go:
    // let mut v: Vec<u64> = Vec::new();
    // v.push(7);
    // v.push(u64::MAX);
    // let r = sum_limbs(&v, Ghost(u64::MAX as nat));
    // proof {
    //     assert(v@.drop_last() =~= seq![7u64]);
    //     assert(v@.drop_last().drop_last() =~= Seq::<u64>::empty());
    //     assert(limb_sum(Seq::<u64>::empty()) == 0);
    //     assert(limb_sum(v@.drop_last()) == 7);
    // }
    // assert(r == 7 + u64::MAX as u128);
}

} // verus!
