//! # Q08 — the permissions module of the Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q08_internals_ii/src/perm.rs` (author-only; never
//! learner-visible). Same module, imports, names, statements, item markers and order as
//! the exercise file; every hole is filled and every check is live. The exec items declare
//! their `// triv:` bodies for the empty-body gate's TRIV mode. Silent under
//! `scripts/vcheck --ref` on the crate.
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
/// **H5v.** Add one to a cell's value, through a mutable borrow of its permission.
///
/// Reference: read through a shared reborrow of the permission, `Tracked(&*perm)`, then
/// write through the mutable borrow itself, `Tracked(perm)`. `write`'s postcondition keeps
/// the permission's `id()` and gives its new value; the precondition rules out overflow.
pub fn bump(cell: &PCell<u64>, Tracked(perm): Tracked<&mut PointsTo<u64>>)
    requires
        cell.id() == old(perm).id(),
        *old(perm).value() < u64::MAX,
    ensures
        final(perm).id() == cell.id(),
        *final(perm).value() == *old(perm).value() + 1,
{
    let v = cell.read(Tracked(&*perm));
    cell.write(Tracked(perm), v + 1);
}
// triv: { }

fn bump_check() {
    // reference-only: live in the twin, commented in the learner crate
    let (cell, Tracked(mut perm)) = PCell::new(4u64);
    bump(&cell, Tracked(&mut perm));
    assert(*perm.value() == 5);
}

// item: Q08.H6v S8
// uses: tracked
/// **H6v.** Move the value of one cell into another, through both permissions.
///
/// Reference: read both values (each through a shared reborrow of its permission), then
/// write 0 into `src` and the sum into `dst`, each through its own mutable borrow. The
/// precondition makes the sum a `u64`; each permission's `id()` survives its write.
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
    let a = src.read(Tracked(&*ps));
    let b = dst.read(Tracked(&*pd));
    src.write(Tracked(ps), 0);
    dst.write(Tracked(pd), b + a);
}
// triv: { }

fn transfer_check() {
    // reference-only: live in the twin, commented in the learner crate
    let (s, Tracked(mut ps)) = PCell::new(3u64);
    let (d, Tracked(mut pd)) = PCell::new(4u64);
    transfer(&s, &d, Tracked(&mut ps), Tracked(&mut pd));
    assert(*ps.value() == 0 && *pd.value() == 7);
}

} // verus!
