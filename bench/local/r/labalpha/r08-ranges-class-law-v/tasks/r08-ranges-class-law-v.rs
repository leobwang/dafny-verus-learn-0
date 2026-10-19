// R12_HINT_SITES: [{"name":"c1","identifiers":["tail","c"],"kind":"calls","callees":["lemma_ranges_set_law"]},{"name":"h1","identifiers":["rs","tail","j"]},{"name":"h2","identifiers":["rs","tail","j"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_ranges_set_law","start":25,"end":44}]
use vstd::prelude::*;

verus! {

// Provided definitions (R08 range-star engine, given), copied verbatim.
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

// The task (R08.H1 lemma_ranges_set_law): the set the engine's start model holds is exactly the characters of the pattern's ranges.
pub proof fn lemma_ranges_set_law(rs: Seq<(char, char)>, c: char)
    ensures
        ranges_set(rs).contains(c) == in_char_ranges(rs, c),
    decreases rs.len(),
{
    if rs.len() > 0 {
        let tail = rs.drop_first();
        /*R12_CALLS:c1*/
        if in_char_ranges(tail, c) {
            let j = choose|j: int| 0 <= j < tail.len() && (#[trigger] tail[j]).0 <= c && c <= tail[j].1;
            assert(/*R12_HINT:h1*/ true);
        }
        if in_char_ranges(rs, c) {
            let j = choose|j: int| 0 <= j < rs.len() && (#[trigger] rs[j]).0 <= c && c <= rs[j].1;
            if j > 0 {
                assert(/*R12_HINT:h2*/ true);
            }
        }
    }
}
} // verus!
