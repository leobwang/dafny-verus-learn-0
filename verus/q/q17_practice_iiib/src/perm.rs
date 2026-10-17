//! # Q17 — the permissions module of the Verus half (Exercises)
//!
//! The module `perm` of the crate `q17_practice_iiib` (the crate root, src/lib.rs, declares
//! it with `mod perm;`). Imports: the vstd prelude and vstd's permissioned cells
//! (`vstd::cell::pcell_maybe_uninit`: `PCell` and its permission `PointsTo`, whose cell may
//! hold no value). It does not use the BigNat spine.
//!
//! How to work this file:
//! 1. Work it after H1 (the header of dafny/Q/Q17_PracticeIIIB/std/Q17_PracticeIIIB.dfy
//!    gives the module's order).
//! 2. Replace the two holes of H2 and uncomment the check beneath them. Your own helper fns
//!    go in the `HELPERS` area above the item, inside the `impl`.
//! 3. Done = `scripts/vcheck --gate verus/q/q17_practice_iiib` prints only the summary line
//!    and exits 0, `scripts/vaudit verus/q/q17_practice_iiib` reports no finding, AND
//!    `scripts/firsttry.sh Q17 --report --strict` exits 0.
//! 4. Stuck for 20 minutes? /tutor Q17.
//!
//! This file ships with exactly 2 holes, H2's two operations, counted by `scripts/vcheck`
//! on the crate (Verus runs with `--no-cheating`, which turns each hole into one counted
//! diagnostic). Item kinds: the header of the Dafny file.
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

    // item: Q17.H2v S8
    // uses: tracked, invariant
    /// **H2.** Two operations of the ring. `push_back` appends `x`; when the ring is full it
    /// first moves every element, in order, into new storage of twice the capacity, with a
    /// new cell and permission per slot (`PCell::new`, `PCell::empty`, the tracked
    /// sequence's `tracked_push`). `pop_front` removes and returns the first element. Here
    /// a value leaves a cell through `take` and enters one through `put` (every `PCell`
    /// method that moves a value needs the cell's permission), the permission borrowed
    /// mutably from `perms` (its `tracked_borrow_mut`). No skeleton. Which permissions change in each operation, and
    /// why does `wf` still hold for every other slot? When the storage grows, what does
    /// each loop keep of the old permissions and the new ones?
    #[verifier::external_body]  // HOLE: remove this line and implement
    pub fn push_back(&mut self, x: u64)
        requires
            old(self).wf(),
            old(self)@.len() < 0x2000_0000,
        ensures
            final(self).wf(),
            final(self)@ == old(self)@.push(x),
    {
        unimplemented!()
    }

    #[verifier::external_body]  // HOLE: remove this line and implement
    pub fn pop_front(&mut self) -> (r: u64)
        requires
            old(self).wf(),
            old(self).len > 0,
        ensures
            final(self).wf(),
            r == old(self)@[0],
            final(self)@ == old(self)@.drop_first(),
    {
        unimplemented!()
    }
}

/// A check of the ring's operations.
fn ring_check() {
    // Uncomment as you go:
    // let mut q = PRing::new();
    // q.push_back(1);
    // q.push_back(2);
    // q.push_back(3);
    // q.push_back(4);
    // q.push_back(5);
    // assert(q@ =~= seq![1u64, 2, 3, 4, 5]);
    // let a = q.pop_front();
    // assert(a == 1 && q@ =~= seq![2u64, 3, 4, 5]);
}

} // verus!
