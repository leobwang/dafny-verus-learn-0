//! Test fixture (tests/wrappers): a construct Verus does not support.
use vstd::prelude::*;

verus! {

pub fn unsupported(x: u64) -> (r: u64) {
    let v: Vec<u64> = Vec::new();
    let n = v.iter().map(|a| a + 1).count();
    x
}

} // verus!
