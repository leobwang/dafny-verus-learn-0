/* CONTRACT — R08 semantic debugger, R-v0
goal: repair the pruning engine so that it honours the trait's laws for its original language matches
allowed-files:
  - verus/r/r08_abstraction/src/agent.rs
acceptance:
  - before the first edit, retain the original snapshot and the native verify-stage diagnostic of scripts/vcheck verus/r/r08_abstraction/src/agent.rs
  - preserve the provided trait, the types, lang, model, res and every requires and ensures; edit only the bodies of the engine's functions and proof fns
  - after every edit run scripts/vcheck verus/r/r08_abstraction/src/agent.rs and retain the actual stage, holes and diagnostics
  - scripts/vcheck --gate verus/r/r08_abstraction/src/agent.rs exits 0 with zero counted holes over the full file
  - scripts/vaudit verus/r/r08_abstraction/src/agent.rs has no findings and scripts/specfreeze --against <snapshot> verus/r/r08_abstraction/src/agent.rs preserves every original statement
  - name a concrete pattern and word on which the original engine's step law fails, and explain why a verified engine with a changed lang would not repair this contract; retain costs and the failed attempt
*/
//! # R08 semantic debugger (Reference Solution)
//!
//! A third engine for A2's step-matcher trait: Config = Model = Re, and each step prunes
//! the derivative's alternatives, dropping the impossible ones and duplicates. It reaches
//! the verifier with zero holes and fails at a real postcondition. The fault is semantic:
//! decide whether the proof or the engine is wrong before you edit anything.
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a2::*;
use rg_re_a2::step_matcher::StepMatcher;

verus! {

/// The engine: simplify the alternatives of a regex.
pub open spec fn prune(r: Re) -> Re
    decreases r,
{
    match r {
        Re::Alt(a, b) => {
            let x = prune(*a);
            let y = prune(*b);
            if x == Re::Empty {
                y
            } else if y == Re::Empty {
                x
            } else if x == y {
                x
            } else {
                Re::Alt(Box::new(x), Box::new(y))
            }
        },
        _ => r,
    }
}

/// Given: syntactic equality of two regexes, executable.
fn same_re(a: &Re, b: &Re) -> (eq: bool)
    ensures
        eq == (*a == *b),
    decreases a,
{
    match (a, b) {
        (Re::Empty, Re::Empty) => true,
        (Re::Eps, Re::Eps) => true,
        (Re::Chr(c), Re::Chr(d)) => *c == *d,
        (Re::Alt(a1, b1), Re::Alt(a2, b2)) => same_re(a1, a2) && same_re(b1, b2),
        (Re::Cat(a1, b1), Re::Cat(a2, b2)) => same_re(a1, a2) && same_re(b1, b2),
        (Re::Star(a1), Re::Star(a2)) => same_re(a1, a2),
        _ => false,
    }
}

/// `prune`, executable.
fn prune_exec(r: &Re) -> (out: Re)
    ensures
        out == prune(*r),
    decreases r,
{
    match r {
        Re::Alt(a, b) => {
            let x = prune_exec(a);
            let y = prune_exec(b);
            if same_re(&x, &Re::Empty) {
                y
            } else if same_re(&y, &Re::Empty) {
                x
            } else if same_re(&x, &y) {
                x
            } else {
                Re::Alt(Box::new(x), Box::new(y))
            }
        },
        _ => copy_re(r),
    }
}

pub struct PruneEngine;

impl StepMatcher for PruneEngine {
    type Pattern = Re;
    type Config = Re;
    type Model = Re;

    open spec fn lang(p: Re, w: Seq<char>) -> bool {
        matches(p, w)
    }

    open spec fn model(st: Re) -> Re {
        st
    }

    open spec fn res(m: Re, w: Seq<char>) -> bool {
        matches(m, w)
    }

    open spec fn start_spec(p: Re) -> Re {
        prune(p)
    }

    open spec fn feed_spec(m: Re, c: char) -> Re {
        prune(deriv(m, c))
    }

    open spec fn final_spec(m: Re) -> bool {
        nullable(m)
    }

    fn start(p: Re) -> (st: Re) {
        prune_exec(&p)
    }

    fn feed(st: Re, c: char) -> (r: Re) {
        prune_exec(&deriv_exec(&st, c))
    }

    fn is_final(st: &Re) -> (b: bool) {
        is_nullable(st)
    }

    proof fn lemma_start_law(p: Re, w: Seq<char>) {
        lemma_prune_law(p, w);
    }

    proof fn lemma_feed_law(m: Re, c: char, w: Seq<char>) {
        lemma_prune_law(deriv(m, c), w);
        lemma_deriv_correct(m, c, w);
    }

    proof fn lemma_final_law(m: Re) {
        lemma_nullable_correct(m);
    }
}

// item: R08.A1v
/// Pruning keeps the language.
pub proof fn lemma_prune_law(r: Re, w: Seq<char>)
    ensures
        matches(prune(r), w) == matches(r, w),
    decreases r,
{
    match r {
        Re::Alt(a, b) => {
            lemma_prune_law(*a, w);
            lemma_prune_law(*b, w);
        },
        _ => {},
    }
}

} // verus!
