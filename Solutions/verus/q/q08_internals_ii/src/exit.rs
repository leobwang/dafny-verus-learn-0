//! # Q08 — exit, Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q08_internals_ii/src/exit.rs` (author-only; never
//! learner-visible). Same imports, names, statements, item markers, `need:` lines and order
//! as the exit file, with both exit items answered; each exec item declares its `// triv:`
//! body for the empty-body gate's TRIV mode. Silent under `scripts/vcheck --ref`.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

// Given (not items): the sum of a sequence of words, for X1 and X2.
pub open spec fn words_sum(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        words_sum(s.drop_last()) + s.last() as nat
    }
}

// Given (not items): a ledger whose total is the sum of its ghost log, for X2.
pub struct Ledger {
    pub total: u64,
    pub log: Ghost<Seq<u64>>,
}

impl Ledger {
    pub open spec fn inv(&self) -> bool {
        self.total == words_sum(self.log@)
    }
}

// item: Q08.X1v S6
// uses: trait-spec
// need: pub fn sum_words<T: NatLike>(xs: &Vec<u64>) -> (r: T)
// need: r.value() == words_sum(xs@),
/// **X1.** Sum the words of `xs` through the trait only.
///
/// Reference: a loop over the indices that adds `T::from_word(xs[i])` to an accumulator
/// started at `T::zero()`; the invariant keeps it valid and worth `words_sum` of the prefix
/// `xs@.subrange(0, i)`. `words_sum` peels the last word (`drop_last`), so each step needs
/// the extensionality fact that the longer prefix without its last word is the shorter
/// prefix; after the loop, the full prefix is `xs@`.
pub fn sum_words<T: NatLike>(xs: &Vec<u64>) -> (r: T)
    ensures
        r.valid(),
        r.value() == words_sum(xs@),
{
    let mut acc = T::zero();
    let mut i: usize = 0;
    while i < xs.len()
        invariant
            0 <= i <= xs.len(),
            acc.valid(),
            acc.value() == words_sum(xs@.subrange(0, i as int)),
        decreases xs.len() - i,
    {
        let w = T::from_word(xs[i]);
        acc = acc.plus(&w);
        assert(xs@.subrange(0, i + 1).drop_last() =~= xs@.subrange(0, i as int));
        i = i + 1;
    }
    assert(xs@.subrange(0, xs.len() as int) =~= xs@);
    acc
}
// triv: { T::zero() }

// item: Q08.X2v S7
// need: pub fn record(&mut self, x: u64)
// need: final(self).log@ == old(self).log@.push(x),
/// **X2.** Record the amount `x` in the ledger.
///
/// Reference: the ghost log is updated by a ghost assignment (`Ghost(old_log.push(x))`, with
/// the old log kept in a `let ghost`), and the total by ordinary code; the invariant after
/// the update needs `words_sum` to peel the appended word, which the extensionality fact
/// `old_log.push(x).drop_last() =~= old_log` supplies.
impl Ledger {
    pub fn record(&mut self, x: u64)
        requires
            old(self).inv(),
            old(self).total + x <= u64::MAX,
        ensures
            final(self).inv(),
            final(self).log@ == old(self).log@.push(x),
    {
        let ghost old_log = self.log@;
        self.log = Ghost(old_log.push(x));
        self.total = self.total + x;
        assert(old_log.push(x).drop_last() =~= old_log);
    }
    // triv: { }
}

} // verus!
