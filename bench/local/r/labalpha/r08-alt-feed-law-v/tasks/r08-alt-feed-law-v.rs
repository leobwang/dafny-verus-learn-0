// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["lemma_alt_feed_law","lemma_parts_law","lemma_deriv_correct"]},{"name":"h1"},{"name":"h2"},{"name":"h3"},{"name":"h4"},{"name":"h5"},{"name":"h6"}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_alt_feed_law","start":254,"end":291}]
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

// Provided fact (rg_re_a1b::lemma_nullable_correct), complete, copied verbatim.
pub proof fn lemma_nullable_correct(r: Re)
    ensures
        nullable(r) <==> matches(r, Seq::<char>::empty()),
    decreases r,
{
    let e = Seq::<char>::empty();
    assert(e.subrange(0, 0) =~= e);
    match r {
        Re::Alt(a, b) => {
            lemma_nullable_correct(*a);
            lemma_nullable_correct(*b);
        },
        Re::Cat(a, b) => {
            lemma_nullable_correct(*a);
            lemma_nullable_correct(*b);
        },
        _ => {},
    }
}

// Provided definition (rg_re_a2::deriv), copied verbatim.
pub open spec fn deriv(r: Re, c: char) -> Re
    decreases r,
{
    match r {
        Re::Empty => Re::Empty,
        Re::Eps => Re::Empty,
        Re::Chr(d) => if c == d { Re::Eps } else { Re::Empty },
        Re::Alt(a, b) => Re::Alt(Box::new(deriv(*a, c)), Box::new(deriv(*b, c))),
        Re::Cat(a, b) => if nullable(*a) {
            Re::Alt(Box::new(Re::Cat(Box::new(deriv(*a, c)), b)), Box::new(deriv(*b, c)))
        } else {
            Re::Cat(Box::new(deriv(*a, c)), b)
        },
        Re::Star(a) => Re::Cat(Box::new(deriv(*a, c)), Box::new(Re::Star(a))),
    }
}

