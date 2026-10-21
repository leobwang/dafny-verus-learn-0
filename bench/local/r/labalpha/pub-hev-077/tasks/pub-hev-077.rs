// R12_HINT_SITES: [{"name":"a1"},{"name":"i2"},{"name":"i3"},{"name":"i4"},{"name":"a5"},{"name":"a6"},{"name":"a7"},{"name":"a8"}]
// R12_SOURCE_SPANS: [{"symbol":"parse_nested_parens","start":57,"end":110}]
// R12 public task: humaneval-verus human_eval_006.rs (MIT (set and HumanEval prompts)); proof annotations moved into hint sites.
/*
### ID
HumanEval/6
*/
/*
### VERUS BEGIN
*/
use vstd::math::*;
use vstd::prelude::*;

verus! {

// TODO: Put your solution (the specification, implementation, and proof) to the task here
/// Given a space separated group of nested parentheses
/// return a list of maximum depths of each group.
pub open spec fn spec_nested_parens(s: Seq<char>) -> Option<Seq<int>> {
    spec_nested_parens_helper(s, 0, 0, seq![])
}

/// Formalizes the problem as a rewrite system
pub open spec fn spec_nested_parens_helper(
    s: Seq<char>,
    depth: int,
    max_depth: int,
    prev_depths: Seq<int>,
) -> Option<Seq<int>>
    decreases s.len(),
{
    if s.len() == 0 && depth == 0 {
        if max_depth == 0 {
            // (s, d, m, p) => Some(p) if s is empty and d is 0 and m == 0
            Some(prev_depths)
        } else {
            // (s, d, m, p) => Some(p + [max_depth]) if s is empty and d is 0 and m != 0
            Some(prev_depths + seq![max_depth])
        }
    } else if s.len() != 0 && s[0] == ' ' && depth == 0 && max_depth != 0 {
        // Move on to the next group (if the previous group is non-empty)
        // (s, d, m, p) => (s[1..], 0, 0, prev_depths + [max_depth]) if s[0] == ' ' and d == 0
        spec_nested_parens_helper(s.drop_first(), 0, 0, prev_depths + seq![max_depth])
    } else if s.len() != 0 && s[0] == '(' {
        // (s, d, m, p) => (s[1..], d + 1, max(d + 1, m), p) if s[0] == '('
        spec_nested_parens_helper(s.drop_first(), depth + 1, max(depth + 1, max_depth), prev_depths)
    } else if s.len() != 0 && s[0] == ')' && depth > 0 {
        // (s, d, m, p) => (s[1..], d - 1, m, p) if s[0] == ')' and d > 0
        spec_nested_parens_helper(s.drop_first(), depth - 1, max_depth, prev_depths)
    } else {
        // Otherwise fail
        None
    }
}

/// Executable version
pub fn parse_nested_parens(s: &str) -> (res: Option<Vec<usize>>)
    ensures
        res matches Some(res) ==> spec_nested_parens(s@) == Some(res@.map_values(|d| d as int)),
        res is None ==> spec_nested_parens(s@) is None,
{
    let s_len = s.unicode_len();
    let mut depth = 0;
    let mut max_depth = 0;
    let mut all_depths = vec![];

    assert(/*R12_HINT:a1*/ true);
    assert(all_depths@.map_values(|d| d as int) =~= Seq::<int>::empty());

    for i in 0..s_len
        invariant
            /*R12_HINT:i2*/ true,
            /*R12_HINT:i3*/ true,
            /*R12_HINT:i4*/ true,
    {
        let c = s.get_char(i);  // Not the best performance-wise

        assert(/*R12_HINT:a5*/ true);

        if c == ' ' && depth == 0 && max_depth != 0 {
            // Push and map_values commute
            assert(/*R12_HINT:a6*/ true);

            all_depths.push(max_depth);
            depth = 0;
            max_depth = 0;
        } else if c == '(' {
            depth += 1;
            if depth > max_depth {
                max_depth = depth;
            }
        } else if c == ')' && depth > 0 {
            depth -= 1;
        } else {
            return None;
        }
    }

    assert(/*R12_HINT:a7*/ true);

    if depth != 0 {
        return None;
    }
    if max_depth != 0 {
        // Push and map_values commute
        assert(/*R12_HINT:a8*/ true);
        all_depths.push(max_depth);
    }
    Some(all_depths)
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT
from typing import List


def parse_nested_parens(paren_string: str) -> List[int]:
    """ Input to this function is a string represented multiple groups for nested parentheses separated by spaces.
    For each of the group, output the deepest level of nesting of parentheses.
    E.g. (()()) has maximum two levels of nesting while ((())) has three.

    >>> parse_nested_parens('(()()) ((())) () ((())()())')
    [2, 3, 1, 3]
    """

*/

/*
### ENTRY POINT
parse_nested_parens
*/

/*
### CANONICAL SOLUTION
    def parse_paren_group(s):
        depth = 0
        max_depth = 0
        for c in s:
            if c == '(':
                depth += 1
                max_depth = max(depth, max_depth)
            else:
                depth -= 1

        return max_depth

    return [parse_paren_group(x) for x in paren_string.split(' ') if x]

*/

/*
### TEST


METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate('(()()) ((())) () ((())()())') == [2, 3, 1, 3]
    assert candidate('() (()) ((())) (((())))') == [1, 2, 3, 4]
    assert candidate('(()(())((())))') == [4]

*/
