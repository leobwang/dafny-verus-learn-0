//! rg_re_a2 — regex spine, layer A2: the character-class API (PROVIDED, complete; frozen;
//! provisional until R03 and R06 pass).
//! Do not open this file before R03 is done: it re-supplies R03's class API, complete and
//! proved. Finish R03's holes and record its first tries (`scripts/firsttry.sh R03 --check`).
//! Imported by R07–R16. Use only the layer chain declared by your module; PLAN.md §2.2 and §2.4.
//! Ranges are u32 code-point pairs: a range's view is the set of chars whose code lies
//! in it, and the only conversion is `c as u32`. The representation is private; read a
//! class's ranges only through the accessor `ranges`.
#![allow(unused_imports)]
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

/// The largest code of a range listing's last range (or `d` for no range).
spec fn last_hi(rs: Seq<(u32, u32)>, d: u32) -> u32 {
    if rs.len() == 0 {
        d
    } else {
        rs.last().1
    }
}

pub struct CharClass {
    ranges: Vec<(u32, u32)>,
}

impl View for CharClass {
    type V = ISet<char>;

    closed spec fn view(&self) -> ISet<char> {
        ISet::new(|c: char| in_ranges(self.ranges@, c))
    }
}

impl CharClass {
    pub closed spec fn valid(&self) -> bool {
        separated(self.ranges@)
    }

    /// The range listing (the accessor's model).
    pub closed spec fn ranges_spec(&self) -> Seq<(u32, u32)> {
        self.ranges@
    }

    /// Every range of the listing ends below code `b`.
    pub open spec fn ranges_below(&self, b: int) -> bool {
        forall|i: int| 0 <= i < self.ranges_spec().len() ==> (#[trigger] self.ranges_spec()[i]).1 < b
    }

    /// The read-only range accessor (for A3's lowering and size accounting).
    pub fn ranges(&self) -> (r: &Vec<(u32, u32)>)
        ensures
            r@ == self.ranges_spec(),
    {
        &self.ranges
    }

    /// The view and validity, stated through the listing.
    pub proof fn lemma_view_ranges(&self)
        ensures
            self@ == ISet::new(|c: char| in_ranges(self.ranges_spec(), c)),
            self.valid() == separated(self.ranges_spec()),
    {
        assert(self@ =~= ISet::new(|c: char| in_ranges(self.ranges_spec(), c)));
    }

    /// The empty class.
    pub fn class_empty() -> (r: CharClass)
        ensures
            r.valid(),
            r@ == ISet::<char>::empty(),
            r.ranges_spec().len() == 0,
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
            r.ranges_spec() == self.ranges_spec(),
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

    /// Is `c` in one of the ranges from index `i` on?
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

    /// Membership.
    pub fn class_member(&self, c: char) -> (b: bool)
        ensures
            b == self@.contains(c),
    {
        self.member_from(c, 0)
    }

    /// Insert the range `lo..=hi`, merging the ranges it overlaps or touches
    /// (total: an empty range `hi < lo` adds nothing).
    pub fn class_insert(&self, lo: u32, hi: u32) -> (res: CharClass)
        requires
            self.valid(),
        ensures
            res.valid(),
            res@ == self@.union(ISet::new(|c: char| lo <= (c as u32) && (c as u32) <= hi)),
            forall|b: int| self.ranges_below(b) && (hi as int) < b ==> #[trigger] res.ranges_below(b),
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
        let ghost m = if last_hi(rs, hi) < hi {
            hi
        } else {
            last_hi(rs, hi)
        };
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
            assert forall|j: int| 0 <= j < n implies (#[trigger] rs[j]).1 <= m by {
                if j < n - 1 {
                    assert(rs[j].1 + 1 < rs[n - 1].0);
                }
            }
        }
        while i < n
            invariant
                n == rs.len(),
                rs == self.ranges@,
                separated(rs),
                i <= n,
                clo <= chi,
                chi <= m,
                forall|j: int| 0 <= j < n ==> (#[trigger] rs[j]).1 <= m,
                forall|k: int| 0 <= k < out@.len() ==> (#[trigger] out@[k]).1 <= m,
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
            assert forall|bound: int| self.ranges_below(bound) && (hi as int) < bound implies #[trigger] res.ranges_below(bound) by {
                assert(self.ranges_spec() == rs);
                assert(res.ranges_spec() == out@);
                if n > 0 {
                    assert(self.ranges_spec()[n - 1].1 < bound);
                }
                assert(m < bound);
            }
        }
        res
    }

    /// The class of the one inclusive char interval `lo..=hi` (total: `hi < lo` gives
    /// the empty class).
    pub fn class_range(lo: char, hi: char) -> (r: CharClass)
        ensures
            r.valid(),
            forall|c: char| r@.contains(c) <==> (lo <= c && c <= hi),
    {
        let e = Self::class_empty();
        let r = e.class_insert(lo as u32, hi as u32);
        r
    }

    /// The union of two classes: every range of `other` inserted in turn.
    pub fn class_union(&self, other: &CharClass) -> (u: CharClass)
        requires
            self.valid(),
            other.valid(),
        ensures
            u.valid(),
            u@ == self@.union(other@),
            forall|b: int| self.ranges_below(b) && other.ranges_below(b) ==> #[trigger] u.ranges_below(b),
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
                os == other.ranges_spec(),
                i <= n,
                u.valid(),
                u@ == self@.union(ISet::new(|c: char| in_ranges(os.subrange(0, i as int), c))),
                forall|b: int| self.ranges_below(b) && other.ranges_below(b) ==> #[trigger] u.ranges_below(b),
            decreases n - i,
        {
            let (a, b) = other.ranges[i];
            let ghost u0 = u;
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
                assert forall|bound: int| self.ranges_below(bound) && other.ranges_below(bound) implies #[trigger] u.ranges_below(bound) by {
                    assert(u0.ranges_below(bound));
                    assert(os[i as int] == (a, b));
                    assert((b as int) < bound);
                }
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

/// The set of the characters of a sequence.
pub open spec fn class_chars(s: Seq<char>) -> ISet<char> {
    ISet::new(|c: char| s.contains(c))
}

proof fn lemma_class_chars_push(s: Seq<char>, c: char)
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

/// The class of the characters of a string.
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

} // verus!