// Provided fact (rg_re_a2::lemma_deriv_correct), complete, copied verbatim.
pub proof fn lemma_deriv_correct(r: Re, c: char, s: Seq<char>)
    ensures
        matches(deriv(r, c), s) <==> matches(r, seq![c] + s),
    decreases r,
{
    let w = seq![c] + s;
    assert(w.len() == s.len() + 1);
    match r {
        Re::Chr(d) => {
            assert(w[0] == c);
        },
        Re::Alt(a, b) => {
            lemma_deriv_correct(*a, c, s);
            lemma_deriv_correct(*b, c, s);
        },
        Re::Cat(a, b) => {
            let da = deriv(*a, c);
            let cat = Re::Cat(Box::new(da), b);
            lemma_nullable_correct(*a);
            assert(w.subrange(0, 0) =~= Seq::<char>::empty());
            assert(w.subrange(0, w.len() as int) =~= w);
            // `r` matches `c s` ==> the derivative matches `s`
            if matches(r, w) {
                let i = choose|i: int|
                    0 <= i <= w.len() && matches(*a, #[trigger] w.subrange(0, i)) && matches(
                        *b,
                        w.subrange(i, w.len() as int),
                    );
                if i == 0 {
                    lemma_deriv_correct(*b, c, s);
                } else {
                    lemma_deriv_correct(*a, c, s.subrange(0, i - 1));
                    assert(w.subrange(0, i) =~= seq![c] + s.subrange(0, i - 1));
                    assert(w.subrange(i, w.len() as int) =~= s.subrange(i - 1, s.len() as int));
                    assert(matches(da, s.subrange(0, i - 1)));
                    assert(matches(cat, s));
                }
            }
            // the derivative matches `s` ==> `r` matches `c s`
            if matches(cat, s) {
                let j = choose|j: int|
                    0 <= j <= s.len() && matches(da, #[trigger] s.subrange(0, j)) && matches(
                        *b,
                        s.subrange(j, s.len() as int),
                    );
                lemma_deriv_correct(*a, c, s.subrange(0, j));
                assert(w.subrange(0, j + 1) =~= seq![c] + s.subrange(0, j));
                assert(w.subrange(j + 1, w.len() as int) =~= s.subrange(j, s.len() as int));
                assert(matches(*a, w.subrange(0, j + 1)));
            }
            if nullable(*a) && matches(deriv(*b, c), s) {
                lemma_deriv_correct(*b, c, s);
                assert(matches(*a, w.subrange(0, 0)));
            }
        },
        Re::Star(a) => {
            let da = deriv(*a, c);
            // `r` matches `c s` ==> the derivative matches `s`
            if matches(r, w) {
                let i = choose|i: int|
                    1 <= i <= w.len() && matches(*a, #[trigger] w.subrange(0, i)) && matches(
                        r,
                        w.subrange(i, w.len() as int),
                    );
                lemma_deriv_correct(*a, c, s.subrange(0, i - 1));
                assert(w.subrange(0, i) =~= seq![c] + s.subrange(0, i - 1));
                assert(w.subrange(i, w.len() as int) =~= s.subrange(i - 1, s.len() as int));
                assert(matches(da, s.subrange(0, i - 1)));
            }
            // the derivative matches `s` ==> `r` matches `c s`
            if matches(deriv(r, c), s) {
                let j = choose|j: int|
                    0 <= j <= s.len() && matches(da, #[trigger] s.subrange(0, j)) && matches(
                        r,
                        s.subrange(j, s.len() as int),
                    );
                lemma_deriv_correct(*a, c, s.subrange(0, j));
                assert(w.subrange(0, j + 1) =~= seq![c] + s.subrange(0, j));
                assert(w.subrange(j + 1, w.len() as int) =~= s.subrange(j, s.len() as int));
                assert(matches(*a, w.subrange(0, j + 1)));
            }
        },
        _ => {},
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

/// Given: the derivative of every alternative, split again.
pub open spec fn feed_all(st: Seq<Re>, c: char) -> Seq<Re>
    decreases st.len(),
{
    if st.len() == 0 {
        Seq::empty()
    } else {
        parts(deriv(st[0], c)) + feed_all(st.drop_first(), c)
    }
}

/// The engine's model, opaque: revealed with `reveal(alt_res)`.
#[verifier::opaque]
pub open spec fn alt_res(m: Seq<Re>, w: Seq<char>) -> bool {
    any_matches(m, w)
}

// Provided fact (R08.H2v lemma_parts_law), complete.
pub proof fn lemma_parts_law(r: Re, w: Seq<char>)
    ensures
        any_matches(parts(r), w) == matches(r, w),
    decreases r,
{
    match r {
        Re::Empty => {},
        Re::Alt(a, b) => {
            lemma_parts_law(*a, w);
            lemma_parts_law(*b, w);
            let pa = parts(*a);
            let pb = parts(*b);
            if matches(*a, w) {
                let i = choose|i: int| 0 <= i < pa.len() && matches(#[trigger] pa[i], w);
                assert((pa + pb)[i] == pa[i]);
            }
            if matches(*b, w) {
                let i = choose|i: int| 0 <= i < pb.len() && matches(#[trigger] pb[i], w);
                assert((pa + pb)[pa.len() + i] == pb[i]);
            }
            if any_matches(pa + pb, w) {
                let i = choose|i: int|
                    0 <= i < (pa + pb).len() && matches(#[trigger] (pa + pb)[i], w);
                if i < pa.len() {
                    assert(matches(pa[i], w));
                } else {
                    assert(matches(pb[i - pa.len()], w));
                }
            }
        },
        _ => {
            assert(parts(r) =~= seq![r]);
            if matches(r, w) {
                assert(matches(parts(r)[0], w));
            }
        },
    }
}

// The task (R08.H3 lemma_alt_feed_law): the alternative-set engine's step law.
pub proof fn lemma_alt_feed_law(m: Seq<Re>, c: char, w: Seq<char>)
    ensures
        alt_res(feed_all(m, c), w) == alt_res(m, seq![c] + w),
    decreases m.len(),
{
    reveal(alt_res);
    if m.len() > 0 {
        let head = parts(deriv(m[0], c));
        let tail = feed_all(m.drop_first(), c);
        /*R12_CALLS:c1*/
        if any_matches(head + tail, w) {
            let i = choose|i: int|
                0 <= i < (head + tail).len() && matches(#[trigger] (head + tail)[i], w);
            if i < head.len() {
                assert(/*R12_HINT:h1*/ true);
            } else {
                assert(/*R12_HINT:h2*/ true);
                let j = choose|j: int|
                    0 <= j < m.drop_first().len() && matches(
                        #[trigger] m.drop_first()[j],
                        seq![c] + w,
                    );
                assert(/*R12_HINT:h3*/ true);
            }
        }
        if any_matches(m, seq![c] + w) {
            let i = choose|i: int| 0 <= i < m.len() && matches(#[trigger] m[i], seq![c] + w);
            if i == 0 {
                let k = choose|k: int| 0 <= k < head.len() && matches(#[trigger] head[k], w);
                assert(/*R12_HINT:h4*/ true);
            } else {
                assert(/*R12_HINT:h5*/ true);
                let k = choose|k: int| 0 <= k < tail.len() && matches(#[trigger] tail[k], w);
                assert(/*R12_HINT:h6*/ true);
            }
        }
    }
}
} // verus!
