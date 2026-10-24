//! # Q33 — The statement problem: the dev prose items, Verus half (Exercises)
//!
//! Six prose tasks (QPLAN §35.1: part A's hand calibration). Each ships an exec fn's
//! signature and its implementation, with the loop bounds its code needs to be safe, and no
//! specification: you write its `requires` and `ensures` from the prose. Its code is given;
//! you may add proof (invariants, `proof { … }` blocks, assertions), never change its code.
//! Then uncomment the use-site check in its client, write a non-vacuity witness (one call
//! whose `requires` hold) in its witness fn, and delete the client's assume. The statements
//! you write by hand calibrate your pipeline's self-checks.
//!
//! What grades a specification: the use-site check, your witness, /review-code, and, in the
//! grader container, a hidden two-way check against the author's specification. The frozen
//! parts of this file (every item but the six prose fns) are pinned by src/statements.rs
//! (`[[against]]` in Q33_Statement.toml).
//!
//! This file ships with exactly 6 holes (H5v-H10v), each counted by `scripts/vcheck`: one
//! labelled assume per client.
#![allow(unused_imports, unused_variables, unused_mut)]
use vstd::prelude::*;

verus! {

// item: Q33.H5v S12
// uses: ensures, witness
// prose: leading_at_most
/// **H5.** Prose task. *How many elements at the front of v are at most x: every one before the count is at most x, and the element at the count (if any) exceeds x.* Write `leading_at_most`'s specification.
pub fn leading_at_most(v: &Vec<i64>, x: i64) -> (i: usize)
{
    let mut i: usize = 0;
    while i < v.len() && v[i] <= x
        invariant
            i <= v.len(),
        decreases v.len() - i,
    {
        i = i + 1;
    }
    i
}

fn leading_at_most_use() {
    #[verifier::proof_note("Q33.H5v")] assume(false);  // HOLE: delete once leading_at_most is specified
    // Uncomment as you go:
    // let mut v: Vec<i64> = Vec::new();
    // v.push(1); v.push(5); v.push(2);
    // let i = leading_at_most(&v, 3);
    // assert(v[0] == 1 && v[1] == 5);
    // assert(i == 1);
}

/// Your non-vacuity witness for `leading_at_most`: one call whose `requires` hold.
fn leading_at_most_witness() {
}

// item: Q33.H6v S12
// uses: ensures, witness
// prose: merge_from_a
/// **H6.** Prose task. *Which list the next element of the merge of two ascending lists a and b (not both empty) comes from: true for a when a is not empty and its head is at most b's (or b is empty), false for b otherwise.* Write `merge_from_a`'s specification.
pub fn merge_from_a(a: &Vec<i64>, b: &Vec<i64>) -> (from_a: bool)
{
    if a.len() == 0 {
        false
    } else if b.len() == 0 {
        true
    } else {
        a[0] <= b[0]
    }
}

fn merge_from_a_use() {
    #[verifier::proof_note("Q33.H6v")] assume(false);  // HOLE: delete once merge_from_a is specified
    // Uncomment as you go:
    // let mut a: Vec<i64> = Vec::new(); a.push(2);
    // let mut b: Vec<i64> = Vec::new(); b.push(2);
    // let f = merge_from_a(&a, &b);
    // assert(f);
}

/// Your non-vacuity witness for `merge_from_a`: one call whose `requires` hold.
fn merge_from_a_witness() {
}

// item: Q33.H7v S12
// uses: ensures, witness
// prose: first_run_length
/// **H7.** Prose task. *How many elements at the front of the non-empty vector v equal its first element: the length of its first run.* Write `first_run_length`'s specification.
pub fn first_run_length(v: &Vec<i64>) -> (n: usize)
{
    if v.len() == 0 {
        return 0;
    }
    let mut n: usize = 1;
    while n < v.len() && v[n] == v[0]
        invariant
            1 <= n <= v.len(),
        decreases v.len() - n,
    {
        n = n + 1;
    }
    n
}

fn first_run_length_use() {
    #[verifier::proof_note("Q33.H7v")] assume(false);  // HOLE: delete once first_run_length is specified
    // Uncomment as you go:
    // let mut v: Vec<i64> = Vec::new();
    // v.push(4); v.push(4); v.push(1);
    // let n = first_run_length(&v);
    // assert(v[0] == 4 && v[1] == 4 && v[2] == 1);
    // assert(n == 2);
}

/// Your non-vacuity witness for `first_run_length`: one call whose `requires` hold.
fn first_run_length_witness() {
}

// item: Q33.H8v S12
// uses: ensures, witness
// prose: ascending_prefix
/// **H8.** Prose task. *Whether the first k elements of v (k at most its length) are in ascending order: each is no greater than the next.* Write `ascending_prefix`'s specification.
pub fn ascending_prefix(v: &Vec<i64>, k: usize) -> (b: bool)
{
    let mut b = true;
    let mut i: usize = 1;
    while i < k && i < v.len()
        invariant
            1 <= i,
        decreases v.len() - i,
    {
        if v[i - 1] > v[i] {
            b = false;
        }
        i = i + 1;
    }
    b
}

fn ascending_prefix_use() {
    #[verifier::proof_note("Q33.H8v")] assume(false);  // HOLE: delete once ascending_prefix is specified
    // Uncomment as you go:
    // let mut v: Vec<i64> = Vec::new();
    // v.push(1); v.push(3); v.push(2);
    // let b = ascending_prefix(&v, 2);
    // assert(v[0] == 1 && v[1] == 3);
    // assert(b);
}

/// Your non-vacuity witness for `ascending_prefix`: one call whose `requires` hold.
fn ascending_prefix_witness() {
}

// item: Q33.H9v S12
// uses: ensures, witness
// prose: clause_holds
/// **H9.** Prose task. *Whether a clause (a disjunction of literals) is true under an assignment: some literal of it holds. A literal (v, true) is variable v and (v, false) its negation; every variable of the clause is an index into assign.* Write `clause_holds`'s specification.
pub fn clause_holds(lits: &Vec<(usize, bool)>, assign: &Vec<bool>) -> (b: bool)
{
    let mut i: usize = 0;
    while i < lits.len()
        invariant
            i <= lits.len(),
        decreases lits.len() - i,
    {
        let (ix, sign) = lits[i];
        if ix < assign.len() && assign[ix] == sign {
            return true;
        }
        i = i + 1;
    }
    false
}

fn clause_holds_use() {
    #[verifier::proof_note("Q33.H9v")] assume(false);  // HOLE: delete once clause_holds is specified
    // Uncomment as you go:
    // let mut lits: Vec<(usize, bool)> = Vec::new();
    // lits.push((0, false)); lits.push((1, false));
    // let mut assign: Vec<bool> = Vec::new();
    // assign.push(true); assign.push(true);
    // let b = clause_holds(&lits, &assign);
    // assert(lits[0].0 == 0 && lits[1].0 == 1 && !lits[0].1 && !lits[1].1 && assign[0] && assign[1]);
    // assert(!b);
}

/// Your non-vacuity witness for `clause_holds`: one call whose `requires` hold.
fn clause_holds_witness() {
}

// item: Q33.H10v S12
// uses: ensures, witness
// prose: first_nonzero
/// **H10.** Prose task. *Where a digit vector d (most significant digit first) starts once its leading zero digits are dropped: every digit before that index is 0, and the digit at it (if any) is not.* Write `first_nonzero`'s specification.
pub fn first_nonzero(d: &Vec<u8>) -> (r: usize)
{
    let mut r: usize = 0;
    while r < d.len() && d[r] == 0
        invariant
            r <= d.len(),
        decreases d.len() - r,
    {
        r = r + 1;
    }
    r
}

fn first_nonzero_use() {
    #[verifier::proof_note("Q33.H10v")] assume(false);  // HOLE: delete once first_nonzero is specified
    // Uncomment as you go:
    // let mut d: Vec<u8> = Vec::new();
    // d.push(0); d.push(0); d.push(7);
    // let r = first_nonzero(&d);
    // assert(d[0] == 0 && d[1] == 0 && d[2] == 7);
    // assert(r == 2);
}

/// Your non-vacuity witness for `first_nonzero`: one call whose `requires` hold.
fn first_nonzero_witness() {
}

} // verus!
