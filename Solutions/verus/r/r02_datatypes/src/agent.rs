/* CONTRACT
goal: implement Alphabet, StarHeight and MinLen (Rust: alphabet, star_height, min_len) according to their prose contracts, satisfying all six shipped checks
allowed-files:
  - verus/r/r02_datatypes/src/agent.rs
acceptance:
  - between edits use only the fast channel: scripts/vcheck --symbol <qualified-symbol> verus/r/r02_datatypes/src/agent.rs
  - exactly one full scripts/vcheck --gate verus/r/r02_datatypes/src/agent.rs run, last; exit 0, summary line only
  - zero tool-counted holes; scripts/vaudit verus/r/r02_datatypes/src/agent.rs reports zero findings
  - git diff changes only the three definition bodies and, in Verus, the three bound-lemma bodies; remove uninterp only to supply its definition
  - preserve signatures, partial contracts, decreases, prose, checks and headings; no assumptions or verification escape hatch
*/
//! R02 — Reference Solution. Implementer vs checks: spec-first. Preserve the weak formal
//! contracts, all six checks and the stronger prose; fill the manual follow-up.
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
verus! {
// item: R02.A1v

/// The finite set of characters occurring in Chr leaves; Empty/Eps have
/// none, Alt/Cat combine their children, and Star retains its body's letters.
pub open spec fn alphabet(r: Re) -> Set<char>
    decreases r,
{
    match r {
        Re::Empty => Set::empty(),
        Re::Eps => Set::empty(),
        Re::Chr(c) => Set::empty().insert(c),
        Re::Alt(a, b) => alphabet(*a).union(alphabet(*b)),
        Re::Cat(a, b) => alphabet(*a).union(alphabet(*b)),
        Re::Star(a) => alphabet(*a),
    }
}
pub proof fn lemma_alphabet_bound(r: Re)
    ensures r is Empty ==> alphabet(r) == Set::<char>::empty(),
    decreases r,
{

}

/// Largest number of nested Star constructors on any root-to-leaf path;
/// leaves have height zero. The bound alone is not this prose specification.
pub open spec fn star_height(r: Re) -> nat
    decreases r,
{
    match r {
        Re::Alt(a, b) => if star_height(*a) < star_height(*b) { star_height(*b) } else { star_height(*a) },
        Re::Cat(a, b) => if star_height(*a) < star_height(*b) { star_height(*b) } else { star_height(*a) },
        Re::Star(a) => 1 + star_height(*a),
        _ => 0,
    }
}
pub proof fn lemma_star_height_bound(r: Re)
    ensures star_height(r) <= node_count(r),
    decreases r,
{
    match r {
        Re::Alt(a, b) => { lemma_star_height_bound(*a); lemma_star_height_bound(*b); },
        Re::Cat(a, b) => { lemma_star_height_bound(*a); lemma_star_height_bound(*b); },
        Re::Star(a) => { lemma_star_height_bound(*a); },
        _ => {},
    }
}

/// Length of the shortest matched string; convention: zero for a regex
/// matching no string. This includes a Cat with an impossible factor. The
/// Eps-only bound lemma deliberately states less than this prose contract.
pub open spec fn min_len(r: Re) -> nat
    decreases r,
{
    match r {
        Re::Empty => 0,
        Re::Eps => 0,
        Re::Chr(_) => 1,
        Re::Star(_) => 0,
        Re::Alt(a, b) => {
            let x = min_len(*a); let y = min_len(*b);
            if x == 0 && !nullable(*a) { y }
            else if y == 0 && !nullable(*b) { x }
            else if x < y { x } else { y }
        },
        Re::Cat(a, b) => {
            let x = min_len(*a); let y = min_len(*b);
            if (x == 0 && !nullable(*a)) || (y == 0 && !nullable(*b)) { 0 } else { x + y }
        },
    }
}
pub proof fn lemma_min_len_bound(r: Re)
    ensures r is Eps ==> min_len(r) == 0,
    decreases r,
{

}

// Six shipped checks; preserve every intermediate assertion as well as the final goal.
proof fn alphabet_leaf_check() {
    assert(alphabet(Re::Chr('q')) == set!['q']);
}
proof fn alphabet_pair_check() {
    let a = Re::Chr('q'); let b = Re::Chr('r');
    assert(alphabet(a) == set!['q']); assert(alphabet(b) == set!['r']);
    assert(alphabet(Re::Cat(Box::new(a), Box::new(b))) == set!['q', 'r']);
}
proof fn star_height_leaf_check() {
    let a = Re::Chr('q'); assert(star_height(a) == 0);
    assert(star_height(Re::Star(Box::new(a))) == 1);
}
proof fn star_height_pair_check() {
    let a = Re::Chr('q'); let b = Re::Chr('r'); let s = Re::Star(Box::new(a));
    assert(star_height(a) == 0); assert(star_height(b) == 0); assert(star_height(s) == 1);
    assert(star_height(Re::Cat(Box::new(s), Box::new(b))) == 1);
}
proof fn min_len_leaf_check() { assert(min_len(Re::Chr('q')) == 1); }
proof fn min_len_pair_check() {
    let a = Re::Chr('q'); let b = Re::Chr('r');
    assert(min_len(a) == 1); assert(min_len(b) == 1);
    assert(min_len(Re::Cat(Box::new(a), Box::new(b))) == 2);
}

  /* LATENCY LOG — learner-owned, after /contract R02:
     symbol | wall time | fast or full | exit | transcript location
     ...
     Did the contractor spend its single full gate last? Compare the evidence,
     including failed edits; do not substitute a claimed latency for a run.

     ADVERSARIAL CHECKS — learner-owned, outside the contractor's scope:
     Add checks that follow from each prose contract but are not implied by
     the shipped suite. Explain which plausible wrong implementation they kill.
     Keep all six original checks and every formal contract.

     FIRST PROPERTY TESTS — after completing the hand exercises:
     Add @Test / #[test] code beside the hand exercise implementations in
     core/R02_Datatypes.dfy / src/lib.rs, where IsVoid / is_void is available.
     Use these samples: Empty, Eps, Chr('q'), Alt(Empty, Chr('r')),
     Cat(Empty, Chr('s')), Star(Empty), Cat(Eps, Chr('q')).
     Loop over them and test that nullable implies not void, compare Alt's
     voidness with its two children's results, and add one property of your own.
     Dafny uses a sequence of Re; Rust uses a Vec<Re> and references/Box.
     Run scripts/vcheck --test on the exercise unit/crate and record the result.
     These manual follow-up edits happen after the contractor has finished;
     they do not enlarge its allowed-files list. A passing finite sample is
     evidence about those runs, not a universal proof. Do not insert assume.
  */
} // verus!
