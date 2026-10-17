//! # qg_bignat_l7::api — the base API of the BigNat mini-crate (PROVIDED, frozen)
//!
//! Part of layer L7 (see `lib.rs`): provided, complete and frozen, never an exercise.
//! `use qg_bignat_l7::*;` brings these names.
//!
//! `BigNatCore` is L4's `NatLike` (zero, one word, addition, multiplication by one word,
//! comparison) plus subtraction (`minus`) and the conversion to one word (`to_word`).
//! `BigNat` implements it with L4's operations and L7's `big_sub` and `to_u64`.
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use qg_bignat_l6::*;
use crate::{big_sub, to_u64};

verus! {

/// The mini-crate's base API: `NatLike` plus subtraction and the conversion to one word.
pub trait BigNatCore: NatLike {
    fn minus(&self, other: &Self) -> (r: Self)
        requires
            self.valid(),
            other.valid(),
            self.value() >= other.value(),
        ensures
            r.valid(),
            r.value() == self.value() - other.value(),
    ;

    fn to_word(&self) -> (r: Option<u64>)
        requires
            self.valid(),
        ensures
            r is Some <==> self.value() < BASE,
            r is Some ==> r->0 as nat == self.value(),
    ;
}

impl BigNatCore for BigNat {
    fn minus(&self, other: &Self) -> (r: Self) {
        big_sub(self, other)
    }

    fn to_word(&self) -> (r: Option<u64>) {
        to_u64(self)
    }
}

} // verus!
