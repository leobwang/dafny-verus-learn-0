//! Regex spike, beyond A5 (R16 capstone reference shape): an exec Pike VM (breadth-first
//! thread sets with an `addthread` closure), proved to decide the fuelled acceptance of
//! A5's VM, and the end-to-end `rexc_match` = emit + run, tied to `matches`.
//!
//! Reference material (DVR0 spike, author-only).
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a2::*;
use rg_re_a3::*;
use rg_re_a4::*;
use rg_re_a5::*;

verus! {

/// Some run from `pc` accepts `t`.
pub open spec fn live(p: Seq<Inst>, pc: int, t: Seq<char>) -> bool {
    exists|f: nat| #[trigger] accepts(p, pc, t, f)
}

/// A thread at `v` on input `t` is good: if it can accept, the whole run accepts (`g`).
pub open spec fn thread_ok(p: Seq<Inst>, v: int, t: Seq<char>, g: bool) -> bool {
    live(p, v, t) ==> g
}

/// `v`'s epsilon successors (in range) are in the set.
pub open spec fn succ_closed(p: Seq<Inst>, set: Seq<bool>, v: int) -> bool {
    match p[v] {
        Inst::Split(x, y) => (x < p.len() ==> set[x as int]) && (y < p.len() ==> set[y as int]),
        Inst::Jmp(x) => x < p.len() ==> set[x as int],
        _ => true,
    }
}

/// The thread list holds exactly the set's members.
pub open spec fn list_matches(p: Seq<Inst>, set: Seq<bool>, list: Seq<usize>) -> bool {
    &&& set.len() == p.len()
    &&& forall|k: int| 0 <= k < list.len() ==> (#[trigger] list[k]) < p.len() && set[list[k] as int]
    &&& forall|v: int| 0 <= v < p.len() && #[trigger] set[v] ==> exists|k: int| 0 <= k < list.len() && list[k] == v
}

pub open spec fn count_false(s: Seq<bool>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        count_false(s.drop_last()) + if s.last() { 0nat } else { 1nat }
    }
}

proof fn lemma_count_update(s: Seq<bool>, i: int)
    requires
        0 <= i < s.len(),
        !s[i],
    ensures
        count_false(s.update(i, true)) + 1 == count_false(s),
    decreases s.len(),
{
    let u = s.update(i, true);
    if i == s.len() - 1 {
        assert(u.drop_last() =~= s.drop_last());
    } else {
        assert(u.drop_last() =~= s.drop_last().update(i, true));
        lemma_count_update(s.drop_last(), i);
    }
}

/// Add the thread `pc` and its epsilon closure (Pike's `addthread`).
fn add_thread(
    p: &Vec<Inst>,
    pc: usize,
    set: &mut Vec<bool>,
    list: &mut Vec<usize>,
    Ghost(t): Ghost<Seq<char>>,
    Ghost(g): Ghost<bool>,
)
    requires
        pc < p.len(),
        list_matches(p@, old(set)@, old(list)@),
        thread_ok(p@, pc as int, t, g),
        forall|v: int| 0 <= v < p.len() && old(set)@[v] ==> thread_ok(p@, v, t, g),
    ensures
        list_matches(p@, final(set)@, final(list)@),
        final(set)@[pc as int],
        forall|v: int| 0 <= v < p.len() && old(set)@[v] ==> final(set)@[v],
        forall|v: int| 0 <= v < p.len() && final(set)@[v] ==> thread_ok(p@, v, t, g),
        forall|v: int|
            0 <= v < p.len() && final(set)@[v] && !old(set)@[v] ==> succ_closed(p@, final(set)@, v),
        count_false(final(set)@) <= count_false(old(set)@),
    decreases count_false(old(set)@),
{
    if set[pc] {
        return;
    }
    proof {
        lemma_count_update(set@, pc as int);
    }
    let ghost s0 = set@;
    set.set(pc, true);
    list.push(pc);
    proof {
        assert(list@[list@.len() - 1] == pc);
        assert forall|v: int| 0 <= v < p.len() && #[trigger] set@[v] implies exists|k: int|
            0 <= k < list@.len() && list@[k] == v by {
            if v != pc {
                let k = choose|k: int| 0 <= k < old(list)@.len() && old(list)@[k] == v;
                assert(list@[k] == v);
            }
        }
    }
    let plen = p.len();
    match &p[pc] {
        Inst::Split(x, y) => {
            let x = *x;
            let y = *y;
            let ghost s1 = set@;
            if x < plen {
                proof {
                    if live(p@, x as int, t) {
                        let f = choose|f: nat| #[trigger] accepts(p@, x as int, t, f);
                        assert(accepts(p@, pc as int, t, f + 1));
                    }
                }
                add_thread(p, x, set, list, Ghost(t), Ghost(g));
            }
            let ghost s2 = set@;
            if y < plen {
                proof {
                    if live(p@, y as int, t) {
                        let f = choose|f: nat| #[trigger] accepts(p@, y as int, t, f);
                        assert(accepts(p@, pc as int, t, f + 1));
                    }
                }
                add_thread(p, y, set, list, Ghost(t), Ghost(g));
            }
            proof {
                assert forall|v: int|
                    0 <= v < p.len() && set@[v] && !old(set)@[v] implies succ_closed(p@, set@, v) by {
                    if v != pc && !s1[v] && s2[v] {
                        assert(succ_closed(p@, s2, v));
                    }
                }
            }
        },
        Inst::Jmp(x) => {
            let x = *x;
            let ghost s1 = set@;
            if x < plen {
                proof {
                    if live(p@, x as int, t) {
                        let f = choose|f: nat| #[trigger] accepts(p@, x as int, t, f);
                        assert(accepts(p@, pc as int, t, f + 1));
                    }
                }
                add_thread(p, x, set, list, Ghost(t), Ghost(g));
            }
        },
        _ => {},
    }
}

/// In a closed set, a live thread reaches a live `Char` or `Match` thread of the set.
proof fn lemma_closure(p: Seq<Inst>, set: Seq<bool>, v: int, t: Seq<char>, f: nat) -> (res: (int, nat))
    requires
        set.len() == p.len(),
        0 <= v < p.len(),
        set[v],
        forall|w: int| 0 <= w < p.len() && set[w] ==> #[trigger] succ_closed(p, set, w),
        accepts(p, v, t, f),
    ensures
        0 <= res.0 < p.len(),
        set[res.0],
        p[res.0] is Char || p[res.0] is Match,
        accepts(p, res.0, t, res.1),
    decreases f,
{
    assert(succ_closed(p, set, v));
    match p[v] {
        Inst::Split(x, y) => {
            if accepts(p, x as int, t, (f - 1) as nat) {
                assert(x < p.len());
                lemma_closure(p, set, x as int, t, (f - 1) as nat)
            } else {
                assert(accepts(p, y as int, t, (f - 1) as nat));
                assert(y < p.len());
                lemma_closure(p, set, y as int, t, (f - 1) as nat)
            }
        },
        Inst::Jmp(x) => {
            assert(accepts(p, x as int, t, (f - 1) as nat));
            assert(x < p.len());
            lemma_closure(p, set, x as int, t, (f - 1) as nat)
        },
        _ => (v, f),
    }
}

fn falses(n: usize) -> (v: Vec<bool>)
    ensures
        v@.len() == n,
        forall|i: int| 0 <= i < n ==> !(#[trigger] v@[i]),
{
    let mut v: Vec<bool> = Vec::new();
    while v.len() < n
        invariant
            v@.len() <= n,
            forall|i: int| 0 <= i < v@.len() ==> !(#[trigger] v@[i]),
        decreases n - v.len(),
    {
        v.push(false);
    }
    v
}

/// The Pike VM: decides whether some run from address 0 accepts `s`.
#[verifier::loop_isolation(false)]
pub fn pike_run(p: &Vec<Inst>, s: &Vec<char>) -> (b: bool)
    ensures
        b == live(p@, 0, s@),
{
    let plen = p.len();
    let n = s.len();
    let ghost g = live(p@, 0, s@);
    if plen == 0 {
        assert(!g);
        return false;
    }
    let mut cset = falses(plen);
    let mut clist: Vec<usize> = Vec::new();
    assert(s@.subrange(0, n as int) =~= s@);
    add_thread(p, 0, &mut cset, &mut clist, Ghost(s@), Ghost(g));
    let mut i: usize = 0;
    while i < n
        invariant
            i <= n,
            list_matches(p@, cset@, clist@),
            forall|v: int| 0 <= v < plen && cset@[v] ==> thread_ok(p@, v, s@.subrange(i as int, n as int), g),
            g ==> exists|v: int| 0 <= v < plen && cset@[v] && live(p@, v, s@.subrange(i as int, n as int)),
            forall|v: int| 0 <= v < plen && cset@[v] ==> succ_closed(p@, cset@, v),
        decreases n - i,
    {
        let ghost t = s@.subrange(i as int, n as int);
        let ghost t1 = s@.subrange(i + 1, n as int);
        assert(t.drop_first() =~= t1);
        let c = s[i];
        let mut nset = falses(plen);
        let mut nlist: Vec<usize> = Vec::new();
        let mut k: usize = 0;
        while k < clist.len()
            invariant
                k <= clist.len(),
                list_matches(p@, nset@, nlist@),
                forall|v: int| 0 <= v < plen && nset@[v] ==> thread_ok(p@, v, t1, g),
                forall|v: int| 0 <= v < plen && nset@[v] ==> succ_closed(p@, nset@, v),
                forall|j: int|
                    0 <= j < k ==> match #[trigger] p@[clist@[j] as int] {
                        Inst::Char(d) => d == c && clist@[j] + 1 < plen ==> nset@[clist@[j] + 1],
                        _ => true,
                    },
            decreases clist.len() - k,
        {
            let q = clist[k];
            match &p[q] {
                Inst::Char(d) => {
                    if *d == c && q + 1 < plen {
                        proof {
                            assert(thread_ok(p@, q as int, t, g));
                            if live(p@, (q + 1) as int, t1) {
                                let f = choose|f: nat| #[trigger] accepts(p@, (q + 1) as int, t1, f);
                                assert(accepts(p@, q as int, t, f + 1));
                            }
                        }
                        add_thread(p, q + 1, &mut nset, &mut nlist, Ghost(t1), Ghost(g));
                    }
                },
                _ => {},
            }
            k = k + 1;
        }
        proof {
            if g {
                let v = choose|v: int| 0 <= v < plen && cset@[v] && live(p@, v, t);
                let f = choose|f: nat| #[trigger] accepts(p@, v, t, f);
                let (q, fq) = lemma_closure(p@, cset@, v, t, f);
                let j = choose|j: int| 0 <= j < clist@.len() && clist@[j] == q;
                assert(match p@[clist@[j] as int] {
                    Inst::Char(d) => d == c && clist@[j] + 1 < plen ==> nset@[clist@[j] + 1],
                    _ => true,
                });
                assert(accepts(p@, q + 1, t1, (fq - 1) as nat));
                assert(live(p@, q + 1, t1));
            }
        }
        cset = nset;
        clist = nlist;
        i = i + 1;
    }
    let ghost t = s@.subrange(n as int, n as int);
    assert(t =~= Seq::<char>::empty());
    let mut k: usize = 0;
    while k < clist.len()
        invariant
            k <= clist.len(),
            forall|j: int| 0 <= j < k ==> !(#[trigger] p@[clist@[j] as int] is Match),
        decreases clist.len() - k,
    {
        let q = clist[k];
        if let Inst::Match = &p[q] {
            proof {
                assert(accepts(p@, q as int, t, 1));
                assert(thread_ok(p@, q as int, t, g));
            }
            return true;
        }
        k = k + 1;
    }
    proof {
        if g {
            let v = choose|v: int| 0 <= v < plen && cset@[v] && live(p@, v, t);
            let f = choose|f: nat| #[trigger] accepts(p@, v, t, f);
            let (q, fq) = lemma_closure(p@, cset@, v, t, f);
            let j = choose|j: int| 0 <= j < clist@.len() && clist@[j] == q;
            assert(!(p@[clist@[j] as int] is Match));
        }
    }
    false
}

/// `rexc`: emit `r` to the VM and run it. `None` only when the program would not fit
/// the address space.
pub fn rexc_match(r: &Re, s: &Vec<char>) -> (res: Option<bool>)
    ensures
        res is Some ==> res->Some_0 == matches(*r, s@),
{
    match emit_prog(r) {
        Some(p) => {
            let b = pike_run(&p, s);
            proof {
                lemma_vm_correct(*r, s@);
            }
            Some(b)
        },
        None => None,
    }
}

} // verus!
