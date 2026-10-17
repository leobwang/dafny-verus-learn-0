//! Test fixture (tests/wrappers): an invented exec item whose ghost sequence
//! is updated in `proof` blocks that directly follow an if/else and a loop
//! (QPLAN §6 Q9: the empty-body variants must strip them with the ghost let).
use vstd::prelude::*;

verus! {

pub fn count_big(v: &Vec<u64>) -> (r: usize)
    ensures
        r <= v.len(),
{
    let mut i: usize = 0;
    let mut r: usize = 0;
    let ghost mut c: Seq<nat> = seq![];
    while i < v.len()
        invariant
            i <= v.len(),
            r <= i,
            c.len() == i,
        decreases v.len() - i,
    {
        if v[i] > 10 {
            r = r + 1;
        } else {
            r = r + 0;
        }
        proof {
            c = c.push(r as nat);
        }
        i = i + 1;
    }
    proof {
        assert(c.len() == v.len());
    }
    r
}

} // verus!
