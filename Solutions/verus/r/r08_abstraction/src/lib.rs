//! # R08 — Abstraction (Reference Solution)
//!
//! Imports: the given regex spine `rg_re_a1`, `rg_re_a1b` and `rg_re_a2`, with A2's
//! step-matcher interface (`rg_re_a2::step_matcher`: the trait `StepMatcher` and the
//! generic `match_word`); nothing else: no earlier exercise file. The layers are frozen and
//! complete; read them, never edit them.
//!
//! How to work this file:
//! 1. Predictions first: fill every slot of specimens/R08/P*.specimen and of the Dafny
//!    file's prediction block (slots/R08.slots), then record the first tries with
//!    `scripts/firsttry.sh R08 --check`, before you run anything they are about.
//! 2. Read the worked derivative engine (W1), then replace each hole, H1 to H4, in order.
//!    Every hole is a lemma that one of an engine's trait laws rests on.
//! 3. Done = `scripts/vcheck --gate verus/r/r08_abstraction` prints only the summary
//!    line and exits 0, `scripts/vaudit verus/r/r08_abstraction` reports no finding,
//!    AND `scripts/firsttry.sh R08 --report --strict` exits 0.
//! 4. Stuck for 20 minutes? /tutor R08.
//!
//! This file ships with exactly 4 holes: H1–H4, each counted by `scripts/vcheck`. The
//! crate's agent file (src/agent.rs, not a module of this crate's library) is the
//! contractor exercise.
//!
//! Item kinds: P prediction (a slot) · W worked example (complete; read it) · H hole
//! (replace the body) · C card.
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a2::*;
use rg_re_a2::char_class::CharClass;
use rg_re_a2::step_matcher::{StepMatcher, match_word};

verus! {

// =========================================================================================
// W1 (worked): the derivative engine
// =========================================================================================

// item: R08.W1v
/// The derivative engine: Pattern = Config = Model = Re. Each law is one call to a layer
/// lemma; `match_word` is the interface's, already verified.
pub struct DerivEngine;

impl StepMatcher for DerivEngine {
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
        p
    }

    open spec fn feed_spec(m: Re, c: char) -> Re {
        deriv(m, c)
    }

    open spec fn final_spec(m: Re) -> bool {
        nullable(m)
    }

    fn start(p: Re) -> (st: Re) {
        p
    }

    fn feed(st: Re, c: char) -> (r: Re) {
        deriv_exec(&st, c)
    }

    fn is_final(st: &Re) -> (b: bool) {
        is_nullable(st)
    }

    proof fn lemma_start_law(p: Re, w: Seq<char>) {
    }

    proof fn lemma_feed_law(m: Re, c: char, w: Seq<char>) {
        lemma_deriv_correct(m, c, w);
    }

    proof fn lemma_final_law(m: Re) {
        lemma_nullable_correct(m);
    }
}

/// A client of the interface: it knows only `match_word`'s contract and the engine's `lang`.
pub fn match_deriv(r: Re, w: &Vec<char>) -> (b: bool)
    ensures
        b == matches(r, w@),
{
    match_word::<DerivEngine>(r, w)
}

// =========================================================================================
// The range-star engine: a second implementation, over A2's class API
// =========================================================================================

