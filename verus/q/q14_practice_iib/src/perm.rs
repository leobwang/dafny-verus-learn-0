//! # Q14 — the permissions module of the Verus half (Exercises)
//!
//! The module `perm` of the crate `q14_practice_iib` (the crate root, src/lib.rs, declares
//! it with `mod perm;`). Imports: the vstd prelude, vstd's simple pointers
//! (`vstd::simple_pptr`: `PPtr` and its permission `PointsTo`) and `vstd::modes`. It does
//! not use the BigNat spine. This is the only file of Q14 that uses a pointer.
//!
//! How to work this file:
//! 1. Work it last, after std/Q14_Loop.dfy (the Dafny file's header gives the module's
//!    order).
//! 2. Replace the two holes of H5 and uncomment the check beneath them. Read the hint only
//!    when stuck.
//! 3. Done = `scripts/vcheck --gate verus/q/q14_practice_iib` prints only the summary line
//!    and exits 0, `scripts/vaudit verus/q/q14_practice_iib` reports no finding, AND
//!    `scripts/firsttry.sh Q14 --report --strict` exits 0.
//! 4. Stuck for 20 minutes? /tutor Q14.
//!
//! This file ships with exactly 2 holes, H5's two operations, counted by `scripts/vcheck`
//! on the crate. Item kinds and the slot protocol: the header of
//! dafny/Q/Q14_PracticeIIB/std/Q14_PracticeIIB.dfy.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::simple_pptr::*;
use vstd::modes::*;

verus! {

// =========================================================================================
// A permission node list
// =========================================================================================

/// Given (not an item): one node. `perm` is the tracked permission of the node `next`
/// points to (`None` at the end of the list).
pub struct Node {
    pub val: u64,
    pub next: Option<PPtr<Node>>,
    pub perm: Tracked<Option<PointsTo<Node>>>,
}

/// Given (not an item): `n` nodes from `p`, each reached through the permission its
/// predecessor holds (`perm` for the first).
pub open spec fn chain_wf(p: Option<PPtr<Node>>, perm: Option<PointsTo<Node>>, n: nat) -> bool
    decreases n,
{
    if n == 0 {
        p is None && perm is None
    } else {
        &&& p is Some
        &&& perm is Some
        &&& perm->0.pptr() == p->0
        &&& perm->0.is_init()
        &&& chain_wf(perm->0.value().next, perm->0.value().perm@, (n - 1) as nat)
    }
}

/// Given (not an item): the values of those `n` nodes, in list order.
pub open spec fn chain_view(p: Option<PPtr<Node>>, perm: Option<PointsTo<Node>>, n: nat) -> Seq<
    u64,
>
    decreases n,
{
    if n == 0 {
        Seq::<u64>::empty()
    } else {
        seq![perm->0.value().val] + chain_view(
            perm->0.value().next,
            perm->0.value().perm@,
            (n - 1) as nat,
        )
    }
}

/// Given (not an item): the sum of a sequence of words, from the front.
pub open spec fn vals_sum(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s[0] as nat + vals_sum(s.drop_first())
    }
}

/// Given (not an item): the list. `perm` is the permission of the head node; `len` is the
/// ghost number of nodes.
pub struct List {
    pub head: Option<PPtr<Node>>,
    pub perm: Tracked<Option<PointsTo<Node>>>,
    pub len: Ghost<nat>,
}

impl View for List {
    type V = Seq<u64>;

    open spec fn view(&self) -> Seq<u64> {
        chain_view(self.head, self.perm@, self.len@)
    }
}

impl List {
    pub open spec fn wf(&self) -> bool {
        chain_wf(self.head, self.perm@, self.len@)
    }

    /// Given (not an item): the empty list.
    pub fn new() -> (l: List)
        ensures
            l.wf(),
            l@ == Seq::<u64>::empty(),
    {
        List { head: None, perm: Tracked(None), len: Ghost(0) }
    }

    // item: Q14.H5v S8
    // uses: tracked
    /// **H5.** A singly linked list of `PPtr` nodes in which each node carries the tracked
    /// permission of the next one: one permission per node, and no map. Two operations:
    /// `push_front` puts a new node in front, and `sum` adds the values in a loop that
    /// borrows each node's permission in turn. No skeleton. Where is the old head's
    /// permission before the new node exists, and how does it get into the node? In `sum`,
    /// what does the loop hold of the node it is at, and what does it hand to the next
    /// step?
    #[verifier::external_body]  // HOLE: remove this line and implement
    pub fn push_front(&mut self, v: u64)
        requires
            old(self).wf(),
        ensures
            final(self).wf(),
            final(self)@ == seq![v] + old(self)@,
    {
        unimplemented!()
    }

    #[verifier::external_body]  // HOLE: remove this line and implement
    pub fn sum(&self) -> (r: u64)
        requires
            self.wf(),
            vals_sum(self@) <= u64::MAX,
        ensures
            r == vals_sum(self@),
    {
        unimplemented!()
    }
    // Hint: a tracked field cannot be moved out of `&mut self` as it stands, but
    //    `vstd::modes` can exchange it for another value; a tracked `&` reference, like a
    //    ghost variable, may be reassigned inside a proof block.
}

fn list_check() {
    // Uncomment as you go:
    // let mut l = List::new();
    // l.push_front(3);
    // l.push_front(4);
    // proof {
    //     assert(l@ =~= seq![4u64, 3u64]);
    //     assert(seq![4u64, 3u64].drop_first() =~= seq![3u64]);
    //     assert(seq![3u64].drop_first() =~= Seq::<u64>::empty());
    //     assert(vals_sum(Seq::<u64>::empty()) == 0);
    //     assert(vals_sum(seq![3u64]) == 3);
    //     assert(vals_sum(seq![4u64, 3u64]) == 7);
    // }
    // let r = l.sum();
    // assert(r == 7);
}

} // verus!
