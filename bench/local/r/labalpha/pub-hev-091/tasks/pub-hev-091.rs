// R12_HINT_SITES: [{"name":"i1","identifiers":["MAX","MIN","b","brackets","c","correct_bracketing","i","i32","len","prev","ret","spec_bracketing","spec_bracketing_helper","stack_size","str"]},{"name":"i2","identifiers":["MAX","MIN","b","brackets","c","correct_bracketing","i","i32","len","prev","ret","spec_bracketing","spec_bracketing_helper","stack_size","str"]},{"name":"i3","identifiers":["MAX","MIN","b","brackets","c","correct_bracketing","i","i32","len","prev","ret","spec_bracketing","spec_bracketing_helper","stack_size","str"]}]
// R12_SOURCE_SPANS: [{"symbol":"correct_bracketing","start":36,"end":67}]
// R12 public task: humaneval-verus human_eval_061.rs (MIT (set and HumanEval prompts)); proof annotations moved into hint sites.
/*
### ID
HumanEval/61
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

// say the return value is (x, b), x = number of '(' - number of ')', b = whether x ever dipped below 0
spec fn spec_bracketing_helper(brackets: Seq<char>) -> (int, bool) {
    brackets.fold_left(
        (0, true),
        |p: (int, bool), c|
            {
                let (x, b) = p;
                match (c) {
                    '(' => (x + 1, b),
                    ')' => (x - 1, b && x - 1 >= 0),
                    _ => (x, b),
                }
            },
    )
}

spec fn spec_bracketing(brackets: Seq<char>) -> bool {
    let p = spec_bracketing_helper(brackets);
    p.1 && p.0 == 0
}

fn correct_bracketing(brackets: &str) -> (ret: bool)
    requires
        brackets@.len() <= i32::MAX,
        -brackets@.len() >= i32::MIN,
    ensures
        ret <==> spec_bracketing(brackets@),
{
    let mut i = 0;
    let mut b = true;
    let mut stack_size: i32 = 0;

    while i < brackets.unicode_len()
        invariant
            /*R12_HINT:i1*/ true,
            /*R12_HINT:i2*/ true,
            /*R12_HINT:i3*/ true,
        decreases brackets@.len() - i,
    {
        let c = brackets.get_char(i);
        let ghost prev = spec_bracketing_helper(brackets@[..i]);
        if (c == '(') {
            stack_size += 1;
        } else if (c == ')') {
            b = b && stack_size > 0;
            stack_size -= 1;
        }
        assert(brackets@[..i + 1].drop_last() =~= brackets@[..i]);
        i += 1;
    }
    assert(brackets@ =~= brackets@[..i]);
    b && stack_size == 0
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT


def correct_bracketing(brackets: str):
    """ brackets is a string of "(" and ")".
    return True if every opening bracket has a corresponding closing bracket.

    >>> correct_bracketing("(")
    False
    >>> correct_bracketing("()")
    True
    >>> correct_bracketing("(()())")
    True
    >>> correct_bracketing(")(()")
    False
    """

*/

/*
### ENTRY POINT
correct_bracketing
*/

/*
### CANONICAL SOLUTION
    depth = 0
    for b in brackets:
        if b == "(":
            depth += 1
        else:
            depth -= 1
        if depth < 0:
            return False
    return depth == 0

*/

/*
### TEST


METADATA = {}


def check(candidate):
    assert candidate("()")
    assert candidate("(()())")
    assert candidate("()()(()())()")
    assert candidate("()()((()()())())(()()(()))")
    assert not candidate("((()())))")
    assert not candidate(")(()")
    assert not candidate("(")
    assert not candidate("((((")
    assert not candidate(")")
    assert not candidate("(()")
    assert not candidate("()()(()())())(()")
    assert not candidate("()()(()())()))()")


*/
