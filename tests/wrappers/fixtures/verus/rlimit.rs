//! Test fixture (tests/wrappers): a nonlinear goal that runs out of rlimit.
use vstd::prelude::*;

verus! {

pub proof fn cubes(x: int, y: int, z: int)
    requires
        x > 0,
        y > 0,
        z > 0,
    ensures
        x * x * x + y * y * y != z * z * z,
{
    assert(x * x * x + y * y * y != z * z * z) by (nonlinear_arith)
        requires
            x > 0,
            y > 0,
            z > 0,
    ;
}

} // verus!
