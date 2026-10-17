/*! R03 — Modules and APIs (Reference Solution).
Standalone R. The local class implementation reuses the supplied range merge,
not a later A2 import. This half has five holes; the Dafny half has five.
Record P1d/P2v and P3dv/P4dv before running scenarios or reading outcomes.
Finish with zero-hole gates, clean audits, specfreeze and the strict report.
Keep private representation, public statements and given code fixed.
*/
#![allow(unused_imports)]
use vstd::prelude::*;

verus! {
pub mod char_class {
use vstd::prelude::*;

verus! {

spec fn in_range(g: (char, char), c: char) -> bool {
    g.0 <= c && c <= g.1
}

spec fn in_ranges(rs: Seq<(char, char)>, c: char) -> bool {
    exists|i: int| 0 <= i < rs.len() && in_range(#[trigger] rs[i], c)
}

spec fn sorted_ranges(rs: Seq<(char, char)>) -> bool {
    &&& forall|i: int| 0 <= i < rs.len() ==> (#[trigger] rs[i]).0 <= rs[i].1
    &&& forall|i: int, j: int| 0 <= i < j < rs.len() ==> (#[trigger] rs[i]).1 < (#[trigger] rs[j]).0
}

proof fn lemma_in_ranges_push(rs: Seq<(char, char)>, x: (char, char), c: char)
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

proof fn lemma_in_ranges_drop(rs: Seq<(char, char)>, i: int, c: char)
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

spec fn cover(out: Seq<(char, char)>, placed: bool, clo: char, chi: char, rest: Seq<(char, char)>, c: char) -> bool {
    in_ranges(out, c) || (!placed && clo <= c && c <= chi) || in_ranges(rest, c)
}

spec fn target(rs: Seq<(char, char)>, lo: char, hi: char, c: char) -> bool {
    in_ranges(rs, c) || (lo <= c && c <= hi)
}

/// One step of `class_insert`'s loop keeps the covered set (the three branches).
proof fn lemma_insert_step(
    rs: Seq<(char, char)>,
    i: int,
    lo: char,
    hi: char,
    out0: Seq<(char, char)>,
    placed0: bool,
    clo0: char,
    chi0: char,
    out1: Seq<(char, char)>,
    placed1: bool,
    clo1: char,
    chi1: char,
)
    requires
        0 <= i < rs.len(),
        forall|c: char|
            #![trigger target(rs, lo, hi, c)]
            cover(out0, placed0, clo0, chi0, rs.subrange(i, rs.len() as int), c) == target(rs, lo, hi, c),
        (placed0 || rs[i].1 < clo0) ==> out1 == out0.push(rs[i]) && placed1 == placed0 && clo1 == clo0
            && chi1 == chi0,
        !(placed0 || rs[i].1 < clo0) && chi0 < rs[i].0 ==> out1 == out0.push((clo0, chi0)).push(rs[i])
            && placed1,
        !(placed0 || rs[i].1 < clo0) && !(chi0 < rs[i].0) ==> out1 == out0 && placed1 == placed0 && clo1
            == (if rs[i].0 < clo0 { rs[i].0 } else { clo0 }) && chi1 == (if chi0 < rs[i].1 { rs[i].1 } else { chi0 }),
    ensures
        forall|c: char|
            #![trigger target(rs, lo, hi, c)]
            cover(out1, placed1, clo1, chi1, rs.subrange(i + 1, rs.len() as int), c) == target(rs, lo, hi, c),
{
    assert forall|c: char|
        #![trigger target(rs, lo, hi, c)]
        cover(out1, placed1, clo1, chi1, rs.subrange(i + 1, rs.len() as int), c) == target(rs, lo, hi, c) by {
        lemma_in_ranges_drop(rs, i, c);
        if placed0 || rs[i].1 < clo0 {
            lemma_in_ranges_push(out0, rs[i], c);
        } else if chi0 < rs[i].0 {
            lemma_in_ranges_push(out0, (clo0, chi0), c);
            lemma_in_ranges_push(out0.push((clo0, chi0)), rs[i], c);
        }
    }
}

pub struct CharClass {
    ranges: Vec<(char, char)>,
}

impl View for CharClass {
    type V = ISet<char>;

    closed spec fn view(&self) -> ISet<char> {
        ISet::new(|c: char| in_ranges(self.ranges@, c))
    }
}

impl CharClass {
    pub closed spec fn valid(&self) -> bool {
        sorted_ranges(self.ranges@)
    }

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
        let mut out: Vec<(char, char)> = Vec::new();
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

    /// Is `c` in one of the ranges from index `i` on? (R03.H1v)
    // item: R03.H1v
// uses: view
// pair: R03.H1d
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
            (lo <= c && c <= hi) || self.member_from(c, i + 1)
        }
    }

    /// Membership.
    pub fn class_member(&self, c: char) -> (b: bool)
        ensures
            b == self@.contains(c),
    {
        self.member_from(c, 0)
    }

    // item: R03.W2v
    /// Insert the range `lo..=hi`, merging the ranges it overlaps (R03.W2v, given).
    pub fn class_insert(&self, lo: char, hi: char) -> (res: CharClass)
        requires
            self.valid(),
        ensures
            res.valid(),
            res@ == self@.union(ISet::new(|c: char| lo <= c && c <= hi)),
    {
        if hi < lo {
            let res = self.copy_class();
            proof {
                assert(res@ =~= self@.union(ISet::new(|c: char| lo <= c && c <= hi)));
            }
            return res;
        }
        let n = self.ranges.len();
        let ghost rs = self.ranges@;
        let mut out: Vec<(char, char)> = Vec::new();
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
                sorted_ranges(rs),
                i <= n,
                clo <= chi,
                sorted_ranges(out@),
                forall|k: int, j: int|
                    0 <= k < out@.len() && i <= j < n ==> (#[trigger] out@[k]).1 < (#[trigger] rs[j]).0,
                !placed ==> forall|k: int| 0 <= k < out@.len() ==> (#[trigger] out@[k]).1 < clo,
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
            if placed || b < clo {
                out.push((a, b));
            } else if chi < a {
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
                in_ranges(out@, c) <==> (in_ranges(rs, c) || (lo <= c && c <= hi)) by {
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
                res@.contains(c) <==> self@.union(ISet::new(|c: char| lo <= c && c <= hi)).contains(c)
                by {
                assert(res@.contains(c) == in_ranges(out@, c));
                assert(self@.contains(c) == in_ranges(rs, c));
            }
            assert(res@ =~= self@.union(ISet::new(|c: char| lo <= c && c <= hi)));
        }
        res
    }

    /// Construct the class described by one interval.
    // item: R03.H2v
// uses: view, closed-spec, pub-visibility
// pair: R03.H2d
// triv: { Self::class_empty() }
pub fn class_range(lo: char, hi: char) -> (r: CharClass)
        ensures r.valid(), forall|c: char| r@.contains(c) <==> (lo <= c && c <= hi),
{ Self::class_empty().class_insert(lo, hi) }

// item: R03.H3v
// uses: view, closed-spec
// pair: R03.H3d
// triv: { Self::class_empty() }
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
// uses: pub-visibility
// pair: R03.H4d
// triv: { CharClass::class_empty() }

pub fn union3(a: &CharClass, b: &CharClass, c: &CharClass) -> (u: CharClass)
    requires a.valid(), b.valid(), c.valid(),
    ensures u.valid(), u@ == a@.union(b@).union(c@),
{ let t=a.class_union(b); t.class_union(c) }

// Given model of the character set of a sequence, plus its append-one fact.
pub open spec fn class_chars(s: Seq<char>) -> ISet<char> {
    ISet::new(|c: char| s.contains(c))
}
pub proof fn lemma_class_chars_push(s: Seq<char>, c: char)
    ensures class_chars(s.push(c)) == class_chars(s).insert(c),
{
    assert forall|x: char| class_chars(s.push(c)).contains(x)
        <==> class_chars(s).insert(c).contains(x) by {
        if s.push(c).contains(x) {
            let i=choose|i: int| 0 <= i < s.push(c).len() && s.push(c)[i] == x;
            if i < s.len() { assert(s[i] == x); }
        }
        if s.contains(x) {
            let i=choose|i: int| 0 <= i < s.len() && s[i] == x;
            assert(s.push(c)[i] == x);
        }
        if x == c { assert(s.push(c)[s.len() as int] == x); }
    }
    assert(class_chars(s.push(c)) =~= class_chars(s).insert(c));
}

// item: R03.H5v
// uses: view
// pair: R03.H5d
// triv: { CharClass::class_empty() }

pub fn class_of_string(s: &Vec<char>) -> (r: CharClass)
    ensures r.valid(), forall|c: char| r@.contains(c) <==> s@.contains(c),
{
    let mut u=CharClass::class_empty(); let mut i: usize=0;
    proof { assert(class_chars(s@.subrange(0, 0)) =~= ISet::<char>::empty()); }
    while i < s.len()
        invariant i <= s.len(), u.valid(),
            u@ == class_chars(s@.subrange(0, i as int)),
        decreases s.len() - i,
    {
        let c=s[i]; let ghost pre=s@.subrange(0, i as int);
        u=u.class_insert(c, c);
        proof {
            assert(s@.subrange(0, i + 1) =~= pre.push(c));
            lemma_class_chars_push(pre, c);
            assert(ISet::new(|x: char| c <= x && x <= c) =~= ISet::<char>::empty().insert(c));
            assert(u@ =~= class_chars(s@.subrange(0, i + 1)));
        }
        i=i+1;
    }
    proof { assert(s@.subrange(0, s.len() as int) =~= s@); }
    u
 }

// Reference checks (enabled):
// reference-only: enabled shipped check
fn interface_checks() { let x=CharClass::class_range('a', 'c'); let b=x.class_member('b'); assert(b); let mut cs=Vec::new(); cs.push('d'); assert(cs@[0] == 'd'); assert(cs@.contains('d')); let y=class_of_string(&cs); assert(y@.contains('d')); let u=x.class_union(&y); assert(u@.contains('d')); let d=u.class_member('d'); assert(d); }
}
}

pub mod span_api {
use vstd::prelude::*;
// item: R03.W1v
pub struct SpanBox { lo: char, hi: char, }

// item: R03.C3v write:view
impl View for SpanBox {
    type V = (char, char);
    closed spec fn view(&self) -> (char, char) { (self.lo, self.hi) }
}
impl SpanBox {
    // item: R03.C4v write:closed-spec
    pub closed spec fn valid(&self) -> bool { self.lo <= self.hi }

    // item: R03.C5v write:pub-visibility
    pub fn make_span(lo: char, hi: char) -> (s: SpanBox)
        requires lo <= hi,
        ensures s.valid(), s@ == (lo, hi),
    { SpanBox { lo, hi } }
    pub fn span_has(&self, c: char) -> (b: bool)
        ensures b == (self@.0 <= c && c <= self@.1),
    { self.lo <= c && c <= self.hi }
}

// item: R03.C7v recognise:opaque
#[verifier::opaque]
spec fn span_code(c: char) -> int { c as int }
}
pub mod span_client {
use vstd::prelude::*;
use super::span_api::SpanBox;
pub fn span_contract_example() {
    let s=SpanBox::make_span('a', 'd');
    assert(s.valid());
    let b=s.span_has('c'); assert(b);
}
}

} // outer verified module declarations
