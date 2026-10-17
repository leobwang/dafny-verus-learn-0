//! Test fixture (tests/wrappers): an invented exec fn whose code consumes a
//! tracked permission bound by `let tracked`, for the empty-body variant that
//! keeps those lines (QPLAN §30 Q65(b), PLAN §8 R15(a)).
use vstd::prelude::*;
use vstd::simple_pptr::*;

verus! {

pub open spec fn count3(n: nat) -> nat
    decreases n,
{
    if n == 0 { 0 } else { 1 + count3((n - 1) as nat) }
}

pub fn read_slot(p: PPtr<u64>, Tracked(perms): Tracked<&Map<int, PointsTo<u64>>>) -> (r: u64)
    requires
        perms.dom().contains(0),
        perms[0].pptr() == p,
        perms[0].is_init(),
    ensures
        r == perms[0].value(),
        count3(3) == 3,
{
    let tracked perm = perms.tracked_borrow(0);
    proof {
        reveal_with_fuel(count3, 4);
    }
    *p.borrow(Tracked(perm))
}

} // verus!
