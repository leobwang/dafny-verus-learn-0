/* CONTRACT — R08 semantic debugger, R-v0
goal: repair the pruning engine so that it honours the trait's laws for its original language matches
allowed-files:
  - verus/r/r08_abstraction/src/agent.rs
acceptance:
  - before the first edit, retain the original snapshot and the native verify-stage diagnostic of scripts/vcheck verus/r/r08_abstraction/src/agent.rs
  - preserve the provided trait, the types, lang, model, res and every requires and ensures; edit only the bodies of the engine's executable functions and proof fns
  - after every edit run scripts/vcheck verus/r/r08_abstraction/src/agent.rs and retain the actual stage, holes and diagnostics
  - scripts/vcheck --gate verus/r/r08_abstraction/src/agent.rs exits 0 with zero counted holes over the full file
  - scripts/vaudit verus/r/r08_abstraction/src/agent.rs has no findings, and scripts/specfreeze --check R08 reports no finding: every statement as shipped
  - name a concrete pattern and word on which the original engine's step law fails, and explain why a verified engine with a changed lang would not repair this contract; retain costs and the failed attempt
*/
//! # R08 semantic debugger (Reference Solution)
//!
//! A third engine for A2's step-matcher trait: Config = Re, and each step prunes the
//! derivative's alternatives, dropping the impossible ones and duplicates. The model of a
//! state is the language it accepts, so the laws are definitions; what must be proved is
//! that the executable start and feed keep that language, which rests on prune_exec's
//! promise. The file reaches the verifier with zero holes and fails at a real
//! postcondition. Decide whether the proof or the engine is wrong before you edit anything.
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a2::*;
use rg_re_a2::step_matcher::StepMatcher;

verus! {

/// The language of a regex, as a set of words.
pub open spec fn words_of(r: Re) -> ISet<Seq<char>> {
    ISet::new(|w: Seq<char>| matches(r, w))
}

pub struct PruneEngine;

impl StepMatcher for PruneEngine {
    type Pattern = Re;
    type Config = Re;
    type Model = ISet<Seq<char>>;

    open spec fn lang(p: Re, w: Seq<char>) -> bool {
        matches(p, w)
    }

    open spec fn model(st: Re) -> ISet<Seq<char>> {
        words_of(st)
    }

    open spec fn res(m: ISet<Seq<char>>, w: Seq<char>) -> bool {
        m.contains(w)
    }

    open spec fn start_spec(p: Re) -> ISet<Seq<char>> {
        words_of(p)
    }

    open spec fn feed_spec(m: ISet<Seq<char>>, c: char) -> ISet<Seq<char>> {
        ISet::new(|w: Seq<char>| m.contains(seq![c] + w))
    }

    open spec fn final_spec(m: ISet<Seq<char>>) -> bool {
        m.contains(Seq::<char>::empty())
    }

    fn start(p: Re) -> (st: Re) {
        let st = prune_exec(&p);
        proof {
            assert(words_of(st) =~= words_of(p));
        }
        st
    }

    fn feed(st: Re, c: char) -> (r: Re) {
        let d = deriv_exec(&st, c);
        let r = prune_exec(&d);
        proof {
            assert forall|w: Seq<char>| words_of(r).contains(w) == words_of(st).contains(seq![c] + w) by {
                lemma_deriv_correct(st, c, w);
            }
            assert(words_of(r) =~= ISet::new(|w: Seq<char>| words_of(st).contains(seq![c] + w)));
        }
        r
    }

    fn is_final(st: &Re) -> (b: bool) {
        proof {
            lemma_nullable_correct(*st);
        }
        is_nullable(st)
    }

    proof fn lemma_start_law(p: Re, w: Seq<char>) {
    }

    proof fn lemma_feed_law(m: ISet<Seq<char>>, c: char, w: Seq<char>) {
    }

    proof fn lemma_final_law(m: ISet<Seq<char>>) {
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

// item: R08.A1v
/// The engine: simplify the alternatives of a regex, keeping its language.
fn prune_exec(r: &Re) -> (out: Re)
    ensures
        forall|w: Seq<char>| matches(out, w) == matches(*r, w),
    decreases r,
{
    match r {
        Re::Alt(a, b) => {
            let x = prune_exec(a);
            let y = prune_exec(b);
            proof {
                assert forall|w: Seq<char>| matches(*r, w) == (matches(x, w) || matches(y, w)) by {
                }
            }
            if same_re(&x, &Re::Empty) {
                y
            } else if same_re(&y, &Re::Empty) {
                x
            } else if same_re(&x, &y) {
                x
            } else {
                let out = Re::Alt(Box::new(x), Box::new(y));
                proof {
                    assert forall|w: Seq<char>| matches(out, w) == (matches(x, w) || matches(y, w)) by {
                    }
                }
                out
            }
        },
        _ => copy_re(r),
    }
}

} // verus!
