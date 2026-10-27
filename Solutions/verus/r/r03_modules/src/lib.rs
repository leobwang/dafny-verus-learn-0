/*! R03 — Modules and APIs (Reference Solution).
Class ranges are u32 code-point pairs (D48): a range's view is the set of chars whose
code lies in it, and the only conversion is `c as u32`.
Standalone R. The local class implementation reuses the supplied range merge,
not a later A2 import. This half has seven hole items (H1v-H7v; 11 counted holes
as shipped, with the four GATED attributes on the given functions that need H6v
and H7v); the Dafny half has five.
Record P1d/P2v and P3dv/P4dv before running scenarios or reading outcomes.
Finish with zero-hole gates, clean audits, specfreeze and the strict report.
Keep private representation, public statements and given code fixed.
*/
#![allow(unused_imports)]
use vstd::prelude::*;

verus! {
pub mod char_class {
// specfreeze: open-visibility
use vstd::prelude::*;

verus! {

/// `c`'s code lies in the inclusive range `g`.
pub open spec fn in_range(g: (u32, u32), c: char) -> bool {
    g.0 <= (c as u32) && (c as u32) <= g.1
}

/// `c`'s code lies in one of the ranges.
pub open spec fn in_ranges(rs: Seq<(u32, u32)>, c: char) -> bool {
    exists|i: int| 0 <= i < rs.len() && in_range(#[trigger] rs[i], c)
}

/// Non-empty ranges, sorted and separated by at least one code.
pub open spec fn separated(rs: Seq<(u32, u32)>) -> bool {
    &&& forall|i: int| 0 <= i < rs.len() ==> (#[trigger] rs[i]).0 <= rs[i].1
    &&& forall|i: int, j: int| 0 <= i < j < rs.len() ==> (#[trigger] rs[i]).1 + 1 < (#[trigger] rs[j]).0
}

proof fn lemma_in_ranges_push(rs: Seq<(u32, u32)>, x: (u32, u32), c: char)
    ensures
        in_ranges(rs.push(x), c) <==> (in_ranges(rs, c) || in_range(x, c)),
{
    let t = rs.push(x);
    if in_ranges(t, c) {
        let i = choose|i: int| 0 <= i < t.len() && in_range(#[trigger] t[i], c);
        if i < rs.len() {
            assert(t[i] == rs[i]);
        }
    }
    if in_ranges(rs, c) {
        let i = choose|i: int| 0 <= i < rs.len() && in_range(#[trigger] rs[i], c);
        assert(t[i] == rs[i]);
    }
    if in_range(x, c) {
        assert(t[rs.len() as int] == x);
    }
}

proof fn lemma_in_ranges_drop(rs: Seq<(u32, u32)>, i: int, c: char)
    requires
        0 <= i < rs.len(),
    ensures
        in_ranges(rs.subrange(i, rs.len() as int), c) <==> (in_range(rs[i], c) || in_ranges(
            rs.subrange(i + 1, rs.len() as int),
            c,
        )),
{
    let t = rs.subrange(i, rs.len() as int);
    let t1 = rs.subrange(i + 1, rs.len() as int);
    if in_ranges(t, c) {
        let k = choose|k: int| 0 <= k < t.len() && in_range(#[trigger] t[k], c);
        if k > 0 {
            assert(t1[k - 1] == t[k]);
        }
    }
    if in_range(rs[i], c) {
        assert(t[0] == rs[i]);
    }
    if in_ranges(t1, c) {
        let k = choose|k: int| 0 <= k < t1.len() && in_range(#[trigger] t1[k], c);
        assert(t[k + 1] == t1[k]);
    }
}

spec fn cover(out: Seq<(u32, u32)>, placed: bool, clo: u32, chi: u32, rest: Seq<(u32, u32)>, c: char) -> bool {
    in_ranges(out, c) || (!placed && clo <= (c as u32) && (c as u32) <= chi) || in_ranges(rest, c)
}

spec fn target(rs: Seq<(u32, u32)>, lo: u32, hi: u32, c: char) -> bool {
    in_ranges(rs, c) || (lo <= (c as u32) && (c as u32) <= hi)
}

/// One step of `class_insert`'s loop keeps the covered set (the three branches).
proof fn lemma_insert_step(
    rs: Seq<(u32, u32)>,
    i: int,
    lo: u32,
    hi: u32,
    out0: Seq<(u32, u32)>,
    placed0: bool,
    clo0: u32,
    chi0: u32,
    out1: Seq<(u32, u32)>,
    placed1: bool,
    clo1: u32,
    chi1: u32,
)
    requires
        0 <= i < rs.len(),
        forall|c: char|
            #![trigger target(rs, lo, hi, c)]
            cover(out0, placed0, clo0, chi0, rs.subrange(i, rs.len() as int), c) == target(rs, lo, hi, c),
        (placed0 || rs[i].1 + 1 < clo0) ==> out1 == out0.push(rs[i]) && placed1 == placed0
            && clo1 == clo0 && chi1 == chi0,
        !(placed0 || rs[i].1 + 1 < clo0) && chi0 + 1 < rs[i].0 ==> out1 == out0.push((clo0, chi0)).push(rs[i])
            && placed1,
        !(placed0 || rs[i].1 + 1 < clo0) && !(chi0 + 1 < rs[i].0) ==> out1 == out0 && placed1 == placed0
            && clo1 == (if rs[i].0 < clo0 { rs[i].0 } else { clo0 })
            && chi1 == (if chi0 < rs[i].1 { rs[i].1 } else { chi0 }),
    ensures
        forall|c: char|
            #![trigger target(rs, lo, hi, c)]
            cover(out1, placed1, clo1, chi1, rs.subrange(i + 1, rs.len() as int), c) == target(rs, lo, hi, c),
{
    assert forall|c: char|
        #![trigger target(rs, lo, hi, c)]
        cover(out1, placed1, clo1, chi1, rs.subrange(i + 1, rs.len() as int), c) == target(rs, lo, hi, c) by {
        lemma_in_ranges_drop(rs, i, c);
        if placed0 || rs[i].1 + 1 < clo0 {
            lemma_in_ranges_push(out0, rs[i], c);
        } else if chi0 + 1 < rs[i].0 {
            lemma_in_ranges_push(out0, (clo0, chi0), c);
            lemma_in_ranges_push(out0.push((clo0, chi0)), rs[i], c);
        }
    }
}

pub struct CharClass {
    ranges: Vec<(u32, u32)>,
}

impl View for CharClass {
    type V = ISet<char>;

    /// The view is `chars` (H7v): the abstraction function of the square.
    closed spec fn view(&self) -> ISet<char> {
        self.chars()
    }
}

impl CharClass {
    // item: R03.H6v
    // uses: closed-spec
    /// **H6.** The representation invariant: every range is non-empty, and the
    /// ranges are sorted and separated by at least one code.
    ///
    /// Reference: `separated(self.ranges@)`. The body reads the private field, so a
    /// public spec fn over it must be `closed`: `open` is refused. Until H6v and H7v
    /// exist, the four given functions below cannot be checked against them.
    pub closed spec fn valid(&self) -> bool {
        separated(self.ranges@)
    }

    // item: R03.H7v
    // uses: closed-spec
    /// **H7.** The chars a class holds: those whose code lies in one of its ranges.
    /// The view is this set.
    ///
    /// Reference: `ISet::new(|c: char| in_ranges(self.ranges@, c))`, `closed` for the
    /// same reason as H6v. `class_empty`, `copy_class`, `class_member` and W2v's
    /// `class_insert` are proved against H6v and H7v.
    pub closed spec fn chars(&self) -> ISet<char> {
        ISet::new(|c: char| in_ranges(self.ranges@, c))
    }

    /// The number of ranges in the representation (Dafny's `ClassRank`).
    pub closed spec fn rank(&self) -> nat {
        self.ranges@.len()
    }
}

// Given: the class's basic operations, proved against H6v and H7v.
impl CharClass {

    /// The empty class.
    pub fn class_empty() -> (r: CharClass)
        ensures
            r.valid(),
            r@ == ISet::<char>::empty(),
    {
        let r = CharClass { ranges: Vec::new() };
        proof {
            assert(r@ =~= ISet::<char>::empty());
        }
        r
    }

    /// A copy of the class.
    pub fn copy_class(&self) -> (r: CharClass)
        ensures
            r@ == self@,
            r.valid() == self.valid(),
    {
        let n = self.ranges.len();
        let mut out: Vec<(u32, u32)> = Vec::new();
        let mut k: usize = 0;
        while k < n
            invariant
                n == self.ranges@.len(),
                k <= n,
                out@ == self.ranges@.subrange(0, k as int),
            decreases n - k,
        {
            out.push(self.ranges[k]);
            k = k + 1;
        }
        proof {
            assert(out@ =~= self.ranges@);
        }
        CharClass { ranges: out }
    }

    /// Membership.
    pub fn class_member(&self, c: char) -> (b: bool)
        ensures
            b == self@.contains(c),
    {
        self.member_from(c, 0)
    }

    // item: R03.H1v
    // pair: R03.H1d
    /// **H1.** Is `c` in one of the ranges from index `i` on?
    ///
    /// Reference: recursion on `i` up to `self.ranges.len()`, with `decreases
    /// self.ranges@.len() - i`. At the end there is no range; otherwise compare
    /// `c as u32` with range `i`'s bounds, or ask the rest.
    fn member_from(&self, c: char, i: usize) -> (b: bool)
        requires
            i <= self.ranges@.len(),
        ensures
            b == (exists|j: int| i <= j < self.ranges@.len() && in_range(#[trigger] self.ranges@[j], c)),
        decreases self.ranges@.len() - i,
    {
        if i == self.ranges.len() {
            false
        } else {
            let (lo, hi) = self.ranges[i];
            let code = c as u32;
            (lo <= code && code <= hi) || self.member_from(c, i + 1)
        }
    }


    // item: R03.W2v
    /// Insert the range `lo..=hi`, merging the ranges it overlaps or touches
    /// (total: an empty range `hi < lo` adds nothing).
    pub fn class_insert(&self, lo: u32, hi: u32) -> (res: CharClass)
        requires
            self.valid(),
        ensures
            res.valid(),
            res@ == self@.union(ISet::new(|c: char| lo <= (c as u32) && (c as u32) <= hi)),
    {
        if hi < lo {
            let res = self.copy_class();
            proof {
                assert(res@ =~= self@.union(ISet::new(|c: char| lo <= (c as u32) && (c as u32) <= hi)));
            }
            return res;
        }
        let n = self.ranges.len();
        let ghost rs = self.ranges@;
        let mut out: Vec<(u32, u32)> = Vec::new();
        let mut clo = lo;
        let mut chi = hi;
        let mut placed = false;
        let mut i: usize = 0;
        proof {
            assert(rs.subrange(0, n as int) =~= rs);
            assert forall|c: char|
                #![trigger target(rs, lo, hi, c)]
                cover(out@, placed, clo, chi, rs.subrange(i as int, n as int), c) == target(rs, lo, hi, c) by {}
        }
        while i < n
            invariant
                n == rs.len(),
                rs == self.ranges@,
                separated(rs),
                i <= n,
                clo <= chi,
                separated(out@),
                forall|k: int, j: int|
                    0 <= k < out@.len() && i <= j < n ==> (#[trigger] out@[k]).1 + 1 < (#[trigger] rs[j]).0,
                !placed ==> forall|k: int| 0 <= k < out@.len() ==> (#[trigger] out@[k]).1 + 1 < clo,
                forall|c: char|
                    #![trigger target(rs, lo, hi, c)]
                    cover(out@, placed, clo, chi, rs.subrange(i as int, n as int), c) == target(rs, lo, hi, c),
            decreases n - i,
        {
            let (a, b) = self.ranges[i];
            let ghost out0 = out@;
            let ghost clo0 = clo;
            let ghost chi0 = chi;
            let ghost placed0 = placed;
            if placed || (b < clo && clo - b > 1) {
                out.push((a, b));
            } else if chi < a && a - chi > 1 {
                out.push((clo, chi));
                out.push((a, b));
                placed = true;
            } else {
                if a < clo {
                    clo = a;
                }
                if chi < b {
                    chi = b;
                }
            }
            proof {
                assert(rs[i as int] == (a, b));
                lemma_insert_step(rs, i as int, lo, hi, out0, placed0, clo0, chi0, out@, placed, clo, chi);
            }
            i = i + 1;
        }
        let ghost out0 = out@;
        if !placed {
            out.push((clo, chi));
        }
        proof {
            assert forall|c: char|
                in_ranges(out@, c) <==> (in_ranges(rs, c) || (lo <= (c as u32) && (c as u32) <= hi)) by {
                if !placed {
                    lemma_in_ranges_push(out0, (clo, chi), c);
                }
                assert(!in_ranges(rs.subrange(n as int, n as int), c));
                assert(cover(out0, placed, clo, chi, rs.subrange(n as int, n as int), c) == target(rs, lo, hi, c));
            }
        }
        let res = CharClass { ranges: out };
        proof {
            assert forall|c: char|
                res@.contains(c) <==> self@.union(ISet::new(|c: char| lo <= (c as u32) && (c as u32) <= hi)).contains(c)
                by {
                assert(res@.contains(c) == in_ranges(out@, c));
                assert(self@.contains(c) == in_ranges(rs, c));
            }
            assert(res@ =~= self@.union(ISet::new(|c: char| lo <= (c as u32) && (c as u32) <= hi)));
        }
        res
    }

    // item: R03.H2v
    // uses: view, pub-visibility
    // pair: R03.H2d
    // triv: { Self::class_empty() }
    /// **H2.** The class of the one inclusive char interval `lo..=hi`, as at most one
    /// range: total, `hi < lo` gives the empty class. The client module calls it, so
    /// it must be public.
    ///
    /// Reference: build the representation directly (one range `(lo as u32, hi as u32)`
    /// when `lo <= hi`, none otherwise): `class_insert` promises nothing about the number
    /// of ranges. Membership needs the witness range 0 for each char of the interval;
    /// the char order is the code order. Add `pub`.
    pub fn class_range(lo: char, hi: char) -> (r: CharClass)
        ensures
            r.valid(),
            r.rank() <= 1,
            forall|c: char| r@.contains(c) <==> (lo <= c && c <= hi),
    {
        let mut v: Vec<(u32, u32)> = Vec::new();
        if lo <= hi {
            v.push((lo as u32, hi as u32));
        }
        let r = CharClass { ranges: v };
        proof {
            assert forall|c: char| r@.contains(c) <==> (lo <= c && c <= hi) by {
                if lo <= c && c <= hi {
                    assert(in_range(r.ranges@[0], c));
                }
            }
        }
        r
    }

    // item: R03.H3v
    // uses: view, pub-visibility
    // pair: R03.H3d
    // triv: { Self::class_empty() }
    /// **H3.** The union of two classes: every range of `other` inserted in turn. The
    /// client module calls it, so it must be public.
    ///
    /// Reference: a loop over `other`'s ranges with the invariant `u@ ==
    /// self@.union(…the chars of the first i ranges…)`. Each step uses
    /// `lemma_in_ranges_push` to extend the prefix by one range. Add `pub`.
    pub fn class_union(&self, other: &CharClass) -> (u: CharClass)
        requires
            self.valid(),
            other.valid(),
        ensures
            u.valid(),
            u@ == self@.union(other@),
    {
        let n = other.ranges.len();
        let ghost os = other.ranges@;
        let mut u = self.copy_class();
        let mut i: usize = 0;
        proof {
            assert(ISet::new(|c: char| in_ranges(os.subrange(0, 0), c)) =~= ISet::<char>::empty());
            assert(u@ =~= self@.union(ISet::new(|c: char| in_ranges(os.subrange(0, 0), c))));
        }
        while i < n
            invariant
                n == os.len(),
                os == other.ranges@,
                i <= n,
                u.valid(),
                u@ == self@.union(ISet::new(|c: char| in_ranges(os.subrange(0, i as int), c))),
            decreases n - i,
        {
            let (a, b) = other.ranges[i];
            u = u.class_insert(a, b);
            proof {
                let pre = os.subrange(0, i as int);
                assert(os.subrange(0, i + 1) =~= pre.push((a, b)));
                assert forall|c: char|
                    u@.contains(c) <==> self@.union(
                        ISet::new(|c: char| in_ranges(os.subrange(0, i + 1), c)),
                    ).contains(c) by {
                    lemma_in_ranges_push(pre, (a, b), c);
                }
                assert(u@ =~= self@.union(ISet::new(|c: char| in_ranges(os.subrange(0, i + 1), c))));
            }
            i = i + 1;
        }
        proof {
            assert(os.subrange(0, n as int) =~= os);
            assert(u@ =~= self@.union(other@));
        }
        u
    }
}

} // verus!
}

pub mod client {
use vstd::prelude::*;
use super::char_class::CharClass;

verus! {

// item: R03.H4v
// uses: view
// pair: R03.H4d
// triv: { CharClass::class_empty() }
/// **H4.** A client of the public API only: the union of a sequence of classes.
///
/// Reference: a loop over `cs` from the empty class, one `class_union` per class,
/// with four invariant clauses: the index bound, every class valid, `u.valid()`, and
/// `u@` holding exactly the chars of the first `k` classes.
pub fn union_of_classes(cs: &Vec<CharClass>) -> (u: CharClass)
    requires
        forall|i: int| 0 <= i < cs.len() ==> (#[trigger] cs[i]).valid(),
    ensures
        u.valid(),
        forall|x: char| u@.contains(x) <==> (exists|i: int| 0 <= i < cs.len() && (#[trigger] cs[i])@.contains(x)),
{
    let mut u = CharClass::class_empty();
    let mut k: usize = 0;
    while k < cs.len()
        invariant
            k <= cs.len(),
            forall|i: int| 0 <= i < cs.len() ==> (#[trigger] cs[i]).valid(),
            u.valid(),
            forall|x: char| u@.contains(x) <==> (exists|i: int| 0 <= i < k && (#[trigger] cs[i])@.contains(x)),
        decreases cs.len() - k,
    {
        u = u.class_union(&cs[k]);
        k = k + 1;
    }
    u
}

// Given model of the character set of a sequence, plus its append-one fact.
pub open spec fn class_chars(s: Seq<char>) -> ISet<char> {
    ISet::new(|c: char| s.contains(c))
}

pub proof fn lemma_class_chars_push(s: Seq<char>, c: char)
    ensures
        class_chars(s.push(c)) == class_chars(s).insert(c),
{
    assert forall|x: char| class_chars(s.push(c)).contains(x) <==> class_chars(s).insert(c).contains(x) by {
        if s.push(c).contains(x) {
            let i = choose|i: int| 0 <= i < s.push(c).len() && s.push(c)[i] == x;
            if i < s.len() {
                assert(s[i] == x);
            }
        }
        if s.contains(x) {
            let i = choose|i: int| 0 <= i < s.len() && s[i] == x;
            assert(s.push(c)[i] == x);
        }
        if x == c {
            assert(s.push(c)[s.len() as int] == x);
        }
    }
    assert(class_chars(s.push(c)) =~= class_chars(s).insert(c));
}

// item: R03.H5v
// uses: view
// pair: R03.H5d
// triv: { CharClass::class_empty() }
/// **H5.** The class of the characters of a string.
///
/// Reference: a loop over the string with the invariant `u@ ==
/// class_chars(s@.subrange(0, i))`. Each step inserts `(c as u32, c as u32)`
/// and uses `lemma_class_chars_push`; the one-code range holds exactly `c`.
pub fn class_of_string(s: &Vec<char>) -> (r: CharClass)
    ensures
        r.valid(),
        forall|c: char| r@.contains(c) <==> s@.contains(c),
{
    let mut u = CharClass::class_empty();
    let mut i: usize = 0;
    proof {
        assert(class_chars(s@.subrange(0, 0)) =~= ISet::<char>::empty());
    }
    while i < s.len()
        invariant
            i <= s.len(),
            u.valid(),
            u@ == class_chars(s@.subrange(0, i as int)),
        decreases s.len() - i,
    {
        let c = s[i];
        let ghost pre = s@.subrange(0, i as int);
        u = u.class_insert(c as u32, c as u32);
        proof {
            assert(s@.subrange(0, i + 1) =~= pre.push(c));
            lemma_class_chars_push(pre, c);
            assert(ISet::new(|x: char| (c as u32) <= (x as u32) && (x as u32) <= (c as u32)) =~= ISet::<char>::empty().insert(c));
            assert(u@ =~= class_chars(s@.subrange(0, i + 1)));
        }
        i = i + 1;
    }
    proof {
        assert(s@.subrange(0, s.len() as int) =~= s@);
    }
    u
}

// The client checks: the API's contracts at concrete classes. The second is the
// abstraction square: two representations (a split pair of ranges and one range
// across the surrogate block, which is valid and adds no char) with one view; a
// client can rely only on the view.
// Reference checks (enabled):
// reference-only: enabled shipped check
fn interface_checks() {
    let x = CharClass::class_range('a', 'c');
    let b = x.class_member('b');
    assert(b);
    let mut cs = Vec::new();
    cs.push('d');
    assert(cs@[0] == 'd');
    assert(cs@.contains('d'));
    let y = class_of_string(&cs);
    assert(y@.contains('d'));
    let u = x.class_union(&y);
    assert(u@.contains('d'));
    let d = u.class_member('d');
    assert(d);
}

// reference-only: enabled shipped check
fn surrogate_span_check() {
    let e = CharClass::class_empty();
    let low = e.class_insert(0xD7FF, 0xD7FF);
    let split = low.class_insert(0xE000, 0xE000);
    let span = e.class_insert(0xD7FF, 0xE000);
    let in_split = split.class_member('\u{E000}');
    let in_span = span.class_member('\u{E000}');
    let a_in_span = span.class_member('a');
    assert(in_split);
    assert(in_span);
    assert(!a_in_span);
}
// end reference checks

} // verus!
}

pub mod span_api {
use vstd::prelude::*;

verus! {

// item: R03.W1v
pub struct SpanBox {
    lo: char,
    hi: char,
}

// item: R03.C3v write:view
impl View for SpanBox {
    type V = (char, char);

    closed spec fn view(&self) -> (char, char) {
        (self.lo, self.hi)
    }
}

impl SpanBox {
    // item: R03.C4v write:closed-spec
    pub closed spec fn valid(&self) -> bool {
        self.lo <= self.hi
    }

    // item: R03.C5v write:pub-visibility
    pub fn make_span(lo: char, hi: char) -> (s: SpanBox)
        requires
            lo <= hi,
        ensures
            s.valid(),
            s@ == (lo, hi),
    {
        SpanBox { lo, hi }
    }

    pub fn span_has(&self, c: char) -> (b: bool)
        ensures
            b == (self@.0 <= c && c <= self@.1),
    {
        self.lo <= c && c <= self.hi
    }
}

// item: R03.C7v recognise:opaque
#[verifier::opaque]
spec fn span_code(c: char) -> int {
    c as int
}

} // verus!
}

pub mod span_client {
use vstd::prelude::*;
use super::span_api::SpanBox;

verus! {

pub fn span_contract_example() {
    let s = SpanBox::make_span('a', 'd');
    assert(s.valid());
    let b = s.span_has('c');
    assert(b);
}

} // verus!
}

} // outer verified module declarations
