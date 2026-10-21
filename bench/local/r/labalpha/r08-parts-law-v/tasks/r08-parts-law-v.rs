// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["lemma_parts_law"]},{"name":"h1"},{"name":"h2"},{"name":"h3"},{"name":"h4"},{"name":"h5"}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_parts_law","start":73,"end":109}]
use vstd::prelude::*;

verus! {

// Provided definitions: rg_re_a1 (layer A1), copied verbatim.
pub enum Re {
    Empty,
    Eps,
    Chr(char),
    Alt(Box<Re>, Box<Re>),
    Cat(Box<Re>, Box<Re>),
    Star(Box<Re>),
}

pub open spec fn matches(r: Re, s: Seq<char>) -> bool
    decreases r, s.len(),
{
    match r {
        Re::Empty => false,
        Re::Eps => s.len() == 0,
        Re::Chr(c) => s.len() == 1 && s[0] == c,
        Re::Alt(a, b) => matches(*a, s) || matches(*b, s),
        Re::Cat(a, b) => exists|i: int|
            0 <= i <= s.len() && matches(*a, #[trigger] s.subrange(0, i)) && matches(
                *b,
                s.subrange(i, s.len() as int),
            ),
        Re::Star(a) => s.len() == 0 || exists|i: int|
            1 <= i <= s.len() && matches(*a, #[trigger] s.subrange(0, i)) && matches(
                r,
                s.subrange(i, s.len() as int),
            ),
    }
}

pub open spec fn nullable(r: Re) -> bool
    decreases r,
{
    match r {
        Re::Empty => false,
        Re::Eps => true,
        Re::Chr(_) => false,
        Re::Alt(a, b) => nullable(*a) || nullable(*b),
        Re::Cat(a, b) => nullable(*a) && nullable(*b),
        Re::Star(_) => true,
    }
}


// Provided definitions (R08 alternative-set engine, given), copied verbatim.
/// Given: split the top-level `Alt` nodes, drop the literal `Empty` parts.
pub open spec fn parts(r: Re) -> Seq<Re>
    decreases r,
{
    match r {
        Re::Empty => Seq::empty(),
        Re::Alt(a, b) => parts(*a) + parts(*b),
        _ => seq![r],
    }
}

/// Given: some alternative of the list matches `w`.
pub open spec fn any_matches(st: Seq<Re>, w: Seq<char>) -> bool {
    exists|i: int| 0 <= i < st.len() && matches(#[trigger] st[i], w)
}

// The task (R08.H2 lemma_parts_law): splitting a pattern into its parts keeps its language.
pub proof fn lemma_parts_law(r: Re, w: Seq<char>)
    ensures
        any_matches(parts(r), w) == matches(r, w),
    decreases r,
{
    match r {
        Re::Empty => {},
        Re::Alt(a, b) => {
            /*R12_CALLS:c1*/
            let pa = parts(*a);
            let pb = parts(*b);
            if matches(*a, w) {
                let i = choose|i: int| 0 <= i < pa.len() && matches(#[trigger] pa[i], w);
                assert(/*R12_HINT:h1*/ true);
            }
            if matches(*b, w) {
                let i = choose|i: int| 0 <= i < pb.len() && matches(#[trigger] pb[i], w);
                assert(/*R12_HINT:h2*/ true);
            }
            if any_matches(pa + pb, w) {
                let i = choose|i: int|
                    0 <= i < (pa + pb).len() && matches(#[trigger] (pa + pb)[i], w);
                if i < pa.len() {
                    assert(/*R12_HINT:h3*/ true);
                } else {
                    assert(/*R12_HINT:h4*/ true);
                }
            }
        },
        _ => {
            assert(parts(r) =~= seq![r]);
            if matches(r, w) {
                assert(/*R12_HINT:h5*/ true);
            }
        },
    }
}
} // verus!
