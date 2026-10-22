// R12_HINT_SITES: [{"name":"h1"},{"name":"h2"},{"name":"d1","kind":"decreases"}]
// R12_SOURCE_SPANS: [{"symbol":"class_covers_r13","start":77,"end":94}]
use vstd::prelude::*;

verus! {

// Provided layer: the membership part of rg_re_a2::char_class (layer A2), copied verbatim
// into a module of its own; the representation stays private to it.
pub mod r12_a2 {
use vstd::prelude::*;

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

}

}

use r12_a2::CharClass;

// The task (R13.H2 class_covers_r13): every character of s lies in the class cc, a verified loop over A2's class API.
pub fn class_covers_r13(cc: &CharClass, s: &Vec<char>) -> (b: bool)
    ensures
        b == (forall|i: int| 0 <= i < s@.len() ==> cc@.contains(#[trigger] s@[i])),
{
    let mut k: usize = 0;
    while k < s.len()
        invariant
            /*R12_HINT:h1*/ true,
            /*R12_HINT:h2*/ true,
        decreases /*R12_DECREASES:d1*/ (0 as int),
    {
        if !cc.class_member(s[k]) {
            return false;
        }
        k = k + 1;
    }
    true
}
} // verus!
