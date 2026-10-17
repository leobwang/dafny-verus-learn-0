//! Test fixture (tests/wrappers): an invented trait-impl hole item, shipped as
//! the course ships exec holes (`external_body` over `unimplemented!()`), for
//! firsttry's per-method empty-body gate (QPLAN §30 Q65(a)). The item id names
//! no registry item.
use vstd::prelude::*;

verus! {

pub trait Acc: Sized {
    spec fn total(&self) -> nat;

    fn add_one(&mut self)
        requires
            old(self).total() < 100,
        ensures
            final(self).total() == old(self).total() + 1,
    ;

    fn read(&self) -> (r: u64)
        requires
            self.total() < 100,
        ensures
            r as nat == self.total(),
    ;
}

pub struct Pair {
    pub lo: u64,
}

// item: Q98.H2v S9
impl Acc for Pair {
    open spec fn total(&self) -> nat {
        self.lo as nat
    }

    #[verifier::external_body]
    fn add_one(&mut self) {
        unimplemented!()
    }

    #[verifier::external_body]
    fn read(&self) -> (r: u64) {
        unimplemented!()
    }
}

} // verus!
