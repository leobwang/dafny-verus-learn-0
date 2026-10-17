//! rg_re_a2 — regex spine, layer A2 (PROVIDED, complete; frozen).
//! Imported by R07–R16: the character-class API and derivative matcher re-supplied after band 1.
//! Use only the layer chain declared by your module; PLAN.md §2.2 and §2.4.
#![allow(unused_imports)]
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

    /// The union of two classes (R03.H3v): every range of `other` inserted in turn.
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
