//! The step-matcher interface (PROVIDED, frozen; PLAN F6).
//!
//! An engine supplies its pattern, its executable state and the state's spec model, its
//! language `lang` (the engine's frozen semantic binding), what a model still accepts
//! (`res`), three executable functions tied to their specs, and three laws. `match_word`'s loop
//! is verified once, here, from the laws alone: no engine re-proves it.
//!
//! No engine lives here. R08 builds the engines; R11's certifying matcher and R16's machine
//! can implement the same trait.
#![allow(unused_imports)]
use vstd::prelude::*;

verus! {

pub trait StepMatcher {
    type Pattern;
    /// The executable state.
    type Config;
    /// The state's spec model: what the laws talk about.
    type Model;

    /// The engine's language: the meaning every client of `match_word` relies on.
    spec fn lang(p: Self::Pattern, w: Seq<char>) -> bool;

    spec fn model(st: Self::Config) -> Self::Model;

    /// The words a model still accepts.
    spec fn res(m: Self::Model, w: Seq<char>) -> bool;

    spec fn start_spec(p: Self::Pattern) -> Self::Model;

    spec fn feed_spec(m: Self::Model, c: char) -> Self::Model;

    spec fn final_spec(m: Self::Model) -> bool;

    fn start(p: Self::Pattern) -> (st: Self::Config)
        ensures
            Self::model(st) == Self::start_spec(p),
    ;

    fn feed(st: Self::Config, c: char) -> (r: Self::Config)
        ensures
            Self::model(r) == Self::feed_spec(Self::model(st), c),
    ;

    fn is_final(st: &Self::Config) -> (b: bool)
        ensures
            b == Self::final_spec(Self::model(*st)),
    ;

    /// The start model accepts the pattern's language ...
    proof fn lemma_start_law(p: Self::Pattern, w: Seq<char>)
        ensures
            Self::res(Self::start_spec(p), w) == Self::lang(p, w),
    ;

    /// ... one step consumes exactly one character ...
    proof fn lemma_feed_law(m: Self::Model, c: char, w: Seq<char>)
        ensures
            Self::res(Self::feed_spec(m, c), w) == Self::res(m, seq![c] + w),
    ;

    /// ... and a final model is one that accepts the empty word.
    proof fn lemma_final_law(m: Self::Model)
        ensures
            Self::final_spec(m) == Self::res(m, Seq::<char>::empty()),
    ;
}

/// The run loop, generic over the engine: its invariant is assembled from the three laws.
pub fn match_word<M: StepMatcher>(p: M::Pattern, w: &Vec<char>) -> (b: bool)
    ensures
        b == M::lang(p, w@),
{
    let ghost pat = p;
    proof {
        M::lemma_start_law(pat, w@);
        assert(w@.subrange(0, w@.len() as int) =~= w@);
    }
    let mut st = M::start(p);
    let mut i: usize = 0;
    while i < w.len()
        invariant
            i <= w.len(),
            M::res(M::model(st), w@.subrange(i as int, w@.len() as int)) == M::lang(pat, w@),
        decreases w.len() - i,
    {
        proof {
            let rest = w@.subrange(i + 1, w@.len() as int);
            M::lemma_feed_law(M::model(st), w@[i as int], rest);
            assert(seq![w@[i as int]] + rest =~= w@.subrange(i as int, w@.len() as int));
        }
        st = M::feed(st, w[i]);
        i = i + 1;
    }
    proof {
        M::lemma_final_law(M::model(st));
        assert(w@.subrange(i as int, w@.len() as int) =~= Seq::<char>::empty());
    }
    M::is_final(&st)
}

} // verus!
