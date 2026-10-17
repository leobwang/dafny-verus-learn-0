//! # Q11 — the permissions module of the Verus half (Exercises)
//!
//! The module `perm` of the crate `q11_practice_ib` (the crate root, src/lib.rs, declares
//! it with `mod perm;`). Imports: the vstd prelude, vstd's permissioned cells
//! (`vstd::cell::pcell`) and the given BigNat spine (`use qg_bignat_l5::*;`). This is the
//! only file of Q11 that uses a cell.
//!
//! How to work this file:
//! 1. Work it last, after std/Q11_Wp.dfy (the Dafny file's header gives the module's
//!    order).
//! 2. Replace the hole and uncomment the check beneath it. Read the hint only when stuck.
//! 3. Done = `scripts/vcheck --gate verus/q/q11_practice_ib` prints only the summary line
//!    and exits 0, `scripts/vaudit verus/q/q11_practice_ib` reports no finding, AND
//!    `scripts/firsttry.sh Q11 --report --strict` exits 0.
//! 4. Stuck for 20 minutes? /tutor Q11.
//!
//! This file ships with exactly 1 hole, H10, counted by `scripts/vcheck` on the crate.
//! Item kinds and the slot protocol: the header of
//! dafny/Q/Q11_PracticeIB/std/Q11_PracticeIB.dfy.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::cell::pcell::*;
use qg_bignat_l5::*;

verus! {

// item: Q11.H10v S8
// uses: tracked
/// **H10v.** A points-to primer. Write into `dst` the larger of the two cells' values,
/// reaching each cell only through its own permission: `ps`, borrowed shared, for `src`,
/// and `pd`, borrowed mutably, for `dst`. Which borrow does each cell operation take, and
/// how do you lend the mutable one for a read?
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn max_into(
    src: &PCell<u64>,
    dst: &PCell<u64>,
    Tracked(ps): Tracked<&PointsTo<u64>>,
    Tracked(pd): Tracked<&mut PointsTo<u64>>,
)
    requires
        src.id() == ps.id(),
        dst.id() == old(pd).id(),
    ensures
        final(pd).id() == dst.id(),
        *final(pd).value() == if *ps.value() > *old(pd).value() {
            *ps.value()
        } else {
            *old(pd).value()
        },
{
    unimplemented!()
}
// Hint: a write is needed only in one case; in the other, what holds of `pd` already?

fn max_into_check() {
    // Uncomment as you go:
    // let (s, Tracked(ps)) = PCell::new(9u64);
    // let (d, Tracked(mut pd)) = PCell::new(4u64);
    // max_into(&s, &d, Tracked(&ps), Tracked(&mut pd));
    // assert(*pd.value() == 9);
    // max_into(&s, &d, Tracked(&ps), Tracked(&mut pd));
    // assert(*pd.value() == 9);
}

} // verus!
