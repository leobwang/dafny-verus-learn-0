//! Regex spike, R11 gated item: an NFA arena on the heap with tracked permissions.
//! Each VM instruction lives in its own heap cell (`PPtr<Inst>`); the arena owns a tracked
//! map from index to `PointsTo<Inst>`, and a ghost model `Seq<Inst>` ties the cells to A5's
//! program view. Feasibility only: build from a program, read and write cells through the
//! permissions, run the verified Pike VM over the arena's view, and free every cell.
//!
//! Reference material (DVR0 spike, author-only).
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::simple_pptr::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a5::*;
use rg_rexc::*;

verus! {

pub fn copy_inst(i: &Inst) -> (out: Inst)
    ensures
        out == *i,
{
    match i {
        Inst::Char(c) => Inst::Char(*c),
        Inst::Split(x, y) => Inst::Split(*x, *y),
        Inst::Jmp(x) => Inst::Jmp(*x),
        Inst::Match => Inst::Match,
    }
}

pub struct Arena {
    ptrs: Vec<PPtr<Inst>>,
    perms: Tracked<Map<int, PointsTo<Inst>>>,
    model: Ghost<Seq<Inst>>,
}

impl Arena {
    pub closed spec fn view(&self) -> Seq<Inst> {
        self.model@
    }

    pub closed spec fn wf(&self) -> bool {
        &&& self.ptrs@.len() == self.model@.len()
        &&& forall|i: int| 0 <= i < self.model@.len() ==> #[trigger] self.perms@.dom().contains(i)
        &&& forall|i: int| 0 <= i < self.model@.len() ==> (#[trigger] self.perms@[i]).pptr() == self.ptrs@[i]
            && self.perms@[i].is_init() && self.perms@[i].value() == self.model@[i]
    }

    pub open spec fn len_spec(&self) -> nat {
        self.view().len()
    }

    pub fn new() -> (a: Arena)
        ensures
            a.wf(),
            a@ == Seq::<Inst>::empty(),
    {
        Arena { ptrs: Vec::new(), perms: Tracked(Map::tracked_empty()), model: Ghost(Seq::empty()) }
    }

    pub fn len(&self) -> (n: usize)
        requires
            self.wf(),
        ensures
            n == self@.len(),
    {
        self.ptrs.len()
    }

    /// Allocate a cell for `inst` at the end.
    pub fn push(&mut self, inst: Inst)
        requires
            old(self).wf(),
        ensures
            final(self).wf(),
            final(self)@ == old(self)@.push(inst),
    {
        let ghost n = self.model@.len() as int;
        let ghost v = inst;
        let (p, Tracked(perm)) = PPtr::new(inst);
        self.ptrs.push(p);
        proof {
            self.perms.borrow_mut().tracked_insert(n, perm);
            self.model@ = self.model@.push(v);
        }
    }

    /// Read cell `i` through its permission.
    pub fn get(&self, i: usize) -> (out: &Inst)
        requires
            self.wf(),
            i < self@.len(),
        ensures
            *out == self@[i as int],
    {
        let tracked perm = self.perms.borrow().tracked_borrow(i as int);
        self.ptrs[i].borrow(Tracked(perm))
    }

    /// Overwrite cell `i` in place.
    pub fn set(&mut self, i: usize, inst: Inst)
        requires
            old(self).wf(),
            i < old(self)@.len(),
        ensures
            final(self).wf(),
            final(self)@ == old(self)@.update(i as int, inst),
    {
        let ghost v = inst;
        let p = self.ptrs[i];
        let tracked mut perm = self.perms.borrow_mut().tracked_remove(i as int);
        let _old = p.take(Tracked(&mut perm));
        p.put(Tracked(&mut perm), inst);
        proof {
            self.perms.borrow_mut().tracked_insert(i as int, perm);
            self.model@ = self.model@.update(i as int, v);
        }
    }

    /// Copy the cells out (the VM's program).
    pub fn to_vec(&self) -> (v: Vec<Inst>)
        requires
            self.wf(),
        ensures
            v@ == self@,
    {
        let mut v: Vec<Inst> = Vec::new();
        let n = self.len();
        let mut i: usize = 0;
        while i < n
            invariant
                self.wf(),
                n == self@.len(),
                i <= n,
                v@ == self@.subrange(0, i as int),
            decreases n - i,
        {
            let x = copy_inst(self.get(i));
            v.push(x);
            i = i + 1;
            assert(v@ =~= self@.subrange(0, i as int));
        }
        assert(self@.subrange(0, n as int) =~= self@);
        v
    }

    /// Free every cell, consuming its permission.
    pub fn free_all(self)
        requires
            self.wf(),
    {
        let Arena { ptrs, perms: Tracked(mut perms), model } = self;
        let n = ptrs.len();
        let mut i: usize = 0;
        while i < n
            invariant
                n == ptrs@.len(),
                n == model@.len(),
                i <= n,
                forall|j: int| i <= j < n ==> #[trigger] perms.dom().contains(j),
                forall|j: int| i <= j < n ==> (#[trigger] perms[j]).pptr() == ptrs@[j] && perms[j].is_init(),
            decreases n - i,
        {
            let tracked mut perm = perms.tracked_remove(i as int);
            let p = ptrs[i];
            let _v = p.take(Tracked(&mut perm));
            p.free(Tracked(perm));
            i = i + 1;
        }
    }
}

/// Load a program into a fresh arena.
pub fn from_prog(p: &Vec<Inst>) -> (a: Arena)
    ensures
        a.wf(),
        a@ == p@,
{
    let mut a = Arena::new();
    let mut i: usize = 0;
    while i < p.len()
        invariant
            a.wf(),
            i <= p.len(),
            a@ == p@.subrange(0, i as int),
        decreases p.len() - i,
    {
        a.push(copy_inst(&p[i]));
        i = i + 1;
        assert(a@ =~= p@.subrange(0, i as int));
    }
    assert(p@.subrange(0, p@.len() as int) =~= p@);
    a
}

/// Retarget a `Jmp` cell whose target is another `Jmp` (one jump-threading rewrite, in place).
/// Only the model update is proved here; the language argument is R16's.
pub fn thread_one(a: &mut Arena, i: usize)
    requires
        old(a).wf(),
        i < old(a)@.len(),
    ensures
        final(a).wf(),
        final(a)@.len() == old(a)@.len(),
        forall|k: int| 0 <= k < final(a)@.len() && k != i ==> final(a)@[k] == old(a)@[k],
{
    let n = a.len();
    let mut target: Option<usize> = None;
    if let Inst::Jmp(x) = a.get(i) {
        let x = *x;
        if x < n {
            if let Inst::Jmp(y) = a.get(x) {
                target = Some(*y);
            }
        }
    }
    if let Some(y) = target {
        a.set(i, Inst::Jmp(y));
    }
}

/// Emit, load into the arena, run the verified Pike VM on the arena's program, free.
pub fn arena_match(r: &Re, s: &Vec<char>) -> (res: Option<bool>)
    ensures
        res is Some ==> res->Some_0 == matches(*r, s@),
{
    match emit_prog(r) {
        Some(p) => {
            let a = from_prog(&p);
            let q = a.to_vec();
            let b = pike_run(&q, s);
            a.free_all();
            proof {
                lemma_vm_correct(*r, s@);
            }
            Some(b)
        },
        None => None,
    }
}

} // verus!
