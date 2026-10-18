// R12_HINT_SITES: [{"name":"i1","identifiers":["MAX","Option","Vec","checked_add","checked_total_str_len","drop_last","fold_left","i","is_none","is_some","len","lens","lst","map_values","push","ret","s","spec_sum","str","sum","total_str_len","unwrap","usize","x","y"]},{"name":"i2","identifiers":["MAX","Option","Vec","checked_add","checked_total_str_len","drop_last","fold_left","i","is_none","is_some","len","lens","lst","map_values","push","ret","s","spec_sum","str","sum","total_str_len","unwrap","usize","x","y"]},{"name":"a3","identifiers":["MAX","Option","Vec","checked_add","checked_total_str_len","drop_last","fold_left","i","is_none","is_some","len","lens","lst","map_values","push","ret","s","spec_sum","str","sum","total_str_len","unwrap","usize","x","y"]},{"name":"a4","identifiers":["MAX","Option","Vec","checked_add","checked_total_str_len","drop_last","fold_left","i","is_none","is_some","len","lens","lst","map_values","push","ret","s","spec_sum","str","sum","total_str_len","unwrap","usize","x","y"]},{"name":"a5","identifiers":["MAX","Option","Vec","checked_add","checked_total_str_len","drop_last","fold_left","i","is_none","is_some","len","lens","lst","map_values","push","ret","s","spec_sum","str","sum","total_str_len","unwrap","usize","x","y"]},{"name":"a6","identifiers":["MAX","Option","Vec","checked_add","checked_total_str_len","drop_last","fold_left","i","is_none","is_some","len","lens","lst","map_values","push","ret","s","spec_sum","str","sum","total_str_len","unwrap","usize","x","y"]},{"name":"a7","identifiers":["MAX","Option","Vec","checked_add","checked_total_str_len","drop_last","fold_left","i","is_none","is_some","len","lens","lst","map_values","push","ret","s","spec_sum","str","sum","total_str_len","unwrap","usize","x","y"]}]
// R12_SOURCE_SPANS: [{"symbol":"checked_total_str_len","start":39,"end":75}]
// R12 public task: humaneval-verus human_eval_074.rs (MIT (set and HumanEval prompts)); proof annotations moved into hint sites.
/*
### ID
HumanEval/74
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

spec fn spec_sum(s: Seq<nat>) -> int {
    s.fold_left(0, |x: int, y| x + y)
}

// i and j are ends of the subrange - exclusive
proof fn lemma_increasing_sum(s: Seq<nat>, i: int, j: int)
    requires
        0 <= i <= j <= s.len(),
    ensures
        spec_sum(s[..i]) <= spec_sum(s[..j]),
    decreases j - i,
{
    if (i < j) {
        assert(spec_sum(s[..j - 1]) <= spec_sum(s[..j])) by {
            assert(s[..j].drop_last() == s[..j - 1]);
        }
        lemma_increasing_sum(s, i, j - 1);
    }
}

spec fn total_str_len(strings: Seq<&str>) -> int {
    spec_sum(strings.map_values(|s: &str| s@.len()))
}

fn checked_total_str_len(lst: &Vec<&str>) -> (ret: Option<usize>)
    ensures
        ret.is_some() <==> total_str_len(lst@) <= usize::MAX,
        ret.is_some() <==> ret.unwrap() == total_str_len(lst@),
{
    let ghost lens = Seq::<nat>::empty();
    let mut sum: usize = 0;
    for i in 0..lst.len()
        invariant
            /*R12_HINT:i1*/ true,
            /*R12_HINT:i2*/ true,
            lens =~= lst@.map_values(|s: &str| s@.len())[..i],
            lens =~= lst@[..i].map_values(|s: &str| s@.len()),
    {
        let x = lst[i].unicode_len();
        proof {
            assert(/*R12_HINT:a3*/ true);
            lens = lens.push(x as nat);
            assert(lens =~= lst@.map_values(|s: &str| s@.len())[..i + 1]);

            lemma_increasing_sum(lst@.map_values(|s: &str| s@.len()), i + 1, lst@.len() as int);
            assert(total_str_len(lst@) >= spec_sum(lens)) by {
                assert(lst@.map_values(|s: &str| s@.len()) =~= lst@.map_values(
                    |s: &str| s@.len(),
                )[..lst@.len()]);
            }
            if x + sum > usize::MAX {
                assert(/*R12_HINT:a4*/ true);
                assert(/*R12_HINT:a5*/ true);
            }
        }
        sum = sum.checked_add(x)?;
        assert(/*R12_HINT:a6*/ true);
    }
    assert(/*R12_HINT:a7*/ true);
    return Some(sum);
}

fn total_match<'a>(lst1: Vec<&'a str>, lst2: Vec<&'a str>) -> (ret: Option<Vec<&'a str>>)
    ensures
        ret.is_some() <== total_str_len(lst1@) <= usize::MAX && total_str_len(lst2@) <= usize::MAX,
        ret.is_some() ==> ret.unwrap() == if total_str_len(lst1@) <= total_str_len(lst2@) {
            lst1
        } else {
            lst2
        },
{
    if checked_total_str_len(&lst1)? <= checked_total_str_len(&lst2)? {
        Some(lst1)
    } else {
        Some(lst2)
    }
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT

def total_match(lst1, lst2):
    '''
    Write a function that accepts two lists of strings and returns the list that has
    total number of chars in the all strings of the list less than the other list.

    if the two lists have the same number of chars, return the first list.

    Examples
    total_match([], []) ➞ []
    total_match(['hi', 'admin'], ['hI', 'Hi']) ➞ ['hI', 'Hi']
    total_match(['hi', 'admin'], ['hi', 'hi', 'admin', 'project']) ➞ ['hi', 'admin']
    total_match(['hi', 'admin'], ['hI', 'hi', 'hi']) ➞ ['hI', 'hi', 'hi']
    total_match(['4'], ['1', '2', '3', '4', '5']) ➞ ['4']
    '''

*/

/*
### ENTRY POINT
total_match
*/

/*
### CANONICAL SOLUTION
    l1 = 0
    for st in lst1:
        l1 += len(st)

    l2 = 0
    for st in lst2:
        l2 += len(st)

    if l1 <= l2:
        return lst1
    else:
        return lst2

*/

/*
### TEST
def check(candidate):

    # Check some simple cases
    assert True, "This prints if this assert fails 1 (good for debugging!)"
    assert candidate([], []) == []
    assert candidate(['hi', 'admin'], ['hi', 'hi']) == ['hi', 'hi']
    assert candidate(['hi', 'admin'], ['hi', 'hi', 'admin', 'project']) == ['hi', 'admin']
    assert candidate(['4'], ['1', '2', '3', '4', '5']) == ['4']
    assert candidate(['hi', 'admin'], ['hI', 'Hi']) == ['hI', 'Hi']
    assert candidate(['hi', 'admin'], ['hI', 'hi', 'hi']) == ['hI', 'hi', 'hi']
    assert candidate(['hi', 'admin'], ['hI', 'hi', 'hii']) == ['hi', 'admin']


    # Check some edge cases that are easy to work out by hand.
    assert True, "This prints if this assert fails 2 (also good for debugging!)"
    assert candidate([], ['this']) == []
    assert candidate(['this'], []) == []


*/
