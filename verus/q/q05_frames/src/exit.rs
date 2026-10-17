//! # Q05 — exit, Verus half (closed book)
//!
//! Closed book: keep the chapter, the exercise files, later modules' files, search tools
//! and /tutor closed. At most the given spine (verus/given/) may be open.
//!
//! This file ships with exactly 2 holes (X1, X2); the Dafny half
//! (dafny/Q/Q05_Frames/exit/Q05_Exit.dfy) ships with 2 holes. Score both halves in one
//! sitting with
//!
//!     scripts/firsttry.sh Q05 --exit
//!
//! Threshold: 3 of the 4 exit items, with at least 1 of the 2 in each language. The first
//! full run (every block attempted) is the score; repair every block afterwards, after
//! which the strict gate covers this file too. This file is never `mod`-declared and is in
//! no build: work it with `scripts/vcheck verus/q/q05_frames/src/exit.rs`.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l3::*;

verus! {

// Given (not items): an account type and its failure, for X1.
pub struct Short;

pub struct Account {
    pub bal: u64,
    pub cap: u64,
}

// Given (not items): a one-digit parser and its errors, for X2.
pub enum ParseError {
    Empty,
    NotDigit,
    Overflow,
}

pub open spec fn is_digit(c: u8) -> bool {
    48 <= c <= 57
}

/// Parse a field of exactly one decimal digit.
pub fn parse_digit(t: &[u8]) -> (r: Result<u64, ParseError>)
    ensures
        r is Ok <==> (t@.len() == 1 && is_digit(t@[0])),
        r is Ok ==> r->Ok_0 == t@[0] - 48,
{
    if t.len() != 1 {
        return Err(ParseError::Empty);
    }
    if t[0] < 48 || t[0] > 57 {
        return Err(ParseError::NotDigit);
    }
    Ok((t[0] - 48) as u64)
}

// item: Q05.X1v S6
// uses: mut-ref, result
// need: pub fn transfer(from: &mut Account, to: &mut Account, k: u64) -> (r: Result<(), Short>)
// need: r is Ok <==> (k <= old(from).bal && old(to).bal + k <= old(to).cap)
/// **X1.** Move `k` units from `from` to `to`: `Ok` exactly when `from` holds `k` and `to`
/// has room for them, with `k` moved; on `Err`, both accounts unchanged.
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn transfer(from: &mut Account, to: &mut Account, k: u64) -> (r: Result<(), Short>)
    requires
        old(from).bal <= old(from).cap,
        old(to).bal <= old(to).cap,
    ensures
        final(from).cap == old(from).cap,
        final(to).cap == old(to).cap,
        final(from).bal <= final(from).cap,
        final(to).bal <= final(to).cap,
        r is Ok <==> (k <= old(from).bal && old(to).bal + k <= old(to).cap),
        r is Ok ==> final(from).bal == old(from).bal - k && final(to).bal == old(to).bal + k,
        r is Err ==> final(from).bal == old(from).bal && final(to).bal == old(to).bal,
{
    unimplemented!()
}

// item: Q05.X2v S6
// uses: error-propagation
// need: pub fn parse_pair(a: &[u8], b: &[u8]) -> (r: Result<(u64, u64), ParseError>)
// need: r is Ok <==> (a@.len() == 1 && is_digit(a@[0]) && b@.len() == 1 && is_digit(b@[0]))
/// **X2.** Parse two one-digit fields with the given `parse_digit`, propagating the first
/// failure with `?`.
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn parse_pair(a: &[u8], b: &[u8]) -> (r: Result<(u64, u64), ParseError>)
    ensures
        r is Ok <==> (a@.len() == 1 && is_digit(a@[0]) && b@.len() == 1 && is_digit(b@[0])),
{
    unimplemented!()
}

} // verus!