/// Given: `c` lies in one of the ranges.
pub open spec fn in_char_ranges(rs: Seq<(char, char)>, c: char) -> bool {
    exists|j: int| 0 <= j < rs.len() && (#[trigger] rs[j]).0 <= c && c <= rs[j].1
}

/// Given: the set of the characters of all the ranges, one range at a time.
pub open spec fn ranges_set(rs: Seq<(char, char)>) -> ISet<char>
    decreases rs.len(),
{
    if rs.len() == 0 {
        ISet::empty()
    } else {
        ISet::new(|c: char| rs[0].0 <= c && c <= rs[0].1).union(ranges_set(rs.drop_first()))
    }
}

/// Given: the class of the ranges from index `k` on, built with A2's class API.
fn ranges_class(rs: &Vec<(char, char)>, k: usize) -> (cls: CharClass)
    requires
        k <= rs.len(),
    ensures
        cls.valid(),
        cls@ == ranges_set(rs@.subrange(k as int, rs@.len() as int)),
    decreases rs.len() - k,
{
    let ghost tail = rs@.subrange(k as int, rs@.len() as int);
    if k == rs.len() {
        let e = CharClass::class_empty();
        proof {
            assert(e@ =~= ranges_set(tail));
        }
        e
    } else {
        let (lo, hi) = rs[k];
        let first = CharClass::class_range(lo, hi);
        let rest = ranges_class(rs, k + 1);
        let u = first.class_union(&rest);
        proof {
            assert(tail.drop_first() =~= rs@.subrange(k + 1, rs@.len() as int));
            assert(tail[0] == (lo, hi));
            assert(first@ =~= ISet::new(|c: char| lo <= c && c <= hi));
            assert(u@ =~= ranges_set(tail));
        }
        u
    }
}

/// The executable state: is the run alive, and the one class built at the start.
pub struct StarState {
    pub alive: bool,
    pub cls: CharClass,
}

pub struct RangeStarEngine;

impl StepMatcher for RangeStarEngine {
    type Pattern = Vec<(char, char)>;
    type Config = StarState;
    type Model = (bool, ISet<char>);

    open spec fn lang(p: Vec<(char, char)>, w: Seq<char>) -> bool {
        forall|i: int| 0 <= i < w.len() ==> in_char_ranges(p@, #[trigger] w[i])
    }

    open spec fn model(st: StarState) -> (bool, ISet<char>) {
        (st.alive, st.cls@)
    }

    open spec fn res(m: (bool, ISet<char>), w: Seq<char>) -> bool {
        m.0 && forall|i: int| 0 <= i < w.len() ==> m.1.contains(#[trigger] w[i])
    }

    open spec fn start_spec(p: Vec<(char, char)>) -> (bool, ISet<char>) {
        (true, ranges_set(p@))
    }

    open spec fn feed_spec(m: (bool, ISet<char>), c: char) -> (bool, ISet<char>) {
        if m.0 && m.1.contains(c) {
            m
        } else {
            (false, m.1)
        }
    }

    open spec fn final_spec(m: (bool, ISet<char>)) -> bool {
        m.0
    }

    fn start(p: Vec<(char, char)>) -> (st: StarState) {
        proof {
            assert(p@.subrange(0, p@.len() as int) =~= p@);
        }
        StarState { alive: true, cls: ranges_class(&p, 0) }
    }

    fn feed(st: StarState, c: char) -> (r: StarState) {
        if st.alive && st.cls.class_member(c) {
            st
        } else {
            StarState { alive: false, cls: st.cls }
        }
    }

    fn is_final(st: &StarState) -> (b: bool) {
        st.alive
    }

    proof fn lemma_start_law(p: Vec<(char, char)>, w: Seq<char>) {
        assert forall|i: int| 0 <= i < w.len() implies ranges_set(p@).contains(#[trigger] w[i])
            == in_char_ranges(p@, w[i]) by {
            lemma_ranges_set_law(p@, w[i]);
        }
    }

    proof fn lemma_feed_law(m: (bool, ISet<char>), c: char, w: Seq<char>) {
        let cw = seq![c] + w;
        assert(cw[0] == c);
        assert forall|i: int| 0 <= i < w.len() implies cw[i + 1] == w[i] by {
        }
    }

    proof fn lemma_final_law(m: (bool, ISet<char>)) {
    }
}

// item: R08.H1v
// uses: trait-spec
// pair: R08.H1d
/// **H1.** The set the engine's start model holds is exactly the characters of the
/// pattern's ranges.
///
/// Reference: induction on `rs.len()`. `ranges_set(rs)` holds `c` exactly when `c` is in
/// the first range or in `ranges_set(rs.drop_first())`, and the recursive call turns the
/// latter into `in_char_ranges(rs.drop_first(), c)`. What is left moves one witness: a
/// range `j` of the tail is range `j + 1` of `rs`, and a range `j > 0` of `rs` is range
/// `j - 1` of the tail; `choose` names it, and the indexing assertion is the trigger term.
pub proof fn lemma_ranges_set_law(rs: Seq<(char, char)>, c: char)
    ensures
        ranges_set(rs).contains(c) == in_char_ranges(rs, c),
    decreases rs.len(),
{
    if rs.len() > 0 {
        let tail = rs.drop_first();
        lemma_ranges_set_law(tail, c);
        if in_char_ranges(tail, c) {
            let j = choose|j: int| 0 <= j < tail.len() && (#[trigger] tail[j]).0 <= c && c <= tail[j].1;
            assert(rs[j + 1] == tail[j]);
        }
        if in_char_ranges(rs, c) {
            let j = choose|j: int| 0 <= j < rs.len() && (#[trigger] rs[j]).0 <= c && c <= rs[j].1;
            if j > 0 {
                assert(tail[j - 1] == rs[j]);
            }
        }
    }
}

// =========================================================================================
// The alternative-set engine: a state is a list of alternatives
// =========================================================================================

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

/// Given: some alternative of the list is nullable.
pub open spec fn any_nullable(st: Seq<Re>) -> bool
    decreases st.len(),
{
    st.len() > 0 && (nullable(st[0]) || any_nullable(st.drop_first()))
}

/// Given: `parts`, executable.
pub fn parts_exec(r: &Re) -> (out: Vec<Re>)
    ensures
        out@ == parts(*r),
    decreases r,
{
    match r {
        Re::Empty => Vec::new(),
        Re::Alt(a, b) => {
            let mut out = parts_exec(a);
            let mut tail = parts_exec(b);
            out.append(&mut tail);
            out
        },
        _ => {
            let mut out = Vec::new();
            out.push(copy_re(r));
            proof {
                assert(out@ =~= seq![*r]);
            }
            out
        },
    }
}

/// Given: `feed_all` of the list from index `i` on, executable.
fn feed_from(st: &Vec<Re>, i: usize, c: char) -> (out: Vec<Re>)
    requires
        i <= st.len(),
    ensures
        out@ == feed_all(st@.subrange(i as int, st@.len() as int), c),
    decreases st.len() - i,
{
    if i == st.len() {
        proof {
            assert(st@.subrange(i as int, st@.len() as int).len() == 0);
        }
        Vec::new()
    } else {
        let mut out = parts_exec(&deriv_exec(&st[i], c));
        let mut tail = feed_from(st, i + 1, c);
        proof {
            let s = st@.subrange(i as int, st@.len() as int);
            assert(s.drop_first() =~= st@.subrange(i + 1, st@.len() as int));
        }
        out.append(&mut tail);
        out
    }
}

/// The engine's model, opaque: its existential stays out of every proof that does not
/// reveal it with `reveal(alt_res)`.
#[verifier::opaque]
pub open spec fn alt_res(m: Seq<Re>, w: Seq<char>) -> bool {
    any_matches(m, w)
}

pub struct AltSetEngine;

impl StepMatcher for AltSetEngine {
    type Pattern = Re;
    type Config = Vec<Re>;
    type Model = Seq<Re>;

    open spec fn lang(p: Re, w: Seq<char>) -> bool {
        matches(p, w)
    }

    open spec fn model(st: Vec<Re>) -> Seq<Re> {
        st@
    }

    open spec fn res(m: Seq<Re>, w: Seq<char>) -> bool {
        alt_res(m, w)
    }

    open spec fn start_spec(p: Re) -> Seq<Re> {
        parts(p)
    }

    open spec fn feed_spec(m: Seq<Re>, c: char) -> Seq<Re> {
        feed_all(m, c)
    }

    open spec fn final_spec(m: Seq<Re>) -> bool {
        any_nullable(m)
    }

    fn start(p: Re) -> (st: Vec<Re>) {
        parts_exec(&p)
    }

    fn feed(st: Vec<Re>, c: char) -> (r: Vec<Re>) {
        proof {
            assert(st@.subrange(0, st@.len() as int) =~= st@);
        }
        feed_from(&st, 0, c)
    }

    fn is_final(st: &Vec<Re>) -> (b: bool) {
        let mut i = st.len();
        let mut b = false;
        while i > 0
            invariant
                i <= st.len(),
                b == any_nullable(st@.subrange(i as int, st@.len() as int)),
            decreases i,
        {
            i = i - 1;
            proof {
                let s = st@.subrange(i as int, st@.len() as int);
                assert(s.drop_first() =~= st@.subrange(i + 1, st@.len() as int));
            }
            b = is_nullable(&st[i]) || b;
        }
        proof {
            assert(st@.subrange(0, st@.len() as int) =~= st@);
        }
        b
    }

    proof fn lemma_start_law(p: Re, w: Seq<char>) {
        // did: reveal the engine's model here, in this proof only
        reveal(alt_res);
        lemma_parts_law(p, w);
    }

    proof fn lemma_feed_law(m: Seq<Re>, c: char, w: Seq<char>) {
        lemma_alt_feed_law(m, c, w);
    }

    proof fn lemma_final_law(m: Seq<Re>) {
        lemma_alt_final_law(m);
    }
}

// item: R08.H2v
// pair: R08.H2d
/// **H2.** Splitting a pattern into its parts keeps its language.
///
/// Reference: induction on `r`. In the `Alt` case each direction moves one index across
/// `parts(a) + parts(b)`: a witness `i` of `parts(a)` is index `i` of the sum, a witness
/// `i` of `parts(b)` is index `parts(a).len() + i`, and back. In every other case except
/// `Empty` the list is `seq![r]`, whose one index is the witness.
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

// item: R08.H3v
// uses: trait-spec, reveal
// pair: R08.H3d
/// **H3.** The alternative-set engine's step law.
///
/// Reference: reveal `alt_res`, then induction on `m.len()`. For the empty list both sides
/// are false. Otherwise the stepped list is `head + tail` with
/// `head = parts(deriv(m[0], c))`: `lemma_parts_law` and `lemma_deriv_correct` turn
/// "some part of head matches w" into `matches(m[0], seq![c] + w)`, and the induction
/// hypothesis does the tail. Each direction moves one witness index across `head + tail`
/// and across `m[0]` / `m.drop_first()`.
pub proof fn lemma_alt_feed_law(m: Seq<Re>, c: char, w: Seq<char>)
    ensures
        alt_res(feed_all(m, c), w) == alt_res(m, seq![c] + w),
    decreases m.len(),
{
    // did: reveal the engine's model here, in this proof only
    reveal(alt_res);
    if m.len() > 0 {
        let head = parts(deriv(m[0], c));
        let tail = feed_all(m.drop_first(), c);
        lemma_alt_feed_law(m.drop_first(), c, w);
        lemma_parts_law(deriv(m[0], c), w);
        lemma_deriv_correct(m[0], c, w);
        if any_matches(head + tail, w) {
            let i = choose|i: int|
                0 <= i < (head + tail).len() && matches(#[trigger] (head + tail)[i], w);
            if i < head.len() {
                assert(matches(head[i], w));
            } else {
                assert(matches(tail[i - head.len()], w));
                let j = choose|j: int|
                    0 <= j < m.drop_first().len() && matches(
                        #[trigger] m.drop_first()[j],
                        seq![c] + w,
                    );
                assert(matches(m[j + 1], seq![c] + w));
            }
        }
        if any_matches(m, seq![c] + w) {
            let i = choose|i: int| 0 <= i < m.len() && matches(#[trigger] m[i], seq![c] + w);
            if i == 0 {
                let k = choose|k: int| 0 <= k < head.len() && matches(#[trigger] head[k], w);
                assert((head + tail)[k] == head[k]);
            } else {
                assert(matches(m.drop_first()[i - 1], seq![c] + w));
                let k = choose|k: int| 0 <= k < tail.len() && matches(#[trigger] tail[k], w);
                assert((head + tail)[head.len() + k] == tail[k]);
            }
        }
    }
}

// item: R08.H4v
// uses: trait-spec, reveal
// pair: R08.H4d
/// **H4.** The alternative-set engine's final law.
///
/// Reference: reveal `alt_res` here and nowhere wider. Induction on `m.len()`:
/// `lemma_nullable_correct` turns `nullable(m[0])` into a match of the empty word, the
/// induction hypothesis handles `m.drop_first()`, and one `assert forall` relates index `i`
/// of `m` to index `i - 1` of the tail, which lets the solver move the witness itself.
pub proof fn lemma_alt_final_law(m: Seq<Re>)
    ensures
        any_nullable(m) == alt_res(m, Seq::<char>::empty()),
    decreases m.len(),
{
    // did: reveal the engine's model here, in this proof only
    reveal(alt_res);
    if m.len() > 0 {
        lemma_alt_final_law(m.drop_first());
        lemma_nullable_correct(m[0]);
        assert forall|i: int| 0 < i < m.len() implies m[i] == m.drop_first()[i - 1] by {
        }
    }
}

/// A client of the alternative-set engine: the same contract as `match_deriv`.
pub fn match_alt(r: Re, w: &Vec<char>) -> (b: bool)
    ensures
        b == matches(r, w@),
{
    match_word::<AltSetEngine>(r, w)
}

/// A client of the range-star engine.
pub fn match_range_star(p: Vec<(char, char)>, w: &Vec<char>) -> (b: bool)
    ensures
        b == (forall|i: int| 0 <= i < w@.len() ==> in_char_ranges(p@, #[trigger] w@[i])),
{
    match_word::<RangeStarEngine>(p, w)
}

} // verus!

// item: R08.C3v recognise:open-spec
// An `open spec fn` in a trait implementation shows its body to every caller that can
// name the engine: a client of `RangeStarEngine` may unfold `res`. Through the trait (as
// `match_word` sees it) only the trait's laws are known. `#[verifier::opaque]` (the alternative-
// set engine's `alt_res`) hides the body even from the engine's own lemmas until revealed.
