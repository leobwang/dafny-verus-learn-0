//! Cheat corpus control C-4: a trait with specs and a verified implementation.
use vstd::prelude::*;

verus! {

pub trait Bump {
    fn bump(&self) -> (r: u64)
        requires
            self.valid(),
        ensures
            r > 0;

    spec fn valid(&self) -> bool;
}

pub struct Small {
    pub v: u64,
}

impl Bump for Small {
    open spec fn valid(&self) -> bool {
        self.v < 100
    }

    fn bump(&self) -> (r: u64) {
        self.v + 1
    }
}

} // verus!
