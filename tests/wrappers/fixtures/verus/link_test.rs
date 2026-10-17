//! Test fixture (tests/wrappers): a proved lemma beside a test module that links a native
//! library no host has, so `verus --compile --test` verifies and then fails to link.
use vstd::prelude::*;

verus! {

pub proof fn sum_thirteen()
{
    assert(6 + 7 == 13);
}

} // verus!

#[cfg(test)]
mod build_probe {
    #[link(name = "dvl_fixture_no_such_library")]
    extern "C" {
        fn dvl_fixture_absent();
    }

    #[test]
    fn calls_the_absent_library() {
        unsafe { dvl_fixture_absent() }
    }
}
