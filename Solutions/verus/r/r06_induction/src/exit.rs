/*! R06 checkpoint (Reference Solution) — CLOSED BOOK,22min.
Four items, two per language: pass at least3/4 with at least1 per language.
Open only for the checkpoint. Keep given definitions and statements fixed.
Record scripts/firsttry.sh R06 --exit; a later observed pass does not replace
the first exit record. No earlier learner file or hand-exercise proof imported.
*/
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
verus! {
// GIVEN: derivative and iteration definitions, count specification and its
// proved bounded exec adapter. These are not checkpoint targets.
pub open spec fn deriv(r: Re, c: char) -> Re
    decreases r,
{
    match r {
        Re::Empty => Re::Empty,
        Re::Eps => Re::Empty,
        Re::Chr(d) => if c == d { Re::Eps } else { Re::Empty },
        Re::Alt(a, b) => Re::Alt(Box::new(deriv(*a, c)), Box::new(deriv(*b, c))),
        Re::Cat(a, b) => if nullable(*a) {
            Re::Alt(Box::new(Re::Cat(Box::new(deriv(*a, c)), b)), Box::new(deriv(*b, c)))
        } else {
            Re::Cat(Box::new(deriv(*a, c)), b)
        },
        Re::Star(a) => Re::Cat(Box::new(deriv(*a, c)), Box::new(Re::Star(a))),
    }
}
pub open spec fn derivs(r: Re, s: Seq<char>) -> Re
    decreases s.len(),
{ if s.len() == 0 { r } else { derivs(deriv(r, s[0]), s.subrange(1, s.len() as int)) } }

pub open spec fn sum_nc(rs: Seq<Re>) -> nat
    decreases rs.len(),
{ if rs.len() == 0 { 0 } else { sum_nc(rs.subrange(0, rs.len()-1)) + node_count(rs[rs.len()-1]) } }

pub proof fn lemma_sum_nc_prefix(rs: Seq<Re>, k: int)
    requires
        0 <= k <= rs.len(),
    ensures
        sum_nc(rs.subrange(0, k)) <= sum_nc(rs),
    decreases rs.len(),
{
    if k == rs.len() {
        assert(rs.subrange(0, k) =~= rs);
    } else {
        let prefix = rs.subrange(0, rs.len()-1);
        assert(prefix.subrange(0, k) =~= rs.subrange(0, k));
        lemma_sum_nc_prefix(prefix, k);
    }
}

pub proof fn lemma_node_bounded_by_sum(rs: Seq<Re>, i: int)
    requires
        0 <= i < rs.len(),
    ensures
        node_count(rs[i]) <= sum_nc(rs),
    decreases rs.len(),
{
    if i < rs.len()-1 {
        let prefix = rs.subrange(0, rs.len()-1);
        assert(prefix[i] == rs[i]);
        lemma_node_bounded_by_sum(prefix, i);
    }
}

pub fn node_count_exec(r: &Re) -> (n: u64)
    requires
        node_count(*r) <= u64::MAX,
    ensures
        n == node_count(*r),
    decreases r,
{
    match r {
        Re::Empty => 1,
        Re::Eps => 1,
        Re::Chr(_) => 1,
        Re::Alt(a, b) => 1 + node_count_exec(a) + node_count_exec(b),
        Re::Cat(a, b) => 1 + node_count_exec(a) + node_count_exec(b),
        Re::Star(a) => 1 + node_count_exec(a),
    }
}

// item: R06.X1v
// uses: lemma-decreases
/// **X1.** Budget 5.5 minutes. Prove the exact general statement, and write
/// the measure its recursion needs.
pub proof fn lemma_derivs_append(r: Re, u: Seq<char>, v: Seq<char>)
    ensures
        derivs(r, u + v) == derivs(derivs(r, u), v),
    decreases u.len(),
{
    // @hole-begin R06.X1v
    if u.len() > 0 {
        assert((u + v)[0] == u[0]);
        assert((u + v).subrange(1, (u + v).len() as int) =~= u.subrange(1, u.len() as int) + v);
        lemma_derivs_append(deriv(r, u[0]), u.subrange(1, u.len() as int), v);
    } else {
    assert(u + v =~= v);
    }
    // @hole-end R06.X1v
}

// item: R06.X2v
// uses: invariant
/// **X2.** Budget 5.5 minutes. Keep the loop and the supplied overflow-support
/// calls; supply its invariants and the facts that connect them.
pub fn sum_node_counts(rs: &Vec<Re>) -> (n: u64)
    requires
        sum_nc(rs@) <= u64::MAX,
    ensures
        n == sum_nc(rs@),
{

    let mut n: u64 = 0;
    let mut i: usize = 0;
    while i < rs.len()
        // @hole-begin R06.X2v
        invariant
            i <= rs.len(),
            n == sum_nc(rs@.subrange(0, i as int)),
            n <= sum_nc(rs@),
            sum_nc(rs@) <= u64::MAX,
        // @hole-end R06.X2v
        decreases rs.len() - i,
    {
        proof {
            lemma_node_bounded_by_sum(rs@, i as int);
            lemma_sum_nc_prefix(rs@, (i + 1) as int);
            // @hole-begin R06.X2v
            assert(rs@.subrange(0, (i + 1) as int).subrange(0, i as int) =~= rs@.subrange(0, i as int));
            // @hole-end R06.X2v
        }
        n = n + node_count_exec(&rs[i]);
        i = i + 1;
    }
    // @hole-begin R06.X2v
    assert(rs@.subrange(0, i as int) =~= rs@);
    // @hole-end R06.X2v
    n
}
}
