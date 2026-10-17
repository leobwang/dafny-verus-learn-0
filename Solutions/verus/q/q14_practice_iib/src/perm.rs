//! # Q14 — the permissions module of the Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q14_practice_iib/src/perm.rs` (author-only; never
//! learner-visible). Same imports, names, statements, item markers and order as the
//! exercise module; both holes are filled and the check is live. Each exec method declares
//! its trivial body in a `// triv:` line. Silent under `scripts/vcheck --ref` on the
//! crate.
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
    // triv: push_front: { }
    // triv: sum: { 0 }
    /// **H5.** Reference: `push_front` moves the old head's permission out of the list
    /// (`tracked_swap` with a `None`) into the new node, allocates it with `PPtr::new`, and
    /// keeps the new node's permission in the list; `sum` walks the list with a tracked
    /// shared reference to the current permission, borrowing each node through it and
    /// stepping to the permission the node holds, with the invariant that the running sum
    /// plus the sum of what is left is the total.
    pub fn push_front(&mut self, v: u64)
        requires
            old(self).wf(),
        ensures
            final(self).wf(),
            final(self)@ == seq![v] + old(self)@,
    {
        let tracked mut old_perm: Option<PointsTo<Node>> = None;
        proof {
            tracked_swap(self.perm.borrow_mut(), &mut old_perm);
        }
        let node = Node { val: v, next: self.head, perm: Tracked(old_perm) };
        let (p, Tracked(pt)) = PPtr::new(node);
        self.head = Some(p);
        self.perm = Tracked(Some(pt));
        self.len = Ghost(self.len@ + 1);
    }

    pub fn sum(&self) -> (r: u64)
        requires
            self.wf(),
            vals_sum(self@) <= u64::MAX,
        ensures
            r == vals_sum(self@),
    {
        let mut s: u64 = 0;
        let mut cur = self.head;
        let tracked mut perm: &Option<PointsTo<Node>> = self.perm.borrow();
        let ghost mut n: nat = self.len@;
        while cur.is_some()
            invariant
                chain_wf(cur, *perm, n),
                s + vals_sum(chain_view(cur, *perm, n)) == vals_sum(self@),
                vals_sum(self@) <= u64::MAX,
            decreases n,
        {
            let p = cur.unwrap();
            let tracked pt = perm.tracked_borrow();
            let node: &Node = p.borrow(Tracked(pt));
            proof {
                let rest = chain_view(node.next, node.perm@, (n - 1) as nat);
                assert(chain_view(cur, *perm, n) == seq![node.val] + rest);
                assert((seq![node.val] + rest).drop_first() =~= rest);
            }
            s = s + node.val;
            cur = node.next;
            proof {
                perm = node.perm.borrow();
                n = (n - 1) as nat;
            }
        }
        s
    }
}

fn list_check() {
    let mut l = List::new();
    l.push_front(3);
    l.push_front(4);
    proof {
        assert(l@ =~= seq![4u64, 3u64]);
        assert(seq![4u64, 3u64].drop_first() =~= seq![3u64]);
        assert(seq![3u64].drop_first() =~= Seq::<u64>::empty());
        assert(vals_sum(Seq::<u64>::empty()) == 0);
        assert(vals_sum(seq![3u64]) == 3);
        assert(vals_sum(seq![4u64, 3u64]) == 7);
    }
    let r = l.sum();
    assert(r == 7);
}

} // verus!
