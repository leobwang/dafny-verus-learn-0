// Topic (e) Q33 dev pair pd-d109-q33d (public; QPLAN §35.4, Δ416): vericoding `DH0136.dfy` at
// 387cd69 (MIT; HumanEval/134), its specification, its proofs and the definitions only its
// specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `check_if_last_char_is_a_letter`'s `requires` and `ensures` from its prose (HumanEval's
// prompt above the method), with any definition they need, and one call whose `requires` hold
// in `check_if_last_char_is_a_letter_witness`. You may add proof annotations; never change its
// executable code, and keep every other line.

predicate IsAlpha(c: char)
{
    ('a' <= c <= 'z') || ('A' <= c <= 'Z')
}

// </vc-preamble>

// <vc-helpers>

// </vc-helpers>

// <vc-spec>
/* The task's prose:
def check_if_last_char_is_a_letter(txt):
    '''
    Create a function that returns True if the last character
    of a given string is an alphabetical character and is not
    a part of a word, and False otherwise.
    Note: "word" is a group of characters separated by space.

    Examples:
    check_if_last_char_is_a_letter("apple pie") ➞ False
    check_if_last_char_is_a_letter("apple pi e") ➞ True
    check_if_last_char_is_a_letter("apple pi e ") ➞ False
    check_if_last_char_is_a_letter("") ➞ False
    '''
*/
method check_if_last_char_is_a_letter(txt: string) returns (result: bool)
// </vc-spec>
// <vc-code>
{
  if |txt| == 0 {
    result := false;
  } else if !IsAlpha(txt[|txt| - 1]) {
    result := false;
  } else if |txt| == 1 {
    result := true;
  } else {
    result := txt[|txt| - 2] == ' ';
  }
}
// </vc-code>

/** A non-vacuity witness for `check_if_last_char_is_a_letter`: one call whose `requires` hold. */
method check_if_last_char_is_a_letter_witness()
{
}
