//! # Q17 — the permissions module of the Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q17_practice_iiib/src/perm.rs` (author-only; never
//! learner-visible). Same imports, names, statements, item markers and order as the
//! exercise module; both holes are filled, the learner's helper `grow` is in `HELPERS`
//! (marked `// reference-only`) and the check is live. Each exec method declares its
//! trivial body in a `// triv:` line. Silent under `scripts/vcheck --ref` on the crate.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::cell::pcell_maybe_uninit::*;

verus! {

// =========================================================================================
// A ring buffer of permissioned cells
// =========================================================================================

/// Given (not an item): storage position `i` of a ring of capacity `c` whose first element
/// is at `h` (the wrap is a comparison, not a remainder).
pub open spec fn slot_of(h: int, c: int, i: int) -> int {
    if h + i < c { h + i } else { h + i - c }
}

/// Given (not an item): Q10's ring buffer with one cell per storage slot. `cells` holds a
/// `PCell` per slot; `perms` holds, at index `k`, the tracked permission of `cells[k]`, which
/// says whether that cell holds a value and which one. `head` is the position of the first
/// element and `len` the number of elements; they wrap around the end of the storage.
/// `live(k)`: slot `k` holds one of the `len` elements. `wf` keeps `head` and `len` inside
/// the storage, ties each permission to its cell, and makes exactly the live slots the
/// initialized ones; the view `self@` is the sequence of the `len` elements in order. `new`
/// is given and verified.
pub struct PRing {
    pub cells: Vec<PCell<u64>>,
    pub perms: Tracked<Seq<PointsTo<u64>>>,
    pub head: usize,
    pub len: usize,
}

impl PRing {
    pub open spec fn cap(&self) -> int {
        self.cells@.len() as int
    }

    pub open spec fn slot(&self, i: int) -> int {
        slot_of(self.head as int, self.cap(), i)
    }

    pub open spec fn live(&self, k: int) -> bool {
        if k >= self.head { k - self.head < self.len } else { k + self.cap() - self.head < self.len }
    }

    pub open spec fn wf(&self) -> bool {
        &&& 0 < self.cap() <= 0x4000_0000
        &&& self.head < self.cap()
        &&& self.len <= self.cap()
        &&& self.perms@.len() == self.cap()
        &&& forall|k: int| 0 <= k < self.cap() ==> {
                &&& (#[trigger] self.perms@[k]).id() == self.cells@[k].id()
                &&& (self.perms@[k].is_init() <==> self.live(k))
            }
    }

    pub open spec fn view(&self) -> Seq<u64> {
        Seq::new(self.len as nat, |i: int| self.perms@[self.slot(i)].value())
    }

    pub fn new() -> (r: PRing)
        ensures
            r.wf(),
            r@ == Seq::<u64>::empty(),
    {
        let mut cells: Vec<PCell<u64>> = Vec::new();
        let tracked mut perms: Seq<PointsTo<u64>> = Seq::tracked_empty();
        let mut k: usize = 0;
        while k < 4
            invariant
                k <= 4,
                cells@.len() == k,
                perms.len() == k,
                forall|j: int| 0 <= j < k ==> (#[trigger] perms[j]).id() == cells@[j].id() && perms[j].is_uninit(),
            decreases 4 - k,
        {
            let (c, Tracked(p)) = PCell::empty();
            cells.push(c);
            proof { perms.tracked_push(p); }
            k = k + 1;
        }
        let r = PRing { cells, perms: Tracked(perms), head: 0, len: 0 };
        assert(r@ =~= Seq::<u64>::empty());
        r
    }

    // HELPERS (Q17.H2v): your helper fns, here.
    // reference-only: the learner's helper (growth by moving every element)
    fn grow(&mut self)
        requires
            old(self).wf(),
            old(self).len == old(self).cap(),
            old(self).cap() <= 0x2000_0000,
        ensures
            final(self).wf(),
            final(self)@ == old(self)@,
            final(self).len < final(self).cap(),
    {
        let ghost v0 = self@;
        let n = self.cells.len();
        let ghost h = self.head as int;
        assert forall|j: int| 0 <= j < n implies self.perms@[#[trigger] slot_of(h, n as int, j)].is_init()
            && self.perms@[slot_of(h, n as int, j)].value() == v0[j] by {
            assert(self.slot(j) == slot_of(h, n as int, j));
            assert(self.live(self.slot(j)));
        }
        let mut cells: Vec<PCell<u64>> = Vec::new();
        let tracked mut perms: Seq<PointsTo<u64>> = Seq::tracked_empty();
        let mut i: usize = 0;
        while i < n
            invariant
                n == self.cap() == self.len,
                self.head == h,
                self.head < n <= 0x2000_0000,
                self.perms@.len() == n,
                forall|k: int| 0 <= k < n ==> (#[trigger] self.perms@[k]).id() == self.cells@[k].id(),
                i <= n,
                cells@.len() == i,
                perms.len() == i,
                forall|j: int| 0 <= j < i ==> (#[trigger] perms[j]).id() == cells@[j].id()
                    && perms[j].is_init() && perms[j].value() == v0[j],
                forall|j: int| i <= j < n ==> self.perms@[#[trigger] slot_of(h, n as int, j)].is_init()
                    && self.perms@[slot_of(h, n as int, j)].value() == v0[j],
            decreases n - i,
        {
            let idx = if i < n - self.head { self.head + i } else { i - (n - self.head) };
            assert(idx == slot_of(h, n as int, i as int));
            let ghost ps = self.perms@;
            let tracked p = self.perms.borrow_mut().tracked_borrow_mut(idx as int);
            let x = self.cells[idx].take(Tracked(p));
            assert forall|j: int| i < j < n implies self.perms@[#[trigger] slot_of(h, n as int, j)]
                == ps[slot_of(h, n as int, j)] by {
                assert(slot_of(h, n as int, j) != idx);
            }
            let (c, Tracked(q)) = PCell::new(x);
            cells.push(c);
            proof { perms.tracked_push(q); }
            i = i + 1;
        }
        let mut k: usize = n;
        while k < 2 * n
            invariant
                n <= k <= 2 * n,
                n <= 0x2000_0000,
                cells@.len() == k,
                perms.len() == k,
                forall|j: int| 0 <= j < k ==> (#[trigger] perms[j]).id() == cells@[j].id(),
                forall|j: int| 0 <= j < n ==> (#[trigger] perms[j]).is_init() && perms[j].value() == v0[j],
                forall|j: int| n <= j < k ==> (#[trigger] perms[j]).is_uninit(),
            decreases 2 * n - k,
        {
            let (c, Tracked(p)) = PCell::empty();
            cells.push(c);
            proof { perms.tracked_push(p); }
            k = k + 1;
        }
        self.cells = cells;
        self.perms = Tracked(perms);
        self.head = 0;
        assert(self@ =~= v0);
    }

    // item: Q17.H2v S8
    // uses: tracked, invariant
    // triv: push_back: { }
    // triv: pop_front: { 0 }
    /// **H2.** Reference: `push_back` grows by `grow` (a loop moving each element, in order,
    /// out of its old cell with `take` into a new initialized cell, then a loop of empty
    /// cells) and then `put`s `x` in the free slot; `pop_front` `take`s the head's value. In
    /// each, the one changed permission is borrowed mutably from `perms`, and an assertion
    /// over the other slots, or over the other elements' slots, carries `wf` and the view
    /// across the write.
    pub fn push_back(&mut self, x: u64)
        requires
            old(self).wf(),
            old(self)@.len() < 0x2000_0000,
        ensures
            final(self).wf(),
            final(self)@ == old(self)@.push(x),
    {
        if self.len == self.cells.len() {
            self.grow();
        }
        let ghost v0 = self@;
        let n = self.cells.len();
        let idx = if self.len < n - self.head { self.head + self.len } else { self.len - (n - self.head) };
        assert(idx == self.slot(self.len as int) && !self.live(idx as int));
        let ghost ps = self.perms@;
        let tracked p = self.perms.borrow_mut().tracked_borrow_mut(idx as int);
        self.cells[idx].put(Tracked(p), x);
        self.len = self.len + 1;
        assert forall|k: int| 0 <= k < n && k != idx implies #[trigger] self.perms@[k] == ps[k] by {}
        assert forall|i: int| 0 <= i < self.len - 1 implies #[trigger] self.slot(i) != idx by {}
        assert(self@ =~= v0.push(x));
    }

    pub fn pop_front(&mut self) -> (r: u64)
        requires
            old(self).wf(),
            old(self).len > 0,
        ensures
            final(self).wf(),
            r == old(self)@[0],
            final(self)@ == old(self)@.drop_first(),
    {
        let ghost v0 = self@;
        let h = self.head;
        assert(self.live(h as int));
        let tracked p = self.perms.borrow_mut().tracked_borrow_mut(h as int);
        let r = self.cells[h].take(Tracked(p));
        self.head = if h + 1 == self.cells.len() { 0 } else { h + 1 };
        self.len = self.len - 1;
        assert(self@ =~= v0.drop_first());
        r
    }
}

/// A check of the ring's operations.
fn ring_check() {
    let mut q = PRing::new();
    q.push_back(1);
    q.push_back(2);
    q.push_back(3);
    q.push_back(4);
    q.push_back(5);
    assert(q@ =~= seq![1u64, 2, 3, 4, 5]);
    let a = q.pop_front();
    assert(a == 1 && q@ =~= seq![2u64, 3, 4, 5]);
}

} // verus!
