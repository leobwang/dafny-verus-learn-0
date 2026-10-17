//! # Q08 — the permissions module of the Verus half (Exercises)
//!
//! The module `perm` of the crate `q08_internals_ii` (the crate root, src/lib.rs,
//! declares it with `mod perm;`). Imports: the vstd prelude, vstd's permissioned cells
//! (`vstd::cell::pcell`) and the given BigNat spine (`use qg_bignat_l4::*;`). This is the
//! only file of Q08 that uses a cell.
//!
//! How to work this file:
//! 1. Work it after src/lib.rs (commit every Q08 prediction first; P2 is about
//!    permissions).
//! 2. Read the worked example W3 and the card C3, then replace each hole and uncomment the
//!    check beneath it. Read the hint only when stuck.
//! 3. Done = `scripts/vcheck --gate verus/q/q08_internals_ii` prints only the summary line
//!    and exits 0, `scripts/vaudit verus/q/q08_internals_ii` reports no finding, AND
//!    `scripts/firsttry.sh Q08 --report --strict` exits 0.
//! 4. Stuck for 20 minutes? /tutor Q08.
//!
//! This file ships with exactly 2 holes, H5 and H6, each counted by `scripts/vcheck` on the
//! crate. Item kinds and the slot protocol: the header of
//! dafny/Q/Q08_InternalsII/std/Q08_InternalsII.dfy.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::cell::pcell::*;
use qg_bignat_l4::*;

verus! {

// =========================================================================================
// Worked example
// =========================================================================================

// item: Q08.W3v S8
/// **W3.** A permissioned cell, start to finish. `PCell::new` returns the cell and, as a
/// tracked ghost value, the one permission to it, a `PointsTo`: its `id()` is the cell's
/// and its `value()` is (a reference to) what the cell holds. Every operation on the cell
/// passes the permission in: a shared borrow, `Tracked(&perm)`, to read; a mutable borrow,
/// `Tracked(&mut perm)`, to write; and the permission itself, moved, to take the value back
/// out with `into_inner`. The verifier tracks the cell's contents through the permission
/// alone.
pub fn cell_round_trip() -> (r: u64)
    ensures
        r == 9,
{
    let (cell, Tracked(mut perm)) = PCell::new(5u64);
    cell.write(Tracked(&mut perm), 9);
    let v = cell.read(Tracked(&perm));
    assert(v == 9);
    cell.into_inner(Tracked(perm))
}

// =========================================================================================
// WRITE card (a success here, a pinned failure demo in specimens/Q08/)
// =========================================================================================

// item: Q08.C3v S8 write:tracked
// C3 — card: tracked permission arguments.
// Jurisdiction: a function that works on a cell it does not own. It takes the cell's
// permission as a tracked argument, `Tracked<&PointsTo<T>>` (a shared borrow) or
// `Tracked<&mut PointsTo<T>>` (a mutable one), and its `requires` links the two by `id()`.
// A function that holds a mutable borrow of a permission lends it for a read as
// `Tracked(&*perm)`. Success: `peek` and `is_small`. Failure:
// specimens/Q08/card-c3v.rs.specimen (another cell's permission).
pub fn peek(cell: &PCell<u64>, Tracked(perm): Tracked<&PointsTo<u64>>) -> (r: u64)
    requires
        cell.id() == perm.id(),
    ensures
        r == *perm.value(),
{
    cell.read(Tracked(perm))
}

pub fn is_small(cell: &PCell<u64>, Tracked(perm): Tracked<&mut PointsTo<u64>>) -> (b: bool)
    requires
        cell.id() == old(perm).id(),
    ensures
        b == (*old(perm).value() < 10),
{
    proof {
        assert(perm.id() == cell.id());
    }
    let v = peek(cell, Tracked(&*perm));
    v < 10
}

// =========================================================================================
// Holes
// =========================================================================================

// item: Q08.H5v S8
// uses: tracked
/// **H5v.** Add one to a cell's value, through a mutable borrow of its permission. Which
/// borrow of `perm` does each cell operation need, and how do you pass the one you hold?
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn bump(cell: &PCell<u64>, Tracked(perm): Tracked<&mut PointsTo<u64>>)
    requires
        cell.id() == old(perm).id(),
        *old(perm).value() < u64::MAX,
    ensures
        final(perm).id() == cell.id(),
        *final(perm).value() == *old(perm).value() + 1,
{
    unimplemented!()
}
// Hint: a read, then a write; the card shows how a mutable borrow lends itself for a read.

fn bump_check() {
    // Uncomment as you go:
    // let (cell, Tracked(mut perm)) = PCell::new(4u64);
    // bump(&cell, Tracked(&mut perm));
    // assert(*perm.value() == 5);
}

// item: Q08.H6v S8
// uses: tracked
/// **H6v.** Move the value of `src` into `dst`: afterwards `src` holds 0 and `dst` the sum
/// of the two values (the precondition keeps the sum a `u64`). Each cell is reached only
/// through its own permission: which one does each operation take?
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn transfer(
    src: &PCell<u64>,
    dst: &PCell<u64>,
    Tracked(ps): Tracked<&mut PointsTo<u64>>,
    Tracked(pd): Tracked<&mut PointsTo<u64>>,
)
    requires
        src.id() == old(ps).id(),
        dst.id() == old(pd).id(),
        *old(pd).value() as nat + *old(ps).value() as nat <= u64::MAX as nat,
    ensures
        final(ps).id() == src.id(),
        final(pd).id() == dst.id(),
        *final(ps).value() == 0,
        *final(pd).value() == *old(pd).value() + *old(ps).value(),
{
    unimplemented!()
}
// Hint: read both values before you write either.

fn transfer_check() {
    // Uncomment as you go:
    // let (s, Tracked(mut ps)) = PCell::new(3u64);
    // let (d, Tracked(mut pd)) = PCell::new(4u64);
    // transfer(&s, &d, Tracked(&mut ps), Tracked(&mut pd));
    // assert(*ps.value() == 0 && *pd.value() == 7);
}

} // verus!
