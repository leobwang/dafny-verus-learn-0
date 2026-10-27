/* CONTRACT
goal: implement class_intersect and class_diff on every valid input with the frozen membership and validity postconditions
allowed-files:
  - verus/r/r03_modules/src/agent.rs
acceptance:
  - scripts/vcheck --gate verus/r/r03_modules/src/agent.rs exits 0, zero counted holes
  - scripts/specfreeze --against <snapshot> verus/r/r03_modules/src/agent.rs reports supplied statements unchanged
  - scripts/vaudit verus/r/r03_modules/src/agent.rs reports zero findings
  - preserve given code, private representation and contracts; no added requires, weakened ensures, assumptions or escape hatches
  - only this file may change; private implementation helpers may be added
*/
/*! Do not open this file before R03's hand holes are done (H1–H5, and in Verus
H6v and H7v): it copies the given class code, including the definitions H6v
and H7v ask you to write. R03 API implementer, R-v0. Save the original file as <snapshot> outside
the delivery before /contract R03 and record its hash. Review totality on
empty and equal inputs and the code boundaries: 0, u32::MAX, adjacent ranges,
a range across the surrogate block. Ranges are u32 code points (D48); nothing
here builds a char from a number.
ADVERSARIAL REVIEW — learner-owned, 30 minutes: check totality, API strength,
code boundaries, snapshot/freeze, delivery diff, audit, gate and transcript.
AGENT DASHBOARD — goal / changed files / obligations / gate / freeze / audit /
transcript / adversarial review / correction: ...
*/
#![allow(unused_imports)]
use vstd::prelude::*;

verus! {

// PROVIDED: a copy of the given class code (R03.W2v), u32 code-point ranges.

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

    closed spec fn view(&self) -> ISet<char> {
        ISet::new(|c: char| in_ranges(self.ranges@, c))
    }
}

impl CharClass {
    pub closed spec fn valid(&self) -> bool {
        separated(self.ranges@)
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

    // PROVIDED: the given insertion (R03.W2v).
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
}
/// PROVIDED: one more range of a prefix.
proof fn lemma_prefix_step(rs: Seq<(u32, u32)>, i: int, c: char)
    requires
        0 <= i < rs.len(),
    ensures
        in_ranges(rs.subrange(0, i + 1), c) <==> (in_ranges(rs.subrange(0, i), c) || in_range(rs[i], c)),
{
    assert(rs.subrange(0, i + 1) =~= rs.subrange(0, i).push(rs[i]));
    lemma_in_ranges_push(rs.subrange(0, i), rs[i], c);
}

impl CharClass {
    // item: R03.A1v
    #[verifier::external_body]
    pub fn class_intersect(&self, other: &CharClass) -> (r: CharClass)
        requires
            self.valid(),
            other.valid(),
        ensures
            r.valid(),
            r@ == self@.intersect(other@),
    {
        unimplemented!()
    }

    #[verifier::external_body]
    pub fn class_diff(&self, other: &CharClass) -> (r: CharClass)
        requires
            self.valid(),
            other.valid(),
        ensures
            r.valid(),
            r@ == self@.difference(other@),
    {
        unimplemented!()
    }
}


} // verus!
