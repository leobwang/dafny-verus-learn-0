//! # Q11 — the permissions module of the Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q11_practice_ib/src/perm.rs` (author-only; never
//! learner-visible). Same module, imports, names, statements, item markers and order as
//! the exercise file; the hole is filled and the check is live. The exec item declares its
//! `// triv:` body for the empty-body gate's TRIV mode. Silent under `scripts/vcheck --ref`
//! on the crate.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::cell::pcell::*;
use qg_bignat_l5::*;

verus! {

// item: Q11.H10v S8
// uses: tracked
/// **H10v.** Write into `dst` the larger of the two cells' values.
///
/// Reference: read `src` through its shared permission and `dst` through a shared
/// reborrow of its mutable one, `Tracked(&*pd)`; write only when the source is larger,
/// through the mutable borrow itself. When nothing is written the permission is unchanged,
/// and `write`'s postcondition keeps its `id()` otherwise.
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
    let s = src.read(Tracked(ps));
    let d = dst.read(Tracked(&*pd));
    if s > d {
        dst.write(Tracked(&mut *pd), s);
    }
}
// triv: { }

fn max_into_check() {
    // reference-only: live in the twin, commented in the learner crate
    let (s, Tracked(ps)) = PCell::new(9u64);
    let (d, Tracked(mut pd)) = PCell::new(4u64);
    max_into(&s, &d, Tracked(&ps), Tracked(&mut pd));
    assert(*pd.value() == 9);
    max_into(&s, &d, Tracked(&ps), Tracked(&mut pd));
    assert(*pd.value() == 9);
}

} // verus!
