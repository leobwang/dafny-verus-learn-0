// Topic (e) Q33 dev pair pv-v106-q33d (public; QPLAN §35.4, Δ416): humaneval-verus
// `human_eval_017.rs` at bbe93f7 (MIT; HumanEval/17), its specification, its proofs and the
// definitions only its specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `parse_music`'s `requires` and `ensures` from its prose (the PROMPT comment below),
// with any definition they need, and one call whose `requires` hold in `parse_music_witness`.
// You may add proof annotations; never change its executable code, and keep every other line.
/*
### ID
HumanEval/17
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

// TODO: Put your solution (the specification, implementation, and proof) to the task here
pub open spec fn spec_parse_music(s: Seq<char>) -> Option<Seq<int>>
    decreases s.len(),
{
    if s.len() == 0 {
        Some(seq![])
    } else if s.len() >= 2 && s[0] == 'o' && s[1] == '|' {
        if let Some(rest) = spec_parse_music(s[2..]) {
            Some(seq![2] + rest)
        } else {
            None
        }
    } else if s.len() >= 2 && s[0] == '.' && s[1] == '|' {
        if let Some(rest) = spec_parse_music(s[2..]) {
            Some(seq![1] + rest)
        } else {
            None
        }
    } else if s.len() != 0 && s[0] == 'o' {
        if let Some(rest) = spec_parse_music(s[1..]) {
            Some(seq![4] + rest)
        } else {
            None
        }
    } else if s.len() != 0 && s[0] == ' ' {
        // Somewhat more lenient: allows multiple spaces between notes
        spec_parse_music(s.drop_first())
    } else {
        None
    }
}

pub fn parse_music(s: &str) -> (res: Option<Vec<u8>>)
{
    let s_len = s.unicode_len();
    let mut beats = vec![];
    let mut i = 0;

    while i < s_len
        decreases s_len - i,
    {
        let c = s.get_char(i);

        if c == ' ' {
            i += 1;
            continue;
        }
        if i < s_len - 1 {
            let c2 = s.get_char(i + 1);

            if c == 'o' && c2 == '|' {
                beats.push(2);
                i += 2;
                continue;
            } else if c == '.' && c2 == '|' {
                beats.push(1);
                i += 2;
                continue;
            }
        }
        if c == 'o' {
            beats.push(4);
            i += 1;
        } else {
            return None;
        }
    }

    Some(beats)
}

/// A non-vacuity witness for `parse_music`: one call whose `requires` hold.
fn parse_music_witness() {
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT
from typing import List


def parse_music(music_string: str) -> List[int]:
    """ Input to this function is a string representing musical notes in a special ASCII format.
    Your task is to parse this string and return list of integers corresponding to how many beats does each
    not last.

    Here is a legend:
    'o' - whole note, lasts four beats
    'o|' - half note, lasts two beats
    '.|' - quater note, lasts one beat

    >>> parse_music('o o| .| o| o| .| .| .| .| o o')
    [4, 2, 1, 2, 2, 1, 1, 1, 1, 4, 4]
    """

*/

/*
### ENTRY POINT
parse_music
*/

/*
### CANONICAL SOLUTION
    note_map = {'o': 4, 'o|': 2, '.|': 1}
    return [note_map[x] for x in music_string.split(' ') if x]

*/

/*
### TEST


METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate('') == []
    assert candidate('o o o o') == [4, 4, 4, 4]
    assert candidate('.| .| .| .|') == [1, 1, 1, 1]
    assert candidate('o| o| .| .| o o o o') == [2, 2, 1, 1, 4, 4, 4, 4]
    assert candidate('o| .| o| .| o o| o o|') == [2, 1, 2, 1, 4, 2, 4, 2]

*/
