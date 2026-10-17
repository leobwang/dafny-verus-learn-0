/* CONTRACT
goal: implement class_intersect and class_diff on every valid input with the frozen membership and validity postconditions
allowed-files:
  - verus/r/r03_modules/src/agent.rs
acceptance:
  - scripts/vcheck --gate verus/r/r03_modules/src/agent.rs exits0, zero counted holes
  - scripts/specfreeze --against <snapshot> verus/r/r03_modules/src/agent.rs reports supplied statements unchanged
  - scripts/vaudit verus/r/r03_modules/src/agent.rs reports zero findings
  - preserve given code, private representation and contracts; no added requires, weakened ensures, assumptions or escape hatches
  - only this file may change; private implementation helpers may be added
*/
/*! R03 API implementer, R-v0. Save the original file as <snapshot> outside
the delivery before /contract R03 and record its hash. Review totality on
empty/equal inputs, and minimum/maximum scalar and surrogate-gap boundaries.
The provided scalar conversion uses vstd's existing UTF-8 contract; its
valid_utf8 precondition is proved here, not assumed by a new specification.
ADVERSARIAL REVIEW — learner-owned, 30 minutes: check totality, API strength,
character boundaries, snapshot/freeze, delivery diff, audit, gate and transcript.
AGENT DASHBOARD — goal / changed files / obligations / gate / freeze / audit /
transcript / adversarial review / correction: ...
*/
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::char_scalar::{char_prev, char_next};
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

}


proof fn lemma_prefix_step(rs: Seq<(char,char)>, i: int, c: char)
    requires 0 <= i < rs.len(),
    ensures in_ranges(rs.subrange(0,i+1),c) <==>
        (in_ranges(rs.subrange(0,i),c) || in_range(rs[i],c)),
{
    assert(rs.subrange(0,i+1) =~= rs.subrange(0,i).push(rs[i]));
    lemma_in_ranges_push(rs.subrange(0,i),rs[i],c);
}

impl CharClass {
    // item: R03.A1v
    pub fn class_intersect(&self, other: &CharClass) -> (r: CharClass)
        requires self.valid(), other.valid(),
        ensures r.valid(), r@ == self@.intersect(other@),
    {
        let mut out=CharClass::class_empty();
        let mut i: usize=0;
        while i < self.ranges.len()
            invariant self.valid(), other.valid(), out.valid(),
                i <= self.ranges@.len(),
                forall|c: char| out@.contains(c) <==>
                    (in_ranges(self.ranges@.subrange(0,i as int),c) && other@.contains(c)),
            decreases self.ranges@.len()-i,
        {
            let (lo,hi)=self.ranges[i];
            out=other.inter_row(lo,hi,0,out);
            proof {
                assert(other.ranges@.subrange(0,other.ranges@.len() as int) =~= other.ranges@);
                assert forall|c: char| out@.contains(c) <==>
                    (in_ranges(self.ranges@.subrange(0,i as int+1),c) && other@.contains(c)) by {
                    lemma_prefix_step(self.ranges@,i as int,c);
                }
            }
            i=i+1;
        }
        proof {
            assert(self.ranges@.subrange(0,self.ranges@.len() as int) =~= self.ranges@);
            assert(out@ =~= self@.intersect(other@));
        }
        out
    }

    pub fn class_diff(&self, other: &CharClass) -> (r: CharClass)
        requires self.valid(), other.valid(),
        ensures r.valid(), r@ == self@.difference(other@),
    {
        let mut out=CharClass::class_empty();
        let mut i: usize=0;
        while i < self.ranges.len()
            invariant self.valid(), other.valid(), out.valid(),
                i <= self.ranges@.len(),
                forall|c: char| out@.contains(c) <==>
                    (in_ranges(self.ranges@.subrange(0,i as int),c) && ! other@.contains(c)),
            decreases self.ranges@.len()-i,
        {
            let (lo,hi)=self.ranges[i];
            out=other.diff_row(lo,hi,0,out);
            proof {
                assert(other.ranges@.subrange(0,other.ranges@.len() as int) =~= other.ranges@);
                assert forall|c: char| out@.contains(c) <==>
                    (in_ranges(self.ranges@.subrange(0,i as int+1),c) && ! other@.contains(c)) by {
                    lemma_prefix_step(self.ranges@,i as int,c);
                }
            }
            i=i+1;
        }
        proof {
            assert(self.ranges@.subrange(0,self.ranges@.len() as int) =~= self.ranges@);
            assert(out@ =~= self@.difference(other@));
        }
        out
    }
}

impl CharClass {
    fn inter_row(&self, lo: char, hi: char, i: usize, acc: CharClass) -> (r: CharClass)
        requires self.valid(), i <= self.ranges@.len(), acc.valid(),
        ensures r.valid(), forall|c: char| r@.contains(c) <==> acc@.contains(c) ||
            (lo <= c && c <= hi && in_ranges(self.ranges@.subrange(i as int,self.ranges@.len() as int),c)),
        decreases self.ranges@.len()-i,
    {
        if i == self.ranges.len() { return acc; }
        let (a,b)=self.ranges[i];
        let l=if lo < a { a } else { lo };
        let h=if hi < b { hi } else { b };
        let ghost old=acc@;
        let step=acc.class_insert(l,h);
        let r=self.inter_row(lo,hi,i+1,step);
        proof {
            assert forall|c: char| r@.contains(c) <==> old.contains(c) ||
                (lo <= c && c <= hi && in_ranges(self.ranges@.subrange(i as int,self.ranges@.len() as int),c)) by {
                lemma_in_ranges_drop(self.ranges@,i as int,c);
            }
        }
        r
    }
    fn diff_row(&self, lo: char, hi: char, i: usize, acc: CharClass) -> (r: CharClass)
        requires self.valid(), i <= self.ranges@.len(), acc.valid(),
        ensures r.valid(), forall|c: char| r@.contains(c) <==> acc@.contains(c) ||
            (lo <= c && c <= hi && !in_ranges(self.ranges@.subrange(i as int,self.ranges@.len() as int),c)),
        decreases self.ranges@.len()-i,
    {
        if lo > hi { return acc; }
        if i == self.ranges.len() { return acc.class_insert(lo,hi); }
        let (a,b)=self.ranges[i];
        let ghost old=acc@;
        let r=if hi < a || b < lo {
            self.diff_row(lo,hi,i+1,acc)
        } else {
            let out=if lo < a {
                let h=char_prev(a); self.diff_row(lo,h,i+1,acc)
            } else { acc };
            if b < hi {
                let l=char_next(b); self.diff_row(l,hi,i+1,out)
            } else { out }
        };
        proof {
            assert forall|c: char| r@.contains(c) <==> old.contains(c) ||
                (lo <= c && c <= hi && !in_ranges(self.ranges@.subrange(i as int,self.ranges@.len() as int),c)) by {
                lemma_in_ranges_drop(self.ranges@,i as int,c);
            }
        }
        r
    }
}
}
